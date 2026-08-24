"""Calendar: read upcoming events from a live ICS feed, and add new ones.

Reading fetches CALENDAR_ICS_URL live (works with Google Calendar's "Secret
address in iCal format" and most other calendars' published ICS feeds) —
read-only, no credentials beyond that URL.

Adding an event doesn't write to the calendar directly (most providers require
a full OAuth flow for that, out of scope for v0); instead it builds a real
.ics file and opens it, which launches your default calendar app's "add
event" dialog for you to confirm — the same prepare-then-confirm pattern used
for reservations and email.
"""

import os
import tempfile
import urllib.request
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from icalendar import Calendar, Event

from sarmad import config


def check_calendar(days_ahead: int = 7) -> dict:
    if not config.CALENDAR_ICS_URL:
        return {"ok": False, "error": "No calendar configured. Set CALENDAR_ICS_URL in .env."}

    with urllib.request.urlopen(config.CALENDAR_ICS_URL, timeout=15) as resp:
        cal = Calendar.from_ical(resp.read())

    now = datetime.now().astimezone()
    horizon = now + timedelta(days=days_ahead)

    events = []
    for component in cal.walk("VEVENT"):
        start = component.decoded("dtstart")
        start_dt = start if isinstance(start, datetime) else datetime.combine(start, datetime.min.time())
        if start_dt.tzinfo is None:
            start_dt = start_dt.astimezone()

        if not (now <= start_dt <= horizon):
            continue

        events.append(
            {
                "title": str(component.get("summary", "")),
                "start": start_dt.isoformat(),
                "location": str(component.get("location", "")),
            }
        )

    events.sort(key=lambda e: e["start"])
    return {"ok": True, "events": events}


def add_calendar_event(title: str, start: str, end: str, description: str = "", location: str = "") -> dict:
    cal = Calendar()
    cal.add("prodid", "-//SARMAD//sarmad//")
    cal.add("version", "2.0")

    event = Event()
    event.add("summary", title)
    event.add("dtstart", datetime.fromisoformat(start))
    event.add("dtend", datetime.fromisoformat(end))
    event.add("uid", f"{uuid.uuid4()}@sarmad")
    if description:
        event.add("description", description)
    if location:
        event.add("location", location)
    cal.add_component(event)

    fd, path = tempfile.mkstemp(suffix=".ics")
    os.close(fd)
    Path(path).write_bytes(cal.to_ical())

    # os.startfile doesn't block, so the temp file is left in place rather
    # than deleted here — the calendar app needs to still be able to read it.
    os.startfile(path)

    return {
        "ok": True,
        "drafted_not_added": True,
        "note": "Opened an add-to-calendar dialog for you to confirm — SARMAD can't write to your calendar directly yet.",
    }
