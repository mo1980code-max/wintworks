#!/usr/bin/env python3
"""
WintWorks — snapshot builder (runs automatically via GitHub Actions cron OR locally).
Fetches jobs from free public APIs, keeps ONLY United States jobs,
deduplicates, normalizes, and writes data/jobs.json (served with the site).

No API keys, no fees, no manual work.
"""
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data", "jobs.json")

UA = {"User-Agent": "Mozilla/5.0 (compatible; WintWorks/1.0)"}


def get_json(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


# ---------------------------------------------------------------- US + ALL-EUROPE detection
US_STATES = {
    "alabama","alaska","arizona","arkansas","california","colorado","connecticut",
    "delaware","florida","georgia","hawaii","idaho","illinois","indiana","iowa",
    "kansas","kentucky","louisiana","maine","maryland","massachusetts","michigan",
    "minnesota","mississippi","missouri","montana","nebraska","nevada","new hampshire",
    "new jersey","new mexico","new york","north carolina","north dakota","ohio",
    "oklahoma","oregon","pennsylvania","rhode island","south carolina","south dakota",
    "tennessee","texas","utah","vermont","virginia","washington","west virginia",
    "wisconsin","wyoming","district of columbia",
}
US_ABBR = {
    "al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id","il","in","ia","ks",
    "ky","la","me","md","ma","mi","mn","ms","mo","mt","ne","nv","nh","nj","nm","ny",
    "nc","nd","oh","ok","or","pa","ri","sc","sd","tn","tx","ut","vt","va","wa","wv",
    "wi","wy","dc",
}
US_CITIES = {
    "atlanta","austin","baltimore","boston","charlotte","chicago","cincinnati",
    "cleveland","columbus","dallas","denver","detroit","houston","indianapolis",
    "jacksonville","las vegas","los angeles","miami","milwaukee","minneapolis",
    "nashville","new orleans","new york","newark","oakland","oklahoma city",
    "omaha","orlando","philadelphia","phoenix","pittsburgh","portland","raleigh",
    "sacramento","san antonio","san diego","san francisco","san jose","seattle",
    "st. louis","st louis","tampa","washington","arlington","boulder","brooklyn",
    "burlington","chandler","charleston","colorado springs","fort worth","frisco",
    "fremont","grand rapids","irvine","jersey city","kansas city","long beach",
    "madison","menlo park","mountain view","new haven","palo alto","plano",
    "redmond","richmond","rochester","salt lake city","santa clara","santa fe",
    "santa monica","sunnyvale","tempe","tucson","tulsa","urbana","waltham",
    "walnut creek","princeton","albany","ann arbor","asheville","boise","corvallis",
    "davis","durham","evanston","fort collins","gainesville","hershey","knoxville",
    "lexington","lincoln","little rock","louisville","mclean","memphis","mesa",
    "norfolk","pasadena","provo","reston","round rock","san mateo","scottsdale",
    "sioux falls","spokane","springfield","stamford","syracuse","tallahassee",
    "wichita","wilmington","worcester","birmingham","manchester","bristol","oxford",
    "plymouth","brighton",
}

EU_WORDS = [
    "europe","european","united kingdom","britain","british","england","scotland",
    "wales","northern ireland","ireland","france","germany","deutschland","allemagne",
    "spain","españa","italy","italia","portugal","netherlands","nederland","holland",
    "belgium","belgique","belgie","luxembourg","switzerland","schweiz","suisse",
    "austria","österreich","sweden","sverige","norway","norge","denmark","danmark",
    "finland","suomi","iceland","poland","polska","polen","czech","czechia",
    "czech republic","slovakia","hungary","romania","bulgaria","greece","croatia",
    "slovenia","serbia","bosnia","montenegro","macedonia","albania","kosovo",
    "estonia","latvia","lithuania","ukraine","moldova","belarus","russia","malta",
    "cyprus","turkey","türkiye","georgien","armenia","azerbaijan","monaco","andorra",
    "liechtenstein","gibraltar","isle of man","bavaria","bayern",
]
EU_ABBR = {"uk","gb","ie","fr","es","it","pt","nl","be","lu","ch","at","se","no",
    "dk","fi","is","pl","cz","sk","hu","ro","bg","gr","hr","si","rs","ba","mk","xk",
    "ee","lv","lt","ua","by","ru","cy","tr"}
EU_CITIES = {
    "london","leeds","liverpool","edinburgh","glasgow","belfast","cardiff","dublin",
    "cork","paris","lyon","marseille","toulouse","bordeaux","nice","lille",
    "strasbourg","nantes","berlin","munich","munchen","münchen","hamburg","frankfurt",
    "cologne","köln","stuttgart","dusseldorf","düsseldorf","leipzig","dortmund",
    "essen","bremen","dresden","hanover","nuremberg","nürnberg","trier","zurich",
    "zürich","geneva","genève","basel","bern","lausanne","amsterdam","rotterdam",
    "utrecht","eindhoven","brussels","brussel","antwerp","ghent","vienna","wien",
    "graz","linz","salzburg","madrid","barcelona","valencia","seville","bilbao",
    "malaga","lisbon","lisboa","porto","milan","milano","rome","roma","turin",
    "torino","naples","napoli","florence","firenze","warsaw","warszawa","krakow",
    "kraków","wroclaw","gdansk","poznan","lodz","lublin","katowice","szczecin",
    "prague","praha","brno","bratislava","budapest","debrecen","szeged","bucharest",
    "bucuresti","cluj","timisoara","iasi","brasov","sofia","plovdiv","varna",
    "athens","athina","thessaloniki","zagreb","split","dubrovnik","ljubljana",
    "belgrade","beograd","sarajevo","skopje","tirana","podgorica","tallinn","tartu",
    "riga","vilnius","kaunas","klaipeda","kyiv","kiev","lviv","odesa","chisinau",
    "minsk","valletta","nicosia","limassol","istanbul","ankara","tbilisi","yerevan",
    "baku","reykjavik","monaco","gibraltar","stockholm","gothenburg","malmo",
    "uppsala","lund","oslo","bergen","stavanger","trondheim","copenhagen",
    "københavn","helsinki","tampere","turku","oulu",
}
# City names shared by the UK and US are not US evidence without a state/country.
UK_AMBIGUOUS_CITIES = {"manchester","birmingham","bristol","cambridge","oxford",
    "newcastle","richmond","plymouth","brighton","york","bath"}
US_CITIES.difference_update(UK_AMBIGUOUS_CITIES)
EU_CITIES.update(UK_AMBIGUOUS_CITIES)

WW_WORDS = ["worldwide","anywhere","any country","global","all countries",
    "international","emea","remote","homeoffice","fully remote","remote job",
    "work from home","wfh"]

COUNTRY_MARKERS = [
    ("United Kingdom", ["united kingdom","britain","british","england","scotland","wales","northern ireland","uk","london","manchester","birmingham","bristol","cambridge","oxford","newcastle","richmond","plymouth","brighton","york","bath","leeds","liverpool","edinburgh","glasgow","belfast","cardiff"]),
    ("Germany", ["germany","deutschland","allemagne","bavaria","bayern","berlin","munich","munchen","münchen","hamburg","frankfurt","cologne","köln","stuttgart","dusseldorf","düsseldorf","leipzig","dortmund","essen","bremen","dresden","hanover","nuremberg","nürnberg","trier","de-"]),
    ("France", ["france","paris","lyon","marseille","toulouse","bordeaux","nice","lille","strasbourg","nantes"]),
    ("Netherlands", ["netherlands","nederland","holland","amsterdam","rotterdam","utrecht","eindhoven"]),
    ("Belgium", ["belgium","belgique","belgie","brussels","brussel","antwerp","ghent"]),
    ("Switzerland", ["switzerland","schweiz","suisse","zurich","zürich","geneva","genève","basel","bern","lausanne","luzern"]),
    ("Austria", ["austria","österreich","oesterreich","vienna","wien","graz","linz","salzburg"]),
    ("Spain", ["spain","españa","espana","espagne","madrid","barcelona","valencia","seville","bilbao","malaga"]),
    ("Portugal", ["portugal","lisbon","lisboa","porto"]),
    ("Italy", ["italy","italia","italie","milan","milano","rome","roma","turin","torino","naples","napoli","florence","firenze"]),
    ("Ireland", ["ireland","irland","irlande","dublin","cork"]),
    ("Sweden", ["sweden","sverige","schweden","suède","stockholm","gothenburg","malmo","uppsala","lund"]),
    ("Norway", ["norway","norge","norwegen","oslo","bergen","stavanger","trondheim"]),
    ("Denmark", ["denmark","danmark","dänemark","copenhagen","københavn","aarhus","odense"]),
    ("Finland", ["finland","finlande","finnland","suomi","helsinki","tampere","turku","oulu"]),
    ("Iceland", ["iceland","island","ísland","reykjavik"]),
    ("Poland", ["poland","polska","polen","pologne","warsaw","warszawa","krakow","kraków","wroclaw","gdansk","poznan","lodz","lublin","katowice","szczecin"]),
    ("Czechia", ["czech","czechia","tschechien","tchéquie","prague","praha","brno"]),
    ("Slovakia", ["slovakia","slovensko","slowakei","bratislava"]),
    ("Hungary", ["hungary","ungarn","hongrie","budapest","debrecen","szeged"]),
    ("Romania", ["romania","românia","rumänien","bucharest","bucuresti","cluj","timisoara","iasi","brasov"]),
    ("Bulgaria", ["bulgaria","bulgarien","sofia","plovdiv","varna"]),
    ("Greece", ["greece","griechenland","grèce","athens","athina","thessaloniki"]),
    ("Croatia", ["croatia","kroatien","hrvatska","zagreb","split","dubrovnik"]),
    ("Slovenia", ["slovenia","slowenien","slovenija","ljubljana"]),
    ("Serbia", ["serbia","serbien","srbija","belgrade","beograd"]),
    ("Bosnia & Herzegovina", ["bosnia","bosnien","bosnie","sarajevo"]),
    ("Montenegro", ["montenegro","monténégro","podgorica"]),
    ("North Macedonia", ["macedonia","nordmazedonien","skopje"]),
    ("Albania", ["albania","albanien","tirana"]),
    ("Kosovo", ["kosovo"]),
    ("Estonia", ["estonia","estland","eesti","tallinn","tartu"]),
    ("Latvia", ["latvia","lettland","latvija","riga"]),
    ("Lithuania", ["lithuania","litauen","lietuva","vilnius","kaunas","klaipeda"]),
    ("Ukraine", ["ukraine","ukraina","kyiv","kiev","lviv","odesa"]),
    ("Moldova", ["moldova","moldawien","chisinau"]),
    ("Belarus", ["belarus","weissrussland","minsk"]),
    ("Malta", ["malta","valletta"]),
    ("Cyprus", ["cyprus","zypern","chypre","nicosia","limassol"]),
    ("Turkey", ["turkey","türkiye","turquie","türkei","istanbul","ankara"]),
    ("Georgia", ["tbilisi","georgien","géorgie"]),
    ("Armenia", ["armenia","armenien","yerevan"]),
    ("Azerbaijan", ["azerbaijan","aserbaidschan","baku"]),
    ("Monaco", ["monaco"]),
    ("Luxembourg", ["luxembourg","luxemburg"]),
    ("Andorra", ["andorra"]),
    ("Liechtenstein", ["liechtenstein"]),
    ("Gibraltar", ["gibraltar"]),
]


def _word(s, w):
    return re.search(r"\b" + re.escape(w) + r"\b", s) is not None


def _abbr(set_, s):
    m = re.search(r",\s*([a-z]{2})\b", s)
    if m and m.group(1) in set_:
        return True
    m = re.search(r"\b([a-z]{2})\s*[,.]?$", s)
    if m and m.group(1) in set_:
        return True
    return False


def has_worldwide(s):
    low = s.lower()
    return any(w in low for w in WW_WORDS)


def region_of(loc):
    """'US' | 'EU' | 'WW' | None — strong evidence beats weak (city) evidence"""
    if not loc:
        return None
    s = loc.strip().lower()
    if not s:
        return None
    us_strong = any(_word(s, w) for w in US_STATES) or _abbr(US_ABBR, s) \
        or any(x in s for x in ("united states", "usa", "u.s.a", "us only"))
    eu_strong = any(_word(s, w) for w in EU_WORDS) or _abbr(EU_ABBR, s)
    us_city = any(_word(s, c) for c in US_CITIES)
    eu_city = any(_word(s, c) for c in EU_CITIES)
    if us_strong and eu_strong:
        return "WW"
    if eu_strong and not us_strong:
        return "EU"
    if us_strong and not eu_strong:
        return "US"
    if eu_city and not us_city:
        return "EU"
    if us_city and not eu_city:
        return "US"
    if has_worldwide(s):
        return "WW"
    return None


def country_of(loc):
    """country display name: 'USA' for US, country name for EU, '' otherwise"""
    if not loc:
        return ""
    s = loc.strip().lower()
    if not s:
        return ""
    r = region_of(loc)
    if r == "US":
        return "USA"
    if r != "EU":
        return ""
    for name, markers in COUNTRY_MARKERS:
        if any(_word(s, w) for w in markers):
            return name
    return ""


# ---------------------------------------------------------------- categories
TAXONOMY = [
    ("Engineering & IT", ["engineering","software","developer","development","devops",
        "frontend","backend","full stack","mobile","ios","android","qa","testing",
        "engineer","tech","it ","information technology","cloud","security","sysadmin",
        "infrastructure","web","python","java","javascript","react","node","golang",
        "ruby","php","blockchain","game","embedded","hardware","architect"]),
    ("Data & AI", ["data","analytics","analyst","analyst","machine learning"," ml ",
        " ai ","artificial intelligence","bi ","database","scientist","statistician",
        "deep learning","nlp","computer vision"]),
    ("Design & Creative", ["design","ux","ui","graphic","creative","illustrator",
        "animation","art ","visual","brand","figma","product design","interior"]),
    ("Marketing & Growth", ["marketing","seo","growth","digital marketing",
        "social media","content marketing","brand","affiliate","ppc","advertising",
        "go-to-market","gtm","communications","community","email marketing","cmo"]),
    ("Sales & Business Dev", ["sales","account executive","business development",
        "bdr","sdr","account manager","partnership","sales development","closer"]),
    ("Product & Project", ["product","pm","product manager","product owner",
        "project manager","program manager","scrum","agile","delivery manager"]),
    ("Customer Support", ["customer support","customer service","support","success",
        "customer success","csm","help desk","technical support","service desk"]),
    ("Finance & Accounting", ["finance","accounting","bookkeeper","financial",
        "tax","audit","payroll","controller","treasury","cpa","actuary","banking"]),
    ("HR & Recruiting", ["hr","human resources","recruiter","recruiting","talent",
        "people operations","people","onboarding","payroll adm"]),
    ("Writing & Content", ["writing","writer","content","copywriter","editor",
        "journalism","translation","editorial","blog","author","proofreader"]),
    ("Operations & Admin", ["operations","administration","office manager",
        "logistics","supply chain","facilities","executive assistant","admin",
        "procurement","warehouse","driver","receptionist","clerk"]),
    ("Education & Training", ["education","teacher","tutor","training",
        "instructional","elearning","learning","professor","curriculum","edtech"]),
    ("Healthcare & Wellness", ["healthcare","nurse","medical","clinical","health",
        "therapy","pharma","physician"," care ","dentist","psycholog","wellness"]),
    ("Legal & Compliance", ["legal","lawyer","attorney","compliance","counsel",
        "paralegal","law ","legal counsel","regulatory"]),
    ("Other", []),
]


def map_category(*texts) -> str:
    blob = " ".join(t.lower() for t in texts if t)
    for name, keys in TAXONOMY:
        if not keys:
            continue
        for k in keys:
            if k in blob:
                return name
    return "Other"


def fmt_money(lo, hi, symbol="$", period="/ year"):
    def m(v):
        return f"{symbol}{float(v):,.0f}" if v else None
    a, b = m(lo), m(hi)
    if a and b:
        return f"{a} – {b} {period}"
    if a:
        return f"{a} {period}"
    if b:
        return f"up to {b} {period}"
    return ""


def clean_desc(html: str) -> str:
    if not html:
        return ""
    # normalize newlines inside plain-text descriptions
    if not re.search(r"<[a-zA-Z]", html):
        html = html.replace("\n", "<br>")
    return html[:1200]


def dt(ts=None):
    return datetime.now(timezone.utc).isoformat()



# Multilingual keywords (DE/FR/ES/IT/NL/PL) so localized Adzuna/Arbeitnow listings
# still map into the right category.
_EXTRA_KEYS = {
    "Engineering & IT": ["informatik", "informatica", "informática", "informatyka",
        "ingenieur", "ingeniero", "ingénieur", "inżynier", "entwickler",
        "desarrollador", "programador", "programmeur", "programista",
        "softwareentwickler", "sistemas", "système", "elektronik", "netzwerk",
        "technik", "ingeniería", "ingenieria", "ingenierie"],
    "Data & AI": ["daten", "datos", "données", "dane", "künstliche intelligenz",
        "inteligencia artificial", "intelligence artificielle",
        "sztuczna inteligencja", "analityk", "datenschutz"],
    "Design & Creative": ["gestaltung", "diseño", "diseno", "conception",
        "projektowanie", "grafika", "ilustración", "illustration"],
    "Marketing & Growth": ["werbung", "publicidad", "pubblicità", "reklama",
        "kommunikation", "comunicación", "communication", "communicatie",
        "komunikacja", "mercadeo", "marketing"],
    "Sales & Business Dev": ["verkauf", "vertrieb", "ventas", "vendite",
        "sprzedaż", "sprzedaz", "verkoop", "handel", "commercial"],
    "Product & Project": ["produktmanager", "projektleitung", "projektmanager",
        "chef de projet", "projectleider", "kierownik projektu",
        "productmanager"],
    "Customer Support": ["kundendienst", "service client", "servicio al cliente",
        "klantenservice", "obsługa klienta", "observação",
        "support"],
    "Finance & Accounting": ["finanzen", "finanzas", "finances", "financieel",
        "księgowość", "ksiegowosc", "buchhaltung", "comptabilité",
        "contabilidad", "contabilità", "rechnungswesen", "buchhalter",
        "accountant", "finanz"],
    "HR & Recruiting": ["personalwesen", "recursos humanos",
        "ressources humaines", "personeelszaken", "zasoby ludzkie",
        "personalabteilung"],
    "Writing & Content": ["redaktion", "redacción", "rédaction", "tekst",
        "content", "übersetzer", "traductor", "traducteur", "tłumacz"],
    "Operations & Admin": ["logistik", "logística", "logistique", "logistiek",
        "logistyka", "verwaltung", "administración", "administration",
        "administratie", "administracja", "einkauf", "compras", "achats",
        "inkoop", "zakupy", "lager", "sachbearbeiter"],
    "Education & Training": ["bildung", "enseñanza", "enseignement",
        "onderwijs", "nauczanie", "lehrer", "profesor", "enseignant",
        "docent", "nauczyciel", "ausbildung"],
    "Healthcare & Wellness": ["gesundheit", "gesundheitswesen", "pflege",
        "soins", "santé", "sanidad", "salud", "salute", "zdrowie",
        "gezondheidszorg", "verpleging", "verpleegkundige", "cuidados",
        "medizin", "médecine", "medicina", "medycyna",
        "krankenpflege", "infirmier"],
    "Legal & Compliance": ["recht", "droit", "derecho", "diritto", "prawo",
        "juridique", "juridisch", "jurídico", "giuridico", "prawny",
        "anwalt", "advocaat"],
}
for _cat, _kws in _EXTRA_KEYS.items():
    for _row in TAXONOMY:
        if _row[0] == _cat:
            _row[1].extend(_kws)
            break

# ---------------------------------------------------------------- sources
def fetch_muse():
    jobs = []
    for page in (1, 2, 3, 4, 5):
        try:
            d = get_json(
                f"https://www.themuse.com/api/public/jobs?page={page}&limit=20"
            )
        except Exception:
            continue
        for r in d.get("results", []):
            locs = [l.get("name", "") for l in r.get("locations", [])]
            loc = "; ".join([x for x in locs if x])
            if loc and not region_of(loc):
                continue
            cats = [c.get("name", "") for c in r.get("categories", [])]
            levels = [l.get("name", "") for l in r.get("levels", [])]
            tags = [t.get("name", "") for t in r.get("tags", [])]
            jobs.append({
                "id": f"muse-{r['id']}",
                "title": r.get("name", ""),
                "company": (r.get("company") or {}).get("name", ""),
                "logo": "",
                "location": loc or "United States",
                "remote": False,
                "type": "",
                "salary": "",
                "date": r.get("publication_date", ""),
                "region": region_of(loc),
                "country": country_of(loc),
                "category": map_category(*cats, *tags, r.get("name", "")),
                "tags": tags[:6],
                "description": clean_desc(r.get("contents", "")),
                "url": (r.get("refs") or {}).get("landing_page", ""),
                "source": "The Muse",
            })
        time.sleep(0.4)
    return jobs


def fetch_jobicy():
    try:
        d = get_json("https://jobicy.com/api/v2/remote-jobs")
    except Exception:
        return []
    jobs = []
    for r in d.get("jobs", []):
        geo = r.get("jobGeo", "")
        if not region_of(geo):
            continue
        lo, hi = r.get("salaryMin"), r.get("salaryMax")
        salary = fmt_money(lo, hi, period="/ " + (r.get("salaryPeriod") or "year"))
        jt = r.get("jobType") or []
        jobs.append({
            "id": f"jobicy-{r['id']}",
            "title": r.get("jobTitle", ""),
            "company": r.get("companyName", ""),
            "logo": r.get("companyLogo", ""),
            "location": geo,
            "remote": True,
            "type": jt[0] if jt else "",
            "salary": salary,
            "date": r.get("pubDate", ""),
            "region": region_of(geo),
                "country": country_of(geo),
            "category": map_category(*(r.get("jobIndustry") or []), r.get("jobTitle", "")),
            "tags": (r.get("jobIndustry") or [])[:4],
            "description": clean_desc(r.get("jobDescription", "") or r.get("jobExcerpt", "")),
            "url": r.get("url", ""),
            "source": "Jobicy",
        })
    return jobs


def fetch_remotive():
    try:
        d = get_json("https://remotive.com/api/remote-jobs")
    except Exception:
        return []
    jobs = []
    for r in d.get("jobs", []):
        loc = r.get("candidate_required_location", "")
        if not region_of(loc):
            continue
        jobs.append({
            "id": f"remotive-{r['id']}",
            "title": r.get("title", ""),
            "company": r.get("company_name", ""),
            "logo": r.get("company_logo_url", "") or r.get("company_logo", ""),
            "location": loc,
            "remote": True,
            "type": (r.get("job_type", "") or "").replace("_", " ").title(),
            "salary": r.get("salary", ""),
            "date": r.get("publication_date", ""),
            "region": region_of(loc),
                "country": country_of(loc),
            "category": map_category(r.get("category", ""), *(r.get("tags") or []),
                                     r.get("title", "")),
            "tags": (r.get("tags") or [])[:6],
            "description": clean_desc(r.get("description", "")),
            "url": r.get("url", ""),
            "source": "Remotive",
        })
    return jobs


def fetch_remoteok():
    try:
        d = get_json("https://remoteok.com/api")
    except Exception:
        return []
    jobs = []
    for r in d:
        if not isinstance(r, dict) or "position" not in r:
            continue
        loc = (r.get("location") or "").replace(",", " ").strip()
        if not region_of(loc):
            continue
        salary = fmt_money(r.get("salary_min"), r.get("salary_max"),
                           period="/ year (est.)")
        jobs.append({
            "id": f"remoteok-{r.get('slug', r.get('id'))}",
            "title": r.get("position", ""),
            "company": r.get("company", ""),
            "logo": r.get("company_logo", "") or r.get("logo", ""),
            "location": loc,
            "remote": True,
            "type": "Remote",
            "salary": salary,
            "date": r.get("date", ""),
            "region": region_of(loc),
                "country": country_of(loc),
            "category": map_category(*(r.get("tags") or []), r.get("position", "")),
            "tags": (r.get("tags") or [])[:6],
            "description": clean_desc(r.get("description", "")),
            "url": r.get("apply_url") or r.get("url", ""),
            "source": "RemoteOK",
        })
    return jobs


def fetch_arbeitnow():
    jobs = []
    for page in range(1, 21):
        try:
            url = f"https://www.arbeitnow.com/api/job-board-api?page={page}"
            d = get_json(url)
        except Exception:
            continue
        for r in d.get("data", []):
            loc = r.get("location", "")
            source_url = r.get("url", "") or ""
            is_uk_source = "arbeitnow.co.uk" in source_url.lower()
            reg = "EU" if is_uk_source else region_of(loc)
            if not reg:
                continue
            jt = r.get("job_types") or []
            jobs.append({
                "id": f"arbeitnow-{r.get('slug', str(r.get('created_at', '')))}",
                "title": r.get("title", ""),
                "company": r.get("company_name", ""),
                "logo": "",
                "location": loc,
                "region": reg,
                "country": "United Kingdom" if is_uk_source else country_of(loc),
                "remote": bool(r.get("remote")),
                "type": jt[0] if jt else "",
                "salary": "",
                "date": datetime.fromtimestamp(r.get("created_at", 0), tz=timezone.utc)
                    .isoformat() if r.get("created_at") else "",
                "category": map_category(*(r.get("tags") or []), r.get("title", "")),
                "tags": (r.get("tags") or [])[:6],
                "description": clean_desc(r.get("description", "")),
                "url": r.get("url", ""),
                "source": "Arbeitnow",
            })
    return jobs




ADZUNA_MARKETS = [
    ("gb", "United Kingdom", "£"), ("de", "Germany", "€"), ("fr", "France", "€"),
    ("nl", "Netherlands", "€"), ("it", "Italy", "€"), ("es", "Spain", "€"),
    ("pl", "Poland", "zł"), ("at", "Austria", "€"), ("be", "Belgium", "€"),
    ("ch", "Switzerland", "CHF"), ("us", "USA", "$"),
]


def _parse_date(v):
    """Accepts ISO-8601 ('2026-08-10T20:43:36Z') or unix seconds."""
    if not v:
        return ""
    if isinstance(v, (int, float)) or str(v).isdigit():
        return datetime.fromtimestamp(float(v), tz=timezone.utc).isoformat()
    s = str(v).strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).isoformat()
    except Exception:
        return s[:10]


