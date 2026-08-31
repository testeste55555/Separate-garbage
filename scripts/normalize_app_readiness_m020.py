#!/usr/bin/env python3
"""Normalize M020 promotion outputs to repository ownership/lifecycle rules.

- IS-* item-evidence sources live only in canonical as merge-preserved supplements;
  they must not be duplicated inside the historical Batch 02 ordinary-source bundle.
- M020 PET collection channel differs by district (drop-off in 葵・駿河, curbside in
  清水). Schema v1.2 has no mixed-channel enum, so leave the optional channel blank
  rather than encode a false municipality-wide channel. Exact district behavior stays
  in category/item evidence text.
- Batch 02 remains the ordinary research bundle. When its M020 category snapshot is
  refreshed to the 2026 system, its historical INITIAL_REVIEW_REQUIRED projections
  must point at those current category rows and copy their category citation fields.
  APP_READY item evidence itself remains canonical-only.
"""
from __future__ import annotations

from pathlib import Path

from schema_v12 import CATEGORY_FIELDS, MAPPING_FIELDS, SOURCE_FIELDS, read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M020"
BATCH = ROOT / "data/research/batches/batch_02"

# Historical auto-projections whose old category disappeared or whose 2026 routing
# materially changed.  Keep them as CATEGORY_LEVEL/UNREVIEWED; this is not a second
# copy of the APP_READY audit.
CURRENT_BATCH_CATEGORY = {
    "I027": "C-M020-02",  # dry cells -> 2026 不燃・粗大ごみ
    "I030": "C-M020-02",  # fluorescent tube -> 不燃・粗大ごみ, separately bagged
    "I033": "C-M020-02",  # lighter -> 不燃・粗大ごみ, separately bagged
    "I038": "C-M020-16",  # household PC -> used small appliance recycling
}


def main() -> None:
    batch_sources = BATCH / "batch_02_sources.csv"
    _, source_rows = read_csv(batch_sources)
    source_rows = [
        row for row in source_rows
        if not (row.get("municipality_id") == MID and row.get("source_id", "").startswith("IS-"))
    ]
    write_csv(
        batch_sources, SOURCE_FIELDS,
        sorted(source_rows, key=lambda r: (r["municipality_id"], r["source_id"])),
    )

    canonical_categories_path = ROOT / "data/research/02_categories_master.csv"
    batch_categories_path = BATCH / "batch_02_categories.csv"
    category_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for path in [canonical_categories_path, batch_categories_path]:
        _, categories = read_csv(path)
        for row in categories:
            if row.get("municipality_id") == MID and row.get("category_id") == "C-M020-10":
                row["collection_channel"] = ""
            if row.get("municipality_id") == MID:
                category_by_key[(MID, row["category_id"])] = dict(row)
        write_csv(path, CATEGORY_FIELDS, categories)

    # Re-bind only the Batch 02 auto-projection layer to the refreshed category
    # snapshot.  No item-specific source is claimed here.
    mapping_path = BATCH / "batch_02_item_mapping.csv"
    _, mappings = read_csv(mapping_path)
    refreshed = 0
    rerouted = 0
    for row in mappings:
        if row.get("municipality_id") != MID:
            continue
        iid = row.get("internal_item_id", "")
        target_cid = CURRENT_BATCH_CATEGORY.get(iid, row.get("category_id", ""))
        if target_cid != row.get("category_id"):
            row["category_id"] = target_cid
            rerouted += 1
        category = category_by_key.get((MID, target_cid))
        if not category or category.get("rule_status") != "CURRENT":
            raise ValueError(f"M020 Batch 02 initial mapping points to non-current category: {iid}/{target_cid}")
        row["分別区分正式名称"] = category["自治体正式名称"]
        row["自治体収集外"] = category["自治体収集外か"]
        row["rule_status"] = category["rule_status"]
        row["effective_from"] = category["effective_from"]
        row["effective_to"] = category["effective_to"]
        row["category_source_id"] = category["source_id"]
        row["category_source_url"] = category["出典URL"]
        row["category_source_locator"] = category["出典ページ・該当箇所"]
        # These remain the historical machine-generated category-level layer.
        row["item_evidence_source_id"] = ""
        row["item_evidence_url"] = ""
        row["item_evidence_locator"] = ""
        row["mapping_status"] = "INITIAL_REVIEW_REQUIRED"
        row["evidence_scope"] = "CATEGORY_LEVEL"
        row["branch_review_status"] = "UNREVIEWED"
        row["reviewed_date"] = ""
        row["reviewed_by"] = ""
        refreshed += 1
    write_csv(mapping_path, MAPPING_FIELDS, mappings)

    print(
        "M020_APP_READY_NORMALIZED "
        f"batch_item_sources=canonical_only pet_channel=explicitly_unspecified "
        f"batch_initial_mappings_refreshed={refreshed} rerouted={rerouted}"
    )


if __name__ == "__main__":
    main()
