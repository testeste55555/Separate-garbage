#!/usr/bin/env python3
"""Atomically promote fully reviewed municipalities to APP_READY.

A municipality is eligible only when all 40 coverage pairs are already either:
- VERIFIED with branch_completeness_confirmed=TRUE and every branch VERIFIED + COMPLETE; or
- VERIFIED_NOT_APPLICABLE with complete official item evidence.

No partial municipality promotion is possible.
"""
from __future__ import annotations

from collections import defaultdict

from schema_v12 import COVERAGE_FIELDS, MAPPING_FIELDS, MASTER, RESEARCH, ROOT, read_csv, write_csv

CHECKED = "2026-08-20"
REVIEWER = "ATOMIC_APP_READY_PROMOTION_V1"
REPORT = ROOT / "docs" / "research" / "app_readiness_atomic_promotion_report.md"


def main() -> int:
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")
    _, items = read_csv(MASTER / "04_common_items_master.csv")
    _, munis = read_csv(RESEARCH / "04_municipalities_research.csv")
    item_ids = [r["internal_item_id"] for r in items]

    cov_by = {(r["municipality_id"], r["internal_item_id"]): r for r in coverage}
    maps_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in mappings:
        maps_by_pair[(r["municipality_id"], r["internal_item_id"])].append(r)

    eligible: list[str] = []
    blockers: dict[str, list[str]] = {}
    for muni in munis:
        mid = muni["municipality_id"]
        problems = []
        for iid in item_ids:
            cov = cov_by.get((mid, iid))
            if not cov:
                problems.append(f"{iid}:missing coverage")
                continue
            status = cov.get("coverage_status")
            if status == "VERIFIED_NOT_APPLICABLE":
                if cov.get("branch_completeness_confirmed") != "TRUE" or cov.get("evidence_scope") != "ITEM_SPECIFIC":
                    problems.append(f"{iid}:bad not-applicable proof")
                continue
            if status != "VERIFIED" or cov.get("branch_completeness_confirmed") != "TRUE" or cov.get("evidence_scope") != "ITEM_SPECIFIC":
                problems.append(f"{iid}:{status}/complete={cov.get('branch_completeness_confirmed')}")
                continue
            branches = maps_by_pair.get((mid, iid), [])
            if not branches:
                problems.append(f"{iid}:verified without branch")
                continue
            if any(
                b.get("mapping_status") != "VERIFIED"
                or b.get("evidence_scope") != "ITEM_SPECIFIC"
                or b.get("branch_review_status") != "COMPLETE"
                or not b.get("item_evidence_source_id")
                or not b.get("item_evidence_url")
                or not b.get("item_evidence_locator")
                for b in branches
            ):
                problems.append(f"{iid}:branch not fully verified")
        if problems:
            blockers[mid] = problems
        else:
            eligible.append(mid)

    eligible_set = set(eligible)
    for m in mappings:
        if m["municipality_id"] in eligible_set:
            m["mapping_status"] = "APP_READY"
            m["branch_review_status"] = "COMPLETE"
            m["reviewed_date"] = CHECKED
            m["reviewed_by"] = REVIEWER
            m["備考"] = (m.get("備考", "") + " 自治体40品目の全pair完了後にatomic APP_READY昇格。").strip()
    for c in coverage:
        if c["municipality_id"] not in eligible_set:
            continue
        if c.get("coverage_status") == "VERIFIED":
            c["coverage_status"] = "APP_READY"
            c["branch_completeness_confirmed"] = "TRUE"
            c["reviewed_date"] = CHECKED
            c["reviewed_by"] = REVIEWER
            c["notes"] = (c.get("notes", "") + " 自治体40品目をatomic APP_READY昇格。").strip()

    mappings.sort(key=lambda r: (r["municipality_id"], r["internal_item_id"], int(r.get("branch_order", "0") or 0)))
    coverage.sort(key=lambda r: (r["municipality_id"], r["internal_item_id"]))
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", COVERAGE_FIELDS, coverage)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", encoding="utf-8") as f:
        f.write("# Atomic APP_READY promotion report\n\n")
        f.write(f"reviewed: {CHECKED}\n\n")
        f.write(f"- eligible/promoted municipalities: {len(eligible)}\n")
        f.write(f"- blocked municipalities: {len(blockers)}\n")
        if eligible:
            f.write("- promoted: " + ", ".join(eligible) + "\n")
        f.write("\n## Blockers by municipality\n\n")
        for mid in sorted(blockers):
            f.write(f"- {mid}: {len(blockers[mid])} unresolved items\n")
    print(f"ATOMIC_APP_READY_PROMOTION promoted={len(eligible)} blocked={len(blockers)} mids={','.join(eligible)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
