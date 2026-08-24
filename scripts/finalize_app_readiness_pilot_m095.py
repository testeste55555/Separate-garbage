#!/usr/bin/env python3
"""Finalize M095 category-completeness metadata after adding APP reference routes."""

from __future__ import annotations

from pathlib import Path

from schema_v12 import (
    CATEGORY_REVIEW_EVIDENCE_FIELDS, MUNICIPALITY_FIELDS, read_csv, write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data/research"
MID = "M095"
REVIEW_ID = "CR-M095-CATEGORY-COVERAGE"
CHECKED = "2026-08-24"
REVIEWER = "OPENAI_CODEX_M095_APP_READINESS_V1"
BASIS = (
    "令和8年度の住民向け7収集区分を全件照合し、現行公式の小型家電回収ボックス経路を"
    "追加確認。CURRENTかつEXCLUDED_NOTICEでない公式葉は8区分。"
    "『市で収集しないごみ』はEXCLUDED_NOTICEのため件数外。"
)


def update_municipalities(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    found = False
    for row in rows:
        if row.get("municipality_id") != MID:
            continue
        found = True
        row["reviewed_category_count"] = "8"
        row["category_count_basis"] = BASIS
        row["category_count_verified"] = "TRUE"
        row["category_count_check_status"] = "MANUAL_INDEX_REVIEW"
        row["category_count_review_id"] = REVIEW_ID
        row["category_count_reviewed_date"] = CHECKED
        row["category_count_reviewed_by"] = REVIEWER
        row["最終確認日"] = CHECKED
        note = row.get("備考", "")
        addition = "APP readinessで小型家電回収ボックスを現行REFERENCE_ONLY区分として追加確認。"
        if addition not in note:
            row["備考"] = (note.rstrip("。") + "。" + addition) if note else addition
    if not found:
        raise AssertionError("M095 municipality row missing")
    return rows


def update_evidence(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    evidence_id = "CRE-M095-03"
    by_id = {row.get("review_evidence_id", ""): row for row in rows}
    by_id[evidence_id] = {
        "review_evidence_id": evidence_id,
        "review_id": REVIEW_ID,
        "municipality_id": MID,
        "source_id": "S-M095-04",
        "locator": "市内18箇所の小型家電回収ボックス／回収対象・対象外・投入口40cm×20cm",
        "evidence_role": "SUPPLEMENTAL_INDEX",
        "notes": "2026-08-24 M095 APP readinessで現行の代替回収経路をcategory completenessへ追加確認",
    }
    return sorted(
        by_id.values(),
        key=lambda row: (row.get("municipality_id", ""), row.get("review_id", ""), row.get("review_evidence_id", "")),
    )


def main() -> None:
    municipality_path = RESEARCH / "04_municipalities_research.csv"
    evidence_path = RESEARCH / "08_category_review_evidence.csv"
    _, municipalities = read_csv(municipality_path)
    _, evidence = read_csv(evidence_path)
    write_csv(municipality_path, MUNICIPALITY_FIELDS, update_municipalities(municipalities))
    write_csv(evidence_path, CATEGORY_REVIEW_EVIDENCE_FIELDS, update_evidence(evidence))

    batch = RESEARCH / "batches/batch_10"
    batch_municipality_path = batch / "batch_10_municipalities.csv"
    batch_evidence_path = batch / "batch_10_category_review_evidence.csv"
    _, batch_municipalities = read_csv(batch_municipality_path)
    _, batch_evidence = read_csv(batch_evidence_path)
    write_csv(batch_municipality_path, MUNICIPALITY_FIELDS, update_municipalities(batch_municipalities))
    write_csv(batch_evidence_path, CATEGORY_REVIEW_EVIDENCE_FIELDS, update_evidence(batch_evidence))
    print("M095_CATEGORY_REVIEW_FINALIZED reviewed_leaf_count=8 supplemental_evidence=CRE-M095-03")


if __name__ == "__main__":
    main()
