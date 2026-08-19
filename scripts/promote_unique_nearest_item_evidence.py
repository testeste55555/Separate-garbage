#!/usr/bin/env python3
"""Create VERIFIED mappings for unmapped pairs with one strong nearest category.

Conservative requirements:
- no existing mapping branches;
- all retained nearest evidence for the pair points to exactly one CURRENT leaf;
- at least one retained evidence row comes from a strong APP/comprehensive item source;
- never creates APP_READY and never marks branch completeness TRUE.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict

from schema_v12 import COVERAGE_FIELDS, MAPPING_FIELDS, RESEARCH, ROOT, read_csv, write_csv

NEAREST=RESEARCH/"app_readiness"/"nearest_item_evidence_candidates.csv"
REPORT=ROOT/"docs"/"research"/"app_readiness_unique_nearest_promotion_report.md"
CHECKED="2026-08-20"; REVIEWER="AUTO_UNIQUE_NEAREST_ITEM_MAPPING_V1"; NS="NOT_STATED_IN_CITED_SOURCE"
COMPREHENSIVE_RE=re.compile(r"50音|五十音|品目.{0,8}(?:一覧|検索|分別)|分別.{0,8}(?:辞典|一覧|早見|ガイド)|ごみ百科|ごみ.{0,5}辞典|分別早見|分け方.{0,5}出し方")


def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def strong(src):
    if src.get("資料種別","").startswith("APP_ITEM_"):return True
    return bool(COMPREHENSIVE_RE.search(" ".join([src.get("資料名",""),src.get("使用した情報",""),src.get("備考","")])))

def main()->int:
    ev=read(NEAREST)
    _,maps=read_csv(RESEARCH/"05_item_mapping_master.csv"); _,cov=read_csv(RESEARCH/"07_item_mapping_coverage.csv")
    _,cats=read_csv(RESEARCH/"02_categories_master.csv"); _,sources=read_csv(RESEARCH/"03_sources_master.csv")
    cat={(r["municipality_id"],r["category_id"]):r for r in cats}; src={(r["municipality_id"],r["source_id"]):r for r in sources}
    parent_ids={(r["municipality_id"],r["parent_category_id"]) for r in cats if r.get("rule_status")=="CURRENT" and r.get("parent_category_id")}
    existing={(r["municipality_id"],r["internal_item_id"]) for r in maps}; ids={r["mapping_id"] for r in maps}
    covby={(r["municipality_id"],r["internal_item_id"]):r for r in cov}; by=defaultdict(list)
    for e in ev:by[(e["municipality_id"],e["internal_item_id"])].append(e)
    added=0; reject_multi=reject_weak=reject_leaf=0
    for pair,rows in sorted(by.items()):
        if pair in existing:continue
        cids={r["category_id"] for r in rows}
        if len(cids)!=1: reject_multi+=1; continue
        cid=next(iter(cids)); cr=cat.get((pair[0],cid))
        if not cr or cr.get("rule_status")!="CURRENT" or cr.get("ui_role")=="EXCLUDED_NOTICE" or (pair[0],cid) in parent_ids:
            reject_leaf+=1; continue
        strong_rows=[r for r in rows if strong(src.get((r["municipality_id"],r["source_id"]),{}))]
        if not strong_rows: reject_weak+=1; continue
        e=sorted(strong_rows,key=lambda r:(int(r.get("gap_chars","999999") or 999999),r["source_id"]))[0]
        mid,iid=pair; mapping_id=f"MAP-{mid}-{iid}-01"
        if mapping_id in ids:continue
        maps.append({
            "mapping_id":mapping_id,"municipality_id":mid,"internal_item_id":iid,"branch_order":"1",
            "自治体での品目表記":e["alias"],"category_id":cid,"分別区分正式名称":cr["自治体正式名称"],
            "条件":cr.get("適用条件") or NS,"前処理":cr.get("出す前の処理") or NS,"例外分別先":cr.get("条件外の扱い") or NS,
            "自治体収集外":cr.get("自治体収集外か") or "FALSE","rule_status":cr.get("rule_status","CURRENT"),
            "effective_from":cr.get("effective_from","") ,"effective_to":cr.get("effective_to",""),
            "category_source_id":cr["source_id"],"category_source_url":cr["出典URL"],"category_source_locator":cr["出典ページ・該当箇所"],
            "item_evidence_source_id":e["source_id"],"item_evidence_url":e["official_url"],"item_evidence_locator":e["locator"],
            "確認日":CHECKED,"mapping_status":"VERIFIED","evidence_scope":"ITEM_SPECIFIC","branch_review_status":"INCOMPLETE",
            "reviewed_date":CHECKED,"reviewed_by":REVIEWER,"備考":"強い公式item sourceで全最近接evidenceが唯一のCURRENT公式葉を指すため1branch追加。条件枝完全性は未確認。",
        }); ids.add(mapping_id); existing.add(pair); added+=1
        c=covby.get(pair)
        if c:
            c["coverage_status"]="VERIFIED"; c["mapping_branch_count"]="1"; c["branch_completeness_confirmed"]="FALSE"; c["evidence_scope"]="ITEM_SPECIFIC"
            c["item_evidence_source_id"]=e["source_id"]; c["item_evidence_url"]=e["official_url"]; c["item_evidence_locator"]=e["locator"]
            c["reviewed_date"]=CHECKED;c["reviewed_by"]=REVIEWER;c["notes"]="強い公式item sourceの唯一最近接categoryからVERIFIED mapping追加。完全性未確認。"
    maps.sort(key=lambda r:(r["municipality_id"],r["internal_item_id"],int(r.get("branch_order","0") or 0)));cov.sort(key=lambda r:(r["municipality_id"],r["internal_item_id"]))
    write_csv(RESEARCH/"05_item_mapping_master.csv",MAPPING_FIELDS,maps);write_csv(RESEARCH/"07_item_mapping_coverage.csv",COVERAGE_FIELDS,cov)
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text("# APP readiness unique nearest mapping promotion\n\n"+f"reviewed: {CHECKED}\n\n- new VERIFIED mappings: {added}\n- rejected multiple nearest categories: {reject_multi}\n- rejected weak source: {reject_weak}\n- rejected non-leaf/invalid category: {reject_leaf}\n- APP_READY claims created: 0\n",encoding="utf-8")
    print(f"UNIQUE_NEAREST_PROMOTION added={added} multi={reject_multi} weak={reject_weak} leaf={reject_leaf} APP_READY=0");return 0

if __name__=="__main__":raise SystemExit(main())
