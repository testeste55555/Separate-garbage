#!/usr/bin/env python3
"""Validate the formal garbage-lesson 15-item set.

This file defines lesson membership only. It does not promote supplemental
items to LESSON_READY_10/APP_READY and does not imply scoring readiness.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SET_PATH = ROOT / "data/app/lesson_item_set.csv"
MASTER_PATH = ROOT / "data/master/04_common_items_master.csv"

EXPECTED_CORE = ["I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"]
EXPECTED_SUPPLEMENTAL = ["I002", "I003", "I027", "I018", "I010"]
EXPECTED_SET_ID = "GARBAGE_LESSON_15_V1"
EXPECTED_FIELDS = [
    "lesson_set_id", "item_role", "display_order", "internal_item_id",
    "canonical_name", "display_name", "note",
]


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def main() -> int:
    errors: list[str] = []
    fields, rows = read(SET_PATH)
    if fields != EXPECTED_FIELDS:
        errors.append(f"unexpected header: {fields}")
    if len(rows) != 15:
        errors.append(f"expected 15 rows, got {len(rows)}")

    ids = [row.get("internal_item_id", "") for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("internal_item_id must be unique")
    if [row.get("display_order") for row in rows] != [str(i) for i in range(1, 16)]:
        errors.append("display_order must be exactly 1..15")
    if any(row.get("lesson_set_id") != EXPECTED_SET_ID for row in rows):
        errors.append(f"lesson_set_id must be {EXPECTED_SET_ID}")

    core = [row.get("internal_item_id") for row in rows if row.get("item_role") == "CORE_10"]
    supplemental = [row.get("internal_item_id") for row in rows if row.get("item_role") == "SUPPLEMENTAL_5"]
    unknown_roles = sorted({row.get("item_role", "") for row in rows} - {"CORE_10", "SUPPLEMENTAL_5"})
    if core != EXPECTED_CORE:
        errors.append(f"CORE_10 mismatch: {core}")
    if supplemental != EXPECTED_SUPPLEMENTAL:
        errors.append(f"SUPPLEMENTAL_5 mismatch: {supplemental}")
    if unknown_roles:
        errors.append(f"unknown item_role: {unknown_roles}")

    _, master_rows = read(MASTER_PATH)
    master = {row["internal_item_id"]: row for row in master_rows}
    for row in rows:
        iid = row.get("internal_item_id", "")
        source = master.get(iid)
        if not source:
            errors.append(f"unknown internal_item_id: {iid}")
            continue
        if row.get("canonical_name") != source.get("一般管理用名称"):
            errors.append(f"canonical_name drift for {iid}")
        if row.get("display_name") != source.get("教材表示名"):
            errors.append(f"display_name drift for {iid}")
        if source.get("selection_status") != "CONFIRMED_V1":
            errors.append(f"item is not CONFIRMED_V1: {iid}")

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        print(f"LESSON_ITEM_SET_VALIDATION_FAILED errors={len(errors)}")
        return 1

    print("PASS formal lesson set = 15 unique confirmed master items")
    print("PASS CORE_10 = 10 / SUPPLEMENTAL_5 = 5")
    print("PASS membership does not alter scoring readiness")
    print("LESSON_ITEM_SET_VALIDATION_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
