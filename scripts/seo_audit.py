#!/usr/bin/env python3
"""
WintWorks — static SEO / internal-linking / Core-Web-Vitals audit.

Runs over every HTML page in the repository (root pages + a sample of the
generated `jobs/*.html` pages) and reports problems grouped by severity:

  ERROR   — breaks indexing, structured data or navigation (fails the build)
  WARN    — measurably hurts SERP appearance, crawl depth or Core Web Vitals
  INFO    — nice-to-have / observation only

Usage:
    python3 scripts/seo_audit.py                # human report, exit 1 on ERROR
    python3 scripts/seo_audit.py --all          # include every jobs/*.html page
    python3 scripts/seo_audit.py --json out.json
    python3 scripts/seo_audit.py --no-fail      # always exit 0

The checker is intentionally dependency-free (stdlib only) so it can run in the
same GitHub Actions job as the snapshot build.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://wintworks.com"
SITEMAP = ROOT / "sitemap.xml"
ROBOTS = ROOT / "robots.txt"

# Pages that are not indexable content and are therefore exempt from
# content/social checks (verification files, redirect stubs, error pages).
EXEMPT_FROM_CONTENT = {"yandex_887be838c598332d.html", "ar-guides-eu-visa-routes.html"}

TITLE_MAX = 60          # Google truncates around 580px ≈ 60 chars
TITLE_HARD_MAX = 70     # above this it is certainly truncated
DESC_MIN, DESC_MAX = 70, 160
OG_REQUIRED = ("og:title", "og:description", "og:type", "og:url", "og:image")
TW_REQUIRED = ("twitter:card", "twitter:title", "twitter:description", "twitter:image")
CWV_THIRD_PARTIES = {
    "pagead2.googlesyndication.com": "AdSense",
    "fonts.googleapis.com": "Google Fonts CSS",
    "fonts.gstatic.com": "Google Fonts files",
    "cdnjs.cloudflare.com": "cdnjs (PDF export)",
    "cdn.tailwindcss.com": "Tailwind CDN (runtime compiler)",
}
GENERIC_ANCHORS = {
    "click here", "here", "read more", "more", "learn more", "link", "this page",
    "official link", "apply now", "apply", "بعد", "المزيد",
}

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


class TagCollector(HTMLParser):
    """Collects the tag-level facts the audit needs, without a DOM library."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.text_parts: list[str] = []
        self.in_script = False
        self.in_style = False
        self.ld_json: list[str] = []
        self._ld_buf: list[str] = []
        self._ld_on = False
        self.head_html: list[str] = []
        self.in_head = True
        self._raw: list[str] = []

    def handle_starttag(self, tag, attrs):
        d = {k.lower(): (v or "") for k, v in attrs}
        self.tags.append((tag, d))
        if tag == "script":
            self.in_script = True
            self._ld_on = d.get("type", "").strip().lower() == "application/ld+json"
        elif tag == "style":
            self.in_style = True
        elif tag == "head":
            self.in_head = True

    def handle_endtag(self, tag):
        if tag == "script":
            if self._ld_on:
                self.ld_json.append("".join(self._ld_buf))
                self._ld_buf = []
                self._ld_on = False
            self.in_script = False
        elif tag == "style":
            self.in_style = False
        elif tag == "head":
            self.in_head = False

    def handle_data(self, data):
        if self._ld_on:
            self._ld_buf.append(data)
        elif not (self.in_script or self.in_style):
            self.text_parts.append(data)
        if self.in_head:
            self.head_html.append(data)

    @property
    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.text_parts)).strip()


def parse(path: Path) -> TagCollector:
    c = TagCollector()
    c.feed(path.read_text(encoding="utf-8", errors="replace"))
    return c


def meta(c: TagCollector, name: str, prop: bool = False) -> str:
    key = "property" if prop else "name"
    for tag, d in c.tags:
        if tag == "meta" and d.get(key, "").lower() == name.lower():
            return d.get("content", "").strip()
    return ""


def link(c: TagCollector, rel: str) -> list[dict]:
    return [d for tag, d in c.tags if tag == "link" and rel in d.get("rel", "").lower().split()]


def first(c: TagCollector, tag: str) -> dict:
    for t, d in c.tags:
        if t == tag:
            return d
    return {}


