#!/usr/bin/env python3
"""Validate Hiroshima City's complete 40-item APP readiness Pilot."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from schema_v12 import read_csv


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "data/research/app_readiness/m094_item_review.csv"
MID = "M094"
EXPECTED_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "canonical_name",
    "display_name", "official_item_wording", "category_id", "category_name",
    "condition", "preparation", "exception_destination", "evidence_basis",
    "item_evidence_source_id", "item_evidence_url", "item_evidence_locator",
    "branch_review_status", "checked_date", "reviewer", "note",
]

EXPECTED_CATEGORIES = {
    "I001": ["C-M094-02"], "I002": ["C-M094-03"],
    "I003": ["C-M094-03", "C-M094-01"], "I004": ["C-M094-06"],
    "I005": ["C-M094-06"], "I006": ["C-M094-06"],
    "I007": ["C-M094-03", "C-M094-01"],
    "I008": ["C-M094-03", "C-M094-01"],
    "I009": ["C-M094-03", "C-M094-01", "C-M094-01"],
    "I010": ["C-M094-03", "C-M094-01", "C-M094-01"],
    "I011": ["C-M094-03"], "I012": ["C-M094-03", "C-M094-04"],
    "I013": ["C-M094-06"], "I014": ["C-M094-06"],
    "I015": ["C-M094-06"], "I016": ["C-M094-06", "C-M094-01"],
    "I017": ["C-M094-01"], "I018": ["C-M094-01"],
    "I019": ["C-M094-01"], "I020": ["C-M094-01"],
    "I021": ["C-M094-06"], "I022": ["C-M094-05"],
    "I023": ["C-M094-05", "C-M094-08"],
    "I024": ["C-M094-05", "C-M094-06", "C-M094-08"],
    "I025": ["C-M094-06", "C-M094-05"],
    "I026": ["C-M094-06", "C-M094-05"],
    "I027": ["C-M094-07"], "I028": ["C-M094-07"],
    "I029": ["C-M094-07"], "I030": ["C-M094-07", "C-M094-05"],
    "I031": ["C-M094-05", "C-M094-07"],
    "I032": ["C-M094-06", "C-M094-09"],
    "I033": ["C-M094-05"], "I034": ["C-M094-05", "C-M094-08"],
    "I035": ["C-M094-05"], "I036": ["C-M094-08"],
    "I037": ["C-M094-08"], "I038": ["C-M094-09"],
    "I039": ["C-M094-01"], "I040": ["C-M094-01", "C-M094-09"],
}

REQUIRED_CONCEPTS = {
    "I003": ["紙製"], "I007": ["汚れ"], "I008": ["色柄", "汚れ"],
    "I009": ["紙製", "汚れ"], "I010": ["紙製", "汚れ"],
    "I012": ["商品を保護", "保護する容器包装ではない"],
    "I016": ["名刺大"], "I023": ["30cm"],
    "I024": ["耐熱", "30cm"], "I025": ["危険", "耐熱"],
    "I026": ["ナイフ", "かみそり"], "I029": ["破損・膨張"],
    "I030": ["水銀", "LED"], "I031": ["白熱", "蛍光"],
    "I032": ["中身を空", "市で収集しない"], "I034": ["30cm"],
    "I035": ["取り外せない", "危険"], "I037": ["家電リサイクル"],
    "I038": ["メーカー", "パソコン3R"], "I040": ["生木5cm", "多量"],
}

BAD_GENERIC_TEXT = {
    "他の分別区分に該当する物", "家庭から出る対象物", "該当する公式区分",
    "公式ガイドの品目・寸法条件", "公式ガイドの指定方法",
    "種類別にまとめ、必要に応じて洗浄・乾燥",
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
    mappings = rows(root / "data/research/05_item_mapping_master.csv")
    coverage = {(r["municipality_id"], r["internal_item_id"]): r for r in rows(root / "data/research/07_item_mapping_coverage.csv")}
    m094_mappings = [r for r in mappings if r["municipality_id"] == MID]
    mapping_by_key = {(r["internal_item_id"], r["branch_order"]): r for r in m094_mappings}

    by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in review:
        by_item[row.get("internal_item_id", "")].append(row)
    expected_items = {f"I{i:03d}" for i in range(1, 41)}
    if set(by_item) != expected_items:
        errors.append(f"review grid must contain I001-I040: missing={sorted(expected_items-set(by_item))} extra={sorted(set(by_item)-expected_items)}")
    if len(review) != 59:
        errors.append(f"review must contain 59 complete condition branches: {len(review)}")
    if len(mapping_by_key) != 59 or len(m094_mappings) != 59:
        errors.append(f"canonical M094 mapping must contain exactly 59 unique branches: rows={len(m094_mappings)} unique={len(mapping_by_key)}")

    for iid in sorted(expected_items):
        item_rows = sorted(by_item.get(iid, []), key=lambda r: int(r.get("branch_order") or 0))
        actual_categories = [r.get("category_id", "") for r in item_rows]
        if actual_categories != EXPECTED_CATEGORIES[iid]:
            errors.append(f"condition branches collapsed/reordered: {iid} {actual_categories}")
        if [r.get("branch_order") for r in item_rows] != [str(i) for i in range(1, len(item_rows) + 1)]:
            errors.append(f"non-contiguous review branches: {iid}")
        combined = "\n".join(
            row.get(field, "") for row in item_rows
            for field in ["official_item_wording", "condition", "preparation", "exception_destination", "note"]
        )
        for concept in REQUIRED_CONCEPTS.get(iid, []):
            if concept not in combined:
                errors.append(f"required condition concept missing: {iid} {concept}")

        cov = coverage.get((MID, iid), {})
        if (
            cov.get("coverage_status") != "APP_READY"
            or cov.get("branch_completeness_confirmed") != "TRUE"
            or cov.get("evidence_scope") != "ITEM_SPECIFIC"
            or cov.get("mapping_branch_count") != str(len(item_rows))
        ):
            errors.append(f"coverage not atomically APP_READY/complete: {iid}")

        master = items.get(iid)
        if not master:
            errors.append(f"unknown common item: {iid}")
            continue
        for row in item_rows:
            label = f"{iid}/{row.get('branch_order')}"
            required = [
                "municipality_id", "canonical_name", "display_name", "official_item_wording",
                "category_id", "category_name", "condition", "preparation",
                "exception_destination", "evidence_basis", "item_evidence_source_id",
                "item_evidence_url", "item_evidence_locator", "branch_review_status",
                "checked_date", "reviewer", "note",
            ]
            if any(not row.get(field) for field in required):
                errors.append(f"review branch has blank required field: {label}")
            if row.get("municipality_id") != MID:
                errors.append(f"wrong municipality scope: {label}")
            if row.get("canonical_name") != master["一般管理用名称"] or row.get("display_name") != master["教材表示名"]:
                errors.append(f"common item master mismatch: {label}")
            if row.get("evidence_basis") not in {"DIRECT_ITEM", "OFFICIAL_RULE_DERIVED"}:
                errors.append(f"bad evidence basis: {label}")
            if row.get("branch_review_status") != "COMPLETE" or not valid_date(row.get("checked_date", "")):
                errors.append(f"bad review status/date: {label}")
            if any(text in combined for text in BAD_GENERIC_TEXT):
                errors.append(f"generic placeholder text is forbidden: {iid}")

            category = categories.get((MID, row.get("category_id", "")))
            source = sources.get((MID, row.get("item_evidence_source_id", "")))
            if not category or category.get("rule_status") != "CURRENT":
                errors.append(f"unknown/non-current category: {label}")
            elif row.get("category_name") != category.get("自治体正式名称"):
                errors.append(f"category name mismatch: {label}")
            if (
                not source
                or source.get("official_verified") != "TRUE"
                or source.get("現行性") not in {"CURRENT", "現行", "現行案内中"}
            ):
                errors.append(f"item evidence is not a current official source: {label}")
            else:
                if row.get("item_evidence_url") != source.get("公式URL"):
                    errors.append(f"item evidence URL/source mismatch: {label}")
                if not row.get("item_evidence_url", "").startswith("https://www.city.hiroshima.lg.jp/"):
                    errors.append(f"item evidence is outside Hiroshima official domain: {label}")

            mapping = mapping_by_key.get((iid, row.get("branch_order", "")))
            if not mapping:
                errors.append(f"canonical branch missing: {label}")
                continue
            comparisons = {
                "category_id": "category_id", "category_name": "分別区分正式名称",
                "official_item_wording": "自治体での品目表記", "condition": "条件",
                "preparation": "前処理", "exception_destination": "例外分別先",
                "item_evidence_source_id": "item_evidence_source_id",
                "item_evidence_url": "item_evidence_url",
                "item_evidence_locator": "item_evidence_locator",
            }
            if any(row.get(left) != mapping.get(right) for left, right in comparisons.items()):
                errors.append(f"review/canonical mapping mismatch: {label}")
            if (
                mapping.get("mapping_status") != "APP_READY"
                or mapping.get("branch_review_status") != "COMPLETE"
                or mapping.get("evidence_scope") != "ITEM_SPECIFIC"
                or not valid_date(mapping.get("reviewed_date", ""))
                or not mapping.get("reviewed_by")
            ):
                errors.append(f"canonical branch is not complete APP_READY: {label}")

    app_mids = {
        row["municipality_id"] for row in rows(root / "data/research/07_item_mapping_coverage.csv")
        if row.get("coverage_status") == "APP_READY"
    }
    if app_mids != {MID}:
        errors.append(f"Pilot must atomically promote M094 only: {sorted(app_mids)}")
    return errors


def main() -> int:
    fields, review = read_csv(AUDIT_PATH)
    errors = []
    if fields != EXPECTED_FIELDS:
        errors.append(f"review header mismatch: {fields}")
    errors.extend(validate_review_rows(review))
    if errors:
        print("M094_APP_READINESS_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("M094_APP_READINESS_VALIDATION_PASSED")
    print("municipality=M094 items=40 branches=59 app_ready_pairs=40 official_sources=9")
    return 0


if __name__ == "__main__":
    sys.exit(main())
