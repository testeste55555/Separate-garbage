#!/usr/bin/env python3
"""Validate immutable Pilot files independently from canonical QA output."""

from __future__ import annotations

from validation_v11 import RESEARCH, print_result, validate_dataset


def main() -> int:
    pilot = RESEARCH / "pilot"
    errors, summary = validate_dataset(
        label="PILOT",
        municipality_path=pilot / "pilot_municipalities.csv",
        category_path=pilot / "pilot_categories.csv",
        source_path=pilot / "pilot_sources.csv",
        qa_path=pilot / "pilot_qa.csv",
        expected_municipality_count=5,
    )
    return print_result("PILOT", errors, summary)


if __name__ == "__main__":
    raise SystemExit(main())
