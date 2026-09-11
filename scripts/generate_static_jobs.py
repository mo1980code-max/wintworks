#!/usr/bin/env python3
"""Generate crawlable job detail pages and SEO fallbacks from data/jobs.json.

Google requires JobPosting structured data on a dedicated, visible job-detail URL,
not on a search/list page. This script generates the newest eligible listings,
adds their URLs to the JSON feed, pre-renders links on the home page, and rebuilds
the sitemap. It is designed to run after build_snapshot.py in GitHub Actions.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "jobs.json"
INDEX = ROOT / "index.html"
JOBS_DIR = ROOT / "jobs"
SITEMAP = ROOT / "sitemap.xml"
MAX_STATIC_JOBS = 250
BASE_URL = "https://wintworks.com"
OG_IMAGE = f"{BASE_URL}/assets/wintworks-og-banner.png"


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()
    return (slug[:150] or "job") + ".html"


BRAND_SUFFIX = " | WintWorks"
TITLE_LIMIT = 60          # keep <title> inside the ~60-char SERP window
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


def page_title(job: dict, suffix: str = "") -> str:
    """'<title> at <company> | WintWorks', shortened to TITLE_LIMIT chars (escaped).

    `suffix` disambiguates pages whose title/company pair collides with another
    live listing (two "Test Manager at Acme" rows from different markets would
    otherwise ship identical <title>s, which Google treats as duplication).
    """
    budget = TITLE_LIMIT - len(BRAND_SUFFIX)
    title = re.sub(r"\s+", " ", str(job.get("title", ""))).strip()
    company = re.sub(r"\s+", " ", str(job.get("company", ""))).strip()
    if suffix:
        budget -= len(suffix) + 3          # " · " separator
    combined = f"{title} at {company}" if company else title
    if len(html.escape(combined, quote=False)) <= budget:
        return html.escape(combined, quote=False) + BRAND_SUFFIX
    if len(html.escape(title, quote=False)) <= budget:
        return html.escape(title, quote=False) + BRAND_SUFFIX
    return fit_escaped(title, budget) + BRAND_SUFFIX


def infer_employment_type(job: dict) -> str:
    """Fallback employmentType from the listing text when the source omits it."""
    blob = f"{job.get('title', '')} {job.get('type', '')} {job.get('description', '')[:400]}".lower()
    for needle, value in (
        ("intern", "INTERN"), ("trainee", "INTERN"), ("apprentice", "INTERN"),
        ("part-time", "PART_TIME"), ("part time", "PART_TIME"), ("parttime", "PART_TIME"),
        ("temporary", "TEMPORARY"), ("seasonal", "TEMPORARY"),
        ("contract", "CONTRACTOR"), ("freelance", "CONTRACTOR"),
        ("working student", "PART_TIME"), ("mini-job", "PART_TIME"),
    ):
        if needle in blob:
            return value
    return "FULL_TIME"


def expiry_date(posted_iso: str, days: int = 45) -> str:
    """Rolling validThrough for a JobPosting (ISO date, +`days`)."""
    try:
        d = datetime.fromisoformat(posted_iso)
    except (TypeError, ValueError):
        return ""
    return (d + timedelta(days=days)).date().isoformat()


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


# Country → the matching country guide, so every job page links into the
# guide cluster instead of dead-ending on the job board anchor.
def _guide_for(job: dict) -> tuple[str, str] | None:
    """(href, label) of the most relevant country guide for this job."""
    country = (job.get("country") or "").strip()
    if not country and job.get("region") == "US":
        country = "USA"
    key = country.lower()
    guides = {
        "united kingdom": ("jobs-in-united-kingdom.html", "UK visa sponsorship jobs"),
        "uk": ("jobs-in-united-kingdom.html", "UK visa sponsorship jobs"),
        "germany": ("jobs-in-germany.html", "jobs in Germany"),
        "france": ("jobs-in-france.html", "jobs in France"),
        "netherlands": ("jobs-in-netherlands.html", "jobs in the Netherlands"),
        "spain": ("jobs-in-spain.html", "jobs in Spain"),
        "italy": ("jobs-in-italy.html", "jobs in Italy"),
        "poland": ("jobs-in-poland.html", "jobs in Poland"),
        "portugal": ("jobs-in-portugal.html", "jobs in Portugal"),
        "ireland": ("jobs-in-ireland.html", "jobs in Ireland"),
        "austria": ("jobs-in-austria.html", "jobs in Austria"),
        "belgium": ("jobs-in-belgium.html", "jobs in Belgium"),
        "czechia": ("jobs-in-czechia.html", "jobs in Czechia"),
        "czech republic": ("jobs-in-czechia.html", "jobs in Czechia"),
        "romania": ("jobs-in-romania.html", "jobs in Romania"),
        "switzerland": ("jobs-in-switzerland.html", "jobs in Switzerland"),
        "usa": ("usa-remote-jobs.html", "USA remote jobs"),
        "united states": ("usa-remote-jobs.html", "USA remote jobs"),
    }
    hit = guides.get(key)
    if hit:
        return hit
    if job.get("region") == "WW" or job.get("remote"):
        return ("remote-jobs-no-experience.html", "remote jobs without experience")
    return ("work-in-europe.html", "how to find work in Europe")


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
    kind = employment_type(job.get("type", "")) or infer_employment_type(job)
    if kind:
        schema["employmentType"] = kind
    posted = iso_date(job["date"])
    if posted:
        # Google keeps a JobPosting eligible only while validThrough is in the
        # future; the snapshot is rebuilt every six hours, so a rolling window
        # is refreshed long before it lapses.
        schema["validThrough"] = expiry_date(posted, days=45)
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


def render_job(job: dict, filename: str, title_suffix: str = "") -> str:
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
    seo_title = page_title(job, title_suffix)
    guide_href, guide_label = _guide_for(job)
    schema = json.dumps(schema_for(job, page_url), ensure_ascii=False,
                        separators=(",", ":")).replace("</", "<\\/")
    desc_meta = fit_escaped(
        f"Apply for {job['title']} at {job['company']} in {job.get('location') or 'remote'}. "
        f"View the job description and original application link.",
        DESC_META_LIMIT,
        quote=True,
    )
    return f"""<!DOCTYPE html>
