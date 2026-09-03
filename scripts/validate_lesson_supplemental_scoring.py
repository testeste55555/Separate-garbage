#!/usr/bin/env python3
"""Validate supplemental-five scoring without widening LESSON_READY_10."""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

from build_lesson_supplemental_scoring import FIELDS, build_rows

ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / "data/app/lesson_supplemental_selection.csv"
SCORING = ROOT / "data/app/lesson_supplemental_item_scoring.csv"
SUPPLEMENTAL_BOXES = ROOT / "data/app/lesson_supplemental_teaching_boxes.csv"
FIXED_VARIANT_BOXES = ROOT / "data/app/lesson_variant_teaching_boxes.csv"
VARIANT_GROUPS = ROOT / "data/app/lesson_variant_groups.csv"
LESSON_SET = ROOT / "data/app/lesson_item_set.csv"
LESSON_SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
ASSETS = ROOT / "data/app/item_image_assets.csv"
APP_JS = ROOT / "app/app.js"

TARGETS = {"M009", "M020", "M094", "M098", "M099", "M105"}
SUPPLEMENTAL = {
    "I002": (11, "PLASTIC_PET_CAP"),
    "I003": (12, "PLASTIC_PET_LABEL"),
    "I027": (13, "STANDARD_DRY_BATTERY"),
    "I018": (14, "HOUSEHOLD_FOOD_WASTE"),
    "I010": (15, "CLEAN_PLASTIC_SNACK_BAG"),
}
EXPECTED_GROUPS = {
    "M009": {""},
    "M020": {""},
    "M094": {""},
    "M098": {"LV-M098-01"},
    "M099": {"LV-M099-01", "LV-M099-02", "LV-M099-03"},
    "M105": {""},
}
EXPECTED_SUPPLEMENTAL_BOXES = {
    "TB-M098-SUP-01": ("LV-M098-01", "M098", "C-M098-01", "もやせるごみ"),
    "TB-M099-01-SUP-01": ("LV-M099-01", "M099", "C-M099-01", "燃やせるごみ"),
    "TB-M099-02-SUP-01": ("LV-M099-02", "M099", "C-M099-01", "燃やせるごみ"),
    "TB-M099-03-SUP-01": ("LV-M099-03", "M099", "C-M099-01", "燃やせるごみ"),
}
FIXED10 = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalized(rows: list[dict[str, str]], fields: list[str]) -> list[dict[str, str]]:
    return [{field: row.get(field, "") for field in fields} for row in rows]


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    selection = read_rows(root / SELECTION.relative_to(ROOT))
    scoring = read_rows(root / SCORING.relative_to(ROOT))
    supplemental_boxes = read_rows(root / SUPPLEMENTAL_BOXES.relative_to(ROOT))
    fixed_boxes = read_rows(root / FIXED_VARIANT_BOXES.relative_to(ROOT))
    groups = read_rows(root / VARIANT_GROUPS.relative_to(ROOT))
    lesson_set = read_rows(root / LESSON_SET.relative_to(ROOT))
    scopes = read_rows(root / LESSON_SCOPE.relative_to(ROOT))
    assets = read_rows(root / ASSETS.relative_to(ROOT))

    formal_supplemental = {
        row.get("internal_item_id", ""): (int(row.get("display_order", "0") or 0), row.get("item_role", ""))
        for row in lesson_set if row.get("item_role") == "SUPPLEMENTAL_5"
    }
    expected_formal = {item_id: (order, "SUPPLEMENTAL_5") for item_id, (order, _) in SUPPLEMENTAL.items()}
    if formal_supplemental != expected_formal:
        errors.append(f"formal supplemental set mismatch: {formal_supplemental}")

    if len(selection) != 40:
        errors.append(f"supplemental selection must have 40 rows, got {len(selection)}")
    if {row.get("municipality_id", "") for row in selection} != TARGETS:
        errors.append("supplemental selection municipality scope mismatch")

    seen: Counter[tuple[str, str, str]] = Counter()
    actual_groups: dict[str, set[str]] = defaultdict(set)
    for row in selection:
        mid = row.get("municipality_id", "")
        gid = row.get("lesson_variant_group_id", "")
        item_id = row.get("internal_item_id", "")
        seen[(mid, gid, item_id)] += 1
        actual_groups[mid].add(gid)
        if item_id not in SUPPLEMENTAL:
            errors.append(f"{mid}/{gid}: unexpected supplemental item {item_id}")
            continue
        expected_order, expected_profile = SUPPLEMENTAL[item_id]
        if row.get("display_order") != str(expected_order):
            errors.append(f"{mid}/{gid}/{item_id}: display order mismatch")
        if row.get("lesson_condition_profile") != expected_profile:
            errors.append(f"{mid}/{gid}/{item_id}: lesson condition profile mismatch")
        if row.get("selected_branch_order") != "1":
            errors.append(f"{mid}/{gid}/{item_id}: only reviewed normal branch 1 may be selected")
        if row.get("selection_status") != "CONFIRMED":
            errors.append(f"{mid}/{gid}/{item_id}: selection is not CONFIRMED")
        if mid in {"M098", "M099"} and not row.get("teaching_box_id"):
            errors.append(f"{mid}/{gid}/{item_id}: regional supplemental row requires a teaching box")
        if mid not in {"M098", "M099"} and row.get("teaching_box_id"):
            errors.append(f"{mid}/{item_id}: municipality-wide row must use canonical category, not variant teaching box")

    if any(count != 1 for count in seen.values()):
        errors.append("supplemental selection contains duplicate municipality/group/item rows")
    if {mid: groupset for mid, groupset in actual_groups.items()} != EXPECTED_GROUPS:
        errors.append(f"supplemental variant topology mismatch: {dict(actual_groups)}")
    for mid, groupset in EXPECTED_GROUPS.items():
        for gid in groupset:
            for item_id in SUPPLEMENTAL:
                if seen[(mid, gid, item_id)] != 1:
                    errors.append(f"missing supplemental row: {mid}/{gid or 'municipality-wide'}/{item_id}")

    scope_by_mid = {row.get("municipality_id", ""): row for row in scopes}
    for mid in TARGETS:
        scope = scope_by_mid.get(mid, {})
        if scope.get("scoring_status") != "APP_READY" or scope.get("required_item_count") != "40":
            errors.append(f"{mid}: supplemental scoring requires existing 40-item APP_READY scope")
        if scope.get("review_source") != f"data/research/app_readiness/{mid.lower()}_item_review.csv":
            errors.append(f"{mid}: APP_READY review source mismatch")

    group_by_id = {row.get("lesson_variant_group_id", ""): row for row in groups}
    m098 = group_by_id.get("LV-M098-01", {})
    if m098.get("municipality_id") != "M098" or m098.get("learner_selection_required") != "FALSE":
        errors.append("M098 learner topology changed; it must remain one hidden-selection group")
    m099_ids = {gid for gid, row in group_by_id.items() if row.get("municipality_id") == "M099"}
    if m099_ids != EXPECTED_GROUPS["M099"]:
        errors.append("M099 must retain exactly three learner variant groups")
    for gid in EXPECTED_GROUPS["M099"]:
        if group_by_id.get(gid, {}).get("learner_selection_required") != "TRUE":
            errors.append(f"{gid}: learner selection must remain TRUE")

    actual_supplemental_boxes = {row.get("teaching_box_id", ""): row for row in supplemental_boxes}
    if set(actual_supplemental_boxes) != set(EXPECTED_SUPPLEMENTAL_BOXES):
        errors.append("supplemental teaching box set mismatch")
    for box_id, (gid, mid, category_id, display_name) in EXPECTED_SUPPLEMENTAL_BOXES.items():
        row = actual_supplemental_boxes.get(box_id, {})
        if (
            row.get("lesson_variant_group_id") != gid
            or row.get("municipality_id") != mid
            or row.get("category_id") != category_id
            or row.get("display_name") != display_name
            or row.get("class_mode") != "ONLINE_CLASS"
            or row.get("box_kind") != "SUPPLEMENTAL_5_SCORING"
            or row.get("style_source_category_ids") != category_id
        ):
            errors.append(f"{box_id}: supplemental teaching box definition mismatch")

    fixed_box_ids = {row.get("teaching_box_id", "") for row in fixed_boxes}
    allowed_box_ids = fixed_box_ids | set(EXPECTED_SUPPLEMENTAL_BOXES)
    for row in selection:
        box_id = row.get("teaching_box_id", "")
        if box_id and box_id not in allowed_box_ids:
            errors.append(f"{box_id}: supplemental selection points to unknown teaching box")

    try:
        rebuilt = build_rows(root)
    except (SystemExit, FileNotFoundError, KeyError) as exc:
        errors.append(f"canonical supplemental rebuild failed: {exc}")
        rebuilt = []
    if normalized(scoring, FIELDS) != normalized(rebuilt, FIELDS):
        errors.append("committed supplemental scoring projection differs from canonical rebuild")
    if len(scoring) != 40 or any(row.get("review_status") != "COMPLETE" for row in scoring):
        errors.append("supplemental scoring projection must contain exactly 40 COMPLETE rows")
    for row in scoring:
        path = row.get("canonical_review_path", "")
        if not path.startswith("data/research/app_readiness/") or "company" in path.lower():
            errors.append(f"{row.get('municipality_id')}/{row.get('internal_item_id')}: evidence pointer must be canonical APP_READY review")

    asset_items = {row.get("internal_item_id", "") for row in assets if row.get("asset_status") == "CONFIRMED"}
    active_supplemental_assets = set(SUPPLEMENTAL) & asset_items
    if active_supplemental_assets and active_supplemental_assets != set(SUPPLEMENTAL):
        errors.append(f"partial supplemental image activation is forbidden: {sorted(active_supplemental_assets)}")

    app_js = (root / APP_JS.relative_to(ROOT)).read_text(encoding="utf-8")
    if 'const EXPECTED_LESSON_READY_ITEM_COUNT = 10;' not in app_js:
        errors.append("LESSON_READY_10 item count was changed")
    for item_id in FIXED10:
        if f'"{item_id}"' not in app_js:
            errors.append(f"fixed10 app invariant lost {item_id}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Supplemental lesson scoring validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    asset_items = {row.get("internal_item_id", "") for row in read_rows(ASSETS) if row.get("asset_status") == "CONFIRMED"}
    activation = "READY" if set(SUPPLEMENTAL) <= asset_items else "PENDING_IMAGES"
    print(f"Supplemental lesson scoring validation passed: 40 selections; image activation={activation}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
