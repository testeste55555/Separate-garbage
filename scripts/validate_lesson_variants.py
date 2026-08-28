#!/usr/bin/env python3
"""Validate fixed-10 learner variants without widening canonical 40-item scope."""

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

ONLINE_CLASS_MODE = "ONLINE_CLASS"
IN_PERSON_CLASS_MODE = "IN_PERSON_CLASS"
IMAGE_ITEMS = ["I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"]
IMAGE_ITEM_SET = set(IMAGE_ITEMS)
TARGETS = {"M076", "M098", "M099", "M100", "M120", "M123", "M127", "M136", "M139"}
CURRENT_SOURCE = {"CURRENT", "現行", "現行案内中"}

EXPECTED_GROUPS = {
    "M076": {"LV-M076-01", "LV-M076-02"},
    "M098": {"LV-M098-01"},
    "M099": {"LV-M099-01", "LV-M099-02", "LV-M099-03"},
    "M100": {"LV-M100-01", "LV-M100-02"},
    "M120": {"LV-M120-01"},
    "M123": {"LV-M123-01", "LV-M123-02"},
    "M127": {"LV-M127-01", "LV-M127-02", "LV-M127-03"},
    "M136": {"LV-M136-01"},
    "M139": {"LV-M139-01"},
}
SELECTION_REQUIRED = {
    "M076": "TRUE", "M098": "FALSE", "M099": "TRUE", "M100": "TRUE",
    "M120": "FALSE", "M123": "TRUE", "M127": "TRUE", "M136": "FALSE", "M139": "FALSE",
}
EXPECTED_SCOPE_GROUPS = {
    "M076": {"LV-M076-01": 1, "LV-M076-02": 1},
    "M098": {"LV-M098-01": 6},
    "M099": {"LV-M099-01": 1, "LV-M099-02": 2, "LV-M099-03": 1},
    "M100": {"LV-M100-01": 1, "LV-M100-02": 1},
    "M120": {"LV-M120-01": 1},
    "M123": {"LV-M123-01": 4, "LV-M123-02": 4},
    "M127": {"LV-M127-01": 1, "LV-M127-02": 1, "LV-M127-03": 1},
    "M136": {"LV-M136-01": 5},
    "M139": {"LV-M139-01": 3},
}

# Immutable regressions for the two previously implemented municipalities.
EXISTING_EXPECTED_ANSWERS = {
    "LV-M098-01": ["TB-M098-01", "TB-M098-03", "TB-M098-03", "TB-M098-02", "TB-M098-03", "TB-M098-03", "TB-M098-03", "TB-M098-04", "TB-M098-04", "TB-M098-04"],
    "LV-M099-01": ["TB-M099-01-01", "TB-M099-01-02", "TB-M099-01-02", "TB-M099-01-01", "TB-M099-01-03", "TB-M099-01-03", "TB-M099-01-06", "TB-M099-01-05", "TB-M099-01-04", "TB-M099-01-05"],
    "LV-M099-02": ["TB-M099-02-01", "TB-M099-02-02", "TB-M099-02-02", "TB-M099-02-01", "TB-M099-02-03", "TB-M099-02-03", "TB-M099-02-03", "TB-M099-02-05", "TB-M099-02-04", "TB-M099-02-05"],
    "LV-M099-03": ["TB-M099-03-01", "TB-M099-03-02", "TB-M099-03-02", "TB-M099-03-01", "TB-M099-03-05", "TB-M099-03-05", "TB-M099-03-05", "TB-M099-03-04", "TB-M099-03-03", "TB-M099-03-04"],
}
EXISTING_EXPECTED_IN_PERSON = {
    "LV-M098-01": {"もやせるごみ", "もやせないごみ", "容器包装プラスチック", "ペットボトル", "資源回収", "有害ごみ", "粗大ごみ"},
    "LV-M099-01": {"燃やせるごみ", "容器包装プラスチックごみ", "資源ごみ", "紙類", "不燃（破砕）ごみ", "燃やせる粗大ごみ", "使用済乾電池等", "資源回収・確認"},
    "LV-M099-02": {"燃やせるごみ", "容器包装プラスチックごみ", "資源ごみ", "紙類", "不燃（破砕）ごみ", "燃やせる粗大ごみ", "使用済乾電池等"},
    "LV-M099-03": {"燃やせるごみ", "容器包装プラスチックごみ", "資源ごみ", "不燃（破砕）ごみ", "燃やせる粗大ごみ", "使用済乾電池等", "資源回収・確認"},
}

