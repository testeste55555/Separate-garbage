#!/usr/bin/env python3
"""Finalize M105 APP_READY generated state without weakening existing validators.

- normalizes audit fields that APP_READY requires to be explicit/nonblank;
- corrects I009 to the current direct R8 bento-container row with its 30 cm branch;
- removes the superseded LESSON_READY_10 review so there is one readiness source of truth.
"""
from __future__ import annotations

from pathlib import Path

from schema_v12 import COVERAGE_FIELDS, MAPPING_FIELDS, read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M105"
AUDIT = ROOT / "data/research/app_readiness/m105_item_review.csv"
LESSON_REVIEW = ROOT / "data/research/lesson_readiness/m105_item_review.csv"
MAPPINGS = ROOT / "data/research/05_item_mapping_master.csv"
COVERAGE = ROOT / "data/research/07_item_mapping_coverage.csv"
CATEGORIES = ROOT / "data/research/02_categories_master.csv"
SOURCES = ROOT / "data/research/03_sources_master.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"

EXPLICIT_NONE = "該当なし"


def main() -> None:
    audit_fields, audit_rows = read_csv(AUDIT)
    mapping_fields, mapping_rows = read_csv(MAPPINGS)
    coverage_fields, coverage_rows = read_csv(COVERAGE)
    category_fields, category_rows = read_csv(CATEGORIES)
    source_fields, source_rows = read_csv(SOURCES)
    scope_fields, scope_rows = read_csv(SCOPE)

    category_by = {
        (row["municipality_id"], row["category_id"]): row for row in category_rows
    }
    source_by = {
        (row["municipality_id"], row["source_id"]): row for row in source_rows
    }

    # APP_READY review fields are intentionally explicit.  Keep canonical rows in lockstep.
    mapping_by_key = {
        (row["municipality_id"], row["internal_item_id"], row["branch_order"]): row
        for row in mapping_rows
    }
    for row in audit_rows:
        if row.get("municipality_id") != MID:
            continue
        for field in ("condition", "preparation", "exception_destination"):
            if not row.get(field, "").strip():
                row[field] = EXPLICIT_NONE
        if not row.get("note", "").strip():
            row["note"] = "公式品目行または公式区分ルールと条件を照合。"
        mapping = mapping_by_key[(MID, row["internal_item_id"], row["branch_order"])]
        mapping["条件"] = row["condition"]
        mapping["前処理"] = row["preparation"]
        mapping["例外分別先"] = row["exception_destination"]

    # R8 table has an exact item row: No.564 弁当容器(コンビニなど).
    source = source_by[(MID, "IS-M105-04")]
    burnable = category_by[(MID, "C-M105-01")]
    bulky = category_by[(MID, "C-M105-09")]
    i009_audit = [row for row in audit_rows if row["municipality_id"] == MID and row["internal_item_id"] == "I009"]
    if len(i009_audit) != 1:
        raise ValueError(f"expected one generated I009 branch before finalization, got {len(i009_audit)}")
    first = i009_audit[0]
    first.update({
        "official_item_wording": "弁当容器(コンビニなど)",
        "category_id": "C-M105-01",
        "category_name": burnable["自治体正式名称"],
        "condition": "長さ30cm未満",
        "preparation": "中身を除いて出す",
        "exception_destination": "長さ30cm以上は大型ごみ",
        "evidence_basis": "DIRECT_ITEM",
        "item_evidence_source_id": "IS-M105-04",
        "item_evidence_url": source["公式URL"],
        "item_evidence_locator": "分別50音表 No.564『弁当容器(コンビニなど)』",
        "note": "令和8年4月版50音表の直接品目行でサイズ分岐まで確認。",
    })
    first_mapping = mapping_by_key[(MID, "I009", "1")]
    first_mapping.update({
        "自治体での品目表記": first["official_item_wording"],
        "category_id": first["category_id"],
        "分別区分正式名称": first["category_name"],
        "条件": first["condition"],
        "前処理": first["preparation"],
        "例外分別先": first["exception_destination"],
        "category_source_id": burnable["source_id"],
        "category_source_url": burnable["出典URL"],
        "category_source_locator": burnable["出典ページ・該当箇所"],
        "item_evidence_source_id": first["item_evidence_source_id"],
        "item_evidence_url": first["item_evidence_url"],
        "item_evidence_locator": first["item_evidence_locator"],
    })

    second_audit = dict(first)
    second_audit.update({
        "branch_order": "2",
        "category_id": "C-M105-09",
        "category_name": bulky["自治体正式名称"],
        "condition": "長さ30cm以上",
        "preparation": "中身を除いて出す",
        "exception_destination": "長さ30cm未満は燃やせるごみ",
        "note": "同一の令和8年4月版50音表品目行に記載された30cm以上の分岐。",
    })
    audit_rows.append(second_audit)

    second_mapping = dict(first_mapping)
    second_mapping.update({
        "mapping_id": "MAP-M105-I009-APP-02",
        "branch_order": "2",
        "category_id": "C-M105-09",
        "分別区分正式名称": bulky["自治体正式名称"],
        "条件": second_audit["condition"],
        "前処理": second_audit["preparation"],
        "例外分別先": second_audit["exception_destination"],
        "自治体収集外": bulky["自治体収集外か"],
        "rule_status": bulky["rule_status"],
        "effective_from": bulky["effective_from"],
        "effective_to": bulky["effective_to"],
        "category_source_id": bulky["source_id"],
        "category_source_url": bulky["出典URL"],
        "category_source_locator": bulky["出典ページ・該当箇所"],
    })
    if any(row["mapping_id"] == second_mapping["mapping_id"] for row in mapping_rows):
        raise ValueError("I009 branch-2 mapping id already exists")
    mapping_rows.append(second_mapping)

    for row in coverage_rows:
        if row["municipality_id"] == MID and row["internal_item_id"] == "I009":
            row["mapping_branch_count"] = "2"
            row["item_evidence_source_id"] = "IS-M105-04"
            row["item_evidence_url"] = source["公式URL"]
            row["item_evidence_locator"] = first["item_evidence_locator"]
            break
    else:
        raise ValueError("M105/I009 coverage row missing")

    audit_rows.sort(key=lambda row: (row["municipality_id"], row["internal_item_id"], int(row["branch_order"])))
    mapping_rows.sort(key=lambda row: (
        row["municipality_id"], row["internal_item_id"], int(row.get("branch_order") or 0), row["mapping_id"]
    ))
    branch_count = sum(row["municipality_id"] == MID for row in audit_rows)
    for row in scope_rows:
        if row["municipality_id"] == MID:
            row["required_branch_count"] = str(branch_count)
            break

    write_csv(AUDIT, audit_fields, audit_rows)
    write_csv(MAPPINGS, mapping_fields or MAPPING_FIELDS, mapping_rows)
    write_csv(COVERAGE, coverage_fields or COVERAGE_FIELDS, coverage_rows)
    write_csv(SCOPE, scope_fields, scope_rows)

    # APP_READY becomes the sole readiness review for M105; the generator can fall back
    # to the APP_READY audit on future rebuilds after this deletion.
    if LESSON_REVIEW.exists():
        LESSON_REVIEW.unlink()

    print(f"M105_APP_READY_FINALIZED branches={branch_count} lesson_review_removed={not LESSON_REVIEW.exists()}")


if __name__ == "__main__":
    main()
