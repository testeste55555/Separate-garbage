#!/usr/bin/env python3
"""Mutation RED TEAM for M009 40-item APP_READY."""
from __future__ import annotations

import validate_app_readiness_m009 as gate


def reject(label, mutate):
    data = gate.load()
    mutate(data)
    if not gate.validate_context(data):
        raise AssertionError(f"RED TEAM mutation accepted: {label}")
    print(f"PASS: {label} rejected")


def main() -> int:
    base = gate.validate()
    if base:
        print("M009_RED_TEAM_BASE_INVALID")
        for error in base:
            print("-", error)
        return 1
    tests = []
    tests.append(("missing one of 40 items", lambda d: d.__setitem__("audit", [r for r in d["audit"] if not (r.get("municipality_id")==gate.MID and r.get("internal_item_id")=="I040")])) )

    def mobile_wrong(d):
        for r in d["audit"]:
            if r.get("municipality_id")==gate.MID and r.get("internal_item_id")=="I029": r["category_id"]="C-M009-02"
    tests.append(("mobile battery removed from dry-battery stream", mobile_wrong))

    def bulb_mercury(d):
        for r in d["audit"]:
            if r.get("municipality_id")==gate.MID and r.get("internal_item_id")=="I031": r["category_id"]="C-M009-07"
    tests.append(("LED/incandescent bulb forced into mercury stream", bulb_mercury))

    def fluorescent_nonburn(d):
        for r in d["audit"]:
            if r.get("municipality_id")==gate.MID and r.get("internal_item_id")=="I030": r["category_id"]="C-M009-02"
    tests.append(("fluorescent tube collapsed into nonburnable", fluorescent_nonburn))

    def spray_hole(d):
        for r in d["audit"]:
            if r.get("municipality_id")==gate.MID and r.get("internal_item_id")=="I032": r["preparation"]="中身を使い切り、穴をあける"
    tests.append(("spray-can hole punching", spray_hole))

    def tray_store_only(d):
        for r in d["audit"]:
            if r.get("municipality_id")==gate.MID and r.get("internal_item_id")=="I007": r["category_id"]="C-M009-09"
    tests.append(("white tray forced to store-only route", tray_store_only))

    def pack_store_only(d):
        for r in d["audit"]:
            if r.get("municipality_id")==gate.MID and r.get("internal_item_id")=="I017": r["category_id"]="C-M009-09"
    tests.append(("paper pack forced to store-only route", pack_store_only))

    def pc_excluded(d):
        for r in d["audit"]:
            if r.get("municipality_id")==gate.MID and r.get("internal_item_id")=="I038": r["category_id"]="C-M009-09"
    tests.append(("household PC sent to general exclusion despite direct haul", pc_excluded))

    def collapse_branch(d):
        d["audit"]=[r for r in d["audit"] if not (r.get("municipality_id")==gate.MID and r.get("internal_item_id")=="I040" and r.get("branch_order")=="2")]
    tests.append(("oversize pruning branch collapsed", collapse_branch))

    def wrong_image(d):
        for r in d["images"]:
            if r.get("municipality_id")==gate.MID and r.get("internal_item_id")=="I029": r["category_id"]="C-M009-02"
    tests.append(("fixed10 mobile battery image mapped to nonburnable", wrong_image))

    def variant(d):
        d["variants"].append({"municipality_id":gate.MID,"lesson_variant_group_id":"LV-M009-FAKE"})
    tests.append(("unnecessary learner regional variant", variant))

    def company_without_ready(d):
        for r in d["scope"]:
            if r.get("municipality_id")==gate.MID: r["scoring_status"]="LESSON_READY_10"
    tests.append(("company active without APP_READY", company_without_ready))

    for label, mutate in tests:
        reject(label, mutate)
    print(f"M009_APP_READINESS_RED_TEAM_PASSED {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
