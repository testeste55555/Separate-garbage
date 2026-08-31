#!/usr/bin/env python3
"""Mutation RED TEAM for M098 Onomichi 40-item APP_READY."""
from __future__ import annotations

import validate_app_readiness_m098 as gate


def reject(label, mutate):
    data = gate.load()
    mutate(data)
    if not gate.validate_context(data):
        raise AssertionError(f"RED TEAM mutation accepted: {label}")
    print(f"PASS: {label} rejected")


def main() -> int:
    base = gate.validate()
    if base:
        print("M098_RED_TEAM_BASE_INVALID")
        for error in base:
            print("-", error)
        return 1

    tests = []
    tests.append((
        "missing one of 40 items",
        lambda d: d.__setitem__("audit", [r for r in d["audit"] if not (r.get("municipality_id") == gate.MID and r.get("internal_item_id") == "I040")]),
    ))

    def old_bulb_route(d):
        for r in d["audit"]:
            if r.get("municipality_id") == gate.MID and r.get("internal_item_id") == "I031":
                r["category_id"] = "C-M098-03"
                r["category_name"] = "もやせないごみ"
                r["item_evidence_source_id"] = "S-M098-04"
    tests.append(("pre-2026 bulb route restored", old_bulb_route))

    def mobile_nonburnable(d):
        for r in d["audit"]:
            if r.get("municipality_id") == gate.MID and r.get("internal_item_id") == "I029":
                r["category_id"] = "C-M098-03"
                r["category_name"] = "もやせないごみ"
    tests.append(("mobile battery collapsed into nonburnable", mobile_nonburnable))

    def button_guessed_dry(d):
        for r in d["audit"]:
            if r.get("municipality_id") == gate.MID and r.get("internal_item_id") == "I028":
                r["category_id"] = "C-M098-06"
                r["category_name"] = "有害ごみ"
    tests.append(("button battery guessed into dry-battery stream", button_guessed_dry))

    def lighter_weakened(d):
        for r in d["audit"]:
            if r.get("municipality_id") == gate.MID and r.get("internal_item_id") == "I033":
                r["preparation"] = "そのまま袋に入れる"
    tests.append(("lighter use-up/separate-bag safety removed", lighter_weakened))

    def spray_no_hole(d):
        for r in d["audit"]:
            if r.get("municipality_id") == gate.MID and r.get("internal_item_id") == "I032":
                r["preparation"] = "中身を使い切って出す"
    tests.append(("spray-can hole requirement removed", spray_no_hole))

    def collapse_pruning(d):
        d["audit"] = [
            r for r in d["audit"]
            if not (r.get("municipality_id") == gate.MID and r.get("internal_item_id") == "I040" and r.get("branch_order") == "2")
        ]
    tests.append(("oversize pruning branch collapsed", collapse_pruning))

    def expose_selector(d):
        for r in d["groups"]:
            if r.get("municipality_id") == gate.MID:
                r["learner_selection_required"] = "TRUE"
    tests.append(("learner region selector exposed", expose_selector))

    def split_district(d):
        for r in d["districts"]:
            if r.get("municipality_id") == gate.MID and r.get("district_scope_id") == "DS-M098-06":
                r["lesson_variant_group_id"] = "LV-M098-FAKE"
    tests.append(("six-district lesson group split", split_district))

    def company_inactive(d):
        for r in d["company"]:
            if r.get("municipality_id") == gate.MID and r.get("company_id") == "C001":
                r["active"] = "FALSE"
    tests.append(("confirmed M098 company left inactive", company_inactive))

    def leak_batch_app_mapping(d):
        d["batch_mappings"].append({
            "municipality_id": gate.MID,
            "mapping_id": "MAP-M098-LEAK",
            "internal_item_id": "I001",
        })
    tests.append(("APP item evidence leaked into Batch 10 ordinary layer", leak_batch_app_mapping))

    for label, mutate in tests:
        reject(label, mutate)
    print(f"M098_APP_READINESS_RED_TEAM_PASSED {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
