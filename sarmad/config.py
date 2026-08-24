import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_TTS_VOICE = os.environ.get("OPENAI_TTS_VOICE", "alloy")

VOSK_MODEL_PATH = os.environ.get("VOSK_MODEL_PATH", "./vosk-model-small-en-us-0.15")

PROJECTS_DIR = Path(os.environ.get("PROJECTS_DIR", "./Projects")).expanduser().resolve()

APPS_CONFIG_PATH = Path(os.environ.get("APPS_CONFIG_PATH", "./apps.json")).expanduser().resolve()

ENABLE_POWER_ACTIONS = os.environ.get("ENABLE_POWER_ACTIONS", "false").strip().lower() == "true"

MEMORY_DB_PATH = Path(os.environ.get("MEMORY_DB_PATH", "./sarmad_memory.db")).expanduser().resolve()

WAKE_PHRASES = ["sarmad", "sarmad daddy's home", "sarmad daddy is home"]


def require_keys() -> None:
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )
