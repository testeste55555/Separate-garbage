#!/usr/bin/env python3
"""Mutation RED TEAM for the M020 40-item APP_READY contract."""
from __future__ import annotations

from copy import deepcopy

import validate_app_readiness_m020 as gate


def expect_rejected(label: str, mutate) -> None:
    data = gate.load_context()
    mutate(data)
    errors = gate.validate_context(data)
    if not errors:
        raise AssertionError(f"RED TEAM mutation was accepted: {label}")
    print(f"PASS: {label} rejected")


def main() -> int:
    base_errors = gate.validate()
    if base_errors:
        print("M020_RED_TEAM_BASE_INVALID")
        for error in base_errors:
            print(f"- {error}")
        return 1

    tests = []

    def missing_item(data):
        data["audit"] = [r for r in data["audit"] if not (r.get("municipality_id") == gate.MID and r.get("internal_item_id") == "I040")]
    tests.append(("missing one of 40 items", missing_item))

    def old_battery_route(data):
        for row in data["audit"]:
            if row.get("municipality_id") == gate.MID and row.get("internal_item_id") == "I027":
                row["category_id"] = "C-M020-04"
                row["category_name"] = "乾電池"
    tests.append(("2026 dry battery downgraded to retired legacy route", old_battery_route))

    def mobile_burnable(data):
        for row in data["audit"]:
            if row.get("municipality_id") == gate.MID and row.get("internal_item_id") == "I029":
                row["category_id"] = "C-M020-01"
                row["category_name"] = "可燃ごみ"
    tests.append(("mobile battery forced into combustible waste", mobile_burnable))

    def collapse_paper_pack(data):
        data["audit"] = [
            r for r in data["audit"]
            if not (r.get("municipality_id") == gate.MID and r.get("internal_item_id") == "I017" and r.get("branch_order") == "2")
        ]
    tests.append(("aluminum paper-pack branch collapsed", collapse_paper_pack))

    def pc_old_excluded(data):
        for row in data["audit"]:
            if row.get("municipality_id") == gate.MID and row.get("internal_item_id") == "I038":
                row["category_id"] = "C-M020-17"
                row["category_name"] = "市では収集・処理できないごみ"
    tests.append(("household PC sent to obsolete general exclusion route", pc_old_excluded))

    def spray_hole(data):
        for row in data["audit"]:
            if row.get("municipality_id") == gate.MID and row.get("internal_item_id") == "I032":
                row["preparation"] = "中身を使い切り、穴を開けて出す"
    tests.append(("spray can hole-punch instruction", spray_hole))

    def lighter_gas(data):
        for row in data["audit"]:
            if row.get("municipality_id") == gate.MID and row.get("internal_item_id") == "I033":
                row["preparation"] = "ガス抜きをして穴を開ける"
    tests.append(("unsupported lighter gas/hole instruction", lighter_gas))

    def image_wrong_category(data):
        for row in data["images"]:
            if row.get("municipality_id") == gate.MID and row.get("internal_item_id") == "I029":
                row["category_id"] = "C-M020-16"
                row["category_name"] = "使用済小型家電"
    tests.append(("fixed10 mobile battery image mapped to small-appliance box", image_wrong_category))

    def unnecessary_variant(data):
        data["variants"].append({"municipality_id": gate.MID, "lesson_variant_group_id": "LV-M020-FAKE"})
    tests.append(("collection-channel-only learner variant introduced", unnecessary_variant))

    def premature_company(data):
        for row in data["scope"]:
            if row.get("municipality_id") == gate.MID:
                row["scoring_status"] = "LESSON_READY_10"
    tests.append(("company remains active after APP_READY scope removal", premature_company))

    for label, mutate in tests:
        expect_rejected(label, mutate)

    print(f"M020_APP_READINESS_RED_TEAM_PASSED {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
