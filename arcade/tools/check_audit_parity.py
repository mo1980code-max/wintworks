#!/usr/bin/env python3
"""Parity gate: the PHP auditor and the Python twin must enforce the SAME shared rules
and the SAME allow/forbid lists. Reads the constants out of both source files and
compares them literally — if an engine gains or loses a rule, the build fails here
instead of diverging silently in production.

Non-vacuity: proved in-session by appending a fake rule to one side and watching exit 1.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHP = ROOT / "src" / "License" / "LicenseAuditor.php"
PY = ROOT / "tools" / "audit_ledger.py"

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"  {'✓' if cond else '✗'} {label}{'' if cond else ' — ' + detail}")
    if not cond:
        FAILURES.append(label)


def php_const_array(source: str, const: str) -> list[str]:
    m = re.search(r"const\s+" + const + r"\s*=\s*\[(.*?)\];", source, re.S)
    if not m:
        raise SystemExit(f"PHP const {const} not found")
    return re.findall(r"'([^']+)'", m.group(1))


def py_list(source: str, name: str) -> list[str]:
    m = re.search(name + r"\s*=\s*[\[\{](.*?)\]", source, re.S)
    if not m:
        raise SystemExit(f"Python list {name} not found")
    return re.findall(r'"([^"]+)"', m.group(1))


def php_list_by_name(source: str) -> dict:
    """Parses the shared/php-only rule lists from the docblock-style constants."""
    shared = php_const_array(source, "SHARED_RULES")
    php_only = php_const_array(source, "PHP_ONLY_RULES")
    return {"shared": shared, "php_only": php_only}


def main() -> int:
    php_src = PHP.read_text(encoding="utf-8")
    py_src = PY.read_text(encoding="utf-8")

    php = php_list_by_name(php_src)
    py_shared = py_list(py_src, "SHARED_RULES")
    py_static_only = py_list(py_src, "STATIC_ONLY_RULES")

    print("check_audit_parity · one IP contract, two engines\n")

    check("shared rules identical (order too)", php["shared"] == py_shared,
          f"php={php['shared']} py={py_shared}")
    check("shared rules non-empty and deduped",
          len(php["shared"]) >= 8 and len(set(php["shared"])) == len(php["shared"]))
    check("php-only rules present", len(php["php_only"]) == 4, str(php["php_only"]))
    check("static-only rules present", len(py_static_only) == 2, str(py_static_only))
    overlap = set(php["php_only"]) & set(py_static_only)
    check("no rule belongs to both exclusive sets", not overlap, str(overlap))
    check("every exclusive rule differs from shared",
          not (set(php["php_only"]) & set(php["shared"])) and not (set(py_static_only) & set(py_shared)))

    check("ALLOWED_REFS identical", php_const_array(php_src, "ALLOWED_REFS") == py_list(py_src, "ALLOWED_REFS"))
    check("FORBIDDEN_PREFIXES identical",
          php_const_array(php_src, "FORBIDDEN_PREFIXES") == py_list(py_src, "FORBIDDEN_PREFIXES"))

    # the example ledger must be clean under the shared contract (warnings ok)
    import json
    import subprocess
    example = ROOT / "data" / "ledger.example.json"
    if example.is_file():
        r = subprocess.run([sys.executable, str(PY), str(example)], capture_output=True, text=True)
        check("ledger.example.json passes the audit", r.returncode == 0, r.stdout[-200:])

    print()
    if FAILURES:
        print(f"✗ {len(FAILURES)} parity failure(s)")
        return 1
    print("✓ engines agree: rules, allow-list and forbidden list are one contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
