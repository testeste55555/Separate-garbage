#!/usr/bin/env python3
"""Mutation RED TEAM for Kure City's M095 APP readiness review."""

from __future__ import annotations

import copy
import sys

from schema_v12 import read_csv
from validate_app_readiness_pilot_m095 import AUDIT_PATH, validate_review_rows


def mutate(rows, iid, branch, field, value):
    out = copy.deepcopy(rows)
    for row in out:
        if row.get("internal_item_id") == iid and row.get("branch_order") == str(branch):
            row[field] = value
            return out
    raise AssertionError(f"row not found {iid}/{branch}")


def main() -> int:
    _, baseline = read_csv(AUDIT_PATH)
    base_errors = validate_review_rows(baseline)
    if base_errors:
        print("M095_RED_TEAM_BASELINE_FAILED")
        for error in base_errors:
            print(f"- {error}")
        return 1

    cases = []
    cases.append(("PET cap regressed to combustible", mutate(baseline, "I002", 1, "category_id", "C-M095-01")))
    cases.append(("PET label regressed to combustible", mutate(baseline, "I003", 1, "category_id", "C-M095-01")))
    cases.append(("spray can puncture rule removed", mutate(baseline, "I032", 1, "preparation", "有害・危険ごみへ出す")))
    cases.append(("spray remaining-content rule removed", mutate(baseline, "I032", 1, "exception_destination", "なし")))
    cases.append(("swollen battery counter route removed", mutate(baseline, "I029", 1, "exception_destination", "通常回収")))
    cases.append(("non-removable battery appliance sent to nonburnable", mutate(baseline, "I035", 1, "category_id", "C-M095-02")))
    cases.append(("home appliance 4 sent to bulky", mutate(baseline, "I037", 1, "category_id", "C-M095-03")))
    cases.append(("foil paper pack sent to combustible", mutate(baseline, "I017", 2, "category_id", "C-M095-01")))
    cases.append(("official source removed", mutate(baseline, "I006", 1, "item_evidence_source_id", "")))
    cases.append(("external evidence URL injected", mutate(baseline, "I022", 1, "item_evidence_url", "https://example.com/kasa")))
    cases.append(("branch completeness downgraded", mutate(baseline, "I030", 2, "branch_review_status", "INCOMPLETE")))
    cases.append(("common item name drift", mutate(baseline, "I021", 1, "display_name", "古着")))
    cases.append(("review date removed", mutate(baseline, "I036", 1, "checked_date", "")))
    cases.append(("unsupported evidence basis", mutate(baseline, "I011", 1, "evidence_basis", "GUESS")))
    removed = copy.deepcopy(baseline)
    removed = [r for r in removed if not (r.get("internal_item_id") == "I040" and r.get("branch_order") == "3")]
    cases.append(("oversize pruning branch dropped", removed))
    duplicate = copy.deepcopy(baseline)
    for row in duplicate:
        if row.get("internal_item_id") == "I006" and row.get("branch_order") == "2":
            row["branch_order"] = "1"
            break
    cases.append(("duplicate branch order", duplicate))

    failures = []
    for name, candidate in cases:
        if not validate_review_rows(candidate):
            failures.append(name)

    if failures:
        print("M095_RED_TEAM_FAILED")
        for name in failures:
            print(f"- mutation escaped validator: {name}")
        return 1
    print(f"M095_RED_TEAM_PASSED mutations={len(cases)}/{len(cases)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
