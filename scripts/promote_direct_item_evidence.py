#!/usr/bin/env python3
"""Promote only direct official item+category evidence to VERIFIED.

Guardrails:
- never emits APP_READY;
- never changes an existing category assignment;
- only promotes an existing mapping branch when an audit candidate explicitly
  matches that exact branch/category;
- a coverage pair becomes VERIFIED only when every existing branch has direct
  ITEM_SPECIFIC evidence;
- branch completeness remains FALSE / INCOMPLETE for later review.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from schema_v12 import COVERAGE_FIELDS, MAPPING_FIELDS, RESEARCH, ROOT, read_csv, write_csv

BASE = RESEARCH / "app_readiness"
CANDIDATE_PATH = BASE / "item_evidence_candidates.csv"
PAIR_PATH = BASE / "item_evidence_pair_status.csv"
REPORT_PATH = ROOT / "docs" / "research" / "app_readiness_direct_evidence_promotion_report.md"
CHECKED = "2026-08-20"
REVIEWER = "AUTO_DIRECT_ITEM_EVIDENCE_V1"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def choose(candidates: list[dict[str, str]], category_source_id: str) -> dict[str, str]:
    """Prefer the category's own official source, then deterministic source/alias."""
    return sorted(
        candidates,
        key=lambda r: (
            0 if r.get("source_id") == category_source_id else 1,
            r.get("source_id", ""), r.get("alias", ""), len(r.get("snippet", "")),
        ),
    )[0]


def main() -> int:
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")
    candidates = read(CANDIDATE_PATH)
    pair_status = {(r["municipality_id"], r["internal_item_id"]): r for r in read(PAIR_PATH)}

    cand_by_branch: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for c in candidates:
        if c.get("match_type") == "EXISTING_BRANCH_DIRECT" and c.get("branch_order"):
            cand_by_branch[(c["municipality_id"], c["internal_item_id"], c["branch_order"])].append(c)

    mappings_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in mappings:
        mappings_by_pair[(r["municipality_id"], r["internal_item_id"])].append(r)

    promoted_branches = 0
    promoted_pairs = 0
    pair_evidence: dict[tuple[str, str], dict[str, str]] = {}

    for pair, branches in mappings_by_pair.items():
        status = pair_status.get(pair, {}).get("status")
        if status != "ALL_EXISTING_BRANCHES_HAVE_DIRECT_CANDIDATE":
            continue
        chosen_for_pair = []
        all_direct = True
        for branch in branches:
            key = (pair[0], pair[1], branch["branch_order"])
            options = [c for c in cand_by_branch.get(key, []) if c.get("category_id") == branch.get("category_id")]
            if not options:
                all_direct = False
                break
            chosen_for_pair.append((branch, choose(options, branch.get("category_source_id", ""))))
        if not all_direct or len(chosen_for_pair) != len(branches):
            continue
        for branch, c in chosen_for_pair:
            branch["自治体での品目表記"] = c["alias"]
            branch["item_evidence_source_id"] = c["source_id"]
            branch["item_evidence_url"] = c["official_url"]
            branch["item_evidence_locator"] = c["locator"]
            branch["確認日"] = CHECKED
            branch["mapping_status"] = "VERIFIED"
            branch["evidence_scope"] = "ITEM_SPECIFIC"
            branch["branch_review_status"] = "INCOMPLETE"
            branch["reviewed_date"] = CHECKED
            branch["reviewed_by"] = REVIEWER
            branch["備考"] = "公式本文で品目表記と既存category正式名称の近接共起を確認。category assignmentは変更せず、条件枝完全性は次工程でレビュー。"
            promoted_branches += 1
        pair_evidence[pair] = chosen_for_pair[0][1]
        promoted_pairs += 1

    for row in coverage:
        pair = (row["municipality_id"], row["internal_item_id"])
        c = pair_evidence.get(pair)
        if not c:
            continue
        branches = mappings_by_pair.get(pair, [])
        if not branches or any(b.get("mapping_status") != "VERIFIED" or b.get("evidence_scope") != "ITEM_SPECIFIC" for b in branches):
            continue
        row["coverage_status"] = "VERIFIED"
        row["mapping_branch_count"] = str(len(branches))
        row["branch_completeness_confirmed"] = "FALSE"
        row["evidence_scope"] = "ITEM_SPECIFIC"
        row["item_evidence_source_id"] = c["source_id"]
        row["item_evidence_url"] = c["official_url"]
        row["item_evidence_locator"] = c["locator"]
        row["reviewed_date"] = CHECKED
        row["reviewed_by"] = REVIEWER
        row["notes"] = "全既存branchに直接ITEM_SPECIFIC候補あり。条件枝完全性は未確定のためAPP_READYではない。"

    mappings.sort(key=lambda r: (r["municipality_id"], r["internal_item_id"], int(r.get("branch_order", "0") or 0)))
    coverage.sort(key=lambda r: (r["municipality_id"], r["internal_item_id"]))
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", COVERAGE_FIELDS, coverage)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("# APP readiness direct ITEM_SPECIFIC evidence promotion\n\n")
        f.write(f"reviewed: {CHECKED}\n\n")
        f.write(f"- promoted existing branches to VERIFIED: {promoted_branches}\n")
        f.write(f"- promoted municipality-item pairs to VERIFIED: {promoted_pairs}\n")
        f.write("- APP_READY claims created: 0\n")
        f.write("- category assignments changed: 0\n\n")
        f.write("All promoted branches retain branch_review_status=INCOMPLETE and all promoted coverage retains branch_completeness_confirmed=FALSE.\n")

    print(f"DIRECT_ITEM_EVIDENCE_PROMOTION branches={promoted_branches} pairs={promoted_pairs} APP_READY=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
