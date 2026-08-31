from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "data/research/07_item_mapping_coverage.csv"
TARGETS = ["M009", "M020", "M098", "M099", "M105"]
REQUIRED_ITEMS = {f"I{number:03d}" for number in range(1, 41)}


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    rows_by_municipality = defaultdict(list)
    for row in read_rows(COVERAGE):
        municipality_id = row.get("municipality_id", "").strip()
        if municipality_id in TARGETS:
            rows_by_municipality[municipality_id].append(row)

    print("CLASSROOM_PILOT_APP_READY_PREFLIGHT")
    blocking = False
    for municipality_id in TARGETS:
        rows = rows_by_municipality[municipality_id]
        item_ids = {row.get("internal_item_id", "").strip() for row in rows}
        missing_items = sorted(REQUIRED_ITEMS - item_ids)
        statuses = Counter(row.get("coverage_status", "").strip() for row in rows)
        complete = sum(row.get("branch_completeness_confirmed", "").strip().upper() == "TRUE" for row in rows)
        app_ready = sum(row.get("coverage_status", "").strip() == "APP_READY" for row in rows)
        print(
            f"{municipality_id}: rows={len(rows)} items={len(item_ids)} "
            f"branch_complete={complete}/40 APP_READY={app_ready}/40 statuses={dict(statuses)}"
        )
        if missing_items:
            print(f"  missing coverage rows: {','.join(missing_items)}")
        not_ready = [
            row.get("internal_item_id", "").strip()
            for row in rows
            if row.get("coverage_status", "").strip() != "APP_READY" or
               row.get("branch_completeness_confirmed", "").strip().upper() != "TRUE"
        ]
        if not_ready:
            print(f"  requires review: {','.join(not_ready)}")
        if missing_items or len(item_ids) != 40 or app_ready != 40 or complete != 40:
            blocking = True

    if blocking:
        print("PREFLIGHT_RESULT: APP_READY_WORK_REQUIRED")
    else:
        print("PREFLIGHT_RESULT: ALL_TARGETS_APP_READY")


if __name__ == "__main__":
    main()
