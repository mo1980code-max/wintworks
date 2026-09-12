#!/usr/bin/env python3
"""Regression tests for scripts/generate_static_jobs.py.

Written after the 2026-09-11 Search Console report showed 274 pages as
"Discovered - currently not indexed". Every assertion here is about a property the
site had lost: stable URLs, no orphans, an honest <lastmod>, no dead links.

Run: python3 test_static_pages.py
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

import generate_static_jobs as gen  # noqa: E402

PASS, FAIL = [], []


def ok(cond, label):
    (PASS if cond else FAIL).append(label)
    print(("  ok  " if cond else "  FAIL ") + label)


def job(i, day, country="Germany", desc="English body text here"):
    return {
        "id": f"src-{i}", "title": f"Engineer {i}", "company": f"Acme {i}",
        "location": "Berlin", "country": country, "region": "EU",
        "remote": False, "date": f"2026-09-{day:02d}T10:00:00+00:00",
        "description": desc, "url": f"https://example.test/{i}", "source": "Test",
    }


# ---------------------------------------------------------------- selection
def test_freshness_window():
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date()
    fresh = job(1, 11)                                     # posted today
    stale = dict(job(2, 1), date="2020-01-01T00:00:00+00:00")
    ok(gen.is_recent(fresh, 21, today), "a listing posted today is recent")
    ok(not gen.is_recent(stale, 21, today), "a 6-year-old listing gets no page")
    ok(not gen.is_recent(dict(job(3, 1), date=""), 21, today), "undated listings are skipped")
    ok(not gen.is_recent(dict(job(4, 1), date="not-a-date"), 21, today), "unparseable dates are skipped")


def test_urls_are_stable_across_runs():
    """A listing that is still live must keep its URL even when it is no longer newest."""
    pool = [job(i, 11) for i in range(1, 30)]
    chosen = gen.pick_jobs(pool, {}, cap=10, max_age_days=21)
    names = {gen.safe_slug(j["id"]) for j in chosen}
    ok(len(chosen) == 10, "cap is respected")
    # Next crawl: a brand-new listing arrives, but the previous pages stay published.
    new = [job(99, 11)] + pool
    previous = {n: {"id": n[:-5].replace("src-", ""), "date": "2026-09-11"} for n in names}
    chosen2 = gen.pick_jobs(new, previous, cap=10, max_age_days=21)
    names2 = {gen.safe_slug(j["id"]) for j in chosen2}
    ok(gen.safe_slug("src-1") in names2, "an existing job page is not deleted to make room")
    ok("src-99" in {j["id"] for j in chosen2}, "a new listing is still added")
    ok(len(chosen2) <= 10, "the cap still bounds the published set")


# ---------------------------------------------------------------- pages
def _render_one(pool):
    j = pool[0]
    j["detail_path"] = f"jobs/{gen.safe_slug(j['id'])}"
    for other in pool[1:]:
        other["detail_path"] = f"jobs/{gen.safe_slug(other['id'])}"
    return gen.render_job(j, Path(j["detail_path"]).name, gen.related_jobs(j, pool))


def test_detail_page_links_out_to_peers():
    pool = [job(i, 11) for i in range(1, 10)]
    html = _render_one(pool)
    ok('href="src-2.html"' in html, "a detail page links to sibling listings")
    ok(html.count('<a href="src-') >= gen.RELATED_LINKS, f"{gen.RELATED_LINKS} cross links are rendered")
    ok('href="index.html"' in html, "a detail page links to the crawlable hub")
    ok('<link rel="canonical" href="https://wintworks.com/jobs/src-1.html">' in html,
       "canonical matches the published URL")
    ok('noindex' not in html, "detail pages are indexable")


def test_language_matches_the_text():
    ok('lang="en"' in _render_one([job(1, 11)]), "English listings declare en")
    de = [dict(job(1, 11), description="Wir suchen einen Techniker und die Arbeit ist für alle in Berlin.")]
    ok('lang="de"' in _render_one(de), "a German listing is not labelled English")


def test_hub_page_links_every_published_url():
    pool = [job(i, 11, country=c) for i, c in
            ((i, ("Germany", "Italy", "Spain")[i % 3]) for i in range(1, 13))]
    for j in pool:
        j["detail_path"] = f"jobs/{gen.safe_slug(j['id'])}"
    name, html = gen.render_hub(pool[:4], 1, 3, len(pool))
    ok(name == "index.html", "page 1 of the hub is index.html")
    for j in pool[:4]:
        assert 'href="' + Path(j["detail_path"]).name + '"' in html
    ok('"@type":"ItemList"' in html, "the hub carries ItemList structured data")
    ok('rel="next"' in html and 'page-2.html' in html, "pagination links are crawlable")
    name2, html2 = gen.render_hub(pool[4:8], 2, 3, len(pool))
    ok(name2 == "page-2.html", "later hub pages are numbered")
    ok('rel="prev"' in html2, "a later hub page links back to the previous one")


def test_write_if_changed_is_quiet():
    tmp = Path(tempfile.mkdtemp())
    try:
        f = tmp / "a.html"
        ok(gen.write_if_changed(f, "<p>x</p>") is True, "a new file is written")
        ok(gen.write_if_changed(f, "<p>x</p>") is False, "identical content is not rewritten")
        untouched = f.stat().st_mtime_ns
        gen.write_if_changed(f, "<p>y</p>")
        ok(f.read_text() == "<p>y</p>", "changed content is written")
        ok(f.stat().st_mtime_ns == untouched, "a no-op write leaves the file's mtime alone")
    finally:
        shutil.rmtree(tmp)


def test_lastmod_moves_only_for_real_changes():
    db: dict = {}
    d1 = gen.touch_lastmod(db, "about.html", "<p>one</p>", "2026-01-01")
    ok(d1 == "2026-01-01", "first sighting records the caller's date")
    ok(gen.touch_lastmod(db, "about.html", "<p>one</p>", "2026-01-01") == d1,
       "unchanged bytes keep the old lastmod")
    d2 = gen.touch_lastmod(db, "about.html", "<p>two</p>", "2026-01-01")
    ok(d2 != d1, "edited bytes move lastmod to today")
    ok(gen.touch_lastmod(db, "about.html", "<p>two</p>", "2026-01-01") == d2,
       "an unchanged re-render does not bump lastmod again")


def test_market_context_links_exist():
    pool = [job(1, 11), job(2, 11, country="USA"), job(3, 11)]
    pool[1]["country"] = "USA"
    pool[2]["country"] = "Worldwide / Remote"
    pool[2]["remote"] = True
    for j in pool:
        hrefs = [h for h, _ in gen.market_links(j)]
        ok(hrefs, f"{j.get('country')}: market context offers links")
        missing = [h for h in hrefs if not (ROOT / h).exists()]
        ok(not missing, f"{j.get('country')}: every context link exists ({missing or 'ok'})")
    block = gen.context_block(job(1, 11, country="Germany"), "../")
    ok("../jobs-in-germany.html" in block, "a German listing links to the Germany guide")
    ok('lang=' not in block, "the context block is markup, not a new document")


def test_published_pages_are_reachable_and_listed():
    """Guards the exact failure that produced 274 'Discovered' URLs.

    Every generated detail page must be (a) linked from a crawlable /jobs/ hub
    page, (b) present in the sitemap, and (c) the sitemap must not list a URL that
    has no file - a sitemap full of dead or unlinked URLs is what taught Google to
    ignore this site.
    """
    hub_files = sorted(ROOT.glob("jobs/index.html")) + sorted(ROOT.glob("jobs/page-*.html"))
    if not hub_files:
        ok(False, "hub pages exist (run scripts/generate_static_jobs.py)")
        return
    hub = "".join(f.read_text(encoding="utf-8") for f in hub_files)
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    published = sorted(x.name for x in (ROOT / "jobs").glob("*.html")
                       if x.name not in {f.name for f in hub_files})
    ok(len(published) > 0, "detail pages exist to check")
    orphans = [name for name in published if 'href="' + name + '"' not in hub]
    ok(not orphans, f"every detail page is linked from the hub ({len(orphans)} orphans)")
    absent = [name for name in published if f"/jobs/{name}" not in sitemap]
    ok(not absent, f"every detail page is in the sitemap ({len(absent)} missing)")
    listed = re.findall(r"<loc>https://wintworks\.com/(jobs/[^<]+)</loc>", sitemap)
    stale = [u for u in listed if not (ROOT / u).exists()]
    ok(not stale, f"the sitemap lists no deleted page ({stale[:3] or 'ok'})")
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    ok('href="jobs/"' in home, "the home page links the hub in crawlable HTML")


def test_generated_pages_declare_honest_lastmod():
    """lastmod must mean 'this page changed', not 'CI ran'."""
    db_path = ROOT / "data" / "lastmod.json"
    if not db_path.exists():
        ok(False, "data/lastmod.json exists")
        return
    db = json.loads(db_path.read_text(encoding="utf-8"))
    unchanged = [k for k, v in db.items() if "sha1" not in v or "date" not in v]
    ok(not unchanged, "every ledger entry records a hash and a date")
    dated = set(re.findall(r"<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>",
                           (ROOT / "sitemap.xml").read_text(encoding="utf-8")))
    ok(dated and max(dated) <= datetime.now(timezone.utc).date().isoformat(),
       f"no lastmod is in the future ({sorted(dated)[-1:]})")


if __name__ == "__main__":
    for fn in [test_freshness_window, test_urls_are_stable_across_runs,
               test_detail_page_links_out_to_peers, test_language_matches_the_text,
               test_hub_page_links_every_published_url, test_write_if_changed_is_quiet,
               test_market_context_links_exist,
               test_published_pages_are_reachable_and_listed,
               test_generated_pages_declare_honest_lastmod,
               test_lastmod_moves_only_for_real_changes]:
        print(f"\n{fn.__name__}")
        fn()
    print(f"\n{len(PASS)} assertions passed, {len(FAIL)} failed")
    if FAIL:
        print("failed: " + ", ".join(FAIL))
    raise SystemExit(1 if FAIL else 0)
