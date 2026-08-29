#!/usr/bin/env python3
"""
WintWorks — scholarships snapshot builder
Fetches scholarships from free public APIs, normalises them,
and writes data/scholarships.json — mirrors the jobs/snapshot pattern.

Sources (free tier, no fees):
  • ScholarshipAPI.com  →  env SCHOLARSHIPAPI_KEY   (free: 100 req/day)
  • Scholarships.com    →  env SCHOLARSHIPS_COM_KEY  (Parse API free tier)

If no API keys are configured, the script still writes a seed snapshot
from built-in sample data so pages render on first deploy.
"""

import json, os, re, sys, time
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(BASE, "data", "scholarships.json")

UA = {"User-Agent": "Mozilla/5.0 (compatible; WintWorks/1.0)"}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _get(url, timeout=25, headers=None):
    h = {**UA, **(headers or {})}
    req = urllib_request.Request(url, headers=h)
    with urllib_request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _post(url, payload, token, timeout=25):
    data = json.dumps(payload).encode()
    req = urllib_request.Request(
        url, data=data,
        headers={
            "User-Agent":   UA["User-Agent"],
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
    with urllib_request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# region / country helpers  (mirrors the jobs taxonomy)
# ---------------------------------------------------------------------------
EU_COUNTRIES = {
    "Germany","France","Netherlands","Spain","Poland","Italy",
    "United Kingdom","Ireland","Sweden","Norway","Denmark","Finland",
    "Iceland","Austria","Switzerland","Belgium","Portugal",
    "Czechia","Slovakia","Hungary","Romania","Bulgaria","Greece",
    "Croatia","Slovenia","Serbia","Bosnia & Herzegovina",
    "Montenegro","North Macedonia","Albania","Kosovo",
    "Estonia","Latvia","Lithuania","Ukraine","Moldova","Belarus",
    "Malta","Cyprus","Turkey","Georgia","Armenia","Azerbaijan",
    "Monaco","Luxembourg","Andorra","Liechtenstein","Gibraltar",
}

US_STATES = {
    "alabama","alaska","arizona","arkansas","california","colorado",
    "connecticut","delaware","florida","georgia","hawaii","idaho",
    "illinois","indiana","iowa","kansas","kentucky","louisiana","maine",
    "maryland","massachusetts","michigan","minnesota","mississippi",
    "missouri","montana","nebraska","nevada","new hampshire","new jersey",
    "new mexico","new york","north carolina","north dakota","ohio",
    "oklahoma","oregon","pennsylvania","rhode island","south carolina",
    "south dakota","tennessee","texas","utah","vermont","virginia",
    "washington","west virginia","wisconsin","wyoming","district of columbia",
}

ARAB_COUNTRIES = {
    "Egypt","Morocco","Tunisia","Algeria","Jordan","Lebanon",
    "United Arab Emirates","Saudi Arabia","Oman","Bahrain","Qatar",
    "Palestine","Syria","Iraq","Sudan","Libya","Mauritania",
    "Djibouti","Yemen","Somalia","Comoros","Somaliland",
}


def _region_of(text):
    """'US' | 'EU' | 'WW' | None  — strong beats weak, mirrors jobs logic."""
    if not text:
        return None
    s = str(text).lower()
    eu_words = [
        "europe","european","united kingdom","britain","british","england",
        "scotland","wales","northern ireland","ireland","france","germany",
        "deutschland","allemagne","spain","españa","italy","italia",
        "portugal","netherlands","nederland","holland","belgium","belgique",
        "belgie","luxembourg","switzerland","schweiz","suisse","austria",
        "österreich","sweden","sverige","norway","norge","denmark","danmark",
        "finland","suomi","iceland","poland","polska","polen","czech",
        "czechia","czech republic","slovakia","hungary","romania","bulgaria",
        "greece","croatia","slovenia","serbia","bosnia","montenegro",
        "macedonia","albania","kosovo","estonia","latvia","lithuania",
        "ukraine","moldova","belarus","russia","malta","cyprus","turkey",
        "türkiye","georgien","armenia","azerbaijan","monaco","andorra",
        "liechtenstein","gibraltar","isle of man","bavaria","bayern",
    ]
    arab_words = [
        "egypt","egyptian","morocco","moroccan","tunisia","tunisian",
        "algeria","algerian","jordan","jordanian","lebanon","lebanese",
        "uae","emirati","dubai","abu dhabi","saudi","saudi arabia",
        "oman","omani","bahrain","bahraini","qatar","qatari",
        "palestine","palestinian","syria","syrian","iraq","iraqi",
        "sudan","sudanese","libya","libyan","mauritania","mauritanian",
        "djibouti","yemen","yemeni","somalia","somalian","comoros",
        "levant","arab","arab world","arab league","league of arab states",
        "maghreb","middle east","mena",
    ]
    us_words = [
        "united states","usa","u.s.a","us only","america","american",
        *US_STATES,
    ]
    ww_words = [
        "worldwide","anywhere","any country","global","all countries",
        "international","emea","remote","homeoffice","fully remote",
        "work from home","wfh","no location",
    ]
    us_strong = any(re.search(r"\b"+re.escape(w)+r"\b", s) for w in us_words)
    eu_strong = any(re.search(r"\b"+re.escape(w)+r"\b", s) for w in eu_words)
    arab_strong = any(re.search(r"\b"+re.escape(w)+r"\b", s) for w in arab_words)
    ww_hit    = any(w in s for w in ww_words)
    if us_strong and (eu_strong or arab_strong):
        return "WW"
    if us_strong:
        return "US"
    if eu_strong:
        return "EU"
    if arab_strong:
        return "AR"  # Arab region
    if ww_hit:
        return "WW"
    for c in EU_COUNTRIES:
        if c.lower() in s:
            return "EU"
    # check Arab countries individually by name
    for c in ARAB_COUNTRIES:
        if c.lower() in s:
            return "AR"
    return None


def _country_of(text):
    if not text:
        return ""
    s = str(text).lower()
    r = _region_of(text)
    if r == "US":
        return "USA"
    if r == "AR":
        for c in sorted(ARAB_COUNTRIES, key=len, reverse=True):
            if c.lower() in s:
                return c
        return ""
    if r != "EU":
        return ""
    for c in sorted(EU_COUNTRIES, key=len, reverse=True):
        if c.lower() in s:
            return c
    return ""


# ---------------------------------------------------------------------------
# scholarship taxonomy
# ---------------------------------------------------------------------------
FUNDING_TYPES = [
    ("Fully Funded",    ["fully funded","full funding","full ride",
                         "covers tuition","full scholarship","fully-funded",
                         "100% funded","complete funding","fully funded scholarship"]),
    ("Partially Funded",["partial","partially funded","partial scholarship",
                         "partial funding","partial grant","partial coverage",
                         "partial award"]),
    ("Government",      ["government","state scholarship","national scholarship",
                         "public fund"," ministry ","gov scholarship",
                         "government grant","state grant"]),
    ("Fellowship",      ["fellowship","postdoctoral fellowship","research fellowship",
                         "doctoral fellowship","phd fellowship"]),
    ("Annual",          ["annual","yearly","recurring","renewable",
                         "renewable scholarship","annual scholarship"]),
    ("Self Funded",     ["self funded","self-funded","unfunded",
                         "pay your own","tuition only"]),
]

LEVELS = [
    ("Bachelor",   ["bachelor","undergraduate","bachelors"," ug ","undergrad"]),
    ("Masters",    ["master","masters","graduate","ma ","ms ","msc","meng","mlitt"," postgraduate ","postgrad"]),
    ("PhD",        ["phd","doctoral","doctorate","dphil","edd","dba"]),
    ("Fellowship", ["fellowship","postdoctoral","postdoc"]),
    ("Internship", ["internship","summer program","summer school","short term"]),
    ("Exchange",   ["exchange","study abroad","mobility","erasmus","exchange program"]),
]


def _funding_type(title, desc):
    blob = f"{title or ''} {desc or ''}".lower()
    for ftype, keys in FUNDING_TYPES:
        if any(k in blob for k in keys):
            return ftype
    return "Annual"


def _level(title, desc):
    """Earliest level keyword mentioned wins (a post about both bachelor
    and master programmes usually leads with the primary one)."""
    blob = f"{title or ''} {desc or ''}".lower()
    best, best_pos = "", 1 << 30
    for lvl, keys in LEVELS:
        for k in keys:
            p = blob.find(k)
            if p != -1 and p < best_pos:
                best_pos, best = p, lvl
    return best


def _amount(text):
    """Extract numeric amount from strings like '€15,000' or '$25,000'."""
    if not text:
        return None
    m = re.search(r"([£$€¥₹]\s*)?([\d,.]+)", str(text).replace(",", ""))
    if m:
        try:
            return float(m.group(2).replace(",", ""))
        except ValueError:
            pass
    return None


def _parse_date(raw):
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw).isoformat()
    except (ValueError, TypeError):
        pass
    for fmt in ("%Y-%m-%d","%m/%d/%Y","%d/%m/%Y","%B %d, %Y",
                "%d %B %Y","%b %d, %Y","%Y/%m/%d"):
        try:
            return datetime.strptime(raw.strip(), fmt).isoformat()
        except (ValueError, TypeError):
            continue
    return ""


def _parse_dt(raw):
    """Parse an ISO deadline into an aware datetime, or None."""
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw))
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _deadline_remains(deadline_iso):
    if not deadline_iso:
        return ""
    try:
        d = datetime.fromisoformat(deadline_iso)
        diff = (d - datetime.now(timezone.utc)).days
        if diff < 0:
            return "Closed"
        if diff == 0:
            return "Today"
        if diff == 1:
            return "Tomorrow"
        if diff < 30:
            return f"{diff} days left"
        if diff < 365:
            return f"{diff // 30} months left"
        return f"{diff // 365} years left"
    except (ValueError, TypeError):
        return ""


