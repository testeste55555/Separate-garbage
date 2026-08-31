#!/usr/bin/env python3
"""Print a compact 40-item readiness/evidence inventory for M098 and M099."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("M098", "M099")


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def clean(value: str) -> str:
    return (value or "").replace("\n", " ").strip()


def main() -> None:
    coverage = rows("data/research/07_item_mapping_coverage.csv")
    mappings = rows("data/research/05_item_mapping_master.csv")
    categories = rows("data/research/02_categories_master.csv")
    sources = rows("data/research/03_sources_master.csv")
    districts = rows("data/app/district_scopes.csv")
    groups = rows("data/app/lesson_variant_groups.csv")
    variant_scoring = rows("data/app/lesson_variant_item_scoring.csv")

    mapping_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mappings:
        if row.get("municipality_id") in TARGETS:
            mapping_by_pair[(row["municipality_id"], row["internal_item_id"])].append(row)

    coverage_by_pair = {
        (row["municipality_id"], row["internal_item_id"]): row
        for row in coverage
        if row.get("municipality_id") in TARGETS
    }

    for mid in TARGETS:
        print(f"=== {mid} 40-ITEM CANONICAL ===")
        for number in range(1, 41):
            iid = f"I{number:03d}"
            cov = coverage_by_pair.get((mid, iid), {})
            branches = sorted(
                mapping_by_pair.get((mid, iid), []),
                key=lambda row: int(row.get("branch_order") or 0),
            )
            branch_text = " | ".join(
                f"b{clean(row.get('branch_order'))}:{clean(row.get('category_id'))}:"
                f"{clean(row.get('分別区分正式名称'))}:status={clean(row.get('mapping_status'))}:"
                f"review={clean(row.get('branch_review_status'))}:src={clean(row.get('item_evidence_source_id'))}:"
                f"cond={clean(row.get('条件'))}"
                for row in branches
            ) or "NO_MAPPING"
            print(
                f"{iid} coverage={clean(cov.get('coverage_status'))} "
                f"complete={clean(cov.get('branch_completeness_confirmed'))} "
                f"branches={clean(cov.get('mapping_branch_count'))} :: {branch_text}"
            )

        print(f"=== {mid} CATEGORIES ===")
        for row in categories:
            if row.get("municipality_id") == mid:
                print(
                    f"{clean(row.get('category_id'))} {clean(row.get('自治体正式名称'))} "
                    f"role={clean(row.get('ui_role'))} parent={clean(row.get('parent_category_id'))} "
                    f"source={clean(row.get('source_id'))}"
                )
        print(f"=== {mid} SOURCES ===")
        for row in sources:
            if row.get("municipality_id") == mid:
                print(
                    f"{clean(row.get('source_id'))} official={clean(row.get('official_verified'))} "
                    f"current={clean(row.get('現行性'))} title={clean(row.get('資料名'))} "
                    f"url={clean(row.get('公式URL'))}"
                )
        print(f"=== {mid} DISTRICTS / LESSON GROUPS ===")
        for row in districts:
            if row.get("municipality_id") == mid:
                print("DISTRICT " + " | ".join(f"{key}={clean(value)}" for key, value in row.items()))
        for row in groups:
            if row.get("municipality_id") == mid:
                print("GROUP " + " | ".join(f"{key}={clean(value)}" for key, value in row.items()))
        print(f"=== {mid} FIXED10 VARIANT CATEGORY DIFFERENCES ===")
        by_item: dict[str, set[tuple[str, str]]] = defaultdict(set)
        for row in variant_scoring:
            if row.get("municipality_id") == mid:
                by_item[row.get("internal_item_id", "")].add(
                    (row.get("lesson_variant_group_id", ""), row.get("category_id", ""))
                )
        for iid, decisions in sorted(by_item.items()):
            categories_used = {category for _, category in decisions}
            if len(categories_used) > 1 or mid == "M099":
                print(iid + " " + " | ".join(f"{group}:{category}" for group, category in sorted(decisions)))


if __name__ == "__main__":
    main()
