# WintWorks — Auto-filled USA & Europe Job Board

A complete, static, zero-maintenance job board for the **United States & Europe**.
Jobs are fetched **automatically** from 5 free public sources (no API keys, no fees) — **The Muse · Jobicy · RemoteOK · Remotive · Arbeitnow (20 pages)** — plus an optional free **Adzuna** source covering 10 European markets + the US.
Every listing is auto-tagged **🇺🇸 USA / 🇪🇺 Europe / 🌍 Worldwide** with a region filter.

- Auto-refresh in the browser every 20 minutes + daily snapshot via GitHub Actions
- Region + **country** auto-detection (USA / all of Europe / Worldwide — 40+ countries), per-country dropdown filter
- Optional **Adzuna** source (free key at developer.adzuna.com): adds local jobs for GB/DE/FR/NL/IT/ES/PL/AT/BE/CH/US
- 3 Google AdSense slots ready (edit `js/app.js` → `CONFIG.adsenseClient`)
- AdSense-ready pages: About / Contact / Privacy / Terms
- Monetization extras: paid featured listings (`advertise.html`), free job posting form

## Deploy (free)

**Netlify Drop** (easiest): drag this whole folder into https://app.netlify.com/drop

**GitHub Pages**: push this folder to a repo → Settings → Pages → deploy from `main` branch.
The included `.github/workflows/update-jobs.yml` re-fetches jobs every day automatically.

Then point your domain `wintworks.com` to the host (Netlify shows you the DNS records).

**User guide (Arabic): see `README-AR.md`.**

## After AdSense approval

1. Open `js/app.js` → set `adsenseClient: "ca-pub-XXXX…"` and your ad slot IDs in `adSlots`.
2. Deploy again. Ad slots appear automatically (top of list, in-feed, job detail).

## Local preview

```bash
python3 -m http.server 8080
# or: php -S localhost:8080
```

## Rebuild snapshot manually

```bash
python3 scripts/build_snapshot.py
```
