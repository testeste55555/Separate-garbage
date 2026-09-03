#!/usr/bin/env python3
"""Mutation RED TEAM for the guarded 15-item learner UI."""
from __future__ import annotations

import copy

from validate_lesson_15_ui import APP, ASSETS, BOXES, SCORING, read_rows, validate_records


def expect_failure(name: str, assets, scoring, boxes, app_text: str) -> None:
    errors = validate_records(assets, scoring, boxes, app_text, check_asset_files=False)
    if not errors:
        raise AssertionError(f"RED TEAM mutation was not detected: {name}")
    print(f"PASS red-team {name}: {errors[0]}")


def main() -> None:
    assets = read_rows(ASSETS)
    scoring = read_rows(SCORING)
    boxes = read_rows(BOXES)
    app_text = APP.read_text(encoding="utf-8")

    mutated = [row for row in copy.deepcopy(assets) if row["internal_item_id"] != "I018"]
    expect_failure("missing supplemental image", mutated, scoring, boxes, app_text)

    mutated = copy.deepcopy(assets)
    next(row for row in mutated if row["internal_item_id"] == "I027")["asset_status"] = "PENDING"
    expect_failure("unconfirmed supplemental image", mutated, scoring, boxes, app_text)

    mutated = copy.deepcopy(assets)
    next(row for row in mutated if row["internal_item_id"] == "I003")["image_file"] = "I003_pet_label.png"
    expect_failure("wrong supplemental filename", mutated, scoring, boxes, app_text)

    mutated = copy.deepcopy(scoring)
    mutated.pop(next(i for i, row in enumerate(mutated) if row["municipality_id"] == "M020" and row["internal_item_id"] == "I010"))
    expect_failure("missing standard scoring row", assets, mutated, boxes, app_text)

    mutated = copy.deepcopy(scoring)
    next(row for row in mutated if row["municipality_id"] == "M099" and row["lesson_variant_group_id"] == "LV-M099-02")["lesson_variant_group_id"] = ""
    expect_failure("lost M099 variant", assets, mutated, boxes, app_text)

    mutated = copy.deepcopy(scoring)
    mutated[0]["municipality_id"] = "M104"
    expect_failure("scope leakage", assets, mutated, boxes, app_text)

    mutated = copy.deepcopy(boxes)
    mutated.pop()
    expect_failure("missing variant supplemental box", assets, scoring, mutated, app_text)

    broken_app = app_text.replace('"M098", "M099", "M105"', '"M098", "M099", "M104", "M105"', 1)
    expect_failure("UI target leakage", assets, scoring, boxes, broken_app)

    broken_app = app_text.replace("const EXPECTED_LESSON_READY_ITEM_COUNT = 10;", "const EXPECTED_LESSON_READY_ITEM_COUNT = 15;", 1)
    expect_failure("LESSON_READY_10 widened", assets, scoring, boxes, broken_app)

    print("PASS all guarded lesson 15 UI RED TEAM mutations")


if __name__ == "__main__":
    main()
