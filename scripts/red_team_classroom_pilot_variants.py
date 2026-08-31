#!/usr/bin/env python3
"""Run regional-variant mutation RED TEAM with the audited M099 promotion boundary."""
from __future__ import annotations

import validate_lesson_variants as base
from classroom_pilot_variant_compat import configure

# Configure before importing the RED TEAM module: it imports validate functions by value.
configure()

import red_team_lesson_variants as red_team  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(red_team.main())
