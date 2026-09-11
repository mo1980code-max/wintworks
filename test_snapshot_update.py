#!/usr/bin/env python3
"""
Regression tests for the "site does not update its jobs" bugs (fixed 2026-09-11).

The GitHub Actions cron *was* running and committing every six hours, yet the board
looked frozen. Three defects in scripts/build_snapshot.py explain it:

  1. The snapshot was trimmed with `sorted(...)[:1800]` over raw `date` strings from
     six different sources in four different formats ('...Z', '+00:00', naive,
     unix seconds, and Adzuna's local-time-as-UTC). Lexical order is not date order,
     and the biggest feed then ate every slot: per run The Muse returned 96 jobs and
     3 survived, Remotive 16 → 1, RemoteOK 37 → 1. Visitors filtering USA or
     Worldwide/remote saw the same handful of listings on every deploy.
  2. Adzuna stamps ~2h in the future, so its jobs permanently outranked every other
     source in the newest-first order.
  3. Nothing guarded a collapsed crawl: if every source errored, build_snapshot.py
     wrote a near-empty data/jobs.json and the workflow committed it, emptying the
     live board.

Also covered: the per-source ceiling, atomic writes, and the app.min.js / app.css
cache-busting stamp that keeps a cached bundle from running old code over new data.
"""

import importlib.util
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from types import ModuleType

BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


snap = load("build_snapshot")

REAL_NOW = datetime(2026, 9, 11, 12, 0, 0, tzinfo=timezone.utc)
failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok  {label}")
    else:
        print(f" FAIL {label} {detail}")
        failures.append(label)


def job(i, source, date, region="EU", country="Germany", desc="x"):
    return {
        "id": f"{source}-{i}", "title": f"T{i}", "company": f"C{i}", "description": desc,
        "date": date, "source": source, "region": region, "country": country,
        "url": f"https://example.com/{i}", "location": "Berlin", "category": "Other",
    }


# ------------------------------------------------------------------ 1. date parsing
print("\n[parse_date_utc]")
cases = {
    "2026-09-11T07:36:07+00:00": "2026-09-11T07:36:07+00:00",   # already normalised
    "2026-09-10T20:22:18Z":      "2026-09-10T20:22:18+00:00",   # The Muse 'Z'
    "2026-09-08T21:47:54":       "2026-09-08T21:47:54+00:00",   # naive → assumed UTC
    "2026-09-11":               "2026-09-11T00:00:00+00:00",   # date only
    "1757517367":               "2025-09-10T15:16:07+00:00",   # unix seconds (RemoteOK)
    "":                         "",                              # missing
    "not a date":               "",                              # garbage
}
for raw, want in cases.items():
    got = snap.parse_date_utc(raw, now=REAL_NOW)
    if want and got != want:
        # allow any equivalent instant: compare parsed values instead of strings
        try:
            same = datetime.fromisoformat(got) == datetime.fromisoformat(want)
        except ValueError:
            same = False
        check(f"{raw!r} → instant", same, f"got {got!r} want {want!r}")
    else:
        check(f"{raw!r} → {got!r}", got == want, f"got {got!r}")

check("RFC-2822 parses", snap.parse_date_utc(
    "Thu, 10 Sep 2026 19:42:29 +0000", now=REAL_NOW) == "2026-09-10T19:42:29+00:00")
check("offset converted to UTC", snap.parse_date_utc(
    "2026-09-11T14:34:00+02:00", now=REAL_NOW + timedelta(hours=6))
    == "2026-09-11T12:34:00+00:00")
check("future stamp clamped (Adzuna local-time bug)",
      snap.parse_date_utc("2026-12-31T23:00:00+00:00", now=REAL_NOW)
      == REAL_NOW.isoformat())
check("clock skew within 20 min tolerated",
      snap.parse_date_utc((REAL_NOW + timedelta(minutes=5)).isoformat(), now=REAL_NOW)
      == (REAL_NOW + timedelta(minutes=5)).isoformat())
for src in list(cases) + ["Thu, 10 Sep 2026 19:42:29 +0000"]:
    out = snap.parse_date_utc(src, now=REAL_NOW)
    if out:
        check(f"idempotent on {out!r}", snap.parse_date_utc(out, now=REAL_NOW) == out)

# --------------------------------------------------------- 1b. source clock-skew shift
print("\n[align_future_dates]")
skewed = [job(i, "Adzuna",
              (REAL_NOW + timedelta(hours=2) - timedelta(minutes=7 * i)).isoformat())
          for i in range(5)]
untouched = [job(i, "The Muse", (REAL_NOW - timedelta(hours=1)).isoformat(), "US", "USA")
             for i in range(2)]
moved = snap.align_future_dates(skewed + untouched, now=REAL_NOW)
check("future batch shifted as a whole", moved == 5, f"shifted {moved}")
check("shifted batch keeps its spread (no identical '32m ago' stamps)",
      len({j["date"] for j in skewed}) == 5, str([j["date"] for j in skewed]))
