#!/usr/bin/env python3
"""Idempotently migrate all existing research bundles to Schema v1.2."""

from __future__ import annotations

from schema_v12 import RESEARCH, completed_batch_dirs, migrate_batch_dir, migrate_bundle


def main() -> None:
    pilot = RESEARCH / "pilot"
    results = {
        "pilot": migrate_bundle(
            pilot / "pilot_municipalities.csv", pilot / "pilot_categories.csv", pilot / "pilot_sources.csv",
            pilot / "pilot_qa.csv", pilot / "pilot_item_mapping.csv", pilot / "pilot_item_coverage.csv",
        )
    }
    for batch in completed_batch_dirs():
        results[batch.name] = migrate_batch_dir(batch)
    results["canonical"] = migrate_bundle(
        RESEARCH / "04_municipalities_research.csv", RESEARCH / "02_categories_master.csv",
        RESEARCH / "03_sources_master.csv", RESEARCH / "06_qa_log.csv",
        RESEARCH / "05_item_mapping_master.csv", RESEARCH / "07_item_mapping_coverage.csv",
    )
    print("SCHEMA_V12_MIGRATION_COMPLETED")
    for label, counts in results.items():
        print(label + " " + " ".join(f"{key}={value}" for key, value in counts.items()))


if __name__ == "__main__":
    main()