def fetch_adzuna():
    """Optional source — uses keys from env ADZUNA_ID/ADZUNA_KEY or data/adzuna.json.
    Free key: https://developer.adzuna.com — 1 call per market per day."""
    app_id = os.environ.get("ADZUNA_ID", "")
    app_key = os.environ.get("ADZUNA_KEY", "")
    if not app_id or not app_key:
        cfg_path = os.path.join(BASE, "data", "adzuna.json")
        if os.path.exists(cfg_path):
            try:
                cfg = json.load(open(cfg_path))
                app_id = cfg.get("appId", "")
                app_key = cfg.get("appKey", "")
            except Exception:
                pass
    if not app_id or not app_key or "YOUR" in app_id or "YOUR" in app_key:
        print("  Adzuna: skipped (no key) — get a free one at developer.adzuna.com")
        return []
    jobs = []
    for code, label, symbol in ADZUNA_MARKETS:
        try:
            d = get_json(
                f"https://api.adzuna.com/v1/api/jobs/{code}/search/1"
                f"?app_id={app_id}&app_key={app_key}&results_per_page=50&sort_by=date",
                timeout=30)
        except Exception as e:
            print(f"  Adzuna {code}: ERROR {e}")
            continue
        for r in d.get("results", []):
            loc_inner = r.get("location") or {}
            loc = (loc_inner.get("display_name") or "").strip() or label
            title = r.get("title", "")
            company = (r.get("company") or {}).get("display_name", "")
            salary = ""
            if r.get("salary_min") or r.get("salary_max"):
                salary = fmt_money(r.get("salary_min"), r.get("salary_max"),
                                   symbol=symbol, period="/ year")
            cat_label = (r.get("category") or {}).get("label", "")
            jobs.append({
                "id": f"adzuna-{code}-{r.get('id')}",
                "title": title,
                "company": company,
                "logo": "",
                "location": loc,
                "region": "US" if code == "us" else "EU",
                "country": "USA" if code == "us" else label,
                "remote": "remote" in loc.lower() or "remote" in title.lower(),
                "type": "",
                "salary": salary,
                "date": _parse_date(r.get("created")),
                "category": map_category(cat_label, title),
                "tags": [t for t in (r.get("contract_time"),) if t][:3],
                "description": clean_desc(r.get("description", "")),
                "url": r.get("redirect_url", "") or r.get("redirect_link", ""),
                "source": "Adzuna",
            })
    return jobs




