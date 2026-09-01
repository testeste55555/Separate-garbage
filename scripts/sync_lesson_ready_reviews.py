#!/usr/bin/env python3
"""Project LESSON_READY_10 review grids into canonical mapping and coverage data.

The review CSV is the human-audited input.  This generic synchronizer deliberately
does not create APP_READY claims: lesson-ready pairs stay VERIFIED in the canonical
40-item matrix while carrying COMPLETE branch review metadata.
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

from schema_v12 import COVERAGE_FIELDS, MAPPING_FIELDS, read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
MAPPING_PATH = ROOT / "data/research/05_item_mapping_master.csv"
COVERAGE_PATH = ROOT / "data/research/07_item_mapping_coverage.csv"
CATEGORY_PATH = ROOT / "data/research/02_categories_master.csv"
IMAGE_MAPPING_PATH = ROOT / "data/app/item_image_mapping_pilot_top8.csv"

LESSON_STATUS = "LESSON_READY_10"
IMAGE_ITEM_ORDER = ["I001", "I007", "I013", "I004", "I006", "I031", "I029", "I014", "I033", "I017"]
REVIEW_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "canonical_name", "display_name",
    "official_item_wording", "category_id", "category_name", "condition", "preparation",
    "exception_destination", "evidence_basis", "item_evidence_source_id", "item_evidence_url",
    "item_evidence_locator", "branch_review_status", "checked_date", "reviewer", "note",
]


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def stable_mapping_id(
    municipality_id: str,
    item_id: str,
    branch_order: str,
    category_id: str,
    existing_rows: list[dict[str, str]],
) -> str:
    for row in existing_rows:
        if row.get("branch_order") == branch_order and row.get("category_id") == category_id:
            return row["mapping_id"]
    same_branch = [row for row in existing_rows if row.get("branch_order") == branch_order]
    if len(same_branch) == 1:
        # mapping_id is a stable record identity. A reviewed category correction must not
        # orphan the original completed-batch key merely because its destination changed.
        return same_branch[0]["mapping_id"]
    return f"MAP-{municipality_id}-{item_id}-LR10-{int(branch_order):02d}"


def synchronize() -> tuple[int, int, int]:
    scope = [row for row in csv_rows(SCOPE_PATH) if row.get("scoring_status") == LESSON_STATUS]
    _, mappings = read_csv(MAPPING_PATH)
    _, coverage = read_csv(COVERAGE_PATH)
    _, categories = read_csv(CATEGORY_PATH)
    category_by_key = {(row["municipality_id"], row["category_id"]): row for row in categories}
    existing_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mappings:
        existing_by_pair[(row["municipality_id"], row["internal_item_id"])].append(row)

    replacement_by_pair: dict[tuple[str, str], list[dict[str, str]]] = {}
    review_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for scope_row in scope:
        review_path = ROOT / scope_row["review_source"]
        review_fields, review_rows = read_csv(review_path)
        if review_fields[: len(REVIEW_FIELDS)] != REVIEW_FIELDS:
            raise ValueError(f"unexpected lesson review header: {review_path}")
        for row in review_rows:
            if row.get("municipality_id") != scope_row.get("municipality_id"):
                raise ValueError(f"review municipality mismatch: {review_path}")
            review_by_pair[(row["municipality_id"], row["internal_item_id"])].append(row)

    for pair, review_rows in review_by_pair.items():
        mid, iid = pair
        review_rows.sort(key=lambda row: int(row["branch_order"]))
        old_rows = existing_by_pair.get(pair, [])
        projected: list[dict[str, str]] = []
        for row in review_rows:
            category = category_by_key[(mid, row["category_id"])]
            projected.append({
                "mapping_id": stable_mapping_id(mid, iid, row["branch_order"], row["category_id"], old_rows),
                "municipality_id": mid,
                "internal_item_id": iid,
                "branch_order": row["branch_order"],
                "自治体での品目表記": row["official_item_wording"],
                "category_id": row["category_id"],
                "分別区分正式名称": row["category_name"],
                "条件": row["condition"],
                "前処理": row["preparation"],
                "例外分別先": row["exception_destination"],
                "自治体収集外": category["自治体収集外か"],
                "rule_status": category["rule_status"],
                "effective_from": category["effective_from"],
                "effective_to": category["effective_to"],
                "category_source_id": category["source_id"],
                "category_source_url": category["出典URL"],
                "category_source_locator": category["出典ページ・該当箇所"],
                "item_evidence_source_id": row["item_evidence_source_id"],
                "item_evidence_url": row["item_evidence_url"],
                "item_evidence_locator": row["item_evidence_locator"],
                "確認日": row["checked_date"],
                "mapping_status": "VERIFIED",
                "evidence_scope": "ITEM_SPECIFIC",
                "branch_review_status": "COMPLETE",
                "reviewed_date": row["checked_date"],
                "reviewed_by": row["reviewer"],
                "備考": "LESSON_READY_10の全条件枝レビュー済み。40品目APP_READYとは独立。",
            })
        replacement_by_pair[pair] = projected

    new_mappings = [
        row for row in mappings
        if (row["municipality_id"], row["internal_item_id"]) not in replacement_by_pair
    ]
    for pair in sorted(replacement_by_pair):
        new_mappings.extend(replacement_by_pair[pair])
    new_mappings.sort(key=lambda row: (
        row["municipality_id"], row["internal_item_id"], int(row["branch_order"]), row["mapping_id"]
    ))

    coverage_by_pair = {(row["municipality_id"], row["internal_item_id"]): row for row in coverage}
    for pair, review_rows in review_by_pair.items():
        review_rows.sort(key=lambda row: int(row["branch_order"]))
        first = review_rows[0]
        coverage_by_pair[pair] = {
            "municipality_id": pair[0],
            "internal_item_id": pair[1],
            "coverage_status": "VERIFIED",
            "mapping_branch_count": str(len(review_rows)),
            "branch_completeness_confirmed": "TRUE",
            "evidence_scope": "ITEM_SPECIFIC",
            "item_evidence_source_id": first["item_evidence_source_id"],
            "item_evidence_url": first["item_evidence_url"],
            "item_evidence_locator": first["item_evidence_locator"],
            "reviewed_date": first["checked_date"],
            "reviewed_by": first["reviewer"],
            "notes": "LESSON_READY_10の全条件枝COMPLETE。残り30品目未完のためAPP_READYではない。",
        }
    new_coverage = [coverage_by_pair[pair] for pair in sorted(coverage_by_pair)]

    image_fields, image_rows = read_csv(IMAGE_MAPPING_PATH)
    scoring_branch_by_pair: dict[tuple[str, str], dict[str, str]] = {}
    for pair, review_rows in review_by_pair.items():
        scoring = [row for row in review_rows if row.get("scoring_branch") == "TRUE"]
        if len(scoring) != 1:
            raise ValueError(f"{pair} must have exactly one scoring branch")
        scoring_branch_by_pair[pair] = scoring[0]
    scope_name_by_mid = {row["municipality_id"]: row["municipality_name"] for row in csv_rows(SCOPE_PATH)}
    existing_image_pairs = {(row.get("municipality_id", ""), row.get("internal_item_id", "")) for row in image_rows}
    for pair, scoring in sorted(scoring_branch_by_pair.items()):
        if pair in existing_image_pairs:
            continue
        mid, iid = pair
        image_rows.append({
            "pair_order": "0",
            "municipality_id": mid,
            "municipality_name": scope_name_by_mid[mid],
            "internal_item_id": iid,
            "canonical_name": scoring["canonical_name"],
            "display_name": scoring["display_name"],
            "review_status": "VERIFIED",
            "evidence_basis": scoring["evidence_basis"],
            "category_id": scoring["category_id"],
            "category_name": scoring["category_name"],
            "condition": scoring["condition"],
            "preparation": scoring["preparation"],
            "exception_destination": scoring["exception_destination"],
            "item_evidence_source_id": scoring["item_evidence_source_id"],
            "item_evidence_url": scoring["item_evidence_url"],
            "item_evidence_locator": scoring["item_evidence_locator"],
            "checked_date": scoring["checked_date"],
            "reviewer": scoring["reviewer"],
            "note": "LESSON_READY_10のscoring_branchと同期。詳細条件は教師用reviewに保持。",
        })
        existing_image_pairs.add(pair)

    image_updates = 0
    for row in image_rows:
        pair = (row.get("municipality_id", ""), row.get("internal_item_id", ""))
        scoring = scoring_branch_by_pair.get(pair)
        if not scoring:
            continue
        row.update({
            "review_status": "VERIFIED",
            "evidence_basis": scoring["evidence_basis"],
            "category_id": scoring["category_id"],
            "category_name": scoring["category_name"],
            "condition": scoring["condition"],
            "preparation": scoring["preparation"],
            "exception_destination": scoring["exception_destination"],
            "item_evidence_source_id": scoring["item_evidence_source_id"],
            "item_evidence_url": scoring["item_evidence_url"],
            "item_evidence_locator": scoring["item_evidence_locator"],
            "checked_date": scoring["checked_date"],
            "reviewer": scoring["reviewer"],
            "note": "LESSON_READY_10のscoring_branchと同期。詳細条件は教師用reviewに保持。",
        })
        image_updates += 1

    scope_order = {row["municipality_id"]: index for index, row in enumerate(csv_rows(SCOPE_PATH))}
    item_order = {iid: index for index, iid in enumerate(IMAGE_ITEM_ORDER)}
    image_rows.sort(key=lambda row: (scope_order.get(row.get("municipality_id", ""), 9999), item_order.get(row.get("internal_item_id", ""), 9999)))
    for order, row in enumerate(image_rows, 1):
        row["pair_order"] = str(order)

    write_csv(MAPPING_PATH, MAPPING_FIELDS, new_mappings)
    write_csv(COVERAGE_PATH, COVERAGE_FIELDS, new_coverage)
    write_csv(IMAGE_MAPPING_PATH, image_fields, image_rows)
    return len(review_by_pair), sum(len(rows) for rows in review_by_pair.values()), image_updates


def main() -> int:
    try:
        pairs, branches, image_updates = synchronize()
    except (KeyError, ValueError) as error:
        print(f"LESSON_READY_SYNC_FAILED: {error}")
        return 1
    print(
        f"LESSON_READY_SYNCED pairs={pairs} branches={branches} "
        f"image_updates={image_updates} status=VERIFIED_COMPLETE"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
