#!/usr/bin/env python3
"""Compatibility gate for regional lesson variants promoted to full APP_READY.

The original variant validator intentionally assumed every regional municipality was
canonical-40 DEFERRED and absent from the municipality-wide scoring scope.  PR #20
promotes M099 only after all 40 canonical items are APP_READY while retaining the
already-audited learner region selector.  This module removes only those two obsolete
boundary errors, and only when the canonical/scoring data proves the promotion.
"""
from __future__ import annotations

from pathlib import Path

import validate_lesson_variants as base

MID = "M099"
APP_READY = "APP_READY"


def _read_rows(path: Path):
    return base.read_rows(path)


def promotion_is_complete(root: Path = base.ROOT) -> bool:
    coverage_path = root / "data/research/07_item_mapping_coverage.csv"
    scope_path = root / base.STANDARD_SCOPE.relative_to(base.ROOT)
    deferred_path = root / base.DEFERRED.relative_to(base.ROOT)
    if not coverage_path.is_file() or not scope_path.is_file() or not deferred_path.is_file():
        return False

    rows = [r for r in _read_rows(coverage_path) if r.get("municipality_id") == MID]
    item_ids = {r.get("internal_item_id") for r in rows}
    if len(rows) != 40 or len(item_ids) != 40:
        return False
    if any(
        r.get("coverage_status") != APP_READY
        or r.get("branch_completeness_confirmed") != "TRUE"
        or r.get("evidence_scope") != "ITEM_SPECIFIC"
        for r in rows
    ):
        return False

    scope = [r for r in _read_rows(scope_path) if r.get("municipality_id") == MID]
    if len(scope) != 1 or scope[0].get("scoring_status") != APP_READY or scope[0].get("required_item_count") != "40":
        return False

    deferred = {r.get("municipality_id") for r in _read_rows(deferred_path)}
    return MID not in deferred


def filter_promotion_boundary_errors(errors: list[str], root: Path = base.ROOT) -> list[str]:
    if not promotion_is_complete(root):
        return list(errors)
    allowed = {
        f"{MID}: canonical 40-item DEFERRED boundary was removed",
        f"variant municipality injected into municipality-wide scoring scope: ['{MID}']",
    }
    return [error for error in errors if error not in allowed]


def configure() -> None:
    if getattr(base, "_classroom_pilot_m099_compat", False):
        return
    original_records = base.validate_records

    def compatible_validate_records(data, root: Path = base.ROOT):
        return filter_promotion_boundary_errors(original_records(data, root), root)

    def compatible_validate(root: Path = base.ROOT):
        return compatible_validate_records(base.records(), root)

    base.validate_records = compatible_validate_records
    base.validate = compatible_validate
    base._classroom_pilot_m099_compat = True
