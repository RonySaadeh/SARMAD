"""Turns a spoken project idea into a real scaffolded folder on disk.

Delegates the actual file-planning to a dedicated Claude call (kept separate from
the main conversation loop) that returns a JSON manifest of relative paths and
file contents, which are then written to disk and git-initialized.
"""

import json
import re
import subprocess

import anthropic

from sarmad import config

_MANIFEST_PROMPT = """You are scaffolding a brand new software project.

Project name: {name}
Description: {description}

Respond with ONLY a JSON object (no markdown fences, no commentary) of the form:
{{
  "files": [
    {{"path": "relative/path/to/file.ext", "content": "full file contents"}}
  ]
}}

Include a README.md describing the project and how to run it, a sensible
directory layout, dependency/config files appropriate for the stack you choose,
and enough starter code that the project actually runs. Keep it focused and
buildable rather than exhaustive. Choose a reasonable tech stack yourself based
on the description if none is specified."""


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "project"


def create_project(name: str, description: str) -> dict:
    """Generate a scaffolded project on disk under config.PROJECTS_DIR and git-init it."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=8000,
        messages=[{"role": "user", "content": _MANIFEST_PROMPT.format(name=name, description=description)}],
    )
    raw = "".join(block.text for block in response.content if block.type == "text").strip()
    raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()

    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"Could not parse project manifest: {exc}"}

    project_dir = config.PROJECTS_DIR / _slugify(name)
    project_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for file_entry in manifest.get("files", []):
        rel_path = file_entry["path"]
        file_path = (project_dir / rel_path).resolve()
        if project_dir.resolve() not in file_path.parents and file_path != project_dir.resolve():
            continue
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file_entry["content"], encoding="utf-8")
        written.append(rel_path)

    try:
        subprocess.run(["git", "init"], cwd=project_dir, capture_output=True, check=False)
    except FileNotFoundError:
        pass

    return {"ok": True, "path": str(project_dir), "files_written": written}
