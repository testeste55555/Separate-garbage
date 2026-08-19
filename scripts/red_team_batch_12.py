#!/usr/bin/env python3
"""Compatibility entrypoint for the current Batch 12 RED TEAM.

The production checks live in red_team_batch_12_active.py because Batch 12 has
projection-only refinements for M116 and M121. Keep this filename runnable so
legacy commands do not execute the superseded pre-refinement checks.
"""
from red_team_batch_12_active import main


if __name__ == "__main__":
    raise SystemExit(main())
