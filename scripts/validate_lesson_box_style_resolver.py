#!/usr/bin/env python3
"""Validate official-style inheritance and runtime-only lesson fallback styling."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")
OFFICIAL = {"OFFICIAL_CONFIRMED", "OFFICIAL_DERIVED"}


def read_rows(root: Path, relative: str) -> tuple[list[str], list[dict[str, str]]]:
    with (root / relative).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    category_fields, categories = read_rows(root, "data/research/02_categories_master.csv")
    _ = category_fields
    standard_fields, standard = read_rows(root, "data/app/lesson_teaching_boxes.csv")
    variant_fields, variants = read_rows(root, "data/app/lesson_variant_teaching_boxes.csv")
    _, groups = read_rows(root, "data/app/lesson_variant_groups.csv")
    _, projections = read_rows(root, "data/style_research/08_style_ui_projection.csv")
    required = {"style_source_category_ids", "style_district_scope"}
    if not required.issubset(standard_fields):
        errors.append("standard teaching boxes lack style source audit columns")
    if not required.issubset(variant_fields):
        errors.append("variant teaching boxes lack style source audit columns")

    category_index = {(row["municipality_id"], row["category_id"]): row for row in categories}
    projection_index = {
        (row["municipality_id"], row.get("district_scope") or "MUNICIPALITY_WIDE", row["category_id"]): row
        for row in projections
    }

    def sort_bucket(mid: str, category_id: str) -> str | None:
        visited: set[str] = set()
        current = category_id
        while current and current not in visited:
            visited.add(current)
            category = category_index.get((mid, current))
            if not category or category.get("rule_status") != "CURRENT":
                return None
            if category.get("ui_role") == "SORT_BUCKET":
                return current
            if category.get("ui_role") in {"HIDDEN", "EXCLUDED_NOTICE"}:
                return None
            current = category.get("parent_category_id", "")
        return None

    resolved_official = 0
    resolved_fallback = 0
    for row in standard:
        label = f"{row.get('municipality_id')}/{row.get('teaching_box_id')}"
        sources = [value for value in row.get("style_source_category_ids", "").split(";") if value]
        if row.get("box_kind") == "SIMPLIFIED_ACTION":
            if sources or row.get("style_district_scope"):
                errors.append(f"{label}: SIMPLIFIED_ACTION must not claim official style sources")
            continue
        if sources != [row.get("category_id")]:
            errors.append(f"{label}: single official category source is not explicit")
        if row.get("style_district_scope") != "MUNICIPALITY_WIDE":
            errors.append(f"{label}: municipality-wide style scope missing")
        for category_id in sources:
            if (row.get("municipality_id", ""), category_id) not in category_index:
                errors.append(f"{label}: unknown style source category {category_id}")
        resolved_styles = []
        for category_id in sources:
            bucket = sort_bucket(row.get("municipality_id", ""), category_id)
            projection = projection_index.get((row.get("municipality_id", ""), "MUNICIPALITY_WIDE", bucket or ""), {})
            if projection.get("color_status") in OFFICIAL and all(
                HEX_RE.fullmatch(projection.get(field, ""))
                for field in ("display_color", "border_color", "text_color")
            ):
                resolved_styles.append(tuple(projection[field].upper() for field in ("display_color", "border_color", "text_color")))
        if sources and len(resolved_styles) == len(sources) and len(set(resolved_styles)) == 1:
            resolved_official += 1
        else:
            resolved_fallback += 1

    group_to_mid = {row["lesson_variant_group_id"]: row["municipality_id"] for row in groups}
    for row in variants:
        label = f"{row.get('lesson_variant_group_id')}/{row.get('teaching_box_id')}"
        sources = [value for value in row.get("style_source_category_ids", "").split(";") if value]
        if row.get("box_kind") == "SIMPLIFIED_ACTION" and (sources or row.get("style_district_scope")):
            errors.append(f"{label}: variant action claims official style")
        mid = group_to_mid.get(row.get("lesson_variant_group_id", ""), "")
        for category_id in sources:
            if (mid, category_id) not in category_index:
                errors.append(f"{label}: variant style source category is not canonical")
        if row.get("box_kind") == "SIMPLIFIED_ACTION" or not sources:
            resolved_fallback += 1

    if resolved_official == 0 or resolved_fallback == 0:
        errors.append("resolver fixtures do not exercise both official and fallback paths")
    m094_standard = [row for row in standard if row.get("municipality_id") == "M094" and row.get("box_kind") != "SIMPLIFIED_ACTION"]
    for row in m094_standard:
        category_id = row.get("style_source_category_ids", "")
        bucket = sort_bucket("M094", category_id)
        projection = projection_index.get(("M094", "MUNICIPALITY_WIDE", bucket or ""), {})
        if projection.get("color_status") not in OFFICIAL:
            errors.append(f"M094/{row.get('teaching_box_id')}: known official style no longer resolves")

    # FALLBACK is runtime provenance only. It must never be persisted into the
    # official projection table as invented municipality color data.
    for row in projections:
        if row.get("color_status") == "FALLBACK" and any(
            row.get(field) for field in ("display_color", "border_color", "text_color", "selected_style_id")
        ):
            errors.append(f"{row.get('projection_id')}: fallback color persisted as official projection")

    js = (root / "app/app.js").read_text(encoding="utf-8")
    css = (root / "app/styles.css").read_text(encoding="utf-8")
    required_js = {
        "function resolveBoxStyle", "function fallbackStyle", 'provenance: "FALLBACK"',
        'boxKind === "SIMPLIFIED_ACTION"', '"CONFLICTING_OFFICIAL_STYLES"',
        '"SAME_OFFICIAL_STYLE"', '"VARIANT_OFFICIAL_STYLE"',
        "box.dataset.styleProvenance", "box.dataset.styleReason", "box.dataset.sourceCategoryIds",
        "box.style.backgroundColor = resolution.style.display_color.trim()",
        '"bucket--fallback-style"', "box.dataset.fallbackPalette",
    }
    for token in required_js:
        if token not in js:
            errors.append(f"app style resolver token missing: {token}")
    if "const style = usesTeachingBox ? null" in js:
        errors.append("teaching box still forces official style to null")

    fallback_match = re.search(r"\.bucket--fallback-style\s*\{(?P<body>.*?)\n\}", css, re.S)
    if not fallback_match:
        errors.append("fallback style rule missing")
    else:
        body = fallback_match.group("body")
        colors = HEX_RE.findall(body)
        if not colors or any(color.lower() in {"#fff", "#ffffff"} for color in colors):
            errors.append("fallback style is white or lacks an explicit non-white surface")
        if "background-image: none" not in body or "border-color" not in body or "border-style: solid" not in body:
            errors.append("fallback style lacks solid high-contrast surface")
        palette_rules = re.findall(r'\.bucket--fallback-style\[data-fallback-palette="[1-8]"\]', css)
        if len(palette_rules) != 8:
            errors.append("fallback palette does not define all 8 classroom colors")
    if '.bucket--fallback-style[data-box-kind="SIMPLIFIED_ACTION"]' not in css or "border-style: dashed" not in css:
        errors.append("simplified action lacks a non-color visual distinction")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("LESSON_BOX_STYLE_RESOLVER_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("LESSON_BOX_STYLE_RESOLVER_VALIDATION_PASSED")
    print("provenance=OFFICIAL_CONFIRMED|OFFICIAL_DERIVED|FALLBACK fallback_persisted=0 fallback_palette=8")
    return 0


if __name__ == "__main__":
    sys.exit(main())