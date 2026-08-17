#!/usr/bin/env python3
"""Validate a completed research batch or the canonical 15-municipality set."""

from __future__ import annotations

import argparse

from validation_v11 import ROOT, print_result, validate_dataset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", help="batch directory under data/research/batches")
    args = parser.parse_args()
    if args.batch:
        base = ROOT / "data" / "research" / "batches" / args.batch
        prefix = f"{args.batch}_"
        paths = {
            "municipality_path": base / f"{prefix}municipalities.csv",
            "category_path": base / f"{prefix}categories.csv",
            "source_path": base / f"{prefix}sources.csv",
            "qa_path": base / f"{prefix}qa.csv",
        }
        label = args.batch.upper()
        expected = None
    else:
        base = ROOT / "data" / "research"
        paths = {
            "municipality_path": base / "04_municipalities_research.csv",
            "category_path": base / "02_categories_master.csv",
            "source_path": base / "03_sources_master.csv",
            "qa_path": base / "06_qa_log.csv",
        }
        label = "CANONICAL"
        expected = 15
    errors, summary = validate_dataset(label=label, expected_municipality_count=expected, **paths)
    return print_result(label, errors, summary)


if __name__ == "__main__":
    raise SystemExit(main())
