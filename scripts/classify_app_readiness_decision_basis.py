#!/usr/bin/env python3
"""Classify all municipality x common-item pairs by decision basis.

This is an audit-only classifier.  It does not mutate canonical mappings or
coverage.  It implements the policy that literal item wording is preferred but
not mandatory: official category rules may determine an item, and ordinary
items may use a stable general classification when no municipality-specific
contrary rule is found.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from app_readiness_evidence_policy import (
    DECISION_BASIS,
    DIRECT_ITEM,
    GENERAL_RULE_DERIVED,
    OFFICIAL_RULE_DERIVED,
    UNRESOLVED,
    general_category_matches,
    has_exception_signal,
    requires_condition_review,
)
from schema_v12 import MASTER, RESEARCH, ROOT, read_csv

BASE = RESEARCH / "app_readiness"
CANDIDATE_PATH = BASE / "item_evidence_candidates.csv"
PAIR_PATH = BASE / "item_evidence_pair_status.csv"
OUT_PATH = BASE / "item_decision_basis.csv"
REPORT_PATH = ROOT / "docs" / "research" / "app_readiness_decision_basis_report.md"
CHECKED = "2026-08-20"

FIELDS = [
    "municipality_id", "internal_item_id", "decision_basis", "category_ids", "category_names",
    "basis_source_ids", "basis_locators", "condition_review_required", "decision_status", "notes",
]


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows([{k: r.get(k, "") for k in FIELDS} for r in rows])


def current_leaf_categories(categories: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    parent_ids = {
        (r["municipality_id"], r["parent_category_id"])
        for r in categories
        if r.get("rule_status") == "CURRENT" and r.get("parent_category_id")
    }
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in categories:
        key = (r["municipality_id"], r["category_id"])
        if r.get("rule_status") != "CURRENT" or r.get("ui_role") == "EXCLUDED_NOTICE" or key in parent_ids:
            continue
        out[r["municipality_id"]].append(r)
    return out


def main() -> int:
    _, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, items = read_csv(MASTER / "04_common_items_master.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    candidates = read(CANDIDATE_PATH)
    pair_audit = {(r["municipality_id"], r["internal_item_id"]): r for r in read(PAIR_PATH)}

    mids = sorted(r["municipality_id"] for r in municipalities)
    item_ids = [r["internal_item_id"] for r in items]
    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    cat_by = {(r["municipality_id"], r["category_id"]): r for r in categories}
    leaf_by_mid = current_leaf_categories(categories)

    mappings_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in mappings:
        mappings_by_pair[(r["municipality_id"], r["internal_item_id"])].append(r)

    candidates_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in candidates:
        candidates_by_pair[(r["municipality_id"], r["internal_item_id"])].append(r)

    rows: list[dict[str, str]] = []
    counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()

    for mid in mids:
        for item_id in item_ids:
            pair = (mid, item_id)
            branches = sorted(mappings_by_pair.get(pair, []), key=lambda r: int(r.get("branch_order", "0") or 0))
            cand = candidates_by_pair.get(pair, [])
            audit = pair_audit.get(pair, {})
            direct_branch_orders = {
                r.get("branch_order", "") for r in cand
                if r.get("match_type") == "EXISTING_BRANCH_DIRECT" and r.get("branch_order")
            }

            basis = UNRESOLVED
            cats: list[dict[str, str]] = []
            source_ids: list[str] = []
            locators: list[str] = []
            notes = ""

            if branches and len(direct_branch_orders) == len(branches):
                basis = DIRECT_ITEM
                cats = [cat_by[(mid, b["category_id"])] for b in branches if (mid, b.get("category_id", "")) in cat_by]
                chosen = []
                for b in branches:
                    options = [
                        c for c in cand
                        if c.get("match_type") == "EXISTING_BRANCH_DIRECT"
                        and c.get("branch_order") == b.get("branch_order")
                        and c.get("category_id") == b.get("category_id")
                    ]
                    if options:
                        chosen.append(sorted(options, key=lambda c: (c.get("source_id", ""), c.get("alias", "")))[0])
                source_ids = [c.get("source_id", "") for c in chosen]
                locators = [c.get("locator", "") for c in chosen]
                notes = "全既存branchで公式資料中の品目表記とcategoryの直接候補あり。"
            elif branches:
                valid = True
                cats = []
                for b in branches:
                    cr = cat_by.get((mid, b.get("category_id", "")))
                    src = source_by.get((mid, b.get("category_source_id", "")))
                    if (
                        cr is None or cr.get("rule_status") != "CURRENT"
                        or cr.get("ui_role") == "EXCLUDED_NOTICE"
                        or src is None or src.get("official_verified") != "TRUE"
                    ):
                        valid = False
                        break
                    cats.append(cr)
                    source_ids.append(b.get("category_source_id", ""))
                    locators.append(b.get("category_source_locator", ""))
                if valid and cats:
                    basis = OFFICIAL_RULE_DERIVED
                    notes = "品目の直接記載は必須とせず、既存mappingを支えるCURRENT公式category ruleから判定。"
            else:
                general = [c for c in leaf_by_mid.get(mid, []) if general_category_matches(item_id, c.get("自治体正式名称", ""))]
                if len(general) == 1:
                    cr = general[0]
                    src = source_by.get((mid, cr.get("source_id", "")))
                    if src and src.get("official_verified") == "TRUE":
                        basis = GENERAL_RULE_DERIVED
                        cats = [cr]
                        source_ids = [cr.get("source_id", "")]
                        locators = [cr.get("出典ページ・該当箇所", "")]
                        notes = "個別記載・既存mappingなし。一般的な材質/用途ルールと一意のCURRENT公式categoryが一致。"
                elif len(general) > 1:
                    notes = f"一般則候補categoryが複数({len(general)})のため自動決定しない。"
                else:
                    notes = "直接記載・公式rule由来mapping・一意な一般則categoryのいずれでも決定できない。"

            condition_required = requires_condition_review(item_id)
            exception_text = " ".join(
                " ".join([
                    c.get("適用条件", ""), c.get("条件外の扱い", ""), c.get("出す前の処理", ""),
                    c.get("袋・容器のルール", ""), c.get("サイズ・条件", ""), c.get("注意事項", ""),
                ]) for c in cats
            )
            if has_exception_signal(exception_text):
                condition_required = True

            if basis == UNRESOLVED:
                decision_status = "UNRESOLVED"
            elif condition_required:
                decision_status = "CATEGORY_SUPPORTED_CONDITION_REVIEW_REQUIRED"
            else:
                decision_status = "CATEGORY_SUPPORTED"

            category_ids = [c.get("category_id", "") for c in cats]
            category_names = [c.get("自治体正式名称", "") for c in cats]
            source_ids = list(dict.fromkeys(x for x in source_ids if x))
            locators = list(dict.fromkeys(x for x in locators if x))
            notes = (notes + (f" collector_status={audit.get('status')}" if audit else "")).strip()

            row = {
                "municipality_id": mid,
                "internal_item_id": item_id,
                "decision_basis": basis,
                "category_ids": "|".join(category_ids),
                "category_names": "|".join(category_names),
                "basis_source_ids": "|".join(source_ids),
                "basis_locators": "|".join(locators),
                "condition_review_required": "TRUE" if condition_required else "FALSE",
                "decision_status": decision_status,
                "notes": notes,
            }
            rows.append(row)
            counts[basis] += 1
            status_counts[decision_status] += 1

    write(OUT_PATH, rows)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("# APP readiness decision-basis audit\n\n")
        f.write(f"checked: {CHECKED}\n\n")
        f.write("Literal item wording is preferred but is not required when an official rule or an unambiguous general rule determines the category. This report is audit-only and creates no APP_READY claim.\n\n")
        f.write(f"- pairs: {len(rows)}\n")
        for key in [DIRECT_ITEM, OFFICIAL_RULE_DERIVED, GENERAL_RULE_DERIVED, UNRESOLVED]:
            f.write(f"- {key}: {counts[key]}\n")
        f.write("\n## Decision status\n\n")
        for key, value in sorted(status_counts.items()):
            f.write(f"- {key}: {value}\n")
        f.write("\n## Policy guardrail\n\n")
        f.write("GENERAL_RULE_DERIVED only resolves a destination when one allowed general category concept matches exactly one CURRENT official leaf. Hazard/size/route-sensitive items still require explicit condition review before APP_READY.\n")

    print(f"APP_DECISION_BASIS rows={len(rows)} basis={dict(counts)} status={dict(status_counts)}")
    assert set(counts).issubset(DECISION_BASIS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