# ---------------------------------------------------------------------------
# source: ScholarshipAPI.com  (primary, free tier)
# ---------------------------------------------------------------------------
def fetch_scholarshipapi(token):
    out = []
    page = 1
    while True:
        try:
            data = _post(
                "https://api.scholarshipapi.com/v1/search",
                {"q": "", "limit": 100, "offset": (page - 1) * 100},
                token,
            )
        except Exception as e:
            print(f"[scholarshipapi] page {page} failed: {e}", file=sys.stderr)
            break
        hits = data.get("hits") or []
        if not hits:
            break
        for h in hits:
            loc = h.get("university", "")
            region = _region_of(loc) or _region_of(h.get("primaryCategory", ""))
            amount_raw = h.get("amount")
            amount_str  = ""
            amount_val  = None
            if amount_raw:
                amount_str = f"{amount_raw} {h.get('currency','')}"
                amount_val = _amount(str(amount_raw))
            deadline_iso = ""
            if h.get("closeDate"):
                try:
                    ms = int(h["closeDate"])
                    deadline_iso = datetime.fromtimestamp(
                        ms / 1000, tz=timezone.utc).isoformat()
                except (ValueError, TypeError):
                    pass
            title = h.get("name", "")
            if not title:
                continue
            sid = re.sub(r"[^a-z0-9]+", "-", title.lower())[:40]
            if h.get("university"):
                sid += "-" + re.sub(r"[^a-z0-9]+", "-", h["university"].lower())[:15]
            out.append({
                "id":        f"schapi-{sid}",
                "title":     title,
                "provider":  h.get("university", ""),
                "location":  loc or "",
                "region":    region or "",
                "country":   _country_of(loc),
                "remote":    h.get("status") == "open",
                "funding":   h.get("primaryCategory", "") or "Annual",
                "amount":    amount_val,
                "amount_str": amount_str,
                "deadline":  deadline_iso,
                "deadline_remains": _deadline_remains(deadline_iso),
                "level":     _level(title, h.get("primaryCategory","")),
                "description": h.get("eligibilitySummary","") or "",
                "tags":      [t for t in (h.get("targetGroups") or [])
                               if isinstance(t, str)][:4],
                "url":       h.get("url","") or "",
                "source":    "ScholarshipAPI",
                "posted_ago": "",
            })
        page += 1
        if page > 3:          # cap: 3 × 100 = 300 — within free-tier limit
            break
        time.sleep(0.3)
    return out


# ---------------------------------------------------------------------------
# source: Scholarships.com  (via Parse API, free tier)
# ---------------------------------------------------------------------------
def fetch_scholarships_com():
    """Pull from Scholarships.com directory via Parse REST API (free tier)."""
    out = []
    base = "https://parseapi.backend/9dccd551-0b32-432f-ac0c-c070031ba36d"
    try:
        categories = _get(f"{base}/scholarships-com-api/categories", timeout=20) or []
    except Exception as e:
        print(f"[scholarships.com] categories failed: {e}", file=sys.stderr)
        return out

    for cat in categories[:2]:          # stay within free-tier budget
        cat_slug = cat.get("slug", "")
        try:
            subcats = _get(
                f"{base}/scholarships-com-api/category/{cat_slug}/subcategories",
                timeout=20) or []
        except Exception:
            continue
        for sub in subcats[:3]:
            subslug = sub.get("slug", "")
            try:
                listings = _get(
                    f"{base}/scholarships-com-api/category/{cat_slug}/scholarships"
                    f"?subcategory={subslug}",
                    timeout=20) or []
            except Exception:
                continue
            for s in listings[:15]:
                title = s.get("name") or ""
                if not title:
                    continue
                loc  = s.get("state","") or ""
                region = _region_of(loc) or ""
                detail = {}
                try:
                    detail = _get(
                        f"{base}/scholarships-com-api/scholarship/"
                        f"{s.get('slug','')}/detail",
                        timeout=20) or {}
                except Exception:
                    pass
                amount_raw = detail.get("amount") or s.get("amount")
                amount_str  = ""
                amount_val  = None
                if amount_raw:
                    amount_str  = str(amount_raw)
                    amount_val  = _amount(amount_str)
                deadline_iso = _parse_date(
                    detail.get("deadline") or s.get("deadline"))
                sid = re.sub(r"[^a-z0-9]+", "-",
                             (title or "").lower())[:40]
                out.append({
                    "id":         f"schcoms-{sid}",
                    "title":      title,
                    "provider":   detail.get("provider","") or "",
                    "location":   loc or "",
                    "region":     region,
                    "country":    _country_of(loc),
                    "remote":     False,
                    "funding":    "Annual",
                    "amount":     amount_val,
                    "amount_str": amount_str,
                    "deadline":   deadline_iso,
                    "deadline_remains": _deadline_remains(deadline_iso),
                    "level":      "",
                    "description": detail.get("eligibility","") or "",
                    "tags":       [],
                    "url":        detail.get("apply_url", s.get("url","")) or "",
                    "source":     "Scholarships.com",
                    "posted_ago": "",
                })
            time.sleep(0.2)
    return out


# ---------------------------------------------------------------------------
# source: Scholars4Dev  (best-effort scrape of listing pages)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# source: WordPress REST API scholarship aggregators (free, no API keys)
#
# These sites run WordPress and expose a stable, documented JSON endpoint:
#   GET {base}/wp-json/wp/v2/posts?per_page=100&page=N
# Far more reliable than HTML scraping (the old regex scraper silently
# returned 0 items from scholars4dev while reporting success).
#
# Verified sources:
#   • scholars4dev.com          — international scholarship listings
#   • scholarshipscorner.website — scholarships/fellowships, updated daily
#   • opportunitiesforyouth.org — scholarships, fellowships, grants for youth
# ---------------------------------------------------------------------------
WP_SOURCES = [
    {"name": "Scholars4Dev",         "base": "https://www.scholars4dev.com",     "pages": 2},
    {"name": "ScholarshipsCorner",   "base": "https://scholarshipscorner.website", "pages": 2},
    {"name": "OpportunitiesForYouth","base": "https://opportunitiesforyouth.org",  "pages": 2},
]

_BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# posts that are clearly not funding opportunities (e.g. plain internships,
# news, "how to apply" guides) are filtered out
_FUNDING_WORDS_RX = re.compile(
    r"scholarship|fellowship|grant|bursar|funding|stipend|financial aid|award",
    re.I)

_MONTHS = {}
for _i, _m in enumerate(
        ["january","february","march","april","may","june","july",
         "august","september","october","november","december"], 1):
    _MONTHS[_m] = _i
    _MONTHS[_m[:3]] = _i
_MONTHS["sept"] = 9