<html lang="en">
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
<p><a href="../#jobs">← Back to all jobs</a></p>
<h1>{title}</h1>
<h2 style="font-size:1.15rem;color:var(--muted)">{company}</h2>
<div class="job-meta"><span class="badge">📍 {location}</span><span class="badge">{category}</span><span class="badge">Posted {posted}</span><span class="badge">Source: {source}</span></div>
<hr>
<div class="job-description"><p>{description}</p></div>
<p style="margin-top:28px"><a class="btn" href="{apply_url}" target="_blank" rel="noopener noreferrer sponsored">Apply on the original site →</a></p>
<p style="color:var(--muted);font-size:.85rem">WintWorks aggregates this listing for discovery. Verify requirements and apply only through the original publisher.</p>
<hr>
<div class="job-guide-links">
<h2 style="font-size:1.05rem">Applying from abroad?</h2>
<ul>
<li>Read the guide: <a href="../{guide_href}">{guide_label}</a></li>
<li>Before you send documents, check <a href="../job-scam-warning-signs.html">how to spot fake job and visa offers</a>.</li>
<li>Not sure which permit you need? Compare <a href="../work-visa-europe.html">Europe work visa routes</a> or browse <a href="../guides.html">all WintWorks guides</a>.</li>
</ul>
</div>
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
    fallback = "\n".join(cards) + "\n<noscript><p>JavaScript is optional: use the job links above or browse our <a href=\"guides.html\">country and visa guides</a>.</p></noscript>"
    pattern = r'(<div class="jobs-grid" id="grid">).*?(</div>\s*\n\s*<div class="load-more-wrap")'
    replacement = r"\1\n<!-- STATIC_JOBS_START -->\n" + fallback + r"\n<!-- STATIC_JOBS_END -->\n\2"
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("Could not find the home-page jobs grid")
    text = stamp_assets(text, version)
    INDEX.write_text(text, encoding="utf-8")


def update_sitemap(selected: list[dict], generated_at: str) -> None:
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
        file_path = ROOT / (url_path or "index.html")
        if file_path.exists():
            lastmod.text = datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc).date().isoformat()
        else:
            lastmod.text = generated_at[:10]
    for job in selected:
        node = ET.SubElement(root, f"{{{ns}}}url")
        ET.SubElement(node, f"{{{ns}}}loc").text = BASE_URL + "/" + job["detail_path"]
        ET.SubElement(node, f"{{{ns}}}lastmod").text = iso_date(job.get("date", "")) or generated_at[:10]
    ET.indent(tree, space="  ")
    tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)


def main() -> int:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    jobs = payload.get("jobs", [])
    selected = [job for job in jobs if eligible(job)][:MAX_STATIC_JOBS]
    staging = ROOT / ".jobs-staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    for job in jobs:
        job.pop("detail_path", None)
    seen_titles: dict[str, int] = {}
    for job in selected:
        filename = safe_slug(job["id"])
        job["detail_path"] = f"jobs/{filename}"
        # keep every <title> unique: on a collision append the location, then the
        # source, so identical listings from different markets stay distinct
        base = re.sub(r"\s+", " ", page_title(job)).lower()
        suffix = ""
        if base in seen_titles:
            seen_titles[base] += 1
            for candidate in (str(job.get("location") or "").strip(),
                              str(job.get("source") or "").strip(),
                              str(seen_titles[base])):
                if not candidate:
                    continue
                trial = page_title(job, candidate)
                if trial.lower() not in seen_titles:
                    suffix = candidate
                    seen_titles[trial.lower()] = 1
                    break
        else:
            seen_titles[base] = 1
        (staging / filename).write_text(render_job(job, filename, suffix), encoding="utf-8")
    if JOBS_DIR.exists():
        shutil.rmtree(JOBS_DIR)
    staging.rename(JOBS_DIR)
    tmp = str(DATA) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    os.replace(tmp, DATA)
    update_home(selected, payload.get("snapshot_id") or (payload.get("generated_at") or "")[:10])
    update_sitemap(selected, payload.get("generated_at") or datetime.now(timezone.utc).isoformat())
    print(f"Generated {len(selected)} crawlable job pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
