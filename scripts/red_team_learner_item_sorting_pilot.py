#!/usr/bin/env python3
"""Mutation RED TEAM for the learner image-sorting Pilot UI projection."""

from __future__ import annotations

import copy
import sys

from schema_v12 import read_csv
from validate_learner_item_sorting_pilot import (
    ASSETS,
    CATEGORIES,
    CSS,
    HTML,
    JAVASCRIPT,
    PILOT_PATH,
    STYLES,
    resolve_sort_bucket,
    validate_static_ui,
    validate_static_ui_text,
    validate_ui_projection,
)


def rows(path):
    return read_csv(path)[1]


def rejected(pilot, categories, styles, assets) -> bool:
    errors, _ = validate_ui_projection(pilot, categories, styles, assets)
    return bool(errors)


def find(data, **expected):
    return next(row for row in data if all(row.get(key) == value for key, value in expected.items()))


def main() -> int:
    pilot = rows(PILOT_PATH)
    categories = rows(CATEGORIES)
    styles = rows(STYLES)
    assets = rows(ASSETS)
    html = HTML.read_text(encoding="utf-8")
    javascript = JAVASCRIPT.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    category_by_key = {(r["municipality_id"], r["category_id"]): r for r in categories}

    checks: list[tuple[str, bool]] = []

    changed = copy.deepcopy(pilot)
    find(changed, municipality_id="M107", internal_item_id="I031")["review_status"] = "VERIFIED"
    checks.append(("UNRESOLVED item cannot become an interactive answer", rejected(changed, categories, styles, assets)))

    changed = copy.deepcopy(categories)
    find(changed, municipality_id="M105", category_id="C-M105-04")["parent_category_id"] = ""
    checks.append(("REFERENCE_ONLY leaf without SORT_BUCKET ancestor is rejected", rejected(pilot, changed, styles, assets)))

    changed = copy.deepcopy(categories)
    find(changed, municipality_id="M106", category_id="C-M106-06")["rule_status"] = "RETIRED"
    checks.append(("non-CURRENT source category is rejected", rejected(pilot, changed, styles, assets)))

    changed = copy.deepcopy(categories)
    find(changed, municipality_id="M109", category_id="C-M109-03")["ui_role"] = "HIDDEN"
    checks.append(("HIDDEN parent cannot become a learner bucket", rejected(pilot, changed, styles, assets)))

    changed = copy.deepcopy(categories)
    find(changed, municipality_id="M105", category_id="C-M105-04")["parent_category_id"] = "C-M105-04"
    checks.append(("category parent cycle is rejected", rejected(pilot, changed, styles, assets)))

    changed = copy.deepcopy(styles)
    find(changed, municipality_id="M094", category_id="C-M094-02")["display_color"] = ""
    checks.append(("official style with missing HEX is rejected", rejected(pilot, categories, changed, assets)))

    changed = copy.deepcopy(styles)
    find(changed, municipality_id="M109", category_id="C-M109-03")["display_color"] = "#00AA00"
    checks.append(("NOT_CONFIRMED style cannot smuggle a guessed color", rejected(pilot, categories, changed, assets)))

    changed = copy.deepcopy(styles)
    changed.remove(find(changed, municipality_id="M095", category_id="C-M095-05"))
    checks.append(("missing style projection is rejected", rejected(pilot, categories, changed, assets)))

    changed = copy.deepcopy(assets)
    find(changed, internal_item_id="I001")["image_file"] = "../I001_pet_bottle.png"
    checks.append(("unsafe image path is rejected", rejected(pilot, categories, styles, changed)))

    changed = copy.deepcopy(pilot)
    find(changed, municipality_id="M094", internal_item_id="I001")["municipality_id"] = "M098"
    checks.append(("district-variant municipality injection is rejected", rejected(changed, categories, styles, assets)))

    bucket, reason = resolve_sort_bucket("M105", "C-M105-04", category_by_key)
    checks.append((
        "official child category remains distinct while projecting to parent box",
        reason is None and bucket is not None and bucket["category_id"] == "C-M105-02",
    ))
    checks.append(("accessible learner controls and feedback contract are present", not validate_static_ui()))

    changed_javascript = javascript.replace(
        'itemImage.alt = "仕分ける品目の画像";',
        'itemImage.alt = `${item.display_name}の教材画像`;',
    )
    checks.append((
        "item name cannot leak through the learner image label",
        bool(validate_static_ui_text(html, changed_javascript, css)),
    ))

    changed_javascript = f"{javascript}\nvoid item.condition;\n"
    checks.append((
        "condition or teacher explanation cannot leak into learner UI",
        bool(validate_static_ui_text(html, changed_javascript, css)),
    ))

    changed_javascript = javascript.replace(
        "activeItems = lessonMode === ONLINE_CLASS_MODE ? availableItems : [];",
        "activeItems = availableItems;",
    )
    checks.append((
        "image quiz remains limited to online lesson mode",
        bool(validate_static_ui_text(html, changed_javascript, css)),
    ))

    changed_javascript = f"{javascript}\nvoid navigator.onLine;\n"
    checks.append((
        "lesson mode must not be confused with network connectivity",
        bool(validate_static_ui_text(html, changed_javascript, css)),
    ))

    changed_html = html.replace('id="lessonModeSelect"', 'id="removedLessonModeSelect"')
    checks.append((
        "lesson mode selector is required",
        bool(validate_static_ui_text(changed_html, javascript, css)),
    ))

    passed = sum(ok for _, ok in checks)
    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    if passed != len(checks):
        print(f"LEARNER_ITEM_SORTING_PILOT_RED_TEAM_FAILED {passed}/{len(checks)}")
        return 1
    print(f"LEARNER_ITEM_SORTING_PILOT_RED_TEAM_PASSED {passed}/{len(checks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
