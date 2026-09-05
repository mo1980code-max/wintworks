#!/usr/bin/env python3
"""Static-side license auditor — the Python twin of src/License/LicenseAuditor.php.

Two engines enforce the SAME shared rules so the dynamic PHP site and the static
export can never disagree about what may be visible:

    python3 tools/audit_ledger.py data/ledger.example.json            # errors fail, warnings pass
    python3 tools/audit_ledger.py data/ledger.json --strict           # warnings fail too

SHARED_RULES / ALLOWED_REFS / FORBIDDEN_PREFIXES below MUST stay byte-identical to the
constants in LicenseAuditor.php — tools/check_audit_parity.py enforces that in CI.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ALLOWED_REFS = [
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD",
    "Unlicense", "Zlib", "OFL-1.1", "CC0-1.0", "publisher-agreement", "own-licence",
]
FORBIDDEN_PREFIXES = ["GPL", "AGPL", "LGPL", "CC-BY-NC", "BSD-4", "NPOSL", "SSPL"]
LICENSE_TYPES = ["oss", "publisher-agreement", "own"]

# MUST stay identical to LicenseAuditor::SHARED_RULES
SHARED_RULES = [
    "slug", "no_license_row", "license_type", "license_status", "license_expiry",
    "copyleft", "allow_list", "proof_upstream", "pin", "external_id",
    "runtime", "attribution",
]
# rules only the static exporter can know
STATIC_ONLY_RULES = ["provider_unknown", "expiry_format"]

KNOWN_PROVIDERS = {"oss-pack", "own", "gamedistribution", "gamemonetize", "gameflare", "gamepix"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,78}[a-z0-9]$")
EXTERNAL_RE = re.compile(r"^[A-Za-z0-9_-]{4,64}$")
PIN_RE = re.compile(r"^[0-9a-f]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def violation(rule: str, slug: str, message: str) -> dict:
    return {"rule": rule, "slug": slug, "message": message}


def scan_license(slug: str, game: dict, lic: dict, today: str) -> tuple[list, list]:
    errors: list = []
    warnings: list = []
    ltype = str(lic.get("license_type", ""))
    ref = str(lic.get("license_ref", ""))
    status = str(lic.get("license_status", ""))
    provider = str(lic.get("provider", "own"))
    external = str(lic.get("external_id", "") or "")
    sha = str(lic.get("commit_sha", "") or "")

    # rule: license_type
    if ltype not in LICENSE_TYPES:
        errors.append(violation("license_type", slug, f"license type '{ltype}' is not one of: " + ", ".join(LICENSE_TYPES)))
    # rule: license_status
    if status != "active":
        errors.append(violation("license_status", slug, f"license status '{status}' is not active"))
    # rules: copyleft + allow_list
    for prefix in FORBIDDEN_PREFIXES:
        if ref and ref.upper().startswith(prefix.upper()):
            errors.append(violation("copyleft", slug, f"'{ref}' is copyleft/non-commercial — banned from this product"))
            break
    if ref not in ALLOWED_REFS:
        errors.append(violation("allow_list", slug, f"license ref '{ref}' is not in the allow-list"))

    if ltype == "oss":
        # rule: proof_upstream
        if not str(lic.get("upstream_repo", "")) or not str(lic.get("proof_url", "")):
            errors.append(violation("proof_upstream", slug, "oss license needs upstream_repo and proof_url"))
        # rule: pin
        if not PIN_RE.match(sha):
            errors.append(violation("pin", slug, f"commit pin '{sha[:12]}' is not a full 40-hex sha"))
        # rule: license_expiry
        expires = str(lic.get("expires_at", "") or "")
        if expires and expires < today:
            errors.append(violation("license_expiry", slug, f"license expired {expires}"))

    # rule: external_id
    if provider != "own" and not EXTERNAL_RE.match(external):
        errors.append(violation("external_id", slug, f"external_id '{external}' must match ^[A-Za-z0-9_-]{{4,64}}$"))

    # rule: runtime — internal consistency
    if ltype == "own" and not str(lic.get("local_path", "") or game.get("local_path", "")).strip():
        errors.append(violation("runtime", slug, "own game has no local_path — nothing lawful to serve"))
    if ltype == "publisher-agreement" and not str(lic.get("allow_origins", "")).strip():
        errors.append(violation("runtime", slug, "publisher-agreement rows must record allow_origins (the embed hosts the contract covers)"))

    # rule: attribution
    if lic.get("attribution_required") and not str(lic.get("attribution_html", "") or "").strip():
        warnings.append(violation("attribution", slug, "attribution_required is set but attribution_html is empty"))

    # static-only: the exporter knows the provider registry
    if provider not in KNOWN_PROVIDERS:
        errors.append(violation("provider_unknown", slug, f"provider '{provider}' is not in the static provider registry"))
    expires_fmt = str(lic.get("expires_at", "") or "")
    if expires_fmt and not DATE_RE.match(expires_fmt):
        errors.append(violation("expiry_format", slug, f"expires_at '{expires_fmt}' must be YYYY-MM-DD"))

    return errors, warnings


def scan_ledger(games: list, today: str | None = None) -> dict:
    today = today or date.today().isoformat()
    errors: list = []
    warnings: list = []
    for game in games:
        slug = str(game.get("slug", ""))
        # rule: slug
        if not SLUG_RE.match(slug):
            errors.append(violation("slug", slug or "(empty)", "game slug missing or malformed"))
        licenses = list(game.get("licenses") or [])
        # rule: no_license_row
        if not licenses and str(game.get("status", "")) == "published":
            errors.append(violation("no_license_row", slug, "published game has no license row — hidden from visitors"))
        for lic in licenses:
            e, w = scan_license(slug, game, lic, today)
            errors.extend(e)
            warnings.extend(w)
    return {"errors": errors, "warnings": warnings, "games": len(games)}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args:
        print(__doc__)
        return 2
    path = Path(args[0])
    if not path.is_file():
        print(f"ledger not found: {path}")
        return 2
    data = json.loads(path.read_text(encoding="utf-8"))
    games = data["games"] if isinstance(data, dict) else data
    report = scan_ledger(games)

    for v in report["errors"]:
        print(f"ERROR   {v['rule']:<14} {v['slug']} · {v['message']}")
    for v in report["warnings"]:
        print(f"WARNING {v['rule']:<14} {v['slug']} · {v['message']}")
    strict = "--strict" in flags
    print(f"audited {report['games']} game(s): {len(report['errors'])} error(s), "
          f"{len(report['warnings'])} warning(s){' · strict' if strict else ''}")
    if report["errors"] or (strict and report["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
