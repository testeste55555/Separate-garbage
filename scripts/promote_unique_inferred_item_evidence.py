#!/usr/bin/env python3
"""Create VERIFIED mappings only for unmapped pairs with one unique official category candidate.

This is intentionally not APP_READY.  The category must be a CURRENT official
leaf and the evidence collector must have found exactly one category co-occurring
locally with the item alias in an official source.  Branch completeness remains
unconfirmed for later review.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from schema_v12 import COVERAGE_FIELDS, MAPPING_FIELDS, RESEARCH, ROOT, read_csv, write_csv

BASE = RESEARCH / "app_readiness"
CANDIDATE_PATH = BASE / "item_evidence_candidates.csv"
PAIR_PATH = BASE / "item_evidence_pair_status.csv"
REPORT_PATH = ROOT / "docs" / "research" / "app_readiness_unique_mapping_promotion_report.md"
CHECKED = "2026-08-20"
REVIEWER = "AUTO_UNIQUE_ITEM_CATEGORY_TEXT_MATCH_V1"
NS = "NOT_STATED_IN_CITED_SOURCE"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    candidates = read(CANDIDATE_PATH)
    pairs = read(PAIR_PATH)

    category_by = {(r["municipality_id"], r["category_id"]): r for r in categories}
    parent_ids = {(r["municipality_id"], r["parent_category_id"]) for r in categories if r.get("parent_category_id") and r.get("rule_status") == "CURRENT"}
    existing_pairs = {(r["municipality_id"], r["internal_item_id"]) for r in mappings}
    mapping_ids = {r["mapping_id"] for r in mappings}
    coverage_by = {(r["municipality_id"], r["internal_item_id"]): r for r in coverage}

    cand_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for c in candidates:
        cand_by_pair[(c["municipality_id"], c["internal_item_id"])].append(c)

    added = 0
    skipped_nonleaf = 0
    skipped_bad = 0
    for p in pairs:
        pair = (p["municipality_id"], p["internal_item_id"])
        if p.get("status") != "ONE_INFERRED_CATEGORY_CANDIDATE" or pair in existing_pairs:
            continue
        options = cand_by_pair.get(pair, [])
        category_ids = {c["category_id"] for c in options}
        if len(category_ids) != 1:
            skipped_bad += 1
            continue
        cid = next(iter(category_ids))
        cat = category_by.get((pair[0], cid))
        if not cat or cat.get("rule_status") != "CURRENT" or cat.get("ui_role") == "EXCLUDED_NOTICE":
            skipped_bad += 1
            continue
        if (pair[0], cid) in parent_ids:
            skipped_nonleaf += 1
            continue
        valid = [c for c in options if c.get("category_id") == cid and c.get("source_id") and c.get("official_url") and c.get("locator")]
        if not valid:
            skipped_bad += 1
            continue
        c = sorted(valid, key=lambda r: (0 if r.get("source_id") == cat.get("source_id") else 1, r.get("source_id"), r.get("alias")))[0]
        mapping_id = f"MAP-{pair[0]}-{pair[1]}-01"
        if mapping_id in mapping_ids:
            skipped_bad += 1
            continue
        row = {
            "mapping_id": mapping_id,
            "municipality_id": pair[0],
            "internal_item_id": pair[1],
            "branch_order": "1",
            "自治体での品目表記": c["alias"],
            "category_id": cid,
            "分別区分正式名称": cat["自治体正式名称"],
            "条件": cat.get("適用条件") or NS,
            "前処理": cat.get("出す前の処理") or NS,
            "例外分別先": cat.get("条件外の扱い") or NS,
            "自治体収集外": cat.get("自治体収集外か") or "FALSE",
            "rule_status": cat.get("rule_status", "CURRENT"),
            "effective_from": cat.get("effective_from", ""),
            "effective_to": cat.get("effective_to", ""),
            "category_source_id": cat["source_id"],
            "category_source_url": cat["出典URL"],
            "category_source_locator": cat["出典ページ・該当箇所"],
            "item_evidence_source_id": c["source_id"],
            "item_evidence_url": c["official_url"],
            "item_evidence_locator": c["locator"],
            "確認日": CHECKED,
            "mapping_status": "VERIFIED",
            "evidence_scope": "ITEM_SPECIFIC",
            "branch_review_status": "INCOMPLETE",
            "reviewed_date": CHECKED,
            "reviewed_by": REVIEWER,
            "備考": "公式本文で品目表記と唯一のCURRENT公式葉が近接共起。新規1branchとしてVERIFIED化したが条件枝完全性は未確認。",
        }
        mappings.append(row)
        mapping_ids.add(mapping_id)
        existing_pairs.add(pair)
        cov = coverage_by.get(pair)
        if cov:
            cov["coverage_status"] = "VERIFIED"
            cov["mapping_branch_count"] = "1"
            cov["branch_completeness_confirmed"] = "FALSE"
            cov["evidence_scope"] = "ITEM_SPECIFIC"
            cov["item_evidence_source_id"] = c["source_id"]
            cov["item_evidence_url"] = c["official_url"]
            cov["item_evidence_locator"] = c["locator"]
            cov["reviewed_date"] = CHECKED
            cov["reviewed_by"] = REVIEWER
            cov["notes"] = "唯一categoryのITEM_SPECIFIC直接候補から1branchを追加。条件枝完全性は未確認。"
        added += 1

    mappings.sort(key=lambda r: (r["municipality_id"], r["internal_item_id"], int(r.get("branch_order", "0") or 0)))
    coverage.sort(key=lambda r: (r["municipality_id"], r["internal_item_id"]))
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", COVERAGE_FIELDS, coverage)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("# APP readiness unique item/category mapping promotion\n\n")
        f.write(f"reviewed: {CHECKED}\n\n")
        f.write(f"- new VERIFIED mappings: {added}\n")
        f.write(f"- skipped because candidate category was a projection parent: {skipped_nonleaf}\n")
        f.write(f"- skipped for structural ambiguity: {skipped_bad}\n")
        f.write("- APP_READY claims created: 0\n\n")
        f.write("All new mappings remain branch_review_status=INCOMPLETE pending explicit completeness review.\n")
    print(f"UNIQUE_ITEM_MAPPING_PROMOTION added={added} skipped_nonleaf={skipped_nonleaf} skipped_bad={skipped_bad} APP_READY=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
