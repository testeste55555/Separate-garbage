#!/usr/bin/env python3
"""Validate the teaching-group layer and learner SORT_BUCKET display contract."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMON_ITEMS = ROOT / "data/master/04_common_items_master.csv"
GROUP_MAPPING = ROOT / "data/master/06_teaching_item_group_mapping.csv"
MUNICIPALITIES = ROOT / "data/master/01_municipalities_master.csv"
CATEGORIES = ROOT / "data/research/02_categories_master.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require_columns(rows: list[dict[str, str]], required: set[str], label: str) -> None:
    if not rows:
        raise AssertionError(f"{label}: no rows")
    missing = required.difference(rows[0].keys())
    if missing:
        raise AssertionError(f"{label}: missing columns: {sorted(missing)}")


def main() -> None:
    common = read_csv(COMMON_ITEMS)
    groups = read_csv(GROUP_MAPPING)
    municipalities = read_csv(MUNICIPALITIES)
    categories = read_csv(CATEGORIES)

    require_columns(common, {"internal_item_id", "一般管理用名称"}, "common items")
    require_columns(
        groups,
        {"internal_item_id", "teaching_group_id", "teaching_group_name", "lesson_scope"},
        "teaching group mapping",
    )
    require_columns(municipalities, {"municipality_id", "都道府県", "市町村"}, "municipalities")
    require_columns(
        categories,
        {"municipality_id", "category_id", "自治体正式名称", "表示順", "ui_role", "rule_status"},
        "categories",
    )

    common_ids = [row["internal_item_id"].strip() for row in common]
    group_ids = [row["internal_item_id"].strip() for row in groups]

    duplicate_common = [item for item, count in Counter(common_ids).items() if count > 1]
    duplicate_groups = [item for item, count in Counter(group_ids).items() if count > 1]
    if duplicate_common:
        raise AssertionError(f"common items: duplicate internal_item_id: {duplicate_common}")
    if duplicate_groups:
        raise AssertionError(f"group mapping: duplicate internal_item_id: {duplicate_groups}")

    if set(common_ids) != set(group_ids):
        missing = sorted(set(common_ids) - set(group_ids))
        unknown = sorted(set(group_ids) - set(common_ids))
        raise AssertionError(f"group mapping coverage mismatch: missing={missing}, unknown={unknown}")

    if len(common_ids) != 40:
        raise AssertionError(f"expected 40 common items, found {len(common_ids)}")

    for row in groups:
        if not row["teaching_group_id"].strip() or not row["teaching_group_name"].strip():
            raise AssertionError(f"blank teaching group for {row['internal_item_id']}")

    municipality_ids = {row["municipality_id"].strip() for row in municipalities}
    display_rows = [
        row
        for row in categories
        if row["ui_role"].strip() == "SORT_BUCKET" and row["rule_status"].strip() == "CURRENT"
    ]

    unknown_municipalities = sorted(
        {row["municipality_id"].strip() for row in display_rows} - municipality_ids
    )
    if unknown_municipalities:
        raise AssertionError(f"SORT_BUCKET rows reference unknown municipalities: {unknown_municipalities}")

    seen_keys: Counter[tuple[str, str]] = Counter(
        (row["municipality_id"].strip(), row["category_id"].strip()) for row in display_rows
    )
    duplicates = [key for key, count in seen_keys.items() if count > 1]
    if duplicates:
        raise AssertionError(f"duplicate display category keys: {duplicates[:10]}")

    blanks = [
        (row["municipality_id"], row["category_id"])
        for row in display_rows
        if not row["自治体正式名称"].strip()
    ]
    if blanks:
        raise AssertionError(f"SORT_BUCKET rows with blank official name: {blanks[:10]}")

    by_municipality: dict[str, int] = defaultdict(int)
    for row in display_rows:
        by_municipality[row["municipality_id"].strip()] += 1

    print("PASS teaching/display layer")
    print(f"common_items={len(common_ids)}")
    print(f"teaching_groups={len({row['teaching_group_id'].strip() for row in groups})}")
    print(f"display_municipalities={len(by_municipality)}")
    print(f"sort_bucket_rows={len(display_rows)}")


if __name__ == "__main__":
    main()
