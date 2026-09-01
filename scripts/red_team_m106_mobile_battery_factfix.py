#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy

from validate_m106_mobile_battery_factfix import load_state, validate_state


def mutate(state, name):
    data = deepcopy(state)
    if name == "review_back_to_retailer":
        row = next(r for r in data["review"] if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029" and r.get("branch_order") == "1")
        row["category_id"] = "C-M106-14"
        row["category_name"] = "販売店やリサイクル業者に引き取ってもらう"
    elif name == "projection_back_to_simplified":
        row = next(r for r in data["projection"] if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029")
        row["teaching_box_id"] = "TB-M106-ON-07"
        row["projection_kind"] = "SIMPLIFIED_ACTION"
        row["category_id"] = "C-M106-14"
    elif name == "image_mapping_stale":
        row = next(r for r in data["image"] if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029")
        row["category_id"] = "C-M106-14"
    elif name == "canonical_mapping_stale":
        row = next(r for r in data["mapping"] if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029" and r.get("branch_order") == "1")
        row["category_id"] = "C-M106-14"
    elif name == "reintroduce_recovery_box":
        data["boxes"].append({"municipality_id": "M106", "teaching_box_id": "TB-M106-ON-07", "class_mode": "ONLINE_CLASS", "category_id": "C-M106-14"})
    elif name == "drop_current_evidence":
        row = next(r for r in data["review"] if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029" and r.get("branch_order") == "1")
        row["item_evidence_url"] = row.get("exception_evidence_url", "")
    else:
        raise ValueError(name)
    return data


def main() -> int:
    base = load_state()
    if validate_state(base):
        print("M106_RED_TEAM_ABORT: baseline is invalid")
        return 1
    cases = [
        "review_back_to_retailer",
        "projection_back_to_simplified",
        "image_mapping_stale",
        "canonical_mapping_stale",
        "reintroduce_recovery_box",
        "drop_current_evidence",
    ]
    failures = []
    for case in cases:
        errors = validate_state(mutate(base, case))
        if not errors:
            failures.append(case)
        else:
            print(f"PASS {case}: rejected ({errors[0]})")
    if failures:
        print("M106_MOBILE_BATTERY_FACTFIX_RED_TEAM_FAILED: " + ", ".join(failures))
        return 1
    print(f"M106_MOBILE_BATTERY_FACTFIX_RED_TEAM_PASSED cases={len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
