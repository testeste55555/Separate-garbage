#!/usr/bin/env python3
"""Validate district scopes and learner-facing lesson variants for M098/M099."""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISTRICT_SCOPES = ROOT / "data/app/district_scopes.csv"
VARIANT_GROUPS = ROOT / "data/app/lesson_variant_groups.csv"
TEACHING_BOXES = ROOT / "data/app/lesson_variant_teaching_boxes.csv"
ITEM_SCORING = ROOT / "data/app/lesson_variant_item_scoring.csv"
SOURCES = ROOT / "data/research/lesson_readiness/lesson_variant_sources.csv"
MUNICIPALITIES = ROOT / "data/master/01_municipalities_master.csv"
DEFERRED = ROOT / "data/master/05_deferred_municipalities.csv"
STANDARD_SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
ASSETS = ROOT / "data/app/item_image_assets.csv"
APP_JS = ROOT / "app/app.js"
APP_HTML = ROOT / "app/index.html"

TARGETS = {"M098", "M099"}
ONLINE_CLASS_MODE = "ONLINE_CLASS"
IN_PERSON_CLASS_MODE = "IN_PERSON_CLASS"
IMAGE_ITEMS = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}
EXPECTED_GROUPS = {
    "M098": {"LV-M098-01"},
    "M099": {"LV-M099-01", "LV-M099-02", "LV-M099-03"},
}
EXPECTED_SCOPE_TO_GROUP = {
    "DS-M098-01": "LV-M098-01",
    "DS-M098-02": "LV-M098-01",
    "DS-M098-03": "LV-M098-01",
    "DS-M098-04": "LV-M098-01",
    "DS-M098-05": "LV-M098-01",
    "DS-M098-06": "LV-M098-01",
    "DS-M099-01": "LV-M099-01",
    "DS-M099-02": "LV-M099-02",
    "DS-M099-03": "LV-M099-02",
    "DS-M099-04": "LV-M099-03",
}
EXPECTED_ANSWERS = {
    "LV-M098-01": {
        "I001": "TB-M098-01", "I004": "TB-M098-03", "I006": "TB-M098-03",
        "I007": "TB-M098-02", "I013": "TB-M098-03", "I014": "TB-M098-03",
        "I017": "TB-M098-03", "I029": "TB-M098-04", "I031": "TB-M098-04",
        "I033": "TB-M098-04",
    },
    "LV-M099-01": {
        "I001": "TB-M099-01-01", "I004": "TB-M099-01-02", "I006": "TB-M099-01-02",
        "I007": "TB-M099-01-01", "I013": "TB-M099-01-03", "I014": "TB-M099-01-03",
        "I017": "TB-M099-01-06", "I029": "TB-M099-01-05", "I031": "TB-M099-01-04",
        "I033": "TB-M099-01-05",
    },
    "LV-M099-02": {
        "I001": "TB-M099-02-01", "I004": "TB-M099-02-02", "I006": "TB-M099-02-02",
        "I007": "TB-M099-02-01", "I013": "TB-M099-02-03", "I014": "TB-M099-02-03",
        "I017": "TB-M099-02-03", "I029": "TB-M099-02-05", "I031": "TB-M099-02-04",
        "I033": "TB-M099-02-05",
    },
    "LV-M099-03": {
        "I001": "TB-M099-03-01", "I004": "TB-M099-03-02", "I006": "TB-M099-03-02",
        "I007": "TB-M099-03-01", "I013": "TB-M099-03-05", "I014": "TB-M099-03-05",
        "I017": "TB-M099-03-05", "I029": "TB-M099-03-04", "I031": "TB-M099-03-03",
        "I033": "TB-M099-03-04",
    },
}
EXPECTED_IN_PERSON_BOXES = {
    "LV-M098-01": {
        "もやせるごみ", "もやせないごみ", "容器包装プラスチック", "ペットボトル",
        "資源回収", "有害ごみ", "粗大ごみ",
    },
    "LV-M099-01": {
        "燃やせるごみ", "容器包装プラスチックごみ", "資源ごみ", "紙類",
        "不燃（破砕）ごみ", "燃やせる粗大ごみ", "使用済乾電池等", "資源回収・確認",
    },
    "LV-M099-02": {
        "燃やせるごみ", "容器包装プラスチックごみ", "資源ごみ", "紙類",
        "不燃（破砕）ごみ", "燃やせる粗大ごみ", "使用済乾電池等",
    },
    "LV-M099-03": {
        "燃やせるごみ", "容器包装プラスチックごみ", "資源ごみ",
        "不燃（破砕）ごみ", "燃やせる粗大ごみ", "使用済乾電池等", "資源回収・確認",
    },
}
CURRENT_SOURCE = {"CURRENT", "現行", "現行案内中"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def records() -> dict[str, list[dict[str, str]]]:
    return {
        "district_scopes": read_rows(DISTRICT_SCOPES),
        "variant_groups": read_rows(VARIANT_GROUPS),
        "teaching_boxes": read_rows(TEACHING_BOXES),
        "item_scoring": read_rows(ITEM_SCORING),
    }


def validate_records(data: dict[str, list[dict[str, str]]], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    scopes = data["district_scopes"]
    groups = data["variant_groups"]
    boxes = data["teaching_boxes"]
    scoring = data["item_scoring"]
    municipalities = {row["municipality_id"]: row for row in read_rows(root / MUNICIPALITIES.relative_to(ROOT))}
    sources = {
        (row["municipality_id"], row["source_id"]): row
        for row in read_rows(root / SOURCES.relative_to(ROOT))
    }
    assets = {
        row["internal_item_id"]: row
        for row in read_rows(root / ASSETS.relative_to(ROOT))
        if row.get("asset_status") == "CONFIRMED"
    }

    group_ids = [row.get("lesson_variant_group_id", "") for row in groups]
    if any(not value for value in group_ids) or len(group_ids) != len(set(group_ids)):
        errors.append("lesson variant group IDs must be unique and nonblank")
    group_by_id = {row.get("lesson_variant_group_id", ""): row for row in groups}
    actual_groups: dict[str, set[str]] = defaultdict(set)
    for row in groups:
        mid = row.get("municipality_id", "")
        gid = row.get("lesson_variant_group_id", "")
        actual_groups[mid].add(gid)
        if mid not in TARGETS or mid not in municipalities:
            errors.append(f"{gid}: unexpected or unknown municipality")
        if row.get("readiness_status") != "LESSON_READY_10":
            errors.append(f"{gid}: readiness is not LESSON_READY_10")
        if not row.get("display_name") or not row.get("display_order"):
            errors.append(f"{gid}: missing learner group display data")
    if dict(actual_groups) != EXPECTED_GROUPS:
        errors.append(f"lesson variant groups mismatch: {dict(actual_groups)}")
    if group_by_id.get("LV-M098-01", {}).get("learner_selection_required") != "FALSE":
        errors.append("M098 must enter its single lesson group without a learner region choice")
    for gid in EXPECTED_GROUPS["M099"]:
        if group_by_id.get(gid, {}).get("learner_selection_required") != "TRUE":
            errors.append(f"{gid}: M099 learner selection must remain required")

    scope_ids = [row.get("district_scope_id", "") for row in scopes]
    if any(not value for value in scope_ids) or len(scope_ids) != len(set(scope_ids)):
        errors.append("district scope IDs must be unique and nonblank")
    actual_scope_to_group = {
        row.get("district_scope_id", ""): row.get("lesson_variant_group_id", "") for row in scopes
    }
    if actual_scope_to_group != EXPECTED_SCOPE_TO_GROUP:
        errors.append(f"district scope grouping mismatch: {actual_scope_to_group}")
    for row in scopes:
        sid = row.get("district_scope_id", "")
        mid = row.get("municipality_id", "")
        gid = row.get("lesson_variant_group_id", "")
        group = group_by_id.get(gid, {})
        if not group or group.get("municipality_id") != mid:
            errors.append(f"{sid}: district scope crosses municipality/group boundary")
        if row.get("learner_visible") != "FALSE":
            errors.append(f"{sid}: internal district scope leaked to learner visibility")
        source = sources.get((mid, row.get("official_source_id", "")), {})
        if not source or source.get("official_verified") != "TRUE" or source.get("現行性") not in CURRENT_SOURCE:
            errors.append(f"{sid}: district source is not current official evidence")
        elif source.get("公式URL") != row.get("official_url"):
            errors.append(f"{sid}: district source URL mismatch")
        if not row.get("official_locator"):
            errors.append(f"{sid}: district source locator is blank")

    m098_scopes = [row for row in scopes if row.get("municipality_id") == "M098"]
    if len(m098_scopes) != 6 or any(
        row.get("fixed_10_answer_set_id") != "M098-FIXED10-V1" or
        row.get("fixed_10_confirmation_status") != "CONFIRMED" or
        row.get("i031_answer_family") != "有害ごみ系" or
        not row.get("i031_evidence_source_id") or
        not row.get("i031_evidence_url") or
        not row.get("i031_evidence_locator")
        for row in m098_scopes
    ):
        errors.append("M098 all six district scopes must confirm one fixed-10 answer set and the I031 hazardous-waste teaching family")
    for row in m098_scopes:
        sid = row.get("district_scope_id", "")
        source = sources.get(("M098", row.get("i031_evidence_source_id", "")), {})
        if not source or source.get("official_verified") != "TRUE" or source.get("現行性") not in CURRENT_SOURCE:
            errors.append(f"{sid}: I031 evidence is not current official evidence")
        elif source.get("公式URL") != row.get("i031_evidence_url"):
            errors.append(f"{sid}: I031 evidence URL mismatch")
    innoshima = next((row for row in m098_scopes if row.get("district_scope_id") == "DS-M098-05"), {})
    if (
        innoshima.get("i031_evidence_source_id") != "S-M098-06" or
        innoshima.get("i031_evidence_url") != "https://www.city.onomichi.hiroshima.jp/uploaded/attachment/57907.pdf" or
        "4頁" not in innoshima.get("i031_evidence_locator", "")
    ):
        errors.append("DS-M098-05: I031 must cite the April 2026 Innoshima guide PDF page 4")

    box_ids = [row.get("teaching_box_id", "") for row in boxes]
    if any(not value for value in box_ids) or len(box_ids) != len(set(box_ids)):
        errors.append("teaching box IDs must be globally unique and nonblank")
    box_by_id = {row.get("teaching_box_id", ""): row for row in boxes}
    in_person_names: dict[str, set[str]] = defaultdict(set)
    for row in boxes:
        gid = row.get("lesson_variant_group_id", "")
        class_mode = row.get("class_mode", "")
        box_kind = row.get("box_kind", "")
        if (gid not in group_by_id or not row.get("display_name") or not row.get("display_order") or
                class_mode not in {ONLINE_CLASS_MODE, IN_PERSON_CLASS_MODE} or
                box_kind not in {"FIXED_10_SCORING", "MAJOR_CATEGORY", "SIMPLIFIED_ACTION"}):
            errors.append(f"{row.get('teaching_box_id', '')}: invalid teaching box")
        if class_mode == IN_PERSON_CLASS_MODE:
            in_person_names[gid].add(row.get("display_name", ""))
            if box_kind == "FIXED_10_SCORING":
                errors.append(f"{row.get('teaching_box_id', '')}: fixed-10-only box leaked into in-person mode")
        if row.get("display_name") == "資源回収・確認" and box_kind != "SIMPLIFIED_ACTION":
            errors.append(f"{row.get('teaching_box_id', '')}: 資源回収・確認 must be marked as a simplified teaching action")
        if any(token in row.get("display_name", "") for token in {"フェリー", "持込", "施設", "特殊回収"}):
            errors.append(f"{row.get('teaching_box_id', '')}: special route leaked into learner-facing box")
    if dict(in_person_names) != EXPECTED_IN_PERSON_BOXES:
        errors.append(f"in-person major teaching boxes mismatch: {dict(in_person_names)}")

    scoring_counts = Counter((row.get("lesson_variant_group_id", ""), row.get("internal_item_id", "")) for row in scoring)
    duplicate_pairs = sorted(pair for pair, count in scoring_counts.items() if count != 1)
    if duplicate_pairs:
        errors.append(f"variant scoring pairs must be unique: {duplicate_pairs}")
    by_group: dict[str, dict[str, str]] = defaultdict(dict)
    for row in scoring:
        gid = row.get("lesson_variant_group_id", "")
        mid = row.get("municipality_id", "")
        iid = row.get("internal_item_id", "")
        box_id = row.get("teaching_box_id", "")
        group = group_by_id.get(gid, {})
        by_group[gid][iid] = box_id
        if group.get("municipality_id") != mid:
            errors.append(f"{gid}/{iid}: municipality mismatch")
        box = box_by_id.get(box_id, {})
        if box.get("lesson_variant_group_id") != gid:
            errors.append(f"{gid}/{iid}: answer box is outside the lesson group")
        if box.get("class_mode") != ONLINE_CLASS_MODE:
            errors.append(f"{gid}/{iid}: scoring answer must use an online fixed-10 box")
        if row.get("review_status") != "COMPLETE":
            errors.append(f"{gid}/{iid}: review is not COMPLETE")
        for field in ("condition", "preparation", "exception_destination", "evidence_locator", "checked_date", "reviewer"):
            if not row.get(field):
                errors.append(f"{gid}/{iid}: blank {field}")
        source = sources.get((mid, row.get("evidence_source_id", "")), {})
        if not source or source.get("official_verified") != "TRUE" or source.get("現行性") not in CURRENT_SOURCE:
            errors.append(f"{gid}/{iid}: scoring source is not current official evidence")
        elif source.get("公式URL") != row.get("evidence_url"):
            errors.append(f"{gid}/{iid}: scoring source URL mismatch")
        asset = assets.get(iid, {})
        image_file = asset.get("image_file", "")
        if not asset or not (root / "app/assets/items" / image_file).is_file():
            errors.append(f"{gid}/{iid}: confirmed image asset is missing")

    if dict(by_group) != EXPECTED_ANSWERS:
        errors.append(f"variant answer matrix mismatch: {dict(by_group)}")

    deferred = {
        row["municipality_id"]: row for row in read_rows(root / DEFERRED.relative_to(ROOT))
    }
    for mid in TARGETS:
        if deferred.get(mid, {}).get("status") != "DEFERRED":
            errors.append(f"{mid}: 40-item/canonical DEFERRED boundary was removed")
    standard_scope_ids = {
        row.get("municipality_id", "") for row in read_rows(root / STANDARD_SCOPE.relative_to(ROOT))
    }
    if TARGETS & standard_scope_ids:
        errors.append("M098/M099 must not be injected into municipality-wide scoring scope")

    html = (root / APP_HTML.relative_to(ROOT)).read_text(encoding="utf-8")
    js = (root / APP_JS.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in {'id="lessonVariantGroup"', 'id="lessonVariantControl"'}:
        if token not in html:
            errors.append(f"learner HTML missing lesson variant control: {token}")
    for token in {
        'districtScopes: "../data/app/district_scopes.csv"',
        'lessonVariantGroups: "../data/app/lesson_variant_groups.csv"',
        'lessonVariantBoxes: "../data/app/lesson_variant_teaching_boxes.csv"',
        'lessonVariantScoring: "../data/app/lesson_variant_item_scoring.csv"',
        "buildLessonVariantData", "activeLessonVariantGroupId", "learner_selection_required",
        "lessonVariantBoxesByGroupAndMode", "IN_PERSON_CLASS_MODE", "ONLINE_CLASS_MODE",
    }:
        if token not in js:
            errors.append(f"learner JavaScript missing variant safety token: {token}")
    for token in {"district_name", "official_locator", "exception_destination", "preparation"}:
        if token in js:
            errors.append(f"learner JavaScript exposes internal/teacher variant detail: {token}")
    return errors


def validate(root: Path = ROOT) -> list[str]:
    return validate_records(records(), root)


def main() -> int:
    errors = validate()
    if errors:
        print("LESSON_VARIANT_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("LESSON_VARIANT_VALIDATION_PASSED")
    print("district_scopes=10 lesson_variant_groups=4 scoring_pairs=40")
    return 0


if __name__ == "__main__":
    sys.exit(main())
