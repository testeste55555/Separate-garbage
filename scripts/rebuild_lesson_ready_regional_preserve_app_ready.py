#!/usr/bin/env python3
"""Rebuild regional LESSON_READY data without regressing unrelated priority metadata."""
from __future__ import annotations

from pathlib import Path

import build_lesson_ready_regional_batch as regional
from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
PRIORITY = ROOT / "data/master/07_implementation_priority.csv"
VARIANT_SOURCES = ROOT / "data/research/lesson_readiness/lesson_variant_sources.csv"
APP_READY = "APP_READY"


def _signature(rows: list[dict[str, str]], fields: list[str]) -> list[tuple[str, ...]]:
    return sorted(tuple(row.get(field, "") for field in fields) for row in rows)


def main() -> None:
    fields, before = read_csv(PRIORITY)
    source_fields, sources_before = read_csv(VARIANT_SOURCES)

    # The historical regional builder owns only regional.TARGETS.  Preserve every
    # non-target municipality exactly as committed so a regional rebuild cannot
    # regress a newly promoted non-regional municipality (for example M021/M027).
    # Also preserve APP_READY rows even when a regional target was later promoted.
    frozen = {
        row["municipality_id"]: dict(row)
        for row in before
        if row.get("municipality_id") not in regional.TARGETS
        or row.get("readiness_status_snapshot") == APP_READY
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
        raise ValueError(
            f"preserved priority rows disappeared: expected={len(frozen)} restored={restored}"
        )
    write_csv(PRIORITY, fields, after)

    # The regional builder may normalize provenance row ordering. Ordering alone is
    # not evidence; if row content is unchanged, retain the committed order so the
    # rebuild remains idempotent.
    rebuilt_source_fields, sources_after = read_csv(VARIANT_SOURCES)
    if rebuilt_source_fields != source_fields:
        raise ValueError("lesson variant source header changed during regional rebuild")
    if _signature(sources_before, source_fields) == _signature(sources_after, source_fields):
        write_csv(VARIANT_SOURCES, source_fields, sources_before)

    print(f"REGIONAL_LESSON_REBUILT preserved_priority_rows={restored}")


if __name__ == "__main__":
    main()
