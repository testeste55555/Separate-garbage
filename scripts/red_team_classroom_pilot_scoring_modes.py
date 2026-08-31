#!/usr/bin/env python3
"""Run the scoring mutation RED TEAM with classroom-pilot APP_READY expectations."""
from __future__ import annotations

import validate_lesson_scoring_modes as base
from classroom_pilot_scoring_compat import configure

# Configure before importing the RED TEAM module: it imports validate() by value.
configure()

import red_team_lesson_scoring_modes as red_team  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(red_team.main())
