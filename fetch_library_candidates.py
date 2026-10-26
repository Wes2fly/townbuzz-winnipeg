"""Fetch Winnipeg Public Library iCal into a REVIEW-ONLY queue.
Does not modify data/events.json or data/community_events.json.
"""
import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'library_candidates.json'
URL = os.environ.get('WPL_ICAL_URL', '').strip()
if not URL:
    print('No WPL_ICAL_URL configured. No changes made.')
    raise SystemExit(0)
parsed = urlparse(URL)
if parsed.scheme != 'https' or parsed.hostname not in ('wpl.libcal.com', 'api3.libcal.com'):
    raise SystemExit('Feed URL must be an HTTPS Winnipeg Public Library LibCal feed.')
with urlopen(Request(URL, headers={'User-Agent':'TownBuzzWinnipeg/1.0 (library calendar review)'}), timeout=25) as resp:
    raw = resp.read(3_000_001)
if len(raw) > 3_000_000:
    raise SystemExit('Feed too large')
calendar = Calendar.from_ical(raw)
now = dt.datetime.now(ZoneInfo('America/Winnipeg'))
cutoff = now.date() + dt.timedelta(days=45)
rows = {}
for item in calendar.walk('VEVENT'):
    start = item.get('DTSTART')
    if not start:
        continue
    val = start.dt
    if isinstance(val, dt.datetime):
        local = val.replace(tzinfo=ZoneInfo('America/Winnipeg')) if val.tzinfo is None else val.astimezone(ZoneInfo('America/Winnipeg'))
        date, time = local.date(), local.strftime('%H:%M')
    else:
        date, time = val, ''
    if not (now.date() <= date <= cutoff):
        continue
    title = str(item.get('SUMMARY','')).strip()[:160]
    if not title:
        continue
    uid = str(item.get('UID',title+str(date)))[:180]
    url = str(item.get('URL','')).strip()
    if not (url.startswith('https://wpl.libcal.com/') or url.startswith('https://www.winnipeg.ca/')):
        url = 'https://wpl.libcal.com/calendar/main/'
    rows[uid+'|'+date.isoformat()] = {
        'id': 'wpl-' + __import__('hashlib').sha256((uid+'|'+date.isoformat()).encode()).hexdigest()[:16],
        'title': title, 'date': date.isoformat(), 'time': time,
        'venue': str(item.get('LOCATION','Winnipeg Public Library'))[:140],
        'url': url, 'source': 'Winnipeg Public Library',
        'category': 'free', 'free_admission': True,
        'verified': False, 'review_status': 'pending',
        'notes': 'Review event link, venue, registration and reuse permission before publishing.'
    }
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({'checked_at':now.isoformat(),'candidates':sorted(rows.values(), key=lambda x:(x['date'],x['time']))},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(f'Saved {len(rows)} review-only library candidates; public event feed untouched.')
