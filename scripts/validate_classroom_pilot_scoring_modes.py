#!/usr/bin/env python3
"""Validate classroom-pilot scoring after APP_READY promotions."""
from __future__ import annotations

import sys

import validate_lesson_scoring_modes as base
from classroom_pilot_scoring_compat import configure

configure()

if __name__ == "__main__":
    errors = base.validate()
    if errors:
        print("CLASSROOM_PILOT_SCORING_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    print("CLASSROOM_PILOT_SCORING_VALIDATION_PASSED")
