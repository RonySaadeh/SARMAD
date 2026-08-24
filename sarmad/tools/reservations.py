"""v0 reservation helper.

Real restaurants mostly have no public booking API, and driving a logged-in
browser session through a real booking flow unattended is a much bigger,
riskier project (credentials, CAPTCHAs, payment confirmation). For v0, SARMAD
prepares the reservation by opening a pre-filled OpenTable search so you land
one click from confirming, rather than silently booking on your behalf.
"""

import webbrowser
from urllib.parse import urlencode


def draft_reservation(restaurant: str, party_size: int, date: str, time: str, city: str = "") -> dict:
    query = restaurant if not city else f"{restaurant} {city}"
    params = {"term": query, "covers": party_size, "dateTime": f"{date}T{time}"}
    url = f"https://www.opentable.com/s?{urlencode(params)}"
    webbrowser.open(url)
    return {
        "ok": True,
        "url": url,
        "note": (
            f"Opened an OpenTable search for {restaurant} ({party_size} people, {date} {time}). "
            "Please confirm the actual booking yourself — SARMAD doesn't complete payments/logins yet."
        ),
    }
