#!/usr/bin/env python3
"""Run the existing scoring mutation RED TEAM with the M105 promotion expectation."""
from __future__ import annotations

import validate_lesson_scoring_modes as base

base.EXPECTED_REGRESSION_STATUS["M105"] = base.APP_READY

import red_team_lesson_scoring_modes as red_team  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(red_team.main())
