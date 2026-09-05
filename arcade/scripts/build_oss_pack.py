#!/usr/bin/env python3
"""Builds the sellable OSS game pack: adapters + metadata + license proof, NEVER game bytes.

Pipeline (real GitHub API, rate-limit aware):
    search (license-filtered) -> per candidate:
        pin commit (40-hex) -> playable gate on index.html @pin
        -> capture LICENSE text @pin (bytes counted, sha noted)
        -> write data/oss-pack/<slug>/{LICENSE.txt,LICENSE.md,SOURCES.md}
    -> data/oss-pack.json manifest

The package ships only: embed URL template (cdn @pin), provenance docs, license text.
A buyer's build reproduces the game from upstream at the pinned commit; we host nothing
unless they choose the vendored mode later.

    python3 scripts/build_oss_pack.py --target 3 --max-api-calls 16   # small live run
    python3 scripts/build_oss_pack.py --verify                        # manifest vs disk + policy
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PACK_DIR = DATA / "oss-pack"
MANIFEST = DATA / "oss-pack.json"

ALLOWED_REFS = [
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD",
    "Unlicense", "Zlib", "OFL-1.1", "CC0-1.0",
]
GITHUB_TOKEN = ""  # optional: export GITHUB_TOKEN to lift rate limits

SEARCH_QUERY = ("q=html5+game+in:name,description+license:mit,apache-2.0"
                "+pushed:>2024-06-01&sort=stars&order=desc&per_page=30")
MIN_STARS = 5

GAME_SIGNAL = re.compile(r"<canvas|createjs|phaser|babylon|three\.js|pixi|<game|godot|construct", re.I)
BAD_ENTRY = re.compile(r"coming\s*soon|under\s*construction|placeholder", re.I)

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"


def call_count() -> dict:
    return {"api": 0, "raw": 0}


def http_get(url: str, counter: dict, kind: str = "api", accept: str = "application/vnd.github+json") -> tuple[int, str]:
    counter[kind] += 1
    req = urllib.request.Request(url, headers={
        "Accept": accept,
        "User-Agent": "nawras-arcade-pack-builder/0.3",
        **({"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.status, res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # network conditions are data, not crashes
        print(f"    ! {kind} {url[:80]} → {e}")
        return 0, ""


def api_json(url: str, counter: dict):
    status, body = http_get(url, counter, "api")
    if status != 200 or not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def guard_rate(counter: dict) -> None:
    if counter["api"] % 8 == 0:  # unauthenticated search/core budget — be a polite citizen
        time.sleep(2)


def playable(html: str) -> bool:
    if not html:
        return False
    if BAD_ENTRY.search(html):
        return False
    return bool(GAME_SIGNAL.search(html))


def build_row(repo: dict, counter: dict) -> dict | None:
    full = repo["full_name"]
    branch = repo.get("default_branch", "main")

    head = api_json(f"{API}/repos/{full}/commits/{branch}", counter)
    guard_rate(counter)
    if not head or "sha" not in head:
        print(f"    · {full}: no head commit, skipped")
        return None
    sha = head["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return None

    idx = api_json(f"{API}/repos/{full}/contents/index.html?ref={sha}", counter)
    guard_rate(counter)
    html = base64.b64decode(idx["content"]).decode("utf-8", "replace") if idx and idx.get("content") else ""
    if not playable(html):
        print(f"    · {full}: index.html not playable, skipped")
        return None

    lic = api_json(f"{API}/repos/{full}/license?ref={sha}", counter)
    guard_rate(counter)
    if not lic or "license" not in lic or not lic.get("content"):
        print(f"    · {full}: no detectable license, skipped")
        return None
    spdx = (lic.get("license") or {}).get("spdx_id", "")
    if spdx in ("NOASSERTION", "Other", ""):
        print(f"    · {full}: spdx '{spdx}' not machine-checkable, skipped")
        return None

    # the license endpoint already carries the text (base64) AT the pinned ref — no raw host needed
    text = base64.b64decode(lic["content"]).decode("utf-8", "replace")
    if len(text) < 50:
        print(f"    · {full}: license text empty at pin, skipped")
        return None

    slug = re.sub(r"[^a-z0-9-]", "-", repo["name"].lower()).strip("-")[:60].strip("-")
    if len(slug) < 3:
        return None

    out = PACK_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "LICENSE.txt").write_text(text, encoding="utf-8")
    (out / "LICENSE.md").write_text(
        f"# {repo['name']}\n\n- upstream: https://github.com/{full}\n"
        f"- pinned commit: `{sha}`\n- license: **{spdx}**\n"
        f"- captured: {date.today().isoformat()} by nawras-arcade pack builder\n",
        encoding="utf-8")
    (out / "SOURCES.md").write_text(
        f"# Sources — {repo['name']}\n\n"
        f"Game code ships from upstream at the pinned commit; this package stores provenance only.\n\n"
        f"| field | value |\n|---|---|\n"
        f"| repo | https://github.com/{full} |\n"
        f"| commit | `{sha}` |\n"
        f"| entry | index.html |\n"
        f"| license | {spdx} |\n"
        f"| stars | {repo.get('stargazers_count', 0)} |\n"
        f"| cdn embed | https://cdn.jsdelivr.net/gh/{full}@{sha}/index.html |\n",
        encoding="utf-8")

    return {
        "slug": slug,
        "repo": full,
        "url": f"https://github.com/{full}",
        "homepage": repo.get("homepage") or "",
        "upstream_name": repo["name"],
        "stars": int(repo.get("stargazers_count", 0)),
        "description": (repo.get("description") or "")[:300],
        "default_branch": branch,
        "commit_sha": sha,
        "license": {
            "spdx": spdx,
            "path": str((out / "LICENSE.txt").relative_to(ROOT)),
            "text_len": len(text),
            "text_bytes": len(text.encode("utf-8")),
        },
        "entry": "index.html",
        "static_ready": True,
        "captured_at": date.today().isoformat(),
    }


def cmd_build(target: int, max_api: int) -> int:
    counter = {"api": 0, "raw": 0}
    print(f"building oss pack · target {target} · api-call budget {max_api}")
    status, body = http_get(f"{API}/search/repositories?{SEARCH_QUERY}", counter, "api")
    if status != 200:
        print(f"✗ search failed (http {status}) — rate-limited? export GITHUB_TOKEN and retry")
        return 2
    items = (json.loads(body)).get("items", [])
    rows: list[dict] = []
    existing = {r["slug"] for r in (json.loads(MANIFEST.read_text())["games"] if MANIFEST.is_file() else [])}
    for repo in items:
        if len(rows) >= target or counter["api"] >= max_api:
            break
        if repo.get("stargazers_count", 0) < MIN_STARS:
            continue
        slug = re.sub(r"[^a-z0-9-]", "-", repo["name"].lower()).strip("-")
        if slug in existing:
            continue
        print(f"  · candidate {repo['full_name']} (★{repo.get('stargazers_count', 0)})")
        row = build_row(repo, counter)
        if row:
            rows.append(row)
            existing.add(row["slug"])
            print(f"    ✓ pinned {row['commit_sha'][:10]} · {row['license']['spdx']} · "
                  f"{row['license']['text_bytes']}B license")

    if MANIFEST.is_file():
        old = json.loads(MANIFEST.read_text())
        merged = {r["slug"]: r for r in old["games"]}
        merged.update({r["slug"]: r for r in rows})
        rows = sorted(merged.values(), key=lambda r: r["slug"])
    MANIFEST.write_text(json.dumps({"_note": "OSS pack manifest — license text captured at pinned commit; "
                                    "package ships provenance, never game bytes", "games": rows},
                                   ensure_ascii=False, indent=1) + "\n")
    print(f"✓ manifest: {len(rows)} entr(y/ies) · api={counter['api']} raw={counter['raw']} calls")
    return 0 if rows or MANIFEST.is_file() else 2


def cmd_verify() -> int:
    if not MANIFEST.is_file():
        print("✗ no manifest")
        return 2
    doc = json.loads(MANIFEST.read_text())
    problems = []
    for row in doc["games"]:
        slug, lic = row["slug"], row["license"]
        p = ROOT / lic["path"]
        if not p.is_file():
            problems.append(f"{slug}: license file missing")
            continue
        raw = p.read_bytes()
        if len(raw) != lic["text_bytes"]:
            problems.append(f"{slug}: license bytes drifted on disk ({len(raw)} ≠ {lic['text_bytes']})")
        if len(raw.decode('utf-8', 'replace')) != lic["text_len"]:
            problems.append(f"{slug}: license chars drifted on disk")
        if not re.fullmatch(r"[0-9a-f]{40}", row["commit_sha"]):
            problems.append(f"{slug}: pin is not 40-hex")
        if lic["spdx"] not in ALLOWED_REFS:
            problems.append(f"{slug}: spdx '{lic['spdx']}' outside policy")
        if not (PACK_DIR / slug / "SOURCES.md").is_file():
            problems.append(f"{slug}: SOURCES.md missing")
    if problems:
        print("✗ pack verification failed:")
        for q in problems:
            print("   -", q)
        return 1
    print(f"✓ pack verified on disk: {len(doc['games'])} entries · pins 40-hex · licenses byte-intact · policy clean")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=3)
    ap.add_argument("--max-api-calls", type=int, default=16)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    global GITHUB_TOKEN
    import os
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
    return cmd_verify() if args.verify else cmd_build(args.target, args.max_api_calls)


if __name__ == "__main__":
    raise SystemExit(main())
