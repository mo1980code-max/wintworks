#!/usr/bin/env python3
"""
Tests for the WordPress-source scholarship fetcher.

The WP sources (scholars4dev.com, scholarshipscorner.website,
opportunitiesforyouth.org) expose /wp-json/wp/v2/posts — the fixtures below
mirror REAL posts from those sites (titles/links/deadline phrasing), with
dynamically-computed future dates so the tests never go stale.
"""

import importlib.util
import os
import re
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(BASE, "scripts", "fetch_scholarships.py")

spec = importlib.util.spec_from_file_location("fetch_scholarships", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

NOW = datetime.now(timezone.utc)
PASS = 0


def ok(label, cond, extra=""):
    global PASS
    assert cond, f"FAIL: {label} {extra}"
    PASS += 1
    print(f"  ✔ {label}")


def future(days, fmt):
    d = NOW + timedelta(days=days)
    if fmt == "dmy":        # 18 Sept 2026
        return d.strftime("%-d %b %Y").replace(
            d.strftime("%b"), d.strftime("%B")[:3] if d.month == 9
            and d.strftime("%b") == "Sep" else d.strftime("%b")), d
    return "", d


def fmt_dmy(d):   # "18 Sept 2026" / "5 Jan 2027"
    names = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug",
             "sept", "oct", "nov", "dec"]
    return f"{d.day} {names[d.month - 1]} {d.year}"


def fmt_mdy(d):   # "December 01, 2026"
    return d.strftime("%B %d, %Y")


# ---------------------------------------------------------------- date parser
print("date parsing:")
ok("18 Sept 2026 style",
   mod._find_date("Deadline: 18 Sept 2026 (annual)").startswith("2026-09-18"))
ok("1 May 2027 style",
   mod._find_date("Deadline: 1 May 2027").startswith("2027-05-01"))
ok("December 01, 2026 style",
   mod._find_date("The application deadline is December 01, 2026.")
   .startswith("2026-12-01"))
ok("ISO style",
   mod._find_date("apply before 2026-09-18 via portal").startswith("2026-09-18"))
ok("numeric d/m/y style",
   mod._find_date("closing date 18/09/2026").startswith("2026-09-18"))
ok("noise text ignored",
   mod._find_date("Top 10 Scholarships in Switzerland for Students 2026") == "")
ok("year-only ignored", mod._find_date("Programs 2027/2028") == "")

dl = mod._extract_deadline(
    "Stuff about the programme. Deadline: " + fmt_dmy(NOW + timedelta(days=40))
    + " (annual). More text.")
ok("deadline extracted near keyword",
   dl.startswith((NOW + timedelta(days=40)).strftime("%Y-%m-%d")))

amt_num, amt_str = mod._extract_amount(
    "The grant is worth CHF 16,000 per academic year.")
ok("CHF amount", amt_num == 16000 and amt_str == "CHF 16,000",
   f"got {amt_num!r},{amt_str!r}")
amt_num, _ = mod._extract_amount("stipend of €15,000 per year")
ok("euro amount", amt_num == 15000)
amt_num, _ = mod._extract_amount("fee of $5 applies")
ok("small noise filtered", amt_num is None)

# --------------------------------------------------------------- WP converter
print("post conversion (fixtures from real posts):")

d40 = NOW + timedelta(days=40)
d90 = NOW + timedelta(days=90)

