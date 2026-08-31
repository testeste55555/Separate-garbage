#!/usr/bin/env python3
"""Strict validator for M009 Oe Town 40-item APP_READY."""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from schema_v12 import read_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M009"
EXPECTED_ITEMS = {f"I{i:03d}" for i in range(1, 41)}
IMAGE_ITEMS = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}
EXPECTED_IMAGE_CATEGORY = {
    "I001":"C-M009-05", "I004":"C-M009-04", "I006":"C-M009-03", "I007":"C-M009-01",
    "I013":"C-M009-01", "I014":"C-M009-01", "I017":"C-M009-01", "I029":"C-M009-06",
    "I031":"C-M009-02", "I033":"C-M009-02",
}


def rr(root: Path, path: str):
    return read_csv(root / path)[1]


def load(root: Path = ROOT):
    return {
        "audit": rr(root, "data/research/app_readiness/m009_item_review.csv"),
        "mappings": rr(root, "data/research/05_item_mapping_master.csv"),
        "coverage": rr(root, "data/research/07_item_mapping_coverage.csv"),
        "categories": rr(root, "data/research/02_categories_master.csv"),
        "sources": rr(root, "data/research/03_sources_master.csv"),
        "scope": rr(root, "data/app/lesson_mode_app_ready_scope.csv"),
        "images": rr(root, "data/app/item_image_mapping_pilot_top8.csv"),
        "company": rr(root, "data/app/company_municipality_mapping.csv"),
        "priority": rr(root, "data/master/07_implementation_priority.csv"),
        "variants": rr(root, "data/app/lesson_variant_groups.csv"),
        "municipalities": rr(root, "data/research/04_municipalities_research.csv"),
        "qa": rr(root, "data/research/06_qa_log.csv"),
    }


