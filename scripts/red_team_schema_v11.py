#!/usr/bin/env python3
"""Deprecated compatibility entrypoint for the scalable Schema v1.2 RED TEAM."""

from red_team_schema_v12 import main


if __name__ == "__main__":
    print("NOTICE: Schema v1.1 RED TEAM is retired; running Schema v1.2 checks")
    raise SystemExit(main())
