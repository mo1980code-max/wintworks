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
    if eu_strong and not us_strong:
        return "EU"
    if arab_strong and not us_strong:
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
    blob = f"{title or ''} {desc or ''}".lower()
    for lvl, keys in LEVELS:
        if any(k in blob for k in keys):
            return lvl
    return ""


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
def fetch_scholars4dev():
    """Scrape Scholars4Dev category listing pages for scholarship entries.
    Best-effort: each page may or may not render; failures are silent.
    We cap at a few pages to respect their server and our runtime budget.
    """
    out = []
    pages = [
        "https://www.scholars4dev.com/category/fully-funded-scholarships/",
        "https://www.scholars4dev.com/category/phd-scholarships/",
        "https://www.scholars4dev.com/category/masters-scholarships/",
        "https://www.scholars4dev.com/category/undergraduate-scholarships/",
        "https://www.scholars4dev.com/category/partial-scholarships/",
    ]
    for page_url in pages:
        try:
            req = urllib_request.Request(
                page_url,
                headers={**UA, "Accept": "text/html,application/xhtml+xml"},
            )
            with urllib_request.urlopen(req, timeout=20) as r:
                html = r.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"[scholars4dev] {page_url} failed: {e}", file=sys.stderr)
            continue

        # Extract <article> entries — Scholars4Dev uses <article> with
        # <h2 class="entry-title"><a href="...">Title</a></h2> and a meta
        # description. This is a best-effort regex, not a full parser.
        articles = re.findall(
            r'<article[^>]*>(?:(?!</article>).)*?</article>',
            html, re.DOTALL,
        )
        for art in articles:
            # title + link
            tm = re.search(
                r'<h2[^>]*class="[^"]*entry-title[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                art, re.DOTALL,
            )
            if not tm:
                tm = re.search(
                    r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                    art, re.DOTALL,
                )
            if not tm:
                continue
            url  = tm.group(1)
            title = re.sub(r"<[^>]+>", "", tm.group(2)).strip()
            if not title or len(title) < 5:
                continue

            # description from meta or first paragraph
            desc = ""
            dm = re.search(
                r'<meta[^>]+name="description"[^>]+content="([^"]+)"',
                art, re.DOTALL,
            )
            if dm:
                desc = dm.group(1)
            else:
                pm = re.search(
                    r'<p[^>]*>(.*?)</p>',
                    art, re.DOTALL,
                )
                if pm:
                    desc = re.sub(r"<[^>]+>", "", pm.group(1)).strip()

            # figure out region from title/description
            loc = ""
            region = _region_of(title + " " + desc)
            if region == "EU":
                loc = _country_of(title + " " + desc) or ""

            # funding type
            funding = _funding_type(title, desc)
            level   = _level(title, desc)

            # deadline — Scholars4Dev usually has "Deadline: ..." or "Closing: ..."
            dl = ""
            dlm = re.search(
                r'(?:deadline|closing|closes|apply by|apply until)[:\s]+([^<\n]+)',
                art, re.IGNORECASE | re.DOTALL,
            )
            if dlm:
                dl = _parse_date(dlm.group(1).strip()[:60])

            sid = re.sub(r"[^a-z0-9]+", "-", title.lower())[:40]
            out.append({
                "id":         f"s4d-{sid}",
                "title":      title,
                "provider":   "",
                "location":   loc or "",
                "region":     region or "",
                "country":    _country_of(title + " " + desc) if region == "EU" else "",
                "remote":     "worldwide" in (title + " " + desc).lower(),
                "funding":    funding,
                "amount":     None,
                "amount_str": "",
                "deadline":   dl,
                "deadline_remains": _deadline_remains(dl),
                "level":      level,
                "description": desc[:600] if desc else "",
                "tags":       [],
                "url":        url if url.startswith("http") else "https://www.scholars4dev.com" + url,
                "source":     "Scholars4Dev",
                "posted_ago": "",
            })
        time.sleep(0.5)
    return out


