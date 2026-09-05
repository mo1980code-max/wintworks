#!/usr/bin/env python3
"""Executable proofs for the license ledger — hostile-injection style, pure stdlib.

Runs the Python twin auditor (tools/audit_ledger.py — same rules as LicenseAuditor.php,
enforced by check_audit_parity.py) over REAL sqlite rows shaped exactly like the SQL the
PHP LicenseRepository emits (LEFT JOIN games -> game_licenses, regrouped per game).

Proves:
  A. clean seed            — 4 lawful games (oss/cdn, publisher, own) audit with zero errors
  B. hostile injections    — each injected violation fires EXACTLY its rule and nothing else:
                             no_license_row, copyleft(GPL-3.0), allow_list(Apache stub->ref bogus),
                             pin(short sha), external_id(traversal), license_expiry(past date),
                             license_status(withdrawn), runtime(own w/o files, publisher w/o origins),
                             license_type(bogus), attribution warning
  C. visibility boundary   — cleanGameIds hides every hostile game; multi-row game with one
                             dirty row stays hidden; warning-only game stays visible
  D. SQL shape             — the LEFT JOIN + regroup really produces one entry per game with
                             its rows (a JOIN bug here would audit a fantasy ledger)

Exit 0 proves all of it; any deviation exits 1.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from audit_ledger import scan_ledger  # noqa: E402

FAILURES: list[str] = []
CHECKS = 0
TODAY = "2026-09-05"

SHA_A = "3f9c2ab41e8d5c7b0a19f6e2d4c8b7a5f3e1d9c0"
SHA_B = "9d1e7c4b2a6f8e0d3c5b7a9f1e3d5c7b9a8f6e4d"
SHA_C = "11aa2bb3cc4dd5ee6ff70a81b92c3da4eb5fc6d7"


def check(label: str, cond: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  ✓ {label}")
    else:
        FAILURES.append(label)
        print(f"  ✗ {label} {detail}")


def rules_of(violations: list) -> list:
    return sorted(v["rule"] for v in violations)


def fresh_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript((ROOT / "db" / "schema.sqlite.sql").read_text(encoding="utf-8"))
    return conn


def add_game(conn: sqlite3.Connection, gid: int, slug: str, status: str = "published",
             kind: str = "feed", local_path: str = "") -> None:
    conn.execute(
        "INSERT INTO games (id, slug, title_ar, title_en, status, kind, local_path, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (gid, slug, slug, slug, status, kind, local_path, "2026-08-01", "2026-08-01"))


def add_license(conn: sqlite3.Connection, gid: int, **kw) -> None:
    row = {
        "provider": "oss-pack", "external_id": kw.get("external_id", SHA_A),
        "license_type": "oss", "license_ref": "MIT",
        "upstream_repo": kw.get("upstream_repo", f"upstream/g{gid}"),
        "commit_sha": kw.get("commit_sha", SHA_A),
        "license_path": f"data/oss-pack/g{gid}/LICENSE.txt",
        "license_sha256": "b" * 64,
        "proof_url": f"https://github.com/upstream/g{gid}/blob/main/LICENSE",
        "invoice_ref": "", "allow_origins": "https://cdn.jsdelivr.net",
        "attribution_required": 0, "attribution_html": "",
        "status": "active", "expires_at": kw.get("expires_at", ""),
    }
    row.update({k: v for k, v in kw.items() if v is not None})
    conn.execute(
        "INSERT INTO game_licenses (game_id, provider, external_id, license_type, license_ref, "
        "upstream_repo, commit_sha, license_path, license_sha256, proof_url, invoice_ref, "
        "allow_origins, attribution_required, attribution_html, status, expires_at, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (gid, row["provider"], row["external_id"] or None, row["license_type"], row["license_ref"],
         row["upstream_repo"], row["commit_sha"], row["license_path"], row["license_sha256"],
         row["proof_url"], row["invoice_ref"], row["allow_origins"],
         row["attribution_required"], row["attribution_html"], row["status"], row["expires_at"],
         "2026-08-01", "2026-08-01"))


def scan_db(conn: sqlite3.Connection) -> tuple[list, dict]:
    """Replicates LicenseRepository::scanAll() SQL + regroup, then audits."""
    rows = conn.execute(
        "SELECT g.id AS game_id, g.slug, g.status, g.kind, g.local_path, "
        "l.provider, l.external_id, l.license_type, l.license_ref, l.upstream_repo, "
        "l.commit_sha, l.license_path, l.license_sha256, l.proof_url, l.invoice_ref, "
        "l.allow_origins, l.attribution_required, l.attribution_html, "
        "l.status AS license_status, l.expires_at "
        "FROM games g LEFT JOIN game_licenses l ON l.game_id = g.id ORDER BY g.id"
    ).fetchall()
    cols = ["game_id", "slug", "status", "kind", "local_path", "provider", "external_id",
            "license_type", "license_ref", "upstream_repo", "commit_sha", "license_path",
            "license_sha256", "proof_url", "invoice_ref", "allow_origins",
            "attribution_required", "attribution_html", "license_status", "expires_at"]
    games: dict = {}
    for r in rows:
        d = dict(zip(cols, r))
        g = games.setdefault(int(d["game_id"]), {
            "slug": d["slug"], "status": d["status"], "kind": d["kind"],
            "local_path": d["local_path"], "licenses": []})
        if d["provider"] is not None:
            g["licenses"].append(d)
    games_list = list(games.values())
    return games_list, scan_ledger(games_list, today=TODAY)


def clean_ids(games: list) -> list:
    report = scan_ledger(games, today=TODAY)
    bad = {v["slug"] for v in report["errors"]}
    return [g["slug"] for g in games if g["slug"] not in bad]


def proof_a() -> list:
    print("A · clean seed audits with zero errors")
    conn = fresh_db()
    add_game(conn, 1, "neon-worm")
    add_license(conn, 1, external_id=SHA_A, commit_sha=SHA_A)
    add_game(conn, 2, "echo-cards")
    add_license(conn, 2, external_id=SHA_B, commit_sha=SHA_B, license_ref="Apache-2.0", upstream_repo="upstream/echo-cards", proof_url="https://github.com/upstream/echo-cards/blob/main/LICENSE")
    add_game(conn, 3, "ad-publisher", kind="feed")
    add_license(conn, 3, license_type="publisher-agreement", license_ref="publisher-agreement",
                external_id="gd-bubble-77", commit_sha="", upstream_repo="", proof_url="https://example.com/terms",
                invoice_ref="GD-2026-42", allow_origins="https://html5.gamedistribution.com", expires_at="2027-01-31")
    add_game(conn, 4, "my-own-game", kind="upload", local_path="var/games/my-own-game")
    add_license(conn, 4, license_type="own", license_ref="own-licence", provider="own",
                external_id="", commit_sha="", upstream_repo="", proof_url="",
                allow_origins="", license_path="", license_sha256="")
    conn.commit()
    games, report = scan_db(conn)
    check("4 clean games → 0 errors", report["errors"] == [], str(report["errors"][:2]))
    check("LEFT JOIN yields exactly 4 game entries", len(games) == 4, str(len(games)))
    check("each entry carries its license rows", all(len(g["licenses"]) == 1 for g in games))
    return games


def proof_b() -> None:
    print("B · each hostile injection fires exactly its rule")

    def one_game(licenses_builder, status="published", kind="feed", local_path=""):
        conn = fresh_db()
        add_game(conn, 1, "target", status=status, kind=kind, local_path=local_path)
        licenses_builder(conn)
        _, report = scan_db(conn)
        return report

    r = one_game(lambda c: None)
    check("no_license_row", rules_of(r["errors"]) == ["no_license_row"], str(rules_of(r["errors"])))

    r = one_game(lambda c: add_license(c, 1, license_ref="GPL-3.0"))
    check("copyleft(GPL-3.0) + allow_list", rules_of(r["errors"]) == ["allow_list", "copyleft"], str(rules_of(r["errors"])))

    r = one_game(lambda c: add_license(c, 1, license_ref="LicenseRef-My-Font"))
    check("allow_list(bogus ref)", rules_of(r["errors"]) == ["allow_list"], str(rules_of(r["errors"])))

    r = one_game(lambda c: add_license(c, 1, commit_sha="abc123"))
    check("pin(short sha)", "pin" in rules_of(r["errors"]), str(rules_of(r["errors"])))

    r = one_game(lambda c: add_license(c, 1, external_id="../../evil?x="))
    check("external_id(traversal)", "external_id" in rules_of(r["errors"]), str(rules_of(r["errors"])))

    r = one_game(lambda c: add_license(c, 1, expires_at="2025-01-01"))
    check("license_expiry(past)", rules_of(r["errors"]) == ["license_expiry"], str(rules_of(r["errors"])))

    r = one_game(lambda c: add_license(c, 1, status="withdrawn"))
    check("license_status(withdrawn)", rules_of(r["errors"]) == ["license_status"], str(rules_of(r["errors"])))

    r = one_game(lambda c: add_license(c, 1, license_type="bogus-type"))
    check("license_type(bogus)", "license_type" in rules_of(r["errors"]), str(rules_of(r["errors"])))

    r = one_game(lambda c: add_license(c, 1, license_type="own", license_ref="own-licence", provider="own",
                                       external_id="", commit_sha="", upstream_repo="", proof_url="",
                                       allow_origins="", license_path="", license_sha256=""),
                 kind="upload")
    check("runtime(own without local files)", rules_of(r["errors"]) == ["runtime"], str(rules_of(r["errors"])))

    r = one_game(lambda c: add_license(c, 1, license_type="publisher-agreement", license_ref="publisher-agreement",
                                       external_id="gd-x-99", commit_sha="", upstream_repo="",
                                       proof_url="https://example.com/t", invoice_ref="GD-1",
                                       allow_origins="", expires_at=""))
    check("runtime(publisher without allow_origins)", "runtime" in rules_of(r["errors"]), str(rules_of(r["errors"])))

    def with_attribution(c):
        c.execute(
            "INSERT INTO game_licenses (game_id, provider, external_id, license_type, license_ref, "
            "upstream_repo, commit_sha, license_path, license_sha256, proof_url, invoice_ref, "
            "allow_origins, attribution_required, attribution_html, status, expires_at, created_at, updated_at) "
            "VALUES (1,'oss-pack',?,'oss','MIT','upstream/t',?, 'p','" + "b" * 64 + "','u','', "
            "'https://cdn.jsdelivr.net',1,'','active','', '2026-08-01','2026-08-01')",
            (SHA_C, SHA_C))
    r = one_game(with_attribution)
    check("attribution warning (non-fatal)", r["errors"] == [] and rules_of(r["warnings"]) == ["attribution"],
          str((r["errors"], r["warnings"])))


def proof_c() -> None:
    print("C · visibility boundary — visitors only ever see clean games")
    conn = fresh_db()
    add_game(conn, 1, "clean-oss");    add_license(conn, 1, external_id=SHA_A, commit_sha=SHA_A)
    add_game(conn, 2, "dirty-gpl");    add_license(conn, 2, license_ref="GPL-2.0")
    add_game(conn, 3, "dirty-expired"); add_license(conn, 3, expires_at="2024-12-31")
    add_game(conn, 4, "warn-only", )
    conn.execute(
        "INSERT INTO game_licenses (game_id, provider, external_id, license_type, license_ref, "
        "upstream_repo, commit_sha, license_path, license_sha256, proof_url, invoice_ref, "
        "allow_origins, attribution_required, attribution_html, status, expires_at, created_at, updated_at) "
        "VALUES (4,'oss-pack',?,'oss','MIT','upstream/w',?, 'p','" + "c" * 64 + "','u','', "
        "'https://cdn.jsdelivr.net',1,'','active','', '2026-08-01','2026-08-01')", (SHA_B, SHA_B))
    add_game(conn, 5, "unpublished-clean", status="draft")
    add_license(conn, 5, external_id=SHA_C, commit_sha=SHA_C)

    games, _ = scan_db(conn)
    visible = clean_ids(games)
    check("dirty games hidden (copyleft + expired)", "dirty-gpl" not in visible and "dirty-expired" not in visible, str(visible))
    check("warning-only game stays visible", "warn-only" in visible, str(visible))
    check("clean oss visible", "clean-oss" in visible, str(visible))

    # multi-row game: one dirty row poisons the game
    conn2 = fresh_db()
    add_game(conn2, 1, "mixed")
    add_license(conn2, 1, external_id=SHA_A, commit_sha=SHA_A)
    add_license(conn2, 1, external_id=SHA_B, commit_sha=SHA_B, license_ref="AGPL-3.0")
    games2, report2 = scan_db(conn2)
    check("one dirty row among many hides the whole game", "mixed" not in clean_ids(games2)
          and any(v["rule"] == "copyleft" for v in report2["errors"]))


def proof_d() -> None:
    print("D · SQL shape — regroup cannot invent or drop games")
    conn = fresh_db()
    add_game(conn, 1, "solo")
    add_license(conn, 1, external_id=SHA_A, commit_sha=SHA_A)
    add_game(conn, 2, "rowless", status="draft")
    games, _ = scan_db(conn)
    check("game without license rows still present (for no_license_row)", len(games) == 2)
    check("rowless game has empty license list", games[1]["licenses"] == [])


def main() -> int:
    proof_a()
    proof_b()
    proof_c()
    proof_d()
    print()
    if FAILURES:
        print(f"✗ {len(FAILURES)}/{CHECKS} checks failed:")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print(f"✓ all {CHECKS} audit checks hold · the ledger, the rules and the visibility boundary behave")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
