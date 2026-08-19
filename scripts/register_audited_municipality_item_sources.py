#!/usr/bin/env python3
"""Register only successfully fetched canonical municipality URLs with item candidates."""
from __future__ import annotations

import csv
from collections import Counter
from urllib.parse import urlparse

from schema_v12 import MASTER, QA_FIELDS, RESEARCH, SOURCE_FIELDS, compute_qa, read_csv, sync_municipality_qa_status, write_csv

BASE = RESEARCH / "app_readiness"
CANDIDATES = BASE / "municipality_url_candidates.csv"
FETCH = BASE / "municipality_url_fetch_status.csv"
CHECKED = "2026-08-20"


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    cand=read(CANDIDATES); fetch=read(FETCH)
    candidate_count=Counter((r["municipality_id"],r["official_url"]) for r in cand)
    ok={(r["municipality_id"],r["url"]):r for r in fetch if r.get("status")=="OK" and candidate_count[(r["municipality_id"],r["url"])]>0}
    _,sources=read_csv(RESEARCH/"03_sources_master.csv")
    muni_fields,munis=read_csv(RESEARCH/"04_municipalities_research.csv")
    _,cats=read_csv(RESEARCH/"02_categories_master.csv")
    _,qa=read_csv(RESEARCH/"06_qa_log.csv")
    _,review=read_csv(RESEARCH/"08_category_review_evidence.csv")
    _,registry=read_csv(MASTER/"02_official_domain_registry.csv")
    reg={(r["municipality_id"],r["host"].lower()):r for r in registry}
    existing_url={(r["municipality_id"],r["公式URL"]) for r in sources}
    existing_id={(r["municipality_id"],r["source_id"]) for r in sources}
    added=[]; rejected=[]
    for (mid,u),fr in sorted(ok.items()):
        if (mid,u) in existing_url: continue
        host=(urlparse(u).hostname or "").lower(); auth=reg.get((mid,host))
        if not auth or not u.startswith("https://"):
            rejected.append((mid,u,"registry")); continue
        role=fr.get("url_role") or "URL"
        sid=f"IS-{mid}-{role}"
        if (mid,sid) in existing_id:
            rejected.append((mid,u,"id collision")); continue
        basis=auth["authority_type"]
        row={
            "municipality_id":mid,"source_id":sid,"資料名":f"APP item evidence {role}",
            "資料種別":"APP_ITEM_AUDITED_MUNICIPALITY_URL","公式URL":u,
            "発行主体":auth.get("authority_name") or mid,"対象年度":"現行","ページ更新日":"現行案内中",
            "取得確認日":CHECKED,"使用した情報":f"APP readiness item evidence; audited_candidates={candidate_count[(mid,u)]}",
            "優先度":"APP_ITEM","現行性":"現行","備考":"canonical municipality URL; successful text extraction and item/category candidate",
            "official_verified":"TRUE","official_basis":basis,
            "official_linking_url":auth.get("verification_url","") if basis=="MUNICIPAL_LINKED_SERVICE" else "",
        }
        sources.append(row); added.append(row); existing_url.add((mid,u)); existing_id.add((mid,sid))
    sources.sort(key=lambda r:(r["municipality_id"],r["source_id"]))
    write_csv(RESEARCH/"03_sources_master.csv",SOURCE_FIELDS,sources)
    newqa=compute_qa(munis,cats,sources,review,qa); sync_municipality_qa_status(munis,newqa)
    write_csv(RESEARCH/"04_municipalities_research.csv",muni_fields,munis); write_csv(RESEARCH/"06_qa_log.csv",QA_FIELDS,newqa)
    print(f"AUDITED_MUNICIPALITY_ITEM_SOURCES added={len(added)} rejected={len(rejected)} total_sources={len(sources)}")
    return 0

if __name__=="__main__": raise SystemExit(main())
