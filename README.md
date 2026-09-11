# WintWorks — Auto-filled USA & Europe Job Board

A complete, static, zero-maintenance job board for the **United States, Europe & remote markets**.
Jobs are fetched **automatically** from 5 free public sources (no API keys, no fees) — **The Muse · Jobicy · RemoteOK · Remotive · Arbeitnow (20 pages)** — plus an **Adzuna** API source covering 10 European markets + the US.
Every listing is auto-tagged **🇺🇸 USA / 🇪🇺 Europe / 🌍 Worldwide** with a region filter.

- Central job snapshot refreshed **every three hours** via GitHub Actions; no per-visitor API polling
- Snapshot URL is version-stamped (`data/jobs.json?v=…`) and the on-page **⟳ Check for new jobs**
  button re-fetches with `no-store`, so no CDN or browser cache can pin yesterday's list
- "Latest jobs" shows the real crawl time (`Updated 12m ago · 1 800 jobs from 6 sources`) plus
  one status pill per source, so freshness is visible instead of assumed
- Region + **country** auto-detection (USA / available European markets / Worldwide), per-country dropdown filter
- **Adzuna** source: local-market jobs for GB/DE/FR/NL/IT/ES/PL/AT/BE/CH/US
- Google AdSense Auto Ads connected to publisher `pub-`; Consent Mode defaults are denied
- AdSense-ready pages: About / Contact / Privacy / Terms
- Monetization extras: paid featured listings (`advertise.html`), free job posting form

## Data freshness — how the update works

```
GitHub Actions (cron 17 */3 * * *)
  └─ scripts/build_snapshot.py         fetch → normalise dates → dedupe → fair trim → data/jobs.json
      └─ scripts/generate_static_jobs.py  jobs/*.html + pre-rendered home links + sitemap.xml
  └─ npm run build:min                 rebuild js/app.min.js (the bundle index.html actually loads)
  └─ commit + push → GitHub Pages deploys
```

### Guardrails (added 2026-09-11, when "the site does not update jobs" was reported)

The cron job was running and committing on time — the board still looked frozen, because of
three defects in the pipeline. They are fixed and covered by `test_snapshot_update.py`:

1. **Mixed date formats + a lexical sort.** Six sources emit `'…Z'`, `'+00:00'`, naive, unix
   seconds and RFC-2822 timestamps. `sorted(...)[:1800]` over those strings is not date order,
   so whole sources vanished on every run (The Muse 96 → 3, RemoteOK 37 → 1, Remotive 16 → 1)
   and visitors filtering 🇺🇸 USA or 🌍 Worldwide kept seeing the same list. Every date is now
   normalised to aware UTC (`parse_date_utc`) and the trim sorts on real instants.
2. **One big feed ate the whole snapshot.** `select_jobs()` now gives any single source at most
   `WW_SOURCE_MAX_SHARE` (50 %) of the snapshot; small feeds are preserved in full and leftover
   slots are still filled newest-first.
3. **A failed crawl used to empty the site.** If a source errors, the run continues with the rest.
   If the *total* collapses (below `WW_MIN_JOBS`, or below 60 % of the published snapshot) the
   builder **refuses to write**, exits non-zero and leaves the last good `data/jobs.json` live.
   The workflow additionally refuses to publish a snapshot with < 200 jobs, < 3 sources or a
   `generated_at` older than 1 h, and writes atomically (`jobs.json.tmp` → `os.replace`).

Also fixed the same day: the client fetched `data/jobs.json` with a bare `fetch()` (CDN + browser
cache could answer with an old copy), nothing revalidated `data/jobs.json` while a tab stayed
open, `js/app.min.js` was never rebuilt by CI (a stale bundle could ship old logic on top of new
data), and `Adzuna.created` — market-local time mislabelled as UTC — pinned that source ~2 h in
the future (`align_future_dates` shifts the batch back by its own skew).

Tunables for `scripts/build_snapshot.py` (all optional, via environment):

