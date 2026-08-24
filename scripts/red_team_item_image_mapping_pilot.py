#!/usr/bin/env python3
"""Mutation RED TEAM for the image-item official mapping pilot."""

from __future__ import annotations

import copy
import sys

from schema_v12 import latest_qa_evidence_date, read_csv
from validate_item_image_mapping_pilot import PILOT_PATH, ROOT, validate_pilot_rows


def mutated(base, mutate):
    candidate = copy.deepcopy(base)
    mutate(candidate)
    return bool(validate_pilot_rows(candidate))


def row(rows, mid, iid):
    return next(r for r in rows if r["municipality_id"] == mid and r["internal_item_id"] == iid)


def main() -> int:
    _, base = read_csv(PILOT_PATH)
    checks = [
        ("missing grid pair rejected", mutated(base, lambda rows: rows.pop())),
        ("canonical item-name tamper rejected", mutated(base, lambda rows: row(rows, "M094", "I001").update({"canonical_name": "PET容器"}))),
        ("district-variant municipality injection rejected", mutated(base, lambda rows: row(rows, "M094", "I001").update({"municipality_id": "M099"}))),
        ("unofficial evidence URL rejected", mutated(base, lambda rows: row(rows, "M095", "I006").update({"item_evidence_url": "https://example.com/bottle"}))),
        ("missing evidence locator rejected", mutated(base, lambda rows: row(rows, "M105", "I029").update({"item_evidence_locator": ""}))),
        ("generic placeholder rule rejected", mutated(base, lambda rows: row(rows, "M095", "I013").update({"preparation": "種類別にまとめ、必要に応じて洗浄・乾燥"}))),
        ("unresolved item cannot claim guessed category", mutated(base, lambda rows: row(rows, "M107", "I031").update({"review_status": "VERIFIED", "category_id": "C-M107-08"}))),
        ("canonical evidence mismatch rejected", mutated(base, lambda rows: row(rows, "M104", "I029").update({"item_evidence_source_id": "IS-M104-04"}))),
    ]

    # Regression for the layer boundary found while implementing this Pilot:
    # an APP item source date may be newer but must not rewrite category QA.
    municipality = {"municipality_id": "MTEST", "最終確認日": "2026-08-19", "category_count_reviewed_date": "2026-08-19"}
    categories = [{"municipality_id": "MTEST", "確認日": "2026-08-19"}]
    sources = [
        {"municipality_id": "MTEST", "source_id": "S-MTEST-01", "取得確認日": "2026-08-19"},
        {"municipality_id": "MTEST", "source_id": "IS-MTEST-01", "取得確認日": "2026-08-24"},
    ]
    checks.append(("APP item-source date is isolated from category QA date", latest_qa_evidence_date(municipality, categories, sources) == "2026-08-19"))

    passed = sum(ok for _, ok in checks)
    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    if passed != len(checks):
        print(f"ITEM_IMAGE_MAPPING_PILOT_RED_TEAM_FAILED {passed}/{len(checks)}")
        return 1
    print(f"ITEM_IMAGE_MAPPING_PILOT_RED_TEAM_PASSED {passed}/{len(checks)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
