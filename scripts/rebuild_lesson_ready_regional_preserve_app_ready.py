#!/usr/bin/env python3
"""Rebuild regional LESSON_READY data without regressing promoted APP_READY metadata."""
from __future__ import annotations

from pathlib import Path

import build_lesson_ready_regional_batch as regional
from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
PRIORITY = ROOT / "data/master/07_implementation_priority.csv"
APP_READY = "APP_READY"


def main() -> None:
    fields, before = read_csv(PRIORITY)
    frozen = {
        row["municipality_id"]: dict(row)
        for row in before
        if row.get("readiness_status_snapshot") == APP_READY
    }

    regional.main()

    rebuilt_fields, after = read_csv(PRIORITY)
    if rebuilt_fields != fields:
        raise ValueError("implementation priority header changed during regional rebuild")
    restored = 0
    for row in after:
        authoritative = frozen.get(row.get("municipality_id", ""))
        if not authoritative:
            continue
        row.clear()
        row.update(authoritative)
        restored += 1
    if restored != len(frozen):
        raise ValueError(f"APP_READY priority rows disappeared: expected={len(frozen)} restored={restored}")
    write_csv(PRIORITY, fields, after)
    print(f"REGIONAL_LESSON_REBUILT app_ready_priority_rows_preserved={restored}")


if __name__ == "__main__":
    main()
