#!/usr/bin/env python3
"""Patch M106 mobile-battery lesson truth to the current household-waste rule.

Akita Takata City's Environmental Policy Division currently lists small
rechargeable batteries as hazardous waste.  The older/parallel Fire Department
page still directs lithium-ion products to retailers/recyclers.  For the
household garbage lesson, the current household-waste collection rule is the
scoring source; the conflicting Fire Department page is retained as secondary
evidence, not as the learner answer.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data/research/lesson_readiness/m106_item_review.csv"
PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
CHECKED_DATE = "2026-09-01"
REVIEWER = "OPENAI_M106_MOBILE_BATTERY_FACTCHECK_V1"
HOUSEHOLD_URL = "https://www.akitakata.jp/ja/shisei/section/siminseikatu/gomi22/"
FIRE_URL = "https://www.akitakata.jp/ja/shisei/section/119/m148-copy-5/"


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def patch_review() -> None:
    fields, rows = read(REVIEW)
    targets = [r for r in rows if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029" and r.get("branch_order") == "1"]
    if len(targets) != 1:
        raise ValueError(f"expected exactly one M106/I029 scoring branch, got {len(targets)}")
    row = targets[0]
    row.update({
        "official_item_wording": "モバイルバッテリー（小型充電式電池）",
        "category_id": "C-M106-12",
        "category_name": "有害ごみ",
        "condition": "家庭から廃棄するリチウムイオン電池を内蔵したモバイルバッテリー",
        "preparation": "有害ごみ専用収集袋で小型充電式電池として出す",
        "exception_destination": "販売店・リサイクル業者への回収案内もあるため、異常品や個別条件は市へ確認する",
        "evidence_basis": "OFFICIAL_RULE_DERIVED",
        "item_evidence_source_id": "S-M106-01",
        "item_evidence_url": HOUSEHOLD_URL,
        "item_evidence_locator": "有害ごみ欄『小型充電式電池』",
        "branch_review_status": "COMPLETE",
        "checked_date": CHECKED_DATE,
        "reviewer": REVIEWER,
        "note": "環境政策課の現行家庭ごみルールを教材正答として優先。消防本部の販売店回収案内は競合する補助情報として保持。",
        "scoring_branch": "TRUE",
        "exception_evidence_source_id": "S-M106-02",
        "exception_evidence_url": FIRE_URL,
        "exception_evidence_locator": "3.廃棄方法（販売店・リサイクル業者への引取案内）",
    })
    write(REVIEW, fields, rows)


def patch_projection() -> None:
    fields, rows = read(PROJECTION)
    targets = [r for r in rows if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029"]
    if len(targets) != 1:
        raise ValueError(f"expected exactly one M106/I029 projection, got {len(targets)}")
    targets[0].update({
        "teaching_box_id": "TB-M106-ON-06",
        "projection_kind": "OFFICIAL_CATEGORY",
        "category_id": "C-M106-12",
        "review_status": "COMPLETE",
        "note": "現行家庭ごみルールの小型充電式電池＝有害ごみへ投影。",
    })
    write(PROJECTION, fields, rows)


def patch_boxes() -> None:
    fields, rows = read(BOXES)
    rows = [r for r in rows if not (r.get("municipality_id") == "M106" and r.get("teaching_box_id") == "TB-M106-ON-07")]
    for row in rows:
        if row.get("municipality_id") != "M106" or row.get("class_mode") != "ONLINE_CLASS":
            continue
        if row.get("teaching_box_id") == "TB-M106-ON-08":
            row["display_order"] = "7"
        elif row.get("teaching_box_id") == "TB-M106-ON-09":
            row["display_order"] = "8"
    write(BOXES, fields, rows)


def patch_scope() -> None:
    fields, rows = read(SCOPE)
    targets = [r for r in rows if r.get("municipality_id") == "M106"]
    if len(targets) != 1:
        raise ValueError(f"expected exactly one M106 scope row, got {len(targets)}")
    targets[0]["note"] = "画像10品目の全条件枝COMPLETE。I029モバイルバッテリーは現行家庭ごみルールに基づき有害ごみへ投影。40品目APP_READYではない"
    write(SCOPE, fields, rows)


def main() -> int:
    patch_review()
    patch_projection()
    patch_boxes()
    patch_scope()
    print("M106_MOBILE_BATTERY_FACTFIX_APPLIED category=C-M106-12 box=TB-M106-ON-06")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
