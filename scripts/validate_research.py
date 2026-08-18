#!/usr/bin/env python3
"""Validate a completed research batch or the scalable canonical union."""

from __future__ import annotations

import argparse

from schema_v12 import completed_batch_dirs, read_csv
from validation_v12 import RESEARCH, ROOT, print_result, validate_dataset


def compare_canonical_union() -> list[str]:
    """Check canonical identity against Pilot + every completed batch."""
    errors = []
    pilot = RESEARCH / "pilot"
    bundles = [(pilot, "pilot_")] + [(path, path.name + "_") for path in completed_batch_dirs()]
    specs = [
        ("municipalities", RESEARCH / "04_municipalities_research.csv", ["municipality_id"]),
        ("categories", RESEARCH / "02_categories_master.csv", ["municipality_id", "category_id"]),
        ("sources", RESEARCH / "03_sources_master.csv", ["municipality_id", "source_id"]),
        ("qa", RESEARCH / "06_qa_log.csv", ["municipality_id"]),
        ("category_review_evidence", RESEARCH / "08_category_review_evidence.csv", ["review_evidence_id"]),
    ]
    for suffix, canonical_path, key_fields in specs:
        _, canonical_rows = read_csv(canonical_path)
        canonical = {tuple(row[field] for field in key_fields): row for row in canonical_rows}
        union = {}
        for base, prefix in bundles:
            path = base / f"{prefix}{suffix}.csv"
            if not path.exists():
                errors.append(f"completed bundle lacks {path.relative_to(ROOT)}")
                continue
            _, rows = read_csv(path)
            for row in rows:
                key = tuple(row[field] for field in key_fields)
                if key in union:
                    errors.append(f"duplicate bundle key in {suffix}: {key}")
                union[key] = row
        if canonical != union:
            errors.append(f"canonical {suffix} differs from Pilot + completed-batch union")
    for suffix, canonical_path, key_fields in [
        ("item_mapping", RESEARCH / "05_item_mapping_master.csv", ["mapping_id"]),
        ("item_coverage", RESEARCH / "07_item_mapping_coverage.csv", ["municipality_id", "internal_item_id"]),
    ]:
        _, canonical_rows = read_csv(canonical_path)
        canonical_keys = {tuple(row[field] for field in key_fields) for row in canonical_rows}
        union_keys = set()
        for base, prefix in bundles:
            path = base / f"{prefix}{suffix}.csv"
            if not path.exists():
                errors.append(f"completed bundle lacks {path.relative_to(ROOT)}")
                continue
            _, rows = read_csv(path)
            union_keys.update(tuple(row[field] for field in key_fields) for row in rows)
        if not union_keys.issubset(canonical_keys):
            errors.append(f"canonical {suffix} loses bundle keys: missing={len(union_keys - canonical_keys)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", help="batch directory under data/research/batches")
    gate_group = parser.add_mutually_exclusive_group()
    gate_group.add_argument("--next-batch-gate", action="store_true", help="require structural validity and QA_PASSED; mapping readiness is not required")
    gate_group.add_argument("--app-readiness-gate", action="store_true", help="require QA_PASSED and all 40 mappings to be app-ready")
    gate_group.add_argument("--gate", action="store_true", help="deprecated alias for --app-readiness-gate")
    args = parser.parse_args()
    if args.batch:
        base = ROOT / "data" / "research" / "batches" / args.batch
        prefix = f"{args.batch}_"
        paths = {
            "municipality_path": base / f"{prefix}municipalities.csv",
            "category_path": base / f"{prefix}categories.csv",
            "source_path": base / f"{prefix}sources.csv",
            "qa_path": base / f"{prefix}qa.csv",
            "mapping_path": base / f"{prefix}item_mapping.csv",
            "coverage_path": base / f"{prefix}item_coverage.csv",
            "review_evidence_path": base / f"{prefix}category_review_evidence.csv",
        }
        label = args.batch.upper()
    else:
        base = ROOT / "data" / "research"
        paths = {
            "municipality_path": base / "04_municipalities_research.csv",
            "category_path": base / "02_categories_master.csv",
            "source_path": base / "03_sources_master.csv",
            "qa_path": base / "06_qa_log.csv",
            "mapping_path": base / "05_item_mapping_master.csv",
            "coverage_path": base / "07_item_mapping_coverage.csv",
            "review_evidence_path": base / "08_category_review_evidence.csv",
        }
        label = "CANONICAL"
    gate_mode = "next_batch" if args.next_batch_gate else "app_readiness" if args.app_readiness_gate or args.gate else None
    errors, gate_errors, summary = validate_dataset(label=label, gate_mode=gate_mode, **paths)
    if not args.batch:
        errors.extend(compare_canonical_union())
    return print_result(label, errors, gate_errors, summary, gate_mode)


if __name__ == "__main__":
    raise SystemExit(main())
