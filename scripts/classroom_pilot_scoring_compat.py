#!/usr/bin/env python3
"""Compatibility gate for APP_READY municipalities that keep regional fixed-10 scoring.

M098 and M099 use their audited lesson-variant matrices for the ten learner images. They
must not receive fake municipality-wide image mappings merely to satisfy the legacy
scoring validator. APP_READY expectations are enabled only after the complete 40-item
promotion exists in the checked worktree.

M098 I028 (button battery) is intentionally non-interactive. Its canonical route is an
internal REFERENCE_ONLY retailer take-back path supported by municipal supplemental
evidence; it is not allowed to become a guessed dry-battery learner answer.
"""
from __future__ import annotations

from pathlib import Path

import validate_lesson_scoring_modes as base
import classroom_pilot_variant_compat as variant_compat

REGIONAL_MIDS = ("M098", "M099")


def _regional_variant_valid(root: Path) -> bool:
    variant_compat.configure()
    return not variant_compat.base.validate(root)


def _m098_button_route_valid(root: Path) -> bool:
    review_path = root / "data/research/app_readiness/m098_item_review.csv"
    sources_path = root / "data/research/03_sources_master.csv"
    categories_path = root / "data/research/02_categories_master.csv"
    if not review_path.is_file() or not sources_path.is_file() or not categories_path.is_file():
        return False
    rows = [r for r in base.read_rows(review_path) if r.get("internal_item_id") == "I028"]
    if len(rows) != 1:
        return False
    row = rows[0]
    if (
        row.get("category_id") != "C-M098-10"
        or row.get("item_evidence_source_id") != "S-M098-12"
        or row.get("branch_review_status") != "COMPLETE"
    ):
        return False
    sources = {
        (r.get("municipality_id"), r.get("source_id")): r
        for r in base.read_rows(sources_path)
    }
    source = sources.get(("M098", "S-M098-12"), {})
    categories = {
        (r.get("municipality_id"), r.get("category_id")): r
        for r in base.read_rows(categories_path)
    }
    category = categories.get(("M098", "C-M098-10"), {})
    return (
        source.get("official_verified") == "TRUE"
        and source.get("公式URL") == row.get("item_evidence_url")
        and category.get("ui_role") == "REFERENCE_ONLY"
        and category.get("collection_channel") == "RETAILER_OR_MAKER"
        and "I028" not in base.EXPECTED_IMAGE_ITEMS_SET
    )


def configure() -> None:
    if getattr(base, "_classroom_pilot_regional_scoring_compat", False):
        return

    base.EXPECTED_REGRESSION_STATUS["M105"] = base.APP_READY
    for mid in REGIONAL_MIDS:
        if variant_compat.promotion_is_complete(base.ROOT, mid):
            base.EXPECTED_REGRESSION_STATUS[mid] = base.APP_READY
        else:
            base.EXPECTED_REGRESSION_STATUS.pop(mid, None)

    original_validate = base.validate

    def compatible_validate(root: Path = base.ROOT):
        errors = original_validate(root)
        complete = {
            mid for mid in REGIONAL_MIDS
            if variant_compat.promotion_is_complete(root, mid)
        }
        if not complete or not _regional_variant_valid(root):
            return errors

        scope = base.read_rows(root / base.LESSON_SCOPE.relative_to(base.ROOT))
        scope_by_mid = {row.get("municipality_id"): row for row in scope}
        active_regional = {
            mid for mid in complete
            if scope_by_mid.get(mid, {}).get("scoring_status") == base.APP_READY
        }
        if not active_regional:
            return errors

        for mid in active_regional:
            image_rows = [
                row for row in base.read_rows(root / base.IMAGE_MAPPING.relative_to(base.ROOT))
                if row.get("municipality_id") == mid
            ]
            # Regional fixed-10 data is the only learner-scoring source for these municipalities.
            # Any generic image row would reintroduce a hidden municipality-wide answer.
            if image_rows:
                return errors + [f"{mid}: generic image mapping must remain absent for regional APP_READY"]

        expected_total = base.EXPECTED_IMAGE_ITEMS * len(scope)
        regional_delta = base.EXPECTED_IMAGE_ITEMS * len(active_regional)
        allowed = {
            f"{mid}: expected {base.EXPECTED_IMAGE_ITEMS} interactive image questions, got 0"
            for mid in active_regional
        }
        allowed.add(
            f"interactive image pair count mismatch: expected={expected_total} actual={expected_total - regional_delta}"
        )
        if "M098" in active_regional and _m098_button_route_valid(root):
            allowed.add("M098/I028/1: source is not current official evidence")
        return [error for error in errors if error not in allowed]

    base.validate = compatible_validate
    base._classroom_pilot_regional_scoring_compat = True
