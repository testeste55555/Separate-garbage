#!/usr/bin/env python3
"""Derive stricter nearest-category evidence from broad item/category candidates.

For each concrete item occurrence, keep a category only when it is the unique
nearest CURRENT category name in the persisted audit snippet, close enough to
the item alias, and sufficiently separated from the second-nearest category.
This is audit-only and never changes canonical mappings/coverage.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from schema_v12 import RESEARCH, ROOT

BASE = RESEARCH / "app_readiness"
INPUT = BASE / "item_evidence_candidates.csv"
OUT = BASE / "nearest_item_evidence_candidates.csv"
REPORT = ROOT / "docs" / "research" / "app_readiness_nearest_evidence_report.md"
CHECKED = "2026-08-20"
MAX_GAP = 120
MIN_MARGIN = 25
FIELDS = [
    "municipality_id","internal_item_id","branch_order","category_id","category_name","source_id","official_url",
    "alias","locator","snippet","gap_chars","second_gap_chars","margin_chars","checked_date",
]


def read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def compact(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text or "")).lower()


def positions(text: str, token: str) -> list[int]:
    out=[]; start=0
    while token:
        p=text.find(token,start)
        if p<0: break
        out.append(p); start=p+max(1,len(token))
    return out


def main() -> int:
    rows=read(INPUT)
    # Same concrete occurrence emits one row per category in its local window.
    groups=defaultdict(list)
    for r in rows:
        key=(r["municipality_id"],r["internal_item_id"],r["source_id"],r["official_url"],r["alias"],r["snippet"])
        groups[key].append(r)
    selected=[]; reasons=Counter()
    for key, group in groups.items():
        sn=compact(group[0]["snippet"]); alias=compact(group[0]["alias"])
        apos=positions(sn,alias)
        if not apos:
            reasons["alias_missing"]+=1; continue
        center=len(sn)//2
        ap=min(apos,key=lambda p:abs(p-center))
        scored=[]
        for r in group:
            cname=compact(r["category_name"]); cps=positions(sn,cname)
            if not cps: continue
            cp=min(cps,key=lambda p:abs(p-ap)); gap=abs(cp-ap)
            scored.append((gap,r,cp))
        if not scored:
            reasons["category_missing"]+=1; continue
        scored.sort(key=lambda x:(x[0],x[1]["category_id"]))
        best_gap,best,_=scored[0]
        second_gap=scored[1][0] if len(scored)>1 else 999999
        # Multiple categories at the same closest distance remain ambiguous.
        if len(scored)>1 and second_gap==best_gap:
            reasons["tie"]+=1; continue
        margin=second_gap-best_gap
        if best_gap>MAX_GAP:
            reasons["too_far"]+=1; continue
        if len(scored)>1 and margin<MIN_MARGIN:
            reasons["small_margin"]+=1; continue
        out={k:best.get(k,"") for k in ["municipality_id","internal_item_id","branch_order","category_id","category_name","source_id","official_url","alias","snippet"]}
        out["locator"]=f"nearest-text:{best['alias']} -> {best['category_name']}; gap={best_gap}; margin={margin if second_gap<999999 else 'single'}"
        out["gap_chars"]=str(best_gap); out["second_gap_chars"]="" if second_gap>=999999 else str(second_gap)
        out["margin_chars"]="" if second_gap>=999999 else str(margin); out["checked_date"]=CHECKED
        selected.append(out); reasons["selected"]+=1
    # Deduplicate exact evidence identity.
    dedupe={
        (r["municipality_id"],r["internal_item_id"],r["branch_order"],r["category_id"],r["source_id"],r["locator"]):r
        for r in selected
    }
    selected=sorted(dedupe.values(),key=lambda r:(r["municipality_id"],r["internal_item_id"],r["category_id"],int(r["gap_chars"])))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n"); w.writeheader(); w.writerows(selected)
    pairs={(r["municipality_id"],r["internal_item_id"]) for r in selected}
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    with REPORT.open("w",encoding="utf-8") as f:
        f.write("# APP readiness nearest-category evidence report\n\n")
        f.write(f"checked: {CHECKED}\n\n- broad candidate rows: {len(rows)}\n- occurrence groups: {len(groups)}\n- nearest evidence rows: {len(selected)}\n- municipality-item pairs represented: {len(pairs)}\n")
        for k,v in reasons.most_common(): f.write(f"- {k}: {v}\n")
        f.write("\nAudit only; no canonical status changes.\n")
    print(f"NEAREST_ITEM_EVIDENCE broad={len(rows)} groups={len(groups)} selected={len(selected)} pairs={len(pairs)} reasons={dict(reasons)}")
    return 0

if __name__=="__main__": raise SystemExit(main())
