#!/usr/bin/env python3
"""Validate Kure City's complete 40-item APP readiness review."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from apply_app_readiness_pilot_m095 import AUDIT_FIELDS, BRANCHES
from schema_v12 import read_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M095"
AUDIT_PATH = ROOT / "data/research/app_readiness/m095_item_review.csv"


def rows(path: Path) -> list[dict[str, str]]:
    return read_csv(path)[1]


def validate_review_rows(review: list[dict[str, str]], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    items = {r["internal_item_id"]: r for r in rows(root / "data/master/04_common_items_master.csv")}
    categories = {(r["municipality_id"], r["category_id"]): r for r in rows(root / "data/research/02_categories_master.csv")}
    sources = {(r["municipality_id"], r["source_id"]): r for r in rows(root / "data/research/03_sources_master.csv")}
    mappings = [r for r in rows(root / "data/research/05_item_mapping_master.csv") if r["municipality_id"] == MID]
    coverage = {(r["municipality_id"], r["internal_item_id"]): r for r in rows(root / "data/research/07_item_mapping_coverage.csv")}
    mapping_by_key = {(r["internal_item_id"], r["branch_order"]): r for r in mappings}
    by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in review:
        by_item[row.get("internal_item_id", "")].append(row)

    expected_items = {f"I{i:03d}" for i in range(1, 41)}
    expected_count = sum(len(specs) for specs in BRANCHES.values())
    if set(by_item) != expected_items:
        errors.append(f"review grid must contain I001-I040: missing={sorted(expected_items-set(by_item))} extra={sorted(set(by_item)-expected_items)}")
    if len(review) != expected_count or len(mappings) != expected_count or len(mapping_by_key) != expected_count:
        errors.append(f"M095 branch count mismatch: expected={expected_count} review={len(review)} mapping={len(mappings)} unique={len(mapping_by_key)}")

    excluded = categories.get((MID, "C-M095-08"), {})
    if not (excluded.get("自治体正式名称") == "市で収集しないごみ" and excluded.get("ui_role") == "EXCLUDED_NOTICE" and excluded.get("自治体収集外か") == "TRUE"):
        errors.append("M095 excluded-route reference category missing or learner-visible")
    small = categories.get((MID, "C-M095-09"), {})
    if not (small.get("自治体正式名称") == "小型家電回収ボックス" and small.get("ui_role") == "REFERENCE_ONLY" and small.get("collection_channel") == "DROP_OFF"):
        errors.append("M095 small-appliance reference route missing or misclassified")

    critical_categories = {
        "I002": ["C-M095-04"], "I003": ["C-M095-04"],
        "I017": ["C-M095-06", "C-M095-02"],
        "I030": ["C-M095-07", "C-M095-02"],
        "I032": ["C-M095-07"], "I035": ["C-M095-09"],
        "I037": ["C-M095-08"], "I038": ["C-M095-08"],
        "I040": ["C-M095-01", "C-M095-08", "C-M095-08"],
    }

    for iid in sorted(expected_items):
        item_rows = sorted(by_item.get(iid, []), key=lambda r: int(r.get("branch_order") or 0))
        expected_categories = [spec.category_id for spec in BRANCHES[iid]]
        if [r.get("category_id") for r in item_rows] != expected_categories:
            errors.append(f"condition branches collapsed/reordered: {iid}")
        if iid in critical_categories and expected_categories != critical_categories[iid]:
            errors.append(f"critical category policy changed: {iid} {expected_categories}")
        if [r.get("branch_order") for r in item_rows] != [str(i) for i in range(1, len(item_rows) + 1)]:
            errors.append(f"non-contiguous branches: {iid}")

        cov = coverage.get((MID, iid), {})
        if not (
            cov.get("coverage_status") == "APP_READY"
            and cov.get("branch_completeness_confirmed") == "TRUE"
            and cov.get("evidence_scope") == "ITEM_SPECIFIC"
            and cov.get("mapping_branch_count") == str(len(item_rows))
        ):
            errors.append(f"coverage not atomically APP_READY/complete: {iid}")

        master = items.get(iid)
        for row in item_rows:
            label = f"{iid}/{row.get('branch_order')}"
            required = [
                "municipality_id", "canonical_name", "display_name", "official_item_wording",
                "category_id", "category_name", "condition", "preparation", "exception_destination",
                "evidence_basis", "item_evidence_source_id", "item_evidence_url",
                "item_evidence_locator", "branch_review_status", "checked_date", "reviewer", "note",
            ]
            if any(not row.get(field) for field in required):
                errors.append(f"review branch has blank required field: {label}")
            if not master or row.get("canonical_name") != master.get("一般管理用名称") or row.get("display_name") != master.get("教材表示名"):
                errors.append(f"common item master mismatch: {label}")
            if row.get("municipality_id") != MID or row.get("branch_review_status") != "COMPLETE" or row.get("checked_date") != "2026-08-24":
                errors.append(f"bad scope/status/date: {label}")
            if row.get("evidence_basis") not in {"DIRECT_ITEM", "OFFICIAL_RULE_DERIVED"}:
                errors.append(f"bad evidence basis: {label}")

            category = categories.get((MID, row.get("category_id", "")))
            source = sources.get((MID, row.get("item_evidence_source_id", "")))
            if not category or category.get("rule_status") != "CURRENT" or row.get("category_name") != category.get("自治体正式名称"):
                errors.append(f"unknown/non-current category or name mismatch: {label}")
            if not source or source.get("official_verified") != "TRUE" or source.get("現行性") not in {"CURRENT", "現行", "現行案内中"}:
                errors.append(f"item evidence is not a current official source: {label}")
            elif row.get("item_evidence_url") != source.get("公式URL") or not row.get("item_evidence_url", "").startswith("https://www.city.kure.lg.jp/"):
                errors.append(f"item evidence URL/source mismatch: {label}")

            mapping = mapping_by_key.get((iid, row.get("branch_order", "")))
            if not mapping:
                errors.append(f"canonical branch missing: {label}")
                continue
            comparisons = {
                "category_id": "category_id", "category_name": "分別区分正式名称",
                "official_item_wording": "自治体での品目表記", "condition": "条件",
                "preparation": "前処理", "exception_destination": "例外分別先",
                "item_evidence_source_id": "item_evidence_source_id",
                "item_evidence_url": "item_evidence_url", "item_evidence_locator": "item_evidence_locator",
            }
            if any(row.get(left) != mapping.get(right) for left, right in comparisons.items()):
                errors.append(f"review/canonical mapping mismatch: {label}")
            if not (mapping.get("mapping_status") == "APP_READY" and mapping.get("branch_review_status") == "COMPLETE" and mapping.get("evidence_scope") == "ITEM_SPECIFIC"):
                errors.append(f"canonical branch is not complete APP_READY: {label}")

    joined = "\n".join(str(v) for r in review for v in r.values())
    if "3日程度水に浸" in joined or "水に浸し" in joined:
        errors.append("obsolete lithium-battery water-soaking instruction reintroduced")
    if "穴を開けず" not in "\n".join(r.get("preparation", "") for r in by_item.get("I032", [])):
        errors.append("current no-puncture spray-can rule missing")
    if "中身が残" not in "\n".join(r.get("exception_destination", "") for r in by_item.get("I032", [])):
        errors.append("current remaining-content spray-can rule missing")
    if "環境施設課" not in "\n".join(r.get("exception_destination", "") for r in by_item.get("I029", [])):
        errors.append("swollen/deformed mobile-battery counter route missing")
    if any(r.get("category_id") != "C-M095-04" for iid in ("I002", "I003") for r in by_item.get(iid, [])):
        errors.append("post-April-2026 PET cap/label plastic-resource rule regressed")

    app_mids = {
        r["municipality_id"] for r in rows(root / "data/research/07_item_mapping_coverage.csv")
        if r.get("coverage_status") == "APP_READY"
    }
    if not {"M094", "M104", MID}.issubset(app_mids):
        errors.append(f"APP readiness progression must retain M094/M104 and promote M095: {sorted(app_mids)}")
    return errors


def main() -> int:
    fields, review = read_csv(AUDIT_PATH)
    errors = ([] if fields == AUDIT_FIELDS else [f"review header mismatch: {fields}"])
    errors.extend(validate_review_rows(review))
    if errors:
        print("M095_APP_READINESS_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("M095_APP_READINESS_VALIDATION_PASSED")
    print(f"municipality=M095 items=40 branches={sum(len(v) for v in BRANCHES.values())} app_ready_pairs=40 references=2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
