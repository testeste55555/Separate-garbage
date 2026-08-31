#!/usr/bin/env python3
"""Validate historical Style Research after a regional municipality is APP_READY.

The Style Research pilot intentionally recorded M098/M099 as canonical-DEFERRED at the
time of that audit and therefore created no municipality-wide official category color
projection for them. A later 40-item APP_READY promotion must not rewrite that historical
style decision or invent colors. This compatibility layer only lets the historical style
validator see the old DEFERRED boundary when the current repository independently proves
that the municipality has since been atomically promoted to APP_READY.
"""
from __future__ import annotations

from pathlib import Path

import validate_style_research as base

PROMOTABLE = {"M098", "M099"}
APP_READY = "APP_READY"


def _rows(path: Path):
    return base.read_csv(path)


def promotion_is_complete(root: Path, mid: str) -> bool:
    coverage_path = root / "data/research/07_item_mapping_coverage.csv"
    scope_path = root / "data/app/lesson_mode_app_ready_scope.csv"
    deferred_path = root / "data/master/05_deferred_municipalities.csv"
    if not coverage_path.is_file() or not scope_path.is_file() or not deferred_path.is_file():
        return False

    coverage = [r for r in _rows(coverage_path) if r.get("municipality_id") == mid]
    if len(coverage) != 40 or len({r.get("internal_item_id") for r in coverage}) != 40:
        return False
    if any(
        r.get("coverage_status") != APP_READY
        or r.get("branch_completeness_confirmed") != "TRUE"
        or r.get("evidence_scope") != "ITEM_SPECIFIC"
        for r in coverage
    ):
        return False

    scope = [r for r in _rows(scope_path) if r.get("municipality_id") == mid]
    if len(scope) != 1 or scope[0].get("scoring_status") != APP_READY or scope[0].get("required_item_count") != "40":
        return False

    deferred = {r.get("municipality_id") for r in _rows(deferred_path)}
    return mid not in deferred


def configure() -> None:
    if getattr(base, "_style_promotion_compat", False):
        return
    original_read_csv = base.read_csv

    def compatible_read_csv(path: Path):
        rows = original_read_csv(path)
        if path.name != "05_deferred_municipalities.csv":
            return rows
        root = path.parents[2]
        existing = {row.get("municipality_id") for row in rows}
        for mid in sorted(PROMOTABLE):
            if mid not in existing and promotion_is_complete(root, mid):
                # The base style validator only reads municipality_id from this snapshot.
                rows.append({"municipality_id": mid})
        return rows

    base.read_csv = compatible_read_csv
    base._style_promotion_compat = True


def main() -> None:
    configure()
    base.main()


if __name__ == "__main__":
    main()
