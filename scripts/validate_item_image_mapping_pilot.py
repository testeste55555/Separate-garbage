#!/usr/bin/env python3
"""Validate the 10 image items x 8 active Style Research municipalities pilot."""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from schema_v12 import read_csv


ROOT = Path(__file__).resolve().parents[1]
PILOT_PATH = ROOT / "data" / "app" / "item_image_mapping_pilot_top8.csv"
TARGETS = ("M094", "M095", "M097", "M104", "M105", "M106", "M107", "M109")
ITEMS = ("I001", "I007", "I013", "I004", "I006", "I031", "I029", "I014", "I033", "I017")
VARIANT_HOLD = {"M098", "M099"}
EXPECTED_UNRESOLVED = {("M107", "I031"), ("M107", "I033"), ("M109", "I031"), ("M109", "I033")}
EXPECTED_FIELDS = [
    "pair_order", "municipality_id", "municipality_name", "internal_item_id",
    "canonical_name", "display_name", "review_status", "evidence_basis",
    "category_id", "category_name", "condition", "preparation",
    "exception_destination", "item_evidence_source_id", "item_evidence_url",
    "item_evidence_locator", "checked_date", "reviewer", "note",
]
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


def validate_pilot_rows(pilot: list[dict[str, str]], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    master_items = {r["internal_item_id"]: r for r in rows(root / "data/master/04_common_items_master.csv")}
    assets = {r["internal_item_id"]: r for r in rows(root / "data/app/item_image_assets.csv")}
    municipalities = {r["municipality_id"]: r for r in rows(root / "data/research/04_municipalities_research.csv")}
    categories = {(r["municipality_id"], r["category_id"]): r for r in rows(root / "data/research/02_categories_master.csv")}
    sources = {(r["municipality_id"], r["source_id"]): r for r in rows(root / "data/research/03_sources_master.csv")}
    mappings = rows(root / "data/research/05_item_mapping_master.csv")
    coverage = {(r["municipality_id"], r["internal_item_id"]): r for r in rows(root / "data/research/07_item_mapping_coverage.csv")}
    lesson_ready_mids = {
        r["municipality_id"]
        for r in rows(root / "data/app/lesson_mode_app_ready_scope.csv")
        if r.get("scoring_status") == "LESSON_READY_10"
    }
    mapping_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for mapping in mappings:
        mapping_by_pair[(mapping["municipality_id"], mapping["internal_item_id"])].append(mapping)

    actual_pairs = [(r.get("municipality_id", ""), r.get("internal_item_id", "")) for r in pilot]
    expected_pairs = {(mid, iid) for mid in TARGETS for iid in ITEMS}
    if len(pilot) != 80:
        errors.append(f"pilot row count must be 80: {len(pilot)}")
    if len(set(actual_pairs)) != len(actual_pairs):
        errors.append("duplicate municipality/item pair")
    if set(actual_pairs) != expected_pairs:
        errors.append(f"pilot grid mismatch: missing={sorted(expected_pairs-set(actual_pairs))} extra={sorted(set(actual_pairs)-expected_pairs)}")
    if VARIANT_HOLD & {mid for mid, _ in actual_pairs}:
        errors.append("district-variant M098/M099 must not enter this municipality-wide pilot")

    status_counts = Counter(r.get("review_status", "") for r in pilot)
    if status_counts != Counter({"VERIFIED": 76, "UNRESOLVED": 4}):
        errors.append(f"unexpected review status counts: {dict(status_counts)}")

    for expected_order, row in enumerate(pilot, start=1):
        mid, iid = row.get("municipality_id", ""), row.get("internal_item_id", "")
        pair = (mid, iid)
        label = f"{mid}/{iid}"
        if row.get("pair_order") != str(expected_order):
            errors.append(f"non-deterministic pair_order: {label}")
        item = master_items.get(iid)
        asset = assets.get(iid)
        municipality = municipalities.get(mid)
        if not item or not asset or not municipality:
            errors.append(f"unknown master reference: {label}")
            continue
        if row.get("canonical_name") != item["一般管理用名称"] or row.get("display_name") != item["教材表示名"]:
            errors.append(f"item name differs from canonical master: {label}")
        if row.get("municipality_name") != municipality["市町村"]:
            errors.append(f"municipality name differs from canonical research: {label}")
        image_path = root / "app/assets/items" / asset.get("image_file", "")
        if asset.get("asset_status") != "CONFIRMED" or not image_path.is_file():
            errors.append(f"confirmed image asset missing: {label}")
        if not valid_date(row.get("checked_date", "")) or not row.get("reviewer"):
            errors.append(f"review metadata missing/invalid: {label}")

        unresolved = pair in EXPECTED_UNRESOLVED
        if unresolved != (row.get("review_status") == "UNRESOLVED"):
            errors.append(f"unexpected unresolved decision: {label}")
        pair_mappings = mapping_by_pair.get(pair, [])
        cov = coverage.get(pair)
        if not cov:
            errors.append(f"coverage row missing: {label}")
            continue
        if unresolved:
            evidence_fields = [
                "category_id", "category_name", "condition", "preparation", "exception_destination",
                "item_evidence_source_id", "item_evidence_url", "item_evidence_locator",
            ]
            if row.get("evidence_basis") != "UNRESOLVED" or any(row.get(field) for field in evidence_fields):
                errors.append(f"unresolved row claims a category or evidence: {label}")
            if not row.get("note") or "推測しない" not in row.get("note", ""):
                errors.append(f"unresolved row lacks explicit non-inference note: {label}")
            if any(m.get("mapping_status") in {"VERIFIED", "APP_READY"} for m in pair_mappings):
                errors.append(f"unresolved pair was promoted in canonical mapping: {label}")
            if cov.get("coverage_status") in {"VERIFIED", "VERIFIED_NOT_APPLICABLE", "APP_READY"}:
                errors.append(f"unresolved pair was promoted in coverage: {label}")
            continue

        if row.get("review_status") != "VERIFIED" or row.get("evidence_basis") not in {"DIRECT_ITEM", "OFFICIAL_CATEGORY_RULE"}:
            errors.append(f"bad verified decision enum: {label}")
        required = [
            "category_id", "category_name", "condition", "preparation", "exception_destination",
            "item_evidence_source_id", "item_evidence_url", "item_evidence_locator", "note",
        ]
        if any(not row.get(field) for field in required):
            errors.append(f"verified row has empty evidence/rule field: {label}")
        combined = "\n".join(row.get(field, "") for field in ["condition", "preparation", "exception_destination"])
        if any(text in combined for text in BAD_GENERIC_TEXT):
            errors.append(f"verified row contains banned generic placeholder: {label}")
        category = categories.get((mid, row.get("category_id", "")))
        source = sources.get((mid, row.get("item_evidence_source_id", "")))
        if not category or category.get("rule_status") != "CURRENT":
            errors.append(f"verified row references unknown/non-current category: {label}")
        elif row.get("category_name") != category.get("自治体正式名称"):
            errors.append(f"verified category name mismatch: {label}")
        if not source or source.get("official_verified") != "TRUE":
            errors.append(f"verified row lacks same-municipality official source: {label}")
        elif row.get("item_evidence_url") != source.get("公式URL"):
            errors.append(f"verified source URL mismatch: {label}")

        if cov.get("coverage_status") == "APP_READY":
            # Municipality-wide APP review may replace the Pilot's historical
            # evidence source with a more precise item locator and may add
            # same-category condition branches. Preserve the category decision,
            # then validate every matching later branch as complete.
            canonical = [
                m for m in pair_mappings
                if m.get("category_id") == row.get("category_id")
                and m.get("mapping_status") == "APP_READY"
            ]
            if not canonical:
                errors.append(f"expected a matching later APP_READY branch: {label}")
            for mapping in canonical:
                # A later municipality-wide review may make the operational
                # wording more specific and add condition branches.  The image
                # Pilot must recognize that forward transition without
                # requiring its historical text/reviewer to overwrite it.
                if (
                    mapping.get("mapping_status") != "APP_READY"
                    or mapping.get("evidence_scope") != "ITEM_SPECIFIC"
                    or mapping.get("branch_review_status") != "COMPLETE"
                    or any(not mapping.get(field) for field in ["条件", "前処理", "例外分別先", "item_evidence_locator"])
                ):
                    errors.append(f"later APP_READY branch is incomplete: {label}")
                if cov.get("branch_completeness_confirmed") != "TRUE":
                    errors.append(f"APP_READY coverage is not branch-complete: {label}")
        elif mid in lesson_ready_mids and cov.get("coverage_status") == "VERIFIED" and cov.get("branch_completeness_confirmed") == "TRUE":
            canonical = [
                m for m in pair_mappings
                if m.get("category_id") == row.get("category_id")
                and m.get("mapping_status") == "VERIFIED"
                and m.get("branch_review_status") == "COMPLETE"
                and m.get("条件") == row.get("condition")
                and m.get("前処理") == row.get("preparation")
                and m.get("例外分別先") == row.get("exception_destination")
                and m.get("item_evidence_source_id") == row.get("item_evidence_source_id")
            ]
            if len(canonical) != 1:
                errors.append(f"expected exactly one matching LESSON_READY_10 scoring branch: {label}")
            if not pair_mappings or any(
                mapping.get("mapping_status") != "VERIFIED"
                or mapping.get("evidence_scope") != "ITEM_SPECIFIC"
                or mapping.get("branch_review_status") != "COMPLETE"
                for mapping in pair_mappings
            ):
                errors.append(f"LESSON_READY_10 condition grid is incomplete: {label}")
        else:
            canonical = [
                m for m in pair_mappings
                if m.get("category_id") == row.get("category_id")
                and m.get("mapping_status") == "VERIFIED"
                and m.get("item_evidence_source_id") == row.get("item_evidence_source_id")
            ]
            if len(canonical) != 1:
                errors.append(f"expected exactly one matching VERIFIED canonical branch: {label}")
            else:
                mapping = canonical[0]
                field_pairs = [
                    ("条件", "condition"), ("前処理", "preparation"), ("例外分別先", "exception_destination"),
                    ("item_evidence_url", "item_evidence_url"),
                    ("item_evidence_locator", "item_evidence_locator"),
                    ("reviewed_date", "checked_date"), ("reviewed_by", "reviewer"),
                ]
                if any(mapping.get(left) != row.get(right) for left, right in field_pairs):
                    errors.append(f"pilot/canonical mapping detail mismatch: {label}")
                if mapping.get("evidence_scope") != "ITEM_SPECIFIC" or mapping.get("branch_review_status") != "INCOMPLETE":
                    errors.append(f"pilot branch must remain ITEM_SPECIFIC/INCOMPLETE until later review: {label}")
                if cov.get("coverage_status") != "VERIFIED" or cov.get("branch_completeness_confirmed") != "FALSE":
                    errors.append(f"coverage must be VERIFIED but branch-incomplete: {label}")
                if cov.get("item_evidence_source_id") != row.get("item_evidence_source_id") or cov.get("item_evidence_locator") != row.get("item_evidence_locator"):
                    errors.append(f"pilot/coverage evidence mismatch: {label}")
        if int(cov.get("mapping_branch_count") or -1) != len(pair_mappings):
            errors.append(f"coverage mapping_branch_count mismatch: {label}")
    return errors


def main() -> int:
    fields, pilot = read_csv(PILOT_PATH)
    errors = []
    if fields != EXPECTED_FIELDS:
        errors.append(f"pilot header mismatch: {fields}")
    errors.extend(validate_pilot_rows(pilot))
    if errors:
        print("ITEM_IMAGE_MAPPING_PILOT_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("ITEM_IMAGE_MAPPING_PILOT_VALIDATION_PASSED")
    coverage = {
        (row["municipality_id"], row["internal_item_id"]): row
        for row in rows(ROOT / "data/research/07_item_mapping_coverage.csv")
    }
    canonical_app_ready = sum(
        coverage[(row["municipality_id"], row["internal_item_id"])].get("coverage_status") == "APP_READY"
        for row in pilot
    )
    canonical_lesson_ready = sum(
        coverage[(row["municipality_id"], row["internal_item_id"])].get("coverage_status") == "VERIFIED"
        and coverage[(row["municipality_id"], row["internal_item_id"])].get("branch_completeness_confirmed") == "TRUE"
        for row in pilot
    )
    print(
        "pairs=80 historical_verified=76 unresolved=4 "
        f"canonical_app_ready={canonical_app_ready} canonical_lesson_ready={canonical_lesson_ready} "
        "municipalities=8 image_items=10"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
