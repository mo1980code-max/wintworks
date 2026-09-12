#!/usr/bin/env python3
"""Generate crawlable job detail pages and SEO fallbacks from data/jobs.json.

Google requires JobPosting structured data on a dedicated, visible job-detail URL,
not on a search/list page. This script generates the newest eligible listings,
adds their URLs to the JSON feed, pre-renders links on the home page, and rebuilds
the sitemap. It is designed to run after build_snapshot.py in GitHub Actions.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "jobs.json"
LASTMOD_DB = ROOT / "data" / "lastmod.json"
INDEX = ROOT / "index.html"
JOBS_DIR = ROOT / "jobs"
SITEMAP = ROOT / "sitemap.xml"
BASE_URL = "https://wintworks.com"
MANIFEST = JOBS_DIR / "manifest.json"
HUB_URL = f"{BASE_URL}/jobs/"

# How many job detail pages to publish, and how old a listing may be to qualify.
#
# These two knobs are the whole indexing story. The generator used to publish the
# *newest* 250 listings on every run and delete the rest. The snapshot refreshes
# four times a day, so each run rotated ~120-190 URLs out (a 404 for anything
# Google had already discovered) and pushed 100-180 brand-new URLs into the
# sitemap: roughly 600 new plus 600 dead URLs a day on a domain with no authority
# to spend. Googlebot notes such URLs and never gets round to them - which is
# exactly what a "Discovered - currently not indexed" list of 274 means here.
#
# Fewer, longer-lived pages get crawled; a rotating 250 does not. Raise these via
# WW_STATIC_JOBS / WW_STATIC_MAX_AGE_DAYS only once the pages start getting
# impressions, not before.
MAX_STATIC_JOBS = int(os.environ.get("WW_STATIC_JOBS", "80"))
MAX_AGE_DAYS = int(os.environ.get("WW_STATIC_MAX_AGE_DAYS", "21"))
HUB_PAGE_SIZE = int(os.environ.get("WW_HUB_PAGE_SIZE", "40"))
# Internal links rendered on each detail page so no page is a dead end.
RELATED_LINKS = 6
OG_IMAGE = f"{BASE_URL}/assets/wintworks-og-banner.png"


def write_if_changed(path: Path, text: str) -> bool:
    """Write `text` only when it differs from what is already on disk.

    Rewriting identical bytes makes every generated file look edited. It fills the
    repo with no-op commits and feeds Google a sitemap claiming the whole site
    changed four times a day, which is a good way to be ignored.
    """
    if path.exists():
        try:
            if path.read_text(encoding="utf-8") == text:
                return False
        except OSError:
            pass
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return True


def date_only(value) -> str:
    """YYYY-MM-DD from any of the timestamp shapes the sources emit."""
    if not value:
        return ""
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        text = str(value)
        return text[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", text) else ""


def is_recent(job: dict, max_age_days: int, today) -> bool:
    """True when a listing is fresh enough to deserve a permanent URL.

    Undated listings are dropped on purpose: a page whose posting date is unknown
    ages into a soft 404, and Google scores the whole site on those.
    """
    day = date_only(job.get("date", ""))
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        return False
    try:
        age = (today - datetime.strptime(day, "%Y-%m-%d").date()).days
    except ValueError:
        return False
    return 0 <= age <= max_age_days


def pick_jobs(jobs: list, previous: dict, cap: int, max_age_days: int) -> list:
    """Choose the pages to publish, preferring URLs that already exist.

    A listing's filename is already stable (`safe_slug(id)`), so the churn came
    from *which* listings were chosen: "newest 250" reshuffles on every crawl.
    "every recent listing, newest first, capped" lets a page keep its URL - and
    its chance of being crawled - for as long as the job is live.
    """
    today = datetime.now(timezone.utc).date()
    pool = [j for j in jobs if eligible(j)]
    fresh = [j for j in pool if is_recent(j, max_age_days, today)]
    fresh.sort(key=lambda j: date_only(j.get("date", "")), reverse=True)

    chosen, names = [], set()
    for job in fresh:
        name = safe_slug(job["id"])
        if name not in names:
            names.add(name)
            chosen.append(job)

    # Keep a published URL alive while its listing is still in the snapshot, even
    # once it is past the fresh window. A page Google has already discovered is
    # worth more than the 404 deleting it would produce.
    by_name = {safe_slug(j.get("id", "")): j for j in pool}
    for name, meta in sorted((previous or {}).items()):
        if len(chosen) >= cap or not isinstance(meta, dict) or meta.get("expired"):
            continue
        job = by_name.get(name)
        if job is not None and name not in names and date_only(job.get("date", "")):
            names.add(name)
            chosen.append(job)
    return chosen[:cap]


MARKET_LANG = {
    "germany": "German", "austria": "German", "switzerland": "German",
    "netherlands": "Dutch", "belgium": "Dutch", "france": "French", "spain": "Spanish",
    "italy": "Italian", "poland": "Polish", "portugal": "Portuguese",
    "czechia": "Czech", "romania": "Romanian", "ireland": "English",
    "united kingdom": "English", "united states": "English", "usa": "English",
}
# Markets whose applicants usually have to think about authorisation first.
EU_CONTEXT_SLUGS = {"germany", "austria", "switzerland", "netherlands", "belgium",
                    "france", "spain", "italy", "poland", "portugal", "czechia",
                    "romania", "ireland", "united-kingdom", "worldwide",
                    "worldwide-remote", ""}


def market_links(job: dict) -> list:
    """Country page + visa guides relevant to this listing, as (file, label).

    A detail page used to carry nothing but a truncated copy of someone else's
    advert plus one outbound sponsored link - a textbook doorway page, which is
    why "Crawled - currently not indexed" persists even after the crawl problems
    are fixed. These links give a reader something to do and point internal
    authority at the original guides that can actually rank.
    """
    country = (job.get("country") or "").strip()
    slug = re.sub(r"[^a-z]+", "-", country.lower()).strip("-")
    links = []
    page = "jobs-in-" + slug + ".html"
    if country and (ROOT / page).exists():
        links.append((page, "All jobs in " + country))
    if slug in ("usa", "united-states"):
        links.append(("usa-remote-jobs.html", "Remote jobs open to US applicants"))
    if slug in EU_CONTEXT_SLUGS:
        links.append(("work-visa-europe.html", "Work visa routes for Europe"))
        links.append(("guides-eu-visa-routes.html", "EU visa routes compared"))
    if job.get("remote"):
        links.append(("remote-jobs-no-experience.html", "Remote jobs, no experience needed"))
    links.append(("guides.html", "All country & visa guides"))
    return links


def context_block(job: dict, rel_prefix: str = "../") -> str:
    rows = "".join(
        '<li><a href="' + rel_prefix + href + '">' + html.escape(label) + "</a></li>"
        for href, label in market_links(job)
    )
    country = (job.get("country") or "").strip()
    slug = re.sub(r"[^a-z]+", "-", country.lower()).strip("-").replace("-", " ")
    us = slug in ("usa", "united-states")
    notes = []
    if job.get("remote"):
        notes.append("This role is listed as remote, so the location shown is the "
                     "employer's base rather than where the work happens.")
    language = MARKET_LANG.get(slug)
    if country and language and language != "English":
        notes.append("Most postings from " + country + " are written in " + language
                     + " by the employer, so read the original advert before applying.")
    if country and not us:
        notes.append("Employers in " + country + " normally expect an EU-format CV and "
                     "may ask about work authorisation in the first message.")
    if not notes:
        notes.append("WintWorks lists this role for discovery; the requirements and "
                     "the application itself live with the original publisher.")
    if country and not us:
        heading = "Working in " + html.escape(country)
    elif us:
        heading = "Working in the United States"
    else:
        heading = "Working remotely"
    return ('<section class="seo-context"><h2>' + heading + "</h2><p>"
            + " ".join(notes) + '</p><ul class="seo-context-links">' + rows
            + "</ul></section>")


def related_jobs(job: dict, pool: list, limit: int = RELATED_LINKS) -> list:
    """Other listings in the same country first, then any - as (path, title).

    Every detail page used to link to exactly one place: the home page. Google
    cannot walk a set of pages that do not reference each other, and 250 pages
    with 12 crawlable inbound links between them all reads as a doorway cluster.
    """
    country = (job.get("country") or "").strip().lower()
    others = [j for j in pool
              if j.get("id") != job.get("id") and j.get("detail_path")]
    same = [j for j in others
            if country and (j.get("country") or "").strip().lower() == country]
    return [(j["detail_path"], j.get("title") or "listing")
            for j in (same + others)[:limit]]


LANG_STOPWORDS = {
    # Enough strongly-marked function words that an English page cannot trip it:
    # a language is only declared when several distinct words appear.
    "de": {" und ", " der ", " die ", " mit ", " für ", " auf "},
    "fr": {" les ", " des ", " une ", " pour ", " avec ", " est "},
    "nl": {" het ", " een ", " van ", " en ", " voor ", " met "},
    "es": {" los ", " las ", " una ", " para ", " con ", " del "},
    "it": {" gli ", " una ", " per ", " con ", " sono ", " del "},
    "pl": {" dla ", " się ", " lub ", " jest ", " przez ", " or "},
}


def detect_lang(text: str) -> str:
    """BCP-47 tag for the listing body, so <html lang> is not a lie.

    The feeds are mixed-language (a Belgian or German posting is written in its
    own market's language). Declaring every page as English tells Google the
    document language is English while the visible text is not, which is a
    quality hit on a page already fighting to be indexed.
    """
    probe = " " + " ".join(str(text).lower().split()) + " "
    best, best_hits = "en", 2
    for code, words in LANG_STOPWORDS.items():
        hits = sum(1 for w in words if w in probe)
        if hits > best_hits:
            best, best_hits = code, hits
    return best


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()
    return (slug[:150] or "job") + ".html"


BRAND_SUFFIX = " | WintWorks"
TITLE_LIMIT = 65          # keep <title> short enough that Google does not truncate it
DESC_META_LIMIT = 158     # meta description sweet spot


def truncate_words(text: str, limit: int) -> str:
    """Cut text at the last full word below `limit` and append an ellipsis."""
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:-–—/|(")
    return cut + "…"


def fit_escaped(text: str, limit: int, quote: bool = False) -> str:
    """Truncate text so that the HTML-escaped result stays within `limit`."""
    candidate = truncate_words(text, limit)
    while len(html.escape(candidate, quote=quote)) > limit and len(candidate) > 20:
        candidate = truncate_words(text, len(candidate) - 2)
    return html.escape(candidate, quote=quote)


def page_title(job: dict) -> str:
    """'<title> at <company> | WintWorks', shortened to TITLE_LIMIT chars (escaped)."""
    budget = TITLE_LIMIT - len(BRAND_SUFFIX)
    title = re.sub(r"\s+", " ", str(job.get("title", ""))).strip()
    company = re.sub(r"\s+", " ", str(job.get("company", ""))).strip()
    combined = f"{title} at {company}" if company else title
    if len(html.escape(combined, quote=False)) <= budget:
        return html.escape(combined, quote=False) + BRAND_SUFFIX
    if len(html.escape(title, quote=False)) <= budget:
        return html.escape(title, quote=False) + BRAND_SUFFIX
    return fit_escaped(title, budget) + BRAND_SUFFIX


def load_lastmod_db() -> dict:
    """Previous path -> {sha1, date} map, so <lastmod> can be honest.

    GitHub Actions checks the repo out with fresh mtimes and the generator rewrites
    every file, so mtime says "changed today" 4x a day for pages nobody edited.
    Google learns fast that lastmod is meaningless here and stops trusting the
    sitemap - which is exactly how a small site ends up with hundreds of
    "Discovered - currently not indexed" URLs.
    """
    try:
        db = json.loads(LASTMOD_DB.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in db.items() if isinstance(v, dict)} if isinstance(db, dict) else {}


def touch_lastmod(db: dict, rel_path: str, content: str, fallback: str = "") -> str:
    """Return the date `rel_path` last genuinely changed, remembering this run.

    Identical bytes keep the stored date; different bytes move to today. `fallback`
    lets a caller supply a more truthful date than "today" (a job's datePosted).
    """
    today = datetime.now(timezone.utc).date().isoformat()
    digest = hashlib.sha1(content.encode("utf-8")).hexdigest()
    record = db.get(rel_path)
    if isinstance(record, dict) and record.get("sha1") == digest and record.get("date"):
        return record["date"]
    if isinstance(record, dict) and record.get("date"):
        date = today                       # edited after it was first published
    else:
        date = fallback or today           # first sighting: the posting date is the truth
    db[rel_path] = {"sha1": digest, "date": date}
    return date


def save_lastmod_db(db: dict, live_paths: set) -> None:
    """Persist only entries for pages that still exist, so the map cannot bloat."""
    pruned = {k: v for k, v in db.items() if k in live_paths}
    tmp = str(LASTMOD_DB) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(pruned, f, ensure_ascii=False, indent=0, sort_keys=True)
    os.replace(tmp, LASTMOD_DB)


def iso_date(value: str) -> str:
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return ""


def employment_type(value: str) -> str | None:
    text = (value or "").lower().replace("-", "_").replace(" ", "_")
    checks = (
        ("full", "FULL_TIME"), ("part", "PART_TIME"),
        ("contract", "CONTRACTOR"), ("temporary", "TEMPORARY"),
        ("intern", "INTERN"), ("volunteer", "VOLUNTEER"),
        ("per_diem", "PER_DIEM"),
    )
    return next((schema for token, schema in checks if token in text), None)


def eligible(job: dict) -> bool:
    return all(str(job.get(k, "")).strip() for k in
               ("id", "title", "company", "description", "date", "url"))


def schema_for(job: dict, page_url: str) -> dict:
    schema = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": job["title"],
        "description": f"<p>{html.escape(job['description'])}</p>",
        "identifier": {
            "@type": "PropertyValue",
            "name": job["company"],
            "value": job["id"],
        },
        "datePosted": iso_date(job["date"]),
        "hiringOrganization": {
            "@type": "Organization",
            "name": job["company"],
        },
        "url": page_url,
        "directApply": False,
    }
    kind = employment_type(job.get("type", ""))
    if kind:
        schema["employmentType"] = kind
    country = job.get("country") or ("USA" if job.get("region") == "US" else "")
    if job.get("remote"):
        schema["jobLocationType"] = "TELECOMMUTE"
        if country and country not in ("Worldwide", "Worldwide / Remote"):
            schema["applicantLocationRequirements"] = {
                "@type": "Country", "name": country
            }
    else:
        schema["jobLocation"] = {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": job.get("location", ""),
                "addressCountry": country or job.get("region", ""),
            },
        }
    return schema


def page_shell(title: str, description: str, canonical: str, body: str,
             rel_prefix: str, extra_head: str = "", lang: str = "en") -> str:
    """Common chrome for the generated hub pages (kept close to the detail pages)."""
    esc = html.escape
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#14357f">
<link rel="icon" type="image/svg+xml" href="{rel_prefix}favicon.svg">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{OG_IMAGE}">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{rel_prefix}css/app.css">
{extra_head}
<script>try{{var t=JSON.parse(localStorage.getItem('ww:theme'));if(t==='dark')document.documentElement.dataset.theme='dark'}}catch(e){{}}</script>
<script src="{rel_prefix}js/consent.js"></script>
</head>
<body>
<header class="site-header"><div class="container header-inner">
<a class="logo" href="{rel_prefix}" aria-label="WintWorks home"><span>Wint<b>Works</b></span></a>
<nav class="main-nav"><a href="{rel_prefix}#jobs">Jobs</a><a href="{rel_prefix}guides.html">Guides</a><a href="{rel_prefix}about.html">About</a></nav>
</div></header>
<main><div class="page"><div class="container">
{body}
</div></div></main>
<footer class="site-footer"><div class="container"><div class="footer-bottom"><span>&copy; WintWorks</span><a href="{rel_prefix}privacy.html">Privacy</a><a href="{rel_prefix}terms.html">Terms</a></div></div></footer>
</body></html>
"""


def render_hub(entries: list, page: int, pages: int, total: int) -> tuple:
    """One crawlable page of the /jobs/ hub. Returns (filename, html).

    This file is the reason the detail pages can be indexed at all: without a
    crawlable listing page, 80% of the detail pages are reachable only from the
    sitemap, and a sitemap-only page is what Google labels "Discovered -
    currently not indexed".
    """
    name = "index.html" if page == 1 else f"page-{page}.html"
    suffix = "" if page == 1 or pages < 2 else f" — page {page} of {pages}"
    title = f"Live jobs in Europe, the USA & remote{suffix} | WintWorks"
    description = (
        f"{total} live job listings across Europe, the USA and remote roles, each with "
        f"company, location and the original apply link. Page {page} of {pages}."
        if pages > 1 else
        f"{total} live job listings across Europe, the USA and remote, each with its "
        f"own page and original application link."
    )
    canonical = HUB_URL if page == 1 else f"{BASE_URL}/jobs/page-{page}.html"

    groups, order = {}, []
    for job in entries:
        key = (job.get("country") or job.get("region") or "Worldwide / Remote").strip()
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(job)

    blocks = []
    for key in order:
        rows = []
        for job in groups[key]:
            href = html.escape(Path(job["detail_path"]).name, quote=True)
            posted = date_only(job.get("date", ""))
            rows.append(
                '<li><a href="' + href + '"><strong>' + html.escape(job["title"])
                + "</strong></a> — " + html.escape(job.get("company") or "")
                + (", " + html.escape(job.get("location")) if job.get("location") else "")
                + (f" · posted {html.escape(posted)}" if posted else "") + "</li>"
            )
        blocks.append(
            f'<section><h2>{html.escape(key)}</h2><ul class="seo-hub-list">'
            + "".join(rows) + "</ul></section>"
        )

    nav = []
    if page > 1:
        prev_name = "index.html" if page == 2 else f"page-{page - 1}.html"
        nav.append(f'<a rel="prev" href="{prev_name}">&larr; Previous</a>')
    if page < pages:
        nav.append(f'<a rel="next" href="page-{page + 1}.html">Next &rarr;</a>')
    nav_html = ('<nav class="seo-pager" aria-label="Pagination">' + " ".join(nav) + "</nav>") if nav else ""

    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "WintWorks live job listings",
        "numberOfItems": total,
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1 + (page - 1) * HUB_PAGE_SIZE,
             "url": f"{BASE_URL}/{job['detail_path']}"}
            for i, job in enumerate(entries)
        ],
    }
    extra = ('<script type="application/ld+json">'
             + json.dumps(item_list, ensure_ascii=False, separators=(",", ":")).replace("</", "<\/")
             + "</script>")

    body = (
        '<article class="page-card" style="max-width:900px;margin:auto">'
        '<h1>Live jobs</h1>'
        f'<p>{total} recent listings across Europe, the USA and remote roles. Every '
        'listing links to the original application page.</p>'
        + "".join(blocks)
        + nav_html
        + f'<p><a href="../">← Back to the home page</a> · <a href="../guides.html">Work in Europe guides</a></p>'
        "</article>"
    )
    return name, page_shell(title, description, canonical, body, "../", extra)


