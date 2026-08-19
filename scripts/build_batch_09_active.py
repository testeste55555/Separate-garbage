#!/usr/bin/env python3
"""Production entrypoint for Batch 09.

M086 新庄村 is deferred outside the active bundle. The wrapper also normalizes
parent/child classification_level literals to the established Schema convention
(PRIMARY parent / SUBCATEGORY child) before importing the builder.
"""
from __future__ import annotations

from pathlib import Path
import importlib


def _normalize_builder_levels() -> None:
    path = Path(__file__).with_name("build_batch_09.py")
    text = path.read_text(encoding="utf-8")
    fixed = text.replace('level="PROJECTION_PARENT"', 'level="PRIMARY"')
    fixed = fixed.replace('level="OFFICIAL_CHILD"', 'level="SUBCATEGORY"')
    if fixed != text:
        path.write_text(fixed, encoding="utf-8")


def main() -> None:
    _normalize_builder_levels()
    batch = importlib.import_module("build_batch_09")
    batch.main()


if __name__ == "__main__":
    main()
