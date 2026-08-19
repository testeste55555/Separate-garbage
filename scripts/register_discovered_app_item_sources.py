#!/usr/bin/env python3
"""Persist recommended discovered official item sources as IS-* supplements.

Requires discovery audit rows with recommended=TRUE. Every URL host must still
exist in the official-domain registry for the same municipality. No category or
mapping assignment is changed. QA dates are recomputed after adding sources.
"""
from __future__ import annotations

import csv
from urllib.parse import urlparse

from schema_v12 import MASTER, QA_FIELDS, RESEARCH, SOURCE_FIELDS, compute_qa, read_csv, sync_municipality_qa_status, write_csv

DISCOVERY = RESEARCH / "app_readiness" / "discovered_item_sources.csv"
CHECKED = "2026-08-20"


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    discovered = read(DISCOVERY)
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    muni_fields, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, qa = read_csv(RESEARCH / "06_qa_log.csv")
    _, review_evidence = read_csv(RESEARCH / "08_category_review_evidence.csv")
    _, registry = read_csv(MASTER / "02_official_domain_registry.csv")
    reg={(r["municipality_id"],r["host"].lower()):r for r in registry}
    existing_urls={(r["municipality_id"],r["公式URL"]) for r in sources}
    existing_ids={(r["municipality_id"],r["source_id"]) for r in sources}
    added=[]; rejected=[]
    for d in discovered:
        if d.get("recommended") != "TRUE" or d.get("fetch_status") != "OK": continue
        mid,u=d["municipality_id"],d["official_url"]
        if (mid,u) in existing_urls: continue
        host=(urlparse(u).hostname or "").lower(); authority=reg.get((mid,host))
        if not u.startswith("https://") or not authority:
            rejected.append((mid,u,"unregistered host")); continue
        sid="IS-" + d["candidate_id"].removeprefix("DISC-")
        if (mid,sid) in existing_ids:
            rejected.append((mid,u,"source id collision")); continue
        basis=authority["authority_type"]
        row={
            "municipality_id":mid,"source_id":sid,
            "資料名":d.get("anchor_text") or f"APP item evidence {sid}",
            "資料種別":"APP_ITEM_DISCOVERED_OFFICIAL_SOURCE","公式URL":u,
            "発行主体":authority.get("authority_name") or mid,"対象年度":"現行",
            "ページ更新日":"現行案内中","取得確認日":CHECKED,
            "使用した情報":f"APP readiness item evidence candidate; common_item_hits={d.get('item_hit_count')}; category_hits={d.get('category_hit_count')}",
            "優先度":"APP_ITEM","現行性":"現行",
            "備考":f"discovered from {d.get('source_page')}; candidate={d.get('candidate_id')}",
            "official_verified":"TRUE","official_basis":basis,
            "official_linking_url":authority.get("verification_url","") if basis=="MUNICIPAL_LINKED_SERVICE" else "",
        }
        sources.append(row); added.append(row); existing_urls.add((mid,u)); existing_ids.add((mid,sid))
    sources.sort(key=lambda r:(r["municipality_id"],r["source_id"]))
    write_csv(RESEARCH/"03_sources_master.csv",SOURCE_FIELDS,sources)
    new_qa=compute_qa(municipalities,categories,sources,review_evidence,qa)
    sync_municipality_qa_status(municipalities,new_qa)
    write_csv(RESEARCH/"04_municipalities_research.csv",muni_fields,municipalities)
    write_csv(RESEARCH/"06_qa_log.csv",QA_FIELDS,new_qa)
    print(f"DISCOVERED_APP_ITEM_SOURCES_REGISTERED added={len(added)} rejected={len(rejected)} total_sources={len(sources)}")
    if rejected: print("REJECTED_SAMPLE="+repr(rejected[:10]))
    return 0

if __name__=="__main__": raise SystemExit(main())
