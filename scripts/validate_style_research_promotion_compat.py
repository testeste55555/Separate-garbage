#!/usr/bin/env python3
"""Validate historical Style Research plus reviewed APP_READY style overlays.

The original Style Research pilot intentionally recorded M098/M099 as canonical-DEFERRED.
Later APP_READY promotion must not rewrite that historical audit.  This compatibility
layer presents the historical boundary to the base validator while separately auditing
post-promotion UI-only projections.  Color is never garbage-rule evidence.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import validate_style_research as base

PROMOTABLE = {"M098", "M099"}
APP_READY = "APP_READY"
ORIGINAL_READ_CSV = base.read_csv
M099_PREFIX = "APP-STP-M099-"
M099_EXPECTED = {
    "C-M099-01": ("燃やせるごみ", "#E85D7F", "#803346", "#000000"),
    "C-M099-02": ("容器包装プラスチックごみ", "#6F79B8", "#3D4365", "#000000"),
    "C-M099-03": ("紙類", "#D4A515", "#755B0C", "#000000"),
    "C-M099-04": ("資源ごみ", "#75B72C", "#406518", "#000000"),
    "C-M099-05": ("不燃（破砕）ごみ", "#8C6F54", "#4D3D2E", "#FFFFFF"),
    "C-M099-06": ("燃やせる粗大ごみ", "#D87920", "#774312", "#000000"),
    "C-M099-07": ("使用済乾電池等", "#E4A72B", "#7D5C18", "#000000"),
}
M099_DISPLAY_TO_CATEGORY = {name: cid for cid, (name, *_colors) in M099_EXPECTED.items()}


class CompatValidationError(AssertionError):
    pass


def _rows(path: Path):
    # Always read persisted data.  base.read_csv may be monkey-patched below.
    return ORIGINAL_READ_CSV(path)


def promotion_is_complete(root: Path, mid: str) -> bool:
    coverage_path = root / "data/research/07_item_mapping_coverage.csv"
    scope_path = root / "data/app/lesson_mode_app_ready_scope.csv"
    deferred_path = root / "data/master/05_deferred_municipalities.csv"
    if not coverage_path.is_file() or not scope_path.is_file() or not deferred_path.is_file():
        return False

    coverage = [r for r in _rows(coverage_path) if r.get("municipality_id") == mid]
    if len(coverage) != 40 or len({r.get("internal_item_id") for r in coverage}) != 40:
        return False
    if any(
        r.get("coverage_status") != APP_READY
        or r.get("branch_completeness_confirmed") != "TRUE"
        or r.get("evidence_scope") != "ITEM_SPECIFIC"
        for r in coverage
    ):
        return False

    scope = [r for r in _rows(scope_path) if r.get("municipality_id") == mid]
    if len(scope) != 1 or scope[0].get("scoring_status") != APP_READY or scope[0].get("required_item_count") != "40":
        return False

    deferred = {r.get("municipality_id") for r in _rows(deferred_path)}
    return mid not in deferred


def validate_m099_overlay(root: Path = base.ROOT) -> dict[str, int]:
    projection_path = root / "data/style_research/08_style_ui_projection.csv"
    boxes_path = root / "data/app/lesson_variant_teaching_boxes.csv"
    overlays = [r for r in _rows(projection_path) if r.get("projection_id", "").startswith(M099_PREFIX)]

    if not promotion_is_complete(root, "M099"):
        if overlays:
            raise CompatValidationError("M099 UI style overlay exists before atomic APP_READY promotion")
        return {"m099_overlay_rows": 0, "m099_styled_teaching_boxes": 0}

    if len(overlays) != len(M099_EXPECTED):
        raise CompatValidationError(f"M099 overlay must contain exactly 7 rows, got {len(overlays)}")
    by_category = {r.get("category_id", ""): r for r in overlays}
    if set(by_category) != set(M099_EXPECTED):
        raise CompatValidationError(f"M099 overlay category set mismatch: {sorted(by_category)}")

    for index, (category_id, expected) in enumerate(M099_EXPECTED.items(), start=1):
        name, display, border, text = expected
        row = by_category[category_id]
        if row.get("projection_id") != f"{M099_PREFIX}{index:02d}":
            raise CompatValidationError(f"M099 overlay projection id drift: {category_id}")
        if row.get("rank") != "2" or row.get("municipality_id") != "M099" or row.get("district_scope") != "MUNICIPALITY_WIDE":
            raise CompatValidationError(f"M099 overlay identity/scope drift: {category_id}")
        if row.get("自治体正式名称") != name:
            raise CompatValidationError(f"M099 overlay label mismatch: {category_id}")
        if (row.get("display_color"), row.get("border_color"), row.get("text_color")) != (display, border, text):
            raise CompatValidationError(f"M099 overlay audited color triplet changed: {category_id}")
        if row.get("color_status") != "OFFICIAL_DERIVED":
            raise CompatValidationError(f"M099 overlay must remain OFFICIAL_DERIVED: {category_id}")
        if row.get("selected_style_id"):
            raise CompatValidationError(f"M099 overlay must not fabricate historical observation id: {category_id}")
        if row.get("accessibility_label_required") != "TRUE" or row.get("icon_status") != "NOT_RESEARCHED_AS_OFFICIAL":
            raise CompatValidationError(f"M099 overlay accessibility/icon contract changed: {category_id}")
        note = row.get("note", "")
        if "近似" not in note or "SS-M099-01" not in note or "色を分別正答の根拠には使用しない" not in note:
            raise CompatValidationError(f"M099 overlay evidence disclaimer missing: {category_id}")
        if base.contrast_ratio(display, text) < 4.5:
            raise CompatValidationError(f"M099 overlay text contrast below WCAG AA: {category_id}")

    boxes = [r for r in _rows(boxes_path) if r.get("lesson_variant_group_id", "").startswith("LV-M099-")]
    styled = 0
    if not boxes:
        raise CompatValidationError("M099 variant teaching boxes missing")
    for row in boxes:
        label = f"{row.get('lesson_variant_group_id')}/{row.get('teaching_box_id')}"
        if row.get("box_kind") == "SIMPLIFIED_ACTION":
            if row.get("style_source_category_ids") or row.get("style_district_scope"):
                raise CompatValidationError(f"{label}: SIMPLIFIED_ACTION claims official style")
            continue
        expected_category = M099_DISPLAY_TO_CATEGORY.get(row.get("display_name", ""))
        if not expected_category:
            raise CompatValidationError(f"{label}: official teaching box lacks audited category mapping")
        if row.get("style_source_category_ids") != expected_category:
            raise CompatValidationError(f"{label}: style source category mismatch")
        if row.get("style_district_scope") != "MUNICIPALITY_WIDE":
            raise CompatValidationError(f"{label}: M099 common style scope missing")
        styled += 1

    return {"m099_overlay_rows": len(overlays), "m099_styled_teaching_boxes": styled}


def configure() -> None:
    if getattr(base, "_style_promotion_compat", False):
        return

    def compatible_read_csv(path: Path):
        rows = ORIGINAL_READ_CSV(path)
        root = path.parents[2] if len(path.parents) > 2 else base.ROOT
        if path.name == "05_deferred_municipalities.csv":
            existing = {row.get("municipality_id") for row in rows}
            for mid in sorted(PROMOTABLE):
                if mid not in existing and promotion_is_complete(root, mid):
                    # Historical validator must continue to see its original boundary.
                    rows.append({"municipality_id": mid})
            return rows
        if path.name == "08_style_ui_projection.csv" and promotion_is_complete(root, "M099"):
            # Post-promotion UI overlay is audited separately above and must not be
            # misinterpreted as part of the historical Style Research pilot.
            return [row for row in rows if not row.get("projection_id", "").startswith(M099_PREFIX)]
        return rows

    base.read_csv = compatible_read_csv
    base._style_promotion_compat = True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args()

    overlay_metrics = validate_m099_overlay(base.ROOT)
    configure()
    metrics = base.validate(base.ROOT)
    print("PASS Style Research APP_READY promotion compatibility")
    for key, value in overlay_metrics.items():
        print(f"{key}={value}")
    if args.gate:
        print("NEXT_STYLE_BATCH_GATE=PASS")
        print("STYLE_APP_ELIGIBILITY_M098=HOLD_CANONICAL_CATEGORY_DEFERRED")
        print("STYLE_APP_ELIGIBILITY_M099=PASS_APP_READY_UI_OVERLAY")
        print(f"eligible_historical_projection_rows={metrics['projections']}")


if __name__ == "__main__":
    main()
