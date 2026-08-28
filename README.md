# WintWorks — Auto-filled USA & Europe Job Board

A complete, static, zero-maintenance job board for the **United States, Europe & remote markets**.
Jobs are fetched **automatically** from 5 free public sources (no API keys, no fees) — **The Muse · Jobicy · RemoteOK · Remotive · Arbeitnow (20 pages)** — plus an **Adzuna** API source covering 10 European markets + the US.
Every listing is auto-tagged **🇺🇸 USA / 🇪🇺 Europe / 🌍 Worldwide** with a region filter.

- Central job snapshot refreshed every six hours via GitHub Actions; no per-visitor API polling
- Region + **country** auto-detection (USA / available European markets / Worldwide), per-country dropdown filter
- **Adzuna** source: local-market jobs for GB/DE/FR/NL/IT/ES/PL/AT/BE/CH/US
- Google AdSense Auto Ads connected to publisher `pub-`; Consent Mode defaults are denied
- AdSense-ready pages: About / Contact / Privacy / Terms
- Monetization extras: paid featured listings (`advertise.html`), free job posting form

## Deploy (free)

**Netlify Drop** (easiest): drag this whole folder into https://app.netlify.com/drop

**GitHub Pages**: push this folder to a repo → Settings → Pages → deploy from `main` branch.
The included `.github/workflows/update-jobs.yml` re-fetches jobs every day automatically.

Then point your domain `wintworks.com` to the host (Netlify shows you the DNS records).

**User guide (Arabic): see `README-AR.md`.**

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
