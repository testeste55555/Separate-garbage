#!/usr/bin/env python3
"""Validate scoring modes after the classroom-pilot M105 APP_READY promotion.

All validation logic remains in validate_lesson_scoring_modes.py.  This wrapper only
updates the explicit regression expectation for the municipality intentionally
promoted by this PR.
"""
from __future__ import annotations

import sys

import validate_lesson_scoring_modes as base

base.EXPECTED_REGRESSION_STATUS["M105"] = base.APP_READY

if __name__ == "__main__":
    errors = base.validate()
    if errors:
        print("CLASSROOM_PILOT_SCORING_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    print("CLASSROOM_PILOT_SCORING_VALIDATION_PASSED")