def load_manifest() -> dict:
    try:
        raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return raw.get("files", {}) if isinstance(raw, dict) else {}


def write_manifest(entries: list) -> None:
    """filename -> {id, date, title} for the pages currently published."""
    files = {Path(e["detail_path"]).name: {
        "id": e.get("id"), "date": date_only(e.get("date", "")),
        "title": e.get("title"),
    } for e in entries}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST.with_name("manifest.json.tmp")
    tmp.write_text(json.dumps({"updated": datetime.now(timezone.utc).date().isoformat(),
                              "files": files}, ensure_ascii=False, indent=1, sort_keys=True),
                   encoding="utf-8")
    os.replace(tmp, MANIFEST)


def render_job(job: dict, filename: str, related: list | None = None) -> str:
    page_url = f"{BASE_URL}/jobs/{quote(filename)}"
    title = html.escape(job["title"])
    company = html.escape(job["company"])
    location = html.escape(job.get("location") or "Not specified")
    description = html.escape(job["description"])
    apply_url = html.escape(job["url"], quote=True)
    source = html.escape(job.get("source") or "original publisher")
    category = html.escape(job.get("category") or "Jobs")
    posted = iso_date(job.get("date", ""))
    remote = " · Remote" if job.get("remote") else ""
    # SEO-safe <title>/OG/Twitter text: full JobPosting title stays in JSON-LD.
    seo_title = page_title(job)
    schema = json.dumps(schema_for(job, page_url), ensure_ascii=False,
                        separators=(",", ":")).replace("</", "<\\/")
    # A detail page sits in the same directory as the hub (/jobs/x.html next to
    # /jobs/index.html), so the hub is a sibling link, not "../".
    hub_href = "index.html"
    context_html = context_block(job, "../")
    nav_html = ""
    related_html = ""
    if related:
        items = "".join(
            f'<li><a href="{html.escape(Path(href).name, quote=True)}">{html.escape(title)}</a></li>'
            for href, title in related
        )
        where = (job.get("location") or "").strip()
        related_html = (
            '<nav class="seo-related" aria-label="More jobs in the same market">'
            f'<h2>More jobs{" in " + html.escape(where) if where else ""}</h2>'
            f'<ul>{items}</ul>'
            '<p><a href="index.html">Browse every live listing &rarr;</a></p></nav>'
        )
    desc_meta = fit_escaped(
        f"Apply for {job['title']} at {job['company']} in {job.get('location') or 'remote'}. "
        f"View the job description and original application link.",
        DESC_META_LIMIT,
        quote=True,
    )
    lang = detect_lang(job["description"])
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{seo_title}</title>
<meta name="description" content="{desc_meta}">
<link rel="canonical" href="{page_url}">
<meta name="theme-color" content="#14357f">
<link rel="icon" type="image/svg+xml" href="../favicon.svg">
<meta property="og:type" content="website">
<meta property="og:url" content="{page_url}">
<meta property="og:title" content="{seo_title}">
<meta property="og:description" content="{desc_meta}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{seo_title}">
<meta name="twitter:description" content="{desc_meta}">
<meta name="twitter:image" content="{OG_IMAGE}">
<link rel="stylesheet" href="../css/app.css">
<script type="application/ld+json">{schema}</script>
<script>try{{var t=JSON.parse(localStorage.getItem('ww:theme'));if(t==='dark')document.documentElement.dataset.theme='dark'}}catch(e){{}}</script>
<script src="../js/consent.js"></script>
</head>
<body>
<header class="site-header"><div class="container header-inner">
<a class="logo" href="../" aria-label="WintWorks home"><span>Wint<b>Works</b></span></a>
<nav class="main-nav"><a href="../#jobs">Jobs</a><a href="../guides.html">Guides</a><a href="../about.html">About</a></nav>
</div></header>
<main><div class="page"><div class="container">
<article class="page-card" style="max-width:900px;margin:auto">
{nav_html}
<nav class="seo-crumbs" aria-label="Breadcrumb"><a href="../">Home</a> › <a href="{hub_href}">All jobs</a></nav>
<h1>{title}</h1>
<h2 style="font-size:1.15rem;color:var(--muted)">{company}</h2>
<div class="job-meta"><span class="badge">📍 {location}</span><span class="badge">{category}</span><span class="badge">Posted {posted}</span><span class="badge">Source: {source}</span></div>
<hr>
<div class="job-description"><p>{description}</p></div>
<p style="margin-top:28px"><a class="btn" href="{apply_url}" target="_blank" rel="noopener noreferrer sponsored">Apply on the original site →</a></p>
<p style="color:var(--muted);font-size:.85rem">WintWorks aggregates this listing for discovery. Verify requirements and apply only through the original publisher.</p>
{related_html}
{context_html}
</article></div></div></main>
<footer class="site-footer"><div class="container"><div class="footer-bottom"><span>© WintWorks</span><a href="../privacy.html">Privacy</a><a href="../terms.html">Terms</a></div></div></footer>
</body></html>
"""


ASSET_RE = re.compile(r"(?P<file>js/app\.min\.js|css/app\.css)(?:\?v=[0-9A-Za-z._-]+)?")


def stamp_assets(text: str, version: str) -> str:
    """Give the home page's bundle links a version that tracks the snapshot.

    GitHub Pages and browser caches keep app.min.js / app.css for a while. Without a
    query that changes whenever the data changes, a deploy can serve a cached bundle
    that no longer matches the shipped snapshot — the visible symptom being "the
    site did not update". Idempotent: the same version rewrites to the same text, so
    a run with no new jobs still produces no diff.
    """
    if not version:
        return text
    version = re.sub(r"[^0-9A-Za-z._-]", "-", str(version))
    return ASSET_RE.sub(lambda m: f"{m.group('file')}?v={version}", text)


def update_home(selected: list[dict], version: str = "") -> None:
    text = INDEX.read_text(encoding="utf-8")
    cards = []
    for job in selected[:12]:
        path = html.escape(job["detail_path"], quote=True)
        cards.append(
            f'<article class="job-card seo-job"><h3 class="job-title"><a href="{path}">'
            f'{html.escape(job["title"])}</a></h3><div class="job-company">'
            f'{html.escape(job["company"])}</div><div class="job-meta"><span class="badge">📍 '
            f'{html.escape(job.get("location") or "Remote")}</span></div></article>'
        )
    more = (
        f'\n<p class="seo-jobs-more"><a href="jobs/">Browse all {len(selected)} live listings '
        f'with their own pages &rarr;</a></p>'
    )
    fallback = ("\n".join(cards) + more
                + "\n<noscript><p>JavaScript is optional: use the job links above or browse our "
                  '<a href="guides.html">country and visa guides</a>.</p></noscript>')
    pattern = r'(<div class="jobs-grid" id="grid">).*?(</div>\s*\n\s*<div class="load-more-wrap")'
    replacement = r"\1\n<!-- STATIC_JOBS_START -->\n" + fallback + r"\n<!-- STATIC_JOBS_END -->\n\2"
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("Could not find the home-page jobs grid")
    text = stamp_assets(text, version)
    INDEX.write_text(text, encoding="utf-8")


def update_sitemap(selected: list[dict], hub_pages: list, generated_at: str,
                   db: dict) -> None:
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", ns)
    tree = ET.parse(SITEMAP)
    root = tree.getroot()
    # Remove previously generated detail URLs and add lastmod to static pages.
    for node in list(root):
        loc = node.find(f"{{{ns}}}loc")
        if loc is not None and "/jobs/" in (loc.text or ""):
            root.remove(node)
            continue
        lastmod = node.find(f"{{{ns}}}lastmod")
        if lastmod is None:
            lastmod = ET.Element(f"{{{ns}}}lastmod")
        else:
            node.remove(lastmod)
        # Sitemap element order is loc, lastmod, changefreq, priority.
        node.insert(1, lastmod)
        url_path = (loc.text or "").replace(BASE_URL + "/", "") if loc is not None else ""
        rel = url_path or "index.html"
        file_path = ROOT / rel
        if file_path.exists():
            lastmod.text = touch_lastmod(db, rel, file_path.read_text(encoding="utf-8"),
                                        generated_at[:10])
        else:
            lastmod.text = generated_at[:10]
    for name, _html in hub_pages:
        rel = f"jobs/{name}"
        node = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(node, f"{{{ns}}}loc").text = (
            HUB_URL if name == "index.html" else f"{BASE_URL}/{rel}")
        ET.SubElement(node, f"{{{ns}}}lastmod").text = touch_lastmod(
            db, rel, _html, generated_at[:10])
    for job in selected:
        rel = job["detail_path"]
        node = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(node, f"{{{ns}}}loc").text = BASE_URL + "/" + rel
        # Prefer the date the *page* last changed; a re-render with identical text
        # must not look like new content.
        ET.SubElement(node, f"{{{ns}}}lastmod").text = touch_lastmod(
            db, rel, job.get("_html", ""), iso_date(job.get("date", "")) or generated_at[:10])
    ET.indent(tree, space="  ")
    tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)


def sitemap_paths() -> set:
    """Root-level pages listed in the sitemap, so their lastmod can be tracked."""
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    try:
        root = ET.parse(SITEMAP).getroot()
    except OSError:
        return set()
    out = set()
    for node in root:
        loc = node.find(f"{ns}loc")
        if loc is None or not loc.text:
            continue
        rel = loc.text.replace(BASE_URL + "/", "").split("/")
        if len(rel) == 1 and rel[0]:
            out.add(rel[0])
    return out or {"index.html"}


def main() -> int:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    jobs = payload.get("jobs", [])
    db = load_lastmod_db()
    previous = load_manifest()

    selected = pick_jobs(jobs, previous, MAX_STATIC_JOBS, MAX_AGE_DAYS)
    for job in jobs:
        job.pop("detail_path", None)
    for job in selected:
        job["detail_path"] = f"jobs/{safe_slug(job['id'])}"

    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for job in selected:
        filename = Path(job["detail_path"]).name
        text = render_job(job, filename, related_jobs(job, selected))
        job["_html"] = text
        if write_if_changed(JOBS_DIR / filename, text):
            written += 1

    # Hub pages: every published URL is linked from crawlable HTML here.
    hub_pages = []
    total = len(selected)
    pages = max(1, -(-total // HUB_PAGE_SIZE))
    for page in range(1, pages + 1):
        chunk = selected[(page - 1) * HUB_PAGE_SIZE: page * HUB_PAGE_SIZE]
        if not chunk:
            continue
        name, html_text = render_hub(chunk, page, pages, total)
        hub_pages.append((name, html_text))
        write_if_changed(JOBS_DIR / name, html_text)

    # Drop only pages that are no longer selected - never the hub or the manifest.
    keep = {Path(j["detail_path"]).name for j in selected} | {n for n, _ in hub_pages} | {"manifest.json"}
    removed = 0
    for path in JOBS_DIR.glob("*.html"):
        if path.name not in keep:
            path.unlink()
            removed += 1

    write_manifest(selected)
    tmp = str(DATA) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    os.replace(tmp, DATA)
    update_home(selected, payload.get("snapshot_id") or (payload.get("generated_at") or "")[:10])
    update_sitemap(selected, hub_pages,
                   payload.get("generated_at") or datetime.now(timezone.utc).isoformat(), db)
    save_lastmod_db(db, {j["detail_path"] for j in selected}
                    | {f"jobs/{name}" for name, _ in hub_pages}
                    | {p for p in sitemap_paths()})
    print(f"Generated {len(selected)} crawlable job pages "
          f"({written} new/changed, {removed} retired) across {len(hub_pages)} hub page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
