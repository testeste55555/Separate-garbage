#!/usr/bin/env python3
"""Validate the guarded 15-item learner UI contract."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "data/app/item_image_assets.csv"
SCORING = ROOT / "data/app/lesson_supplemental_item_scoring.csv"
BOXES = ROOT / "data/app/lesson_supplemental_teaching_boxes.csv"
APP = ROOT / "app/app.js"
ASSET_DIR = ROOT / "app/assets/items"

CORE = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}
SUP_ORDER = ["I002", "I003", "I027", "I018", "I010"]
SUP = set(SUP_ORDER)
LESSON_15 = CORE | SUP
TARGETS = {"M009", "M020", "M094", "M098", "M099", "M105"}
EXPECTED_GROUPS = {
    "M098": {"LV-M098-01"},
    "M099": {"LV-M099-01", "LV-M099-02", "LV-M099-03"},
}
EXPECTED_FILES = {
    "I002": "I002_pet_cap.webp",
    "I003": "I003_pet_label.webp",
    "I027": "I027_dry_battery.webp",
    "I018": "I018_food_waste.webp",
    "I010": "I010_snack_bag.webp",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_records(
    asset_rows: list[dict[str, str]],
    scoring_rows: list[dict[str, str]],
    box_rows: list[dict[str, str]],
    app_text: str,
    *,
    check_asset_files: bool = True,
) -> list[str]:
    errors: list[str] = []
    asset_ids = [row.get("internal_item_id", "").strip() for row in asset_rows]
    if len(asset_ids) != 15 or set(asset_ids) != LESSON_15:
        errors.append("image asset registry must contain exactly the formal 15 lesson items")
    if len(asset_ids) != len(set(asset_ids)):
        errors.append("image asset IDs must be unique")

    assets = {row.get("internal_item_id", "").strip(): row for row in asset_rows}
    for item_id, image_file in EXPECTED_FILES.items():
        row = assets.get(item_id)
        if not row:
            errors.append(f"{item_id}: supplemental image asset missing")
            continue
        if row.get("asset_status", "").strip() != "CONFIRMED":
            errors.append(f"{item_id}: supplemental image is not CONFIRMED")
        if row.get("image_file", "").strip() != image_file:
            errors.append(f"{item_id}: unexpected supplemental image filename")
        if check_asset_files:
            path = ASSET_DIR / image_file
            if not path.is_file():
                errors.append(f"{item_id}: image file missing")
            else:
                data = path.read_bytes()[:12]
                if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
                    errors.append(f"{item_id}: image file is not WEBP")

    actual_targets = {row.get("municipality_id", "").strip() for row in scoring_rows}
    if actual_targets != TARGETS:
        errors.append(f"supplemental scoring municipality scope mismatch: {sorted(actual_targets)}")
    if len(scoring_rows) != 40:
        errors.append(f"supplemental scoring must contain exactly 40 rows, got {len(scoring_rows)}")

    standard: dict[str, list[dict[str, str]]] = defaultdict(list)
    variants: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in scoring_rows:
        mid = row.get("municipality_id", "").strip()
        gid = row.get("lesson_variant_group_id", "").strip()
        item_id = row.get("internal_item_id", "").strip()
        if item_id not in SUP:
            errors.append(f"{mid}/{gid}: non-supplemental item leaked into supplemental scoring: {item_id}")
        if row.get("review_status", "").strip() != "COMPLETE":
            errors.append(f"{mid}/{gid}/{item_id}: scoring row is not COMPLETE")
        expected_order = SUP_ORDER.index(item_id) + 11 if item_id in SUP else None
        if expected_order is not None and row.get("display_order", "").strip() != str(expected_order):
            errors.append(f"{mid}/{gid}/{item_id}: display order mismatch")
        if mid in EXPECTED_GROUPS:
            if gid not in EXPECTED_GROUPS[mid]:
                errors.append(f"{mid}/{item_id}: variant group mismatch: {gid}")
            variants[(mid, gid)].append(row)
        else:
            if gid:
                errors.append(f"{mid}/{item_id}: unexpected variant group {gid}")
            standard[mid].append(row)

    for mid in TARGETS - set(EXPECTED_GROUPS):
        rows = standard.get(mid, [])
        if len(rows) != 5 or {row.get("internal_item_id", "").strip() for row in rows} != SUP:
            errors.append(f"{mid}: standard supplemental set is not complete 5/5")
    for mid, groups in EXPECTED_GROUPS.items():
        for gid in groups:
            rows = variants.get((mid, gid), [])
            if len(rows) != 5 or {row.get("internal_item_id", "").strip() for row in rows} != SUP:
                errors.append(f"{mid}/{gid}: variant supplemental set is not complete 5/5")

    box_groups = Counter(row.get("lesson_variant_group_id", "").strip() for row in box_rows)
    if set(box_groups) != {"LV-M098-01", "LV-M099-01", "LV-M099-02", "LV-M099-03"}:
        errors.append("supplemental box groups must be limited to M098/M099 lesson variants")
    if any(count != 1 for count in box_groups.values()) or len(box_rows) != 4:
        errors.append("each regional variant must have exactly one supplemental burnable box")
    if any(row.get("class_mode", "").strip() != "ONLINE_CLASS" for row in box_rows):
        errors.append("supplemental teaching boxes must be ONLINE_CLASS only")

    required_app_markers = [
        'lessonSupplementalScoring: "../data/app/lesson_supplemental_item_scoring.csv"',
        'lessonSupplementalBoxes: "../data/app/lesson_supplemental_teaching_boxes.csv"',
        'const SUPPLEMENTAL_IMAGE_ITEM_IDS = new Set(["I002", "I003", "I027", "I018", "I010"]);',
        'const SUPPLEMENTAL_TARGET_MUNICIPALITIES = new Set(["M009", "M020", "M094", "M098", "M099", "M105"]);',
        'function supplementalSetReady(rows)',
        'supplementalImageGateReady = [...SUPPLEMENTAL_IMAGE_ITEM_IDS].every((itemId) => assetsByItem.has(itemId));',
        'SUPPLEMENTAL_TARGET_MUNICIPALITIES.has(id) && supplementalSetReady(supplementalItems)',
        'buildLessonSupplementalData(parseCsv(supplementalScoringText), parseCsv(supplementalBoxText));',
        'const EXPECTED_LESSON_READY_ITEM_COUNT = 10;',
    ]
    for marker in required_app_markers:
        if marker not in app_text:
            errors.append(f"learner UI contract marker missing: {marker}")
    if '.(?:png|webp)$/' not in app_text:
        errors.append("learner UI image safety regex does not allow the confirmed WEBP assets")

    return errors


def validate() -> list[str]:
    return validate_records(read_rows(ASSETS), read_rows(SCORING), read_rows(BOXES), APP.read_text(encoding="utf-8"))


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL lesson 15 UI: {error}", file=sys.stderr)
        raise SystemExit(1)
    print("PASS guarded lesson 15 UI")
    print("confirmed_lesson_assets=15")
    print("supplemental_scoring_rows=40")
    print("lesson15_target_municipalities=6")


if __name__ == "__main__":
    main()
