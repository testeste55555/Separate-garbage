#!/usr/bin/env python3
"""Review VERIFIED item branches for destination completeness using official evidence candidates.

A pair is marked branch-complete only when:
1) every branch is already VERIFIED with ITEM_SPECIFIC evidence;
2) the set of locally co-occurring official category candidates equals exactly
   the set of mapped categories (no missing/extra destination candidate);
3) every mapped branch has at least one strong evidence candidate from either a
   comprehensive item-index/guide source or a source explicitly about the item.

This script does not itself create APP_READY claims.  It sets COMPLETE/TRUE on
eligible VERIFIED pairs so municipality-level promotion can be atomic later.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from schema_v12 import COVERAGE_FIELDS, MAPPING_FIELDS, RESEARCH, ROOT, read_csv, write_csv

BASE = RESEARCH / "app_readiness"
CANDIDATE_PATH = BASE / "item_evidence_candidates.csv"
PAIR_PATH = BASE / "item_evidence_pair_status.csv"
FETCH_PATH = BASE / "official_source_fetch_status.csv"
REPORT_PATH = ROOT / "docs" / "research" / "app_readiness_branch_review_report.md"
CHECKED = "2026-08-20"
REVIEWER = "AUTO_BRANCH_DESTINATION_REVIEW_V1"

COMPREHENSIVE_RE = re.compile(r"50音|五十音|品目.{0,8}(?:一覧|検索|分別)|分別.{0,8}(?:辞典|一覧|早見|ガイド)|ごみ百科|ごみ.{0,5}辞典|分別早見|分け方.{0,5}出し方")


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text or "")).lower()


def source_is_strong(source: dict[str, str], candidate: dict[str, str]) -> bool:
    hay = " ".join([source.get("資料名", ""), source.get("使用した情報", ""), source.get("備考", "")])
    if COMPREHENSIVE_RE.search(hay):
        return True
    a = norm(candidate.get("alias", ""))
    return bool(a and a in norm(hay))


def main() -> int:
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    candidates = read(CANDIDATE_PATH)
    fetch = read(FETCH_PATH)

    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    fetch_ok = {(r["municipality_id"], r["source_id"]): r.get("status") == "OK" for r in fetch}
    cand_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    cand_by_branch: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for c in candidates:
        pair = (c["municipality_id"], c["internal_item_id"])
        cand_by_pair[pair].append(c)
        if c.get("branch_order"):
            cand_by_branch[(pair[0], pair[1], c["branch_order"])].append(c)

    mappings_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in mappings:
        mappings_by_pair[(r["municipality_id"], r["internal_item_id"])].append(r)
    coverage_by = {(r["municipality_id"], r["internal_item_id"]): r for r in coverage}

    completed_pairs = 0
    rejected_set_mismatch = 0
    rejected_weak_source = 0
    rejected_not_verified = 0

    for pair, cov in coverage_by.items():
        branches = mappings_by_pair.get(pair, [])
        if cov.get("coverage_status") != "VERIFIED" or not branches or any(
            b.get("mapping_status") != "VERIFIED" or b.get("evidence_scope") != "ITEM_SPECIFIC" for b in branches
        ):
            continue
        mapped_cats = {b["category_id"] for b in branches}
        pair_candidates = cand_by_pair.get(pair, [])
        candidate_cats = {c["category_id"] for c in pair_candidates}
        if candidate_cats != mapped_cats:
            rejected_set_mismatch += 1
            continue
        strong_all = True
        for b in branches:
            options = [c for c in pair_candidates if c.get("category_id") == b.get("category_id")]
            if not any(
                fetch_ok.get((c["municipality_id"], c["source_id"]), False)
                and source_is_strong(source_by.get((c["municipality_id"], c["source_id"]), {}), c)
                for c in options
            ):
                strong_all = False
                break
        if not strong_all:
            rejected_weak_source += 1
            continue
        for b in branches:
            b["branch_review_status"] = "COMPLETE"
            b["reviewed_date"] = CHECKED
            b["reviewed_by"] = REVIEWER
            b["備考"] = (b.get("備考", "") + " 条件枝の分別先集合を公式ITEM_SPECIFIC候補集合と照合し一致。強い公式item sourceを確認。").strip()
        cov["branch_completeness_confirmed"] = "TRUE"
        cov["reviewed_date"] = CHECKED
        cov["reviewed_by"] = REVIEWER
        cov["notes"] = "VERIFIED全branchの分別先集合が公式item候補集合と一致し、各branchに強い公式item sourceあり。"
        completed_pairs += 1

    mappings.sort(key=lambda r: (r["municipality_id"], r["internal_item_id"], int(r.get("branch_order", "0") or 0)))
    coverage.sort(key=lambda r: (r["municipality_id"], r["internal_item_id"]))
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", COVERAGE_FIELDS, coverage)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("# APP readiness branch completeness review\n\n")
        f.write(f"reviewed: {CHECKED}\n\n")
        f.write(f"- VERIFIED pairs marked branch-complete: {completed_pairs}\n")
        f.write(f"- rejected: candidate category set mismatch: {rejected_set_mismatch}\n")
        f.write(f"- rejected: no strong official item source for every branch: {rejected_weak_source}\n")
        f.write("- APP_READY claims created: 0\n")
    print(f"BRANCH_COMPLETENESS_REVIEW complete={completed_pairs} set_mismatch={rejected_set_mismatch} weak={rejected_weak_source} APP_READY=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
