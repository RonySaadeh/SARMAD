"""Email: read recent inbox messages, and reply.

Reading is always live (IMAP). Replying defaults to opening a pre-filled draft
in your default mail app rather than sending — the same "prepare, you confirm"
pattern used for reservations. Set ENABLE_EMAIL_SEND=true in .env to let
SARMAD actually send via SMTP instead.
"""

import email as email_lib
import imaplib
import smtplib
import webbrowser
from email.header import decode_header
from email.message import EmailMessage
from urllib.parse import urlencode

from sarmad import config


def _decode_header_value(value: str) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    decoded = ""
    for text, charset in parts:
        decoded += text.decode(charset or "utf-8", errors="replace") if isinstance(text, bytes) else text
    return decoded


def _extract_snippet(msg: email_lib.message.Message, max_len: int = 200) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                return text.strip()[:max_len]
        return ""
    payload = msg.get_payload(decode=True)
    if payload is None:
        return ""
    return payload.decode(msg.get_content_charset() or "utf-8", errors="replace").strip()[:max_len]


def check_inbox(limit: int = 5, unread_only: bool = True) -> dict:
    if not (config.EMAIL_ADDRESS and config.EMAIL_APP_PASSWORD):
        return {"ok": False, "error": "Email isn't configured. Set EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env."}

    conn = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    try:
        conn.login(config.EMAIL_ADDRESS, config.EMAIL_APP_PASSWORD)
        conn.select("INBOX")
        _, data = conn.search(None, "UNSEEN" if unread_only else "ALL")
        ids = data[0].split()[-limit:]

        emails = []
        for eid in reversed(ids):
            _, msg_data = conn.fetch(eid, "(RFC822)")
            msg = email_lib.message_from_bytes(msg_data[0][1])
            emails.append(
                {
                    "id": eid.decode(),
                    "from": _decode_header_value(msg.get("From", "")),
                    "subject": _decode_header_value(msg.get("Subject", "")),
                    "snippet": _extract_snippet(msg),
                }
            )
        return {"ok": True, "emails": emails}
    finally:
        conn.logout()


def reply_email(to: str, subject: str, body: str) -> dict:
    if config.ENABLE_EMAIL_SEND:
        if not (config.EMAIL_ADDRESS and config.EMAIL_APP_PASSWORD):
            return {"ok": False, "error": "Email isn't configured. Set EMAIL_ADDRESS and EMAIL_APP_PASSWORD in .env."}
        msg = EmailMessage()
        msg["From"] = config.EMAIL_ADDRESS
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.EMAIL_ADDRESS, config.EMAIL_APP_PASSWORD)
            server.send_message(msg)
        return {"ok": True, "sent_to": to}

    params = urlencode({"subject": subject, "body": body})
    webbrowser.open(f"mailto:{to}?{params}")
    return {
        "ok": True,
        "drafted_not_sent": True,
        "note": (
            "Opened a draft in your email client instead of sending — set "
            "ENABLE_EMAIL_SEND=true in .env to let SARMAD send directly."
        ),
    }
