# WintWorks search launch checklist

Code-side SEO is complete: canonical URLs, sitemap, robots.txt and a noindex 404 page are present. The remaining actions require account access.

## Google Search Console
1. Add and verify the `wintworks.com` domain property.
2. Submit `https://wintworks.com/sitemap.xml`.
3. Request indexing for `/`, `/guides.html`, `/work-visa-europe.html`, `/guides-eu-visa-routes.html`, the reviewed country guides, `/about.html`, `/privacy.html`, and `/sources.html` after content changes.
4. In **Removals**, temporarily remove legacy URLs such as `/page9.html` and `/tai-app-sunwin`. They already return the site's noindex 404 response.
5. Review Page indexing, Core Web Vitals and manual actions weekly until legacy results disappear.
6. Recheck the query cluster (`work visa Europe`, `EU work permit`, `European work visa`, and `Schengen work permit`) after Google recrawls the two visa pages. Code changes can improve relevance and snippets, but clicks will only appear after the pages are indexed and ranking data accumulates.

## AdSense
1. Confirm the site using publisher `pub-7088247829787060`.
2. In **Privacy & messaging**, publish Google's certified European regulations message with Consent, Do not consent and Manage options.
3. Set the privacy policy URL to `https://wintworks.com/privacy.html`.
4. Enable Auto Ads only after approval. The publisher tag and `ads.txt` are installed.

## Page indexing: "Discovered - currently not indexed" (274 pages, 2026-09-11)

Cause, in the repo's own numbers: the generator published the newest 250 job pages
every 6 h and deleted the rest (~100-180 added / ~120-196 removed per commit), and
only 12 of those pages were linked from crawlable HTML. Google discovered a rotating
set of thin, orphaned URLs and deprioritised all of them.

Fixed in code: a market-context block (country + visa guide links) and an `<html lang>` that matches the listing's language, so a detail page is not a bare copy of the source advert; stable URLs while a listing is live, ~80 pages instead of 250,
crawlable `/jobs/` hub pages that link every detail page, sibling links on each
detail page, `<lastmod>` that only moves when bytes change, and the 404 link the
cookie banner injected on every `/jobs/*` page.

Then, by hand in Search Console (code cannot do these):

1. **Sitemaps** → re-submit `https://wintworks.com/sitemap.xml`, confirm the URL
   count drops to ~116 and `https://wintworks.com/jobs/` is listed.
2. **URL inspection** on `https://wintworks.com/jobs/` → Request indexing. Then do
   the same for 10-15 detail pages, a handful a day - not all at once.
3. **Removals** → temporarily hide the retired `/jobs/*.html` still shown as
   "Discovered"; they are 404s now and will age out of the report within weeks.
4. Leave the ~250 retired URLs alone otherwise. Do not re-add them to a sitemap:
   re-publishing dead URLs is what created the backlog.
5. Judge progress on **impressions for the editorial pages**
   (`work-visa-europe.html`, `guides-eu-visa-routes.html`, the country guides), not
   on the "Discovered" count. That number only falls as Google reallocates crawl
   demand, which takes weeks on a young domain.
6. If the detail pages still refuse to index after ~4 weeks, stop fighting for
   them: add `<meta name="robots" content="noindex,follow">` to the template, drop
   `/jobs/` from the sitemap and spend the crawl budget on original guides.
