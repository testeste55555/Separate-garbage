#!/usr/bin/env python3
"""Idempotent rebuild entrypoint for M105 APP_READY.

Before first promotion the fixed-10 lesson review is the authoritative seed. After
promotion that review is intentionally removed, so subsequent rebuilds use the
committed 40-item APP_READY audit as the seed for the already-reviewed fixed items.
The underlying generator remains unchanged and this wrapper supplies the correct
review input for either lifecycle state.
"""
from __future__ import annotations

import apply_app_readiness_m105 as build


def rebuild_seed_branches() -> dict[str, list[build.Branch]]:
    source = build.LESSON_REVIEW if build.LESSON_REVIEW.exists() else build.AUDIT_PATH
    grouped: dict[str, list[build.Branch]] = {}
    for row in build.csv_rows(source):
        iid = row["internal_item_id"].strip()
        # Only the original fixed-10 items are sourced from the seed review. The
        # remaining 30 items are always supplied by EXTRA in the generator.
        if iid in build.EXTRA:
            continue
        grouped.setdefault(iid, []).append(build.b(
            row["category_id"].strip(),
            row["item_evidence_source_id"].strip(),
            row["item_evidence_locator"].strip(),
            row["official_item_wording"].strip(),
            "" if row["condition"].strip() == "該当なし" else row["condition"].strip(),
            "" if row["preparation"].strip() == "該当なし" else row["preparation"].strip(),
            "" if row["exception_destination"].strip() == "該当なし" else row["exception_destination"].strip(),
            row["evidence_basis"].strip() or "DIRECT_ITEM",
            row["note"].strip(),
        ))
    return grouped


if __name__ == "__main__":
    build.lesson_branches = rebuild_seed_branches
    build.main()
