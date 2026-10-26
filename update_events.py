"""Refresh Winnipeg Ticketmaster events and merge verified community listings."""
import datetime as dt
import json
import os
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / "data" / "events.json"
COMMUNITY = ROOT / "data" / "community_events.json"
KEY = os.environ.get("TICKETMASTER_API_KEY", "").strip()

if not KEY:
    raise SystemExit("Missing TICKETMASTER_API_KEY; existing feed preserved.")

now = dt.datetime.now(dt.timezone.utc)
today = now.date().isoformat()
records = {}

def valid_url(url):
    return isinstance(url, str) and url.startswith("https://")

def category_for(event):
    classifications = event.get("classifications") or [{}]
    classification = classifications[0]
    segment = (classification.get("segment") or {}).get("name", "").lower()
    genre = (classification.get("genre") or {}).get("name", "").lower()
    if segment == "music":
        return "music"
    if "family" in genre:
        return "family"
    return "date"

# Fetch Ticketmaster listings.
for page in range(3):
    query = urllib.parse.urlencode({
        "apikey": KEY,
        "city": "Winnipeg",
        "countryCode": "CA",
        "startDateTime": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sort": "date,asc",
        "size": 100,
        "page": page,
    })
    request = urllib.request.Request(
        "https://app.ticketmaster.com/discovery/v2/events.json?" + query,
        headers={"User-Agent": "TownBuzzWinnipeg/1.1"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    events = payload.get("_embedded", {}).get("events", [])
    for event in events:
        venue = (event.get("_embedded", {}).get("venues") or [{}])[0]
        city = (venue.get("city") or {}).get("name", "")
        if city.casefold() != "winnipeg":
            continue

        start = (event.get("dates") or {}).get("start") or {}
        day = start.get("localDate", "")
        url = event.get("url", "")
        if day < today or not valid_url(url):
            continue

        event_id = event.get("id")
        if not event_id:
            continue

        records["tm:" + event_id] = {
            "id": "tm:" + event_id,
            "title": event.get("name", "Upcoming event")[:160],
            "date": day,
            "time": start.get("localTime", "")[:5],
            "venue": venue.get("name", "Winnipeg")[:140],
            "category": category_for(event),
            "url": url,
            "source": "Ticketmaster",
            "price": "Check organizer for pricing",
        }

    if len(events) < 100:
        break

# Add reviewed community listings.
allowed_categories = {"free", "market", "food", "music", "family", "date"}
if COMMUNITY.exists():
    community_data = json.loads(COMMUNITY.read_text(encoding="utf-8"))
    for event in community_data.get("events", []):
        if not isinstance(event, dict):
            continue
        day = str(event.get("date", ""))
        url = event.get("url", "")
        category = event.get("category", "")
        if day < today or not valid_url(url):
            continue
        if category not in allowed_categories:
            continue
        if not event.get("verified", False):
            continue
        if category == "free" and event.get("free_admission") is not True:
            continue

        event_id = str(event.get("id", "")).strip()
        if not event_id:
            continue

        records["community:" + event_id] = {
            "id": "community:" + event_id,
            "title": str(event.get("title", "Community event"))[:160],
            "date": day,
            "time": str(event.get("time", ""))[:5],
            "venue": str(event.get("venue", "Winnipeg"))[:140],
            "category": category,
            "url": url,
            "source": str(event.get("source", "Community organizer"))[:80],
            "price": (
                "Free admission"
                if event.get("free_admission") is True
                else "Check organizer for pricing"
            ),
        }

result = {
    "updated_at": now.isoformat(),
    "events": sorted(
        records.values(),
        key=lambda event: (event["date"], event["time"])
    ),
}
DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(
    json.dumps(result, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(
    f"Updated {len(records)} Winnipeg events "
    f"({sum(k.startswith('community:') for k in records)} community)"
)
