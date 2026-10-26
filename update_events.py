"""Refresh Ticketmaster Winnipeg events and merge reviewed community listings.
Requires TICKETMASTER_API_KEY. Optional data/community_events.json contains
organizer-confirmed listings; no unapproved scraping or guessed free prices.
"""
import datetime as dt
import json
import os
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / 'data' / 'events.json'
COMMUNITY = ROOT / 'data' / 'community_events.json'
KEY = os.environ.get('TICKETMASTER_API_KEY', '').strip()
if not KEY:
    raise SystemExit('Missing TICKETMASTER_API_KEY; existing feed unchanged.')
now = dt.datetime.now(dt.timezone.utc)
today = now.date().isoformat()
records = {}
for page in range(3):
    query = urllib.parse.urlencode({
        'apikey': KEY, 'city': 'Winnipeg', 'countryCode': 'CA',
        'startDateTime': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'sort': 'date,asc', 'size': 100, 'page': page,
    })
    request = urllib.request.Request(
        'https://app.ticketmaster.com/discovery/v2/events.json?' + query,
        headers={'User-Agent': 'TownBuzzWinnipeg/1.1'})
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.load(response)
    events = payload.get('_embedded', {}).get('events', [])
    for event in events:
        venue = (event.get('_embedded', {}).get('venues') or [{}])[0]
        if venue.get('city', {}).get('name', '').casefold() != 'winnipeg':
            continue
        start = event.get('dates', {}).get('start', {})
        day = start.get('localDate')
        link = event.get('url', '')
        if not day or day < today or not link.startswith('https://'):
            continue
        classification = (event.get('classifications') or [{}])[0]
        segment = classification.get('segment', {}).get('name', '').casefold()
        genre = classification.get('genre', {}).get('name', '').casefold()
        category = 'music' if segment == 'music' else 'family' if 'family' in genre else 'date'
        identifier = str(event.get('id', link))
        records['ticketmaster:' + identifier] = {
            'id': identifier, 'title': event.get('name', 'Upcoming event')[:160],
            'date': day, 'time': start.get('localTime', '')[:5],
            'venue': venue.get('name', 'Winnipeg')[:140], 'category': category,
            'url': link, 'source': 'Ticketmaster',
            'price': 'Check organizer for pricing',
        }
    if len(events) < 100:
        break

# Community entries are manually reviewed or imported from sources with permission.
# They use the same public schema as Ticketmaster entries.
allowed_categories = {'free', 'market', 'food', 'music', 'family', 'date'}
community_count = 0
if COMMUNITY.exists():
    community_data = json.loads(COMMUNITY.read_text(encoding='utf-8'))
    for item in community_data.get('events', []):
        if not isinstance(item, dict):
            continue
        category = item.get('category', '')
        day = str(item.get('date', ''))
        url = str(item.get('url', ''))
        if category not in allowed_categories or day < today or not url.startswith('https://'):
            continue
        if category == 'free' and item.get('free_verified') is not True:
            continue
        if not item.get('title') or not item.get('venue') or not item.get('source'):
            continue
        event_id = str(item.get('id') or (day + ':' + url))
        records['community:' + event_id] = {
            'id': 'community:' + event_id,
            'title': str(item['title'])[:160], 'date': day,
            'time': str(item.get('time', ''))[:5],
            'venue': str(item['venue'])[:140], 'category': category,
            'url': url, 'source': str(item['source'])[:80],
            'price': 'Free admission (verified)' if category == 'free'
                     else str(item.get('price') or 'Check organizer for pricing')[:100],
        }
        community_count += 1

result = {'updated_at': now.isoformat(),
          'events': sorted(records.values(), key=lambda e: (e['date'], e['time'], e['title']))}
DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(f'Updated {len(records)} Winnipeg events ({community_count} reviewed community entries)')
