# Verified SEO and code fixes

This repository was checked against the supplied 12-item audit. The recommendations were not applied blindly.

## Applied

1. Replaced the broken remote `ssh-action` rsync command with runner-to-host rsync.
2. Removed the duplicate legacy `fetch_arbeitnow()` that called undefined `is_us_location()`.
3. Removed the homepage canonical from `404.html` and retained `noindex,follow`.
4. Added pre-rendered job links to the initial homepage HTML.
5. Added generated, dedicated `/jobs/*.html` detail pages with visible content and one valid `JobPosting` JSON-LD object per page.
6. Replaced SVG social previews with a 1200×630 PNG and complete OG metadata.
7. Corrected the Chinese characters accidentally embedded in the Arabic Twitter title.
8. Added reciprocal English, Arabic, and x-default hreflang annotations.
9. Added real `<lastmod>` fields and generated-job URLs to the sitemap.
10. Added Apache/LiteSpeed 410 responses for known inherited spam URL patterns.
11. Refined the Europe work-visa pages around the Search Console query cluster: stronger titles and descriptions, an explicit Schengen/work-authorisation explanation, country comparison links, accessible FAQ content, Article/Breadcrumb/FAQ structured data, and clearer job-search calls to action.
12. Added shared editorial-page styles so guide content, comparison tables, calls to action and FAQ panels are readable on desktop and mobile.

## Reviewed, but intentionally not applied as written

- **AdSense warning:** this is a policy/editorial recommendation, not a deterministic code bug. Manual ad slots are already empty and guarded by JavaScript. The site also has original guides plus About, Contact, Privacy, Terms, and Sources pages. Do not invent slot IDs. AdSense approval still cannot be guaranteed by code.
- **Downgrade `actions/checkout@v5` / `setup-python@v6`:** rejected. These are official stable releases, not experimental versions. Downgrading would be incorrect. GitHub-hosted `ubuntu-latest` runners satisfy their Node 24 runner requirement.
- **Netlify `_redirects` with `410!`:** not added because that syntax is not a portable/verified Netlify rule. `.htaccess` still contains Apache/LiteSpeed 410 rules for inherited spam URLs. Production is GitHub Pages (which ignores `.htaccess`); if a VPS or Cloudflare is used later, equivalent server-side rules must be configured there.

## Deployment

Production is **GitHub Pages** from `main` (`pages-build-deployment`). The old
rsync-to-host workflow (`.github/workflows/deploy.yml`) was removed: its
HOST / USERNAME / SITE_PATH / SSH_PRIVATE_KEY secrets were never configured,
so every push to `main` failed while Pages was already publishing the site.

If a VPS/rsync deploy is needed later, restore that workflow from git history
and set the secrets first — do not re-enable it empty.
