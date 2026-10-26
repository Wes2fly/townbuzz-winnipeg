"""Update upcoming Winnipeg listings from Ticketmaster Discovery API.
Requires TICKETMASTER_API_KEY environment variable. No API key is shipped to browsers.
"""
import datetime as dt
import json
import os
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / 'data' / 'events.json'
KEY = os.environ.get('TICKETMASTER_API_KEY', '').strip()
if not KEY:
    raise SystemExit('Missing TICKETMASTER_API_KEY; keeping existing event data.')
now = dt.datetime.now(dt.timezone.utc)
records = {}
for page in range(3):
    query = urllib.parse.urlencode({
        'apikey': KEY, 'city': 'Winnipeg', 'countryCode': 'CA',
        'startDateTime': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'sort': 'date,asc', 'size': 100, 'page': page,
    })
    req = urllib.request.Request('https://app.ticketmaster.com/discovery/v2/events.json?' + query,
                                 headers={'User-Agent': 'WinnipegDealsEvents/1.0'})
    with urllib.request.urlopen(req, timeout=25) as response:
        payload = json.load(response)
    events = payload.get('_embedded', {}).get('events', [])
    for event in events:
        venue = (event.get('_embedded', {}).get('venues') or [{}])[0]
        if venue.get('city', {}).get('name', '').casefold() != 'winnipeg':
            continue
        start = event.get('dates', {}).get('start', {})
        day = start.get('localDate')
        if not day or day < now.date().isoformat():
            continue
        link = event.get('url', '')
        if not link.startswith('https://'):
            continue
        segment = (event.get('classifications') or [{}])[0].get('segment', {}).get('name', '')
        genre = (event.get('classifications') or [{}])[0].get('genre', {}).get('name', '')
        category = 'music' if segment.casefold() == 'music' else 'family' if 'family' in genre.casefold() else 'date'
        records[event['id']] = {
            'id': event['id'], 'title': event.get('name', 'Upcoming event')[:160],
            'date': day, 'time': start.get('localTime', '')[:5],
            'venue': venue.get('name', 'Winnipeg')[:140], 'category': category,
            'url': link, 'source': 'Ticketmaster', 'price': 'Check organizer for pricing',
        }
    if len(events) < 100:
        break
result = {'updated_at': now.isoformat(), 'events': sorted(records.values(), key=lambda e: (e['date'], e['time']))}
DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(f'Updated {len(records)} Winnipeg events')
