#!/usr/bin/env python3
"""Run the operational NEXT_BATCH_GATE without requiring APP_READY mappings."""

from __future__ import annotations

import hashlib
from pathlib import Path

from merge_research import main as merge_main
from red_team_schema_v12 import main as red_team_main
from schema_v12 import RESEARCH, completed_batch_dirs
from validate_research import compare_canonical_union
from validation_v12 import validate_dataset


CANONICAL_FILES = [
    RESEARCH / "04_municipalities_research.csv", RESEARCH / "02_categories_master.csv",
    RESEARCH / "03_sources_master.csv", RESEARCH / "06_qa_log.csv",
    RESEARCH / "05_item_mapping_master.csv", RESEARCH / "07_item_mapping_coverage.csv",
]


def bundle_paths(base: Path, prefix: str) -> dict[str, Path]:
    return {
        "municipality_path": base / f"{prefix}municipalities.csv",
        "category_path": base / f"{prefix}categories.csv",
        "source_path": base / f"{prefix}sources.csv",
        "qa_path": base / f"{prefix}qa.csv",
        "mapping_path": base / f"{prefix}item_mapping.csv",
        "coverage_path": base / f"{prefix}item_coverage.csv",
    }


def canonical_paths() -> dict[str, Path]:
    return {
        "municipality_path": RESEARCH / "04_municipalities_research.csv",
        "category_path": RESEARCH / "02_categories_master.csv",
        "source_path": RESEARCH / "03_sources_master.csv",
        "qa_path": RESEARCH / "06_qa_log.csv",
        "mapping_path": RESEARCH / "05_item_mapping_master.csv",
        "coverage_path": RESEARCH / "07_item_mapping_coverage.csv",
    }


def hashes() -> dict[str, str]:
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in CANONICAL_FILES}


def main() -> int:
    datasets = [("PILOT", bundle_paths(RESEARCH / "pilot", "pilot_"))]
    datasets.extend(
        (batch.name.upper(), bundle_paths(batch, batch.name + "_")) for batch in completed_batch_dirs()
    )
    datasets.append(("CANONICAL", canonical_paths()))
    structural_errors: list[str] = []
    for label, paths in datasets:
        errors, _, _ = validate_dataset(label=label, **paths)
        structural_errors.extend(f"{label}: {error}" for error in errors)
    structural_errors.extend(compare_canonical_union())

    _, gate_errors, _ = validate_dataset(
        label="CANONICAL", gate_mode="next_batch", **canonical_paths()
    )

    before = hashes()
    merge_main()
    first = hashes()
    merge_main()
    second = hashes()
    if not (before == first == second):
        structural_errors.append("canonical merge is not a no-change idempotent operation")
    structural_errors.extend(compare_canonical_union())

    red_team_code = red_team_main()
    if red_team_code:
        structural_errors.append("Schema v1.2.2 RED TEAM failed")

    if structural_errors:
        print("NEXT_BATCH_GATE_FAILED")
        for error in structural_errors:
            print(f"- {error}")
        return 1
    if gate_errors:
        print("NEXT_BATCH_GATE_HOLD")
        for error in gate_errors:
            print(f"- {error}")
        return 2
    print("NEXT_BATCH_GATE_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
