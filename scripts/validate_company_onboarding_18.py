from __future__ import annotations
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
