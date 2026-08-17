#!/usr/bin/env python3
"""Idempotently merge Pilot and completed Schema v1.2 batches."""

from __future__ import annotations

import csv
from pathlib import Path

from schema_v12 import read_csv, write_csv


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data" / "research"
BATCH_ROOT = RESEARCH / "batches"


def merge(target: Path, inputs: list[Path], key_fields: list[str]) -> None:
    fields: list[str] = []
    merged: dict[tuple[str, ...], dict[str, str]] = {}
    for path in inputs:
        current_fields, rows = read_csv(path)
        if not fields:
            fields = current_fields
        elif current_fields != fields:
            raise ValueError(f"header mismatch: {path.relative_to(ROOT)}")
        for row in rows:
            key = tuple(row[field] for field in key_fields)
            if key in merged:
                raise ValueError(f"duplicate key {key} from {path.relative_to(ROOT)}")
            merged[key] = row
    rows = sorted(merged.values(), key=lambda row: tuple(row[field] for field in key_fields))
    write_csv(target, fields, rows)
    print(f"{target.relative_to(ROOT)}={len(rows)}")


def completed_batches() -> list[Path]:
    result = []
    for directory in sorted(path for path in BATCH_ROOT.iterdir() if path.is_dir()):
        prefix = directory.name + "_"
        expected = [
            directory / f"{prefix}municipalities.csv",
            directory / f"{prefix}categories.csv",
            directory / f"{prefix}sources.csv",
            directory / f"{prefix}qa.csv",
            directory / f"{prefix}item_mapping.csv",
            directory / f"{prefix}item_coverage.csv",
        ]
        if all(path.exists() for path in expected):
            result.append(directory)
    return result


def merge_review_table(target: Path, inputs: list[Path], key_fields: list[str], status_field: str,
                       manual_statuses: set[str]) -> None:
    existing = {}
    if target.exists():
        _, rows = read_csv(target)
        existing = {tuple(row.get(field, "") for field in key_fields): row for row in rows}
    fields: list[str] = []
    merged = {}
    for path in inputs:
        current_fields, rows = read_csv(path)
        if not fields:
            fields = current_fields
        elif current_fields != fields:
            raise ValueError(f"header mismatch: {path.relative_to(ROOT)}")
        for row in rows:
            key = tuple(row[field] for field in key_fields)
            if key in merged:
                raise ValueError(f"duplicate key {key} from {path.relative_to(ROOT)}")
            previous = existing.get(key)
            merged[key] = previous if previous and previous.get(status_field) in manual_statuses else row
    # Preserve a manually reviewed canonical mapping even if a later heuristic
    # no longer proposes it.  Structural validation still requires valid refs.
    for key, row in existing.items():
        if key not in merged and row.get(status_field) in manual_statuses:
            merged[key] = row
    write_csv(target, fields, sorted(merged.values(), key=lambda row: tuple(row[field] for field in key_fields)))
    print(f"{target.relative_to(ROOT)}={len(merged)}")


def main() -> None:
    pilot = RESEARCH / "pilot"
    municipality_inputs = [pilot / "pilot_municipalities.csv"]
    category_inputs = [pilot / "pilot_categories.csv"]
    source_inputs = [pilot / "pilot_sources.csv"]
    qa_inputs = [pilot / "pilot_qa.csv"]
    mapping_inputs = [pilot / "pilot_item_mapping.csv"]
    coverage_inputs = [pilot / "pilot_item_coverage.csv"]
    for batch in completed_batches():
        prefix = batch.name + "_"
        municipality_inputs.append(batch / f"{prefix}municipalities.csv")
        category_inputs.append(batch / f"{prefix}categories.csv")
        source_inputs.append(batch / f"{prefix}sources.csv")
        qa_inputs.append(batch / f"{prefix}qa.csv")
        mapping_inputs.append(batch / f"{prefix}item_mapping.csv")
        coverage_inputs.append(batch / f"{prefix}item_coverage.csv")

    merge(RESEARCH / "04_municipalities_research.csv", municipality_inputs, ["municipality_id"])
    merge(RESEARCH / "02_categories_master.csv", category_inputs, ["municipality_id", "category_id"])
    merge(RESEARCH / "03_sources_master.csv", source_inputs, ["municipality_id", "source_id"])
    merge(RESEARCH / "06_qa_log.csv", qa_inputs, ["municipality_id"])

    merge_review_table(
        RESEARCH / "05_item_mapping_master.csv", mapping_inputs,
        ["municipality_id", "internal_item_id", "category_id"], "mapping_status", {"VERIFIED", "APP_READY"},
    )
    merge_review_table(
        RESEARCH / "07_item_mapping_coverage.csv", coverage_inputs,
        ["municipality_id", "internal_item_id"], "coverage_status", {"VERIFIED", "VERIFIED_NOT_APPLICABLE", "APP_READY"},
    )


if __name__ == "__main__":
    main()