class Report:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, sev: str, code: str, page: str, msg: str, detail: str = "") -> None:
        self.items.append({"severity": sev, "code": code, "page": page,
                           "message": msg, "detail": detail})

    def count(self, sev: str) -> int:
        return sum(1 for i in self.items if i["severity"] == sev)


# --------------------------------------------------------------------------- #
# per-page checks
# --------------------------------------------------------------------------- #
def check_page(path: Path, rel: str, rep: Report, in_sitemap: set[str]) -> None:
    c = parse(path)
    html = path.read_text(encoding="utf-8", errors="replace")
    exempt = rel in EXEMPT_FROM_CONTENT
    noindex = "noindex" in meta(c, "robots").lower()

    # ---- head basics ------------------------------------------------------
    if rel in EXEMPT_FROM_CONTENT:
        return
    if not first(c, "html").get("lang"):
        rep.add("ERROR", "html-lang", rel, "<html> has no lang attribute")
    if not meta(c, "viewport") and not exempt:
        rep.add("ERROR", "viewport", rel, "missing viewport meta")
    if not re.search(r'<meta\s+charset', html, re.I):
        rep.add("WARN", "charset", rel, "no explicit <meta charset>")

    title = ""
    for tag, d in c.tags:
        if tag == "title":
            break
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    tlen = len(title)
    if noindex or exempt:
        pass
    elif not title:
        rep.add("ERROR", "title-missing", rel, "no <title>")
    elif tlen > TITLE_HARD_MAX:
        rep.add("ERROR", "title-long", rel, f"title is {tlen} chars (limit {TITLE_HARD_MAX})", title)
    elif tlen > TITLE_MAX:
        rep.add("WARN", "title-long", rel, f"title is {tlen} chars — truncates in Google (≤{TITLE_MAX})", title)

    desc = meta(c, "description")
    if not noindex and not exempt:
        if not desc:
            rep.add("ERROR", "desc-missing", rel, "missing meta description")
        elif len(desc) > DESC_MAX:
            rep.add("WARN", "desc-long", rel, f"description is {len(desc)} chars (≤{DESC_MAX})", desc[:90] + "…")
        elif len(desc) < DESC_MIN:
            rep.add("INFO", "desc-short", rel, f"description is only {len(desc)} chars")

    # ---- canonical / robots ----------------------------------------------
    canon = link(c, "canonical")
    if not canon and not exempt and rel != "404.html":
        rep.add("ERROR", "canonical-missing", rel, "missing <link rel=canonical>")
    elif canon:
        href = canon[0].get("href", "")
        expected = BASE_URL + "/" + rel if rel != "index.html" else BASE_URL + "/"
        if not href.startswith("http"):
            rep.add("ERROR", "canonical-relative", rel, f"canonical is not absolute: {href}")
        elif href.rstrip("/") != expected.rstrip("/") and rel != "ar-guides-eu-visa-routes.html":
            rep.add("WARN", "canonical-mismatch", rel, f"canonical {href} != {expected}")
    if rel == "404.html" and "noindex" not in meta(c, "robots").lower():
        rep.add("WARN", "404-noindex", rel, "404 page should carry <meta name=robots content=noindex>")

    # ---- social cards -----------------------------------------------------
    if not noindex and not exempt:
        for prop in OG_REQUIRED:
            if not meta(c, prop, prop=True):
                rep.add("WARN", "og-missing", rel, f"missing {prop}")
        for prop in TW_REQUIRED:
            if not meta(c, prop):
                rep.add("WARN", "twitter-missing", rel, f"missing {prop}")
        og_img = meta(c, "og:image", prop=True)
        if og_img and og_img.startswith("http") and not (ROOT / og_img.replace(BASE_URL + "/", "")).exists():
            rep.add("ERROR", "og-image-404", rel, f"og:image file not found: {og_img}")

    # ---- headings ---------------------------------------------------------
    h1s = [d for t, d in c.tags if t == "h1"]
    level_counts: dict[int, int] = defaultdict(int)
    for t, _ in c.tags:
        if re.fullmatch(r"h[1-6]", t):
            level_counts[int(t[1])] += 1
    if not exempt and not h1s and not noindex:
        rep.add("ERROR", "h1-missing", rel, "no <h1> on the page")
    elif len(h1s) > 1:
        rep.add("WARN", "h1-multiple", rel, f"{len(h1s)} <h1> elements")
    # heading hierarchy: an h3 before any h2, or skipping a level
    seq = [int(t[1]) for t, _ in c.tags if re.fullmatch(r"h[1-6]", t)]
    prev = 0
    for lvl in seq:
        if prev and lvl > prev + 1:
            rep.add("INFO", "heading-skip", rel, f"heading level jumps h{prev} → h{lvl}")
            break
        prev = lvl

    # ---- structured data --------------------------------------------------
    if not noindex and not exempt and not c.ld_json:
        rep.add("WARN", "ld-missing", rel, "no JSON-LD structured data")
    for blob in c.ld_json:
        try:
            data = json.loads(blob)
        except json.JSONDecodeError as e:
            rep.add("ERROR", "ld-invalid", rel, f"JSON-LD does not parse: {e}")
            continue
        for obj in data if isinstance(data, list) else [data]:
            check_ld(obj, rel, rep)
            check_ld_refs(obj, rel, rep)
    check_duplicate_schema(c, rel, rep)

    # ---- images -----------------------------------------------------------
    for t, d in c.tags:
        if t != "img":
            continue
        src = d.get("src", "")
        if "alt" not in d:
            rep.add("ERROR", "img-alt", rel, f"<img> without alt: {src}")
        if not d.get("width") or not d.get("height"):
            rep.add("WARN", "img-dimensions", rel, f"<img> without width/height (CLS risk): {src}")
        if not d.get("decoding"):
            rep.add("INFO", "img-decoding", rel, f"<img> without decoding=async: {src}")
    if re.search(r"<iframe", html) and 'loading="lazy"' not in html:
        rep.add("INFO", "iframe-lazy", rel, "<iframe> without loading=lazy")

    # ---- internal links ---------------------------------------------------
    internal: set[str] = set()
    for t, d in c.tags:
        if t != "a":
            continue
        href = d.get("href", "").strip()
        if not href or href.startswith(("http://", "https://", "mailto:", "tel:", "#", "javascript:")):
            continue
        target = href.split("#")[0].split("?")[0]
        if not target:
            continue
        internal.add(target)
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            rep.add("ERROR", "broken-link", rel, f"internal link to a missing file: {target}")
    # anchor text quality
    text = c.text.lower()
    del text

    # ---- Core Web Vitals heuristics ---------------------------------------
    head_html = html[: html.lower().find("</head>")] if "</head>" in html.lower() else html
    for m2 in re.finditer(r"<script[^>]*\ssrc=\"([^\"]+)\"[^>]*>", head_html):
        tag = m2.group(0)
        src = m2.group(1)
        if "async" in tag or "defer" in tag:
            continue
        if src.startswith("http"):
            rep.add("WARN", "render-blocking-js", rel, f"third-party blocking script in <head>: {src}")
        else:
            rep.add("INFO", "blocking-local-js", rel, f"small local script in <head> (no defer): {src}")
    if re.search(r"<script src=\"https://cdn\.tailwindcss\.com", html):
        rep.add("ERROR", "tailwind-cdn", rel,
                "Tailwind Play CDN compiles CSS in the browser (~400 KB JS) — ship a built stylesheet")
    head_no_noscript = re.sub(r"<noscript>.*?</noscript>", "", head_html, flags=re.S | re.I)
    for src in re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', head_no_noscript):
        if src.startswith("http"):
            rep.add("WARN", "render-blocking-css", rel, f"third-party blocking stylesheet: {src}")
    for host, label in CWV_THIRD_PARTIES.items():
        if host in html and f'preconnect" href="https://{host}' not in html and \
                f'preconnect" href="https://{host}/' not in html:
            rep.add("INFO", "no-preconnect", rel, f"no preconnect for {label} ({host})")
    for m3 in re.finditer(r'<img[^>]+src="([^"]+)"', html):
        f = ROOT / m3.group(1).lstrip("/")
        if f.exists() and f.stat().st_size > 200_000:
            rep.add("WARN", "img-heavy", rel, f"image >200 KB: {m3.group(1)} ({f.stat().st_size // 1024} KB)")

    # ---- content depth ----------------------------------------------------
    words = len(c.text.split())
    if not noindex and not exempt and words < 300 and rel not in ("404.html",):
        rep.add("INFO", "thin-content", rel, f"only {words} words of visible text")

    # ---- sitemap membership ----------------------------------------------
    if not noindex and not exempt and rel not in in_sitemap and rel != "404.html":
        rep.add("WARN", "not-in-sitemap", rel, "indexable page is missing from sitemap.xml")