# real scholars4dev post structure (ARES scholarships)
ares = {
    "id": 2489,
    "date": (NOW - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S"),
    "link": "https://www.scholars4dev.com/2489/cud-development-scholarships-for-developing-countries/",
    "slug": "cud-development-scholarships-for-developing-countries",
    "title": {"rendered": "ARES Scholarships in Belgium for Developing Countries"},
    "content": {"rendered":
        "<p><strong>Official/Endorsed Funded Scholarship</strong>"
        "Masters Degree/Training</div>  <b>Deadline:</b> " + fmt_dmy(d40) +
        " (annual)<br>Study in:\u00a0 Belgium<br>Course starts "
        + str(d40.year + 1) + "</p>"
        "<p>Brief description: Each year, the ARES offers the chance to "
        "pursue an advanced bachelor’s or master’s degree programme or a "
        "2-to-6-month continuing education course within a higher education "
        "institution of the Wallonia-Brussels Federation, Belgium.</p>"},
    "excerpt": {"rendered": "<p>Masters Degree/Training in Belgium…</p>"},
    "class_list": ["post-2489", "category-scholarships",
                   "category-master-scholarships"],
}
item = mod._wp_post_to_scholarship("Scholars4Dev", ares)
ok("ARES post converted", item is not None)
ok("ARES deadline", item["deadline"].startswith(d40.strftime("%Y-%m-%d")),
   f"got {item['deadline']}")
ok("ARES region EU (Belgium)", item["region"] == "EU")
ok("ARES country from 'Study in'", item["country"] == "Belgium",
   f"got {item['country']!r}")
ok("ARES id prefix", item["id"].startswith("s4d-"))
ok("ARES level masters", item["level"] == "Masters")

# real scholarshipscorner post structure (EWC fellowship)
ewc = {
    "id": 27975,
    "date": NOW.strftime("%Y-%m-%dT%H:%M:%S"),
    "link": "https://scholarshipscorner.website/ewc-graduate-degree-fellowship-usa/",
    "slug": "ewc-graduate-degree-fellowship-usa",
    "title": {"rendered":
              "EWC Graduate Degree Fellowship in the United States | Fully Funded"},
    "content": {"rendered":
        "<p>The East West Center Graduate Degree Fellowship in the United "
        "States welcomes committed graduates from around the globe.</p>"
        "<h3>EWC Fellowship Application Deadline:</h3><ul><li>The application "
        "deadline is " + fmt_mdy(d90) + ".</li></ul>"
        "<h3>Program Level:</h3><ul><li>Master’s Level.</li>"
        "<li>Doctoral Level.</li></ul>"},
    "excerpt": {"rendered": "<p>Fully funded fellowship in the USA […]</p>"},
    "class_list": ["category-fellowships", "category-scholarships-in-usa",
                   "tag-fully-funded-scholarships"],
}
item = mod._wp_post_to_scholarship("ScholarshipsCorner", ewc)
ok("EWC post converted", item is not None)
ok("EWC deadline (Month DD, YYYY)", item["deadline"].startswith(
    d90.strftime("%Y-%m-%d")), f"got {item['deadline']}")
ok("EWC fully funded", item["funding"] == "Fully Funded")
ok("EWC region US", item["region"] == "US")
ok("EWC id prefix", item["id"].startswith("sc-"))

# real opportunitiesforyouth post (funding call)
ikf = {
    "id": 90876,
    "date": NOW.strftime("%Y-%m-%dT%H:%M:%S"),
    "link": "https://opportunitiesforyouth.org/2026/08/29/international-coproduction-fund-ikf/",
    "slug": "international-coproduction-fund-ikf",
    "title": {"rendered":
              "International Coproduction Fund (IKF): Funding Opportunity "
              "for International Music, Dance and Theatre Projects"},
    "content": {"rendered":
        "<p>The Goethe-Institut International Coproduction Fund (IKF) "
        "supports international artistic collaborations. Deadline: "
        + fmt_dmy(d40) + ".</p>"},
    "excerpt": {"rendered": "<p>Funding for international projects […]</p>"},
    "class_list": ["category-grants", "category-funding"],
}
item = mod._wp_post_to_scholarship("OpportunitiesForYouth", ikf)
ok("IKF post converted", item is not None)
ok("IKF region worldwide", item["region"] == "WW")
ok("IKF id prefix", item["id"].startswith("ofy-"))

# non-funding post must be filtered out (real OFY post)
nonfund = {
    "id": 90879, "date": NOW.strftime("%Y-%m-%dT%H:%M:%S"),
    "link": "https://opportunitiesforyouth.org/2026/08/29/victorias-secret/",
    "slug": "victorias-secret",
    "title": {"rendered":
              "Victoria’s Secret & PINK Early Talent Internship Opportunities"},
    "content": {"rendered": "<p>Internships in specialty retail.</p>"},
    "excerpt": {"rendered": "<p>Internships…</p>"},
    "class_list": ["category-internships"],
}
ok("non-funding post filtered",
   mod._wp_post_to_scholarship("OpportunitiesForYouth", nonfund) is None)

# past-deadline post must be skipped
past = dict(ares, id=1, slug="old-grant",
            link="https://www.scholars4dev.com/old-grant/",
            title={"rendered": "Old Closed Grant Scholarship Programme"},
            content={"rendered":
                     "<p>Deadline: " + fmt_dmy(NOW - timedelta(days=10))
                     + "</p>"})
ok("past-deadline post skipped",
   mod._wp_post_to_scholarship("Scholars4Dev", past) is None)

# ------------------------------------------------------------ build_snapshot
print("snapshot build & merge:")
scraped = [mod._wp_post_to_scholarship("Scholars4Dev", ares),
           mod._wp_post_to_scholarship("ScholarshipsCorner", ewc),
           mod._wp_post_to_scholarship("OpportunitiesForYouth", ikf)]
seed_row = seed = None
seed_rows = mod.seed_scholarships()
seed_titles = {r["title"].lower() for r in seed_rows}

snap = mod.build_snapshot(scraped, {"Scholars4Dev": True,
                                     "ScholarshipsCorner": True,
                                     "OpportunitiesForYouth": True})
_seed_unique = len({re.sub(r"[^a-z0-9]+", " ", r["title"].lower()).strip()
                     for r in mod.seed_scholarships()})
ok("snapshot = scraped + seed baseline (dups removed)",
   snap["count"] == _seed_unique + 3, f"count={snap['count']}")
ok("no title duplicates",
   len({s["title"].lower() for s in snap["scholarships"]}) == snap["count"])
ok("sorted by nearest deadline first",
   snap["scholarships"][0]["deadline"] <= snap["scholarships"][-1]["deadline"])
ok("scraped items survive dedupe",
   any(s["id"].startswith("s4d-") for s in snap["scholarships"]))

# seed-only input still works (network-down day)
snap2 = mod.build_snapshot([], {})
ok("seed-only snapshot ok", snap2["count"] == _seed_unique)

# all-expired input raises the guard (seed suppressed to isolate the check)
expired = [dict(scraped[0], deadline=(NOW - timedelta(days=1)).isoformat())]
_orig_seed = mod.seed_scholarships
mod.seed_scholarships = lambda: []
try:
    mod.build_snapshot(expired, {})
    ok("all-expired guard raises", False)
except mod.AllExpiredError:
    ok("all-expired guard raises", True)
finally:
    mod.seed_scholarships = _orig_seed

print(f"\nAll {PASS} WordPress-source checks passed.")
