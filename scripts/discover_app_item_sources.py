#!/usr/bin/env python3
"""Discover high-value official item-index sources from canonical official pages.

Audit only.  Starts from already-canonical municipality/source URLs, follows one
link level, and accepts candidate links only on hosts registered for the same
municipality.  Candidate resources are scored by actual extracted common-item
aliases and CURRENT category names.  No canonical source/mapping/coverage row is
changed here.
"""
from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

import collect_app_readiness_evidence as base
from schema_v12 import MASTER, RESEARCH, ROOT, read_csv

OUT = RESEARCH / "app_readiness" / "discovered_item_sources.csv"
REPORT = ROOT / "docs" / "research" / "app_readiness_item_source_discovery_report.md"
CHECKED = "2026-08-20"
MAX_LINKS_PER_MUNI = 12
FIELDS = [
    "municipality_id","candidate_id","source_page","anchor_text","official_url","host","authority_type",
    "fetch_status","http_status","text_chars","item_hit_count","category_hit_count","matched_items",
    "recommended","reason","checked_date",
]

LINK_RE = re.compile(
    r"50音|五十音|品目|分別.{0,8}(?:一覧|検索|辞典|早見|表)|ごみ.{0,8}(?:検索|辞典|百科|早見)|"
    r"ごみ分別|ゴミ分別|分け方.{0,8}出し方|家庭ごみ.{0,8}(?:ガイド|一覧)|ごみナビ|分別ガイド",
    re.I,
)
PDF_RE = re.compile(r"\.pdf(?:$|[?#])", re.I)


def clean_url(base_url: str, href: str) -> str:
    try:
        url = urljoin(base_url, href.strip())
        url, _ = urldefrag(url)
        return url
    except Exception:
        return ""


def fetch_html(url: str) -> tuple[str, int, str]:
    try:
        r = requests.get(url, timeout=(6, 18), headers={"User-Agent":"Separate-garbage-official-source-discovery/1.0"})
        code = r.status_code
        r.raise_for_status()
        ctype = (r.headers.get("content-type") or "").lower()
        if "html" not in ctype and not (r.text[:200].lower().find("<html") >= 0):
            return "", code, "NOT_HTML"
        return r.text, code, "OK"
    except Exception as exc:
        return "", 0, f"ERROR:{type(exc).__name__}"