| Variable | Default | Meaning |
| --- | --- | --- |
| `WW_MAX_JOBS` | `1800` | size of the published snapshot |
| `WW_SOURCE_MAX_SHARE` | `0.5` | largest share one source may own |
| `WW_MIN_JOBS` | `250` | refuse to publish below this many jobs |
| `WW_SHRINK_RATIO` | `0.6` | refuse to publish below this fraction of the live snapshot |
| `WW_ALLOW_SHRINK` | `0` | `1` bypasses both guards (only after a confirmed source outage) |

### Adzuna keys (required for the Adzuna source)

Register free at [developer.adzuna.com](https://developer.adzuna.com), then add two **repository secrets** in
*Settings → Secrets and variables → Actions*:

- `ADZUNA_APP_ID` — your Adzuna App ID
- `ADZUNA_APP_KEY` — your Adzuna App Key

The `update-jobs` workflow passes them to `scripts/build_snapshot.py` as environment variables.
Without them the run still succeeds; it just prints a warning and skips the Adzuna markets.

> ⚠️ **Action required — the previous keys are burned.** `data/adzuna.json` was committed with real
> credentials in it (despite being listed in `.gitignore`) and is public in the repository history.
> It is untracked as of 2026-09-11, but that does not un-leak it. Rotate:
>
> 1. developer.adzuna.com → your app → **regenerate / create a new App Key** (the App ID may stay).
> 2. Store the new pair as the two repository secrets above — never in a file that is committed.
> 3. For local runs only, create `data/adzuna.json` from `data/adzuna.json.example`; it stays ignored.
>    Alternatively export `ADZUNA_ID` / `ADZUNA_KEY` in your shell.
> 4. Run *Actions → Auto-update jobs → Run workflow* and confirm the log prints `Adzuna: 550 jobs`.
> 5. Optional cleanup: purge the old blob from history (`git filter-repo` + force-push) if you
>    restructure the repo — treat the leaked key as revoked regardless.

## SEO, internal linking & Core Web Vitals

`scripts/seo_audit.py` walks every HTML page (root pages + `jobs/*.html`), the
sitemap, robots.txt and the asset sizes, and reports findings grouped by
severity. It exits non-zero on ERROR, so it is a build gate:

```bash
npm run seo:audit              # grouped human report
python3 scripts/seo_audit.py --all --json seo-report.json   # every page + machine-readable
```

What it checks: `<title>`/meta-description length, canonical correctness,
single `<h1>`, heading order, Open Graph / Twitter cards, JSON-LD validity with
per-@type required fields (Article, FAQPage, JobPosting, BreadcrumbList,
CollectionPage, WebApplication …) **including `@id` cross-references**, broken
internal links, orphan pages, click depth from the homepage, weak inbound-link
pages, sitemap ↔ file mismatches, duplicate titles/descriptions, image
alt/width/height/decoding, and Core-Web-Vitals smells (render-blocking
third-party scripts, runtime CSS compilers, missing preconnects, >200 KB
images).

`.github/workflows/seo-audit.yml` runs the suite plus this audit on every pull
request, uploads the JSON report and fails if `css/tailwind.min.css` is stale.

### What the audit found and what was fixed (2026-09-11)

| Finding | Fix |
| --- | --- |
| 15 `<title>`s over the ~60-character SERP window, 3 descriptions over 160 | titles/descriptions rewritten (the reviewed-guide generator `scripts/update_guides.py` was updated too, so a re-run cannot reintroduce them) |
| `cv-builder.html` loaded the **Tailwind Play CDN** (~400 KB of JS, compiled in the browser after paint) | pre-built, purged `css/tailwind.min.css` (≈13 KB) via `npm run build:css`; `test_tailwind_build.py` fails if the page and the build drift apart |
| every page declared `Organization`/`WebSite` inconsistently; 10 pages had no structured data at all; breadcrumbs had no schema | one shared vocabulary in `scripts/schema_kit.py` (stable `@id`s, publisher logo, `datePublished`), `WebPage`/`AboutPage`/`ContactPage`/`CollectionPage`/`WebApplication` nodes, `BreadcrumbList` generated from the visible breadcrumb |
| `scholarships.html` had **1 inbound internal link**, `guides-eu-visa-routes.html` had 2 | footer link sitewide, guides-hub card, and contextual "Related guides" blocks on 9 guide pages |
| job pages were generate-once dead ends | each job page now links to its country guide, the scam guide and the visa comparison |
| `JobPosting` had no `validThrough`/`employmentType`; job titles ran to 65 characters | rolling `validThrough` (+45 days), inferred `employmentType`, 60-character title budget in `scripts/generate_static_jobs.py` |
| `cv-builder.html` had no Open Graph/Twitter tags; AdSense had no preconnect; a logo `<img>` had no `decoding` | all added |
| sitemap omitted `cv-builder.html` and `disclaimer.html` | both added |


## Deploy (free)

The live site at [wintworks.com](https://wintworks.com) is published automatically
via **GitHub Pages** from the `main` branch. No SSH host, rsync workflow, or
server secrets are required.

**GitHub Pages** (what production uses): Settings → Pages → deploy from `main`.
The included `.github/workflows/update-jobs.yml` re-fetches jobs every three hours;
`.github/workflows/update-scholarships.yml` refreshes scholarships daily.

**Netlify Drop** (optional alternative): drag this whole folder into https://app.netlify.com/drop

Then point your domain `wintworks.com` to the host.

> GitHub Pages ignores `.htaccess` (it is only for the legacy Apache host) and does not let you set
> `Cache-Control` for `data/jobs.json`. That is why freshness is handled with a versioned URL plus
> `no-store` on the manual refresh instead of response headers.

### WordPress sources (ScholarshipsCorner, Scholars4Dev, OpportunitiesForYouth)

These sites expose `/wp-json/wp/v2/posts`, so no key or scraping is needed.
The parser was hardened on 2026-09-11 after measuring the live
ScholarshipsCorner feed (82 rows):

| Problem | Fix |
| --- | --- |
| 60/82 rows had an empty `location`; a few carried prose fragments such as `"America's best institutions which they would not b"` | the host country is resolved against a country table (`COUNTRY_ALIASES`, aliases like `UK`, `U.S.A`, `Türkiye` included) and read from the `Host Country:` / `Study in:` block these sites publish — free prose can no longer become a location |
| `"… in UK"` posts were region-less because the region word list had no short form | short forms added; every EU/Arab country name is now an automatic alias |
| 44/82 rows had no `deadline` (the date was only searched in the first 6 000 characters, ±140 characters around a keyword) | the whole body is scanned, the window follows the keyword (a "closing date" block no longer picks up an earlier "apply from" date), candidates are scored so `deadline`/`closing date`/`last date`/`apply by` beat a passing mention, and only future dates win |
| non-EU/US/Arab destinations (Japan, Canada, Cambodia …) vanished from the country filter | any named host country is kept in `country`, even when its region stays untagged |

Regression coverage for all of the above lives in `test_wp_sources.py`
(66 checks, fixtures mirroring real posts).


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
   Always rebuild the bundle afterwards — `index.html` loads `js/app.min.js`, not `js/app.js`:

   ```bash
   npm ci && npm run build:min
   ```

## Local preview

```bash
python3 -m http.server 8080
# or: php -S localhost:8080
```

## Rebuild snapshot manually

```bash
python3 scripts/build_snapshot.py     # or: npm run snapshot
npm run build:css                     # rebuild css/tailwind.min.css after editing cv-builder.html
npm test                              # sitemap + snapshot + scholarships + Tailwind + SEO audit + front-end tests
```

To force the live site to re-crawl right now: **Actions → Auto-update jobs → Run workflow**
(`workflow_dispatch`). Tick *allow_shrink* only if a source outage legitimately shrank the board and
you still want the smaller snapshot published.