LD_REQUIRED = {
    "Article": ("headline",),
    "NewsArticle": ("headline",),
    "BlogPosting": ("headline",),
    "FAQPage": ("mainEntity",),
    "JobPosting": ("title", "description", "datePosted", "hiringOrganization", "jobLocation"),
    "Organization": ("name",),
    "WebSite": ("url", "name"),
    "BreadcrumbList": ("itemListElement",),
    "WebPage": ("name",),
    "CollectionPage": ("name",),
    "ItemList": ("itemListElement",),
    "SoftwareApplication": ("name", "applicationCategory"),
    "ContactPage": ("name",),
    "AboutPage": ("name",),
}
LD_TYPES = set(LD_REQUIRED)


def walk_ld(obj):
    """Yield every schema.org node, including @graph members (once each)."""
    if isinstance(obj, dict):
        if "@type" in obj:
            yield obj
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                yield from walk_ld(value)
    elif isinstance(obj, list):
        for sub in obj:
            yield from walk_ld(sub)


def check_ld(obj, rel: str, rep: Report) -> None:
    types: list[str] = []
    for node in walk_ld(obj):
        t = node.get("@type")
        types.extend(t if isinstance(t, list) else [t])
    if not types:
        rep.add("WARN", "ld-no-type", rel, "JSON-LD block without @type")
        return
    for node in walk_ld(obj):
        t = node.get("@type")
        t = t[0] if isinstance(t, list) else t
        req = LD_REQUIRED.get(t)
        if not req:
            continue
        missing = [k for k in req if not node.get(k)]
        if missing:
            rep.add("ERROR", "ld-incomplete", rel, f"{t} missing {', '.join(missing)}")
        if t == "FAQPage":
            for q in node.get("mainEntity") or []:
                if not (isinstance(q, dict) and q.get("name") and
                        isinstance(q.get("acceptedAnswer"), dict) and
                        q["acceptedAnswer"].get("text")):
                    rep.add("ERROR", "ld-faq", rel, "FAQPage entry without name/acceptedAnswer.text")
        if t in ("Article", "NewsArticle", "BlogPosting"):
            if not node.get("datePublished"):
                rep.add("WARN", "ld-article-datePublished", rel,
                        "Article without datePublished (Google uses it for freshness)")
        if t == "JobPosting":
            if not node.get("validThrough"):
                rep.add("WARN", "ld-jobposting-validThrough", rel,
                        "JobPosting without validThrough (Google recommends it for expiry)")
            if not node.get("employmentType"):
                rep.add("INFO", "ld-jobposting-employmentType", rel,
                        "JobPosting without employmentType")
    if "FAQPage" in types and not any(t in ("Article", "WebPage", "CollectionPage") for t in types) \
            and rel not in ("index.html",):
        rep.add("INFO", "ld-faq-only", rel, "page has FAQPage but no Article/WebPage node")


