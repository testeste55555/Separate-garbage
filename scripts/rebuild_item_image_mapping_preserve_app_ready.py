#!/usr/bin/env python3
"""Rebuild the historical image-mapping Pilot without downgrading APP_READY rows.

The Pilot generator predates municipality-wide APP_READY promotion. Its internal R
fixture remains useful for non-promoted municipalities, but it must not overwrite a
newer committed scoring row once a municipality is APP_READY. Snapshot those rows,
run the historical builder unchanged, then restore the authoritative rows in place.
"""
from __future__ import annotations

from pathlib import Path

import apply_item_image_mapping_pilot_top8 as pilot
from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
IMAGE_MAPPING = ROOT / "data/app/item_image_mapping_pilot_top8.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
APP_READY = "APP_READY"


def main() -> None:
    fields, before = read_csv(IMAGE_MAPPING)
    _, scope = read_csv(SCOPE)
    app_ready_mids = {
        row["municipality_id"]
        for row in scope
        if row.get("scoring_status") == APP_READY
    }
    frozen = {
        (row["municipality_id"], row["internal_item_id"]): dict(row)
        for row in before
        if row.get("municipality_id") in app_ready_mids
    }

    pilot.main()

    rebuilt_fields, rebuilt = read_csv(IMAGE_MAPPING)
    if rebuilt_fields != fields:
        raise ValueError("image mapping header changed during historical Pilot rebuild")

    restored = 0
    seen_frozen: set[tuple[str, str]] = set()
    for row in rebuilt:
        key = (row.get("municipality_id", ""), row.get("internal_item_id", ""))
        authoritative = frozen.get(key)
        if not authoritative:
            continue
        pair_order = row.get("pair_order", "")
        row.clear()
        row.update(authoritative)
        # Ordering is a projection concern; preserve the freshly rebuilt order while
        # restoring all evidence/scoring fields from the APP_READY snapshot.
        row["pair_order"] = pair_order
        restored += 1
        seen_frozen.add(key)

    missing = sorted(set(frozen) - seen_frozen)
    if missing:
        raise ValueError(f"APP_READY image rows disappeared during rebuild: {missing}")

    write_csv(IMAGE_MAPPING, fields, rebuilt)
    print(
        f"ITEM_IMAGE_PILOT_REBUILT app_ready_municipalities={len(app_ready_mids)} "
        f"frozen_rows={len(frozen)} restored={restored}"
    )


if __name__ == "__main__":
    main()
