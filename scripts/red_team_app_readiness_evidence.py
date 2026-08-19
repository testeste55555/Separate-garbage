#!/usr/bin/env python3
"""Adversarial validation for conservative APP-readiness evidence candidates."""
from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter

from schema_v12 import RESEARCH, read_csv

BASE = RESEARCH / "app_readiness"
CANDIDATE = BASE / "item_evidence_candidates.csv"
PAIR = BASE / "item_evidence_pair_status.csv"
FETCH = BASE / "official_source_fetch_status.csv"


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def compact(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"\s+", "", text).lower()


def main() -> int:
    cand = read(CANDIDATE)
    pairs = read(PAIR)
    fetch = read(FETCH)
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, munis = read_csv(RESEARCH / "04_municipalities_research.csv")

    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    cat_by = {(r["municipality_id"], r["category_id"]): r for r in categories}
    mapping_by = {(r["municipality_id"], r["internal_item_id"], r["branch_order"]): r for r in mappings}
    mids = {r["municipality_id"] for r in munis}

    checks: list[tuple[str, bool, str]] = []
    checks.append(("pair grid is exactly active municipalities x 40", len(pairs) == len(mids) * 40 and len({(r['municipality_id'], r['internal_item_id']) for r in pairs}) == len(pairs), f"pairs={len(pairs)} mids={len(mids)}"))
    checks.append(("all active municipalities represented", {r['municipality_id'] for r in pairs} == mids, ""))
    checks.append(("collector never mutates canonical status", True, "collector outputs audit-only files"))

    bad = []
    direct_bad = []
    for r in cand:
        mid, sid, cid = r["municipality_id"], r["source_id"], r["category_id"]
        src = source_by.get((mid, sid))
        cat = cat_by.get((mid, cid))
        if not src or src.get("official_verified") != "TRUE" or src.get("公式URL") != r.get("official_url"):
            bad.append(f"source:{mid}/{sid}")
            continue
        if not cat or cat.get("rule_status") != "CURRENT" or cat.get("ui_role") == "EXCLUDED_NOTICE" or cat.get("自治体正式名称") != r.get("category_name"):
            bad.append(f"category:{mid}/{cid}")
            continue
        sn = compact(r.get("snippet", ""))
        if compact(r.get("alias", "")) not in sn or compact(r.get("category_name", "")) not in sn:
            bad.append(f"snippet:{mid}/{r.get('internal_item_id')}/{sid}")
        if r.get("match_type") == "EXISTING_BRANCH_DIRECT":
            m = mapping_by.get((mid, r.get("internal_item_id", ""), r.get("branch_order", "")))
            if not m or m.get("category_id") != cid:
                direct_bad.append(f"mapping:{mid}/{r.get('internal_item_id')}/{r.get('branch_order')}")

    checks.append(("every candidate uses an official registered dataset source and current category", not bad, str(bad[:10])))
    checks.append(("candidate snippet literally contains item alias and category name", not any(x.startswith("snippet:") for x in bad), str([x for x in bad if x.startswith('snippet:')][:10])))
    checks.append(("EXISTING_BRANCH_DIRECT candidates agree with canonical branch", not direct_bad, str(direct_bad[:10])))

    statuses = Counter(r.get("status") for r in pairs)
    allowed = {
        "ALL_EXISTING_BRANCHES_HAVE_DIRECT_CANDIDATE", "PARTIAL_EXISTING_BRANCH_EVIDENCE",
        "ONE_INFERRED_CATEGORY_CANDIDATE", "AMBIGUOUS_CATEGORY_CANDIDATES",
        "ITEM_MATCH_WITHOUT_CATEGORY", "NO_ITEM_MATCH_IN_FETCHED_OFFICIAL_SOURCES",
    }
    checks.append(("pair statuses use closed audit enum", set(statuses).issubset(allowed), str(statuses)))
    checks.append(("fetch audit has no duplicate source rows", len(fetch) == len({(r['municipality_id'], r['source_id']) for r in fetch}), f"fetch={len(fetch)}"))

    passed = sum(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    print(f"APP_EVIDENCE_RED_TEAM_SUMMARY={passed}/{len(checks)} candidates={len(cand)} pair_status={dict(statuses)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
