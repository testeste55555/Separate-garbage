#!/usr/bin/env python3
"""Batch 03 specific adversarial checks.

This report intentionally expects Yura Town (M028) to remain QA_REQUIRED until a
complete current official category index is obtained. The point is to prevent the
pipeline from converting an evidence gap into a false QA pass.
"""

from __future__ import annotations

from collections import Counter

from schema_v12 import RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS = {"M023", "M024", "M025", "M026", "M027", "M028", "M029", "M031", "M032", "M033"}
REVIEWED = TARGETS - {"M028"}


def paths():
    base = RESEARCH / "batches" / "batch_03"
    p = "batch_03_"
    return {
        "municipality_path": base / f"{p}municipalities.csv",
        "category_path": base / f"{p}categories.csv",
        "source_path": base / f"{p}sources.csv",
        "qa_path": base / f"{p}qa.csv",
        "mapping_path": base / f"{p}item_mapping.csv",
        "coverage_path": base / f"{p}item_coverage.csv",
        "review_evidence_path": base / f"{p}category_review_evidence.csv",
    }


def main() -> int:
    p = paths()
    errors, _, _ = validate_dataset(label="BATCH_03", **p)
    _, municipalities = read_csv(p["municipality_path"])
    _, categories = read_csv(p["category_path"])
    _, qa = read_csv(p["qa_path"])
    _, evidence = read_csv(p["review_evidence_path"])

    by_mid = {row["municipality_id"]: row for row in municipalities}
    qa_by_mid = {row["municipality_id"]: row for row in qa}
    evidence_count = Counter(row["municipality_id"] for row in evidence)

    checks = []
    checks.append(("structural validation passes", not errors, f"errors={len(errors)}"))
    checks.append(("exact MASTER target set", set(by_mid) == TARGETS, f"targets={sorted(by_mid)}"))
    checks.append(("nine reviewed municipalities pass QA", all(
        by_mid[mid]["category_count_check_status"] == "MANUAL_INDEX_REVIEW"
        and by_mid[mid]["category_count_verified"] == "TRUE"
        and qa_by_mid[mid]["確認ステータス"] == "QA_PASSED"
        and evidence_count[mid] >= 1
        and int(by_mid[mid]["reviewed_category_count"]) == counted_category_total(mid, categories)
        for mid in REVIEWED
    ), ""))
    checks.append(("Yura evidence gap remains explicit", (
        by_mid["M028"]["category_count_check_status"] == "NOT_REVIEWED"
        and by_mid["M028"]["category_count_verified"] == "FALSE"
        and qa_by_mid["M028"]["確認ステータス"] == "QA_REQUIRED"
        and evidence_count["M028"] == 0
    ), "M028 must not be auto-promoted"))
    checks.append(("no filler text in Batch 03 category details", not any(
        is_placeholder_category_value(row.get(field, ""))
        for row in categories for field in CATEGORY_DETAIL_FIELDS
    ), f"categories={len(categories)}"))
    checks.append(("all stored category sources are dated 2026-08-19", all(
        row.get("確認日") == "2026-08-19" for row in categories
    ), ""))

    passed = sum(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    print(f"BATCH03_RED_TEAM_SUMMARY={passed}/{len(checks)}")
    if passed == len(checks):
        print("BATCH03_RED_TEAM_PASSED_WITH_M028_EVIDENCE_HOLD")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
