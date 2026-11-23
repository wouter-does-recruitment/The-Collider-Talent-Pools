# Dripify → The Collider dashboard (aggregate only)

This repository is **public**. Never commit API keys, candidate records, lead exports, messages,
LinkedIn URLs, email addresses, or raw Dripify responses.

## Implementation

- GitHub repository secret: `DRIPIFY_API_KEY`.
- Source: official Dripify Open API at `https://api.dripify.com/v1/open-api`.
- The script `scripts/sync_dripify.py` calls **GET** statistics for three explicitly
  approved campaign IDs only. It doesn't read or send messages.
- Output: `data/dripify-summary.json`, containing only approved labels, IDs, numeric
  aggregates, and the refresh timestamp. A failed request prevents any publication.
- The workflow runs every day at 06:20 UTC or manually from Actions.
- Dashboard: `dripify.html`, linked separately from the existing static dashboard.

## Activate

1. Review the pull request and the three campaign IDs/labels in the script.
2. Merge the PR into `main`.
3. Run **Actions → Dripify aggregate stats sync → Run workflow** on `main`.
4. Verify the workflow succeeded and inspect `data/dripify-summary.json`.
5. Open `https://wouter-does-recruitment.github.io/The-Collider-Talent-Pools/dripify.html`
   if GitHub Pages is configured for this repository.

If the workflow returns 401, check the secret. 403 may mean API plan/access restrictions.
404 may indicate API disabled or a campaign no longer accessible. If the GitHub Action
cannot push, check repository Settings → Actions → General → Workflow permissions.

## Privacy and interpretation

The API key grants broad privileges in Dripify even though this particular script only
uses GET requests. Keep the secret restricted and rotate it if exposed.
Statistics are campaign-level, potentially overlapping across campaigns. An accepted
connection is not equivalent to a qualified candidate; a reply is not necessarily positive.
For individual response classification, use a **private** datastore with a separate access
control design. Do not publish it to GitHub Pages.