def main() -> int:
    _, munis = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, registry = read_csv(MASTER / "02_official_domain_registry.csv")

    registered: dict[str, dict[str, dict[str,str]]] = defaultdict(dict)
    for r in registry:
        registered[r["municipality_id"]][r["host"].lower()] = r
    existing_urls = {(r["municipality_id"], r["公式URL"]) for r in sources}
    cats = defaultdict(list)
    for r in categories:
        if r.get("rule_status") == "CURRENT" and r.get("ui_role") != "EXCLUDED_NOTICE":
            cats[r["municipality_id"]].append(r)

    seeds: dict[str, set[str]] = defaultdict(set)
    for m in munis:
        mid = m["municipality_id"]
        for field in ["品目検索URL","分別ガイドURL","自治体ごみトップURL"]:
            u = m.get(field, "")
            if u: seeds[mid].add(u)
    for s in sources:
        mid, u = s["municipality_id"], s["公式URL"]
        if u and not PDF_RE.search(u): seeds[mid].add(u)

    # Fetch seed HTML and discover relevant links.
    discovered: dict[str, dict[str, tuple[str,str]]] = defaultdict(dict)  # mid -> url -> (source_page, anchor)
    seed_tasks = [(mid,u) for mid, urls in seeds.items() for u in urls]
    with ThreadPoolExecutor(max_workers=12) as pool:
        futs = {pool.submit(fetch_html,u):(mid,u) for mid,u in seed_tasks}
        for fut in as_completed(futs):
            mid, source_page = futs[fut]
            html, _, status = fut.result()
            if status != "OK": continue
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                anchor = " ".join(a.stripped_strings)[:300]
                href = a.get("href", "")
                u = clean_url(source_page, href)
                if not u.startswith("http"): continue
                host = (urlparse(u).hostname or "").lower()
                if host not in registered.get(mid, {}): continue
                hay = f"{anchor} {u}"
                if not LINK_RE.search(hay):
                    # PDF is accepted only when its anchor/href clearly concerns waste/sorting.
                    if not (PDF_RE.search(u) and re.search(r"ごみ|ゴミ|分別|資源|廃棄", hay, re.I)):
                        continue
                if (mid,u) in existing_urls: continue
                prev = discovered[mid].get(u)
                if not prev or len(anchor) > len(prev[1]):
                    discovered[mid][u] = (source_page, anchor)

    # Rank before fetching to cap load per municipality.
    tasks = []
    for mid, by_url in discovered.items():
        ranked = []
        for u,(page,anchor) in by_url.items():
            score = 0
            hay = f"{anchor} {u}"
            if re.search(r"50音|五十音|品目", hay): score += 6
            if re.search(r"検索|辞典|百科|早見|一覧", hay): score += 4
            if PDF_RE.search(u): score += 2
            if re.search(r"分別", hay): score += 2
            ranked.append((-score,u,page,anchor))
        ranked.sort()
        for _,u,page,anchor in ranked[:MAX_LINKS_PER_MUNI]:
            tasks.append((mid,u,page,anchor))

    rows=[]
    def fetch_candidate(task):
        mid,u,page,anchor=task
        pseudo={"municipality_id":mid,"source_id":"DISCOVERY","公式URL":u}
        st,text=base.fetch_source(pseudo)
        return task,st,text

    with ThreadPoolExecutor(max_workers=12) as pool:
        futs={pool.submit(fetch_candidate,t):t for t in tasks}
        for fut in as_completed(futs):
            (mid,u,page,anchor),st,text=fut.result()
            ctext=base.compact(text) if text else ""
            matched=[]
            for iid, aliases in base.ALIASES.items():
                if any(base.compact(a) and base.compact(a) in ctext for a in aliases): matched.append(iid)
            cat_hits=sum(1 for c in cats[mid] if base.compact(c["自治体正式名称"]) in ctext)
            item_hits=len(matched)
            recommended = st["status"]=="OK" and ((item_hits>=5 and cat_hits>=1) or (item_hits>=10))
            reason = (
                "high-value official item/index text" if recommended else
                "official candidate but insufficient extracted item/category coverage"
            )
            authority=registered[mid].get((urlparse(u).hostname or "").lower(),{})
            cid=hashlib.sha1(u.encode("utf-8")).hexdigest()[:10].upper()
            rows.append({
                "municipality_id":mid,"candidate_id":f"DISC-{mid}-{cid}","source_page":page,"anchor_text":anchor,
                "official_url":u,"host":(urlparse(u).hostname or "").lower(),"authority_type":authority.get("authority_type",""),
                "fetch_status":st["status"],"http_status":st["http_status"],"text_chars":st["text_chars"],
                "item_hit_count":str(item_hits),"category_hit_count":str(cat_hits),"matched_items":"|".join(matched),
                "recommended":"TRUE" if recommended else "FALSE","reason":reason,"checked_date":CHECKED,
            })

    rows.sort(key=lambda r:(r["municipality_id"], r["recommended"]!="TRUE", -int(r["item_hit_count"]), r["official_url"]))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n"); w.writeheader(); w.writerows(rows)
    counts=Counter(r["fetch_status"] for r in rows)
    rec=[r for r in rows if r["recommended"]=="TRUE"]
    rec_mids={r["municipality_id"] for r in rec}
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    with REPORT.open("w",encoding="utf-8") as f:
        f.write("# APP readiness official item-source discovery report\n\n")
        f.write(f"checked: {CHECKED}\n\n")
        f.write(f"- seed pages considered: {len(seed_tasks)}\n")
        f.write(f"- discovered relevant official links after cap: {len(tasks)}\n")
        f.write(f"- fetched OK: {counts.get('OK',0)}\n")
        f.write(f"- fetch ERROR: {counts.get('ERROR',0)}\n")
        f.write(f"- recommended high-value official item sources: {len(rec)}\n")
        f.write(f"- municipalities with recommended source: {len(rec_mids)}\n\n")
        f.write("No canonical source/mapping/coverage status is changed by discovery.\n")
    print(f"APP_ITEM_SOURCE_DISCOVERY seeds={len(seed_tasks)} links={len(tasks)} fetch={dict(counts)} recommended={len(rec)} municipalities={len(rec_mids)}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
