"""System control: open apps freely, but keep scripts/power actions gated.

Opening an app is low-risk, so open_app isn't limited to a manual whitelist —
it checks apps.json first (for custom aliases/paths), then searches Start
Menu shortcuts for anything installed normally. Running a script or a power
action is a different risk category and stays deliberately gated: scripts
must be explicitly registered under ./scripts, and power actions
(shutdown/sleep/lock) are off by default until ENABLE_POWER_ACTIONS=true.
"""

import difflib
import json
import os
import subprocess
import webbrowser
from pathlib import Path

from sarmad import config

SCRIPTS_DIR = Path("./scripts").resolve()

_START_MENU_DIRS = [
    Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Microsoft/Windows/Start Menu/Programs",
    Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
]

_POWER_COMMANDS = {
    "shutdown": ["shutdown", "/s", "/t", "0"],
    "restart": ["shutdown", "/r", "/t", "0"],
    "sleep": ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
    "lock": ["rundll32.exe", "user32.dll,LockWorkStation"],
}


def _load_apps() -> dict:
    if not config.APPS_CONFIG_PATH.exists():
        return {}
    return json.loads(config.APPS_CONFIG_PATH.read_text(encoding="utf-8"))


def _index_start_menu_shortcuts() -> dict[str, Path]:
    index = {}
    for base in _START_MENU_DIRS:
        if not base.exists():
            continue
        for shortcut in base.rglob("*.lnk"):
            index[shortcut.stem.lower()] = shortcut
    return index


def open_app(app_name: str) -> dict:
    key = app_name.strip().lower()

    apps = _load_apps()
    if key in apps:
        subprocess.Popen([apps[key]])
        return {"ok": True, "opened": key}

    shortcuts = _index_start_menu_shortcuts()
    if key in shortcuts:
        os.startfile(str(shortcuts[key]))
        return {"ok": True, "opened": key}

    match = difflib.get_close_matches(key, shortcuts.keys(), n=1, cutoff=0.6)
    if match:
        os.startfile(str(shortcuts[match[0]]))
        return {"ok": True, "opened": match[0]}

    return {
        "ok": False,
        "error": f"Couldn't find an app matching '{app_name}' in your Start Menu. Add it to apps.json with its exe path.",
    }


def open_url(url: str) -> dict:
    webbrowser.open(url)
    return {"ok": True, "opened": url}


def run_script(script_name: str) -> dict:
    key = Path(script_name).name
    script_path = SCRIPTS_DIR / key
    if not script_path.exists() or script_path.parent.resolve() != SCRIPTS_DIR:
        return {"ok": False, "error": f"'{script_name}' is not a registered script in ./scripts"}
    subprocess.Popen([str(script_path)], shell=False)
    return {"ok": True, "ran": key}


def power_action(action: str) -> dict:
    if not config.ENABLE_POWER_ACTIONS:
        return {
            "ok": False,
            "error": "Power actions are disabled. Set ENABLE_POWER_ACTIONS=true in .env to allow shutdown/restart/sleep/lock.",
        }
    key = action.strip().lower()
    if key not in _POWER_COMMANDS:
        return {"ok": False, "error": f"Unknown power action '{action}'. Options: {', '.join(_POWER_COMMANDS)}"}
    subprocess.Popen(_POWER_COMMANDS[key])
    return {"ok": True, "action": key}
