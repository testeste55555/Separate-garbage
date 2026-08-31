#!/usr/bin/env python3
"""Validate lesson variants with the audited M099 APP_READY promotion boundary."""
from __future__ import annotations

import sys

import validate_lesson_variants as base
from classroom_pilot_variant_compat import configure

configure()

if __name__ == "__main__":
    errors = base.validate()
    if errors:
        print("CLASSROOM_PILOT_VARIANT_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    print("CLASSROOM_PILOT_VARIANT_VALIDATION_PASSED")
