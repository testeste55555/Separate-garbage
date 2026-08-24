#!/usr/bin/env python3
"""Mutation RED TEAM for the M094 municipality-wide APP readiness Pilot."""

from __future__ import annotations

import copy
import sys

from schema_v12 import read_csv
from validate_app_readiness_pilot_m094 import AUDIT_PATH, validate_review_rows


def mutated(base, mutate) -> bool:
    candidate = copy.deepcopy(base)
    mutate(candidate)
    return bool(validate_review_rows(candidate))


def item(rows, iid):
    return [r for r in rows if r["internal_item_id"] == iid]


def branch(rows, iid, order):
    return next(r for r in rows if r["internal_item_id"] == iid and r["branch_order"] == str(order))


def drop_branch(rows, iid, order):
    rows.remove(branch(rows, iid, order))


def main() -> int:
    _, base = read_csv(AUDIT_PATH)
    checks = [
        ("base M094 review passes", not validate_review_rows(base)),
        ("missing one of 40 items is rejected", mutated(base, lambda rows: rows.__setitem__(slice(None), [r for r in rows if r["internal_item_id"] != "I040"]))),
        ("official item name tamper is rejected", mutated(base, lambda rows: branch(rows, "I001", 1).update({"canonical_name": "PET容器"}))),
        ("unofficial evidence URL is rejected", mutated(base, lambda rows: branch(rows, "I029", 1).update({"item_evidence_url": "https://example.com/battery"}))),
        ("missing locator is rejected", mutated(base, lambda rows: branch(rows, "I032", 1).update({"item_evidence_locator": ""}))),
        ("generic placeholder rule is rejected", mutated(base, lambda rows: branch(rows, "I013", 1).update({"preparation": "公式ガイドの指定方法"}))),
        ("dirty tray fallback branch cannot be collapsed", mutated(base, lambda rows: drop_branch(rows, "I007", 2))),
        ("paper snack-bag branch cannot be collapsed", mutated(base, lambda rows: drop_branch(rows, "I010", 2))),
        ("heat-resistant glass branch cannot be collapsed", mutated(base, lambda rows: drop_branch(rows, "I024", 1))),
        ("razor/cutter-blade branch cannot be collapsed", mutated(base, lambda rows: drop_branch(rows, "I026", 2))),
        ("LED fluorescent-tube branch cannot be collapsed", mutated(base, lambda rows: drop_branch(rows, "I030", 2))),
        ("mercury bulb branch cannot be collapsed", mutated(base, lambda rows: drop_branch(rows, "I031", 2))),
        ("nonempty spray-can route cannot be collapsed", mutated(base, lambda rows: drop_branch(rows, "I032", 2))),
        ("small-appliance size branch cannot be collapsed", mutated(base, lambda rows: drop_branch(rows, "I034", 2))),
        ("bulk pruning route cannot be collapsed", mutated(base, lambda rows: drop_branch(rows, "I040", 2))),
        ("same-category condition branches retain identity", [r["category_id"] for r in item(base, "I009")] == ["C-M094-03", "C-M094-01", "C-M094-01"]),
    ]
    passed = sum(ok for _, ok in checks)
    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    if passed != len(checks):
        print(f"M094_APP_READINESS_RED_TEAM_FAILED {passed}/{len(checks)}")
        return 1
    print(f"M094_APP_READINESS_RED_TEAM_PASSED {passed}/{len(checks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
