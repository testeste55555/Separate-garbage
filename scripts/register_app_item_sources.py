#!/usr/bin/env python3
"""Register canonical municipality URLs as persistent IS-* APP item sources.

Only URLs already present in canonical municipality records and registered in
the official-domain registry are eligible.  Existing category-research source
URLs are not duplicated.  QA is recomputed because new official evidence has a
new acquisition date.
"""
from __future__ import annotations

from urllib.parse import urlparse

from schema_v12 import (
    MASTER, QA_FIELDS, RESEARCH, SOURCE_FIELDS, compute_qa, read_csv,
    sync_municipality_qa_status, write_csv,
)

CHECKED = "2026-08-20"
ROLE_SPECS = [
    ("品目検索URL", "SEARCH", "自治体公式品目検索導線"),
    ("分別ガイドURL", "GUIDE", "自治体公式分別ガイド導線"),
    ("自治体ごみトップURL", "TOP", "自治体公式ごみトップ導線"),
]


def main() -> int:
    _, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, qa = read_csv(RESEARCH / "06_qa_log.csv")
    _, review_evidence = read_csv(RESEARCH / "08_category_review_evidence.csv")
    _, registry = read_csv(MASTER / "02_official_domain_registry.csv")

    registry_by = {(r["municipality_id"], r["host"].lower()): r for r in registry}
    existing_url = {(r["municipality_id"], r["公式URL"]): r for r in sources}
    existing_id = {(r["municipality_id"], r["source_id"]) for r in sources}
    added = []

    for m in municipalities:
        mid = m["municipality_id"]
        used_urls = set()
        for field, role, title in ROLE_SPECS:
            url = m.get(field, "")
            if not url or url in used_urls or (mid, url) in existing_url:
                continue
            used_urls.add(url)
            host = (urlparse(url).hostname or "").lower()
            authority = registry_by.get((mid, host))
            if not url.startswith("https://") or not authority:
                continue
            sid = f"IS-{mid}-{role}"
            if (mid, sid) in existing_id:
                continue
            basis = authority["authority_type"]
            row = {
                "municipality_id": mid,
                "source_id": sid,
                "資料名": f"{m['市町村']} {title}",
                "資料種別": "APP_ITEM_OFFICIAL_URL",
                "公式URL": url,
                "発行主体": authority.get("authority_name") or m["市町村"],
                "対象年度": m.get("対象年度", "現行"),
                "ページ更新日": "現行案内中",
                "取得確認日": CHECKED,
                "使用した情報": "APP readinessのITEM_SPECIFIC品目確認用公式導線。具体的品目証拠は本文match locatorで別途記録する。",
                "優先度": "APP_ITEM",
                "現行性": "現行",
                "備考": f"item-evidence supplement from canonical municipality field {field}",
                "official_verified": "TRUE",
                "official_basis": basis,
                "official_linking_url": authority.get("verification_url", "") if basis == "MUNICIPAL_LINKED_SERVICE" else "",
            }
            sources.append(row); added.append(row); existing_id.add((mid, sid)); existing_url[(mid, url)] = row

    sources.sort(key=lambda r: (r["municipality_id"], r["source_id"]))
    write_csv(RESEARCH / "03_sources_master.csv", SOURCE_FIELDS, sources)

    new_qa = compute_qa(municipalities, categories, sources, review_evidence, qa)
    sync_municipality_qa_status(municipalities, new_qa)
    # municipality fields are unchanged except the QA mirror status; write with existing header.
    muni_fields, _ = read_csv(RESEARCH / "04_municipalities_research.csv")
    write_csv(RESEARCH / "04_municipalities_research.csv", muni_fields, municipalities)
    write_csv(RESEARCH / "06_qa_log.csv", QA_FIELDS, new_qa)

    by_role = {}
    for r in added:
        role = r["source_id"].rsplit("-", 1)[-1]
        by_role[role] = by_role.get(role, 0) + 1
    print(f"APP_ITEM_SOURCES_REGISTERED added={len(added)} by_role={by_role} total_sources={len(sources)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
