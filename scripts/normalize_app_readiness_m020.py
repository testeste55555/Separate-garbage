#!/usr/bin/env python3
"""Normalize M020 promotion outputs to repository source/channel ownership rules.

- IS-* item-evidence sources live only in canonical as merge-preserved supplements;
  they must not be duplicated inside the historical Batch 02 ordinary-source bundle.
- M020 PET collection channel differs by district (drop-off in 葵・駿河, curbside in
  清水). Schema v1.2 has no mixed-channel enum, so leave the optional channel blank
  rather than encode a false municipality-wide channel. The exact district behavior
  remains in the category and item evidence text.
"""
from __future__ import annotations

from pathlib import Path

from schema_v12 import CATEGORY_FIELDS, SOURCE_FIELDS, read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M020"


def main() -> None:
    batch_sources = ROOT / "data/research/batches/batch_02/batch_02_sources.csv"
    _, rows = read_csv(batch_sources)
    rows = [
        row for row in rows
        if not (row.get("municipality_id") == MID and row.get("source_id", "").startswith("IS-"))
    ]
    write_csv(batch_sources, SOURCE_FIELDS, sorted(rows, key=lambda r: (r["municipality_id"], r["source_id"])))

    for path in [
        ROOT / "data/research/02_categories_master.csv",
        ROOT / "data/research/batches/batch_02/batch_02_categories.csv",
    ]:
        _, categories = read_csv(path)
        for row in categories:
            if row.get("municipality_id") == MID and row.get("category_id") == "C-M020-10":
                row["collection_channel"] = ""
        write_csv(path, CATEGORY_FIELDS, categories)

    print("M020_APP_READY_NORMALIZED batch_item_sources=canonical_only pet_channel=explicitly_unspecified")


if __name__ == "__main__":
    main()