def check_ld_refs(obj, rel: str, rep: Report) -> None:
    """Resolve @id references (e.g. Article.publisher → Organization) and check
    that targets carry the fields rich results need."""
    by_id: dict[str, dict] = {}
    for node in walk_ld(obj):
        if node.get("@id"):
            by_id[str(node["@id"])] = node
    for node in walk_ld(obj):
        if node.get("@type") in ("Article", "NewsArticle", "BlogPosting"):
            pub = node.get("publisher")
            target = None
            if isinstance(pub, dict):
                target = by_id.get(str(pub.get("@id"))) if pub.get("@id") else pub
            if isinstance(target, dict) and not target.get("logo"):
                rep.add("INFO", "ld-publisher-logo", rel,
                        "Article publisher has no ImageObject logo (needed for rich results)")


def check_duplicate_schema(c: TagCollector, rel: str, rep: Report) -> None:
    """A page should not declare the same top-level @type twice.

    Only graph members count: an Article's nested `author`/`publisher`
    Organization is a property, not a competing entity, so recursion into
    values would produce false positives.
    """
    seen: dict[str, int] = defaultdict(int)
    for blob in c.ld_json:
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        for obj in data if isinstance(data, list) else [data]:
            members = obj.get("@graph") if isinstance(obj, dict) else None
            members = members if isinstance(members, list) else [obj]
            for node in members:
                if not isinstance(node, dict):
                    continue
                t = node.get("@type")
                if isinstance(t, list):
                    t = t[0]
                if t:
                    seen[t] += 1
    for t, n in seen.items():
        if n > 1:
            rep.add("INFO", "ld-duplicate", rel, f"{t} declared {n}× at graph level — merge into one node")


