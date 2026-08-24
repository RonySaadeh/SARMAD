"""Messaging: prepare a WhatsApp message via its "click to chat" link.

No API key or login needed — wa.me opens WhatsApp Web/the desktop app with the
message pre-filled, and the user hits send themselves. Same prepare-then-
confirm pattern used for reservations, email, and calendar.
"""

import re
import webbrowser
from urllib.parse import quote


def send_whatsapp_message(phone: str, message: str) -> dict:
    digits = re.sub(r"\D", "", phone)
    if not digits:
        return {"ok": False, "error": f"'{phone}' doesn't look like a phone number."}

    webbrowser.open(f"https://wa.me/{digits}?text={quote(message)}")
    return {
        "ok": True,
        "drafted_not_sent": True,
        "note": "Opened WhatsApp with the message ready — hit send yourself.",
    }
