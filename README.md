# TownBuzz Winnipeg — automatic event feed

This site automatically refreshes **Ticketmaster-listed events in Winnipeg** about every six hours after setup. It does **not** automatically find all free events, markets, restaurant deals, or every local event. Those require additional approved sources or business submissions. Pricing is never inferred to be free.

## Setup (one time)
Create a public GitHub repository named `townbuzz-winnipeg`. Upload the **contents of this folder**, not the enclosing folder, so `index.html` is in the repository root.
1. Create a free GitHub account and a new repository. Upload all files, including the `.github/workflows/update-events.yml` folder.
2. Request a Ticketmaster Discovery API key from the Ticketmaster developer portal (developer.ticketmaster.com). Approval/limits depend on Ticketmaster.
3. In your repository, go to **Settings → Secrets and variables → Actions → New repository secret**. Name it `TICKETMASTER_API_KEY` and paste your key. Do not put the key in the HTML or commit it.
4. In **Actions**, open **Refresh Winnipeg events**, enable workflows if prompted, and click **Run workflow**. The script writes `data/events.json` and commits the results. GitHub Actions must have permission to write repository contents (Settings → Actions → General → Workflow permissions: Read and write permissions), or configure an alternative deployment method.
5. Publish the repository with **GitHub Pages** (Settings → Pages → Deploy from a branch → main / root). Wait for the first workflow to finish. The site reads `data/events.json` when visitors open it.
6. Check the published URL. The refresh runs on GitHub's schedule, which can be delayed. If the API fails, the previous feed remains; the site may show outdated refresh time, and expired events are hidden in the browser.

## Local preview
A browser opened directly on `index.html` may block reading the JSON file. From this folder run `python -m http.server 8000` and visit `http://localhost:8000`. Until a real feed is fetched, no live event cards will appear.

## Before taking payments
- Add a real business contact method, privacy policy, and newsletter service with consent and unsubscribe handling. Current forms are demonstrations and do not send or store data.
- Verify listing and attribution requirements for every event source; do not scrape sites against their terms.
- Mark all sponsored placements clearly. Sell advertising only after measuring actual traffic.
- Consider adding approved municipal/community feeds and direct business submissions to cover free events and markets. Ticketmaster alone is incomplete.

## Safety and maintenance
The API key stays in GitHub Secrets; browser code sees only the public generated JSON. Event titles are inserted as text, not HTML. Links open the original organizer/Ticketmaster page. Check GitHub Actions logs when refreshes fail.