def validate_context(data) -> list[str]:
    errors: list[str] = []
    audit = [r for r in data["audit"] if r.get("municipality_id") == MID]
    mappings = [r for r in data["mappings"] if r.get("municipality_id") == MID]
    coverage = [r for r in data["coverage"] if r.get("municipality_id") == MID]
    categories = {(r.get("municipality_id"), r.get("category_id")): r for r in data["categories"]}
    sources = {(r.get("municipality_id"), r.get("source_id")): r for r in data["sources"]}
    by_item: dict[str, list[dict[str,str]]] = defaultdict(list)
    for row in audit:
        by_item[row.get("internal_item_id", "")].append(row)
    if set(by_item) != EXPECTED_ITEMS:
        errors.append("M009 audit must cover exact 40 items")
    for iid, rows in by_item.items():
        rows.sort(key=lambda r: int(r.get("branch_order") or 0))
        if [r.get("branch_order") for r in rows] != [str(i) for i in range(1, len(rows)+1)]:
            errors.append(f"{iid}: non-contiguous audit branches")
        for row in rows:
            if row.get("branch_review_status") != "COMPLETE" or row.get("checked_date") != "2026-08-31" or row.get("reviewer") != "OPENAI_M009_APP_READY_V1":
                errors.append(f"{iid}: incomplete audit metadata")
            if row.get("evidence_basis") not in {"DIRECT_ITEM", "OFFICIAL_RULE_DERIVED"}:
                errors.append(f"{iid}: unsupported evidence basis")
            src = sources.get((MID, row.get("item_evidence_source_id", "")))
            if not src or src.get("official_verified") != "TRUE" or row.get("item_evidence_url") != src.get("公式URL"):
                errors.append(f"{iid}: item evidence is not current official source")
            cat = categories.get((MID, row.get("category_id", "")))
            if not cat or cat.get("rule_status") != "CURRENT" or cat.get("自治体正式名称") != row.get("category_name"):
                errors.append(f"{iid}: current category mismatch")

    map_by_item: dict[str, list[dict[str,str]]] = defaultdict(list)
    for row in mappings:
        map_by_item[row.get("internal_item_id", "")].append(row)
    if set(map_by_item) != EXPECTED_ITEMS or len(mappings) != len(audit):
        errors.append("M009 canonical mappings must exactly match 40-item audit branches")
    audit_key = {(r["internal_item_id"], r["branch_order"]): r for r in audit}
    for row in mappings:
        review = audit_key.get((row.get("internal_item_id", ""), row.get("branch_order", "")))
        if not review:
            errors.append("canonical mapping lacks audit branch")
            continue
        if row.get("mapping_status") != "APP_READY" or row.get("evidence_scope") != "ITEM_SPECIFIC" or row.get("branch_review_status") != "COMPLETE":
            errors.append(f"{row.get('internal_item_id')}: canonical branch not APP_READY")
        parity = [("category_id","category_id"),("条件","condition"),("前処理","preparation"),("例外分別先","exception_destination"),("item_evidence_source_id","item_evidence_source_id"),("item_evidence_url","item_evidence_url"),("item_evidence_locator","item_evidence_locator")]
        if any(row.get(a) != review.get(b) for a,b in parity):
            errors.append(f"{row.get('internal_item_id')}: canonical/audit mismatch")

    cov = {r.get("internal_item_id"): r for r in coverage}
    if set(cov) != EXPECTED_ITEMS or len(coverage) != 40:
        errors.append("M009 coverage must contain exact 40 rows")
    for iid in EXPECTED_ITEMS:
        row = cov.get(iid, {})
        if row.get("coverage_status") != "APP_READY" or row.get("branch_completeness_confirmed") != "TRUE" or row.get("evidence_scope") != "ITEM_SPECIFIC" or row.get("mapping_branch_count") != str(len(by_item.get(iid, []))):
            errors.append(f"{iid}: coverage not atomic APP_READY")

    critical = {
        "I007":{"C-M009-01"}, "I017":{"C-M009-01"}, "I027":{"C-M009-06"}, "I028":{"C-M009-06"},
        "I029":{"C-M009-06"}, "I030":{"C-M009-07"}, "I031":{"C-M009-02"}, "I032":{"C-M009-02"},
        "I033":{"C-M009-02"}, "I035":{"C-M009-02"}, "I036":{"C-M009-08"}, "I037":{"C-M009-09"},
        "I038":{"C-M009-10"}, "I039":{"C-M009-01"}, "I040":{"C-M009-01","C-M009-09"},
    }
    for iid, expected in critical.items():
        actual = {r.get("category_id") for r in by_item.get(iid, [])}
        if actual != expected:
            errors.append(f"{iid}: critical category mismatch {sorted(actual)}")
    if len(by_item.get("I040", [])) != 2:
        errors.append("I040: normal/oversize branches must both remain")
    mobile = " ".join(" ".join(r.values()) for r in by_item.get("I029", []))
    if "乾電池と一緒" not in mobile or "絶縁" not in mobile:
        errors.append("I029: current mobile-battery rule missing")
    spray = " ".join(" ".join(r.values()) for r in by_item.get("I032", []))
    if "穴をあけず" not in spray or "使い切" not in spray:
        errors.append("I032: no-hole/use-up rule missing")
    pc = categories.get((MID, "C-M009-10"), {})
    if pc.get("ui_role") != "REFERENCE_ONLY" or pc.get("collection_channel") != "DIRECT_HAUL" or pc.get("自治体収集外か") != "FALSE":
        errors.append("I038: household PC direct-haul category is not modeled safely")
    dry = categories.get((MID, "C-M009-06"), {})
    if "モバイルバッテリー" not in dry.get("代表品目", "") or "ボタン電池" not in dry.get("代表品目", ""):
        errors.append("C-M009-06: current battery scope not refreshed")

    scope = [r for r in data["scope"] if r.get("municipality_id") == MID]
    if len(scope) != 1 or scope[0].get("scoring_status") != "APP_READY" or scope[0].get("required_item_count") != "40" or scope[0].get("required_branch_count") != str(len(audit)):
        errors.append("M009 APP_READY scope mismatch")
    images = [r for r in data["images"] if r.get("municipality_id") == MID]
    if len(images) != 10 or {r.get("internal_item_id") for r in images} != IMAGE_ITEMS:
        errors.append("M009 fixed10 image mapping mismatch")
    for row in images:
        if row.get("review_status") != "VERIFIED" or row.get("category_id") != EXPECTED_IMAGE_CATEGORY.get(row.get("internal_item_id")):
            errors.append(f"{row.get('internal_item_id')}: fixed10 category mismatch")
    if any(r.get("municipality_id") == MID for r in data["variants"]):
        errors.append("M009 must not have learner regional variant")
    company = [r for r in data["company"] if r.get("company_id") == "C011" and r.get("municipality_id") == MID]
    if len(company) != 1 or company[0].get("active") != "TRUE":
        errors.append("C011 must activate after M009 APP_READY")
    priority = [r for r in data["priority"] if r.get("municipality_id") == MID]
    if len(priority) != 1 or priority[0].get("readiness_status_snapshot") != "APP_READY":
        errors.append("M009 priority snapshot not APP_READY")
    municipality = [r for r in data["municipalities"] if r.get("municipality_id") == MID]
    if len(municipality) != 1 or municipality[0].get("reviewed_category_count") != "9":
        errors.append("M009 current category count must be 9 after PC direct-haul audit")
    qa = [r for r in data["qa"] if r.get("municipality_id") == MID]
    if len(qa) != 1 or qa[0].get("確認ステータス") != "QA_PASSED":
        errors.append("M009 category QA is not QA_PASSED")
    return errors


def validate(root: Path = ROOT) -> list[str]:
    return validate_context(load(root))


def main() -> int:
    errors = validate()
    if errors:
        print("M009_APP_READINESS_VALIDATION_FAILED")
        for error in errors:
            print("-", error)
        return 1
    data = load()
    audit = [r for r in data["audit"] if r.get("municipality_id") == MID]
    print("M009_APP_READINESS_VALIDATION_PASSED")
    print(f"municipality=M009 items=40 branches={len(audit)} image_pairs=10 company=C011_active")
    return 0


if __name__ == "__main__":
    sys.exit(main())
