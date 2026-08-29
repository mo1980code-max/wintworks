# WintWorks — Auto-filled USA & Europe Job Board

A complete, static, zero-maintenance job board for the **United States, Europe & remote markets**.
Jobs are fetched **automatically** from 5 free public sources (no API keys, no fees) — **The Muse · Jobicy · RemoteOK · Remotive · Arbeitnow (20 pages)** — plus an **Adzuna** API source covering 10 European markets + the US.
Every listing is auto-tagged **🇺🇸 USA / 🇪🇺 Europe / 🌍 Worldwide** with a region filter.

- Central job snapshot refreshed every six hours via GitHub Actions; no per-visitor API polling
- Region + **country** auto-detection (USA / available European markets / Worldwide), per-country dropdown filter
- **Adzuna** source: local-market jobs for GB/DE/FR/NL/IT/ES/PL/AT/BE/CH/US

### Adzuna keys (required for the Adzuna source)

Register free at [developer.adzuna.com](https://developer.adzuna.com), then add two **repository secrets** in
*Settings → Secrets and variables → Actions*:

- `ADZUNA_APP_ID` — your Adzuna App ID
- `ADZUNA_APP_KEY` — your Adzuna App Key

The `update-jobs` workflow passes them to `scripts/build_snapshot.py` as environment variables.
**Never commit real keys to the repository** — `data/adzuna.json` is git-ignored for this reason.
- Google AdSense Auto Ads connected to publisher `pub-`; Consent Mode defaults are denied
- AdSense-ready pages: About / Contact / Privacy / Terms
- Monetization extras: paid featured listings (`advertise.html`), free job posting form

## Deploy (free)

The live site at [wintworks.com](https://wintworks.com) is published automatically
via **GitHub Pages** from the `main` branch. No SSH host, rsync workflow, or
server secrets are required.

**GitHub Pages** (what production uses): Settings → Pages → deploy from `main`.
The included `.github/workflows/update-jobs.yml` re-fetches jobs every six hours;
`.github/workflows/update-scholarships.yml` refreshes scholarships daily.

**Netlify Drop** (optional alternative): drag this whole folder into https://app.netlify.com/drop

Then point your domain `wintworks.com` to the host.

### Optional extra scholarship APIs

Live listings already come from public WordPress sources (no keys). To enable
two additional free-tier APIs later, add these **repository secrets** in
*Settings → Secrets and variables → Actions*:

- `SCHOLARSHIPAPI_KEY` — ScholarshipAPI.com bearer token
- `SCHOLARSHIPS_COM_KEY` — Scholarships.com Parse API key

The `update-scholarships` workflow already passes them to
`scripts/fetch_scholarships.py`. Without the keys the workflow still succeeds
using WordPress sources plus seed data.

## After AdSense approval

1. In AdSense, open **Privacy & messaging** and enable Google’s certified European regulations CMP.
2. Enable Auto Ads for `wintworks.com`. The sitewide publisher tag and `ads.txt` are already installed.
3. If you later create manual ad units, add their real slot IDs in `js/app.js`; never use placeholder slot IDs.

## Local preview

```bash
python3 -m http.server 8080
# or: php -S localhost:8080
```

## Rebuild snapshot manually

```bash
python3 scripts/build_snapshot.py
```
