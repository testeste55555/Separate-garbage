#!/usr/bin/env python3
"""Idempotently merge immutable Pilot and completed batches into canonical v1.1 tables."""

from __future__ import annotations

import csv
from pathlib import Path

from migrate_schema_v11 import MAPPING_FIELDS, build_initial_mapping, read_csv, write_csv


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
        ]
        if all(path.exists() for path in expected):
            result.append(directory)
    return result


def main() -> None:
    pilot = RESEARCH / "pilot"
    municipality_inputs = [pilot / "pilot_municipalities.csv"]
    category_inputs = [pilot / "pilot_categories.csv"]
    source_inputs = [pilot / "pilot_sources.csv"]
    qa_inputs = [pilot / "pilot_qa.csv"]
    for batch in completed_batches():
        prefix = batch.name + "_"
        municipality_inputs.append(batch / f"{prefix}municipalities.csv")
        category_inputs.append(batch / f"{prefix}categories.csv")
        source_inputs.append(batch / f"{prefix}sources.csv")
        qa_inputs.append(batch / f"{prefix}qa.csv")

    merge(RESEARCH / "04_municipalities_research.csv", municipality_inputs, ["municipality_id"])
    merge(RESEARCH / "02_categories_master.csv", category_inputs, ["municipality_id", "category_id"])
    merge(RESEARCH / "03_sources_master.csv", source_inputs, ["municipality_id", "source_id"])
    merge(RESEARCH / "06_qa_log.csv", qa_inputs, ["municipality_id"])

    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    mappings = build_initial_mapping(categories)
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    print(f"data/research/05_item_mapping_master.csv={len(mappings)}")


if __name__ == "__main__":
    main()
