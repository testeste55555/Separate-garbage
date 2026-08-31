#!/usr/bin/env python3
"""Run the historical Style Research mutation RED TEAM with APP_READY promotion compatibility."""
from __future__ import annotations

import validate_style_research_promotion_compat as compat

compat.configure()

import red_team_style_research as red_team  # noqa: E402


if __name__ == "__main__":
    red_team.main()
