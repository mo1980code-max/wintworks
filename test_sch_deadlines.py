#!/usr/bin/env python3
"""
Regression test: scholarship seed deadlines must always be in the future.

Bug (fixed 2026-08-29): scripts/fetch_scholarships.py generated seed deadlines
with `now.replace(day=min(now.day+days, 28))`, which
  • could never cross a month boundary,
  • clamped every deadline to day 28 of the *current* month.
Snapshots built on the 29th/30th/31st therefore contained only PAST deadlines,
the client-side isExpired() filter hid every scholarship, and the grants
section of the site went empty at every month end.

This test simulates snapshot generation on month-end days (incl. short
February) and asserts all deadlines lie strictly in the future.
"""

import importlib.util
import os
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(BASE, "scripts", "fetch_scholarships.py")

spec = importlib.util.spec_from_file_location("fetch_scholarships", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

REAL_NOW = datetime.now(timezone.utc)


def seed_with_fake_now(fake_now):
    """Call seed_scholarships() with datetime.now() monkeypatched to fake_now."""
    class FakeDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fake_now if tz else fake_now.replace(tzinfo=None)

    original = mod.datetime
    mod.datetime = FakeDateTime
    try:
        return mod.seed_scholarships()
    finally:
        mod.datetime = original


def check(fake_now, label):
    rows = seed_with_fake_now(fake_now)
    assert rows, f"{label}: seed returned no scholarships"
    deadlines = []
    for r in rows:
        d = r.get("deadline", "")
        assert d, f"{label}: missing deadline on {r.get('title')!r}"
        dt = datetime.fromisoformat(d)
        assert dt.tzinfo, f"{label}: deadline {d} is not timezone-aware"
        assert dt > fake_now, (
            f"{label}: deadline {d} for {r.get('title')!r} is in the past "
            f"(fake now={fake_now.isoformat()})"
        )
        deadlines.append(dt)
    # Deadlines must be spread out, not collapsed onto one day.
    unique_days = {dt.date() for dt in deadlines}
    assert len(unique_days) >= 10, (
        f"{label}: deadlines collapsed onto {len(unique_days)} day(s) — "
        "replace(day=...) regression?"
    )
    print(f"  {label}: {len(rows)} scholarships, "
          f"deadlines span {min(deadlines).date()} → {max(deadlines).date()}  ✔")


# Real generation (no patching) must also be entirely future-dated.
check(REAL_NOW, "real now")

# Month-end days — the exact scenario that used to wipe the grants section.
check(datetime(2026, 8, 29, 6, 15, tzinfo=timezone.utc), "Aug 29 (31-day month)")
check(datetime(2026, 8, 30, 6, 15, tzinfo=timezone.utc), "Aug 30")
check(datetime(2026, 8, 31, 23, 59, tzinfo=timezone.utc), "Aug 31 23:59")
check(datetime(2027, 1, 31, 6, 15, tzinfo=timezone.utc), "Jan 31")
check(datetime(2026, 2, 27, 6, 15, tzinfo=timezone.utc), "Feb 27 (short month)")
check(datetime(2028, 2, 29, 6, 15, tzinfo=timezone.utc), "Feb 29 (leap year)")
check(datetime(2026, 12, 31, 6, 15, tzinfo=timezone.utc), "Dec 31 (year end)")


# ---- guard: an all-expired snapshot must abort the build --------------
import tempfile

def run_main_with_seed(seed_rows):
    """Run fetch_scholarships.main() against a temp output file."""
    mod.fetch_scholarshipapi = lambda key: []
    mod.fetch_scholarships_com = lambda: []
    mod.WP_SOURCES = []          # no network in tests
    mod.seed_scholarships = lambda: list(seed_rows)
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    mod.OUT = tmp.name
    try:
        mod.main()
        code = 0
    except SystemExit as e:
        code = e.code or 1
    with open(tmp.name) as f:
        content = f.read()
    os.unlink(tmp.name)
    return code, content

past = REAL_NOW - timedelta(days=3)
bad_rows = [{
    "id": "bad-1", "title": "Expired Grant", "provider": "X",
    "location": "Worldwide", "region": "WW", "country": "",
    "remote": False, "funding": "Fully Funded", "amount": 1000,
    "amount_str": "$1,000", "deadline": past.isoformat(), "level": "",
    "description": "", "tags": [], "url": "https://example.com",
    "source": "test", "date": REAL_NOW.isoformat(),
}]
code, content = run_main_with_seed(bad_rows)
assert code != 0, "guard did not abort on an all-expired snapshot"
assert content.strip() == "", "guard aborted but still wrote a snapshot"
print("  all-expired snapshot → build aborted, file untouched  ✔")

future = REAL_NOW + timedelta(days=20)
good_rows = [dict(bad_rows[0], id="good-1", title="Open Grant",
                  deadline=future.isoformat())]
code, content = run_main_with_seed(good_rows)
assert code == 0, "guard aborted on a healthy snapshot"
assert '"Open Grant"' in content, "healthy snapshot was not written"
print("  healthy snapshot → written normally  ✔")

print("\nAll deadline regression checks passed.")