SOURCES = [
    ("The Muse", fetch_muse, "US on-site & hybrid jobs from 400k+ live listings"),
    ("Jobicy", fetch_jobicy, "US remote jobs with salary data"),
    ("RemoteOK", fetch_remoteok, "Remote tech jobs open to US candidates"),
    ("Remotive", fetch_remotive, "Remote jobs for US & Europe based applicants"),
    ("Arbeitnow", fetch_arbeitnow, "European jobs network (UK, DACH, Benelux…)"),
    ("Adzuna", fetch_adzuna, "OPTIONAL — local jobs for GB/DE/FR/NL/IT/ES/PL/AT/BE/CH/US (free key)"),
]


def main():
    all_jobs = []
    per_source = {}
    errors = []
    for name, fn, _ in SOURCES:
        try:
            js = fn()
            per_source[name] = len(js)
            all_jobs.extend(js)
            print(f"  {name}: {len(js)} jobs (US/EU/WW)")
            time.sleep(0.5)
        except Exception as e:
            errors.append(f"{name}: {e}")
            per_source[name] = 0
            print(f"  {name}: ERROR {e}")

    # dedupe by title+company (cross-source duplicates)
    seen = {}
    for j in all_jobs:
        key = (j["title"].strip().lower(), j["company"].strip().lower())
        if key in seen:
            existing = seen[key]
            # keep the richer one (longer description)
            if len(j["description"]) > len(existing["description"]):
                seen[key] = j
        else:
            seen[key] = j
    jobs = sorted(seen.values(),
                  key=lambda j: j.get("date", ""), reverse=True)[:1800]

    for j in jobs:  # drop empty fields to shrink the payload
        if not j.get("logo"):
            j.pop("logo", None)
        if not j.get("type"):
            j.pop("type", None)
        if not j.get("tags"):
            j.pop("tags", None)
    payload = {
        "generated_at": dt(),
        "count": len(jobs),
        "per_source": per_source,
        "jobs": jobs,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    from collections import Counter
    regs = Counter(j.get("region", "") for j in jobs)
    ctrs = Counter(j.get("country", "Worldwide / Remote") for j in jobs)
    print("  regions:", dict(regs.most_common()))
    print("  top countries:", dict(ctrs.most_common(20)))
    size = os.path.getsize(OUT) / 1024
    print(f"Wrote {OUT}: {len(jobs)} jobs ({size:.0f} KB)")
    if errors:
        print("Errors:", errors)

    # Generate dedicated, crawlable detail pages with JobPosting JSON-LD.
    # Import here so this file remains runnable directly from any working directory.
    from generate_static_jobs import main as generate_static_jobs
    generate_static_jobs()
    return 0


if __name__ == "__main__":
    sys.exit(main())
