#!/usr/bin/env python3
"""Shared structural and two-gate validation for Schema v1.2.2."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from schema_v12 import (
    CATEGORY_FIELDS, CHECK_STATUS, COUNT_STATUS, COVERAGE_FIELDS, MAPPING_FIELDS, MASTER,
    MUNICIPALITY_FIELDS, QA_FIELDS, RESEARCH, ROOT, SOURCE_FIELDS, compute_qa,
    counted_category_total, read_csv, ui_role_valid,
)

BOOL = {"TRUE", "FALSE", "CONDITIONAL", "UNKNOWN"}
CHANNEL = {"CURBSIDE", "BOOKED_PICKUP", "DROP_OFF", "DIRECT_HAUL", "RETAILER_OR_MAKER", "NOT_COLLECTED"}
LEVEL = {"PRIMARY", "SUBCATEGORY", "ALTERNATIVE", "EXCLUDED"}
RULE_STATUS = {"CURRENT", "PLANNED", "RETIRED"}
OFFICIAL_BASIS = {"MUNICIPAL_DOMAIN", "INTERMUNICIPAL_AUTHORITY_DOMAIN", "MUNICIPAL_LINKED_SERVICE"}
SAFETY = {"SAFE_REAL", "EMPTY_CLEAN_ONLY", "TEACHER_ONLY", "MOCK_ONLY"}
MAPPING_STATUS = {"INITIAL_REVIEW_REQUIRED", "VERIFIED", "APP_READY"}
EVIDENCE_SCOPE = {"NONE", "CATEGORY_LEVEL", "ITEM_SPECIFIC"}
BRANCH_REVIEW = {"UNREVIEWED", "INCOMPLETE", "COMPLETE"}
COVERAGE_STATUS = {"NOT_RESEARCHED", "MAPPED_INITIAL", "VERIFIED", "VERIFIED_NOT_APPLICABLE", "APP_READY"}
READY_COVERAGE = {"VERIFIED_NOT_APPLICABLE", "APP_READY"}
COMMON_ITEM_FIELDS = [
    "internal_item_id", "一般管理用名称", "教材表示名", "品目グループ", "確認ポイント",
    "handling_safety", "safety_note", "selection_status", "表示順",
]
REGISTRY_FIELDS = [
    "municipality_id", "host", "authority_type", "authority_name", "verification_url",
    "verified_date", "notes",
]
CORE_REQUIRED_CATEGORY_FIELDS = [
    "municipality_id", "category_id", "自治体正式名称", "category_group", "classification_level",
    "表示順", "代表品目", "入れてはいけない物", "条件外の扱い", "出す前の処理",
    "自治体収集外か", "source_id", "出典URL", "出典ページ・該当箇所", "確認日", "ui_role", "rule_status",
]


def iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))
    except (TypeError, ValueError):
        return False


def validate_headers(errors: list[str], path: Path, actual: list[str], expected: list[str]) -> None:
    if actual != expected:
        errors.append(f"header mismatch: {path.relative_to(ROOT)}")


def validate_optional_check(errors: list[str], row: dict[str, str], *, url_field: str, status_field: str,
                            evidence_field: str) -> None:
    mid, url, status, evidence = row.get("municipality_id", ""), row.get(url_field, ""), row.get(status_field, ""), row.get(evidence_field, "")
    if status not in CHECK_STATUS:
        errors.append(f"bad optional-resource check status: {mid} {status_field}={status}")
    elif status == "CHECKED_PRESENT":
        if not url.startswith("https://") or url not in evidence or "checked:" not in evidence:
            errors.append(f"CHECKED_PRESENT lacks URL/date evidence: {mid} {status_field}")
    elif status == "CHECKED_ABSENT":
        if url or not evidence or "https://" not in evidence or "checked:" not in evidence:
            errors.append(f"CHECKED_ABSENT lacks official search evidence: {mid} {status_field}")
    elif url or evidence:
        errors.append(f"NOT_CHECKED must not claim URL/evidence: {mid} {status_field}")


def validate_item_evidence(errors: list[str], row: dict[str, str], *, mid: str,
                           source_by_key: dict, context: str) -> None:
    source_id = row.get("item_evidence_source_id", "")
    url = row.get("item_evidence_url", "")
    locator = row.get("item_evidence_locator", "")
    source = source_by_key.get((mid, source_id))
    if not source_id or not url or not locator:
        errors.append(f"{context} lacks item-specific source/url/locator")
        return
    if source is None or source.get("official_verified") != "TRUE":
        errors.append(f"{context} item evidence is not an official dataset source")
    elif url != source.get("公式URL"):
        errors.append(f"{context} item evidence URL differs from source")


def validate_dataset(*, label: str, municipality_path: Path, category_path: Path, source_path: Path,
                     qa_path: Path, mapping_path: Path, coverage_path: Path, gate_mode: str | None = None):
    errors: list[str] = []
    gate_errors: list[str] = []
    try:
        municipality_fields, municipalities = read_csv(municipality_path)
        category_fields, categories = read_csv(category_path)
        source_fields, sources = read_csv(source_path)
        qa_fields, qa = read_csv(qa_path)
        mapping_fields, mappings = read_csv(mapping_path)
        coverage_fields, coverage = read_csv(coverage_path)
        master_fields, master = read_csv(MASTER / "01_municipalities_master.csv")
        registry_fields, registry = read_csv(MASTER / "02_official_domain_registry.csv")
        item_fields, items = read_csv(MASTER / "04_common_items_master.csv")
    except (FileNotFoundError, OSError) as exc:
        return [f"missing or unreadable file: {exc}"], [], {}

    for path, actual, expected in [
        (municipality_path, municipality_fields, MUNICIPALITY_FIELDS), (category_path, category_fields, CATEGORY_FIELDS),
        (source_path, source_fields, SOURCE_FIELDS), (qa_path, qa_fields, QA_FIELDS),
        (mapping_path, mapping_fields, MAPPING_FIELDS), (coverage_path, coverage_fields, COVERAGE_FIELDS),
        (MASTER / "02_official_domain_registry.csv", registry_fields, REGISTRY_FIELDS),
        (MASTER / "04_common_items_master.csv", item_fields, COMMON_ITEM_FIELDS),
    ]:
        validate_headers(errors, path, actual, expected)

    master_ids = [row.get("municipality_id", "") for row in master]
    if len(master) != 143 or len(set(master_ids)) != 143:
        errors.append(f"MASTER must contain 143 unique municipality IDs: rows={len(master)} unique={len(set(master_ids))}")
    if "municipality_id" not in master_fields:
        errors.append("MASTER is missing municipality_id")
    master_by_id = {row["municipality_id"]: row for row in master}
    mids = [row.get("municipality_id", "") for row in municipalities]
    mid_set = set(mids)
    if not mids or len(mids) != len(mid_set):
        errors.append("dataset has no municipalities or duplicate municipality_id")

    registry_map = {}
    for row in registry:
        key = (row.get("municipality_id", ""), row.get("host", "").lower())
        if key in registry_map:
            errors.append(f"duplicate official-domain registry key: {key}")
        registry_map[key] = row
        if row.get("authority_type") not in OFFICIAL_BASIS or not row.get("verification_url", "").startswith("https://"):
            errors.append(f"bad registry authority: {key}")
        if not iso_date(row.get("verified_date", "")):
            errors.append(f"bad registry verified_date: {key}")

    source_by_key = {}
    for row in sources:
        key = (row.get("municipality_id", ""), row.get("source_id", ""))
        if key in source_by_key:
            errors.append(f"duplicate source key: {key}")
        source_by_key[key] = row
        if key[0] not in mid_set:
            errors.append(f"source municipality outside dataset: {key}")
        url = row.get("公式URL", "")
        host = (urlparse(url).hostname or "").lower()
        authority = registry_map.get((key[0], host))
        if not url.startswith("https://") or authority is None:
            errors.append(f"source is not on registered official host: {key}")
        if row.get("official_verified") != "TRUE" or row.get("official_basis") not in OFFICIAL_BASIS:
            errors.append(f"source lacks official verification: {key}")
        elif authority and row.get("official_basis") != authority.get("authority_type"):
            errors.append(f"source official_basis disagrees with registry: {key}")
        if row.get("official_basis") == "MUNICIPAL_LINKED_SERVICE":
            link_host = (urlparse(row.get("official_linking_url", "")).hostname or "").lower()
            if registry_map.get((key[0], link_host), {}).get("authority_type") == "MUNICIPAL_LINKED_SERVICE":
                errors.append(f"linked service lacks municipal linking evidence: {key}")

    for row in municipalities:
        mid = row.get("municipality_id", "")
        if mid not in master_by_id:
            errors.append(f"unknown MASTER municipality_id: {mid}")
            continue
        for field in ("都道府県", "市町村", "実装区分"):
            if row.get(field) != master_by_id[mid].get(field):
                errors.append(f"municipality differs from MASTER: {mid} {field}")
        for field in ("自治体ごみトップURL", "分別ガイドURL"):
            if not row.get(field, "").startswith("https://"):
                errors.append(f"non-HTTPS required municipality URL: {mid} {field}")
        count_status = row.get("category_count_check_status", "")
        verified = row.get("category_count_verified", "")
        source_key = (mid, row.get("category_count_evidence_source_id", ""))
        if count_status not in COUNT_STATUS:
            errors.append(f"bad category count check status: {mid}")
        elif count_status == "NOT_REVIEWED":
            if verified != "FALSE" or any(row.get(f) for f in [
                "reviewed_category_count", "category_count_evidence_source_id",
                "category_count_reviewed_date", "category_count_reviewed_by",
            ]):
                errors.append(f"NOT_REVIEWED claims category-count evidence: {mid}")
        else:
            if verified != "TRUE" or not row.get("category_count_basis") or source_key not in source_by_key:
                errors.append(f"verified category count lacks evidence source/basis: {mid}")
            if not iso_date(row.get("category_count_reviewed_date", "")) or not row.get("category_count_reviewed_by"):
                errors.append(f"verified category count lacks reviewer/date: {mid}")
            official_count = row.get("official_category_count", "")
            reviewed_count = row.get("reviewed_category_count", "")
            if count_status == "OFFICIAL_COUNT_MATCHED" and not official_count.isdigit():
                errors.append(f"OFFICIAL_COUNT_MATCHED lacks numeric official count: {mid}")
            if count_status == "OFFICIAL_COUNT_MATCHED" and reviewed_count:
                errors.append(f"OFFICIAL_COUNT_MATCHED must not claim a manual reviewed count: {mid}")
            if count_status == "MANUAL_INDEX_REVIEW":
                if not reviewed_count.isdigit():
                    errors.append(f"MANUAL_INDEX_REVIEW lacks numeric reviewed count: {mid}")
                if official_count and not official_count.isdigit():
                    errors.append(f"MANUAL_INDEX_REVIEW has non-numeric optional official count: {mid}")
        validate_optional_check(errors, row, url_field="品目検索URL", status_field="search_service_check_status", evidence_field="search_service_check_evidence")
        validate_optional_check(errors, row, url_field="やさしい日本語URL", status_field="easy_japanese_check_status", evidence_field="easy_japanese_check_evidence")
        validate_optional_check(errors, row, url_field="多言語資料URL", status_field="multilingual_check_status", evidence_field="multilingual_check_evidence")

    category_by_key = {}
    category_counts = Counter()
    names_by_mid: dict[str, set[str]] = defaultdict(set)
    for row in categories:
        key = (row.get("municipality_id", ""), row.get("category_id", ""))
        if key in category_by_key:
            errors.append(f"duplicate category key: {key}")
        category_by_key[key] = row
        category_counts[key[0]] += 1
        if key[0] not in mid_set:
            errors.append(f"category municipality outside dataset: {key}")
        for field in CORE_REQUIRED_CATEGORY_FIELDS:
            if not row.get(field):
                errors.append(f"missing CORE category field: {key} {field}")
        name = row.get("自治体正式名称", "")
        if name in names_by_mid[key[0]]:
            errors.append(f"duplicate official category name: {key[0]} {name}")
        names_by_mid[key[0]].add(name)
        if row.get("classification_level") not in LEVEL:
            errors.append(f"bad classification_level: {key}")
        if row.get("collection_channel") and row.get("collection_channel") not in CHANNEL:
            errors.append(f"bad optional collection_channel: {key}")
        for field in ("粗大ごみ扱いか", "予約が必要か", "有料か", "自治体収集外か"):
            if row.get(field) and row.get(field) not in BOOL:
                errors.append(f"bad category enum: {key} {field}={row.get(field)}")
        if (key[0], row.get("source_id", "")) not in source_by_key:
            errors.append(f"missing category source: {key}")
        if registry_map.get((key[0], (urlparse(row.get("出典URL", "")).hostname or "").lower())) is None:
            errors.append(f"category citation not on registered host: {key}")
        if row.get("rule_status") not in RULE_STATUS:
            errors.append(f"bad rule_status: {key}")
        if row.get("rule_status") == "PLANNED" and not iso_date(row.get("effective_from", "")):
            errors.append(f"PLANNED row lacks effective_from: {key}")
        if row.get("rule_status") == "RETIRED" and not iso_date(row.get("effective_to", "")):
            errors.append(f"RETIRED row lacks effective_to: {key}")
        if not ui_role_valid(row):
            errors.append(f"ui_role violates explicit-role invariants: {key} {row.get('ui_role')}")
        if not iso_date(row.get("確認日", "")):
            errors.append(f"bad category confirmation date: {key}")
    for row in categories:
        parent = row.get("parent_category_id", "")
        if parent and (row["municipality_id"], parent) not in category_by_key:
            errors.append(f"missing parent category: {row['municipality_id']} {row['category_id']} -> {parent}")
    for municipality in municipalities:
        mid = municipality["municipality_id"]
        if not any(r["municipality_id"] == mid and r.get("rule_status") == "CURRENT" and r.get("ui_role") == "SORT_BUCKET" for r in categories):
            errors.append(f"no current learner SORT_BUCKET: {mid}")
        count_status = municipality.get("category_count_check_status")
        actual = counted_category_total(mid, categories)
        if count_status == "OFFICIAL_COUNT_MATCHED":
            official_count = municipality.get("official_category_count", "")
            if not official_count.isdigit() or int(official_count) != actual:
                errors.append(
                    f"official category count mismatch: {mid} "
                    f"stated={official_count} data={actual}"
                )
        elif count_status == "MANUAL_INDEX_REVIEW":
            reviewed_count = municipality.get("reviewed_category_count", "")
            if not reviewed_count.isdigit() or int(reviewed_count) != actual:
                errors.append(
                    f"manual reviewed category count mismatch: {mid} "
                    f"reviewed={reviewed_count} data={actual}"
                )
            official_count = municipality.get("official_category_count", "")
            if official_count and (not official_count.isdigit() or int(official_count) != actual):
                errors.append(
                    f"optional official category count mismatch: {mid} stated={official_count} data={actual}"
                )

    if len(items) != 40:
        errors.append(f"common item master must contain exactly 40 rows: {len(items)}")
    item_ids = {row.get("internal_item_id", "") for row in items}
    if len(item_ids) != len(items):
        errors.append("duplicate common item ID")
    for row in items:
        for field in COMMON_ITEM_FIELDS:
            if not row.get(field):
                errors.append(f"missing common item field: {row.get('internal_item_id')} {field}")
        if row.get("handling_safety") not in SAFETY:
            errors.append(f"bad handling_safety: {row.get('internal_item_id')}")

    mapping_ids, mapping_branch_keys = set(), set()
    mappings_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mappings:
        mapping_id = row.get("mapping_id", "")
        pair = (row.get("municipality_id", ""), row.get("internal_item_id", ""))
        branch_key = (*pair, row.get("branch_order", ""))
        if mapping_id in mapping_ids:
            errors.append(f"duplicate mapping_id: {mapping_id}")
        mapping_ids.add(mapping_id)
        if branch_key in mapping_branch_keys:
            errors.append(f"duplicate conditional mapping branch: {branch_key}")
        mapping_branch_keys.add(branch_key)
        mappings_by_pair[pair].append(row)
        if pair[0] not in mid_set or pair[1] not in item_ids:
            errors.append(f"mapping outside municipality/item set: {mapping_id}")
        category = category_by_key.get((pair[0], row.get("category_id", "")))
        if category is None:
            errors.append(f"mapping has unknown category: {mapping_id}")
        else:
            comparisons = {
                "分別区分正式名称": "自治体正式名称", "rule_status": "rule_status",
                "effective_from": "effective_from", "effective_to": "effective_to",
                "category_source_id": "source_id", "category_source_url": "出典URL",
                "category_source_locator": "出典ページ・該当箇所",
            }
            for mapping_field, category_field in comparisons.items():
                if row.get(mapping_field, "") != category.get(category_field, ""):
                    errors.append(f"mapping/category mismatch: {mapping_id} {mapping_field}")
        if not all(row.get(field) for field in ["条件", "前処理", "例外分別先"]):
            errors.append(f"mapping branch lacks condition/preparation/fallback: {mapping_id}")
        if row.get("mapping_status") not in MAPPING_STATUS or row.get("evidence_scope") not in EVIDENCE_SCOPE or row.get("branch_review_status") not in BRANCH_REVIEW:
            errors.append(f"bad mapping review enum: {mapping_id}")
        if row.get("mapping_status") == "VERIFIED":
            if row.get("evidence_scope") != "ITEM_SPECIFIC" or not iso_date(row.get("reviewed_date", "")) or not row.get("reviewed_by"):
                errors.append(f"VERIFIED mapping lacks review evidence: {mapping_id}")
            validate_item_evidence(
                errors, row, mid=pair[0], source_by_key=source_by_key,
                context=f"VERIFIED mapping {mapping_id}",
            )
        if row.get("mapping_status") == "APP_READY":
            if row.get("evidence_scope") != "ITEM_SPECIFIC" or row.get("branch_review_status") != "COMPLETE":
                errors.append(f"APP_READY mapping lacks item-specific complete branch review: {mapping_id}")
            if not iso_date(row.get("reviewed_date", "")) or not row.get("reviewed_by") or not row.get("自治体での品目表記") or row.get("自治体での品目表記") == "既存category代表品目から抽出":
                errors.append(f"APP_READY mapping lacks human/item evidence: {mapping_id}")
            validate_item_evidence(
                errors, row, mid=pair[0], source_by_key=source_by_key,
                context=f"APP_READY mapping {mapping_id}",
            )
        if row.get("mapping_status") == "INITIAL_REVIEW_REQUIRED" and any(
            row.get(field) for field in ["item_evidence_source_id", "item_evidence_url", "item_evidence_locator"]
        ):
            errors.append(f"initial mapping must not claim item evidence: {mapping_id}")
    for pair, branches in mappings_by_pair.items():
        try:
            actual = sorted(int(row.get("branch_order", "")) for row in branches)
        except ValueError:
            errors.append(f"non-numeric mapping branch: {pair}")
        else:
            if actual != list(range(1, len(branches) + 1)):
                errors.append(f"non-contiguous mapping branches: {pair} {actual}")

    coverage_by_pair = {}
    for row in coverage:
        pair = (row.get("municipality_id", ""), row.get("internal_item_id", ""))
        if pair in coverage_by_pair:
            errors.append(f"duplicate mapping coverage pair: {pair}")
        coverage_by_pair[pair] = row
        if pair[0] not in mid_set or pair[1] not in item_ids:
            errors.append(f"coverage outside municipality/item set: {pair}")
        status, branches = row.get("coverage_status", ""), mappings_by_pair.get(pair, [])
        if status not in COVERAGE_STATUS or row.get("evidence_scope") not in EVIDENCE_SCOPE or row.get("branch_completeness_confirmed") not in {"TRUE", "FALSE"}:
            errors.append(f"bad coverage enum: {pair}")
        try:
            stated_count = int(row.get("mapping_branch_count", ""))
        except ValueError:
            stated_count = -1
            errors.append(f"non-numeric coverage branch count: {pair}")
        if stated_count != len(branches):
            errors.append(f"coverage/mapping branch count mismatch: {pair} {stated_count}!={len(branches)}")
        if status == "NOT_RESEARCHED" and (branches or row.get("evidence_scope") != "NONE" or row.get("branch_completeness_confirmed") != "FALSE"):
            errors.append(f"NOT_RESEARCHED makes an evidence claim: {pair}")
        if status == "MAPPED_INITIAL" and (not branches or row.get("evidence_scope") != "CATEGORY_LEVEL" or row.get("branch_completeness_confirmed") != "FALSE"):
            errors.append(f"MAPPED_INITIAL is inconsistent: {pair}")
        if status in {"NOT_RESEARCHED", "MAPPED_INITIAL"} and any(
            row.get(field) for field in ["item_evidence_source_id", "item_evidence_url", "item_evidence_locator"]
        ):
            errors.append(f"unreviewed coverage must not claim item evidence: {pair}")
        if status in {"VERIFIED", "APP_READY", "VERIFIED_NOT_APPLICABLE"}:
            if row.get("evidence_scope") != "ITEM_SPECIFIC" or not iso_date(row.get("reviewed_date", "")) or not row.get("reviewed_by"):
                errors.append(f"reviewed coverage lacks item-specific official evidence: {pair}")
            validate_item_evidence(
                errors, row, mid=pair[0], source_by_key=source_by_key,
                context=f"reviewed coverage {pair}",
            )
        if status == "VERIFIED_NOT_APPLICABLE" and (branches or row.get("branch_completeness_confirmed") != "TRUE"):
            errors.append(f"VERIFIED_NOT_APPLICABLE must prove zero complete branches: {pair}")
        if status == "APP_READY":
            if not branches or row.get("branch_completeness_confirmed") != "TRUE" or any(branch.get("mapping_status") != "APP_READY" for branch in branches):
                errors.append(f"APP_READY coverage does not have complete APP_READY branches: {pair}")
    expected_pairs = {(mid, item_id) for mid in mid_set for item_id in item_ids}
    missing_pairs = expected_pairs - set(coverage_by_pair)
    extra_pairs = set(coverage_by_pair) - expected_pairs
    if missing_pairs or extra_pairs:
        errors.append(f"coverage must equal municipality x 40 items: missing={len(missing_pairs)} extra={len(extra_pairs)}")
    for mid in mid_set:
        municipality_rows = [coverage_by_pair.get((mid, item_id), {}) for item_id in item_ids]
        has_app_ready_claim = any(row.get("coverage_status") == "APP_READY" for row in municipality_rows) or any(
            row.get("municipality_id") == mid and row.get("mapping_status") == "APP_READY" for row in mappings
        )
        if has_app_ready_claim and not all(row.get("coverage_status") in READY_COVERAGE for row in municipality_rows):
            errors.append(f"partial APP_READY claim before all 40 items are ready: {mid}")
        for item_id in item_ids:
            pair = (mid, item_id)
            if any(row.get("mapping_status") == "APP_READY" for row in mappings_by_pair.get(pair, [])) and coverage_by_pair.get(pair, {}).get("coverage_status") != "APP_READY":
                errors.append(f"APP_READY mapping lacks APP_READY coverage: {pair}")

    qa_by_id = {row.get("municipality_id", ""): row for row in qa}
    if len(qa_by_id) != len(qa) or set(qa_by_id) != mid_set:
        errors.append("municipality and QA ID sets differ or QA IDs duplicate")
    recalculated = {row["municipality_id"]: row for row in compute_qa(municipalities, categories, sources, qa)}
    for mid, row in qa_by_id.items():
        if row.get("確認ステータス") not in {"QA_PASSED", "QA_REQUIRED"}:
            errors.append(f"bad QA status: {mid}")
        for field in ["検索サービス存在", "やさしい日本語存在", "多言語存在"]:
            if row.get(field) not in {"TRUE", "FALSE", "UNKNOWN"}:
                errors.append(f"bad optional-resource QA state: {mid} {field}")
        for field in QA_FIELDS:
            if field != "備考" and row.get(field) != recalculated.get(mid, {}).get(field):
                errors.append(f"stored QA differs from recomputation: {mid} {field}")
        municipality_status = next(
            (item.get("確認ステータス") for item in municipalities if item.get("municipality_id") == mid), None
        )
        if municipality_status != row.get("確認ステータス"):
            errors.append(
                f"municipality QA status mirror differs from QA log: {mid} "
                f"municipality={municipality_status} qa={row.get('確認ステータス')}"
            )

    if gate_mode in {"next_batch", "app_readiness"}:
        for mid in sorted(mid_set):
            if qa_by_id.get(mid, {}).get("確認ステータス") != "QA_PASSED":
                gate_errors.append(f"QA not passed: {mid}")
            if gate_mode == "app_readiness":
                not_ready = [item_id for item_id in item_ids if coverage_by_pair.get((mid, item_id), {}).get("coverage_status") not in READY_COVERAGE]
                if not_ready:
                    gate_errors.append(f"40-item mapping not APP_READY: {mid} remaining={len(not_ready)}")

    summary = {
        "municipalities": len(municipalities), "categories": len(categories), "sources": len(sources),
        "qa": len(qa), "mappings": len(mappings), "coverage": len(coverage),
        "qa_passed": sum(row.get("確認ステータス") == "QA_PASSED" for row in qa),
        "qa_required": sum(row.get("確認ステータス") == "QA_REQUIRED" for row in qa),
        "coverage_status": dict(Counter(row.get("coverage_status") for row in coverage)),
        "app_ready_municipalities": sum(all(coverage_by_pair.get((mid, item_id), {}).get("coverage_status") in READY_COVERAGE for item_id in item_ids) for mid in mid_set),
        "category_counts": dict(sorted(category_counts.items())),
    }
    return errors, gate_errors, summary


def print_result(label: str, errors: list[str], gate_errors: list[str], summary: dict,
                 gate_mode: str | None = None) -> int:
    if errors:
        print(f"{label}_STRUCTURAL_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"{label}_STRUCTURAL_VALIDATION_PASSED")
    print(" ".join(f"{key}={value}" for key, value in summary.items() if key != "category_counts"))
    if summary.get("category_counts"):
        print("category_counts=" + ",".join(f"{mid}:{count}" for mid, count in summary["category_counts"].items()))
    if gate_mode:
        gate_label = "NEXT_BATCH_GATE" if gate_mode == "next_batch" else "APP_READINESS_GATE"
        if gate_errors:
            print(f"{label}_{gate_label}_HOLD")
            for error in gate_errors:
                print(f"- {error}")
            return 2
        print(f"{label}_{gate_label}_PASSED")
    return 0
