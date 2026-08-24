"""Fixes/extends a project by delegating to the Claude Code CLI itself.

SARMAD doesn't reimplement a coding agent — it shells out to `claude`, the
same CLI this project was built with, scoped to one project folder via its
working directory. That gets the real thing (full file editing, running
tests/installs, and whatever GitHub access your local `claude` login already
has) instead of a smaller reimplementation.

Requires the Claude Code CLI installed and authenticated on this machine
(https://docs.claude.com/en/docs/claude-code — run `claude login` once) and
ENABLE_CODING_AGENT=true in .env, since it runs unattended with permission
prompts bypassed so it can actually finish a task without you at the
keyboard.
"""

import subprocess

from sarmad import config

_TIMEOUT_SECONDS = 600


def fix_project(project_name: str, instructions: str) -> dict:
    if not config.ENABLE_CODING_AGENT:
        return {
            "ok": False,
            "error": "The coding agent is disabled. Set ENABLE_CODING_AGENT=true in .env to allow it.",
        }

    project_dir = (config.PROJECTS_DIR / project_name).resolve()
    if config.PROJECTS_DIR.resolve() not in project_dir.parents:
        return {"ok": False, "error": "Invalid project name."}
    if not project_dir.is_dir():
        return {"ok": False, "error": f"No project folder named '{project_name}' under {config.PROJECTS_DIR}."}

    try:
        proc = subprocess.run(
            ["claude", "-p", instructions, "--permission-mode", "bypassPermissions"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "The `claude` CLI isn't installed or on PATH. Install Claude Code and run `claude login` first.",
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Gave up after {_TIMEOUT_SECONDS} seconds without finishing."}

    if proc.returncode != 0:
        return {"ok": False, "error": (proc.stderr or proc.stdout).strip()[-2000:] or "claude CLI failed."}

    return {"ok": True, "summary": proc.stdout.strip()[-2000:]}
