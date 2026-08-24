#!/usr/bin/env python3
"""Mutation RED TEAM for the M104 municipality-wide APP readiness Pilot."""

from __future__ import annotations

import copy
import sys

from schema_v12 import read_csv
from validate_app_readiness_pilot_m104 import AUDIT_PATH, validate_review_rows


def branch(rows, iid, order):
    return next(r for r in rows if r["internal_item_id"] == iid and r["branch_order"] == str(order))


def drop(rows, iid, order):
    rows.remove(branch(rows, iid, order))


def mutated(base, mutate) -> bool:
    candidate = copy.deepcopy(base)
    mutate(candidate)
    return bool(validate_review_rows(candidate))


def main() -> int:
    _, base = read_csv(AUDIT_PATH)
    checks = [
        ("base M104 review passes", not validate_review_rows(base)),
        ("missing common item is rejected", mutated(base, lambda r: r.__setitem__(slice(None), [x for x in r if x["internal_item_id"] != "I040"]))),
        ("common-item master tamper is rejected", mutated(base, lambda r: branch(r, "I001", 1).update({"display_name": "PET"}))),
        ("unofficial evidence URL is rejected", mutated(base, lambda r: branch(r, "I029", 1).update({"item_evidence_url": "https://example.com/"}))),
        ("blank source locator is rejected", mutated(base, lambda r: branch(r, "I032", 1).update({"item_evidence_locator": ""}))),
        ("generic placeholder is rejected", mutated(base, lambda r: branch(r, "I013", 1).update({"preparation": "公式ガイドの指定方法"}))),
        ("non-food glass route cannot collapse", mutated(base, lambda r: drop(r, "I006", 2))),
        ("unmarked tray route cannot collapse", mutated(base, lambda r: drop(r, "I007", 2))),
        ("dirty tray route cannot collapse", mutated(base, lambda r: drop(r, "I008", 3))),
        ("non-package lunch-box route cannot collapse", mutated(base, lambda r: drop(r, "I009", 2))),
        ("paper snack-bag route cannot collapse", mutated(base, lambda r: drop(r, "I010", 3))),
        ("non-package shopping-bag route cannot collapse", mutated(base, lambda r: drop(r, "I011", 2))),
        ("oversize foam route cannot collapse", mutated(base, lambda r: drop(r, "I012", 3))),
        ("nonrecyclable paper route cannot collapse", mutated(base, lambda r: drop(r, "I016", 2))),
        ("aluminum-lined carton route cannot collapse", mutated(base, lambda r: drop(r, "I017", 2))),
        ("oversize ceramic route cannot collapse", mutated(base, lambda r: drop(r, "I023", 2))),
        ("oversize battery route cannot collapse", mutated(base, lambda r: drop(r, "I029", 2))),
        ("battery-built-in appliance size route cannot collapse", mutated(base, lambda r: drop(r, "I035", 2))),
        ("oversize futon route cannot collapse", mutated(base, lambda r: drop(r, "I036", 2))),
        ("home appliances cannot be relabeled bulky waste", mutated(base, lambda r: branch(r, "I037", 1).update({"category_id": "C-M104-11"}))),
        ("PC cannot be relabeled bulky waste", mutated(base, lambda r: branch(r, "I038", 1).update({"category_id": "C-M104-11"}))),
        ("three pruning diameter branches retain identity", [x["category_id"] for x in base if x["internal_item_id"] == "I040"] == ["C-M104-01", "C-M104-04", "C-M104-04"]),
    ]
    passed = sum(ok for _, ok in checks)
    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    if passed != len(checks):
        print(f"M104_APP_READINESS_RED_TEAM_FAILED {passed}/{len(checks)}")
        return 1
    print(f"M104_APP_READINESS_RED_TEAM_PASSED {passed}/{len(checks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
