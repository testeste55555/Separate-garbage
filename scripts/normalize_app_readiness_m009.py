#!/usr/bin/env python3
"""Keep Batch 01's historical M009 category-level projections aligned with current categories."""
from __future__ import annotations

from pathlib import Path

from schema_v12 import MAPPING_FIELDS, read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M009"
BATCH = ROOT / "data/research/batches/batch_01"


def main() -> None:
    _, categories = read_csv(BATCH / "batch_01_categories.csv")
    category_by = {(r["municipality_id"], r["category_id"]): r for r in categories}
    path = BATCH / "batch_01_item_mapping.csv"
    _, mappings = read_csv(path)
    refreshed = 0
    for row in mappings:
        if row.get("municipality_id") != MID:
            continue
        category = category_by.get((MID, row.get("category_id", "")))
        if not category or category.get("rule_status") != "CURRENT":
            raise ValueError(f"M009 Batch 01 initial mapping points to non-current category: {row.get('mapping_id')}")
        row["分別区分正式名称"] = category["自治体正式名称"]
        row["自治体収集外"] = category["自治体収集外か"]
        row["rule_status"] = category["rule_status"]
        row["effective_from"] = category["effective_from"]
        row["effective_to"] = category["effective_to"]
        row["category_source_id"] = category["source_id"]
        row["category_source_url"] = category["出典URL"]
        row["category_source_locator"] = category["出典ページ・該当箇所"]
        row["item_evidence_source_id"] = ""
        row["item_evidence_url"] = ""
        row["item_evidence_locator"] = ""
        row["mapping_status"] = "INITIAL_REVIEW_REQUIRED"
        row["evidence_scope"] = "CATEGORY_LEVEL"
        row["branch_review_status"] = "UNREVIEWED"
        row["reviewed_date"] = ""
        row["reviewed_by"] = ""
        refreshed += 1
    write_csv(path, MAPPING_FIELDS, mappings)
    print(f"M009_APP_READY_NORMALIZED batch_initial_mappings_refreshed={refreshed}")


if __name__ == "__main__":
    main()
