#!/usr/bin/env python3
"""RED TEAM staged APP-readiness mapping/coverage promotions.

This checker permits VERIFIED staging but rejects unsupported evidence claims,
category reassignment, and any partial municipality-level APP_READY claim.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from schema_v12 import MASTER, RESEARCH, read_csv
from validation_v12 import validate_dataset

BASE = RESEARCH / "app_readiness"
CANDIDATE_PATH = BASE / "item_evidence_candidates.csv"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    paths = {
        "municipality_path": RESEARCH / "04_municipalities_research.csv",
        "category_path": RESEARCH / "02_categories_master.csv",
        "source_path": RESEARCH / "03_sources_master.csv",
        "qa_path": RESEARCH / "06_qa_log.csv",
        "mapping_path": RESEARCH / "05_item_mapping_master.csv",
        "coverage_path": RESEARCH / "07_item_mapping_coverage.csv",
        "review_evidence_path": RESEARCH / "08_category_review_evidence.csv",
    }
    errors, _, _ = validate_dataset(label="APP_READINESS_STAGING", **paths)
    _, mappings = read_csv(paths["mapping_path"])
    _, coverage = read_csv(paths["coverage_path"])
    _, categories = read_csv(paths["category_path"])
    _, sources = read_csv(paths["source_path"])
    _, municipalities = read_csv(paths["municipality_path"])
    candidates = read(CANDIDATE_PATH) if CANDIDATE_PATH.exists() else []

    cat_by = {(r["municipality_id"], r["category_id"]): r for r in categories}
    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    candidate_keys = {
        (c["municipality_id"], c["internal_item_id"], c.get("branch_order", ""), c["category_id"], c["source_id"], c["official_url"])
        for c in candidates
    }
    cov_by = {(r["municipality_id"], r["internal_item_id"]): r for r in coverage}
    maps_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in mappings:
        maps_by_pair[(r["municipality_id"], r["internal_item_id"])].append(r)

    checks: list[tuple[str, bool, str]] = []
    checks.append(("canonical structural validation passes", not errors, str(errors[:10])))

    unsupported = []
    reassigned = []
    for m in mappings:
        if m.get("mapping_status") not in {"VERIFIED", "APP_READY"}:
            continue
        mid, iid, order = m["municipality_id"], m["internal_item_id"], m["branch_order"]
        cat = cat_by.get((mid, m.get("category_id", "")))
        src = source_by.get((mid, m.get("item_evidence_source_id", "")))
        if not cat or m.get("分別区分正式名称") != cat.get("自治体正式名称"):
            reassigned.append(m["mapping_id"])
        key = (mid, iid, order, m.get("category_id", ""), m.get("item_evidence_source_id", ""), m.get("item_evidence_url", ""))
        inferred_key = (mid, iid, "", m.get("category_id", ""), m.get("item_evidence_source_id", ""), m.get("item_evidence_url", ""))
        if key not in candidate_keys and inferred_key not in candidate_keys:
            # Allow future manually reviewed evidence only when reviewer is not an AUTO_* reviewer.
            if m.get("reviewed_by", "").startswith("AUTO_"):
                unsupported.append(m["mapping_id"])
        if not src or src.get("official_verified") != "TRUE":
            unsupported.append(m["mapping_id"] + ":source")
    checks.append(("staged mappings never change canonical category identity", not reassigned, str(reassigned[:10])))
    checks.append(("automatic VERIFIED evidence is traceable to collected official candidate", not unsupported, str(unsupported[:10])))

    partial_app = []
    for muni in municipalities:
        mid = muni["municipality_id"]
        rows = [cov_by[(mid, f"I{i:03d}")] for i in range(1, 41)]
        any_app = any(r.get("coverage_status") == "APP_READY" for r in rows) or any(
            m.get("municipality_id") == mid and m.get("mapping_status") == "APP_READY" for m in mappings
        )
        if any_app and not all(r.get("coverage_status") in {"APP_READY", "VERIFIED_NOT_APPLICABLE"} for r in rows):
            partial_app.append(mid)
    checks.append(("no partial municipality-level APP_READY claims", not partial_app, str(partial_app)))

    verified_pairs = sum(r.get("coverage_status") == "VERIFIED" for r in coverage)
    complete_verified_pairs = sum(
        r.get("coverage_status") == "VERIFIED" and r.get("branch_completeness_confirmed") == "TRUE" for r in coverage
    )
    app_pairs = sum(r.get("coverage_status") == "APP_READY" for r in coverage)
    not_app = sum(r.get("coverage_status") == "VERIFIED_NOT_APPLICABLE" for r in coverage)
    checks.append(("coverage grid remains exactly 132x40", len(coverage) == 5280 and len(cov_by) == 5280, f"coverage={len(coverage)} unique={len(cov_by)}"))

    passed = sum(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    print(
        f"APP_PROMOTION_RED_TEAM_SUMMARY={passed}/{len(checks)} "
        f"verified_pairs={verified_pairs} complete_verified_pairs={complete_verified_pairs} "
        f"app_ready_pairs={app_pairs} verified_not_applicable={not_app}"
    )
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
