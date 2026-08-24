"""Safe, whitelist-only system control.

Deliberately does NOT expose arbitrary shell execution to the model. Apps and
scripts must be explicitly registered by the user first (apps.json / scripts/),
and power actions (shutdown/sleep/lock) are off by default and must be opted
into via ENABLE_POWER_ACTIONS=true in .env.
"""

import json
import subprocess
import webbrowser
from pathlib import Path

from sarmad import config

SCRIPTS_DIR = Path("./scripts").resolve()

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


def open_app(app_name: str) -> dict:
    apps = _load_apps()
    key = app_name.strip().lower()
    if key not in apps:
        return {
            "ok": False,
            "error": f"'{app_name}' is not in apps.json. Known apps: {', '.join(apps) or '(none configured)'}",
        }
    subprocess.Popen([apps[key]])
    return {"ok": True, "opened": key}


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