_DATE_PATTERNS = [
    # 18 Sept 2026 / 18th September, 2026 / 1 May 2027
    (re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})",
                re.I), "dmy"),
    # December 01, 2026 / December 1 2026
    (re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})",
                re.I), "mdy"),
    # 2026-09-18
    (re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"), "iso"),
    # 18/09/2026 or 18.09.2026  (interpreted as day/month/year)
    (re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b"), "dmnum"),
]

_DEADLINE_WORD_RX = re.compile(
    r"dead\s*line|deadline|closing date|closes?\s+(?:on|date)|apply by|last date",
    re.I)


def _strip_html(html):
    """Remove tags, decode common entities, collapse whitespace."""
    if not html:
        return ""
    txt = re.sub(r"<(script|style)\b.*?</\1>", " ", html,
                 flags=re.I | re.DOTALL)
    txt = re.sub(r"<br\s*/?>", "\n", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    for ent, ch in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                    ("&gt;", ">"), ("&quot;", '"'), ("&#8217;", "'"),
                    ("&#8216;", "'"), ("&#8220;", '"'), ("&#8221;", '"'),
                    ("&#8230;", "..."), ("&rsquo;", "'"), ("&ndash;", "-"),
                    ("&mdash;", "-"), ("&#x27;", "'")):
        txt = txt.replace(ent, ch)
    txt = re.sub(r"&#\d+;", " ", txt)
    return re.sub(r"[ \t\u00a0]+", " ", txt).strip()


def _find_date(s):
    """Return ISO date for the first plausible date in *s*, else ''."""
    for rx, kind in _DATE_PATTERNS:
        m = rx.search(s)
        if not m:
            continue
        try:
            if kind == "dmy":
                d, mm, y = int(m.group(1)), _MONTHS.get(
                    m.group(2).lower().rstrip(".")), int(m.group(3))
            elif kind == "mdy":
                mm, d, y = _MONTHS.get(m.group(1).lower().rstrip(".")), \
                    int(m.group(2)), int(m.group(3))
            elif kind == "iso":
                y, mm, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            else:  # dmnum
                d, mm, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if not mm or not (1 <= d <= 31) or not (2000 <= y <= 2100):
                continue
            return datetime(y, mm, d, 23, 59, tzinfo=timezone.utc).isoformat()
        except (ValueError, TypeError):
            continue
    return ""


def _extract_deadline(text):
    """Find a deadline date near the word 'deadline' (falls back to the
    start of the text). Returns an ISO string, end-of-day UTC, or ''."""
    if not text:
        return ""
    windows = []
    for m in _DEADLINE_WORD_RX.finditer(text):
        windows.append(text[max(0, m.start() - 40): m.end() + 140])
    if not windows:
        windows = [text[:400]]
    for win in windows:
        iso = _find_date(win)
        if iso:
            return iso
    return ""


_AMT_RX = re.compile(
    r"([£$€]\s?(\d[\d,.]{2,}))"                    # £15,000  $10,000  €1,500
    r"|(\b(?:CHF|SEK|NOK|DKK|EUR|USD|GBP|AUD|CAD|INR|JPY))\s?(\d[\d,.]{2,})",
    re.I)

_CURRENCY_SYMBOL = {"£": "£", "$": "$", "€": "€"}


def _extract_amount(text):
    """(numeric_amount, display_string) from real-world money mentions."""
    if not text:
        return None, ""
    m = _AMT_RX.search(text[:4000])
    if not m:
        return None, ""
    if m.group(1):
        sym, digits = m.group(1)[0], m.group(2)
    else:
        cur, digits = m.group(3).upper(), m.group(4)
        sym = {"CHF": "CHF ", "SEK": "SEK ", "NOK": "NOK ", "DKK": "DKK ",
               "EUR": "€", "USD": "$", "GBP": "£", "AUD": "A$",
               "CAD": "C$", "INR": "₹", "JPY": "¥"}.get(cur, cur + " ")
    clean = digits.replace(",", "").rstrip(".")
    try:
        num = float(clean)
    except ValueError:
        return None, ""
    if not (500 <= num <= 2_000_000):   # filter noise ($5, €20 fees…)
        return None, ""
    return num, f"{sym}{digits.strip()}"


def _wp_fetch_posts(base, page=1, per_page=100, timeout=25):
    """One page of posts from a WordPress site's public REST API."""
    fields = "id,date,link,title,content,excerpt,slug,class_list"
    url = (f"{base}/wp-json/wp/v2/posts"
           f"?per_page={per_page}&page={page}&_fields={fields}")
    try:
        return _get(url, timeout=timeout, headers={"User-Agent": _BROWSER_UA,
                                                   "Accept": "application/json"})
    except Exception as e:
        # invalid page number = past the last page → stop paging quietly
        if getattr(e, "code", None) == 400 and page > 1:
            return []
        # some older WP versions reject _fields with class_list — retry plain
        if getattr(e, "code", None) == 400:
            url = (f"{base}/wp-json/wp/v2/posts"
                   f"?per_page={per_page}&page={page}"
                   f"&_fields=id,date,link,title,content,excerpt,slug")
            return _get(url, timeout=timeout,
                        headers={"User-Agent": _BROWSER_UA,
                                 "Accept": "application/json"})
        raise


def _wp_post_to_scholarship(source_name, p):
    """Convert a WP REST post into a scholarship snapshot row (or None)."""
    if not isinstance(p, dict):
        return None
    title = _strip_html((p.get("title") or {}).get("rendered", "")).strip()
    link  = (p.get("link") or "").strip()
    if not title or len(title) < 8 or not link.startswith("http"):
        return None

    classes   = " ".join(p.get("class_list") or [])
    class_txt = classes.replace("category-", " ").replace("tag-", " ")
    class_txt = _strip_html(class_txt.replace("-", " "))

    if not _FUNDING_WORDS_RX.search(title + " " + class_txt):
        return None  # not a funding opportunity

    content_html = (p.get("content") or {}).get("rendered", "") or ""
    excerpt_html = (p.get("excerpt") or {}).get("rendered", "") or ""
    body    = _strip_html(content_html)
    excerpt = _strip_html(excerpt_html)

    # deadline — skip posts whose parsed deadline is already past
    deadline = _extract_deadline(title + "\n" + body[:6000])
    if deadline:
        dt = _parse_dt(deadline)
        if dt and dt <= datetime.now(timezone.utc):
            return None

    # "Study in: Belgium" style lines are the cleanest location signal
    study_in = ""
    sim = re.search(r"study in:?\s*\|?\s*([A-Za-z][A-Za-z ,&/()']{2,50})",
                    body[:6000], re.I)
    if sim:
        study_in = re.split(r"[.,;(\n]", sim.group(1))[0].strip()[:50]

    blob = " ".join([title, class_txt, study_in])
    region  = _region_of(blob) or ""
    country = _country_of(study_in) or _country_of(blob) if region else ""

    funding = _funding_type(title, body[:2500])
    level   = _level(title, body[:2500])
    amount, amount_str = _extract_amount(title + " " + body)

    tags = []
    for c in (p.get("class_list") or []):
        for pref in ("category-", "tag-"):
            if c.startswith(pref):
                t = c[len(pref):].replace("-", " ").strip()
                if t and t not in tags and len(t) > 3:
                    tags.append(t)
    tags = tags[:6]

    slug = (p.get("slug") or re.sub(r"[^a-z0-9]+", "-", title.lower()))[:60]
    prefix = {"Scholars4Dev": "s4d", "ScholarshipsCorner": "sc",
              "OpportunitiesForYouth": "ofy"}.get(source_name, "wp")

    return {
        "id":         f"{prefix}-{slug}",
        "title":      title,
        "provider":   "",
        "location":   study_in,
        "region":     region,
        "country":    country if region in ("EU", "AR") else "",
        "remote":     "worldwide" in blob.lower(),
        "funding":    funding,
        "amount":     amount,
        "amount_str": amount_str,
        "deadline":   deadline,
        "level":      level,
        "description": (excerpt or body)[:600],
        "tags":       tags,
        "url":        link,
        "source":     source_name,
        "posted_ago": "",
    }


def fetch_wp_source(name, base, pages=2, per_page=100):
    """All recent scholarship posts from one WordPress aggregator."""
    out = []
    for page in range(1, max(1, pages) + 1):
        posts = _wp_fetch_posts(base, page=page, per_page=per_page)
        if not posts:
            break
        for p in posts:
            item = _wp_post_to_scholarship(name, p)
            if item:
                out.append(item)
        time.sleep(0.6)  # be polite
    return out


def seed_scholarships():
    """Representative seed scholarships — replaced by real API data
    as soon as keys are configured."""
    now = datetime.now(timezone.utc)

    def _d(days):
        # Real calendar arithmetic: now + N days. The old implementation used
        # now.replace(day=min(now.day+days, 28)), which could never cross a
        # month boundary and clamped every deadline to day 28 of the current
        # month — so snapshots generated on the 29th/30th/31st produced
        # *past* deadlines and every scholarship vanished from the site.
        return (now + timedelta(days=days)).isoformat()

    rows = [
        # ── GERMANY ──────────────────────────────────────────────
        {"title":"DAAD Scholarship for International Graduates",
         "provider":"DAAD (German Academic Exchange Service)",
         "location":"Germany","region":"EU","country":"Germany",
         "remote":False,"funding":"Fully Funded","amount":15000,
         "amount_str":"€15,000 / yr","deadline":_d(30),
         "level":"Masters",
         "description":"Funding for international graduates pursuing a masters or PhD at a German university.",
         "tags":["Engineering & IT","Data & AI","Research","PhD"],
         "url":"https://www.daad.de/en/study-and-research-in-germany/scholarships/",
         "source":"DAAD"},

        {"title":"Eiffel Excellence Scholarship Programme",
         "provider":"French Ministry for Europe and Foreign Affairs",
         "location":"France","region":"EU","country":"France",
         "remote":False,"funding":"Fully Funded","amount":18000,
         "amount_str":"€18,000 / yr","deadline":_d(45),
         "level":"Masters",
         "description":"French government scholarship for international master's and PhD students.",
         "tags":["Engineering & IT","Business","Arts","PhD"],
         "url":"https://www.campusfrance.org/en/eiffel-excellence-scholarship-programme",
         "source":"Campus France"},

        {"title":"Orange Knowledge Programme (OKP)",
         "provider":"Nuffic (Netherlands)",
         "location":"Netherlands","region":"EU","country":"Netherlands",
         "remote":False,"funding":"Fully Funded","amount":20000,
         "amount_str":"€20,000","deadline":_d(60),
         "level":"Masters",
         "description":"OKP scholarships for professionals from developing countries for short masters in the Netherlands.",
         "tags":["Engineering & IT","Healthcare","Education","Short program"],
         "url":"https://www.okp.nl/","source":"Nuffic"},

        {"title":"Spain Grant for International Masters Students",
         "provider":"Spanish Ministry of Education",
         "location":"Spain","region":"EU","country":"Spain",
         "remote":False,"funding":"Partially Funded","amount":6000,
         "amount_str":"€6,000 / yr","deadline":_d(21),
         "level":"Masters",
         "description":"Partial scholarship for international students enrolled in a masters program in Spain.",
         "tags":["Engineering & IT","Arts","Business"],
         "url":"https://www.educacion.gob.es/teso/convocatorias.html",
         "source":"Spanish Ministry"},

        {"title":"Polish Government Scholarship for Foreign Students",
         "provider":"Polish National Agency for Academic Exchange (NAWA)",
         "location":"Poland","region":"EU","country":"Poland",
         "remote":False,"funding":"Fully Funded","amount":12000,
         "amount_str":"€12,000 / yr","deadline":_d(14),
         "level":"Masters",
         "description":"NAWA scholarships for foreign students and researchers in Poland.",
         "tags":["Engineering & IT","Data & AI","PhD","Research"],
         "url":"https://nawo.gov.pl/en/","source":"NAWA"},

        {"title":"Study in Italy — MAECI Scholarships",
         "provider":"Italian Ministry of Foreign Affairs",
         "location":"Italy","region":"EU","country":"Italy",
         "remote":False,"funding":"Fully Funded","amount":14000,
         "amount_str":"€14,000 / yr","deadline":_d(35),
         "level":"Masters",
         "description":"MAECI scholarships for foreign citizens to study at masters and PhD level in Italy.",
         "tags":["Engineering & IT","Arts","Design & Creative"],
         "url":"https://www.esteri.it/en/scholarships/","source":"MAECI"},

        {"title":"Croatia State Scholarships for Foreigners",
         "provider":"Croatian Ministry of Science and Education",
         "location":"Croatia","region":"EU","country":"Croatia",
         "remote":False,"funding":"Fully Funded","amount":8000,
         "amount_str":"€8,000 / yr","deadline":_d(20),
         "level":"Bachelor",
         "description":"State scholarships for foreign citizens studying in Croatia.",
         "tags":["Engineering & IT","Healthcare","Education"],
         "url":"https://mzo.hr/en/scholarships","source":"Croatian Ministry"},

        {"title":"Sweden Institute Scholarships for Global Professionals",
         "provider":"Sweden Institute",
         "location":"Sweden","region":"EU","country":"Sweden",
         "remote":False,"funding":"Fully Funded","amount":22000,
         "amount_str":"SEK 220,000","deadline":_d(50),
         "level":"Masters",
         "description":"Full scholarship for global professionals to pursue a masters in Sweden.",
         "tags":["Engineering & IT","Data & AI","Business","Leadership"],
         "url":"https://si.se/en/scholarships/","source":"Sweden Institute"},

        {"title":"Denmark Government Scholarships for International Students",
         "provider":"Danish Ministry of Higher Education",
         "location":"Denmark","region":"EU","country":"Denmark",
         "remote":False,"funding":"Partially Funded","amount":10000,
         "amount_str":"DKK 100,000","deadline":_d(25),
         "level":"Masters",
         "description":"Danish government scholarships for international master's students.",
         "tags":["Engineering & IT","Data & AI","Healthcare"],
         "url":"https://ufm.dk/en/scholarships","source":"Danish Ministry"},

        {"title":"Finland Government Scholarships for International Students",
         "provider":"Finnish Ministry of Education",
         "location":"Finland","region":"EU","country":"Finland",
         "remote":False,"funding":"Partially Funded","amount":8000,
         "amount_str":"€8,000 / yr","deadline":_d(18),
         "level":"Masters",
         "description":"Finnish government scholarships for international masters students.",
         "tags":["Engineering & IT","Technology","Education"],
         "url":"https://minedu.fi/en/scholarships","source":"Finnish Ministry"},

        # ── UK ───────────────────────────────────────────────────
        {"title":"Chevening Scholarships",
         "provider":"UK Government (FCDO)",
         "location":"United Kingdom","region":"EU","country":"United Kingdom",
         "remote":False,"funding":"Fully Funded","amount":35000,
         "amount_str":"£35,000","deadline":_d(10),
         "level":"Masters",
         "description":"Global scholarship programme for future leaders to study in the UK.",
         "tags":["Leadership","Engineering & IT","Business","Policy","All majors"],
         "url":"https://www.chevening.org/scholarship/","source":"Chevening"},

        {"title":"Commonwealth Scholarships for UK Masters",
         "provider":"Commonwealth Scholarship Commission",
         "location":"United Kingdom","region":"EU","country":"United Kingdom",
         "remote":False,"funding":"Fully Funded","amount":28000,
         "amount_str":"£28,000","deadline":_d(40),
         "level":"Masters",
         "description":"Full scholarship for citizens of Commonwealth countries to study in the UK.",
         "tags":["Engineering & IT","Data & AI","PhD","Healthcare","All majors"],
         "url":"https://comdetails.org/","source":"Commonwealth"},

        {"title":"Rhodes Scholarships",
         "provider":"Rhodes Trust",
         "location":"United Kingdom","region":"EU","country":"United Kingdom",
         "remote":False,"funding":"Fully Funded","amount":38000,
         "amount_str":"£38,000","deadline":_d(55),
         "level":"Masters",
         "description":"Prestigious scholarship for outstanding students from selected countries to study at Oxford.",
         "tags":["Leadership","Engineering & IT","Humanities","Business"],
         "url":"https://www.rhodesscholarships.org/","source":"Rhodes Trust"},

        # ── USA ──────────────────────────────────────────────────
        {"title":"Fulbright Foreign Student Program",
         "provider":"US Department of State",
         "location":"USA","region":"US","country":"USA",
         "remote":False,"funding":"Fully Funded","amount":40000,
         "amount_str":"$40,000 / yr","deadline":_d(28),
         "level":"Masters",
         "description":"US government scholarship for international students to pursue masters or PhD in the USA.",
         "tags":["Engineering & IT","Data & AI","Humanities","Business","All majors"],
         "url":"https://fulbright.org/","source":"Fulbright"},

        {"title":"Hertz Foundation Graduate Fellowship",
         "provider":"Hertz Foundation",
         "location":"USA","region":"US","country":"USA",
         "remote":False,"funding":"Fully Funded","amount":35000,
         "amount_str":"$35,000 / yr","deadline":_d(34),
         "level":"PhD",
         "description":"Fellowship for applied physical and biological sciences PhD students in the USA.",
         "tags":["Engineering & IT","Data & AI","PhD","Research"],
         "url":"https://hertzfoundation.org/","source":"Hertz Foundation"},

        {"title":"NSF Graduate Research Fellowship",
         "provider":"National Science Foundation",
         "location":"USA","region":"US","country":"USA",
         "remote":False,"funding":"Fully Funded","amount":34000,
         "amount_str":"$34,000 / yr","deadline":_d(60),
         "level":"PhD",
         "description":"Prestigious US government fellowship for graduate students in STEM.",
         "tags":["Engineering & IT","Data & AI","PhD","Research","All STEM"],
         "url":"https://www.nsfgrfp.org/","source":"NSF"},

        {"title":"Gates Millennium Scholars Program",
         "provider":"Bill & Melinda Gates Foundation",
         "location":"USA","region":"US","country":"USA",
         "remote":False,"funding":"Fully Funded","amount":50000,
         "amount_str":"$50,000 / yr","deadline":_d(12),
         "level":"Bachelor",
         "description":"Last-dollar scholarship for minority high-achieving students in the USA.",
         "tags":["All majors","Leadership","Community","Underrepresented"],
         "url":"https://www.gmsp.org/","source":"Gates Foundation"},

        {"title":"AAUW International Fellowship",
         "provider":"AAUW (American Association of University Women)",
         "location":"USA","region":"US","country":"USA",
         "remote":False,"funding":"Partially Funded","amount":20000,
         "amount_str":"$20,000","deadline":_d(22),
         "level":"Masters",
         "description":"Fellowship for women who are not US citizens to pursue graduate study in the USA.",
         "tags":["Engineering & IT","Data & AI","Business","PhD","Women"],
         "url":"https://www.aauw.org/fellowships-grants/","source":"AAUW"},

        # ── WORLDWIDE / REMOTE ──────────────────────────────────
        {"title":"Google PhD Fellowship Program",
         "provider":"Google Research",
         "location":"Worldwide / Remote","region":"WW","country":"",
         "remote":True,"funding":"Fully Funded","amount":50000,
         "amount_str":"$50,000","deadline":_d(30),
         "level":"PhD",
         "description":"Global fellowship for PhD students in computer science and related fields.",
         "tags":["Engineering & IT","Data & AI","PhD","Research"],
         "url":"https://research.google/outreach/phd-fellowship/","source":"Google"},

        {"title":"Microsoft Research PhD Fellowship",
         "provider":"Microsoft Research",
         "location":"Worldwide / Remote","region":"WW","country":"",
         "remote":True,"funding":"Fully Funded","amount":45000,
         "amount_str":"$45,000","deadline":_d(26),
         "level":"PhD",
         "description":"Fellowship for PhD students in computing and related areas worldwide.",
         "tags":["Engineering & IT","Data & AI","PhD","Research"],
         "url":"https://www.microsoft.com/en-us/research/academic-program/phd-fellowship/",
         "source":"Microsoft Research"},

        {"title":"Outreachy Internship — Paid Remote",
         "provider":"Outreachy",
         "location":"Worldwide / Remote","region":"WW","country":"",
         "remote":True,"funding":"Fully Funded","amount":6500,
         "amount_str":"$6,500 stipend","deadline":_d(7),
         "level":"Internship",
         "description":"Paid remote internships in open source for underrepresented groups in tech.",
         "tags":["Engineering & IT","Data & AI","Design & Creative","Open source"],
         "url":"https://www.outreachy.org/","source":"Outreachy"},

        {"title":"Courtois Fellowship Scholarship — Canada",
         "provider":"Courtois Foundation",
         "location":"Canada","region":"WW","country":"Canada",
         "remote":False,"funding":"Fully Funded","amount":25000,
         "amount_str":"CAD 25,000","deadline":_d(52),
         "level":"Masters",
         "description":"Fully funded masters scholarship for international students in Canada.",
         "tags":["Engineering & IT","Data & AI","Business"],
         "url":"https://www.courtois.org/","source":"Courtois Foundation"},

        {"title":"Commonwealth PhD Scholarships — UK",
         "provider":"Commonwealth Scholarship Commission",
         "location":"United Kingdom","region":"EU","country":"United Kingdom",
         "remote":False,"funding":"Fully Funded","amount":30000,
         "amount_str":"£30,000","deadline":_d(48),
         "level":"PhD",
         "description":"Full PhD funding for Commonwealth citizens.",
         "tags":["Engineering & IT","Data & AI","PhD","Research"],
         "url":"https://comdetails.org/","source":"Commonwealth"},

        {"title":"NTHU Scholarship — Taiwan",
         "provider":"National Tsing Hua University",
         "location":"Taiwan","region":"WW","country":"Taiwan",
         "remote":False,"funding":"Fully Funded","amount":18000,
         "amount_str":"NT$18,000 / month","deadline":_d(33),
         "level":"Masters",
         "description":"Full scholarship for international students at NTHU Taiwan.",
         "tags":["Engineering & IT","Data & AI","Design & Creative"],
         "url":"https://www.nthu.edu.tw/en/","source":"NTHU"},

        {"title":"Oregon State University Scholarships 2027",
         "provider":"Oregon State University",
         "location":"USA","region":"US","country":"USA",
         "remote":False,"funding":"Fully Funded","amount":22000,
         "amount_str":"$22,000 / yr","deadline":_d(19),
         "level":"Masters",
         "description":"Fully funded masters scholarships for international students at OSU.",
         "tags":["Engineering & IT","Data & AI","Business"],
         "url":"https://oregonstate.edu/","source":"Oregon State University"},

        {"title":"GWI Scholars Program — USA 2026",
         "provider":"Global Women's Institute",
         "location":"USA","region":"US","country":"USA",
         "remote":False,"funding":"Fully Funded","amount":15000,
         "amount_str":"$15,000","deadline":_d(8),
         "level":"Masters",
         "description":"Scholarship for women pursuing graduate studies in the USA.",
         "tags":["Engineering & IT","Healthcare","Business","Leadership","Women"],
         "url":"https://gwi-scholars.org/","source":"GWI"},

        # ── AFRICA ──────────────────────────────────────────────────
        {"title":"African Development Bank (AfDB) Scholarship Programme",
         "provider":"African Development Bank",
         "location":"Africa (regional)","region":"WW","country":"",
         "remote":False,"funding":"Fully Funded","amount":20000,
         "amount_str":"$20,000 / yr","deadline":_d(45),
         "level":"Masters",
         "description":"AfDB scholarship for African students pursuing masters at African universities.",
         "tags":["Engineering & IT","Business","Regional","Africa"],
         "url":"https://www.afdb.org/en/scholarships","source":"AfDB"},

        {"title":"Mastercard Foundation Scholars Programme",
         "provider":"Mastercard Foundation",
         "location":"Africa (multiple countries)","region":"WW","country":"",
         "remote":False,"funding":"Fully Funded","amount":30000,
         "amount_str":"$30,000 / yr","deadline":_d(35),
         "level":"Masters",
         "description":"Fully-funded scholarship for young Africans with a track record of leadership.",
         "tags":["Engineering & IT","Business","Leadership","Africa","Young leaders"],
         "url":"https://mastercardfoundation.org/scholars","source":"Mastercard Foundation"},

        {"title":"Joint Japan/World Bank Graduate Scholarship Program",
         "provider":"World Bank Group",
         "location":"Worldwide (developing countries)","region":"WW","country":"",
         "remote":False,"funding":"Fully Funded","amount":40000,
         "amount_str":"$40,000 / yr","deadline":_d(50),
         "level":"Masters",
         "description":"Scholarship for students from World Bank eligible countries to study development-related masters.",
         "tags":["Engineering & IT","Development","Economics","All majors","Developing countries"],
         "url":"https://www.worldbank.org/en/scholarships","source":"World Bank"},

        {"title":"Commonwealth Distance Learning Scholarships",
         "provider":"Commonwealth Scholarship Commission",
         "location":"United Kingdom (distance)","region":"EU","country":"United Kingdom",
         "remote":True,"funding":"Fully Funded","amount":15000,
         "amount_str":"£15,000","deadline":_d(55),
         "level":"Masters",
         "description":"Distance-learning PhD and masters scholarships for Commonwealth citizens.",
         "tags":["Engineering & IT","PhD","Masters","Distance learning","Commonwealth"],
         "url":"https://cscuk.fcdo.org.uk/scholarships/distance-learning","source":"Commonwealth UK"},

        {"title":"University of Edinburgh Global Development Scholarships",
         "provider":"University of Edinburgh",
         "location":"United Kingdom","region":"EU","country":"United Kingdom",
         "remote":False,"funding":"Partially Funded","amount":10000,
         "amount_str":"£10,000","deadline":_d(28),
         "level":"Masters",
         "description":"Partial scholarship for students from low- and middle-income countries.",
         "tags":["Engineering & IT","Masters","International","UK"],
         "url":"https://www.ed.ac.uk/scholarships","source":"University of Edinburgh"},

        {"title":"University of Sussex Chancellor's International Development Scholarships",
         "provider":"University of Sussex",
         "location":"United Kingdom","region":"EU","country":"United Kingdom",
         "remote":False,"funding":"Partially Funded","amount":8000,
         "amount_str":"£8,000","deadline":_d(30),
         "level":"Masters",
         "description":"Scholarships for international students studying development-related masters at Sussex.",
         "tags":["Engineering & IT","Development","Masters","UK"],
         "url":"https://www.sussex.ac.uk/scholarships","source":"University of Sussex"},

        # ── MIDDLE EAST ─────────────────────────────────────────────
        {"title":"Qatar Foundation International Scholarship Programme",
         "provider":"Qatar Foundation",
         "location":"Qatar / USA / UK","region":"WW","country":"",
         "remote":False,"funding":"Fully Funded","amount":45000,
         "amount_str":"$45,000 / yr","deadline":_d(40),
         "level":"Masters",
         "description":"Fully-funded scholarship for students from developing countries to study at top universities.",
         "tags":["Engineering & IT","Business","Energy","All majors"],
         "url":"https://www.qf.org.qa/scholarships","source":"Qatar Foundation"},

        {"title":"Islamic Development Bank (IsDB) Scholarship Programme",
         "provider":"Islamic Development Bank",
         "location":"Worldwide (IsDB member countries)","region":"WW","country":"",
         "remote":False,"funding":"Fully Funded","amount":25000,
         "amount_str":"$25,000 / yr","deadline":_d(50),
         "level":"Masters",
         "description":"Scholarship for students from IsDB member countries to pursue masters at IsDB partner universities.",
         "tags":["Engineering & IT","Business","Regional","Islamic countries"],
         "url":"https://www.isdb.org/scholarships","source":"IsDB"},

        {"title":"Saudi Government Scholarship Programme (KSA)",
         "provider":"Saudi Arabian Cultural Bureau",
         "location":"Saudi Arabia / USA / UK","region":"WW","country":"",
         "remote":False,"funding":"Fully Funded","amount":50000,
         "amount_str":"$50,000 / yr","deadline":_d(33),
         "level":"Masters",
         "description":"Fully-funded scholarship for international students to study in Saudi Arabia or partner countries.",
         "tags":["Engineering & IT","Business","Energy","All majors"],
         "url":"https://www.sacb.gov.sa/","source":"Saudi Cultural Bureau"},

        {"title":"Kuwait Government Scholarship for Foreign Students",
         "provider":"Kuwait Ministry of Higher Education",
         "location":"Kuwait","region":"WW","country":"Kuwait",
         "remote":False,"funding":"Fully Funded","amount":20000,
         "amount_str":"$20,000 / yr","deadline":_d(25),
         "level":"Masters",
         "description":"Government scholarship for international students to study at Kuwaiti universities.",
         "tags":["Engineering & IT","Business","Regional","Kuwait"],
         "url":"https://www.mohe.gov.kw/","source":"Kuwait Ministry"},

        # ── ASIA ────────────────────────────────────────────────────
        {"title":"Japanese Government (MEXT) Scholarship",
         "provider":"Japanese Ministry of Education (MEXT)",
         "location":"Japan","region":"WW","country":"Japan",
         "remote":False,"funding":"Fully Funded","amount":35000,
         "amount_str":"¥35,000 / month + expenses","deadline":_d(42),
         "level":"Masters",
         "description":"Fully-funded Japanese government scholarship for international students at Japanese universities.",
         "tags":["Engineering & IT","Technology","All majors","Japanese language"],
         "url":"https://www.studyinjapan.go.jp/en/scholarships","source":"MEXT Japan"},

        {"title":"China Government Scholarship (CSC)",
         "provider":"Chinese Scholarship Council",
         "location":"China","region":"WW","country":"China",
         "remote":False,"funding":"Fully Funded","amount":25000,
         "amount_str":"¥25,000 / yr + accommodation","deadline":_d(38),
         "level":"Masters",
         "description":"Fully-funded scholarship for international students to study at Chinese universities.",
         "tags":["Engineering & IT","Technology","Business","All majors","Chinese language"],
         "url":"https://www.csc.edu.cn/","source":"CSC China"},

        {"title":"Korean Government Scholarship Program (GKS)",
         "provider":"Korean Ministry of Education",
         "location":"South Korea","region":"WW","country":"South Korea",
         "remote":False,"funding":"Fully Funded","amount":30000,
         "amount_str":"₩30,000 / yr + stipend","deadline":_d(44),
         "level":"Masters",
         "description":"Fully-funded Korean government scholarship for international students.",
         "tags":["Engineering & IT","Technology","Korean language","All majors"],
         "url":"https://studyinkorea.go.kr/","source":"NIIED Korea"},

        {"title":"Singapore Government Scholarship (SGS)",
         "provider":"Singapore Ministry of Education",
         "location":"Singapore","region":"WW","country":"Singapore",
         "remote":False,"funding":"Fully Funded","amount":40000,
         "amount_str":"SGD 40,000 / yr","deadline":_d(29),
         "level":"Masters",
         "description":"Fully-funded scholarship for international students to pursue masters at Singapore universities.",
         "tags":["Engineering & IT","Data & AI","Business","Technology"],
         "url":"https://www.moe.gov.sg/scholarships","source":"Singapore MOE"},

        {"title":"India Council of Cultural Relations (ICCR) Scholarships",
         "provider":"Indian Council for Cultural Relations",
         "location":"India","region":"WW","country":"India",
         "remote":False,"funding":"Fully Funded","amount":15000,
         "amount_str":"₹15,000 / month + tuition","deadline":_d(48),
         "level":"Masters",
         "description":"Scholarships for international students from select countries to study in India.",
         "tags":["Engineering & IT","Arts","Humanities","Regional","India"],
         "url":"https://www.iccr.gov.in/","source":"ICCR India"},

        {"title":"University of Tokyo Scholarship for International Students",
         "provider":"University of Tokyo",
         "location":"Japan","region":"WW","country":"Japan",
         "remote":False,"funding":"Fully Funded","amount":25000,
         "amount_str":"¥25,000 / month + tuition waiver","deadline":_d(36),
         "level":"Masters",
         "description":"Tuition waiver and monthly stipend for international students at University of Tokyo.",
         "tags":["Engineering & IT","Data & AI","Japanese language","Research"],
         "url":"https://www.u-tokyo.ac.jp/en/education/scholarships","source":"University of Tokyo"},

        {"title":"KAIST Scholarship for International Students",
         "provider":"KAIST (Korea Advanced Institute of Science and Technology)",
         "location":"South Korea","region":"WW","country":"South Korea",
         "remote":False,"funding":"Fully Funded","amount":30000,
         "amount_str":"₩30,000 / yr + stipend","deadline":_d(32),
         "level":"Masters",
         "description":"Full scholarship for international students pursuing masters or PhD at KAIST.",
         "tags":["Engineering & IT","Data & AI","PhD","Technology","Korean language"],
         "url":"https://www.kaist.ac.kr/en/scholarship","source":"KAIST"},

        # ── SOUTH AMERICA ────────────────────────────────────────────
        {"title":"Santander Universities Scholarships",
         "provider":"Banco Santander",
         "location":"Multiple countries (Spain, UK, USA, etc.)","region":"EU","country":"",
         "remote":False,"funding":"Partially Funded","amount":10000,
         "amount_str":"€10,000","deadline":_d(40),
         "level":"Masters",
         "description":"Partial scholarships for international students at Santander-partner universities worldwide.",
         "tags":["Engineering & IT","Business","International","Multiple countries"],
         "url":"https://www.santander.com/scholarships","source":"Santander"},

        {"title":"Brazil Government Scholarship (Ciência sem Fronteiras successor)",
         "provider":"Brazilian Ministry of Education (CAPES)",
         "location":"Brazil","region":"WW","country":"Brazil",
         "remote":False,"funding":"Fully Funded","amount":18000,
         "amount_str":"R$18,000 / yr","deadline":_d(45),
         "level":"Masters",
         "description":"Brazilian government scholarships for international students to study in Brazil.",
         "tags":["Engineering & IT","Environmental","Portuguese language","Regional"],
         "url":"https://www.capes.gov.br/","source":"CAPES Brazil"},

        {"title":"Fulbright Colombia Programme",
         "provider":"US Department of State / Fulbright Colombia",
         "location":"USA","region":"US","country":"USA",
         "remote":False,"funding":"Fully Funded","amount":35000,
         "amount_str":"$35,000 / yr","deadline":_d(35),
         "level":"Masters",
         "description":"Fulbright scholarship for Colombian citizens to pursue masters study in the USA.",
         "tags":["Engineering & IT","All majors","Colombia","Leadership"],
         "url":"https://www.fulbright.org.co/","source":"Fulbright Colombia"},

        {"title":"SIMED Scholarships for Latin American Students",
         "provider":"SIMED (Sociedad Iberoamericana de Educación y Docencia)",
         "location":"Spain","region":"EU","country":"Spain",
         "remote":False,"funding":"Partially Funded","amount":8000,
         "amount_str":"€8,000","deadline":_d(27),
         "level":"Masters",
         "description":"Partial scholarships for Latin American students to study masters in Spain.",
         "tags":["Engineering & IT","Business","Spanish language","Latin America"],
         "url":"https://www.simed.org/","source":"SIMED"},

        # ── ARAB WORLD ────────────────────────────────────────────────
        {"title":"Al-Azhar University Scholarships for International Students",
         "provider":"Al-Azhar University (Egypt)",
         "location":"Egypt","region":"AR","country":"Egypt",
         "remote":False,"funding":"Fully Funded","amount":5000,
         "amount_str":"$5,000 / yr (tuition + stipend)","deadline":_d(18),
         "level":"Masters",
         "description":"Scholarships for international Muslim students to study at Al-Azhar University in Cairo.",
         "tags":["Engineering & IT","Islamic studies","Arabic language","Africa","Religious"],
         "url":"https://www.alazhar.edu.eg/","source":"Al-Azhar University"},

        {"title":"Misr El Kheir Foundation Scholarships (Egypt)",
         "provider":"Misr El Kheir Foundation",
         "location":"Egypt","region":"AR","country":"Egypt",
         "remote":False,"funding":"Fully Funded","amount":8000,
         "amount_str":"$8,000 / yr","deadline":_d(22),
         "level":"Masters",
         "description":"Scholarships for Egyptian and Arab students pursuing higher education in Egypt.",
         "tags":["Engineering & IT","Education","Africa","Egypt","Community"],
         "url":"https://www.misr-el-kheir.org/","source":"Misr El Kheir"},

        {"title":"Arab Fund Scholarship Programme",
         "provider":"Arab Fund for Economic and Social Development",
         "location":"Arab world / USA / Europe","region":"AR","country":"",
         "remote":False,"funding":"Fully Funded","amount":30000,
         "amount_str":"$30,000 / yr","deadline":_d(45),
         "level":"Masters",
         "description":"Fully-funded scholarships for Arab citizens to pursue masters at top international universities.",
         "tags":["Engineering & IT","Business","Economics","Arab world","Development"],
         "url":"https://www.arabfund.org/scholarships","source":"Arab Fund"},

        {"title":"Islamic Development Bank (IsDB) Scholarship Programme",
         "provider":"Islamic Development Bank",
         "location":"Worldwide (IsDB member countries)","region":"AR","country":"",
         "remote":False,"funding":"Fully Funded","amount":25000,
         "amount_str":"$25,000 / yr","deadline":_d(50),
         "level":"Masters",
         "description":"Scholarship for students from IsDB member countries (including all Arab states) to pursue masters.",
         "tags":["Engineering & IT","Business","Regional","Islamic countries","Arab world"],
         "url":"https://www.isdb.org/scholarships","source":"IsDB"},

        {"title":"Qatar Foundation — Arab World Scholarship Track",
         "provider":"Qatar Foundation",
         "location":"Qatar / USA","region":"AR","country":"Qatar",
         "remote":False,"funding":"Fully Funded","amount":50000,
         "amount_str":"$50,000 / yr","deadline":_d(40),
         "level":"Masters",
         "description":"Fully-funded scholarship for Arab students to pursue masters at Qatar Foundation partner universities.",
         "tags":["Engineering & IT","Business","Energy","Arab world","Qatar"],
         "url":"https://www.qf.org.qa/scholarships","source":"Qatar Foundation"},

        {"title":"Saudi Cultural Bureau Scholarships for Arab Students",
         "provider":"Saudi Arabian Cultural Bureau",
         "location":"Saudi Arabia / USA","region":"AR","country":"Saudi Arabia",
         "remote":False,"funding":"Fully Funded","amount":50000,
         "amount_str":"$50,000 / yr","deadline":_d(33),
         "level":"Masters",
         "description":"Scholarships for Arab students to study at Saudi universities or partner institutions abroad.",
         "tags":["Engineering & IT","Business","Energy","Saudi Arabia","Arab world"],
         "url":"https://www.sacb.gov.sa/","source":"Saudi Cultural Bureau"},

        {"title":"Kuwait Foundation for the Advancement of Sciences (KFAS) Scholarships",
         "provider":"KFAS (Kuwait)",
         "location":"Kuwait / USA / Europe","region":"AR","country":"Kuwait",
         "remote":False,"funding":"Fully Funded","amount":20000,
         "amount_str":"$20,000 / yr","deadline":_d(25),
         "level":"Masters",
         "description":"Scholarships for Arab students in science and technology fields.",
         "tags":["Engineering & IT","Data & AI","Science","Kuwait","Arab world"],
         "url":"https://www.kfas.org.sa/","source":"KFAS Kuwait"},

        {"title":"UAE Government Scholarships for Arab Students",
         "provider":"UAE Ministry of Education",
         "location":"UAE","region":"AR","country":"United Arab Emirates",
         "remote":False,"funding":"Fully Funded","amount":25000,
         "amount_str":"$25,000 / yr","deadline":_d(28),
         "level":"Masters",
         "description":"Government scholarships for Arab students to study at UAE universities.",
         "tags":["Engineering & IT","Business","UAE","Arab world","Education"],
         "url":"https://www.moe.gov.ae/","source":"UAE Ministry"},

        {"title":"Queen Rania Foundation Scholarships",
         "provider":"Queen Rania Foundation",
         "location":"Jordan","region":"AR","country":"Jordan",
         "remote":False,"funding":"Fully Funded","amount":10000,
         "amount_str":"$10,000 / yr","deadline":_d(15),
         "level":"Masters",
         "description":"Scholarships for Jordanian and Arab students pursuing masters in Jordan.",
         "tags":["Engineering & IT","Education","Jordan","Arab world","Women"],
         "url":"https://qrfoundation.org/","source":"Queen Rania Foundation"},

        {"title":"Moroccan Ministry of Higher Education Scholarships",
         "provider":"Moroccan Ministry of Higher Education",
         "location":"Morocco","region":"AR","country":"Morocco",
         "remote":False,"funding":"Fully Funded","amount":6000,
         "amount_str":"$6,000 / yr","deadline":_d(20),
         "level":"Masters",
         "description":"Scholarships for Moroccan and Arab students to study in Moroccan universities.",
         "tags":["Engineering & IT","Education","Morocco","Arab world","Africa"],
         "url":"https://www.mesrs.gov.ma/","source":"Moroccan MESRS"},

        {"title":"Tunisian Government Scholarships for Foreign Students",
         "provider":"Tunisian Ministry of Higher Education",
         "location":"Tunisia","region":"AR","country":"Tunisia",
         "remote":False,"funding":"Fully Funded","amount":5000,
         "amount_str":"$5,000 / yr (tuition waiver)","deadline":_d(24),
         "level":"Masters",
         "description":"Scholarships for Arab and African students to study at Tunisian universities.",
         "tags":["Engineering & IT","Education","Tunisia","Arab world","Africa"],
         "url":"https://www.mesr.rn.tn/","source":"Tunisian MESR"},

        {"title":"Algerian Government Scholarships for International Students",
         "provider":"Algerian Ministry of Higher Education",
         "location":"Algeria","region":"AR","country":"Algeria",
         "remote":False,"funding":"Fully Funded","amount":6000,
         "amount_str":"$6,000 / yr (tuition + stipend)","deadline":_d(26),
         "level":"Masters",
         "description":"Scholarships for Arab and African students to study at Algerian universities.",
         "tags":["Engineering & IT","Education","Algeria","Arab world","Africa"],
         "url":"https://www.mesrs.dz/","source":"Algerian MESRS"},

        {"title":"Lebanese University Scholarships for Arab Students",
         "provider":"Lebanese University",
         "location":"Lebanon","region":"AR","country":"Lebanon",
         "remote":False,"funding":"Partially Funded","amount":4000,
         "amount_str":"$4,000 / yr","deadline":_d(17),
         "level":"Masters",
         "description":"Partial scholarships for Arab students to study at Lebanese University.",
         "tags":["Engineering & IT","Education","Lebanon","Arab world"],
         "url":"https://www.ul.edu.lb/","source":"Lebanese University"},

        {"title":"Palestinian Ministry of Education Scholarships",
         "provider":"Palestinian Ministry of Education",
         "location":"Palestine / Arab partner countries","region":"AR","country":"Palestine",
         "remote":False,"funding":"Fully Funded","amount":7000,
         "amount_str":"$7,000 / yr","deadline":_d(14),
         "level":"Masters",
         "description":"Scholarships for Palestinian and Arab students to pursue higher education.",
         "tags":["Engineering & IT","Education","Palestine","Arab world","Development"],
         "url":"https://www.moe.gov.ps/","source":"Palestinian MOE"},

        {"title":"Iraqi Ministry of Higher Education Scholarships",
         "provider":"Iraqi Ministry of Higher Education",
         "location":"Iraq","region":"AR","country":"Iraq",
         "remote":False,"funding":"Fully Funded","amount":5000,
         "amount_str":"$5,000 / yr (tuition waiver)","deadline":_d(19),
         "level":"Masters",
         "description":"Scholarships for Arab and regional students to study at Iraqi universities.",
         "tags":["Engineering & IT","Education","Iraq","Arab world","Regional"],
         "url":"https://www.moesr.gov.iq/","source":"Iraqi MOE"},

        {"title":"Moroccan Organization for the Development of Scientific Research (ORDIS) Scholarships",
         "provider":"ORDIS (Morocco)",
         "location":"Morocco / International","region":"AR","country":"Morocco",
         "remote":False,"funding":"Partially Funded","amount":4000,
         "amount_str":"$4,000 / yr","deadline":_d(22),
         "level":"Masters",
         "description":"Partial scholarships for Arab students in scientific and technological fields.",
         "tags":["Engineering & IT","Data & AI","Science","Morocco","Arab world"],
         "url":"https://www.ordis.ma/","source":"ORDIS Morocco"},

        # ── WOMEN-FOCUSED SCHOLARSHIPS ──────────────────────────────
        {"title":"Women in Tech Global Scholarship",
         "provider":"Women in Tech Global Organization",
         "location":"Worldwide","region":"WW","country":"",
         "remote":False,"funding":"Fully Funded","amount":5000,
         "amount_str":"$5,000","deadline":_d(15),
         "level":"Masters",
         "description":"Global scholarship for women pursuing studies or careers in technology fields.",
         "tags":["Engineering & IT","Data & AI","Women","Technology","Global"],
         "url":"https://www.womenintech.org/scholarships","source":"Women in Tech"},

        {"title":"P.E.O. International Peace Scholarship",
         "provider":"P.E.O. International",
         "location":"USA / Canada","region":"US","country":"USA",
         "remote":False,"funding":"Fully Funded","amount":15000,
         "amount_str":"$15,000 / yr","deadline":_d(18),
         "level":"Masters",
         "description":"Scholarship for international women to pursue graduate study in the USA or Canada.",
         "tags":["Engineering & IT","All majors","Women","International","Peace"],
         "url":"https://www.peointernational.org/peace-scholarship","source":"P.E.O."},

        {"title":"Schlumberger Foundation Faculty for the Future",
         "provider":"Schlumberger Foundation",
         "location":"Worldwide","region":"WW","country":"",
         "remote":False,"funding":"Fully Funded","amount":40000,
         "amount_str":"$40,000 / yr","deadline":_d(40),
         "level":"PhD",
         "description":"Fellowship for women in developing countries pursuing PhD in STEM fields.",
         "tags":["Engineering & IT","Data & AI","PhD","Women","STEM","Developing countries"],
         "url":"https://www.facultyforthefuture.org/","source":"Schlumberger Foundation"},

        {"title":"Google Women Techmakers Scholarships",
         "provider":"Google (Women Techmakers)",
         "location":"Worldwide","region":"WW","country":"",
         "remote":False,"funding":"Fully Funded","amount":10000,
         "amount_str":"$10,000 + retreat","deadline":_d(12),
         "level":"Masters",
         "description":"Scholarship + mentorship + retreat for women in technology studying at university.",
         "tags":["Engineering & IT","Data & AI","Women","Technology","Mentorship"],
         "url":"https://womenintech.google/community/scholarships/","source":"Google WTM"},

        {"title":"Forté Foundation MBA Scholarships for Women",
         "provider":"Forté Foundation",
         "location":"USA / Canada (partner schools)","region":"US","country":"USA",
         "remote":False,"funding":"Partially Funded","amount":20000,
         "amount_str":"$20,000","deadline":_d(25),
         "level":"Masters",
         "description":"MBA scholarships for women at Forté Foundation partner business schools.",
         "tags":["Business","Women","MBA","Leadership","USA"],
         "url":"https://www.fortéfoundation.org/scholarships","source":"Forté Foundation"},

        {"title":"Adobe Research Women-in-Technology Scholarship",
         "provider":"Adobe Research",
         "location":"Worldwide (remote component possible)","region":"WW","country":"",
         "remote":True,"funding":"Fully Funded","amount":10000,
         "amount_str":"$10,000 + internship","deadline":_d(28),
         "level":"Masters",
         "description":"Scholarship for women pursuing computer science or related fields at university.",
         "tags":["Engineering & IT","Data & AI","Women","Technology","Internship"],
         "url":"https://www.adobe.com/careers/university/scholarships.html","source":"Adobe Research"},

        {"title":"Palantir Women in Technology Scholarship",
         "provider":"Palantir Technologies",
         "location":"USA / remote","region":"US","country":"USA",
         "remote":True,"funding":"Fully Funded","amount":7000,
         "amount_str":"$7,000 + mentorship","deadline":_d(20),
         "level":"Masters",
         "description":"Scholarship for women studying computer science or related technical fields.",
         "tags":["Engineering & IT","Data & AI","Women","Technology","Mentorship"],
         "url":"https://www.palantir.com/college/scholarships/","source":"Palantir"},

        {"title":"Microsoft Gaming Scholarship for Women",
         "provider":"Microsoft",
         "location":"Worldwide","region":"WW","country":"",
         "remote":False,"funding":"Partially Funded","amount":5000,
         "amount_str":"$5,000","deadline":_d(10),
         "level":"Bachelor",
         "description":"Scholarship for women pursuing bachelor's degree in gaming or computer science.",
         "tags":["Engineering & IT","Women","Gaming","Technology","Bachelor"],
         "url":"https://www.microsoft.com/en-us/gaming/scholarship","source":"Microsoft Gaming"},

        {"title":"IEEE Women in Engineering Scholarship",
         "provider":"IEEE WIE",
         "location":"Worldwide","region":"WW","country":"",
         "remote":False,"funding":"Partially Funded","amount":3000,
         "amount_str":"$3,000","deadline":_d(22),
         "level":"Masters",
         "description":"Scholarship for women pursuing electrical, electronics, or computer engineering degrees.",
         "tags":["Engineering & IT","Data & AI","Women","Electrical engineering"],
         "url":"https://wie.ieee.org/scholarships","source":"IEEE WIE"},

        {"title":" AnitaB.org Grace Hopper Celebration Scholarship",
         "provider":"AnitaB.org",
         "location":"Worldwide (GHC conference)","region":"WW","country":"",
         "remote":True,"funding":"Fully Funded","amount":5000,
         "amount_str":"$5,000 + conference pass","deadline":_d(16),
         "level":"Masters",
         "description":"Scholarship to attend the Grace Hopper Celebration for women in computing.",
         "tags":["Engineering & IT","Women","Conference","Computing","Networking"],
         "url":"https://ghc.anitab.org/","source":"AnitaB.org"},

        # ── TECH / COMPUTER SCIENCE SPECIFIC ───────────────────────
        {"title":"Meta / Facebook Developer Circle Scholarship",
         "provider":"Meta (Facebook)",
         "location":"Worldwide","region":"WW","country":"",
         "remote":False,"funding":"Fully Funded","amount":5000,
         "amount_str":"$5,000 + training","deadline":_d(24),
         "level":"Masters",
         "description":"Scholarship for students in developer circles pursuing technology degrees.",
         "tags":["Engineering & IT","Data & AI","Technology","Meta","Training"],
         "url":"https://developers.facebook.com/community/developer-circles/scholarships/","source":"Meta"},

        {"title":"Amazon AWS Scholarship Programme",
         "provider":"Amazon Web Services",
         "location":"Worldwide","region":"WW","country":"",
         "remote":False,"funding":"Fully Funded","amount":5000,
         "amount_str":"$5,000 + AWS training","deadline":_d(26),
         "level":"Masters",
         "description":"Scholarship for students studying cloud computing, AI, or related technology fields.",
         "tags":["Engineering & IT","Cloud","Data & AI","AWS","Cloud computing"],
         "url":"https://aws.amazon.com/scholarships/","source":"AWS"},

        {"title":"GitHub Student Developer Pack Scholarships",
         "provider":"GitHub",
         "location":"Worldwide","region":"WW","country":"",
         "remote":True,"funding":"Fully Funded","amount":2000,
         "amount_str":"$2,000 + tool pack","deadline":_d(8),
         "level":"Bachelor",
         "description":"Scholarships + free developer tools for students building technology projects.",
         "tags":["Engineering & IT","Technology","Open source","Bachelor","Tools"],
         "url":"https://education.github.com/pack","source":"GitHub"},

        {"title":"Salesforce Dreamforce Scholarships",
         "provider":"Salesforce Foundation",
         "location":"USA (Dreamforce conference)","region":"US","country":"USA",
         "remote":False,"funding":"Fully Funded","amount":3000,
         "amount_str":"$3,000 + pass","deadline":_d(30),
         "level":"Masters",
         "description":"Scholarship for students attending Dreamforce tech conference.",
         "tags":["Engineering & IT","Technology","Conference","CRM","Salesforce"],
         "url":"https://www.salesforce.com/dreamforce/scholarships/","source":"Salesforce"},

        {"title":"TensorFlow Research Scholarships",
         "provider":"Google TensorFlow Team",
         "location":"Worldwide (remote research)","region":"WW","country":"",
         "remote":True,"funding":"Fully Funded","amount":8000,
         "amount_str":"$8,000 research grant","deadline":_d(33),
         "level":"PhD",
         "description":"Research grant for PhD students working on machine learning with TensorFlow.",
         "tags":["Engineering & IT","Data & AI","Machine learning","PhD","Research"],
         "url":"https://www.tensorflow.org/scholarships","source":"TensorFlow"},
    ]

    for r in rows:
        r["posted_ago"] = ""
    return rows


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
class AllExpiredError(Exception):
    """Raised when a snapshot would contain only past deadlines."""


def build_snapshot(scholarships, sources_ok=None):
    """Merge scraped scholarships with the seed baseline, dedupe, sort and
    validate. Pure function (no network, no file IO) so it is testable.
    Raises AllExpiredError if every deadline would be in the past."""
    sources_ok = dict(sources_ok or {})

    def _title_key(t):
        return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()

    def _sid(s):
        return (s.get("id") or re.sub(
            r"[^a-z0-9]+", "-", (s.get("title") or "").lower()
        ).strip("-")[:100])

    seen_ids, seen_titles, unique = set(), set(), []
    for s in scholarships:
        if not (s.get("title") and s.get("url")):
            continue
        sid, tk = _sid(s), _title_key(s["title"])
        if sid in seen_ids or (tk and tk in seen_titles):
            continue
        seen_ids.add(sid)
        seen_titles.add(tk)
        s["id"] = sid
        unique.append(s)

    # Seed rows are always merged as a baseline so the page never runs dry;
    # live-scraped entries win whenever titles collide.
    seed_added = 0
    for s in seed_scholarships():
        sid, tk = _sid(s), _title_key(s["title"])
        if sid in seen_ids or (tk and tk in seen_titles):
            continue
        seen_ids.add(sid)
        seen_titles.add(tk)
        s["id"] = sid
        unique.append(s)
        seed_added += 1
    if seed_added:
        sources_ok["seed"] = True

    def _deadline_key(s):
        dt = _parse_dt(s.get("deadline", ""))
        return dt.timestamp() if dt else 9e18
    unique.sort(key=_deadline_key)

    per_source = {}
    for s in unique:
        src_name = s.get("source", "") or "unknown"
        per_source[src_name] = per_source.get(src_name, 0) + 1

    deadlines = [s.get("deadline") for s in unique if s.get("deadline")]
    now_utc = datetime.now(timezone.utc)
    if deadlines and not any(_parse_dt(d) and _parse_dt(d) > now_utc
                             for d in deadlines):
        raise AllExpiredError(
            "all %d deadlines are in the past — the site would show no "
            "scholarships" % len(deadlines))

    return {
        "generated_at": _now_iso(),
        "count":        len(unique),
        "per_source":   per_source,
        "sources_ok":   sources_ok,
        "scholarships": unique,
    }


def main():
    import urllib.request as _urllib_request
    global urllib_request
    urllib_request = _urllib_request

    api_key   = os.environ.get("SCHOLARSHIPAPI_KEY", "").strip()
    parse_key = os.environ.get("SCHOLARSHIPS_COM_KEY", "").strip()

    sources_ok = {}

    def _collect(label, fn, *a, **kw):
        try:
            items = fn(*a, **kw)
        except Exception as e:
            print(f"[{label}] failed: {e}", file=sys.stderr)
            return []
        print(f"[{label}] {len(items)} items", file=sys.stderr)
        return items

    scholarships = []

    if api_key:
        items = _collect("scholarshipapi", fetch_scholarshipapi, api_key)
        sources_ok["ScholarshipAPI"] = bool(items)
        scholarships += items
    else:
        print("[scholarshipapi] no key — skipping", file=sys.stderr)

    if parse_key:
        items = _collect("scholarships.com", fetch_scholarships_com)
        sources_ok["Scholarships.com"] = bool(items)
        scholarships += items
    else:
        print("[scholarships.com] no key — skipping", file=sys.stderr)

    # ── WordPress aggregator sources (free, no keys) ────────────
    for src_cfg in WP_SOURCES:
        items = _collect(src_cfg["name"], fetch_wp_source,
                         src_cfg["name"], src_cfg["base"],
                         src_cfg.get("pages", 2))
        sources_ok[src_cfg["name"]] = bool(items)
        scholarships += items

    try:
        snapshot = build_snapshot(scholarships, sources_ok)
    except AllExpiredError as e:
        print(f"[scholarships] FATAL: {e} — keeping existing snapshot.",
              file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"[scholarships] written {snapshot['count']} scholarships → {OUT}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
