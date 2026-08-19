#!/usr/bin/env python3
"""Build active Batch 08 while preserving deferred Bizen research outside canonical.

M076 備前市 is deferred because FY2026 still has two resident-facing sorting
systems by district. The current Schema/UI has no district-variant selector, so
forcing either system city-wide would create incorrect guidance.

This wrapper is the production Batch 08 entrypoint: only active municipalities
are emitted into the completed bundle and canonical merge.
"""
from __future__ import annotations

import build_batch_08 as batch

DEFERRED={"M076"}


def main() -> None:
    for mid in DEFERRED:
        batch.TARGETS.discard(mid)
        batch.PASS_TARGETS.discard(mid)
        batch.municipality_specs.pop(mid, None)
        batch.source_specs.pop(mid, None)
    batch.cats[:] = [row for row in batch.cats if row.get("municipality_id") not in DEFERRED]
    batch.main()


if __name__ == "__main__":
    main()
