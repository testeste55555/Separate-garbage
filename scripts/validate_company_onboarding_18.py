from __future__ import annotations
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from validate_company_municipality_mapping import validate

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "data/app/company_municipality_mapping.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BASELINE_SHA256 = "02180886ff89be6faee73c54e2902e0e8d7e99f5dc5f84ce745a7eddf78caa4e"
READY_STATUSES = {"APP_READY", "LESSON_READY_10"}


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

    with SCOPE.open(encoding="utf-8-sig", newline="") as handle:
        ready = {r["municipality_id"] for r in csv.DictReader(handle) if r["scoring_status"] in READY_STATUSES}

    counts = Counter(r["active"] for r in added)
    actual_active = counts.get("TRUE", 0)
    actual_pending = counts.get("FALSE", 0)
    expected_active = sum(r["municipality_id"] in ready for r in added)
    expected_pending = len(added) - expected_active
    assert not (set(counts) - {"TRUE", "FALSE"}), f"unexpected active values: {counts}"
    assert (actual_active, actual_pending) == (expected_active, expected_pending), (
        f"new company readiness count mismatch: active={actual_active}/{expected_active} "
        f"pending={actual_pending}/{expected_pending}"
    )
    assert all((r["active"] == "TRUE") == (r["municipality_id"] in ready) for r in added)
    assert all(r["mapping_status"] == "CONFIRMED" for r in added)
    assert all(r["lesson_variant_group_id"] == "LV-M098-01" for r in added if r["municipality_id"] == "M098")
    assert all(not r["lesson_variant_group_id"] for r in added if r["municipality_id"] == "M099")
    assert not validate(), "company mapping validation failed"
    print(
        "COMPANY_ONBOARDING_18_VALIDATION_PASSED "
        f"companies=29 sites=46 added=18/35 active={actual_active} pending={actual_pending}"
    )


if __name__ == "__main__":
    check()
