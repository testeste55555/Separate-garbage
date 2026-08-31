#!/usr/bin/env python3
"""Idempotent M099 APP_READY entry point used by CI.

The APP review keeps only the learner-relevant/municipal collection branch for I040.
The official pruning page still records that larger quantities may be directly hauled,
but that transport option is an exception_destination, not the generic public drop-off
category used for small appliances, batteries and old paper.
"""
from __future__ import annotations

import apply_app_readiness_m099 as build


def main() -> None:
    pruning = build.RULES["I040"]
    if not pruning:
        raise ValueError("M099 I040 pruning review is empty")
    build.RULES["I040"] = [pruning[0]]
    build.main()


if __name__ == "__main__":
    main()
