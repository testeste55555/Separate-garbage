#!/usr/bin/env python3
"""Validate APP_READY and LESSON_READY_10 learner-scoring boundaries."""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ROOT / "data/research/02_categories_master.csv"
SOURCES = ROOT / "data/research/03_sources_master.csv"
MAPPINGS = ROOT / "data/research/05_item_mapping_master.csv"
COVERAGE = ROOT / "data/research/07_item_mapping_coverage.csv"
ITEMS = ROOT / "data/master/04_common_items_master.csv"
ASSETS = ROOT / "data/app/item_image_assets.csv"
IMAGE_MAPPING = ROOT / "data/app/item_image_mapping_pilot_top8.csv"
LESSON_SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
TEACHING_BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
SCORING_PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"
HTML = ROOT / "app/index.html"
JS = ROOT / "app/app.js"
CSS = ROOT / "app/styles.css"

APP_READY = "APP_READY"
LESSON_READY = "LESSON_READY_10"
EXPECTED_APP_READY_ITEMS = {f"I{i:03d}" for i in range(1, 41)}
EXPECTED_IMAGE_ITEMS = 10
EXPECTED_IMAGE_ITEMS_SET = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}
IMAGE_RE = re.compile(r"I\d{3}_[A-Za-z0-9_]+\.png")
REVIEW_PATH_RE = re.compile(r"data/research/(?:app_readiness|lesson_readiness)/m\d{3}_item_review\.csv")
CURRENT_SOURCE = {"CURRENT", "現行", "現行案内中"}
REVIEW_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "canonical_name", "display_name",
    "official_item_wording", "category_id", "category_name", "condition", "preparation",
    "exception_destination", "evidence_basis", "item_evidence_source_id", "item_evidence_url",
    "item_evidence_locator", "branch_review_status", "checked_date", "reviewer", "note",
]
LESSON_EXTRA_FIELDS = [
    "scoring_branch", "exception_evidence_source_id", "exception_evidence_url",
    "exception_evidence_locator",
]
EXPECTED_REGRESSION_STATUS = {
    "M094": APP_READY, "M095": APP_READY, "M104": APP_READY,
    "M097": LESSON_READY, "M105": LESSON_READY, "M106": LESSON_READY,
}
FORBIDDEN_LEARNER_ROUTE_TERMS = {
    "販売店", "リサイクル業者", "施設", "持込", "持ち込み", "引取", "小型家電回収ボックス",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def read_rows(path: Path) -> list[dict[str, str]]:
    return read_csv(path)[1]


def resolve_sort_bucket(
    mid: str,
    category_id: str,
    by_key: dict[tuple[str, str], dict[str, str]],
) -> str | None:
    current = category_id
    visited: set[str] = set()
    while current:
        if current in visited:
            return None
        visited.add(current)
        row = by_key.get((mid, current))
        if not row or row.get("rule_status") != "CURRENT":
            return None
        role = row.get("ui_role", "")
        if role == "SORT_BUCKET":
            return current
        if role in {"HIDDEN", "EXCLUDED_NOTICE"}:
            return None
        current = row.get("parent_category_id", "").strip()
    return None


def build_context(root: Path = ROOT) -> dict[str, object]:
    categories = read_rows(root / CATEGORIES.relative_to(ROOT))
    sources = read_rows(root / SOURCES.relative_to(ROOT))
    mappings = read_rows(root / MAPPINGS.relative_to(ROOT))
    coverage = read_rows(root / COVERAGE.relative_to(ROOT))
    items = read_rows(root / ITEMS.relative_to(ROOT))
    assets = read_rows(root / ASSETS.relative_to(ROOT))
    teaching_boxes = read_rows(root / TEACHING_BOXES.relative_to(ROOT))
    scoring_projection = read_rows(root / SCORING_PROJECTION.relative_to(ROOT))
    return {
        "category_by_key": {(r["municipality_id"], r["category_id"]): r for r in categories},
        "source_by_key": {(r["municipality_id"], r["source_id"]): r for r in sources},
        "mapping_by_key": {
            (r["municipality_id"], r["internal_item_id"], r["branch_order"]): r for r in mappings
        },
        "coverage_by_key": {(r["municipality_id"], r["internal_item_id"]): r for r in coverage},
        "item_by_id": {r["internal_item_id"]: r for r in items},
        "image_item_ids": {
            r["internal_item_id"] for r in assets if r.get("asset_status") == "CONFIRMED"
        },
        "teaching_boxes": teaching_boxes,
        "teaching_box_by_key": {
            (r["municipality_id"], r["class_mode"], r["teaching_box_id"]): r for r in teaching_boxes
        },
        "scoring_projection": scoring_projection,
        "projection_by_pair": {
            (r["municipality_id"], r["internal_item_id"]): r for r in scoring_projection
        },
    }


def validate_official_reference(
    errors: list[str],
    *,
    label: str,
    mid: str,
    source_id: str,
    url: str,
    locator: str,
    source_by_key: dict[tuple[str, str], dict[str, str]],
) -> None:
    if not source_id or not url or not locator:
        errors.append(f"{label}: blank official reference")
        return
    source = source_by_key.get((mid, source_id))
    if not source or source.get("official_verified") != "TRUE" or source.get("現行性") not in CURRENT_SOURCE:
        errors.append(f"{label}: source is not current official evidence")
    elif source.get("公式URL") != url:
        errors.append(f"{label}: source URL mismatch")


def validate_teaching_projection(
    teaching_boxes: list[dict[str, str]],
    scoring_projection: list[dict[str, str]],
    category_by_key: dict[tuple[str, str], dict[str, str]],
) -> list[str]:
    """Keep learner actions separate from the detailed official category layer."""
    errors: list[str] = []
    box_counts = Counter(
        (row.get("municipality_id", ""), row.get("class_mode", ""), row.get("teaching_box_id", ""))
        for row in teaching_boxes
    )
    duplicates = sorted(key for key, count in box_counts.items() if "" in key or count != 1)
    if duplicates:
        errors.append(f"teaching boxes contain blank or duplicate keys: {duplicates}")
    box_by_key = {
        (row.get("municipality_id", ""), row.get("class_mode", ""), row.get("teaching_box_id", "")): row
        for row in teaching_boxes
    }

    for row in teaching_boxes:
        mid = row.get("municipality_id", "")
        box_id = row.get("teaching_box_id", "")
        mode = row.get("class_mode", "")
        kind = row.get("box_kind", "")
        label = row.get("display_name", "")
        category = category_by_key.get((mid, row.get("category_id", "")), {})
        if mode not in {"ONLINE_CLASS", "IN_PERSON_CLASS"}:
            errors.append(f"{mid}/{box_id}: invalid class mode")
        if kind not in {"FIXED_10_SCORING", "SIMPLIFIED_ACTION", "MAJOR_CATEGORY"}:
            errors.append(f"{mid}/{box_id}: invalid teaching box kind")
        if mode == "ONLINE_CLASS" and kind == "MAJOR_CATEGORY":
            errors.append(f"{mid}/{box_id}: online fixed scoring uses a major-category box")
        if mode == "IN_PERSON_CLASS" and kind != "MAJOR_CATEGORY":
            errors.append(f"{mid}/{box_id}: in-person boxes must be MAJOR_CATEGORY")
        if not category or category.get("rule_status") != "CURRENT":
            errors.append(f"{mid}/{box_id}: teaching box lacks a current evidence category")
        if not label or any(term in label for term in FORBIDDEN_LEARNER_ROUTE_TERMS):
            errors.append(f"{mid}/{box_id}: learner label exposes a special collection route")

    projection_counts = Counter(
        (row.get("municipality_id", ""), row.get("internal_item_id", "")) for row in scoring_projection
    )
    duplicate_pairs = sorted(key for key, count in projection_counts.items() if "" in key or count != 1)
    if duplicate_pairs:
        errors.append(f"scoring projection contains blank or duplicate pairs: {duplicate_pairs}")

    for row in scoring_projection:
        mid = row.get("municipality_id", "")
        iid = row.get("internal_item_id", "")
        category_id = row.get("category_id", "")
        projection_kind = row.get("projection_kind", "")
        box = box_by_key.get((mid, "ONLINE_CLASS", row.get("teaching_box_id", "")), {})
        category = category_by_key.get((mid, category_id), {})
        sort_bucket = resolve_sort_bucket(mid, category_id, category_by_key)
        if row.get("review_status") != "COMPLETE" or not box:
            errors.append(f"{mid}/{iid}: incomplete or missing online scoring projection")
            continue
        if box.get("category_id") != category_id:
            errors.append(f"{mid}/{iid}: projection/category evidence mismatch")
        if projection_kind == "SIMPLIFIED_ACTION":
            if box.get("box_kind") != "SIMPLIFIED_ACTION":
                errors.append(f"{mid}/{iid}: SIMPLIFIED_ACTION is not distinct from official scoring boxes")
            if sort_bucket or category.get("ui_role") != "EXCLUDED_NOTICE" or category.get("collection_channel") != "NOT_COLLECTED":
                errors.append(f"{mid}/{iid}: simplified action does not preserve a non-normal category")
        elif projection_kind == "OFFICIAL_CATEGORY":
            if box.get("box_kind") != "FIXED_10_SCORING" or not sort_bucket:
                errors.append(f"{mid}/{iid}: normal answer is not backed by a CURRENT SORT_BUCKET")
        else:
            errors.append(f"{mid}/{iid}: invalid projection kind")

    m106_items = {row.get("internal_item_id") for row in scoring_projection if row.get("municipality_id") == "M106"}
    if m106_items != EXPECTED_IMAGE_ITEMS_SET:
        errors.append(f"M106: teaching projection must cover the fixed 10 items, got {sorted(m106_items)}")
    m106_online = [row for row in teaching_boxes if row.get("municipality_id") == "M106" and row.get("class_mode") == "ONLINE_CLASS"]
    m106_in_person = [row for row in teaching_boxes if row.get("municipality_id") == "M106" and row.get("class_mode") == "IN_PERSON_CLASS"]
    if len(m106_online) != 9 or len(m106_in_person) != 6:
        errors.append(f"M106: expected 9 online scoring boxes and 6 in-person major boxes")
    i029 = next((row for row in scoring_projection if row.get("municipality_id") == "M106" and row.get("internal_item_id") == "I029"), {})
    if i029.get("projection_kind") != "SIMPLIFIED_ACTION":
        errors.append("M106/I029: non-normal route must use SIMPLIFIED_ACTION")
    return errors


def validate_scope_review(
    scope_row: dict[str, str],
    review_fields: list[str],
    review_rows: list[dict[str, str]],
    context: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    mid = scope_row.get("municipality_id", "")
    status = scope_row.get("scoring_status", "")
    category_by_key = context["category_by_key"]
    source_by_key = context["source_by_key"]
    mapping_by_key = context["mapping_by_key"]
    coverage_by_key = context["coverage_by_key"]
    item_by_id = context["item_by_id"]
    image_item_ids = context["image_item_ids"]
    projection_by_pair = context["projection_by_pair"]
    assert isinstance(category_by_key, dict)
    assert isinstance(source_by_key, dict)
    assert isinstance(mapping_by_key, dict)
    assert isinstance(coverage_by_key, dict)
    assert isinstance(item_by_id, dict)
    assert isinstance(image_item_ids, set)
    assert isinstance(projection_by_pair, dict)

    if review_fields[: len(REVIEW_FIELDS)] != REVIEW_FIELDS:
        errors.append(f"{mid}: review header does not start with the common audit fields")
    if status == LESSON_READY and any(field not in review_fields for field in LESSON_EXTRA_FIELDS):
        errors.append(f"{mid}: LESSON_READY_10 review lacks scoring/exception audit fields")

    by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in review_rows:
        by_item[row.get("internal_item_id", "")].append(row)
    expected_items = EXPECTED_APP_READY_ITEMS if status == APP_READY else image_item_ids
    try:
        required_count = int(scope_row.get("required_item_count", ""))
    except ValueError:
        required_count = -1
    try:
        required_branch_count = int(scope_row.get("required_branch_count", ""))
    except ValueError:
        required_branch_count = -1
    if status not in {APP_READY, LESSON_READY}:
        errors.append(f"{mid}: unsupported scoring status {status}")
    if required_count != len(expected_items) or set(by_item) != expected_items:
        errors.append(
            f"{mid}: review item scope mismatch required={required_count} "
            f"actual={len(by_item)} expected={len(expected_items)}"
        )
    if required_branch_count <= 0 or required_branch_count != len(review_rows):
        errors.append(
            f"{mid}: review branch scope mismatch required={required_branch_count} "
            f"actual={len(review_rows)}"
        )

    for iid, rows in sorted(by_item.items()):
        rows.sort(key=lambda row: int(row.get("branch_order") or 0))
        if [row.get("branch_order") for row in rows] != [str(i) for i in range(1, len(rows) + 1)]:
            errors.append(f"{mid}/{iid}: non-contiguous condition branches")
        if status == LESSON_READY:
            scoring = [row for row in rows if row.get("scoring_branch") == "TRUE"]
            if len(scoring) != 1 or any(row.get("scoring_branch") not in {"TRUE", "FALSE"} for row in rows):
                errors.append(f"{mid}/{iid}: exactly one scoring branch is required")

        coverage = coverage_by_key.get((mid, iid), {})
        expected_coverage = APP_READY if status == APP_READY else "VERIFIED"
        if not (
            coverage.get("coverage_status") == expected_coverage
            and coverage.get("branch_completeness_confirmed") == "TRUE"
            and coverage.get("evidence_scope") == "ITEM_SPECIFIC"
            and coverage.get("mapping_branch_count") == str(len(rows))
        ):
            errors.append(f"{mid}/{iid}: canonical coverage is not complete for {status}")

        for row in rows:
            label = f"{mid}/{iid}/{row.get('branch_order')}"
            if row.get("municipality_id") != mid:
                errors.append(f"{label}: municipality mismatch")
            if any(not row.get(field) for field in REVIEW_FIELDS):
                errors.append(f"{label}: blank required review field")
            if row.get("branch_review_status") != "COMPLETE":
                errors.append(f"{label}: branch is not COMPLETE")
            if row.get("evidence_basis") not in {"DIRECT_ITEM", "OFFICIAL_RULE_DERIVED"}:
                errors.append(f"{label}: unsupported evidence basis")
            master = item_by_id.get(iid, {})
            if row.get("canonical_name") != master.get("一般管理用名称") or row.get("display_name") != master.get("教材表示名"):
                errors.append(f"{label}: common item master mismatch")
            category = category_by_key.get((mid, row.get("category_id", "")), {})
            if not category or category.get("rule_status") != "CURRENT" or row.get("category_name") != category.get("自治体正式名称"):
                errors.append(f"{label}: current official category mismatch")
            validate_official_reference(
                errors,
                label=label,
                mid=mid,
                source_id=row.get("item_evidence_source_id", ""),
                url=row.get("item_evidence_url", ""),
                locator=row.get("item_evidence_locator", ""),
                source_by_key=source_by_key,
            )
            if status == LESSON_READY:
                validate_official_reference(
                    errors,
                    label=f"{label} exception",
                    mid=mid,
                    source_id=row.get("exception_evidence_source_id", ""),
                    url=row.get("exception_evidence_url", ""),
                    locator=row.get("exception_evidence_locator", ""),
                    source_by_key=source_by_key,
                )
                if row.get("scoring_branch") == "TRUE":
                    category_id = row.get("category_id", "")
                    projection = projection_by_pair.get((mid, iid), {})
                    if not resolve_sort_bucket(mid, category_id, category_by_key):
                        if not (
                            projection.get("projection_kind") == "SIMPLIFIED_ACTION"
                            and projection.get("category_id") == category_id
                        ):
                            errors.append(f"{label}: non-normal scoring category lacks SIMPLIFIED_ACTION projection")
            mapping = mapping_by_key.get((mid, iid, row.get("branch_order", "")), {})
            comparisons = {
                "official_item_wording": "自治体での品目表記",
                "category_id": "category_id",
                "category_name": "分別区分正式名称",
                "condition": "条件",
                "preparation": "前処理",
                "exception_destination": "例外分別先",
                "item_evidence_source_id": "item_evidence_source_id",
                "item_evidence_url": "item_evidence_url",
                "item_evidence_locator": "item_evidence_locator",
            }
            if not mapping or any(row.get(left) != mapping.get(right) for left, right in comparisons.items()):
                errors.append(f"{label}: review/canonical mapping mismatch")
            expected_mapping_status = APP_READY if status == APP_READY else "VERIFIED"
            if not (
                mapping.get("mapping_status") == expected_mapping_status
                and mapping.get("branch_review_status") == "COMPLETE"
                and mapping.get("evidence_scope") == "ITEM_SPECIFIC"
            ):
                errors.append(f"{label}: canonical branch is not complete for {status}")
    return errors


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    context = build_context(root)
    category_by_key = context["category_by_key"]
    teaching_boxes = context["teaching_boxes"]
    scoring_projection = context["scoring_projection"]
    projection_by_pair = context["projection_by_pair"]
    assert isinstance(category_by_key, dict)
    assert isinstance(teaching_boxes, list)
    assert isinstance(scoring_projection, list)
    assert isinstance(projection_by_pair, dict)
    errors.extend(validate_teaching_projection(teaching_boxes, scoring_projection, category_by_key))
    assets = read_rows(root / ASSETS.relative_to(ROOT))
    image_mapping = read_rows(root / IMAGE_MAPPING.relative_to(ROOT))
    scope = read_rows(root / LESSON_SCOPE.relative_to(ROOT))
    asset_by_item = {r["internal_item_id"]: r for r in assets if r.get("asset_status") == "CONFIRMED"}

    scope_counts = Counter(row.get("municipality_id", "") for row in scope)
    duplicate_scope_ids = sorted(mid for mid, count in scope_counts.items() if not mid or count != 1)
    if duplicate_scope_ids:
        errors.append(f"lesson scope contains blank or duplicate municipality IDs: {duplicate_scope_ids}")

    app_review_paths = {
        path.relative_to(root).as_posix()
        for path in (root / "data/research/app_readiness").glob("m*_item_review.csv")
    }
    lesson_review_paths = {
        path.relative_to(root).as_posix()
        for path in (root / "data/research/lesson_readiness").glob("m*_item_review.csv")
    }
    scoped_app_paths = {r.get("review_source", "") for r in scope if r.get("scoring_status") == APP_READY}
    scoped_lesson_paths = {r.get("review_source", "") for r in scope if r.get("scoring_status") == LESSON_READY}
    if scoped_app_paths != app_review_paths:
        errors.append(f"APP_READY review/scope mismatch: scope={sorted(scoped_app_paths)} files={sorted(app_review_paths)}")
    if scoped_lesson_paths != lesson_review_paths:
        errors.append(
            f"LESSON_READY_10 review/scope mismatch: scope={sorted(scoped_lesson_paths)} "
            f"files={sorted(lesson_review_paths)}"
        )

    ready_pairs: set[tuple[str, str]] = set()
    scoring_branch_by_pair: dict[tuple[str, str], dict[str, str]] = {}
    for scope_row in scope:
        mid = scope_row.get("municipality_id", "")
        review_source = scope_row.get("review_source", "")
        if scope_row.get("lesson_mode") != "ONLINE_CLASS":
            errors.append(f"{mid}: scoring scope is not ONLINE_CLASS")
        if scope_row.get("image_mapping_source") != IMAGE_MAPPING.relative_to(ROOT).as_posix():
            errors.append(f"{mid}: image mapping source mismatch")
        if not REVIEW_PATH_RE.fullmatch(review_source):
            errors.append(f"{mid}: unsafe review source path")
            continue
        review_path = root / review_source
        if not review_path.is_file():
            errors.append(f"{mid}: review source missing")
            continue
        fields, review_rows = read_csv(review_path)
        scoped_errors = validate_scope_review(scope_row, fields, review_rows, context)
        errors.extend(scoped_errors)
        if not scoped_errors:
            ready_pairs.update((mid, row["internal_item_id"]) for row in review_rows)
        if scope_row.get("scoring_status") == LESSON_READY:
            for row in review_rows:
                if row.get("scoring_branch") == "TRUE":
                    scoring_branch_by_pair[(mid, row["internal_item_id"])] = row

    interactive: list[tuple[str, str]] = []
    scope_by_mid = {row["municipality_id"]: row for row in scope}
    for mid, expected_status in EXPECTED_REGRESSION_STATUS.items():
        if scope_by_mid.get(mid, {}).get("scoring_status") != expected_status:
            errors.append(f"{mid}: scoring readiness regression; expected {expected_status}")
    for row in image_mapping:
        mid = row.get("municipality_id", "")
        iid = row.get("internal_item_id", "")
        if mid not in scope_by_mid:
            continue
        if row.get("review_status") != "VERIFIED":
            errors.append(f"{mid}/{iid}: scoped image mapping is not VERIFIED")
            continue
        if (mid, iid) not in ready_pairs:
            errors.append(f"{mid}/{iid}: image row lacks complete scoring-ready review")
            continue
        if scope_by_mid[mid].get("scoring_status") == LESSON_READY:
            scoring = scoring_branch_by_pair.get((mid, iid), {})
            comparisons = [
                ("category_id", "category_id"), ("condition", "condition"),
                ("preparation", "preparation"), ("exception_destination", "exception_destination"),
                ("item_evidence_source_id", "item_evidence_source_id"),
                ("item_evidence_url", "item_evidence_url"),
                ("item_evidence_locator", "item_evidence_locator"),
            ]
            if not scoring or any(row.get(a) != scoring.get(b) for a, b in comparisons):
                errors.append(f"{mid}/{iid}: image mapping does not match the audited scoring branch")
                continue
        asset = asset_by_item.get(iid)
        image_file = asset.get("image_file", "") if asset else ""
        if not asset or not IMAGE_RE.fullmatch(image_file) or not image_file.startswith(f"{iid}_"):
            errors.append(f"{mid}/{iid}: missing or unsafe confirmed image asset")
            continue
        if not (root / "app/assets/items" / image_file).is_file():
            errors.append(f"{mid}/{iid}: image file missing")
            continue
        if not resolve_sort_bucket(mid, row.get("category_id", ""), category_by_key):
            projection = projection_by_pair.get((mid, iid), {})
            if not (
                projection.get("projection_kind") == "SIMPLIFIED_ACTION"
                and projection.get("category_id") == row.get("category_id", "")
            ):
                errors.append(f"{mid}/{iid}: scoring answer is neither CURRENT SORT_BUCKET nor safe SIMPLIFIED_ACTION")
                continue
        interactive.append((mid, iid))

    counts = Counter(mid for mid, _ in interactive)
    for mid in scope_by_mid:
        if counts[mid] != EXPECTED_IMAGE_ITEMS:
            errors.append(f"{mid}: expected 10 interactive image questions, got {counts[mid]}")
    if len(interactive) != EXPECTED_IMAGE_ITEMS * len(scope_by_mid):
        errors.append(
            f"interactive image pair count mismatch: expected={EXPECTED_IMAGE_ITEMS * len(scope_by_mid)} "
            f"actual={len(interactive)}"
        )

    html = (root / HTML.relative_to(ROOT)).read_text(encoding="utf-8")
    js = (root / JS.relative_to(ROOT)).read_text(encoding="utf-8")
    css = (root / CSS.relative_to(ROOT)).read_text(encoding="utf-8")
    for token in {
        'id="lessonModeSelect"', 'id="municipalitySelect"', 'id="practicePanel"',
        'id="itemImage"', 'id="answerFeedback"', 'id="nextItemButton"', 'id="bucketGrid"',
    }:
        if token not in html:
            errors.append(f"HTML missing {token}")
    for token in {
        "itemDisplayName", "itemCondition", "answerDestination", "answerPreparation",
        "answerException", "practiceInstruction", "画像仕分け Pilot",
    }:
        if token in html:
            errors.append(f"learner HTML exposes forbidden item/explanation element: {token}")
    for token in {
        'const ONLINE_CLASS_MODE = "ONLINE_CLASS"',
        'const IN_PERSON_CLASS_MODE = "IN_PERSON_CLASS"',
        'const LESSON_READY_STATUS = "LESSON_READY_10"',
        'lessonScope: "../data/app/lesson_mode_app_ready_scope.csv"',
        'lessonTeachingBoxes: "../data/app/lesson_teaching_boxes.csv"',
        'lessonItemScoringProjection: "../data/app/lesson_item_scoring_projection.csv"',
        "buildScoringReadyData",
        "buildLessonTeachingData",
        'row.branch_review_status?.trim() === "COMPLETE"',
        "scoringReadyMunicipalities.has(municipalityId)",
        "scoringReadyPairs.has(pairKey(municipalityId, itemId))",
        'row.review_status?.trim() !== "VERIFIED"',
        'answerFeedback.textContent = "○"',
        'answerFeedback.textContent = "×"',
    }:
        if token not in js:
            errors.append(f"JavaScript missing safety token: {token}")
    for token in {
        "navigator.onLine", "item.display_name", "item.condition", "item.preparation",
        "item.exception_destination", "answerDestination", "answerPreparation", "answerException",
    }:
        if token in js:
            errors.append(f"learner JavaScript leaks explanation or confuses class/network mode: {token}")
    for token in [":focus-visible", 'data-answer-state="correct"', 'data-answer-state="incorrect"']:
        if token not in css:
            errors.append(f"CSS missing feedback/accessibility token: {token}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("LESSON_SCORING_MODE_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    scope = read_rows(LESSON_SCOPE)
    counts = Counter(row["scoring_status"] for row in scope)
    print("LESSON_SCORING_MODE_VALIDATION_PASSED")
    print(
        f"scoring_municipalities={len(scope)} image_pairs={len(scope) * EXPECTED_IMAGE_ITEMS} "
        f"app_ready={counts[APP_READY]} lesson_ready_10={counts[LESSON_READY]}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
