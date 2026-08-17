#!/usr/bin/env python3
"""Validate immutable Pilot files independently from canonical QA output."""

from __future__ import annotations

import argparse

from validation_v12 import RESEARCH, print_result, validate_dataset


def main() -> int:
    parser = argparse.ArgumentParser()
    gate_group = parser.add_mutually_exclusive_group()
    gate_group.add_argument("--next-batch-gate", action="store_true", help="require structural validity and QA_PASSED")
    gate_group.add_argument("--app-readiness-gate", action="store_true", help="also require all 40 mappings to be app-ready")
    gate_group.add_argument("--gate", action="store_true", help="deprecated alias for --app-readiness-gate")
    args = parser.parse_args()
    pilot = RESEARCH / "pilot"
    gate_mode = "next_batch" if args.next_batch_gate else "app_readiness" if args.app_readiness_gate or args.gate else None
    errors, gate_errors, summary = validate_dataset(
        label="PILOT",
        municipality_path=pilot / "pilot_municipalities.csv",
        category_path=pilot / "pilot_categories.csv",
        source_path=pilot / "pilot_sources.csv",
        qa_path=pilot / "pilot_qa.csv",
        mapping_path=pilot / "pilot_item_mapping.csv",
        coverage_path=pilot / "pilot_item_coverage.csv",
        gate_mode=gate_mode,
    )
    return print_result("PILOT", errors, gate_errors, summary, gate_mode)


if __name__ == "__main__":
    raise SystemExit(main())
