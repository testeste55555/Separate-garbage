#!/usr/bin/env python3
"""Validate implementation priority as a layer independent from readiness."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIORITY_A = {f"M{i:03d}" for i in range(1, 29)} | {f"M{i:03d}" for i in range(136, 144)}
PRIORITY_B = {
    "M029", "M030", "M032", "M042", "M048", "M050", "M052", "M055", "M067", "M068",
    "M070", "M071", "M072", "M078", "M096", "M101", "M117", "M120", "M121", "M123",
    "M128", "M131", "M133", "M135",
}


def rows(path: str, root: Path = ROOT) -> list[dict[str, str]]:
    with (root / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    municipalities = {row["municipality_id"]: row for row in rows("data/master/01_municipalities_master.csv", root)}
    priority = rows("data/master/07_implementation_priority.csv", root)
    standard = {row["municipality_id"]: row["scoring_status"] for row in rows("data/app/lesson_mode_app_ready_scope.csv", root)}
    variant = {row["municipality_id"]: row["readiness_status"] for row in rows("data/app/lesson_variant_groups.csv", root)}
    # A municipality may retain regional learner variants after its full 40-item
    # canonical promotion.  Full APP_READY is the stronger readiness snapshot and
    # must take precedence over the older LESSON_READY_10 variant-layer status.
    expected_readiness = variant | standard
    ids = [row.get("municipality_id", "") for row in priority]
    if len(ids) != 143 or set(ids) != set(municipalities) or len(ids) != len(set(ids)):
        errors.append("priority layer must cover 143 unique master municipalities")
    actual_priority = {row["municipality_id"] for row in priority if row.get("priority_status") == "PRIORITY"}
    if actual_priority != PRIORITY_A | PRIORITY_B:
        errors.append("priority set differs from the 36 individual plus 24 Chugoku targets")
    for row in priority:
        mid = row.get("municipality_id", "")
        master = municipalities.get(mid, {})
        if row.get("prefecture") != master.get("都道府県") or row.get("municipality_name") != master.get("市町村"):
            errors.append(f"{mid}: master identity mismatch")
        readiness = expected_readiness.get(mid, "NOT_LESSON_READY")
        expected_implementation = "IMPLEMENTED" if readiness in {"APP_READY", "LESSON_READY_10"} else "NOT_IMPLEMENTED"
        if row.get("readiness_status_snapshot") != readiness or row.get("implementation_status") != expected_implementation:
            errors.append(f"{mid}: implementation/readiness snapshot drift")
        if row.get("company_link_status") != "PENDING_COMPANY_LINK":
            errors.append(f"{mid}: company link was inferred without a repository evidence record")
        if mid in PRIORITY_A and row.get("priority_basis") != "USER_SPECIFIED_MASTER_36":
            errors.append(f"{mid}: individual priority basis mismatch")
        if mid in PRIORITY_B and mid not in PRIORITY_A and row.get("priority_basis") != "USER_CONFIRMED_CHUGOKU_CANDIDATE":
            errors.append(f"{mid}: Chugoku priority basis mismatch")
    for mid in {"M065", "M086"}:
        record = next((row for row in priority if row.get("municipality_id") == mid), {})
        if record.get("implementation_status") != "NOT_IMPLEMENTED" or record.get("readiness_status_snapshot") != "NOT_LESSON_READY":
            errors.append(f"{mid}: DEFERRED hold boundary changed")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("IMPLEMENTATION_PRIORITY_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    data = rows("data/master/07_implementation_priority.csv")
    print("IMPLEMENTATION_PRIORITY_VALIDATION_PASSED")
    print(f"municipalities={len(data)} priority={sum(r['priority_status'] == 'PRIORITY' for r in data)} implemented={sum(r['implementation_status'] == 'IMPLEMENTED' for r in data)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())