#!/usr/bin/env python3
"""Idempotently merge Pilot/batches while preserving reviewed APP evidence."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from schema_v12 import completed_batch_dirs, read_csv, write_csv


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data" / "research"
ITEM_SOURCE_PREFIX = "IS-"


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


def merge_sources(target: Path, inputs: list[Path]) -> None:
    """Merge category-research sources and retain IS-* APP item evidence sources."""
    supplements = []
    if target.exists():
        _, existing = read_csv(target)
        supplements = [r for r in existing if r.get("source_id", "").startswith(ITEM_SOURCE_PREFIX)]
    fields: list[str] = []
    merged: dict[tuple[str, str], dict[str, str]] = {}
    for path in inputs:
        current_fields, rows = read_csv(path)
        if not fields:
            fields = current_fields
        elif current_fields != fields:
            raise ValueError(f"header mismatch: {path.relative_to(ROOT)}")
        for row in rows:
            key = (row["municipality_id"], row["source_id"])
            if key in merged:
                raise ValueError(f"duplicate source key {key} from {path.relative_to(ROOT)}")
            merged[key] = row
    for row in supplements:
        key = (row["municipality_id"], row["source_id"])
        if key in merged:
            raise ValueError(f"APP item source collides with batch source: {key}")
        merged[key] = row
    write_csv(target, fields, sorted(merged.values(), key=lambda r: (r["municipality_id"], r["source_id"])))
    print(f"{target.relative_to(ROOT)}={len(merged)} item_supplements={len(supplements)}")


def merge_review_table(target: Path, inputs: list[Path], key_fields: list[str], status_field: str,
                       manual_statuses: set[str],
                       sort_key: Callable[[dict[str, str]], tuple[object, ...]] | None = None) -> None:
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
    for key, row in existing.items():
        if key not in merged and row.get(status_field) in manual_statuses:
            merged[key] = row
    row_sort_key = sort_key or (lambda row: tuple(row[field] for field in key_fields))
    write_csv(target, fields, sorted(merged.values(), key=row_sort_key))
    print(f"{target.relative_to(ROOT)}={len(merged)}")


def main() -> None:
    pilot = RESEARCH / "pilot"
    municipality_inputs = [pilot / "pilot_municipalities.csv"]
    category_inputs = [pilot / "pilot_categories.csv"]
    source_inputs = [pilot / "pilot_sources.csv"]
    qa_inputs = [pilot / "pilot_qa.csv"]
    mapping_inputs = [pilot / "pilot_item_mapping.csv"]
    coverage_inputs = [pilot / "pilot_item_coverage.csv"]
    review_evidence_inputs = [pilot / "pilot_category_review_evidence.csv"]
    for batch in completed_batch_dirs():
        prefix = batch.name + "_"
        municipality_inputs.append(batch / f"{prefix}municipalities.csv")
        category_inputs.append(batch / f"{prefix}categories.csv")
        source_inputs.append(batch / f"{prefix}sources.csv")
        qa_inputs.append(batch / f"{prefix}qa.csv")
        mapping_inputs.append(batch / f"{prefix}item_mapping.csv")
        coverage_inputs.append(batch / f"{prefix}item_coverage.csv")
        review_evidence_inputs.append(batch / f"{prefix}category_review_evidence.csv")

    merge(RESEARCH / "04_municipalities_research.csv", municipality_inputs, ["municipality_id"])
    merge(RESEARCH / "02_categories_master.csv", category_inputs, ["municipality_id", "category_id"])
    merge_sources(RESEARCH / "03_sources_master.csv", source_inputs)
    merge(RESEARCH / "06_qa_log.csv", qa_inputs, ["municipality_id"])
    merge(RESEARCH / "08_category_review_evidence.csv", review_evidence_inputs, ["review_evidence_id"])

    merge_review_table(
        RESEARCH / "05_item_mapping_master.csv", mapping_inputs,
        ["mapping_id"], "mapping_status", {"VERIFIED", "APP_READY"},
        sort_key=lambda row: (
            row["municipality_id"],
            row["internal_item_id"],
            int(row.get("branch_order") or 0),
            row["mapping_id"],
        ),
    )
    merge_review_table(
        RESEARCH / "07_item_mapping_coverage.csv", coverage_inputs,
        ["municipality_id", "internal_item_id"], "coverage_status", {"VERIFIED", "VERIFIED_NOT_APPLICABLE", "APP_READY"},
    )


if __name__ == "__main__":
    main()
