#!/usr/bin/env python3
"""Validate the learner image-sorting Pilot UI and its read-only projections."""

from __future__ import annotations

import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from schema_v12 import read_csv
from validate_item_image_mapping_pilot import PILOT_PATH, validate_pilot_rows


ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ROOT / "data/research/02_categories_master.csv"
STYLES = ROOT / "data/style_research/08_style_ui_projection.csv"
ASSETS = ROOT / "data/app/item_image_assets.csv"
HTML = ROOT / "app/index.html"
JAVASCRIPT = ROOT / "app/app.js"
CSS = ROOT / "app/styles.css"
OFFICIAL_STYLE_STATUSES = {"OFFICIAL_CONFIRMED", "OFFICIAL_DERIVED"}
EXPECTED_BY_MUNICIPALITY = {
    "M094": 10,
    "M095": 10,
    "M097": 10,
    "M104": 10,
    "M105": 10,
    "M106": 10,
    "M107": 8,
    "M109": 8,
}
VARIANT_HOLD = {"M098", "M099"}
HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")
IMAGE_RE = re.compile(r"I\d{3}_[A-Za-z0-9_]+\.png")


def rows(path: Path) -> list[dict[str, str]]:
    return read_csv(path)[1]


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name == "id" and value:
                self.ids.add(value)


def resolve_sort_bucket(
    municipality_id: str,
    category_id: str,
    category_by_key: dict[tuple[str, str], dict[str, str]],
) -> tuple[dict[str, str] | None, str | None]:
    """Walk a CURRENT category branch to its learner-visible SORT_BUCKET ancestor."""
    visited: set[str] = set()
    current_id = category_id
    while current_id:
        if current_id in visited:
            return None, "category parent cycle"
        visited.add(current_id)
        category = category_by_key.get((municipality_id, current_id))
        if not category:
            return None, "missing category/parent"
        if category.get("rule_status") != "CURRENT":
            return None, "non-CURRENT category in projection path"
        if category.get("ui_role") == "SORT_BUCKET":
            return category, None
        if category.get("ui_role") in {"HIDDEN", "EXCLUDED_NOTICE"}:
            return None, f"forbidden ui_role in projection path: {category.get('ui_role')}"
        current_id = category.get("parent_category_id", "").strip()
    return None, "no SORT_BUCKET ancestor"


def validate_ui_projection(
    pilot: list[dict[str, str]],
    categories: list[dict[str, str]],
    styles: list[dict[str, str]],
    assets: list[dict[str, str]],
    root: Path = ROOT,
) -> tuple[list[str], list[dict[str, str]]]:
    errors: list[str] = []
    category_by_key = {(r["municipality_id"], r["category_id"]): r for r in categories}
    style_by_key: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for style in styles:
        key = (style["municipality_id"], style["district_scope"], style["category_id"])
        style_by_key.setdefault(key, []).append(style)
    asset_by_item = {r["internal_item_id"]: r for r in assets if r["asset_status"] == "CONFIRMED"}
    projected: list[dict[str, str]] = []

    if VARIANT_HOLD & {r.get("municipality_id", "") for r in pilot}:
        errors.append("district-variant M098/M099 entered the municipality-wide UI Pilot")

    for row in pilot:
        if row.get("review_status") != "VERIFIED":
            continue
        mid = row.get("municipality_id", "")
        iid = row.get("internal_item_id", "")
        label = f"{mid}/{iid}"
        bucket, reason = resolve_sort_bucket(mid, row.get("category_id", ""), category_by_key)
        if not bucket:
            errors.append(f"{label}: cannot project to SORT_BUCKET: {reason}")
            continue

        asset = asset_by_item.get(iid)
        image_file = asset.get("image_file", "") if asset else ""
        if not asset or not IMAGE_RE.fullmatch(image_file) or not image_file.startswith(f"{iid}_"):
            errors.append(f"{label}: unsafe or missing confirmed image asset")
            continue
        if not (root / "app/assets/items" / image_file).is_file():
            errors.append(f"{label}: image file missing")

        style_matches = style_by_key.get((mid, "MUNICIPALITY_WIDE", bucket["category_id"]), [])
        if len(style_matches) != 1:
            errors.append(f"{label}: expected one municipality-wide style projection for {bucket['category_id']}")
            continue
        style = style_matches[0]
        status = style.get("color_status", "")
        colors = [style.get("display_color", ""), style.get("border_color", ""), style.get("text_color", "")]
        if status in OFFICIAL_STYLE_STATUSES:
            if not all(HEX_RE.fullmatch(value) for value in colors):
                errors.append(f"{label}: official style lacks complete HEX triplet")
        elif status == "NOT_CONFIRMED":
            if any(colors):
                errors.append(f"{label}: NOT_CONFIRMED style must not contain guessed colors")
        else:
            errors.append(f"{label}: unsupported style status {status!r}")

        projected.append(
            {
                "municipality_id": mid,
                "internal_item_id": iid,
                "source_category_id": row["category_id"],
                "ui_category_id": bucket["category_id"],
                "style_status": status,
                "image_file": image_file,
            }
        )

    counts = Counter(r["municipality_id"] for r in projected)
    if counts != Counter(EXPECTED_BY_MUNICIPALITY):
        errors.append(f"projected pair counts mismatch: {dict(counts)}")
    if len(projected) != 76:
        errors.append(f"only 76 VERIFIED pairs may be interactive: {len(projected)}")
    projected_pairs = {(r["municipality_id"], r["internal_item_id"]) for r in projected}
    unresolved_pairs = {
        (r.get("municipality_id", ""), r.get("internal_item_id", ""))
        for r in pilot
        if r.get("review_status") == "UNRESOLVED"
    }
    if projected_pairs & unresolved_pairs:
        errors.append("UNRESOLVED pair entered interactive projection")
    return errors, projected


