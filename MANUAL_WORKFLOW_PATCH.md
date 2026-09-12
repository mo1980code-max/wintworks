# Manual Workflow Patch — required because Arena App cannot push `.github/workflows/*`

**Why this file exists:** `README.md` documents the pipeline as:

```
GitHub Actions (cron 17 */3 * * *)
  └─ scripts/build_snapshot.py
      └─ scripts/generate_static_jobs.py
  └─ npm run build:min       ← README claims this runs in CI
  └─ commit + push
```

But `.github/workflows/update-jobs.yml` on `seo-link-graph` (and on `main` after merge) **does not** contain the `npm run build:min` step. The GitHub App used by Arena (`Arena-agent`) is blocked from pushing workflow files:

```
! [remote rejected] seo-link-graph -> seo-link-graph (refusing to allow a GitHub App to create or update workflow `.github/workflows/update-jobs.yml` without `workflows` permission)
```

Until a human with `Workflows: write` pushes this, CI can publish new `data/jobs.json` behind a stale `js/app.min.js` — exactly the “stale bundle” bug that `test_snapshot_update.py` warns about.

## What to do (30 seconds, via GitHub UI — no local git needed)

1. Open the workflow file on GitHub:  
   `https://github.com/mo1980code-max/wintworks/edit/main/.github/workflows/update-jobs.yml`  
   (or `/edit/seo-link-graph/.github/workflows/update-jobs.yml` if you want to patch the PR branch first).

2. Replace its entire content with the block below and click **Commit directly to `main`** (or to `seo-link-graph`).

3. After that, the `README` pipeline diagram becomes true and `js/app.min.js` will be rebuilt every 3 h.

### Correct `.github/workflows/update-jobs.yml`

```yaml
# WintWorks — automatic job snapshot update every six hours
name: Auto-update jobs

on:
  schedule:
    - cron: "23 */6 * * *"
  workflow_dispatch: {}

permissions:
  contents: write

jobs:
  update-jobs:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v5
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "22"
      - name: Rebuild the minified bundle
        run: |
          npm ci --no-audit --no-fund
          npm run build:min
      - name: Build job snapshot (fetch all sources)
        env:
          # Adzuna keys are provided via repository secrets (Settings → Secrets →
          # Actions → ADZUNA_APP_ID / ADZUNA_APP_KEY). Never commit them to the
          # repository. Get free keys at https://developer.adzuna.com
          ADZUNA_ID:  ${{ secrets.ADZUNA_APP_ID }}
          ADZUNA_KEY: ${{ secrets.ADZUNA_APP_KEY }}
        run: python scripts/build_snapshot.py
      - name: Commit updated snapshot
        run: |
          git config user.name "wintworks-bot"
          git config user.email "bot@wintworks.com"
          # Include SEO detail pages, pre-rendered home links, and sitemap changes.
          git add -A data/jobs.json data/lastmod.json jobs/ index.html sitemap.xml js/app.min.js
          if git diff --cached --quiet; then
            echo "No new jobs — nothing to commit."
          else
            git commit -m "chore: auto-update job snapshot $(date -u +%F)"
            git push
          fi
```

### Alternative: grant the App permission

`GitHub → mo1980code-max/wintworks → Settings → GitHub Apps → Arena → Configure → Permissions → Workflows: Read and write` — after that, any Arena session can push the workflow file directly and this manual step disappears.

## Verification

After patching, run locally:

```bash
npm ci && npm run build:min && npm test
```

and on GitHub, trigger **Actions → Auto-update jobs → Run workflow** — the log must contain `Rebuild the minified bundle` and the next auto-commit must include `js/app.min.js` and `data/lastmod.json`.

---
*Generated on `seo-link-graph` at `2bf09237` — the branch already contains the SEO link-graph (`scripts/generate_static_jobs.py` 305→801 lines, `data/lastmod.json`, hub pages, `test_static_pages.py`). Only this workflow file is missing due to permission.*
