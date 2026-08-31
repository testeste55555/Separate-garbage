#!/usr/bin/env python3
"""Rebuild historical Style Research while preserving reviewed APP_READY UI overlays."""
from __future__ import annotations

import csv
from pathlib import Path

import build_style_research_pilot as pilot

ROOT = Path(__file__).resolve().parents[1]
PROJECTION = ROOT / "data/style_research/08_style_ui_projection.csv"
OVERLAY_PREFIXES = ("APP-STP-M099-",)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def is_overlay(row: dict[str, str]) -> bool:
    projection_id = row.get("projection_id", "")
    return any(projection_id.startswith(prefix) for prefix in OVERLAY_PREFIXES)


def main() -> None:
    fields_before, rows_before = read_csv(PROJECTION)
    overlays = [dict(row) for row in rows_before if is_overlay(row)]

    pilot.main()

    fields_after, rows_after = read_csv(PROJECTION)
    if fields_after != fields_before:
        raise ValueError("style projection header changed during historical rebuild")
    historical = [row for row in rows_after if not is_overlay(row)]
    write_csv(PROJECTION, fields_after, historical + overlays)
    print(f"STYLE_RESEARCH_REBUILT_PRESERVING_APP_READY overlays={len(overlays)}")


if __name__ == "__main__":
    main()