# --------------------------------------------------------------------------- #
# site-wide checks
# --------------------------------------------------------------------------- #
def load_sitemap(rep: Report) -> set[str]:
    if not SITEMAP.exists():
        rep.add("ERROR", "sitemap", "-", "sitemap.xml is missing")
        return set()
    xml = SITEMAP.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", xml)
    urls = set()
    for loc in locs:
        if not loc.startswith(BASE_URL):
            rep.add("WARN", "sitemap-foreign", "-", f"sitemap URL outside the canonical host: {loc}")
            continue
        rel = loc[len(BASE_URL):].lstrip("/") or "index.html"
        urls.add(rel)
        if not (ROOT / rel).exists():
            rep.add("ERROR", "sitemap-404", "-", f"sitemap lists a page that does not exist: {rel}")
    lastmods = re.findall(r"<lastmod>([^<]+)</lastmod>", xml)
    if len(lastmods) < len(locs):
        rep.add("WARN", "sitemap-lastmod", "-",
                f"{len(locs) - len(lastmods)} sitemap entries without <lastmod>")
    return urls


def check_robots(rep: Report) -> None:
    if not ROBOTS.exists():
        rep.add("ERROR", "robots", "-", "robots.txt is missing")
        return
    txt = ROBOTS.read_text(encoding="utf-8")
    if "sitemap:" not in txt.lower():
        rep.add("WARN", "robots-sitemap", "-", "robots.txt has no Sitemap: line")
    if re.search(r"^disallow:\s*/\s*$", txt, re.I | re.M):
        rep.add("ERROR", "robots-blockall", "-", "robots.txt disallows the whole site")


def check_duplicates(pages: dict[str, TagCollector], rep: Report) -> None:
    titles: dict[str, list[str]] = defaultdict(list)
    descs: dict[str, list[str]] = defaultdict(list)
    for rel, c in pages.items():
        m = re.search(r"<title[^>]*>(.*?)</title>", (ROOT / rel).read_text(encoding="utf-8"), re.S)
        if m:
            titles[re.sub(r"\s+", " ", m.group(1)).strip()].append(rel)
        d = meta(c, "description")
        if d:
            descs[d].append(rel)
    for t, files in titles.items():
        if len(files) > 1 and t:
            rep.add("ERROR", "duplicate-title", files[0], f"same <title> on {len(files)} pages: {files}")
    for d, files in descs.items():
        if len(files) > 1:
            rep.add("WARN", "duplicate-desc", files[0], f"same meta description on {len(files)} pages: {files}")


