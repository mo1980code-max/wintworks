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

## Reviewed, but intentionally not applied as written

- **AdSense warning:** this is a policy/editorial recommendation, not a deterministic code bug. Manual ad slots are already empty and guarded by JavaScript. The site also has original guides plus About, Contact, Privacy, Terms, and Sources pages. Do not invent slot IDs. AdSense approval still cannot be guaranteed by code.
- **Downgrade `actions/checkout@v5` / `setup-python@v6`:** rejected. These are official stable releases, not experimental versions. Downgrading would be incorrect. GitHub-hosted `ubuntu-latest` runners satisfy their Node 24 runner requirement.
- **Netlify `_redirects` with `410!`:** not added because that syntax is not a portable/verified Netlify rule. The repository's SSH deployment is consistent with Apache/LiteSpeed hosting, so `.htaccess` contains the valid 410 rules. If production uses Nginx or Cloudflare instead, equivalent server-side rules must be configured there.

## Required deployment secret change

The deploy workflow now requires `SSH_PRIVATE_KEY` in GitHub Actions secrets. Remove the old password secret after a successful key-based deployment.
