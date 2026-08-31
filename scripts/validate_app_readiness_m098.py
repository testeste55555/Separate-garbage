#!/usr/bin/env python3
"""Strict validator for M098 Onomichi 40-item APP_READY."""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import apply_app_readiness_m098 as build
from schema_v12 import read_csv

ROOT = Path(__file__).resolve().parents[1]
MID = build.MID
EXPECTED_ITEMS = {f"I{i:03d}" for i in range(1, 41)}
FIXED10 = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}
EXPECTED_COMPANIES = {"C001", "C004", "C007"}
EXPECTED_CATEGORIES = {row["category_id"] for row in build.CATEGORIES}
EXPECTED_SOURCES = {row["source_id"] for row in build.SOURCES}
EXPECTED_BRANCHES = sum(len(rows) for rows in build.RULES.values())


def rr(root: Path, path: str):
    return read_csv(root / path)[1]


def load(root: Path = ROOT):
    return {
        "audit": rr(root, "data/research/app_readiness/m098_item_review.csv"),
        "mappings": rr(root, "data/research/05_item_mapping_master.csv"),
        "coverage": rr(root, "data/research/07_item_mapping_coverage.csv"),
        "categories": rr(root, "data/research/02_categories_master.csv"),
        "sources": rr(root, "data/research/03_sources_master.csv"),
        "municipalities": rr(root, "data/research/04_municipalities_research.csv"),
        "qa": rr(root, "data/research/06_qa_log.csv"),
        "scope": rr(root, "data/app/lesson_mode_app_ready_scope.csv"),
        "groups": rr(root, "data/app/lesson_variant_groups.csv"),
        "districts": rr(root, "data/app/district_scopes.csv"),
        "variant_scoring": rr(root, "data/app/lesson_variant_item_scoring.csv"),
        "company": rr(root, "data/app/company_municipality_mapping.csv"),
        "priority": rr(root, "data/master/07_implementation_priority.csv"),
        "deferred": rr(root, "data/master/05_deferred_municipalities.csv"),
        "registry": rr(root, "data/master/02_official_domain_registry.csv"),
        "batch_municipalities": rr(root, "data/research/batches/batch_10/batch_10_municipalities.csv"),
        "batch_categories": rr(root, "data/research/batches/batch_10/batch_10_categories.csv"),
        "batch_sources": rr(root, "data/research/batches/batch_10/batch_10_sources.csv"),
        "batch_qa": rr(root, "data/research/batches/batch_10/batch_10_qa.csv"),
        "batch_mappings": rr(root, "data/research/batches/batch_10/batch_10_item_mapping.csv"),
        "batch_coverage": rr(root, "data/research/batches/batch_10/batch_10_item_coverage.csv"),
    }