def validate_static_ui_text(html: str, javascript: str, css: str) -> list[str]:
    errors: list[str] = []
    parser = IdCollector()
    parser.feed(html)
    required_ids = {
        "lessonModeSelect", "municipalitySelect", "bucketGrid", "practicePanel",
        "practiceProgress", "itemCard", "itemImage", "practiceInstruction",
        "answerFeedback", "nextItemButton",
    }
    missing = required_ids - parser.ids
    if missing:
        errors.append(f"learner UI missing required elements: {sorted(missing)}")
    forbidden_ids = {
        "itemDisplayName", "itemCondition", "answerDetail", "answerDestination",
        "answerPreparation", "answerException",
    }
    leaked_ids = forbidden_ids & parser.ids
    if leaked_ids:
        errors.append(f"learner UI exposes answer/explanation elements: {sorted(leaked_ids)}")

    required_js = {
        "../data/app/item_image_assets.csv",
        "../data/app/item_image_mapping_pilot_top8.csv",
        'row.review_status?.trim() !== "VERIFIED"',
        "findSortBucket",
        "OFFICIAL_STYLE_STATUSES",
        "practiceFinished",
        'const ONLINE_CLASS_MODE = "ONLINE_CLASS"',
        'const IN_PERSON_CLASS_MODE = "IN_PERSON_CLASS"',
        "lessonModeSelect.value",
        "activeItems = lessonMode === ONLINE_CLASS_MODE ? availableItems : [];",
        'itemImage.alt = "仕分ける品目の画像";',
    }
    missing_js = sorted(value for value in required_js if value not in javascript)
    if missing_js:
        errors.append(f"learner UI missing safety/projection logic: {missing_js}")
    forbidden_js = {
        "item.display_name", "item.condition", "item.preparation",
        "item.exception_destination", "answerDestination", "answerPreparation",
        "answerException", "navigator.onLine",
    }
    leaked_js = sorted(value for value in forbidden_js if value in javascript)
    if leaked_js:
        errors.append(f"learner UI leaks answer detail or confuses class mode with network state: {leaked_js}")
    for token in [":focus-visible", 'data-answer-state="correct"', 'data-answer-state="incorrect"']:
        if token not in css:
            errors.append(f"learner UI CSS missing accessibility/feedback token: {token}")
    return errors


def validate_static_ui(root: Path = ROOT) -> list[str]:
    return validate_static_ui_text(
        (root / "app/index.html").read_text(encoding="utf-8"),
        (root / "app/app.js").read_text(encoding="utf-8"),
        (root / "app/styles.css").read_text(encoding="utf-8"),
    )


def main() -> int:
    pilot = rows(PILOT_PATH)
    errors = validate_pilot_rows(pilot)
    projection_errors, projected = validate_ui_projection(
        pilot,
        rows(CATEGORIES),
        rows(STYLES),
        rows(ASSETS),
    )
    errors.extend(projection_errors)
    errors.extend(validate_static_ui())
    if errors:
        print("LEARNER_ITEM_SORTING_PILOT_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    style_counts = Counter(r["style_status"] for r in projected)
    child_projections = sum(r["source_category_id"] != r["ui_category_id"] for r in projected)
    print("LEARNER_ITEM_SORTING_PILOT_VALIDATION_PASSED")
    print(
        f"interactive_pairs={len(projected)} municipalities=8 unresolved_excluded=4 "
        f"child_to_bucket_projections={child_projections} style_statuses={dict(style_counts)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