# ---------------------------------------------------------------------------
# source: Scholarships.com  (via Parse API, free tier)
# ---------------------------------------------------------------------------
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
def main():
    import urllib.request as _urllib_request
    global urllib_request
    urllib_request = _urllib_request

    api_key   = os.environ.get("SCHOLARSHIPAPI_KEY", "").strip()
    parse_key = os.environ.get("SCHOLARSHIPS_COM_KEY", "").strip()

    scholarships = []
    sources_ok  = {}

    # ── primary source ──────────────────────────────────────────
    if api_key:
        print("[scholarshipapi] fetching…", file=sys.stderr)
        try:
            scholarships += fetch_scholarshipapi(api_key)
            sources_ok["ScholarshipAPI"] = True
            print(f"[scholarshipapi] total so far: {len(scholarships)}",
                  file=sys.stderr)
        except Exception as e:
            print(f"[scholarshipapi] failed: {e}", file=sys.stderr)
            sources_ok["ScholarshipAPI"] = False
    else:
        print("[scholarshipapi] no key — skipping", file=sys.stderr)

    # ── secondary source ────────────────────────────────────────
    if parse_key:
        print("[scholarships.com] fetching…", file=sys.stderr)
        try:
            scholarships += fetch_scholarships_com()
            sources_ok["Scholarships.com"] = True
            print(f"[scholarships.com] total so far: {len(scholarships)}",
                  file=sys.stderr)
        except Exception as e:
            print(f"[scholarships.com] failed: {e}", file=sys.stderr)
            sources_ok["Scholarships.com"] = False
    else:
        print("[scholarships.com] no key — skipping", file=sys.stderr)

    # ── best-effort scrape source ───────────────────────────────
    print("[scholars4dev] scraping…", file=sys.stderr)
    try:
        scholarships += fetch_scholars4dev()
        sources_ok["Scholars4Dev"] = True
        print(f"[scholars4dev] total so far: {len(scholarships)}", file=sys.stderr)
    except Exception as e:
        print(f"[scholars4dev] failed: {e}", file=sys.stderr)
        sources_ok["Scholars4Dev"] = False

    # ── dedupe ───────────────────────────────────────────────────
    seen   = set()
    unique = []
    for s in scholarships:
        sid = s["id"]
        if sid not in seen and s.get("title") and s.get("url"):
            seen.add(sid)
            unique.append(s)

    # ── sort: nearest deadline first ─────────────────────────────
    def _deadline_key(s):
        d = s.get("deadline","")
        if d:
            try:
                return datetime.fromisoformat(d).timestamp()
            except (ValueError, TypeError):
                pass
        return 9e18
    unique.sort(key=_deadline_key)

    # ── if API returned nothing, use seed ───────────────────────
    if not unique:
        print("[scholarships] no API data — using seed", file=sys.stderr)
        unique = seed_scholarships()
        sources_ok["seed"] = True

    # ── build per-source counts ──────────────────────────────────
    per_source = {}
    for s in unique:
        src = s.get("source","") or "unknown"
        per_source[src] = per_source.get(src, 0) + 1

    snapshot = {
        "generated_at":  _now_iso(),
        "count":         len(unique),
        "per_source":    per_source,
        "sources_ok":    sources_ok,
        "scholarships":  unique,
    }

    # ── safety net: never ship an all-expired snapshot ────────────
    # If every deadline ends up in the past (bad source data or a
    # generator bug), the site's isExpired() filter would hide every
    # scholarship. Refuse to overwrite a working snapshot in that case
    # so the page keeps showing the last good data instead of going empty.
    deadlines = [s.get("deadline") for s in unique if s.get("deadline")]
    if deadlines:
        now_utc = datetime.now(timezone.utc)
        future = [d for d in deadlines
                  if _parse_dt(d) and _parse_dt(d) > now_utc]
        if not future:
            print(
                "[scholarships] FATAL: all %d deadlines are in the past — "
                "site would show no scholarships; keeping existing snapshot."
                % len(deadlines), file=sys.stderr)
            sys.exit(1)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"[scholarships] written {len(unique)} scholarships → {OUT}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
