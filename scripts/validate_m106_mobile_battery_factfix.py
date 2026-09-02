#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOUSEHOLD_URL = "https://www.akitakata.jp/ja/shisei/section/siminseikatu/gomi22/"


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_state(data: dict[str, list[dict[str, str]]]) -> list[str]:
    errors: list[str] = []

    review = [r for r in data["review"] if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029" and r.get("branch_order") == "1"]
    if len(review) != 1:
        errors.append("review must contain exactly one M106/I029 branch 1")
    else:
        r = review[0]
        expected = {
            "category_id": "C-M106-12",
            "category_name": "有害ごみ",
            "scoring_branch": "TRUE",
            "item_evidence_url": HOUSEHOLD_URL,
            "evidence_basis": "OFFICIAL_RULE_DERIVED",
        }
        for key, value in expected.items():
            if r.get(key) != value:
                errors.append(f"review {key} must be {value!r}, got {r.get(key)!r}")
        if "小型充電式電池" not in r.get("item_evidence_locator", ""):
            errors.append("review locator must point to 小型充電式電池")
        if "m148-copy-5" not in r.get("exception_evidence_url", ""):
            errors.append("review must retain Fire Department conflicting guidance as secondary evidence")

    projection = [r for r in data["projection"] if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029"]
    if len(projection) != 1:
        errors.append("projection must contain exactly one M106/I029 row")
    else:
        p = projection[0]
        if p.get("category_id") != "C-M106-12":
            errors.append("M106/I029 projection must use C-M106-12")
        if p.get("teaching_box_id") != "TB-M106-ON-06":
            errors.append("M106/I029 projection must use hazardous box TB-M106-ON-06")
        if p.get("projection_kind") != "OFFICIAL_CATEGORY":
            errors.append("M106/I029 projection must be OFFICIAL_CATEGORY")

    image = [r for r in data["image"] if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029"]
    if len(image) != 1:
        errors.append("image mapping must contain exactly one M106/I029 row")
    else:
        i = image[0]
        if i.get("category_id") != "C-M106-12" or i.get("category_name") != "有害ごみ":
            errors.append("M106/I029 image mapping must resolve to 有害ごみ")
        if i.get("item_evidence_url") != HOUSEHOLD_URL:
            errors.append("M106/I029 image mapping must use current household-waste source")

    mapping = [r for r in data["mapping"] if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029" and r.get("branch_order") == "1"]
    if len(mapping) != 1:
        errors.append("canonical mapping must contain exactly one M106/I029 branch 1")
    else:
        m = mapping[0]
        if m.get("category_id") != "C-M106-12" or m.get("分別区分正式名称") != "有害ごみ":
            errors.append("canonical M106/I029 branch 1 must resolve to 有害ごみ")
        if m.get("item_evidence_url") != HOUSEHOLD_URL:
            errors.append("canonical M106/I029 must use current household-waste source")

    coverage = [r for r in data["coverage"] if r.get("municipality_id") == "M106" and r.get("internal_item_id") == "I029"]
    if len(coverage) != 1:
        errors.append("coverage must contain exactly one M106/I029 row")
    else:
        c = coverage[0]
        if c.get("coverage_status") != "VERIFIED" or c.get("branch_completeness_confirmed") != "TRUE":
            errors.append("M106/I029 coverage must remain VERIFIED and branch-complete")

    boxes = [r for r in data["boxes"] if r.get("municipality_id") == "M106" and r.get("class_mode") == "ONLINE_CLASS"]
    if any(r.get("teaching_box_id") == "TB-M106-ON-07" for r in boxes):
        errors.append("obsolete M106 回収・確認 box TB-M106-ON-07 must not remain learner-visible")
    hazardous = [r for r in boxes if r.get("teaching_box_id") == "TB-M106-ON-06"]
    if len(hazardous) != 1 or hazardous[0].get("category_id") != "C-M106-12":
        errors.append("M106 online hazardous box must remain C-M106-12")

    scope = [r for r in data["scope"] if r.get("municipality_id") == "M106"]
    if len(scope) != 1 or "有害ごみ" not in scope[0].get("note", ""):
        errors.append("M106 lesson scope note must record I029 hazardous projection")

    return errors


def load_state() -> dict[str, list[dict[str, str]]]:
    return {
        "review": rows("data/research/lesson_readiness/m106_item_review.csv"),
        "projection": rows("data/app/lesson_item_scoring_projection.csv"),
        "image": rows("data/app/item_image_mapping_pilot_top8.csv"),
        "mapping": rows("data/research/05_item_mapping_master.csv"),
        "coverage": rows("data/research/07_item_mapping_coverage.csv"),
        "boxes": rows("data/app/lesson_teaching_boxes.csv"),
        "scope": rows("data/app/lesson_mode_app_ready_scope.csv"),
    }


def main() -> int:
    errors = validate_state(load_state())
    if errors:
        print("M106_MOBILE_BATTERY_FACTFIX_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("M106_MOBILE_BATTERY_FACTFIX_VALIDATION_PASSED category=C-M106-12 box=TB-M106-ON-06")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
