#!/usr/bin/env python3
"""Build Batch 07 with the current active target set.

M065 知夫村 is intentionally deferred by user decision on 2026-08-19.
Its fixed MASTER ID and previously gathered source notes are retained outside
this active Batch; the Batch itself contains only the nine municipalities that
are currently in implementation scope.
"""
from __future__ import annotations

import build_batch_07 as batch

DEFERRED = {"M065"}


def main() -> None:
    for mid in DEFERRED:
        batch.TARGETS.discard(mid)
        batch.PASS_TARGETS.discard(mid)
        batch.municipality_specs.pop(mid, None)
        batch.source_specs.pop(mid, None)
    batch.main()


if __name__ == "__main__":
    main()
