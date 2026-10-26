import json
import os
import pathlib
import hashlib
import sys
from datetime import datetime, date, time, timedelta, timezone
from urllib.parse import urlparse

import requests
from icalendar import Calendar

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "data" / "library_candidates.json"
FEED_URL = os.environ.get("WPL_ICAL_URL", "").strip()

ALLOWED_HOSTS = {"wpl.libcal.com", "api3.libcal.com"}


def valid_url(url):
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme == "https"
            and parsed.hostname in ALLOWED_HOSTS
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


def event_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    return None


def text_value(event, key, default=""):
    value = event.get(key)
    return str(value).strip() if value is not None else default


def main():
    if not FEED_URL:
        print("WPL_ICAL_URL is not configured.")
        print("No library events were collected.")
        print("Existing event files remain unchanged.")
        return

    if not valid_url(FEED_URL):
        sys.exit("Invalid library calendar feed URL.")

    response = requests.get(
        FEED_URL,
        timeout=25,
        headers={"User-Agent": "TownBuzzWinnipeg/1.0"}
    )
    response.raise_for_status()

    if not response.text.lstrip().startswith("BEGIN:VCALENDAR"):
        sys.exit("The supplied URL did not return an iCal calendar.")

    calendar = Calendar.from_ical(response.content)
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=90)
    candidates = []
    seen = set()

    for event in calendar.walk("VEVENT"):
        start_field = event.get("DTSTART")
        if not start_field:
            continue

        start = event_datetime(start_field.dt)
        if start is None:
            continue

        if start.tzinfo is None:
            from zoneinfo import ZoneInfo
            start = start.replace(tzinfo=ZoneInfo("America/Winnipeg"))

        start_utc = start.astimezone(timezone.utc)

        if not (now <= start_utc <= cutoff):
            continue

        status = text_value(event, "STATUS").upper()
        if status == "CANCELLED":
            continue

        title = text_value(event, "SUMMARY")
        if not title:
            continue

        uid = text_value(event, "UID", title)
        key = uid + "|" + start_utc.isoformat()
        event_id = hashlib.sha256(key.encode()).hexdigest()[:20]

        if event_id in seen:
            continue
        seen.add(event_id)

        event_url = text_value(event, "URL")
        if event_url and not event_url.startswith("https://"):
            event_url = ""

        local_start = start_utc.astimezone(
            __import__("zoneinfo").ZoneInfo("America/Winnipeg")
        )

        candidates.append({
            "id": "wpl-" + event_id,
            "title": title[:160],
            "date": local_start.date().isoformat(),
            "time": local_start.strftime("%H:%M"),
            "venue": text_value(event, "LOCATION")[:140],
            "description": text_value(event, "DESCRIPTION")[:500],
            "url": event_url,
            "source": "Winnipeg Public Library",
            "status": "needs_review",
            "verified": False,
            "free_admission": None,
            "registration_required": None
        })

    candidates.sort(key=lambda e: (e["date"], e["time"]))

    DEST.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "updated_at": now.isoformat(),
        "source": "Winnipeg Public Library iCal",
        "publication_status": "review_only",
        "events": candidates
    }

    DEST.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    print(f"Saved {len(candidates)} library candidates.")
    print("No live TownBuzz event listings were modified.")


if __name__ == "__main__":
    main()
