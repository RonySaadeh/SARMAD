import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

# Model tiers for voice replies: FAST_MODEL handles everyday questions/chat by
# default; SMART_MODEL is used when the user says something like "use your
# smartest model" or "use Opus" for a genuinely hard task. See brain.py.
FAST_MODEL = os.environ.get("FAST_MODEL", "claude-haiku-4-5-20251001")
SMART_MODEL = os.environ.get("SMART_MODEL", "claude-opus-5")

WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
# faster-whisper auto-detects the spoken language per request (English, Arabic,
# or a mix), so no separate language switch is needed for speech-to-text.
EDGE_TTS_VOICE = os.environ.get("EDGE_TTS_VOICE", "en-US-GuyNeural")
# Used instead of EDGE_TTS_VOICE when a reply contains Arabic script.
ARABIC_TTS_VOICE = os.environ.get("ARABIC_TTS_VOICE", "ar-SA-HamedNeural")

VOSK_MODEL_PATH = os.environ.get("VOSK_MODEL_PATH", "./vosk-model-small-en-us-0.15")

PROJECTS_DIR = Path(os.environ.get("PROJECTS_DIR", "./Projects")).expanduser().resolve()

APPS_CONFIG_PATH = Path(os.environ.get("APPS_CONFIG_PATH", "./apps.json")).expanduser().resolve()

ENABLE_POWER_ACTIONS = os.environ.get("ENABLE_POWER_ACTIONS", "false").strip().lower() == "true"

ENABLE_HUD = os.environ.get("ENABLE_HUD", "true").strip().lower() == "true"

CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", "0"))

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD", "")
IMAP_HOST = os.environ.get("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
ENABLE_EMAIL_SEND = os.environ.get("ENABLE_EMAIL_SEND", "false").strip().lower() == "true"

ENABLE_CODING_AGENT = os.environ.get("ENABLE_CODING_AGENT", "false").strip().lower() == "true"

# A calendar's private ICS feed URL (read-only). For Google Calendar: Settings
# > [your calendar] > "Secret address in iCal format". Works the same way for
# any calendar that publishes an ICS feed (Outlook, iCloud, etc).
CALENDAR_ICS_URL = os.environ.get("CALENDAR_ICS_URL", "")

MEMORY_DB_PATH = Path(os.environ.get("MEMORY_DB_PATH", "./sarmad_memory.db")).expanduser().resolve()

# "Sarmad" itself isn't a word the small English Vosk model recognizes (it's
# always transcribed as [unk]), so matching only requires the part that IS
# reliably recognized - you still say "Sarmad, Daddy's home" out loud, this
# just triggers on "daddy...home". Written without an apostrophe since Vosk
# transcribes speech as "daddy is home", not the contraction.
WAKE_PHRASES = ["daddy is home", "daddy home"]


def require_keys() -> None:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "Missing required environment variable: ANTHROPIC_API_KEY. "
            "Copy .env.example to .env and fill it in."
        )
