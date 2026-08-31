#!/usr/bin/env python3
"""Rebuild the historical image-mapping Pilot without downgrading APP_READY rows.

The Pilot generator predates municipality-wide APP_READY promotion. Its internal R
fixture remains useful for non-promoted municipalities, but it must not overwrite or
drop a newer committed scoring row once a municipality is APP_READY. Snapshot those
rows, run the historical builder unchanged, restore matching rows, and preserve the
committed pair ordering as the stable projection order.

Regional APP_READY municipalities such as M099 intentionally have no municipality-wide
image rows, so nothing is fabricated for them here.
"""
from __future__ import annotations

from pathlib import Path

import apply_item_image_mapping_pilot_top8 as pilot
from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
IMAGE_MAPPING = ROOT / "data/app/item_image_mapping_pilot_top8.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
APP_READY = "APP_READY"


def row_key(row: dict[str, str]) -> tuple[str, str]:
    return row.get("municipality_id", ""), row.get("internal_item_id", "")


def main() -> None:
    fields, before = read_csv(IMAGE_MAPPING)
    _, scope = read_csv(SCOPE)
    app_ready_mids = {
        row["municipality_id"]
        for row in scope
        if row.get("scoring_status") == APP_READY
    }
    frozen = {
        row_key(row): dict(row)
        for row in before
        if row.get("municipality_id") in app_ready_mids
    }
    committed_order = [row_key(row) for row in before]

    pilot.main()

    rebuilt_fields, rebuilt = read_csv(IMAGE_MAPPING)
    if rebuilt_fields != fields:
        raise ValueError("image mapping header changed during historical Pilot rebuild")

    rebuilt_by_key = {row_key(row): dict(row) for row in rebuilt}
    if len(rebuilt_by_key) != len(rebuilt):
        raise ValueError("historical Pilot rebuild produced duplicate municipality/item pairs")

    # Restore APP_READY evidence/scoring fields. Ordering is handled separately below;
    # it is a projection concern and must not change merely because a municipality was
    # promoted after the historical Pilot fixture was created.
    restored = 0
    for key in set(rebuilt_by_key) & set(frozen):
        rebuilt_by_key[key] = dict(frozen[key])
        restored += 1

    # A newly promoted APP_READY municipality can post-date the historical Pilot
    # fixture entirely. Preserve its already-reviewed image rows instead of treating
    # their absence from that historical fixture as an error.
    appended = 0
    for key in sorted(set(frozen) - set(rebuilt_by_key)):
        rebuilt_by_key[key] = dict(frozen[key])
        appended += 1

    # Preserve the committed pair sequence for every pair that still exists. This
    # makes a no-op rebuild genuinely idempotent while still allowing semantic changes
    # from the historical builder to surface as a git diff. Any genuinely new pair is
    # appended deterministically after the established sequence.
    ordered: list[dict[str, str]] = []
    emitted: set[tuple[str, str]] = set()
    for key in committed_order:
        row = rebuilt_by_key.get(key)
        if row is None or key in emitted:
            continue
        ordered.append(row)
        emitted.add(key)
    for key in sorted(set(rebuilt_by_key) - emitted):
        ordered.append(rebuilt_by_key[key])
        emitted.add(key)

    for order, row in enumerate(ordered, start=1):
        row["pair_order"] = str(order)

    write_csv(IMAGE_MAPPING, fields, ordered)
    print(
        f"ITEM_IMAGE_PILOT_REBUILT app_ready_municipalities={len(app_ready_mids)} "
        f"frozen_rows={len(frozen)} restored={restored} appended={appended} "
        f"rows={len(ordered)}"
    )


if __name__ == "__main__":
    main()
