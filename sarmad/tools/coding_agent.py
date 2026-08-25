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
import time
from pathlib import Path

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

    print(f"\n----- Claude Code working in {project_dir.name} -----")
    try:
        proc = subprocess.Popen(
            ["claude", "-p", instructions, "--permission-mode", "bypassPermissions"],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "The `claude` CLI isn't installed or on PATH. Install Claude Code and run `claude login` first.",
        }

    # Stream its output live to this console as it works, instead of only
    # showing something once the whole task is done.
    output_lines: list[str] = []
    start = time.monotonic()
    for line in proc.stdout:
        print(line, end="", flush=True)
        output_lines.append(line)
        if time.monotonic() - start > _TIMEOUT_SECONDS:
            proc.kill()
            return {"ok": False, "error": f"Gave up after {_TIMEOUT_SECONDS} seconds without finishing."}
    proc.wait()
    print(f"----- Claude Code finished (exit {proc.returncode}) -----\n")

    output = "".join(output_lines)
    if proc.returncode != 0:
        return {"ok": False, "error": output.strip()[-2000:] or "claude CLI failed."}

    changed = _changed_files(project_dir)
    if changed:
        subprocess.run(["git", "add", "-A"], cwd=project_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"SARMAD: {instructions[:72]}"],
            cwd=project_dir,
            capture_output=True,
        )
        print(f"----- Changed files: {', '.join(changed)} -----\n")

    return {"ok": True, "summary": output.strip()[-2000:], "files_changed": changed}


def _changed_files(project_dir: Path) -> list[str]:
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=project_dir, capture_output=True, text=True)
    return [line[3:].strip() for line in proc.stdout.splitlines() if line.strip()]