check("shifted batch no longer runs into the future",
      all(snap.parse_date_utc(j["date"], now=REAL_NOW) == j["date"] for j in skewed))
check("newest shifted listing sits at build time",
      skewed[0]["date"] == REAL_NOW.isoformat(), skewed[0]["date"])
check("sources without skew are left alone",
      untouched[0]["date"] == (REAL_NOW - timedelta(hours=1)).isoformat())

# ------------------------------------------------------------------ 2. ordering + fairness
print("\n[select_jobs]")
mixed = ([job(i, "Arbeitnow", (REAL_NOW - timedelta(hours=i)).isoformat())
          for i in range(1400)]
         + [job(i, "Adzuna", (REAL_NOW - timedelta(minutes=30 * i)).isoformat())
            for i in range(550)]
         + [job(i, "The Muse", (REAL_NOW - timedelta(days=1)).isoformat(), "US", "USA")
            for i in range(96)]
         + [job(i, "RemoteOK", (REAL_NOW - timedelta(days=2)).isoformat(), "WW", "")
            for i in range(37)]
         + [job(i, "Remotive", (REAL_NOW - timedelta(hours=6)).isoformat(), "WW", "")
            for i in range(16)])
kept = snap.select_jobs(mixed, max_jobs=1800, max_share=0.5)
by_src = {}
for j in kept:
    by_src[j["source"]] = by_src.get(j["source"], 0) + 1

check("snapshot keeps its size", len(kept) == 1800, f"got {len(kept)}")
check("no source may claim the whole board",
      by_src["Arbeitnow"] / len(kept) < 0.65, f"share {by_src['Arbeitnow']/len(kept):.2f}")
check("dominant source is capped at its ceiling in the fair pass",
      by_src["Arbeitnow"] == 900 + (1800 - 900 - 550 - 96 - 37 - 16),
      f"kept {by_src['Arbeitnow']}")

# Four equally big feeds and too few slots: everyone scales down together instead of
# the first two eating every slot (this is what starved the US sources).
rival = [job(i, s, (REAL_NOW - timedelta(hours=n * 600 + i)).isoformat())
         for n, s in enumerate(("A", "B", "C", "D")) for i in range(600)]
balanced = snap.select_jobs(rival, max_jobs=1200, max_share=0.5)
counts = {}
for j in balanced:
    counts[j["source"]] = counts.get(j["source"], 0) + 1
check("equal sources keep equal shares", sorted(counts.values()) == [300, 300, 300, 300],
      str(counts))
check("The Muse fully preserved (was 96 → 3)", by_src["The Muse"] == 96,
      f"kept {by_src.get('The Muse')}")
check("RemoteOK fully preserved (was 37 → 1)", by_src["RemoteOK"] == 37,
      f"kept {by_src.get('RemoteOK')}")
check("Remotive fully preserved (was 16 → 1)", by_src["Remotive"] == 16,
      f"kept {by_src.get('Remotive')}")
check("output is newest-first",
      all(snap.date_key(kept[i]) >= snap.date_key(kept[i + 1]) for i in range(len(kept) - 1)))
check("undated jobs sort last, not first",
      snap.date_key({"date": ""}) == 0.0
      and snap.select_jobs([job(1, "S", ""), job(2, "S", REAL_NOW.isoformat())],
                           max_jobs=2, max_share=0.5)[0]["id"] == "S-2")
small = snap.select_jobs([job(i, "Tiny", REAL_NOW.isoformat()) for i in range(5)],
                         max_jobs=1800, max_share=0.5)
check("sources smaller than the ceiling are never trimmed", len(small) == 5)

# A 'Z'-suffixed same-instant job must not lose to a '+00:00' one by string order.
tie = snap.select_jobs([job(1, "A", "2026-09-11T10:00:00Z"),
                        job(2, "B", "2026-09-11T10:05:00+00:00")],
                       max_jobs=1, max_share=0.5)
check("newer minute wins regardless of format", tie[0]["id"] == "B-2", f"got {tie}")

# ------------------------------------------------------------------ 3. collapse guard
print("\n[collapse guard]")


