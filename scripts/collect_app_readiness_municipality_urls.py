#!/usr/bin/env python3
"""Audit already-registered municipality URLs not yet present in source master.

No canonical data is mutated.  Only HTTPS URLs already carried by canonical
municipality records and on the municipality's registered official host are
fetched.  Item/category local co-occurrence candidates are written for review.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import collect_app_readiness_evidence as base
from schema_v12 import MASTER, RESEARCH, ROOT, read_csv

OUT = RESEARCH / "app_readiness" / "municipality_url_candidates.csv"
FETCH = RESEARCH / "app_readiness" / "municipality_url_fetch_status.csv"
REPORT = ROOT / "docs" / "research" / "app_readiness_municipality_url_audit_report.md"
CHECKED = "2026-08-20"
FIELDS = ["municipality_id","internal_item_id","category_id","category_name","url_role","official_url","alias","locator","snippet","checked_date"]
FETCH_FIELDS = ["municipality_id","url_role","url","status","http_status","bytes","text_chars","error"]
URL_FIELDS = [("品目検索URL","ITEM_SEARCH"),("分別ガイドURL","GUIDE"),("自治体ごみトップURL","TOP")]


def write(path: Path, fields: list[str], rows: list[dict[str,str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)


def main() -> int:
    _, munis = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, registry = read_csv(MASTER / "02_official_domain_registry.csv")
    source_urls={(r["municipality_id"],r["公式URL"]) for r in sources}
    registered={(r["municipality_id"],r["host"].lower()) for r in registry}
    cats=defaultdict(list)
    for r in categories:
        if r.get("rule_status")=="CURRENT" and r.get("ui_role")!="EXCLUDED_NOTICE": cats[r["municipality_id"]].append(r)

    targets=[]; seen=set()
    for m in munis:
        mid=m["municipality_id"]
        for field,role in URL_FIELDS:
            url=m.get(field,"")
            host=(urlparse(url).hostname or "").lower()
            key=(mid,url)
            if not url.startswith("https://") or key in source_urls or key in seen or (mid,host) not in registered: continue
            seen.add(key); targets.append((mid,role,url))

    fetch_rows=[]; texts={}
    def one(t):
        mid,role,url=t
        pseudo={"municipality_id":mid,"source_id":role,"公式URL":url}
        st,text=base.fetch_source(pseudo)
        out={"municipality_id":mid,"url_role":role,"url":url,"status":st["status"],"http_status":st["http_status"],"bytes":st["bytes"],"text_chars":st["text_chars"],"error":st["error"]}
        return out,text
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures={pool.submit(one,t):t for t in targets}
        for fut in as_completed(futures):
            st,text=fut.result(); fetch_rows.append(st)
            if st["status"]=="OK": texts[(st["municipality_id"],st["url_role"],st["url"])]=text

    candidates=[]; dedupe=set()
    for (mid,role,url),text in texts.items():
        ctext=base.compact(text)
        for iid,aliases in base.ALIASES.items():
            occ=base.find_occurrences(text,aliases)
            for pos,alias in occ[:40]:
                snip=base.snippet_from_compact(ctext,pos)
                for cat in cats[mid]:
                    cname=base.compact(cat["自治体正式名称"])
                    if not cname or cname not in snip: continue
                    k=(mid,iid,cat["category_id"],url,alias,pos)
                    if k in dedupe: continue
                    dedupe.add(k)
                    candidates.append({"municipality_id":mid,"internal_item_id":iid,"category_id":cat["category_id"],"category_name":cat["自治体正式名称"],"url_role":role,"official_url":url,"alias":alias,"locator":f"text-match:{alias} + {cat['自治体正式名称']}","snippet":snip[:820],"checked_date":CHECKED})
    candidates.sort(key=lambda r:(r["municipality_id"],r["internal_item_id"],r["category_id"],r["url_role"]))
    fetch_rows.sort(key=lambda r:(r["municipality_id"],r["url_role"],r["url"]))
    write(OUT,FIELDS,candidates); write(FETCH,FETCH_FIELDS,fetch_rows)
    fc=Counter(r["status"] for r in fetch_rows)
    pairs={(r["municipality_id"],r["internal_item_id"]) for r in candidates}
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text("# APP readiness municipality URL audit\n\n"+f"checked: {CHECKED}\n\n- official municipality URLs attempted: {len(targets)}\n- fetch OK: {fc.get('OK',0)}\n- fetch ERROR: {fc.get('ERROR',0)}\n- candidate rows: {len(candidates)}\n- municipality-item pairs with candidate: {len(pairs)}\n\nNo canonical source/mapping/coverage row is changed by this audit.\n",encoding="utf-8")
    print(f"MUNICIPALITY_URL_AUDIT urls={len(targets)} fetch={dict(fc)} candidates={len(candidates)} pairs={len(pairs)}")
    return 0

if __name__=="__main__": raise SystemExit(main())