def validate_context(data) -> list[str]:
    errors: list[str] = []

    municipalities = [r for r in data["municipalities"] if r.get("municipality_id") == MID]
    qas = [r for r in data["qa"] if r.get("municipality_id") == MID]
    if len(municipalities) != 1 or municipalities[0].get("確認ステータス") != "QA_PASSED":
        errors.append("M098 municipality ordinary research layer is not QA_PASSED")
    if len(qas) != 1 or qas[0].get("確認ステータス") != "QA_PASSED":
        errors.append("M098 computed QA is not QA_PASSED")

    categories = [r for r in data["categories"] if r.get("municipality_id") == MID]
    category_by = {r.get("category_id"): r for r in categories}
    if set(category_by) != EXPECTED_CATEGORIES or len(categories) != len(EXPECTED_CATEGORIES):
        errors.append("M098 canonical category set differs from reviewed builder")
    for cid in EXPECTED_CATEGORIES:
        row = category_by.get(cid, {})
        if row.get("rule_status") != "CURRENT":
            errors.append(f"{cid}: category is not CURRENT")
    button_category = category_by.get("C-M098-10", {})
    if button_category.get("ui_role") != "REFERENCE_ONLY" or button_category.get("collection_channel") != "RETAIL_TAKEBACK":
        errors.append("C-M098-10: button-battery route must remain internal retail take-back")
    excluded_category = category_by.get("C-M098-09", {})
    if excluded_category.get("ui_role") != "EXCLUDED_NOTICE" or excluded_category.get("自治体収集外か") != "TRUE":
        errors.append("C-M098-09: city-not-processed route is not modeled as EXCLUDED_NOTICE")

    sources = [r for r in data["sources"] if r.get("municipality_id") == MID]
    source_by = {r.get("source_id"): r for r in sources}
    if set(source_by) != EXPECTED_SOURCES or len(sources) != len(EXPECTED_SOURCES):
        errors.append("M098 canonical source set differs from reviewed builder")
    for sid in EXPECTED_SOURCES:
        row = source_by.get(sid, {})
        if row.get("official_verified") != "TRUE" or not row.get("公式URL", "").startswith("https://www.city.onomichi.hiroshima.jp/"):
            errors.append(f"{sid}: source is not verified Onomichi official evidence")

    audit = [r for r in data["audit"] if r.get("municipality_id") == MID]
    by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in audit:
        by_item[row.get("internal_item_id", "")].append(row)
    if set(by_item) != EXPECTED_ITEMS:
        errors.append("M098 audit must cover exact 40 items")
    if len(audit) != EXPECTED_BRANCHES:
        errors.append(f"M098 audit branch count mismatch expected={EXPECTED_BRANCHES} actual={len(audit)}")
    for iid in EXPECTED_ITEMS:
        rows = sorted(by_item.get(iid, []), key=lambda r: int(r.get("branch_order") or 0))
        expected_rules = build.RULES.get(iid, [])
        if len(rows) != len(expected_rules):
            errors.append(f"{iid}: branch count differs from reviewed rules")
            continue
        if [r.get("branch_order") for r in rows] != [str(i) for i in range(1, len(rows) + 1)]:
            errors.append(f"{iid}: non-contiguous audit branch order")
        for row, expected in zip(rows, expected_rules):
            if row.get("branch_review_status") != "COMPLETE" or row.get("checked_date") != build.CHECKED or row.get("reviewer") != build.REVIEWER:
                errors.append(f"{iid}: incomplete audit metadata")
            if row.get("evidence_basis") not in {"DIRECT_ITEM", "OFFICIAL_RULE_DERIVED"}:
                errors.append(f"{iid}: unsupported evidence basis")
            if row.get("category_id") != expected["category_id"] or row.get("item_evidence_source_id") != expected["source_id"]:
                errors.append(f"{iid}: audit differs from reviewed rule set")
            src = source_by.get(row.get("item_evidence_source_id", ""), {})
            if src.get("official_verified") != "TRUE" or row.get("item_evidence_url") != src.get("公式URL"):
                errors.append(f"{iid}: item evidence is not official source")
            cat = category_by.get(row.get("category_id", ""), {})
            if not cat or row.get("category_name") != cat.get("自治体正式名称"):
                errors.append(f"{iid}: audit category/name mismatch")

    mappings = [r for r in data["mappings"] if r.get("municipality_id") == MID]
    map_by_key = {(r.get("internal_item_id"), r.get("branch_order")): r for r in mappings}
    audit_by_key = {(r.get("internal_item_id"), r.get("branch_order")): r for r in audit}
    if len(mappings) != EXPECTED_BRANCHES or set(map_by_key) != set(audit_by_key):
        errors.append("M098 canonical mappings must exactly match reviewed branches")
    for key, review in audit_by_key.items():
        row = map_by_key.get(key, {})
        if row.get("mapping_status") != "APP_READY" or row.get("evidence_scope") != "ITEM_SPECIFIC" or row.get("branch_review_status") != "COMPLETE":
            errors.append(f"{key[0]}: canonical branch is not atomic APP_READY")
        parity = [
            ("category_id", "category_id"), ("条件", "condition"), ("前処理", "preparation"),
            ("例外分別先", "exception_destination"), ("item_evidence_source_id", "item_evidence_source_id"),
            ("item_evidence_url", "item_evidence_url"), ("item_evidence_locator", "item_evidence_locator"),
        ]
        if any(row.get(a) != review.get(b) for a, b in parity):
            errors.append(f"{key[0]}: canonical/audit mismatch")

    coverage = [r for r in data["coverage"] if r.get("municipality_id") == MID]
    cov_by = {r.get("internal_item_id"): r for r in coverage}
    if len(coverage) != 40 or set(cov_by) != EXPECTED_ITEMS:
        errors.append("M098 coverage must contain exact 40 rows")
    for iid in EXPECTED_ITEMS:
        row = cov_by.get(iid, {})
        if row.get("coverage_status") != "APP_READY" or row.get("branch_completeness_confirmed") != "TRUE" or row.get("evidence_scope") != "ITEM_SPECIFIC":
            errors.append(f"{iid}: coverage is not APP_READY")
        if row.get("mapping_branch_count") != str(len(by_item.get(iid, []))):
            errors.append(f"{iid}: coverage branch count mismatch")

    critical = {
        "I028": {"C-M098-10"},
        "I029": {"C-M098-06"},
        "I031": {"C-M098-06"},
        "I032": {"C-M098-08"},
        "I033": {"C-M098-06"},
        "I037": {"C-M098-09"},
        "I038": {"C-M098-09"},
        "I040": {"C-M098-01", "C-M098-07"},
    }
    for iid, expected in critical.items():
        actual = {r.get("category_id") for r in by_item.get(iid, [])}
        if actual != expected:
            errors.append(f"{iid}: critical category mismatch {sorted(actual)}")
    bulb = " ".join(" ".join(r.values()) for r in by_item.get("I031", []))
    if "S-M098-06" not in bulb or "有害ごみ" not in bulb:
        errors.append("I031: April-2026 hazardous-waste bulb precedence missing")
    mobile = " ".join(" ".join(r.values()) for r in by_item.get("I029", []))
    if "有害ごみ" not in mobile or "膨張" not in mobile:
        errors.append("I029: current mobile-battery safety rule missing")
    spray = " ".join(" ".join(r.values()) for r in by_item.get("I032", []))
    if "使い切" not in spray or "穴" not in spray:
        errors.append("I032: use-up/hole rule missing")
    lighter = " ".join(" ".join(r.values()) for r in by_item.get("I033", []))
    if "使い切" not in lighter or "別" not in lighter:
        errors.append("I033: lighter use-up/separate-bag rule missing")
    if len(by_item.get("I040", [])) != 2:
        errors.append("I040: normal and oversize pruning branches must both remain")

    scope = [r for r in data["scope"] if r.get("municipality_id") == MID]
    if len(scope) != 1 or scope[0].get("scoring_status") != "APP_READY" or scope[0].get("required_item_count") != "40" or scope[0].get("required_branch_count") != str(EXPECTED_BRANCHES):
        errors.append("M098 APP_READY scope mismatch")

    groups = [r for r in data["groups"] if r.get("municipality_id") == MID]
    if len(groups) != 1 or groups[0].get("lesson_variant_group_id") != "LV-M098-01" or groups[0].get("learner_region_selector_required") != "FALSE":
        errors.append("M098 must preserve one hidden learner lesson group")
    districts = [r for r in data["districts"] if r.get("municipality_id") == MID]
    if len(districts) != 6 or {r.get("lesson_variant_group_id") for r in districts} != {"LV-M098-01"} or any(r.get("learner_visible") != "FALSE" for r in districts):
        errors.append("M098 six district scopes must remain one non-visible lesson group")
    variant_rows = [r for r in data["variant_scoring"] if r.get("municipality_id") == MID]
    if len(variant_rows) != 10 or {r.get("internal_item_id") for r in variant_rows} != FIXED10 or {r.get("lesson_variant_group_id") for r in variant_rows} != {"LV-M098-01"}:
        errors.append("M098 existing fixed10 lesson scoring changed")

    companies = [r for r in data["company"] if r.get("municipality_id") == MID]
    if {r.get("company_id") for r in companies} != EXPECTED_COMPANIES or len(companies) != 3:
        errors.append("M098 must keep exactly the three confirmed company mappings")
    for row in companies:
        if row.get("mapping_status") != "CONFIRMED" or row.get("active") != "TRUE" or row.get("lesson_variant_group_id") != "LV-M098-01":
            errors.append(f"{row.get('company_id')}: company routing not activated safely")

    priority = [r for r in data["priority"] if r.get("municipality_id") == MID]
    if len(priority) != 1 or priority[0].get("implementation_status") != "IMPLEMENTED" or priority[0].get("readiness_status_snapshot") != "APP_READY":
        errors.append("M098 implementation priority snapshot not APP_READY")
    if any(r.get("municipality_id") == MID for r in data["deferred"]):
        errors.append("M098 obsolete schema-scope DEFERRED row must be removed")
    registry = [r for r in data["registry"] if r.get("municipality_id") == MID and r.get("host") == "www.city.onomichi.hiroshima.jp"]
    if len(registry) != 1 or registry[0].get("authority_type") != "MUNICIPAL_DOMAIN":
        errors.append("M098 official host registry missing")

    batch_m = [r for r in data["batch_municipalities"] if r.get("municipality_id") == MID]
    batch_c = [r for r in data["batch_categories"] if r.get("municipality_id") == MID]
    batch_s = [r for r in data["batch_sources"] if r.get("municipality_id") == MID]
    batch_q = [r for r in data["batch_qa"] if r.get("municipality_id") == MID]
    batch_map = [r for r in data["batch_mappings"] if r.get("municipality_id") == MID]
    batch_cov = [r for r in data["batch_coverage"] if r.get("municipality_id") == MID]
    if len(batch_m) != 1 or batch_m[0].get("確認ステータス") != "QA_PASSED" or len(batch_q) != 1 or batch_q[0].get("確認ステータス") != "QA_PASSED":
        errors.append("M098 Batch 10 ordinary municipality/QA layer missing")
    if {r.get("category_id") for r in batch_c} != EXPECTED_CATEGORIES or {r.get("source_id") for r in batch_s} != EXPECTED_SOURCES:
        errors.append("M098 Batch 10 ordinary category/source layer mismatch")
    if batch_map:
        errors.append("M098 APP item mappings must not leak into completed Batch 10 ordinary layer")
    if len(batch_cov) != 40 or {r.get("internal_item_id") for r in batch_cov} != EXPECTED_ITEMS or any(r.get("coverage_status") != "NOT_RESEARCHED" for r in batch_cov):
        errors.append("M098 Batch 10 must retain 40 NOT_RESEARCHED APP placeholders")

    return errors


def validate(root: Path = ROOT) -> list[str]:
    return validate_context(load(root))


def main() -> int:
    errors = validate()
    if errors:
        print("M098_APP_READINESS_VALIDATION_FAILED")
        for error in errors:
            print("-", error)
        return 1
    print("M098_APP_READINESS_VALIDATION_PASSED")
    print(f"municipality=M098 items=40 branches={EXPECTED_BRANCHES} lesson_group=LV-M098-01 districts=6 companies=3")
    return 0


if __name__ == "__main__":
    sys.exit(main())
