#!/usr/bin/env python3
"""One-time, branch-scoped repair. Removed after the verified commit."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "288c6dffac803e1d11eab43ea3ac3e34aad1421b"


def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise AssertionError(f"Expected exactly one anchor in {path}: {old}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main():
    mapping = ROOT / "data/app/company_municipality_mapping.csv"
    raw = mapping.read_bytes()
    if not raw.startswith(b"\xef\xbb\xbf"):
        mapping.write_bytes(b"\xef\xbb\xbf" + raw)

    validator = ROOT / "scripts/validate_app_readiness_m098.py"
    replace_once(
        validator,
        'if {r.get("company_id") for r in companies} != EXPECTED_COMPANIES or len(companies) != 3:',
        'if not EXPECTED_COMPANIES.issubset({r.get("company_id") for r in companies}) or len({r.get("site_id") for r in companies}) != len(companies):',
    )
    replace_once(
        validator,
        "M098 must keep exactly the three confirmed company mappings",
        "M098 must preserve the original three company mappings and unique site IDs",
    )

    redteam = ROOT / "scripts/red_team_app_readiness_m098.py"
    addition = '''    def added_company_wrong_variant(d):
        for r in d["company"]:
            if r.get("company_id") == "C024" and r.get("municipality_id") == gate.MID:
                r["lesson_variant_group_id"] = "LV-M099-01"
    tests.append(("new M098 company routed to wrong variant", added_company_wrong_variant))

'''
    replace_once(redteam, "    for label, mutate in tests:\n", addition + "    for label, mutate in tests:\n")

    test = ROOT / "scripts/validate_company_onboarding_18.py"
    test.write_text('''from __future__ import annotations
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from validate_company_municipality_mapping import validate

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "data/app/company_municipality_mapping.csv"
BASELINE_SHA256 = "02180886ff89be6faee73c54e2902e0e8d7e99f5dc5f84ce745a7eddf78caa4e"
APP_READY = {"M009", "M020", "M094", "M095", "M098", "M099", "M104", "M105"}


def check():
    with MAPPING.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    legacy = [r for r in rows if r["company_id"] in {f"C{i:03d}" for i in range(1, 12)}]
    digest = hashlib.sha256(json.dumps(legacy, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    assert digest == BASELINE_SHA256, "existing 11 company records changed"
    assert len(rows) == 46
    assert len({r["site_id"] for r in rows}) == 46
    assert {r["company_id"] for r in rows} == {f"C{i:03d}" for i in range(1, 30)}
    added = [r for r in rows if int(r["company_id"][1:]) >= 12]
    assert len(added) == 35
    assert len({r["company_id"] for r in added}) == 18
    assert Counter(r["active"] for r in added) == {"TRUE": 15, "FALSE": 20}
    assert all((r["active"] == "TRUE") == (r["municipality_id"] in APP_READY) for r in added)
    assert all(r["mapping_status"] == "CONFIRMED" for r in added)
    assert all(r["lesson_variant_group_id"] == "LV-M098-01" for r in added if r["municipality_id"] == "M098")
    assert all(not r["lesson_variant_group_id"] for r in added if r["municipality_id"] == "M099")
    assert not validate(), "company mapping validation failed"
    print("COMPANY_ONBOARDING_18_VALIDATION_PASSED companies=29 sites=46 added=18/35 active=15 pending=20")


if __name__ == "__main__":
    check()
''', encoding="utf-8")

    # Restore the existing workflow from the exact base, adding only the new regression.
    workflow = ROOT / ".github/workflows/company-selector.yml"
    original = subprocess.check_output(
        ["git", "show", f"{BASE}:.github/workflows/company-selector.yml"],
        cwd=ROOT, text=True,
    )
    original = original.replace(
        '      - "scripts/validate_company_municipality_mapping.py"',
        '      - "scripts/validate_company_municipality_mapping.py"\n      - "scripts/validate_company_onboarding_18.py"',
    )
    anchor = '      - name: Mutation RED TEAM\n'
    assert original.count(anchor) == 1
    original = original.replace(anchor, '      - name: Validate 18-company onboarding\n        run: python scripts/validate_company_onboarding_18.py\n' + anchor)
    workflow.write_text(original, encoding="utf-8")

    # The final branch contains only the permanent fixes, not delivery helpers.
    (ROOT / "scripts/_repair_company_onboarding_once.py").unlink()
    for path in [validator, redteam, test]:
        ast.parse(path.read_text(encoding="utf-8"))
    print("COMPATIBILITY_REPAIR_PREPARED")


if __name__ == "__main__":
    main()
