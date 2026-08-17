#!/usr/bin/env python3
"""Validate immutable Pilot files independently from canonical QA output."""

from __future__ import annotations

import argparse

from validation_v12 import RESEARCH, print_result, validate_dataset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true", help="also require QA and all 40 mappings to be app-ready")
    args = parser.parse_args()
    pilot = RESEARCH / "pilot"
    errors, gate_errors, summary = validate_dataset(
        label="PILOT",
        municipality_path=pilot / "pilot_municipalities.csv",
        category_path=pilot / "pilot_categories.csv",
        source_path=pilot / "pilot_sources.csv",
        qa_path=pilot / "pilot_qa.csv",
        mapping_path=pilot / "pilot_item_mapping.csv",
        coverage_path=pilot / "pilot_item_coverage.csv",
        gate=args.gate,
    )
    return print_result("PILOT", errors, gate_errors, summary, args.gate)


if __name__ == "__main__":
    raise SystemExit(main())
