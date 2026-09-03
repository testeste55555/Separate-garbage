#!/usr/bin/env python3
"""Build the supplemental-five lesson scoring projection from canonical APP_READY reviews.

The selection file chooses an already-reviewed normal branch. Evidence stays in the
canonical APP_READY review; this projection only records the selected branch and
its category for learner scoring.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / "data/app/lesson_supplemental_selection.csv"
OUTPUT = ROOT / "data/app/lesson_supplemental_item_scoring.csv"
APP_READY_DIR = ROOT / "data/research/app_readiness"

FIELDS = [
    "municipality_id",
    "lesson_variant_group_id",
    "display_order",
    "internal_item_id",
    "lesson_condition_profile",
    "selected_branch_order",
    "category_id",
    "category_name",
    "teaching_box_id",
    "canonical_review_path",
    "canonical_checked_date",
    "canonical_reviewer",
    "review_status",
    "note",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_rows(root: Path = ROOT) -> list[dict[str, str]]:
    selections = read_rows(root / SELECTION.relative_to(ROOT))
    cache: dict[str, list[dict[str, str]]] = {}
    result: list[dict[str, str]] = []

    for selected in selections:
        municipality_id = selected["municipality_id"].strip()
        item_id = selected["internal_item_id"].strip()
        branch_order = selected["selected_branch_order"].strip()
        review_relative = Path("data/research/app_readiness") / f"{municipality_id.lower()}_item_review.csv"
        review_path = root / review_relative
        if municipality_id not in cache:
            cache[municipality_id] = read_rows(review_path)

        matches = [
            row for row in cache[municipality_id]
            if row.get("municipality_id", "").strip() == municipality_id
            and row.get("internal_item_id", "").strip() == item_id
            and row.get("branch_order", "").strip() == branch_order
        ]
        if len(matches) != 1:
            raise SystemExit(
                f"{municipality_id} {item_id} branch {branch_order}: expected one canonical row, got {len(matches)}"
            )
        canonical = matches[0]
        if canonical.get("branch_review_status", "").strip() != "COMPLETE":
            raise SystemExit(f"{municipality_id} {item_id}: selected canonical branch is not COMPLETE")
        if selected.get("selection_status", "").strip() != "CONFIRMED":
            raise SystemExit(f"{municipality_id} {item_id}: supplemental selection is not CONFIRMED")

        result.append({
            "municipality_id": municipality_id,
            "lesson_variant_group_id": selected.get("lesson_variant_group_id", "").strip(),
            "display_order": selected["display_order"].strip(),
            "internal_item_id": item_id,
            "lesson_condition_profile": selected["lesson_condition_profile"].strip(),
            "selected_branch_order": branch_order,
            "category_id": canonical.get("category_id", "").strip(),
            "category_name": canonical.get("category_name", "").strip(),
            "teaching_box_id": selected.get("teaching_box_id", "").strip(),
            "canonical_review_path": review_relative.as_posix(),
            "canonical_checked_date": canonical.get("checked_date", "").strip(),
            "canonical_reviewer": canonical.get("reviewer", "").strip(),
            "review_status": "COMPLETE",
            "note": "既存APP_READY正本のCOMPLETE枝を授業用に選択。公式根拠はcanonical reviewに保持。",
        })

    return result


def write_rows(rows: list[dict[str, str]], output: Path = OUTPUT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = build_rows()
    write_rows(rows)
    print(f"Wrote {len(rows)} supplemental lesson scoring rows to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