def run_build(sources, previous_count):
    """Run build_snapshot.main() against fake fetchers in a temp checkout."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "jobs.json")
        if previous_count:
            with open(out, "w", encoding="utf-8") as f:
                json.dump({"count": previous_count, "jobs": []}, f)
        # Stub the static-page generator: it rewrites index.html/jobs/sitemap.
        fake_gen = ModuleType("generate_static_jobs")
        fake_gen.main = lambda: 0
        sys.modules["generate_static_jobs"] = fake_gen

        saved = {k: getattr(snap, k) for k in
                 ("OUT", "SOURCES", "MIN_JOBS", "ALLOW_SHRINK")}
        snap.OUT = out
        snap.SOURCES = sources
        snap.MIN_JOBS = 250
        snap.ALLOW_SHRINK = False
        try:
            rc = snap.main()
            written = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else None
        finally:
            for k, v in saved.items():
                setattr(snap, k, v)
            del sys.modules["generate_static_jobs"]
        return rc, written


dead = [("Dead", lambda: (_ for _ in ()).throw(RuntimeError("503 Service Unavailable")), "")]
rc, written = run_build(dead, previous_count=1800)
check("total outage fails the run instead of emptying the board", rc == 2, f"rc={rc}")
check("previous snapshot survives on disk",
      written is not None and written.get("count") == 1800, f"got {written and written.get('count')}")

few = [("Tiny", lambda: [job(i, "Tiny", REAL_NOW.isoformat()) for i in range(3)], "")]
rc, written = run_build(few, previous_count=1800)
check("a 99% shrink is refused (0.6 ratio guard)", rc == 2, f"rc={rc}")
check("live file untouched after a refused shrink",
      written is not None and written.get("count") == 1800)

rc, written = run_build([("Tiny", lambda: [
    job(i, "Tiny", (REAL_NOW - timedelta(minutes=i)).isoformat()) for i in range(3)], "")],
    previous_count=0)
check("a fresh bootstrap below the floor still refuses to publish", rc == 2, f"rc={rc}")

saved = {k: getattr(snap, k) for k in ("OUT", "SOURCES", "MIN_JOBS", "ALLOW_SHRINK")}
fake_gen = ModuleType("generate_static_jobs")
fake_gen.main = lambda: 0
sys.modules["generate_static_jobs"] = fake_gen
with tempfile.TemporaryDirectory() as tmp:
    snap.OUT = os.path.join(tmp, "jobs.json")
    snap.SOURCES = [("Tiny", lambda: [
        job(i, "Tiny", (REAL_NOW - timedelta(minutes=i)).isoformat()) for i in range(400)], "")]
    snap.MIN_JOBS = 250
    snap.ALLOW_SHRINK = True
    rc = snap.main()
    payload = json.load(open(snap.OUT, encoding="utf-8"))
for k, v in saved.items():
    setattr(snap, k, v)
del sys.modules["generate_static_jobs"]
check("WW_ALLOW_SHRINK=1 can override the guard", rc == 0, f"rc={rc}")

# ------------------------------------------------------------------ 4. payload contract
print("\n[snapshot payload]")
check("count matches jobs", payload["count"] == len(payload["jobs"]))
check("snapshot_id present (the client diffs this to detect an update)",
      bool(payload.get("snapshot_id")))
check("per_source_kept present", payload.get("per_source_kept") == {"Tiny": 400},
      str(payload.get("per_source_kept")))
check("source_errors present", isinstance(payload.get("source_errors"), list))
check("generated_at is ISO/UTC", payload["generated_at"].endswith("+00:00"))
check("every job has a UTC date",
      all(str(j.get("date", "")).endswith("+00:00") for j in payload["jobs"]))

# The file the live site serves must satisfy the same contract.
live = json.load(open(os.path.join(BASE, "data", "jobs.json"), encoding="utf-8"))
live_dates = [j.get("date", "") for j in live["jobs"]]
check("committed data/jobs.json dates are all parseable",
      all(snap.parse_date_utc(d, now=datetime.now(timezone.utc)) for d in live_dates))
check("committed data/jobs.json is newest-first",
      all(snap.parse_date_utc(live_dates[i], now=REAL_NOW)
          >= snap.parse_date_utc(live_dates[i + 1], now=REAL_NOW)
          for i in range(min(200, len(live_dates) - 1))))

# ------------------------------------------------------------------ 5. asset stamping
print("\n[cache-busting stamp]")
gen = load("generate_static_jobs")
sample = '<link rel="stylesheet" href="css/app.css"><script src="js/app.min.js" defer></script>'
stamped = gen.stamp_assets(sample, "abc123")
check("app.min.js versioned", "js/app.min.js?v=abc123" in stamped, stamped)
check("app.css versioned", "css/app.css?v=abc123" in stamped, stamped)
check("idempotent (no new commit when nothing changed)",
      gen.stamp_assets(stamped, "abc123") == stamped)
re_stamped = gen.stamp_assets(stamped, "def456")
check("version replaced, not appended",
      "js/app.min.js?v=def456" in re_stamped and "?v=abc123" not in re_stamped, re_stamped)
check("empty version leaves the page alone", gen.stamp_assets(sample, "") == sample)
check("unsafe characters stripped",
      "js/app.min.js?v=a-b-c" in gen.stamp_assets("js/app.min.js", "a b/c"))

print()
if failures:
    print(f"{len(failures)} FAILURE(S): " + ", ".join(failures))
    sys.exit(1)
print("all snapshot-update regression tests passed")
