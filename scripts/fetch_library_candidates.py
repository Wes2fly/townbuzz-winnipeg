# TownBuzz Winnipeg — Winnipeg Public Library candidate importer

## What it does
Fetches an approved Winnipeg Public Library iCal feed daily into `data/library_candidates.json` for **human review only**. It **never** edits `data/events.json`, `data/community_events.json`, `index.html`, `update_events.py`, or the existing Ticketmaster workflow. No new events appear publicly until reviewed and manually added to `data/community_events.json`.

## Before activating
1. Request/confirm permission from Winnipeg Public Library / the calendar owner for reusing event metadata on a commercial/sponsored directory. An iCal subscription link being public does **not** establish republication rights. Until permission is confirmed, leave the feed secret unset and use the library calendar as an outbound link instead.
2. Visit https://wpl.libcal.com/calendar/main/ and use the **iCal** subscription feature. Copy the *actual* HTTPS iCal URL, not the calendar webpage URL. The script accepts only `wpl.libcal.com` or `api3.libcal.com` hosts.
3. In GitHub repo Settings > Secrets and variables > Actions, create `WPL_ICAL_URL` with that URL. Do not paste it into public files. Some calendar URLs may contain access tokens.

## Install on iPhone
1. Unzip this archive in Files.
2. In your GitHub repository, use Add file > Upload files (or create files individually) and put these exact paths in place: `scripts/fetch_library_candidates.py`, `.github/workflows/library-candidates.yml`, `data/library_candidates.json`.
3. Commit the changes to `main`.
4. After permissions and URL setup, open Actions > Discover Library Event Candidates > Run workflow.
5. Inspect `data/library_candidates.json` and workflow logs. If candidates are found, check event page, date, branch, free status, registration requirements and permission. Copy reviewed items into `data/community_events.json`, setting `verified: true`, then run existing Update TownBuzz Events workflow.

## Limitations
- Some feeds expose only a limited time window; recurrence exceptions, cancellations and registration availability need checking.
- This is a review queue, **not** an auto-publisher. The existing public feed remains unchanged.
- GitHub scheduled runs can be delayed and sometimes disabled for inactive repositories.
- A public feed may be suitable for calendar subscription but not commercial republication; obtain approval before using it to populate a commercial site.
