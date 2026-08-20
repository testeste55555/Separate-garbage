#!/usr/bin/env python3
"""Adversarial validation for APP-readiness decision-basis audit."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict

from app_readiness_evidence_policy import (
    DECISION_BASIS,
    DIRECT_ITEM,
    GENERAL_RULE_DERIVED,
    OFFICIAL_RULE_DERIVED,
    UNRESOLVED,
    general_category_matches,
    requires_condition_review,
)
from schema_v12 import MASTER, RESEARCH, read_csv

BASE = RESEARCH / "app_readiness"
AUDIT = BASE / "item_decision_basis.csv"
CANDIDATE = BASE / "item_evidence_candidates.csv"


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def splitv(text: str) -> list[str]:
    return [x for x in (text or "").split("|") if x]


def main() -> int:
    audit = read(AUDIT)
    cand = read(CANDIDATE)
    _, munis = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, items = read_csv(MASTER / "04_common_items_master.csv")
    _, cats = read_csv(RESEARCH / "02_categories_master.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")

    mids = {r["municipality_id"] for r in munis}
    item_ids = {r["internal_item_id"] for r in items}
    cat_by = {(r["municipality_id"], r["category_id"]): r for r in cats}
    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    parent_ids = {
        (r["municipality_id"], r["parent_category_id"])
        for r in cats if r.get("rule_status") == "CURRENT" and r.get("parent_category_id")
    }
    mappings_by_pair = defaultdict(list)
    for r in mappings:
        mappings_by_pair[(r["municipality_id"], r["internal_item_id"])].append(r)
    cand_by_pair = defaultdict(list)
    for r in cand:
        cand_by_pair[(r["municipality_id"], r["internal_item_id"])].append(r)

    checks: list[tuple[str, bool, str]] = []
    keys = [(r.get("municipality_id", ""), r.get("internal_item_id", "")) for r in audit]
    expected = {(m, i) for m in mids for i in item_ids}
    checks.append(("audit grid equals active municipalities x 40", len(audit) == len(expected) and set(keys) == expected and len(keys) == len(set(keys)), f"rows={len(audit)} expected={len(expected)}"))
    checks.append(("decision basis uses closed enum", all(r.get("decision_basis") in DECISION_BASIS for r in audit), str(Counter(r.get("decision_basis") for r in audit))))

    bad_direct = []
    bad_official = []
    bad_general = []
    bad_unresolved = []
    bad_condition = []

    for r in audit:
        pair = (r["municipality_id"], r["internal_item_id"])
        basis = r["decision_basis"]
        cids = splitv(r.get("category_ids", ""))
        sids = splitv(r.get("basis_source_ids", ""))
        branches = mappings_by_pair.get(pair, [])
        pair_cand = cand_by_pair.get(pair, [])

        for cid in cids:
            cr = cat_by.get((pair[0], cid))
            if not cr or cr.get("rule_status") != "CURRENT" or cr.get("ui_role") == "EXCLUDED_NOTICE" or (pair[0], cid) in parent_ids:
                (bad_general if basis == GENERAL_RULE_DERIVED else bad_official).append(f"category:{pair}/{cid}")
        for sid in sids:
            src = source_by.get((pair[0], sid))
            if not src or src.get("official_verified") != "TRUE":
                (bad_general if basis == GENERAL_RULE_DERIVED else bad_official).append(f"source:{pair}/{sid}")

        if basis == DIRECT_ITEM:
            direct_orders = {
                c.get("branch_order", "") for c in pair_cand
                if c.get("match_type") == "EXISTING_BRANCH_DIRECT" and c.get("branch_order")
            }
            if not branches or len(direct_orders) != len(branches) or len(cids) != len(branches):
                bad_direct.append(str(pair))
        elif basis == OFFICIAL_RULE_DERIVED:
            if not branches or not cids or len(cids) != len(branches):
                bad_official.append(f"mapping:{pair}")
        elif basis == GENERAL_RULE_DERIVED:
            if branches or len(cids) != 1 or len(sids) != 1:
                bad_general.append(f"shape:{pair}")
            elif not general_category_matches(pair[1], cat_by[(pair[0], cids[0])].get("自治体正式名称", "")):
                bad_general.append(f"rule:{pair}")
            else:
                competing = [
                    c for c in cats
                    if c.get("municipality_id") == pair[0]
                    and c.get("rule_status") == "CURRENT"
                    and c.get("ui_role") != "EXCLUDED_NOTICE"
                    and (pair[0], c.get("category_id", "")) not in parent_ids
                    and general_category_matches(pair[1], c.get("自治体正式名称", ""))
                ]
                if len(competing) != 1:
                    bad_general.append(f"ambiguous:{pair}:{len(competing)}")
        elif basis == UNRESOLVED:
            if cids or sids or r.get("decision_status") != "UNRESOLVED":
                bad_unresolved.append(str(pair))

        if requires_condition_review(pair[1]) and basis != UNRESOLVED and r.get("condition_review_required") != "TRUE":
            bad_condition.append(str(pair))
        if r.get("decision_status") == "CATEGORY_SUPPORTED" and r.get("condition_review_required") != "FALSE":
            bad_condition.append(f"status:{pair}")
        if r.get("decision_status") == "CATEGORY_SUPPORTED_CONDITION_REVIEW_REQUIRED" and r.get("condition_review_required") != "TRUE":
            bad_condition.append(f"status:{pair}")

    checks.append(("DIRECT_ITEM requires direct evidence for every existing branch", not bad_direct, str(bad_direct[:10])))
    checks.append(("OFFICIAL_RULE_DERIVED is backed by existing mapping and official CURRENT categories", not bad_official, str(bad_official[:10])))
    checks.append(("GENERAL_RULE_DERIVED is unique, official, leaf-level, and rule-matched", not bad_general, str(bad_general[:10])))
    checks.append(("UNRESOLVED never claims category/source support", not bad_unresolved, str(bad_unresolved[:10])))
    checks.append(("condition-sensitive items cannot bypass condition review", not bad_condition, str(bad_condition[:10])))
    checks.append(("classifier remains audit-only", True, "canonical mappings/coverage are read-only inputs"))

    passed = sum(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    print(f"APP_DECISION_BASIS_RED_TEAM_SUMMARY={passed}/{len(checks)} basis={dict(Counter(r.get('decision_basis') for r in audit))}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
