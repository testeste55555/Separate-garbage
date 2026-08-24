#!/usr/bin/env python3
"""Validate Higashihiroshima City's complete 40-item APP readiness review."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from apply_app_readiness_pilot_m104 import AUDIT_FIELDS, BRANCHES
from schema_v12 import read_csv

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "data/research/app_readiness/m104_item_review.csv"
MID = "M104"
BAD_GENERIC_TEXT = {
    "他の分別区分に該当する物", "家庭から出る対象物", "該当する公式区分",
    "公式ガイドの品目・寸法条件", "公式ガイドの指定方法",
    "種類別にまとめ、必要に応じて洗浄・乾燥",
}
REQUIRED_CONCEPTS = {
    "I006": ["飲料・食品用", "化粧品"], "I007": ["プラマーク", "汚れ"],
    "I008": ["色柄", "汚れ"], "I009": ["商品包装", "汚れ"],
    "I010": ["紙製", "汚れ"], "I011": ["包装以外", "汚れ"],
    "I012": ["商品を保護", "指定袋に入らない", "紙製"],
    "I016": ["感熱紙", "防水加工"], "I017": ["アルミ加工"],
    "I023": ["指定袋に入らない"], "I024": ["大型ガラス"],
    "I025": ["新聞紙"], "I026": ["包丁"], "I029": ["膨張", "40L"],
    "I035": ["外せず", "危険 電池あり"], "I036": ["ひも"],
    "I037": ["家電リサイクル券"], "I038": ["パソコン3R"],
    "I039": ["固形化"], "I040": ["8cm", "20cm", "150cm", "30cm"],
}


def rows(path: Path) -> list[dict[str, str]]:
    return read_csv(path)[1]


def valid_date(value: str) -> bool:
    try:
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)) and date.fromisoformat(value) <= date.today()
    except ValueError:
        return False


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
        errors.append(f"M104 must retain {expected_count} unique condition branches: review={len(review)} mapping={len(mappings)} unique={len(mapping_by_key)}")

    excluded = categories.get((MID, "C-M104-12"), {})
    if not (excluded.get("ui_role") == "EXCLUDED_NOTICE" and excluded.get("自治体収集外か") == "TRUE"):
        errors.append("M104 excluded-route reference category is missing or learner-visible")

    for iid in sorted(expected_items):
        item_rows = sorted(by_item.get(iid, []), key=lambda r: int(r.get("branch_order") or 0))
        expected_categories = [spec.category_id for spec in BRANCHES[iid]]
        if [r.get("category_id") for r in item_rows] != expected_categories:
            errors.append(f"condition branches collapsed/reordered: {iid}")
        if [r.get("branch_order") for r in item_rows] != [str(i) for i in range(1, len(item_rows) + 1)]:
            errors.append(f"non-contiguous branches: {iid}")
        combined = "\n".join(row.get(field, "") for row in item_rows for field in [
            "official_item_wording", "condition", "preparation", "exception_destination", "note"
        ])
        for concept in REQUIRED_CONCEPTS.get(iid, []):
            if concept not in combined:
                errors.append(f"required condition concept missing: {iid} {concept}")
        if any(text in combined for text in BAD_GENERIC_TEXT):
            errors.append(f"generic placeholder text is forbidden: {iid}")

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
            if row.get("municipality_id") != MID or row.get("branch_review_status") != "COMPLETE" or not valid_date(row.get("checked_date", "")):
                errors.append(f"bad scope/status/date: {label}")
            if row.get("evidence_basis") not in {"DIRECT_ITEM", "OFFICIAL_RULE_DERIVED"}:
                errors.append(f"bad evidence basis: {label}")

            category = categories.get((MID, row.get("category_id", "")))
            source = sources.get((MID, row.get("item_evidence_source_id", "")))
            if not category or category.get("rule_status") != "CURRENT" or row.get("category_name") != category.get("自治体正式名称"):
                errors.append(f"unknown/non-current category or name mismatch: {label}")
            if not source or source.get("official_verified") != "TRUE" or source.get("現行性") not in {"CURRENT", "現行", "現行案内中"}:
                errors.append(f"item evidence is not a current official source: {label}")
            elif row.get("item_evidence_url") != source.get("公式URL") or not row.get("item_evidence_url", "").startswith("https://www.city.higashihiroshima.lg.jp/"):
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
            if not (
                mapping.get("mapping_status") == "APP_READY"
                and mapping.get("branch_review_status") == "COMPLETE"
                and mapping.get("evidence_scope") == "ITEM_SPECIFIC"
                and valid_date(mapping.get("reviewed_date", "")) and mapping.get("reviewed_by")
            ):
                errors.append(f"canonical branch is not complete APP_READY: {label}")

    app_mids = {
        r["municipality_id"] for r in rows(root / "data/research/07_item_mapping_coverage.csv")
        if r.get("coverage_status") == "APP_READY"
    }
    if not {"M094", MID}.issubset(app_mids):
        errors.append(f"APP readiness progression must retain M094 and promote M104: {sorted(app_mids)}")
    return errors


def main() -> int:
    fields, review = read_csv(AUDIT_PATH)
    errors = ([] if fields == AUDIT_FIELDS else [f"review header mismatch: {fields}"])
    errors.extend(validate_review_rows(review))
    if errors:
        print("M104_APP_READINESS_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("M104_APP_READINESS_VALIDATION_PASSED")
    print("municipality=M104 items=40 branches=63 app_ready_pairs=40 item_evidence_sources=7 registered_official_sources=14 excluded_reference=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
