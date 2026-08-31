#!/usr/bin/env python3
"""Keep Batch 01's historical M009 category-level projections aligned with current categories.

Batch 01 originally machine-extracted I037 (家電4品目) twice: once as 粗大ごみ and
once as the general not-collected route. The official guide is explicit that these four
appliances are not accepted by the clean center, so the rough-garbage candidate is a
stale machine-extraction artifact, not a real condition branch. Collapse it here rather
than carrying a false branch into the APP_READY audit.
"""
from __future__ import annotations

from pathlib import Path

from schema_v12 import COVERAGE_FIELDS, MAPPING_FIELDS, read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M009"
BATCH = ROOT / "data/research/batches/batch_01"


def main() -> None:
    _, categories = read_csv(BATCH / "batch_01_categories.csv")
    category_by = {(r["municipality_id"], r["category_id"]): r for r in categories}
    path = BATCH / "batch_01_item_mapping.csv"
    _, mappings = read_csv(path)

    # Keep the first stable key so canonical merge identity remains deterministic, but
    # correct its category to the official not-collected route and drop the stale twin.
    m009_i037 = [r for r in mappings if r.get("municipality_id") == MID and r.get("internal_item_id") == "I037"]
    keep_i037_id = sorted((r.get("mapping_id", "") for r in m009_i037))[0] if m009_i037 else ""
    mappings = [
        r for r in mappings
        if not (
            r.get("municipality_id") == MID and r.get("internal_item_id") == "I037"
            and r.get("mapping_id") != keep_i037_id
        )
    ]

    refreshed = 0
    for row in mappings:
        if row.get("municipality_id") != MID:
            continue
        if row.get("internal_item_id") == "I037":
            row["category_id"] = "C-M009-09"
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
        if row.get("internal_item_id") == "I037":
            row["条件"] = "家電リサイクル法対象4品目"
            row["前処理"] = "クリーンセンターへ出さず、指定のリサイクル手続を行う"
            row["例外分別先"] = "販売店・指定引取場所等"
        refreshed += 1
    write_csv(path, MAPPING_FIELDS, mappings)

    coverage_path = BATCH / "batch_01_item_coverage.csv"
    _, coverage = read_csv(coverage_path)
    for row in coverage:
        if row.get("municipality_id") == MID and row.get("internal_item_id") == "I037":
            row["mapping_branch_count"] = "1"
            row["coverage_status"] = "MAPPED_INITIAL"
            row["branch_completeness_confirmed"] = "FALSE"
            row["evidence_scope"] = "CATEGORY_LEVEL"
            row["item_evidence_source_id"] = ""
            row["item_evidence_url"] = ""
            row["item_evidence_locator"] = ""
            row["reviewed_date"] = ""
            row["reviewed_by"] = ""
            row["notes"] = "旧機械抽出の粗大ごみ候補を除外し、公式の家電4品目収集外ルート1枝へ正規化。品目別APP_READY根拠はcanonical側で保持。"
    write_csv(coverage_path, COVERAGE_FIELDS, coverage)

    print(
        f"M009_APP_READY_NORMALIZED batch_initial_mappings_refreshed={refreshed} "
        f"i037_stale_branch_collapsed={max(0, len(m009_i037)-1)}"
    )


if __name__ == "__main__":
    main()