# Expected learner-facing answer labels in fixed item order.
NEW_EXPECTED_LABELS = {
    "LV-M076-01": ["ペットボトル", "アルミ缶", "無色びん", "白色トレイ・発泡スチロール", "新聞", "ダンボール", "紙パック", "回収BOX等", "びん類 その他", "燃えるごみ"],
    "LV-M076-02": ["拠点回収（ペットボトル）", "金属類", "びん", "もえるごみ", "紙類", "紙類", "回収BOX等", "回収BOX等", "取扱注意ごみ", "もえるごみ"],
    "LV-M100-01": ["ペットボトル", "資源ごみ", "資源ごみ", "容器包装プラスチックごみ", "資源ごみ", "資源ごみ", "資源ごみ", "資源ごみ", "埋立ごみ", "埋立ごみ"],
    "LV-M100-02": ["ペットボトル", "カン・ビン・乾電池・金属・小型家電", "カン・ビン・乾電池・金属・小型家電", "容器包装プラスチックごみ", "新聞・古着・紙パック", "雑誌・ダンボール", "新聞・古着・紙パック", "カン・ビン・乾電池・金属・小型家電", "埋立ごみ", "埋立ごみ"],
    "LV-M120-01": ["資源", "資源", "資源", "プラスチック製容器包装", "資源", "資源", "資源", "有害ごみ", "燃やせない", "有害ごみ"],
    "LV-M123-01": ["回収BOX等", "資源品", "びん類", "回収BOX等", "資源品", "資源品", "資源品", "回収BOX等", "金属類及び破砕ごみ", "処理困難ごみ"],
    "LV-M123-02": ["回収BOX等", "資源品", "びん類", "プラスチック類", "資源品", "資源品", "資源品", "回収BOX等", "金属類及び破砕ごみ", "処理困難ごみ"],
    "LV-M127-01": ["リサイクルステーション", "缶類", "びん類", "回収BOX等", "紙リサイクルステーション", "紙リサイクルステーション", "固形燃料化できるごみ", "回収BOX等", "リサイクルステーション", "硬質プラスチック類"],
    "LV-M127-02": ["ペットボトル", "缶類", "びん類", "回収BOX等", "新聞・広告", "段ボール", "固形燃料化できるごみ", "回収BOX等", "有害ごみ", "有害ごみ"],
    "LV-M127-03": ["リサイクルステーション", "缶類", "びん類", "回収BOX等", "リサイクルステーション", "リサイクルステーション", "固形燃料化できるごみ", "回収BOX等", "有害ごみ", "有害ごみ"],
    "LV-M136-01": ["ペットボトル", "カン・金属", "無色透明びん", "もやせるごみ", "新聞紙", "ダンボール", "回収BOX等", "回収BOX等", "埋立・危険なごみ", "埋立・危険なごみ"],
    "LV-M139-01": ["資源ごみ", "資源ごみ", "資源ごみ", "可燃ごみ", "資源ごみ", "資源ごみ", "資源ごみ", "回収BOX等", "不燃ごみ", "資源ごみ"],
}


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
    scopes, groups = data["district_scopes"], data["variant_groups"]
    boxes, scoring = data["teaching_boxes"], data["item_scoring"]
    municipalities = {row["municipality_id"] for row in read_rows(root / MUNICIPALITIES.relative_to(ROOT))}
    sources = {(row["municipality_id"], row["source_id"]): row for row in read_rows(root / SOURCES.relative_to(ROOT))}
    assets = {row["internal_item_id"]: row for row in read_rows(root / ASSETS.relative_to(ROOT)) if row.get("asset_status") == "CONFIRMED"}

    group_ids = [row.get("lesson_variant_group_id", "") for row in groups]
    if any(not value for value in group_ids) or len(group_ids) != len(set(group_ids)):
        errors.append("lesson variant group IDs must be unique and nonblank")
    group_by_id = {row.get("lesson_variant_group_id", ""): row for row in groups}
    actual_groups: dict[str, set[str]] = defaultdict(set)
    for row in groups:
        mid, gid = row.get("municipality_id", ""), row.get("lesson_variant_group_id", "")
        actual_groups[mid].add(gid)
        if mid not in TARGETS or mid not in municipalities:
            errors.append(f"{gid}: unexpected or unknown municipality")
        if row.get("readiness_status") != "LESSON_READY_10":
            errors.append(f"{gid}: readiness is not LESSON_READY_10")
        if row.get("learner_selection_required") != SELECTION_REQUIRED.get(mid):
            errors.append(f"{gid}: learner selection flag mismatch")
        if not row.get("display_name") or not row.get("display_order"):
            errors.append(f"{gid}: missing learner group display data")
    if dict(actual_groups) != EXPECTED_GROUPS:
        errors.append(f"lesson variant groups mismatch: {dict(actual_groups)}")

    scope_ids = [row.get("district_scope_id", "") for row in scopes]
    if any(not value for value in scope_ids) or len(scope_ids) != len(set(scope_ids)):
        errors.append("district scope IDs must be unique and nonblank")
    actual_scope_groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in scopes:
        sid, mid, gid = row.get("district_scope_id", ""), row.get("municipality_id", ""), row.get("lesson_variant_group_id", "")
        actual_scope_groups[mid][gid] += 1
        if group_by_id.get(gid, {}).get("municipality_id") != mid:
            errors.append(f"{sid}: district scope crosses municipality/group boundary")
        if row.get("learner_visible") != "FALSE":
            errors.append(f"{sid}: internal district scope leaked to learner visibility")
        for field in ("district_name", "official_source_id", "official_url", "official_locator"):
            if not row.get(field):
                errors.append(f"{sid}: blank {field}")
        if mid != "M099":
            for field in ("fixed_10_answer_set_id", "i031_answer_family", "i031_evidence_locator"):
                if not row.get(field):
                    errors.append(f"{sid}: blank {field}")
            if row.get("fixed_10_confirmation_status") != "CONFIRMED":
                errors.append(f"{sid}: fixed-10 answer set is not confirmed")
        source = sources.get((mid, row.get("official_source_id", "")), {})
        if not source or source.get("official_verified") != "TRUE" or source.get("現行性") not in CURRENT_SOURCE:
            errors.append(f"{sid}: district source is not current official evidence")
        elif source.get("公式URL") != row.get("official_url"):
            errors.append(f"{sid}: district source URL mismatch")
        if mid != "M099":
            i031_source = sources.get((mid, row.get("i031_evidence_source_id", "")), {})
            if not i031_source or i031_source.get("公式URL") != row.get("i031_evidence_url"):
                errors.append(f"{sid}: I031 evidence mismatch")
    normalized_scope_groups = {mid: dict(counts) for mid, counts in actual_scope_groups.items()}
    if normalized_scope_groups != EXPECTED_SCOPE_GROUPS:
        errors.append(f"district scope grouping mismatch: {normalized_scope_groups}")

    innoshima = next((row for row in scopes if row.get("district_scope_id") == "DS-M098-05"), {})
    if (innoshima.get("i031_evidence_source_id") != "S-M098-06" or
            innoshima.get("i031_evidence_url") != "https://www.city.onomichi.hiroshima.jp/uploaded/attachment/57907.pdf" or
            "4頁" not in innoshima.get("i031_evidence_locator", "")):
        errors.append("DS-M098-05: I031 must cite the April 2026 Innoshima guide PDF page 4")
    if any(row.get("fixed_10_answer_set_id") != "M098-FIXED10-V1" or row.get("i031_answer_family") != "有害ごみ系" for row in scopes if row.get("municipality_id") == "M098"):
        errors.append("M098 district provenance must retain one fixed-10 answer set and I031 family")

    box_ids = [row.get("teaching_box_id", "") for row in boxes]
    if any(not value for value in box_ids) or len(box_ids) != len(set(box_ids)):
        errors.append("teaching box IDs must be globally unique and nonblank")
    box_by_id = {row.get("teaching_box_id", ""): row for row in boxes}
    online_labels: dict[str, set[str]] = defaultdict(set)
    in_person_labels: dict[str, set[str]] = defaultdict(set)
    for row in boxes:
        gid, box_id = row.get("lesson_variant_group_id", ""), row.get("teaching_box_id", "")
        mode, kind, label = row.get("class_mode", ""), row.get("box_kind", ""), row.get("display_name", "")
        if gid not in group_by_id or mode not in {ONLINE_CLASS_MODE, IN_PERSON_CLASS_MODE} or kind not in {"FIXED_10_SCORING", "MAJOR_CATEGORY", "SIMPLIFIED_ACTION"} or not label or not row.get("display_order"):
            errors.append(f"{box_id}: invalid teaching box")
        if mode == ONLINE_CLASS_MODE:
            online_labels[gid].add(label)
            if kind == "MAJOR_CATEGORY":
                errors.append(f"{box_id}: online fixed10 uses a non-scoring major box")
        else:
            in_person_labels[gid].add(label)
            if kind == "FIXED_10_SCORING":
                errors.append(f"{box_id}: fixed-10-only box leaked into in-person mode")
        if label in {"資源回収・確認", "回収BOX等"} and kind != "SIMPLIFIED_ACTION":
            errors.append(f"{box_id}: learner action must be SIMPLIFIED_ACTION")
        if kind == "SIMPLIFIED_ACTION" and label not in {"資源回収・確認", "回収BOX等"}:
            errors.append(f"{box_id}: unapproved simplified action label")
        if any(token in label for token in {"フェリー", "特殊回収", "処理施設持込"}):
            errors.append(f"{box_id}: special route leaked into learner-facing box")
    for gid in NEW_EXPECTED_LABELS:
        if online_labels.get(gid) != in_person_labels.get(gid):
            errors.append(f"{gid}: online/in-person box labels drifted")
    for gid, names in EXISTING_EXPECTED_IN_PERSON.items():
        if in_person_labels.get(gid) != names:
            errors.append(f"{gid}: existing in-person major boxes regressed")

    scoring_counts = Counter((row.get("lesson_variant_group_id", ""), row.get("internal_item_id", "")) for row in scoring)
    duplicate_pairs = sorted(pair for pair, count in scoring_counts.items() if count != 1)
    if duplicate_pairs:
        errors.append(f"variant scoring pairs must be unique: {duplicate_pairs}")
    answer_ids: dict[str, dict[str, str]] = defaultdict(dict)
    answer_labels: dict[str, dict[str, str]] = defaultdict(dict)
    for row in scoring:
        gid, mid, iid, box_id = row.get("lesson_variant_group_id", ""), row.get("municipality_id", ""), row.get("internal_item_id", ""), row.get("teaching_box_id", "")
        answer_ids[gid][iid] = box_id
        box = box_by_id.get(box_id, {})
        answer_labels[gid][iid] = box.get("display_name", "")
        if group_by_id.get(gid, {}).get("municipality_id") != mid:
            errors.append(f"{gid}/{iid}: municipality mismatch")
        if iid not in IMAGE_ITEM_SET:
            errors.append(f"{gid}/{iid}: item is outside fixed10")
        if box.get("lesson_variant_group_id") != gid or box.get("class_mode") != ONLINE_CLASS_MODE:
            errors.append(f"{gid}/{iid}: answer box is outside online lesson group")
        if row.get("review_status") != "COMPLETE":
            errors.append(f"{gid}/{iid}: review is not COMPLETE")
        for field in ("condition", "preparation", "exception_destination", "evidence_source_id", "evidence_url", "evidence_locator", "checked_date", "reviewer"):
            if not row.get(field):
                errors.append(f"{gid}/{iid}: blank {field}")
        source = sources.get((mid, row.get("evidence_source_id", "")), {})
        if not source or source.get("official_verified") != "TRUE" or source.get("現行性") not in CURRENT_SOURCE:
            errors.append(f"{gid}/{iid}: scoring source is not current official evidence")
        elif source.get("公式URL") != row.get("evidence_url"):
            errors.append(f"{gid}/{iid}: scoring source URL mismatch")
        asset = assets.get(iid, {})
        if not asset or not (root / "app/assets/items" / asset.get("image_file", "")).is_file():
            errors.append(f"{gid}/{iid}: confirmed image asset is missing")
    for gid in group_by_id:
        if set(answer_ids.get(gid, {})) != IMAGE_ITEM_SET:
            errors.append(f"{gid}: scoring does not cover fixed10 exactly")
    for gid, expected in EXISTING_EXPECTED_ANSWERS.items():
        actual = [answer_ids.get(gid, {}).get(iid) for iid in IMAGE_ITEMS]
        if actual != expected:
            errors.append(f"{gid}: existing answer matrix regressed: {actual}")
    for gid, expected in NEW_EXPECTED_LABELS.items():
        actual = [answer_labels.get(gid, {}).get(iid) for iid in IMAGE_ITEMS]
        if actual != expected:
            errors.append(f"{gid}: fixed10 answer labels mismatch: {actual}")

    deferred = {row["municipality_id"]: row for row in read_rows(root / DEFERRED.relative_to(ROOT))}
    for mid in TARGETS:
        if deferred.get(mid, {}).get("status") != "DEFERRED":
            errors.append(f"{mid}: canonical 40-item DEFERRED boundary was removed")
    standard_scope_ids = {row.get("municipality_id", "") for row in read_rows(root / STANDARD_SCOPE.relative_to(ROOT))}
    if TARGETS & standard_scope_ids:
        errors.append(f"variant municipality injected into municipality-wide scoring scope: {sorted(TARGETS & standard_scope_ids)}")

    html = (root / APP_HTML.relative_to(ROOT)).read_text(encoding="utf-8")
    js = (root / APP_JS.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in {'id="lessonVariantGroup"', 'id="lessonVariantControl"'}:
        if token not in html:
            errors.append(f"learner HTML missing lesson variant control: {token}")
    for token in {"buildLessonVariantData", "activeLessonVariantGroupId", "learner_selection_required", "lessonVariantBoxesByGroupAndMode", "IN_PERSON_CLASS_MODE", "ONLINE_CLASS_MODE"}:
        if token not in js:
            errors.append(f"learner JavaScript missing variant safety token: {token}")
    for token in {'itemImage.alt = "仕分けるごみの画像"', "activeItems = lessonMode === ONLINE_CLASS_MODE", "if (lessonMode === IN_PERSON_CLASS_MODE)"}:
        if token not in js:
            errors.append(f"learner mode/image privacy contract missing: {token}")
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
    data = records()
    print("LESSON_VARIANT_VALIDATION_PASSED")
    print(f"municipalities={len(TARGETS)} district_scopes={len(data['district_scopes'])} lesson_variant_groups={len(data['variant_groups'])} scoring_pairs={len(data['item_scoring'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
