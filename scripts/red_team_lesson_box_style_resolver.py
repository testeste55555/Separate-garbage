#!/usr/bin/env python3
"""Mutation RED TEAM for lesson teaching-box style provenance and fallback."""

from __future__ import annotations

import csv
import shutil
import sys
import tempfile
from pathlib import Path

from validate_lesson_box_style_resolver import ROOT, validate


def replace(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"mutation token missing: {relative}: {old}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def mutate_csv(root: Path, relative: str, change) -> None:
    path = root / relative
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = list(reader.fieldnames or []), list(reader)
    change(rows)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def row_by(rows: list[dict[str, str]], field: str, value: str) -> dict[str, str]:
    return next(row for row in rows if row.get(field) == value)


def main() -> int:
    baseline = validate()
    if baseline:
        print("LESSON_BOX_STYLE_RED_TEAM_BASELINE_FAILED")
        for error in baseline:
            print(f"- {error}")
        return 1

    cases = [
        ("SIMPLIFIED_ACTION official-style guard removed", lambda root: replace(root, "app/app.js", 'boxKind === "SIMPLIFIED_ACTION"', 'boxKind === "NEVER"')),
        ("official conflict fallback removed", lambda root: replace(root, "app/app.js", '"CONFLICTING_OFFICIAL_STYLES"', '"STYLE_SELECTED_ARBITRARILY"')),
        ("style provenance DOM audit removed", lambda root: replace(root, "app/app.js", "box.dataset.styleProvenance = status;", "")),
        ("teaching boxes forced back to null style", lambda root: replace(root, "app/app.js", "const resolution = resolveBoxStyle(id, row, usesTeachingBox);", "const style = usesTeachingBox ? null : {};\n      const resolution = resolveBoxStyle(id, row, usesTeachingBox);")),
        ("fallback surface returned to white", lambda root: replace(root, "app/styles.css", "background-color: #e8edf2;", "background-color: #ffffff;")),
        ("fallback pattern removed", lambda root: replace(root, "app/styles.css", "background-image: repeating-linear-gradient(", "background-image: linear-gradient(")),
        ("simplified action claims official category", lambda root: mutate_csv(root, "data/app/lesson_teaching_boxes.csv", lambda rows: row_by(rows, "box_kind", "SIMPLIFIED_ACTION").update({"style_source_category_ids": "C-M106-01", "style_district_scope": "MUNICIPALITY_WIDE"}))),
        ("fallback color persisted into official projection", lambda root: mutate_csv(root, "data/style_research/08_style_ui_projection.csv", lambda rows: rows[0].update({"color_status": "FALLBACK"}))),
        ("variant box cites unknown canonical category", lambda root: mutate_csv(root, "data/app/lesson_variant_teaching_boxes.csv", lambda rows: rows[0].update({"style_source_category_ids": "C-FAKE-01"}))),
    ]

    escaped: list[str] = []
    for label, change in cases:
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "repo"
            shutil.copytree(ROOT, candidate, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            change(candidate)
            if not validate(candidate):
                escaped.append(label)
    if escaped:
        print("LESSON_BOX_STYLE_RED_TEAM_FAILED")
        for label in escaped:
            print(f"- mutation escaped validator: {label}")
        return 1
    print(f"LESSON_BOX_STYLE_RED_TEAM_PASSED mutations={len(cases)}/{len(cases)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
