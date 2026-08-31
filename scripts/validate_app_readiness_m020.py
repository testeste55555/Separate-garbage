#!/usr/bin/env python3
"""Strict validator for the M020 Shizuoka City 40-item APP_READY promotion."""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from schema_v12 import read_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M020"
EXPECTED_ITEMS = {f"I{i:03d}" for i in range(1, 41)}
IMAGE_ITEMS = ("I001", "I007", "I013", "I004", "I006", "I031", "I029", "I014", "I033", "I017")
EXPECTED_IMAGE_CATEGORY = {
    "I001": "C-M020-10",
    "I007": "C-M020-01",
    "I013": "C-M020-12",
    "I004": "C-M020-09",
    "I006": "C-M020-08",
    "I031": "C-M020-02",
    "I029": "C-M020-02",
    "I014": "C-M020-14",
    "I033": "C-M020-02",
    "I017": "C-M020-15",
}
CURRENT_SOURCE = {"現行", "現行案内中", "CURRENT"}


def rows(root: Path, relative: str) -> list[dict[str, str]]:
    return read_csv(root / relative)[1]


def load_context(root: Path = ROOT) -> dict[str, list[dict[str, str]]]:
    return {
        "audit": rows(root, "data/research/app_readiness/m020_item_review.csv"),
        "mappings": rows(root, "data/research/05_item_mapping_master.csv"),
        "coverage": rows(root, "data/research/07_item_mapping_coverage.csv"),
        "sources": rows(root, "data/research/03_sources_master.csv"),
        "categories": rows(root, "data/research/02_categories_master.csv"),
        "scope": rows(root, "data/app/lesson_mode_app_ready_scope.csv"),
        "images": rows(root, "data/app/item_image_mapping_pilot_top8.csv"),
        "company": rows(root, "data/app/company_municipality_mapping.csv"),
        "variants": rows(root, "data/app/lesson_variant_groups.csv"),
        "priority": rows(root, "data/master/07_implementation_priority.csv"),
        "qa": rows(root, "data/research/06_qa_log.csv"),
    }


