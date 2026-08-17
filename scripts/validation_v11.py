#!/usr/bin/env python3
"""Shared Schema v1.1 validation for Pilot, batches, and canonical research."""

from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from migrate_schema_v11 import (
    CATEGORY_FIELDS,
    MAPPING_FIELDS,
    MUNICIPALITY_FIELDS,
    QA_FIELDS,
    SOURCE_FIELDS,
    compute_qa,
)


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "master"
RESEARCH = ROOT / "data" / "research"

BOOL = {"TRUE", "FALSE", "CONDITIONAL", "UNKNOWN"}
CHANNEL = {"CURBSIDE", "BOOKED_PICKUP", "DROP_OFF", "DIRECT_HAUL", "RETAILER_OR_MAKER", "NOT_COLLECTED"}
LEVEL = {"PRIMARY", "SUBCATEGORY", "ALTERNATIVE", "EXCLUDED"}
RULE_STATUS = {"CURRENT", "PLANNED", "RETIRED"}
UI_ROLE = {"SORT_BUCKET", "REFERENCE_ONLY", "HIDDEN", "EXCLUDED_NOTICE"}
OFFICIAL_BASIS = {"MUNICIPAL_DOMAIN", "INTERMUNICIPAL_AUTHORITY_DOMAIN", "MUNICIPAL_LINKED_SERVICE"}
SAFETY = {"SAFE_REAL", "EMPTY_CLEAN_ONLY", "TEACHER_ONLY", "MOCK_ONLY"}
QA_TRISTATE = {"TRUE", "FALSE", "NOT_APPLICABLE"}
MAPPING_STATUS = {"INITIAL_REVIEW_REQUIRED", "VERIFIED", "APP_READY"}

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
    "袋・容器のルール", "自治体収集外か", "source_id", "出典URL", "出典ページ・該当箇所", "確認日",
    "ui_role", "rule_status",
]
REFERENCE_CATEGORY_FIELDS = {
    "collection_channel", "粗大ごみ扱いか", "予約が必要か", "有料か", "料金ルール",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))
    except ValueError:
        return False


def expected_ui_role(row: dict[str, str]) -> str:
    if row["rule_status"] in {"PLANNED", "RETIRED"}:
        return "HIDDEN"
    if row["自治体収集外か"] == "TRUE" or row["classification_level"] == "EXCLUDED" or row["collection_channel"] == "NOT_COLLECTED":
        return "EXCLUDED_NOTICE"
    if row["collection_channel"] in {"BOOKED_PICKUP", "DROP_OFF", "DIRECT_HAUL", "RETAILER_OR_MAKER"} or row["classification_level"] == "ALTERNATIVE":
        return "REFERENCE_ONLY"
    return "SORT_BUCKET"


def validate_headers(errors: list[str], path: Path, actual: list[str], expected: list[str]) -> None:
    if actual != expected:
        errors.append(f"header mismatch: {path.relative_to(ROOT)}")