def check_internal_graph(pages: dict[str, TagCollector], rep: Report) -> None:
    inbound: dict[str, set[str]] = defaultdict(set)
    outbound: dict[str, set[str]] = defaultdict(set)
    generic = 0
    for rel, c in pages.items():
        for t, d in c.tags:
            if t != "a":
                continue
            href = d.get("href", "").split("#")[0].split("?")[0]
            if not href or href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:")):
                continue
            if href not in pages:
                continue
            outbound[rel].add(href)
            inbound[href].add(rel)

    for rel in pages:
        if rel in EXEMPT_FROM_CONTENT or rel == "404.html":
            continue
        sources = inbound.get(rel, set())
        if not sources and rel != "index.html":
            sev = "INFO" if rel.startswith("jobs/") else "ERROR"
            rep.add(sev, "orphan", rel, "no internal links point to this page")

    # link depth from the homepage (crawl budget / PageRank flow)
    depth = {"index.html": 0}
    frontier = ["index.html"]
    while frontier:
        nxt = []
        for node in frontier:
            for link_to in outbound.get(node, ()):
                if link_to not in depth:
                    depth[link_to] = depth[node] + 1
                    nxt.append(link_to)
        frontier = nxt
    for rel in pages:
        if rel in EXEMPT_FROM_CONTENT or rel == "404.html" or rel.startswith("jobs/"):
            continue
        d = depth.get(rel)
        if d is None:
            rep.add("WARN", "unreachable", rel, "not reachable from index.html by internal links")
        elif d > 2:
            rep.add("INFO", "deep-click", rel, f"{d} clicks from the homepage")

    # weak pages: fewer than 3 inbound internal links
    for rel, sources in sorted(inbound.items()):
        if rel in EXEMPT_FROM_CONTENT or rel == "index.html" or rel.startswith("jobs/"):
            continue
        if len(sources) < 3:
            rep.add("WARN", "weak-inlinks", rel,
                    f"only {len(sources)} page(s) link here: {sorted(sources)}")

    # anchor text quality (generic anchors are an SEO smell)
    for rel in pages:
        html = (ROOT / rel).read_text(encoding="utf-8")
        for m in re.finditer(r"<a[^>]*>(.*?)</a>", html, re.S):
            txt = re.sub(r"<[^>]+>", "", m.group(1))
            txt = re.sub(r"\s+", " ", txt.replace("&amp;", "&")).strip().lower()
            if txt in GENERIC_ANCHORS and m.group(0).count('href="http') == 0:
                generic += 1
    if generic > 20:
        rep.add("INFO", "generic-anchors", "-", f"{generic} generic anchor texts on the site")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="WintWorks static SEO / CWV audit")
    ap.add_argument("--all", action="store_true", help="audit every jobs/*.html page")
    ap.add_argument("--json", metavar="PATH", help="also write a JSON report")
    ap.add_argument("--no-fail", action="store_true", help="always exit 0")
    ap.add_argument("--max-jobs-pages", type=int, default=25)
    args = ap.parse_args()

    rep = Report()
    sitemap_urls = load_sitemap(rep)
    check_robots(rep)

    root_pages = sorted(p.name for p in ROOT.glob("*.html"))
    jobs_pages = sorted(p.name for p in (ROOT / "jobs").glob("*.html"))
    if not args.all and len(jobs_pages) > args.max_jobs_pages:
        step = max(1, len(jobs_pages) // args.max_jobs_pages)
        jobs_pages = jobs_pages[::step][: args.max_jobs_pages]

    pages: dict[str, TagCollector] = {}
    for rel in root_pages:
        pages[rel] = parse(ROOT / rel)
    for rel in jobs_pages:
        pages[f"jobs/{rel}"] = parse(ROOT / "jobs" / rel)

    sitemap_rel = set(sitemap_urls)
    for rel in root_pages:
        check_page(ROOT / rel, rel, rep, sitemap_rel)
    for rel in jobs_pages:
        check_page(ROOT / "jobs" / rel, f"jobs/{rel}", rep, sitemap_rel)

    check_duplicates(pages, rep)
    check_internal_graph(pages, rep)

    errors = [i for i in rep.items if i["severity"] == "ERROR"]
    warns = [i for i in rep.items if i["severity"] == "WARN"]
    infos = [i for i in rep.items if i["severity"] == "INFO"]

    by_code: dict[str, list[dict]] = defaultdict(list)
    for i in rep.items:
        by_code[i["code"]].append(i)

    print(f"WintWorks SEO audit — {len(pages)} pages "
          f"({len(root_pages)} root + {len(jobs_pages)} jobs)")
    print(f"  {len(errors)} errors · {len(warns)} warnings · {len(infos)} notes\n")
    for code in sorted(by_code, key=lambda k: (min("EWI".index(i['severity'][0]) for i in by_code[k]), k)):
        items = by_code[code]
        sev = min(items, key=lambda i: "EWI".index(i["severity"][0]))["severity"]
        print(f"[{sev}] {code} ×{len(items)}")
        shown = items[:4] if len(items) > 4 else items
        for i in shown:
            print(f"    {i['page']:<38} {i['message']}")
            if i["detail"]:
                print(f"        → {i['detail'][:110]}")
        if len(items) > len(shown):
            print(f"    … and {len(items) - len(shown)} more")
        print()

    if args.json:
        Path(args.json).write_text(json.dumps(rep.items, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"JSON report → {args.json}")

    if errors and not args.no_fail:
        print(f"FAILED: {len(errors)} SEO errors")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
