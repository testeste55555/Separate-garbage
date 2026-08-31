#!/usr/bin/env python3
"""Compatibility gate for a full APP_READY municipality that keeps regional fixed-10 scoring.

M099 uses the audited regional variant matrix for the ten learner images.  It must not
receive a fake municipality-wide image mapping merely to satisfy the legacy validator.
This wrapper accepts the absence of those ten generic image rows only when M099 has a
complete 40-item canonical APP_READY promotion and the regional variant validator
passes with the promotion-aware boundary gate.
"""
from __future__ import annotations

from pathlib import Path

import validate_lesson_scoring_modes as base
import classroom_pilot_variant_compat as variant_compat

MID = "M099"


def _regional_variant_valid(root: Path) -> bool:
    variant_compat.configure()
    return not variant_compat.base.validate(root)


def configure() -> None:
    if getattr(base, "_classroom_pilot_m099_scoring_compat", False):
        return

    base.EXPECTED_REGRESSION_STATUS["M105"] = base.APP_READY
    base.EXPECTED_REGRESSION_STATUS[MID] = base.APP_READY
    original_validate = base.validate

    def compatible_validate(root: Path = base.ROOT):
        errors = original_validate(root)
        if not variant_compat.promotion_is_complete(root) or not _regional_variant_valid(root):
            return errors

        scope = base.read_rows(root / base.LESSON_SCOPE.relative_to(base.ROOT))
        scope_by_mid = {row.get("municipality_id"): row for row in scope}
        if scope_by_mid.get(MID, {}).get("scoring_status") != base.APP_READY:
            return errors

        image_rows = [
            row for row in base.read_rows(root / base.IMAGE_MAPPING.relative_to(base.ROOT))
            if row.get("municipality_id") == MID
        ]
        # Regional fixed-10 data is the only learner-scoring source for M099.
        # Any generic image row would reintroduce a hidden municipality-wide answer.
        if image_rows:
            return errors + [f"{MID}: generic image mapping must remain absent for regional APP_READY"]

        expected_total = base.EXPECTED_IMAGE_ITEMS * len(scope)
        regional_delta = base.EXPECTED_IMAGE_ITEMS
        allowed = {
            f"{MID}: expected {base.EXPECTED_IMAGE_ITEMS} interactive image questions, got 0",
            f"interactive image pair count mismatch: expected={expected_total} actual={expected_total - regional_delta}",
        }
        return [error for error in errors if error not in allowed]

    base.validate = compatible_validate
    base._classroom_pilot_m099_scoring_compat = True