def validate_dataset(
    *,
    label: str,
    municipality_path: Path,
    category_path: Path,
    source_path: Path,
    qa_path: Path,
    expected_municipality_count: int | None = None,
) -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []
    try:
        municipality_fields, municipalities = read_csv(municipality_path)
        category_fields, categories = read_csv(category_path)
        source_fields, sources = read_csv(source_path)
        qa_fields, qa = read_csv(qa_path)
        master_fields, master = read_csv(MASTER / "01_municipalities_master.csv")
        registry_fields, registry = read_csv(MASTER / "02_official_domain_registry.csv")
        item_fields, items = read_csv(MASTER / "04_common_items_master.csv")
        mapping_fields, all_mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    except (FileNotFoundError, OSError) as exc:
        return [f"missing or unreadable file: {exc}"], {}

    validate_headers(errors, municipality_path, municipality_fields, MUNICIPALITY_FIELDS)
    validate_headers(errors, category_path, category_fields, CATEGORY_FIELDS)
    validate_headers(errors, source_path, source_fields, SOURCE_FIELDS)
    validate_headers(errors, qa_path, qa_fields, QA_FIELDS)
    validate_headers(errors, MASTER / "02_official_domain_registry.csv", registry_fields, REGISTRY_FIELDS)
    validate_headers(errors, MASTER / "04_common_items_master.csv", item_fields, COMMON_ITEM_FIELDS)
    validate_headers(errors, RESEARCH / "05_item_mapping_master.csv", mapping_fields, MAPPING_FIELDS)

    master_ids = [row.get("municipality_id", "") for row in master]
    if len(master) != 143 or len(set(master_ids)) != 143:
        errors.append(f"MASTER must contain 143 unique municipality_id values: rows={len(master)} unique={len(set(master_ids))}")
    if len({(row.get("都道府県", ""), row.get("市町村", "")) for row in master}) != 143:
        errors.append("MASTER contains duplicate municipality names")
    if "municipality_id" not in master_fields:
        errors.append("MASTER is missing municipality_id")
    master_by_id = {row["municipality_id"]: row for row in master}

    mids = [row.get("municipality_id", "") for row in municipalities]
    mid_set = set(mids)
    if expected_municipality_count is not None and len(municipalities) != expected_municipality_count:
        errors.append(f"{label} municipality count differs: {len(municipalities)} != {expected_municipality_count}")
    if len(mids) != len(mid_set):
        errors.append("duplicate municipality_id")
    for row in municipalities:
        mid = row.get("municipality_id", "")
        if mid not in master_by_id:
            errors.append(f"unknown MASTER municipality_id: {mid}")
            continue
        for field in ("都道府県", "市町村", "実装区分"):
            if row.get(field) != master_by_id[mid].get(field):
                errors.append(f"municipality differs from MASTER: {mid} {field}")
        if row.get("category_count_verified") != "TRUE":
            errors.append(f"category count is not verified: {mid}")
        if not row.get("category_count_basis"):
            errors.append(f"missing category_count_basis: {mid}")
        for field in ("自治体ごみトップURL", "分別ガイドURL"):
            if not row.get(field, "").startswith("https://"):
                errors.append(f"non-HTTPS required municipality URL: {mid} {field}")

    registry_map: dict[tuple[str, str], dict[str, str]] = {}
    for row in registry:
        key = (row.get("municipality_id", ""), row.get("host", "").lower())
        if key in registry_map:
            errors.append(f"duplicate official-domain registry key: {key}")
        registry_map[key] = row
        if row.get("municipality_id") not in master_by_id:
            errors.append(f"registry municipality not in MASTER: {row.get('municipality_id')}")
        if row.get("authority_type") not in OFFICIAL_BASIS:
            errors.append(f"bad registry authority_type: {key}")
        if not row.get("verification_url", "").startswith("https://"):
            errors.append(f"bad registry verification URL: {key}")
        if not iso_date(row.get("verified_date", "")):
            errors.append(f"bad registry verified_date: {key}")

    source_keys: set[tuple[str, str]] = set()
    source_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for row in sources:
        mid, sid = row.get("municipality_id", ""), row.get("source_id", "")
        key = (mid, sid)
        if key in source_keys:
            errors.append(f"duplicate source key: {key}")
        source_keys.add(key)
        source_by_key[key] = row
        if mid not in mid_set:
            errors.append(f"source municipality outside dataset: {key}")
        url = row.get("公式URL", "")
        host = (urlparse(url).hostname or "").lower()
        authority = registry_map.get((mid, host))
        if not url.startswith("https://"):
            errors.append(f"non-HTTPS source: {key}")
        if row.get("official_verified") != "TRUE":
            errors.append(f"source not officially verified: {key}")
        if row.get("official_basis") not in OFFICIAL_BASIS:
            errors.append(f"bad official_basis: {key}")
        if authority is None:
            errors.append(f"source host absent from official-domain registry: {key} {host}")
        elif row.get("official_basis") != authority.get("authority_type"):
            errors.append(f"official_basis disagrees with registry: {key}")
        if row.get("official_basis") == "MUNICIPAL_LINKED_SERVICE":
            link = row.get("official_linking_url", "")
            link_host = (urlparse(link).hostname or "").lower()
            link_authority = registry_map.get((mid, link_host))
            if not link.startswith("https://"):
                errors.append(f"linked external service lacks official linking URL: {key}")
            elif link_authority is None or link_authority.get("authority_type") == "MUNICIPAL_LINKED_SERVICE":
                errors.append(f"external service linking URL is not an official authority host: {key}")
        elif row.get("official_linking_url"):
            errors.append(f"direct official source should not need official_linking_url: {key}")
        if row.get("現行性") not in {"現行", "現行案内中", "施行予定", "終了"}:
            errors.append(f"bad source currency: {key} {row.get('現行性')}")

    category_keys: set[tuple[str, str]] = set()
    category_by_key: dict[tuple[str, str], dict[str, str]] = {}
    names_by_mid: dict[str, set[str]] = {}
    category_counts: Counter[str] = Counter()
    for row in categories:
        mid, cid = row.get("municipality_id", ""), row.get("category_id", "")
        key = (mid, cid)
        if key in category_keys:
            errors.append(f"duplicate category key: {key}")
        category_keys.add(key)
        category_by_key[key] = row
        category_counts[mid] += 1
        if mid not in mid_set:
            errors.append(f"category municipality outside dataset: {key}")
        for field in CORE_REQUIRED_CATEGORY_FIELDS:
            if not row.get(field):
                errors.append(f"missing category field: {key} {field}")
        names = names_by_mid.setdefault(mid, set())
        if row.get("自治体正式名称") in names:
            errors.append(f"duplicate official category name: {mid} {row.get('自治体正式名称')}")
        names.add(row.get("自治体正式名称", ""))
        if row.get("classification_level") not in LEVEL:
            errors.append(f"bad classification_level: {key}")
        # REFERENCE fields are validated when present, but are deliberately
        # not CORE-required for future municipality research.
        if row.get("collection_channel") and row.get("collection_channel") not in CHANNEL:
            errors.append(f"bad collection_channel: {key}")
        for field in ("粗大ごみ扱いか", "予約が必要か", "有料か", "自治体収集外か"):
            if row.get(field) and row.get(field) not in BOOL:
                errors.append(f"bad boolean enum: {key} {field}={row.get(field)}")
        source = source_by_key.get((mid, row.get("source_id", "")))
        if source is None:
            errors.append(f"missing source reference: {key} {row.get('source_id')}")
        category_host = (urlparse(row.get("出典URL", "")).hostname or "").lower()
        if registry_map.get((mid, category_host)) is None:
            errors.append(f"category citation host absent from official-domain registry: {key} {category_host}")
        if row.get("rule_status") not in RULE_STATUS:
            errors.append(f"bad rule_status: {key}")
        if row.get("rule_status") == "PLANNED" and not iso_date(row.get("effective_from", "")):
            errors.append(f"PLANNED row lacks effective_from: {key}")
        if row.get("rule_status") == "RETIRED" and not iso_date(row.get("effective_to", "")):
            errors.append(f"RETIRED row lacks effective_to: {key}")
        if row.get("ui_role") not in UI_ROLE:
            errors.append(f"bad ui_role: {key}")
        elif row.get("ui_role") != expected_ui_role(row):
            errors.append(f"non-deterministic ui_role: {key} {row.get('ui_role')} != {expected_ui_role(row)}")
        if row.get("rule_status") != "CURRENT" and row.get("ui_role") == "SORT_BUCKET":
            errors.append(f"non-current rule leaks into current learner buckets: {key}")
        if not row.get("出典URL", "").startswith("https://"):
            errors.append(f"non-HTTPS category source: {key}")
        if not iso_date(row.get("確認日", "")):
            errors.append(f"bad category confirmation date: {key}")

    for row in categories:
        parent = row.get("parent_category_id", "")
        if parent and (row["municipality_id"], parent) not in category_keys:
            errors.append(f"missing parent category: {row['municipality_id']} {row['category_id']} -> {parent}")

    for mid in mid_set:
        learner_buckets = [row for row in categories if row["municipality_id"] == mid and row["rule_status"] == "CURRENT" and row["ui_role"] == "SORT_BUCKET"]
        if not learner_buckets:
            errors.append(f"no current learner SORT_BUCKET: {mid}")
        municipality = next(row for row in municipalities if row["municipality_id"] == mid)
        stated_count = municipality.get("official_category_count", "")
        if stated_count:
            if not stated_count.isdigit():
                errors.append(f"official_category_count is not an integer: {mid}")
            else:
                current_official = sum(
                    row["municipality_id"] == mid and row["rule_status"] == "CURRENT" and row["ui_role"] != "EXCLUDED_NOTICE"
                    for row in categories
                )
                if int(stated_count) != current_official:
                    errors.append(f"official category count mismatch: {mid} stated={stated_count} data={current_official}")

    if not 30 <= len(items) <= 50:
        errors.append(f"common item master must contain 30-50 rows: {len(items)}")
    item_ids: set[str] = set()
    for row in items:
        item_id = row.get("internal_item_id", "")
        if item_id in item_ids:
            errors.append(f"duplicate common item id: {item_id}")
        item_ids.add(item_id)
        for field in COMMON_ITEM_FIELDS:
            if not row.get(field):
                errors.append(f"missing common item field: {item_id} {field}")
        if row.get("handling_safety") not in SAFETY:
            errors.append(f"bad handling_safety: {item_id}")
        if not row.get("safety_note"):
            errors.append(f"missing safety_note: {item_id}")

    mappings = [row for row in all_mappings if row.get("municipality_id") in mid_set]
    mapping_ids: set[str] = set()
    branch_keys: set[tuple[str, str, str]] = set()
    mappings_by_pair: Counter[tuple[str, str]] = Counter()
    for row in mappings:
        mapping_id = row.get("mapping_id", "")
        pair = (row.get("municipality_id", ""), row.get("internal_item_id", ""))
        branch_key = (*pair, row.get("branch_order", ""))
        mappings_by_pair[pair] += 1
        if mapping_id in mapping_ids:
            errors.append(f"duplicate mapping_id: {mapping_id}")
        mapping_ids.add(mapping_id)
        if branch_key in branch_keys:
            errors.append(f"duplicate conditional mapping branch: {branch_key}")
        branch_keys.add(branch_key)
        if row.get("internal_item_id") not in item_ids:
            errors.append(f"mapping has unknown common item: {mapping_id}")
        category = category_by_key.get((row.get("municipality_id", ""), row.get("category_id", "")))
        if category is None:
            errors.append(f"mapping has unknown category: {mapping_id}")
            continue
        if row.get("分別区分正式名称") != category.get("自治体正式名称"):
            errors.append(f"mapping category name mismatch: {mapping_id}")
        for field in ("rule_status", "effective_from", "effective_to", "source_id", "出典URL", "出典ページ・該当箇所"):
            if row.get(field) != category.get(field):
                errors.append(f"mapping/category mismatch: {mapping_id} {field}")
        if not row.get("条件") or not row.get("前処理") or not row.get("例外分別先"):
            errors.append(f"mapping branch lacks condition/preparation/fallback: {mapping_id}")
        if row.get("自治体収集外") not in BOOL:
            errors.append(f"bad mapping collection enum: {mapping_id}")
        if row.get("mapping_status") not in MAPPING_STATUS:
            errors.append(f"bad mapping_status: {mapping_id}")
    for pair, count in mappings_by_pair.items():
        actual = sorted(int(row["branch_order"]) for row in mappings if (row["municipality_id"], row["internal_item_id"]) == pair)
        if actual != list(range(1, count + 1)):
            errors.append(f"non-contiguous mapping branches: {pair} {actual}")
    for mid in mid_set:
        if not any(row["municipality_id"] == mid for row in mappings):
            errors.append(f"municipality has no initial common-item mapping: {mid}")

    qa_map = {row.get("municipality_id", ""): row for row in qa}
    if len(qa_map) != len(qa):
        errors.append("duplicate QA municipality_id")
    if set(qa_map) != mid_set:
        errors.append("municipality and QA id sets differ")
    recalculated = {row["municipality_id"]: row for row in compute_qa(municipalities, categories, sources, qa)}
    optional_exists = {"検索サービス存在", "やさしい日本語存在", "多言語存在"}
    required_true = {
        "ごみトップ", "現行ルール", "全分別区分", "正式名称", "代表品目", "前処理", "袋容器",
        "危険有害", "収集しない物", "公式出典", "参照整合性", "Schema検証",
        "category_count_verified", "rule_status検証", "ui_role検証", "検索サービス確認済み",
        "やさしい日本語確認済み", "多言語確認済み",
    }
    for mid, row in qa_map.items():
        for field in required_true:
            if row.get(field) != "TRUE":
                errors.append(f"required QA check is not TRUE: {mid} {field}={row.get(field)}")
            if row.get(field) == "UNKNOWN":
                errors.append(f"required QA check remains UNKNOWN: {mid} {field}")
        for field in optional_exists:
            if row.get(field) not in {"TRUE", "FALSE"}:
                errors.append(f"optional existence must be explicit TRUE/FALSE: {mid} {field}")
        if row.get("粗大ごみ") not in QA_TRISTATE:
            errors.append(f"bad bulky-waste QA enum: {mid}")
        if row.get("確認ステータス") != "QA_PASSED":
            errors.append(f"QA not passed: {mid}")
        expected = recalculated.get(mid)
        if expected:
            for field in QA_FIELDS:
                if field != "備考" and row.get(field) != expected.get(field):
                    errors.append(f"stored QA differs from mechanical recomputation: {mid} {field}")

    summary: dict[str, object] = {
        "municipalities": len(municipalities),
        "categories": len(categories),
        "sources": len(sources),
        "qa": len(qa),
        "mappings": len(mappings),
        "current": sum(row.get("rule_status") == "CURRENT" for row in categories),
        "planned": sum(row.get("rule_status") == "PLANNED" for row in categories),
        "ui_roles": dict(Counter(row.get("ui_role") for row in categories)),
        "category_counts": dict(sorted(category_counts.items())),
    }
    return errors, summary


def print_result(label: str, errors: list[str], summary: dict[str, object]) -> int:
    if errors:
        print(f"{label}_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"{label}_VALIDATION_PASSED")
    print(" ".join(f"{key}={value}" for key, value in summary.items() if key != "category_counts"))
    print("category_counts=" + ",".join(f"{mid}:{count}" for mid, count in summary["category_counts"].items()))
    return 0