def validate_context(data: dict[str, list[dict[str, str]]]) -> list[str]:
    errors: list[str] = []
    audit = [r for r in data["audit"] if r.get("municipality_id") == MID]
    mappings = [r for r in data["mappings"] if r.get("municipality_id") == MID]
    coverage = [r for r in data["coverage"] if r.get("municipality_id") == MID]
    sources = {(r.get("municipality_id"), r.get("source_id")): r for r in data["sources"]}
    categories = {(r.get("municipality_id"), r.get("category_id")): r for r in data["categories"]}

    by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in audit:
        by_item[row.get("internal_item_id", "")].append(row)
    if set(by_item) != EXPECTED_ITEMS:
        errors.append(f"audit item scope mismatch: missing={sorted(EXPECTED_ITEMS-set(by_item))} extra={sorted(set(by_item)-EXPECTED_ITEMS)}")
    if any(not rows_ for rows_ in by_item.values()):
        errors.append("audit contains empty item branch list")
    for iid, item_rows in by_item.items():
        item_rows.sort(key=lambda r: int(r.get("branch_order") or 0))
        if [r.get("branch_order") for r in item_rows] != [str(i) for i in range(1, len(item_rows) + 1)]:
            errors.append(f"{iid}: audit branch_order is not contiguous")
        if any(r.get("branch_review_status") != "COMPLETE" for r in item_rows):
            errors.append(f"{iid}: audit branch not COMPLETE")
        if any(r.get("checked_date") != "2026-08-31" or r.get("reviewer") != "OPENAI_M020_APP_READY_V1" for r in item_rows):
            errors.append(f"{iid}: audit metadata mismatch")

    mapping_by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in mappings:
        mapping_by_item[row.get("internal_item_id", "")].append(row)
    if set(mapping_by_item) != EXPECTED_ITEMS:
        errors.append("canonical M020 mapping must cover exact 40 items")
    if len(mappings) != len(audit):
        errors.append(f"canonical/audit branch count mismatch: mappings={len(mappings)} audit={len(audit)}")

    audit_by_key = {(r["internal_item_id"], r["branch_order"]): r for r in audit}
    for row in mappings:
        key = (row.get("internal_item_id", ""), row.get("branch_order", ""))
        review = audit_by_key.get(key)
        if not review:
            errors.append(f"mapping lacks audit branch: {key}")
            continue
        required = {
            "mapping_status": "APP_READY",
            "evidence_scope": "ITEM_SPECIFIC",
            "branch_review_status": "COMPLETE",
            "rule_status": "CURRENT",
            "reviewed_date": "2026-08-31",
            "reviewed_by": "OPENAI_M020_APP_READY_V1",
        }
        if any(row.get(field) != value for field, value in required.items()):
            errors.append(f"{key}: canonical APP_READY metadata incomplete")
        parity = [
            ("category_id", "category_id"), ("分別区分正式名称", "category_name"),
            ("条件", "condition"), ("前処理", "preparation"), ("例外分別先", "exception_destination"),
            ("item_evidence_source_id", "item_evidence_source_id"),
            ("item_evidence_url", "item_evidence_url"), ("item_evidence_locator", "item_evidence_locator"),
        ]
        if any(row.get(left) != review.get(right) for left, right in parity):
            errors.append(f"{key}: canonical/audit detail mismatch")
        category = categories.get((MID, row.get("category_id", "")))
        if not category or category.get("rule_status") != "CURRENT":
            errors.append(f"{key}: mapping targets non-current category")
        source = sources.get((MID, row.get("item_evidence_source_id", "")))
        if not source or source.get("official_verified") != "TRUE" or source.get("現行性") not in CURRENT_SOURCE:
            errors.append(f"{key}: item evidence is not current official")
        elif not source.get("公式URL", "").startswith("https://www.city.shizuoka.lg.jp/"):
            errors.append(f"{key}: item evidence is not on Shizuoka official host")
        elif source.get("公式URL") != row.get("item_evidence_url"):
            errors.append(f"{key}: item evidence URL mismatch")

    cov_by_item = {r.get("internal_item_id", ""): r for r in coverage}
    if set(cov_by_item) != EXPECTED_ITEMS or len(coverage) != 40:
        errors.append("M020 coverage must contain exactly 40 rows")
    for iid in EXPECTED_ITEMS:
        row = cov_by_item.get(iid)
        if not row:
            continue
        if (
            row.get("coverage_status") != "APP_READY"
            or row.get("branch_completeness_confirmed") != "TRUE"
            or row.get("evidence_scope") != "ITEM_SPECIFIC"
            or row.get("mapping_branch_count") != str(len(by_item.get(iid, [])))
        ):
            errors.append(f"{iid}: coverage is not atomic APP_READY")

    # Critical 2026 changes and condition branches.
    expected_item_categories = {
        "I027": {"C-M020-02"}, "I028": {"C-M020-02"}, "I029": {"C-M020-02"},
        "I030": {"C-M020-02"}, "I031": {"C-M020-02"}, "I033": {"C-M020-02"},
        "I035": {"C-M020-02"}, "I032": {"C-M020-07"}, "I037": {"C-M020-17"},
        "I038": {"C-M020-16"}, "I039": {"C-M020-01"}, "I040": {"C-M020-01"},
    }
    for iid, expected_categories in expected_item_categories.items():
        actual = {r.get("category_id") for r in by_item.get(iid, [])}
        if actual != expected_categories:
            errors.append(f"{iid}: critical category mismatch {sorted(actual)} != {sorted(expected_categories)}")

    if len(by_item.get("I017", [])) != 2 or {r.get("category_id") for r in by_item.get("I017", [])} != {"C-M020-15", "C-M020-01"}:
        errors.append("I017: aluminum/non-aluminum paper-pack branch must be retained")
    if len(by_item.get("I014", [])) != 2 or {r.get("category_id") for r in by_item.get("I014", [])} != {"C-M020-14", "C-M020-01"}:
        errors.append("I014: aluminum-processed cardboard branch must be retained")
    if len(by_item.get("I031", [])) != 2 or {r.get("category_id") for r in by_item.get("I031", [])} != {"C-M020-02"}:
        errors.append("I031: incandescent/LED evidence branches must both remain")

    dry = "\n".join(" ".join(r.values()) for r in by_item.get("I027", []))
    if "電池入り" not in dry or "令和8年4月" not in dry:
        errors.append("I027: 2026 battery separation/BOX rule missing")
    mobile = "\n".join(" ".join(r.values()) for r in by_item.get("I029", []))
    if "不燃・粗大" not in mobile and not any(r.get("category_id") == "C-M020-02" for r in by_item.get("I029", [])):
        errors.append("I029: mobile battery was not promoted to current nonburnable/bulky route")
    spray = "\n".join(" ".join(r.values()) for r in by_item.get("I032", []))
    if "穴を開けず" not in spray or "使い切" not in spray:
        errors.append("I032: no-hole/use-up spray rule missing")
    lighter = "\n".join(" ".join(r.values()) for r in by_item.get("I033", []))
    if "穴を" in lighter or "ガス抜き" in lighter:
        errors.append("I033: unsupported lighter gas/hole instruction introduced")
    pc = "\n".join(" ".join(r.values()) for r in by_item.get("I038", []))
    if "不燃・粗大ごみ不可" not in pc and not any(r.get("category_id") == "C-M020-16" for r in by_item.get("I038", [])):
        errors.append("I038: household PC current small-appliance route missing")

    retired = [categories.get((MID, cid), {}) for cid in ("C-M020-04", "C-M020-05", "C-M020-06")]
    if any(r.get("rule_status") != "RETIRED" or r.get("ui_role") != "HIDDEN" for r in retired):
        errors.append("legacy M020 危険・有害 categories must be retained only as hidden retired history")
    if any("危険・有害" in r.get("category_name", "") for r in audit):
        errors.append("legacy 危険・有害 label leaked into current APP_READY audit")

    scope = [r for r in data["scope"] if r.get("municipality_id") == MID]
    if len(scope) != 1:
        errors.append("M020 scope row must exist exactly once")
    elif (
        scope[0].get("scoring_status") != "APP_READY"
        or scope[0].get("required_item_count") != "40"
        or scope[0].get("required_branch_count") != str(len(audit))
        or scope[0].get("review_source") != "data/research/app_readiness/m020_item_review.csv"
    ):
        errors.append("M020 scope does not match 40-item audit")

    image_rows = [r for r in data["images"] if r.get("municipality_id") == MID]
    if len(image_rows) != 10 or {r.get("internal_item_id") for r in image_rows} != set(IMAGE_ITEMS):
        errors.append("M020 image mapping must contain exact fixed 10 items")
    first_audit = {iid: sorted(by_item.get(iid, []), key=lambda r: int(r.get("branch_order") or 0))[0] for iid in IMAGE_ITEMS if by_item.get(iid)}
    for row in image_rows:
        iid = row.get("internal_item_id", "")
        if row.get("review_status") != "VERIFIED" or row.get("category_id") != EXPECTED_IMAGE_CATEGORY.get(iid):
            errors.append(f"{iid}: M020 fixed10 image category mismatch")
        review = first_audit.get(iid)
        if not review:
            continue
        for left, right in [
            ("category_id", "category_id"), ("condition", "condition"), ("preparation", "preparation"),
            ("exception_destination", "exception_destination"), ("item_evidence_source_id", "item_evidence_source_id"),
            ("item_evidence_url", "item_evidence_url"), ("item_evidence_locator", "item_evidence_locator"),
        ]:
            if row.get(left) != review.get(right):
                errors.append(f"{iid}: image/audit parity mismatch for {left}")

    if any(r.get("municipality_id") == MID for r in data["variants"]):
        errors.append("M020 must not have learner regional variants for collection-channel-only differences")

    company = [r for r in data["company"] if r.get("company_id") == "C009" and r.get("municipality_id") == MID]
    if len(company) != 1 or company[0].get("active") != "TRUE" or company[0].get("mapping_status") != "CONFIRMED":
        errors.append("C009 M020 company site must activate only after APP_READY")

    priority = [r for r in data["priority"] if r.get("municipality_id") == MID]
    if len(priority) != 1 or priority[0].get("implementation_status") != "IMPLEMENTED" or priority[0].get("readiness_status_snapshot") != "APP_READY":
        errors.append("M020 implementation-priority snapshot not updated to APP_READY")

    qa = [r for r in data["qa"] if r.get("municipality_id") == MID]
    if len(qa) != 1 or qa[0].get("確認ステータス") != "QA_PASSED":
        errors.append("M020 canonical category QA is not QA_PASSED")

    if Counter(r.get("internal_item_id") for r in audit) != Counter({iid: len(by_item[iid]) for iid in EXPECTED_ITEMS}):
        errors.append("audit branch counter inconsistency")
    return errors


def validate(root: Path = ROOT) -> list[str]:
    return validate_context(load_context(root))


def main() -> int:
    errors = validate()
    if errors:
        print("M020_APP_READINESS_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    data = load_context()
    audit = [r for r in data["audit"] if r.get("municipality_id") == MID]
    print("M020_APP_READINESS_VALIDATION_PASSED")
    print(f"municipality=M020 items=40 branches={len(audit)} image_pairs=10 company=C009_active")
    return 0


if __name__ == "__main__":
    sys.exit(main())
