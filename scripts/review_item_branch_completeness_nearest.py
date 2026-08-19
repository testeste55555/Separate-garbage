#!/usr/bin/env python3
"""Complete VERIFIED branch review only with strong nearest-category evidence."""
from __future__ import annotations

import csv
import re
from collections import defaultdict

from schema_v12 import COVERAGE_FIELDS, MAPPING_FIELDS, RESEARCH, ROOT, read_csv, write_csv

NEAREST = RESEARCH / "app_readiness" / "nearest_item_evidence_candidates.csv"
REPORT = ROOT / "docs" / "research" / "app_readiness_nearest_branch_review_report.md"
CHECKED = "2026-08-20"
REVIEWER = "AUTO_NEAREST_BRANCH_REVIEW_V1"
COMPREHENSIVE_RE = re.compile(r"50音|五十音|品目.{0,8}(?:一覧|検索|分別)|分別.{0,8}(?:辞典|一覧|早見|ガイド)|ごみ百科|ごみ.{0,5}辞典|分別早見|分け方.{0,5}出し方")


def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))


def strong_source(src: dict[str,str]) -> bool:
    if src.get("資料種別","").startswith("APP_ITEM_"): return True
    hay=" ".join([src.get("資料名",""),src.get("使用した情報",""),src.get("備考","")])
    return bool(COMPREHENSIVE_RE.search(hay))


def main() -> int:
    nearest=read(NEAREST)
    _,maps=read_csv(RESEARCH/"05_item_mapping_master.csv")
    _,cov=read_csv(RESEARCH/"07_item_mapping_coverage.csv")
    _,sources=read_csv(RESEARCH/"03_sources_master.csv")
    src={(r["municipality_id"],r["source_id"]):r for r in sources}
    n_by_pair=defaultdict(list)
    for r in nearest: n_by_pair[(r["municipality_id"],r["internal_item_id"])].append(r)
    m_by_pair=defaultdict(list)
    for r in maps: m_by_pair[(r["municipality_id"],r["internal_item_id"])].append(r)
    completed=0; reject_set=0; reject_branch=0; reject_source=0
    for c in cov:
        pair=(c["municipality_id"],c["internal_item_id"]); branches=m_by_pair.get(pair,[])
        if c.get("coverage_status")!="VERIFIED" or not branches: continue
        if any(b.get("mapping_status")!="VERIFIED" or b.get("evidence_scope")!="ITEM_SPECIFIC" for b in branches): continue
        ev=n_by_pair.get(pair,[])
        mapped_cats={b["category_id"] for b in branches}; ev_cats={e["category_id"] for e in ev}
        if not ev or ev_cats != mapped_cats:
            reject_set+=1; continue
        ok=True
        for b in branches:
            opts=[e for e in ev if e.get("category_id")==b.get("category_id") and e.get("branch_order")==b.get("branch_order")]
            if not opts:
                reject_branch+=1; ok=False; break
            strong=[e for e in opts if strong_source(src.get((e["municipality_id"],e["source_id"]),{}))]
            if not strong:
                reject_source+=1; ok=False; break
        if not ok: continue
        for b in branches:
            b["branch_review_status"]="COMPLETE"; b["reviewed_date"]=CHECKED; b["reviewed_by"]=REVIEWER
            b["備考"]=(b.get("備考","")+" 強い公式source上で品目とbranch categoryの一意な最近接関係を確認。").strip()
        c["branch_completeness_confirmed"]="TRUE"; c["reviewed_date"]=CHECKED; c["reviewed_by"]=REVIEWER
        c["notes"]="全VERIFIED branchを強い公式item sourceの最近接category evidenceで照合。"
        completed+=1
    maps.sort(key=lambda r:(r["municipality_id"],r["internal_item_id"],int(r.get("branch_order","0") or 0)))
    cov.sort(key=lambda r:(r["municipality_id"],r["internal_item_id"]))
    write_csv(RESEARCH/"05_item_mapping_master.csv",MAPPING_FIELDS,maps); write_csv(RESEARCH/"07_item_mapping_coverage.csv",COVERAGE_FIELDS,cov)
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text("# APP readiness nearest-evidence branch review\n\n"+f"reviewed: {CHECKED}\n\n- pairs newly marked branch-complete: {completed}\n- rejected category-set mismatch: {reject_set}\n- rejected missing exact branch evidence: {reject_branch}\n- rejected weak source: {reject_source}\n- APP_READY claims created: 0\n",encoding="utf-8")
    print(f"NEAREST_BRANCH_REVIEW complete={completed} set={reject_set} branch={reject_branch} source={reject_source} APP_READY=0")
    return 0

if __name__=="__main__": raise SystemExit(main())
