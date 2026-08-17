#!/usr/bin/env python3
"""Merge immutable Pilot output and completed PHASE 3 batches into canonical tables."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data" / "research"
BATCH_ROOT = RESEARCH / "batches"


def read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames or [], list(reader)


def write(path: Path, fields: list[str], rows: list[dict[str, str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def merge(target: Path, inputs: list[Path], key_fields: list[str]):
    fields: list[str] = []
    merged: dict[tuple[str, ...], dict[str, str]] = {}
    for path in inputs:
        current_fields, rows = read(path)
        if not fields:
            fields = current_fields
        elif current_fields != fields:
            raise ValueError(f"header mismatch: {path}")
        for row in rows:
            key = tuple(row[field] for field in key_fields)
            if key in merged:
                raise ValueError(f"duplicate key {key} from {path}")
            merged[key] = row
    rows = sorted(merged.values(), key=lambda r: tuple(r[field] for field in key_fields))
    write(target, fields, rows)
    print(f"{target.relative_to(ROOT)}={len(rows)}")


def main():
    batches = sorted(p for p in BATCH_ROOT.iterdir() if p.is_dir())
    municipality_inputs = [RESEARCH / "pilot" / "pilot_municipalities.csv"]
    category_inputs = [RESEARCH / "pilot" / "pilot_categories.csv"]
    source_inputs = [RESEARCH / "pilot" / "pilot_sources.csv"]
    qa_inputs = [RESEARCH / "06_qa_log.csv"]
    for batch in batches:
        prefix = batch.name + "_"
        municipality_inputs.append(batch / f"{prefix}municipalities.csv")
        category_inputs.append(batch / f"{prefix}categories.csv")
        source_inputs.append(batch / f"{prefix}sources.csv")
        qa_inputs.append(batch / f"{prefix}qa.csv")
    # The existing 06_qa_log.csv may already be canonical. Restrict its input to
    # immutable Pilot IDs so reruns remain idempotent after canonical overwrite.
    pilot_ids = {"M001", "M013", "M030", "M094", "M102"}
    qa_fields, qa_existing = read(RESEARCH / "06_qa_log.csv")
    qa_pilot_path = RESEARCH / "pilot" / "pilot_qa.csv"
    write(qa_pilot_path, qa_fields, [r for r in qa_existing if r["municipality_id"] in pilot_ids])
    qa_inputs[0] = qa_pilot_path

    merge(RESEARCH / "04_municipalities_research.csv", municipality_inputs, ["municipality_id"])
    merge(RESEARCH / "02_categories_master.csv", category_inputs, ["municipality_id", "category_id"])
    merge(RESEARCH / "03_sources_master.csv", source_inputs, ["municipality_id", "source_id"])
    merge(RESEARCH / "06_qa_log.csv", qa_inputs, ["municipality_id"])


if __name__ == "__main__":
    main()
