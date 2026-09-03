#!/usr/bin/env python3
"""Mutation RED TEAM for supplemental-five lesson scoring."""

from __future__ import annotations

import csv
import shutil
import tempfile
from pathlib import Path

from validate_lesson_supplemental_scoring import ROOT, validate

REQUIRED = [
    "data/app/lesson_supplemental_selection.csv",
    "data/app/lesson_supplemental_item_scoring.csv",
    "data/app/lesson_supplemental_teaching_boxes.csv",
    "data/app/lesson_variant_teaching_boxes.csv",
    "data/app/lesson_variant_groups.csv",
    "data/app/lesson_item_set.csv",
    "data/app/lesson_mode_app_ready_scope.csv",
    "data/app/item_image_assets.csv",
    "app/app.js",
]
REQUIRED += [f"data/research/app_readiness/{mid}_item_review.csv" for mid in ("m009", "m020", "m094", "m098", "m099", "m105")]


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fixture() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name) / "repo"
    for relative in REQUIRED:
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return temp, root


def expect_rejected(name: str, mutate) -> None:
    temp, root = fixture()
    try:
        mutate(root)
        errors = validate(root)
        if not errors:
            raise AssertionError(f"RED TEAM mutation escaped validator: {name}")
        print(f"PASS {name}: {errors[0]}")
    finally:
        temp.cleanup()


def mutate_selection(root: Path, predicate, updates: dict[str, str]) -> None:
    path = root / "data/app/lesson_supplemental_selection.csv"
    fields, rows = read_rows(path)
    matched = False
    for row in rows:
        if predicate(row):
            row.update(updates)
            matched = True
            break
    if not matched:
        raise AssertionError("mutation target missing")
    write_rows(path, fields, rows)


def main() -> int:
    expect_rejected(
        "M094 plastic label replaced by paper-label branch",
        lambda root: mutate_selection(
            root,
            lambda row: row["municipality_id"] == "M094" and row["internal_item_id"] == "I003",
            {"selected_branch_order": "2"},
        ),
    )
    expect_rejected(
        "clean snack-bag lesson profile changed",
        lambda root: mutate_selection(
            root,
            lambda row: row["municipality_id"] == "M094" and row["internal_item_id"] == "I010",
            {"lesson_condition_profile": "DIRTY_OR_NONPLASTIC_SNACK_BAG"},
        ),
    )

    def remove_m099_variant(root: Path) -> None:
        path = root / "data/app/lesson_supplemental_selection.csv"
        fields, rows = read_rows(path)
        rows = [
            row for row in rows
            if not (row["municipality_id"] == "M099" and row["lesson_variant_group_id"] == "LV-M099-03" and row["internal_item_id"] == "I010")
        ]
        write_rows(path, fields, rows)
    expect_rejected("M099 variant row removed", remove_m099_variant)

    def add_lesson_ready_only_municipality(root: Path) -> None:
        path = root / "data/app/lesson_supplemental_selection.csv"
        fields, rows = read_rows(path)
        extra = dict(rows[0])
        extra.update({"municipality_id": "M106", "lesson_variant_group_id": "", "internal_item_id": "I002"})
        rows.append(extra)
        write_rows(path, fields, rows)
    expect_rejected("LESSON_READY_10-only municipality added", add_lesson_ready_only_municipality)

    def expose_m098_selector(root: Path) -> None:
        path = root / "data/app/lesson_variant_groups.csv"
        fields, rows = read_rows(path)
        for row in rows:
            if row["lesson_variant_group_id"] == "LV-M098-01":
                row["learner_selection_required"] = "TRUE"
        write_rows(path, fields, rows)
    expect_rejected("M098 learner region selector exposed", expose_m098_selector)

    def corrupt_battery_category(root: Path) -> None:
        path = root / "data/app/lesson_supplemental_item_scoring.csv"
        fields, rows = read_rows(path)
        for row in rows:
            if row["municipality_id"] == "M105" and row["internal_item_id"] == "I027":
                row["category_id"] = "C-M105-01"
                row["category_name"] = "燃やせるごみ"
        write_rows(path, fields, rows)
    expect_rejected("dry battery projected to burnable garbage", corrupt_battery_category)

    def company_mapping_as_evidence(root: Path) -> None:
        path = root / "data/app/lesson_supplemental_item_scoring.csv"
        fields, rows = read_rows(path)
        rows[0]["canonical_review_path"] = "data/app/company_municipality_mapping.csv"
        write_rows(path, fields, rows)
    expect_rejected("company mapping used as evidence", company_mapping_as_evidence)

    def remove_burnable_box(root: Path) -> None:
        path = root / "data/app/lesson_supplemental_teaching_boxes.csv"
        fields, rows = read_rows(path)
        rows = [row for row in rows if row["teaching_box_id"] != "TB-M098-SUP-01"]
        write_rows(path, fields, rows)
    expect_rejected("required supplemental burnable box removed", remove_burnable_box)

    print("Supplemental lesson scoring RED TEAM passed: 8/8 mutations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
