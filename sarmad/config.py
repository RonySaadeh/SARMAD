import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
EDGE_TTS_VOICE = os.environ.get("EDGE_TTS_VOICE", "en-US-GuyNeural")

VOSK_MODEL_PATH = os.environ.get("VOSK_MODEL_PATH", "./vosk-model-small-en-us-0.15")

PROJECTS_DIR = Path(os.environ.get("PROJECTS_DIR", "./Projects")).expanduser().resolve()

APPS_CONFIG_PATH = Path(os.environ.get("APPS_CONFIG_PATH", "./apps.json")).expanduser().resolve()

ENABLE_POWER_ACTIONS = os.environ.get("ENABLE_POWER_ACTIONS", "false").strip().lower() == "true"

MEMORY_DB_PATH = Path(os.environ.get("MEMORY_DB_PATH", "./sarmad_memory.db")).expanduser().resolve()

WAKE_PHRASES = ["sarmad", "sarmad daddy's home", "sarmad daddy is home"]


def require_keys() -> None:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "Missing required environment variable: ANTHROPIC_API_KEY. "
            "Copy .env.example to .env and fill it in."
        )
