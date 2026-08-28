#!/usr/bin/env python3
"""Mutation RED TEAM for priority/readiness/company-link separation."""

from __future__ import annotations

import csv
import shutil
import sys
import tempfile
from pathlib import Path

from validate_implementation_priority import ROOT, validate


def mutate(root: Path, change) -> None:
    path = root / "data/master/07_implementation_priority.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, records = list(reader.fieldnames or []), list(reader)
    change(records)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def record(rows: list[dict[str, str]], mid: str) -> dict[str, str]:
    return next(row for row in rows if row["municipality_id"] == mid)


def main() -> int:
    if validate():
        print("IMPLEMENTATION_PRIORITY_RED_TEAM_BASELINE_FAILED")
        return 1
    cases = [
        ("unconfirmed municipality labelled NO_COMPANY", lambda rows: record(rows, "M065").update({"company_link_status": "NO_COMPANY"})),
        ("company candidate promoted to ready", lambda rows: record(rows, "M029").update({"implementation_status": "IMPLEMENTED", "readiness_status_snapshot": "LESSON_READY_10"})),
        ("ready municipality demoted for company state", lambda rows: record(rows, "M120").update({"implementation_status": "NOT_IMPLEMENTED"})),
        ("individual priority removed", lambda rows: record(rows, "M136").update({"priority_status": "STANDARD"})),
        ("non-priority municipality promoted", lambda rows: record(rows, "M065").update({"priority_status": "PRIORITY"})),
        ("deferred M086 marked implemented", lambda rows: record(rows, "M086").update({"implementation_status": "IMPLEMENTED"})),
    ]
    escaped = []
    for label, change in cases:
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "repo"
            shutil.copytree(ROOT, candidate, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            mutate(candidate, change)
            if not validate(candidate):
                escaped.append(label)
    if escaped:
        print("IMPLEMENTATION_PRIORITY_RED_TEAM_FAILED")
        for label in escaped:
            print(f"- mutation escaped validator: {label}")
        return 1
    print(f"IMPLEMENTATION_PRIORITY_RED_TEAM_PASSED mutations={len(cases)}/{len(cases)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
