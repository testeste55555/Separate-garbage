#!/usr/bin/env python3
"""Schema v1.2.1 migration and mapping reconciliation helpers.

Schema v1.2.1 keeps the researched category/source rows intact, records what has
not been checked, and separates structural validity from application readiness.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "master"
RESEARCH = ROOT / "data" / "research"
CHECKED = "2026-08-17"

CATEGORY_FIELDS = [
    "municipality_id", "category_id", "自治体正式名称", "category_group", "parent_category_id",
    "classification_level", "表示順", "collection_channel", "代表品目", "入れてはいけない物",
    "適用条件", "条件外の扱い", "出す前の処理", "袋・容器のルール", "サイズ・条件",
    "粗大ごみ扱いか", "予約が必要か", "有料か", "料金ルール", "自治体収集外か", "注意事項",
    "source_id", "出典URL", "出典ページ・該当箇所", "確認日", "ui_role", "rule_status",
    "effective_from", "effective_to",
]
SOURCE_FIELDS = [
    "municipality_id", "source_id", "資料名", "資料種別", "公式URL", "発行主体", "対象年度",
    "ページ更新日", "取得確認日", "使用した情報", "優先度", "現行性", "備考",
    "official_verified", "official_basis", "official_linking_url",
]
MUNICIPALITY_FIELDS = [
    "municipality_id", "都道府県", "市町村", "実装区分", "ごみ処理主体", "自治体ごみトップURL",
    "分別ガイドURL", "品目検索URL", "やさしい日本語URL", "多言語資料URL", "対象年度",
    "最終確認日", "確認ステータス", "備考", "official_category_count", "category_count_basis",
    "category_count_verified", "category_count_check_status", "category_count_evidence_source_id",
    "category_count_reviewed_date", "category_count_reviewed_by",
    "search_service_check_status", "search_service_check_evidence",
    "easy_japanese_check_status", "easy_japanese_check_evidence",
    "multilingual_check_status", "multilingual_check_evidence",
]
QA_FIELDS = [
    "municipality_id", "確認日", "ごみトップ", "現行ルール", "全分別区分", "正式名称", "代表品目",
    "前処理", "袋容器", "危険有害", "収集しない物", "公式出典", "参照整合性", "Schema検証",
    "category_count_verified", "rule_status検証", "ui_role検証", "検索サービス確認済み", "検索サービス存在",
    "やさしい日本語確認済み", "やさしい日本語存在", "多言語確認済み", "多言語存在", "粗大ごみ",
    "確認ステータス", "備考",
]
MAPPING_FIELDS = [
    "mapping_id", "municipality_id", "internal_item_id", "branch_order", "自治体での品目表記",
    "category_id", "分別区分正式名称", "条件", "前処理", "例外分別先", "自治体収集外",
    "rule_status", "effective_from", "effective_to", "source_id", "出典URL", "出典ページ・該当箇所",
    "確認日", "mapping_status", "evidence_scope", "branch_review_status", "reviewed_date", "reviewed_by", "備考",
]
COVERAGE_FIELDS = [
    "municipality_id", "internal_item_id", "coverage_status", "mapping_branch_count",
    "branch_completeness_confirmed", "evidence_scope", "source_id", "出典URL",
    "出典ページ・該当箇所", "reviewed_date", "reviewed_by", "notes",
]

CHECK_STATUS = {"CHECKED_PRESENT", "CHECKED_ABSENT", "NOT_CHECKED"}
COUNT_STATUS = {"OFFICIAL_COUNT_MATCHED", "MANUAL_INDEX_REVIEW", "NOT_REVIEWED"}
UI_ROLE = {"SORT_BUCKET", "REFERENCE_ONLY", "HIDDEN", "EXCLUDED_NOTICE"}
MANUAL_MAPPING_STATUS = {"VERIFIED", "APP_READY"}
MANUAL_COVERAGE_STATUS = {"VERIFIED", "VERIFIED_NOT_APPLICABLE", "APP_READY"}
BATCH_MIGRATION_INPUT_SUFFIXES = ("municipalities", "categories", "sources", "qa")
BATCH_REQUIRED_SUFFIXES = (*BATCH_MIGRATION_INPUT_SUFFIXES, "item_mapping", "item_coverage")

ITEM_PATTERNS = {
    "I001": ("name", r"ペットボトル|^PET$"), "I002": ("representative", r"キャップ"),
    "I003": ("representative", r"ラベル"), "I004": ("all", r"アルミ缶"),
    "I005": ("all", r"スチール缶"), "I006": ("name", r"(?:ガラス)?[びビ]ん|ビン類|びん類"),
    "I007": ("name", r"白色.*トレ"), "I008": ("representative", r"色付きトレイ|白色以外のトレイ|色柄トレイ"),
    "I009": ("representative", r"弁当.*容器"), "I010": ("representative", r"お菓子の袋|菓子袋|スナック菓子の袋"),
    "I011": ("representative", r"レジ袋"), "I012": ("representative", r"発泡スチロール"),
    "I013": ("name", r"新聞"), "I014": ("name", r"段ボール|ダンボール"),
    "I015": ("name", r"雑誌"), "I016": ("name", r"その他紙|雑紙"),
    "I017": ("name", r"紙パック"), "I018": ("representative", r"生ごみ"),
    "I019": ("representative", r"ティッシュ"), "I020": ("representative", r"紙おむつ|おむつ"),
    "I021": ("all", r"衣類|古着|布類"), "I022": ("representative", r"傘"),
    "I023": ("representative", r"陶磁器|せともの"), "I024": ("representative", r"ガラス製品"),
    "I025": ("all", r"割れたガラス|割れガラス"), "I026": ("all", r"刃物|包丁"),
    "I027": ("all", r"乾電池"), "I028": ("all", r"ボタン電池"),
    "I029": ("all", r"モバイルバッテリー"), "I030": ("all", r"蛍光管|蛍光灯"),
    "I031": ("all", r"電球"), "I032": ("all", r"スプレー缶"),
    "I033": ("all", r"ライター"), "I034": ("all", r"小型家電"),
    "I035": ("all", r"電池を外せない.*家電|充電式電池を外せない.*家電"),
    "I036": ("representative", r"布団"),
    "I037": ("all", r"家電4品目|家電４品目|テレビ.*エアコン.*冷蔵庫|テレビ・エアコン"),
    "I038": ("all", r"パソコン"), "I039": ("all", r"食用油"), "I040": ("all", r"剪定枝|枝木"),
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def load_registry() -> dict[tuple[str, str], dict[str, str]]:
    _, rows = read_csv(MASTER / "02_official_domain_registry.csv")
    return {(row["municipality_id"], row["host"].lower()): row for row in rows}


def migrate_sources(rows: list[dict[str, str]], registry: dict) -> list[dict[str, str]]:
    result = []
    for original in rows:
        row = dict(original)
        host = (urlparse(row.get("公式URL", "")).hostname or "").lower()
        authority = registry.get((row.get("municipality_id", ""), host))
        if authority:
            row["official_verified"] = "TRUE"
            row["official_basis"] = authority["authority_type"]
            row["official_linking_url"] = (
                authority["verification_url"] if authority["authority_type"] == "MUNICIPAL_LINKED_SERVICE" else ""
            )
        else:
            row["official_verified"] = "FALSE"
            row["official_basis"] = "UNVERIFIED"
            row["official_linking_url"] = ""
        result.append(row)
    return result


def japanese_date_to_iso(text: str) -> str:
    match = re.search(r"(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日", text or "")
    if not match:
        return ""
    year, month, day = (int(part) for part in match.groups())
    return f"{year:04d}-{month:02d}-{day:02d}"


def is_excluded_name(name: str) -> bool:
    return bool(re.search(r"収集.*(?:しない|できない)|処理できない|ステーションに出せない", name or ""))


def legacy_ui_role(row: dict[str, str]) -> str:
    """Provide a one-time legacy default; ui_role is explicit thereafter."""
    if row.get("rule_status") in {"PLANNED", "RETIRED"}:
        return "HIDDEN"
    if row.get("自治体収集外か") == "TRUE" or row.get("classification_level") == "EXCLUDED":
        return "EXCLUDED_NOTICE"
    if row.get("classification_level") == "ALTERNATIVE":
        return "REFERENCE_ONLY"
    return "SORT_BUCKET"


def migrate_categories(rows: list[dict[str, str]], sources: list[dict[str, str]]) -> list[dict[str, str]]:
    source_currency = {(r["municipality_id"], r["source_id"]): r.get("現行性", "") for r in sources}
    result = []
    for original in rows:
        row = dict(original)
        if not row.get("category_group"):
            row["category_group"] = row.get("自治体正式名称", "")
        if is_excluded_name(row.get("自治体正式名称", "")):
            row["自治体収集外か"] = "TRUE"
            if row.get("classification_level") == "PRIMARY":
                row["classification_level"] = "EXCLUDED"
        status = row.get("rule_status", "")
        currency = source_currency.get((row.get("municipality_id", ""), row.get("source_id", "")), "")
        if status not in {"CURRENT", "PLANNED", "RETIRED"}:
            status = "PLANNED" if "施行予定" in currency else "RETIRED" if "終了" in currency else "CURRENT"
        row["rule_status"] = status
        if status == "PLANNED" and not row.get("effective_from"):
            row["effective_from"] = japanese_date_to_iso(" ".join([row.get("注意事項", ""), row.get("適用条件", "")]))
        row.setdefault("effective_from", "")
        row.setdefault("effective_to", "")
        if row.get("ui_role") not in UI_ROLE:
            row["ui_role"] = legacy_ui_role(row)
        if status in {"PLANNED", "RETIRED"}:
            row["ui_role"] = "HIDDEN"
        result.append(row)
    return result


def select_count_source(mid: str, count: str, sources: list[dict[str, str]]) -> str:
    candidates = [row for row in sources if row.get("municipality_id") == mid and row.get("official_verified") == "TRUE"]
    for row in candidates:
        haystack = " ".join([row.get("資料名", ""), row.get("使用した情報", ""), row.get("備考", "")])
        if re.search(rf"(?<!\d){re.escape(count)}(?:区分|種類|分別)(?!\d)", haystack):
            return row.get("source_id", "")
    return ""


def migrate_check(url: str, status: str, evidence: str, checked_date: str) -> tuple[str, str]:
    if status in CHECK_STATUS:
        return status, evidence
    if url:
        return "CHECKED_PRESENT", f"URL:{url}; checked:{checked_date or CHECKED}"
    return "NOT_CHECKED", ""


def migrate_municipalities(rows: list[dict[str, str]], sources: list[dict[str, str]]) -> list[dict[str, str]]:
    result = []
    for original in rows:
        row = dict(original)
        mid = row.get("municipality_id", "")
        count = row.get("official_category_count", "")
        basis = row.get("category_count_basis", "")
        status = row.get("category_count_check_status", "")
        source_id = row.get("category_count_evidence_source_id", "")
        if status not in COUNT_STATUS:
            source_id = select_count_source(mid, count, sources) if count.isdigit() else ""
            if count.isdigit() and source_id and basis:
                status = "OFFICIAL_COUNT_MATCHED"
                row["category_count_reviewed_date"] = row.get("最終確認日") or CHECKED
                row["category_count_reviewed_by"] = "AUTOMATED_OFFICIAL_COUNT_MATCH"
            else:
                status = "NOT_REVIEWED"
        row["category_count_check_status"] = status
        row["category_count_evidence_source_id"] = source_id if status != "NOT_REVIEWED" else ""
        if status == "NOT_REVIEWED":
            row["category_count_verified"] = "FALSE"
            row["category_count_reviewed_date"] = ""
            row["category_count_reviewed_by"] = ""
        else:
            row["category_count_verified"] = "TRUE"
        for url_field, status_field, evidence_field in [
            ("品目検索URL", "search_service_check_status", "search_service_check_evidence"),
            ("やさしい日本語URL", "easy_japanese_check_status", "easy_japanese_check_evidence"),
            ("多言語資料URL", "multilingual_check_status", "multilingual_check_evidence"),
        ]:
            new_status, new_evidence = migrate_check(
                row.get(url_field, ""), row.get(status_field, ""), row.get(evidence_field, ""), row.get("最終確認日", "")
            )
            row[status_field], row[evidence_field] = new_status, new_evidence
        result.append(row)
    return result


def ui_role_valid(row: dict[str, str]) -> bool:
    role = row.get("ui_role", "")
    if role not in UI_ROLE:
        return False
    if row.get("rule_status") != "CURRENT" and role != "HIDDEN":
        return False
    if role == "SORT_BUCKET" and row.get("自治体収集外か") == "TRUE":
        return False
    if role == "EXCLUDED_NOTICE" and row.get("自治体収集外か") != "TRUE":
        return False
    return True


def check_to_qa(status: str) -> tuple[str, str]:
    if status == "CHECKED_PRESENT":
        return "TRUE", "TRUE"
    if status == "CHECKED_ABSENT":
        return "TRUE", "FALSE"
    return "FALSE", "UNKNOWN"


def compute_qa(municipalities, categories, sources, old_qa=None):
    old_by_id = {row["municipality_id"]: row for row in (old_qa or [])}
    source_by_key = {(row["municipality_id"], row["source_id"]): row for row in sources}
    all_category_keys = [(row["municipality_id"], row["category_id"]) for row in categories]
    rows = []
    for municipality in municipalities:
        mid = municipality["municipality_id"]
        cats = [row for row in categories if row["municipality_id"] == mid]
        srcs = [row for row in sources if row["municipality_id"] == mid]
        current = [row for row in cats if row.get("rule_status") == "CURRENT"]
        referenced = [source_by_key.get((mid, row.get("source_id", ""))) for row in cats]
        ref_ok = all(item is not None for item in referenced)
        official_ok = ref_ok and all(item.get("official_verified") == "TRUE" for item in referenced if item)
        dangerous = any(re.search(r"危険|有害|電池|蛍光|水銀|スプレー缶|ライター", " ".join(row.values())) for row in cats)
        excluded = any(row.get("ui_role") == "EXCLUDED_NOTICE" for row in cats)
        bulky = any(row.get("粗大ごみ扱いか") in {"TRUE", "CONDITIONAL"} or "粗大" in row.get("自治体正式名称", "") for row in cats)
        status_ok = all(
            row.get("rule_status") in {"CURRENT", "PLANNED", "RETIRED"}
            and (row.get("rule_status") != "PLANNED" or bool(row.get("effective_from")))
            and (row.get("rule_status") != "RETIRED" or bool(row.get("effective_to"))) for row in cats
        )
        ui_ok = all(ui_role_valid(row) for row in cats)
        core_fields = [
            "municipality_id", "category_id", "自治体正式名称", "category_group", "classification_level",
            "表示順", "代表品目", "入れてはいけない物", "条件外の扱い", "出す前の処理",
            "自治体収集外か", "source_id", "出典URL", "出典ページ・該当箇所", "確認日", "ui_role", "rule_status",
        ]
        core_ok = bool(cats) and all(all(row.get(field, "") for field in core_fields) for row in cats)
        schema_ok = core_ok and status_ok and ui_ok and official_ok and len(set(all_category_keys)) == len(all_category_keys)
        search_checked, search_exists = check_to_qa(municipality.get("search_service_check_status", ""))
        easy_checked, easy_exists = check_to_qa(municipality.get("easy_japanese_check_status", ""))
        multi_checked, multi_exists = check_to_qa(municipality.get("multilingual_check_status", ""))
        count_ok = municipality.get("category_count_verified") == "TRUE" and municipality.get("category_count_check_status") in {
            "OFFICIAL_COUNT_MATCHED", "MANUAL_INDEX_REVIEW"
        }
        row = {
            "municipality_id": mid, "確認日": CHECKED,
            "ごみトップ": "TRUE" if municipality.get("自治体ごみトップURL", "").startswith("https://") else "FALSE",
            "現行ルール": "TRUE" if current and any(src.get("現行性") in {"現行", "現行案内中"} for src in srcs) else "FALSE",
            "全分別区分": "TRUE" if cats and count_ok else "FALSE",
            "正式名称": "TRUE" if cats and len({r.get("自治体正式名称") for r in cats}) == len(cats) else "FALSE",
            "代表品目": "TRUE" if current and all(cat.get("代表品目") for cat in current) else "FALSE",
            "前処理": "TRUE" if current and all(cat.get("出す前の処理") for cat in current) else "FALSE",
            "袋容器": "TRUE" if current and all(cat.get("袋・容器のルール") for cat in current) else "FALSE",
            "危険有害": "TRUE" if dangerous else "FALSE", "収集しない物": "TRUE" if excluded else "FALSE",
            "公式出典": "TRUE" if official_ok else "FALSE", "参照整合性": "TRUE" if ref_ok else "FALSE",
            "Schema検証": "TRUE" if schema_ok else "FALSE", "category_count_verified": "TRUE" if count_ok else "FALSE",
            "rule_status検証": "TRUE" if status_ok else "FALSE", "ui_role検証": "TRUE" if ui_ok else "FALSE",
            "検索サービス確認済み": search_checked, "検索サービス存在": search_exists,
            "やさしい日本語確認済み": easy_checked, "やさしい日本語存在": easy_exists,
            "多言語確認済み": multi_checked, "多言語存在": multi_exists,
            "粗大ごみ": "TRUE" if bulky else "NOT_APPLICABLE",
            "備考": old_by_id.get(mid, {}).get("備考", "Schema v1.2で機械再計算"),
        }
        required = [
            "ごみトップ", "現行ルール", "全分別区分", "正式名称", "代表品目", "前処理", "危険有害",
            "収集しない物", "公式出典", "参照整合性", "Schema検証", "category_count_verified",
            "rule_status検証", "ui_role検証",
        ]
        row["確認ステータス"] = "QA_PASSED" if all(row[field] == "TRUE" for field in required) else "QA_REQUIRED"
        rows.append(row)
    return rows


def sync_municipality_qa_status(municipalities, qa):
    """Make municipalities.確認ステータス a read-only mirror of computed QA."""
    qa_status = {row["municipality_id"]: row["確認ステータス"] for row in qa}
    for municipality in municipalities:
        municipality["確認ステータス"] = qa_status.get(municipality["municipality_id"], "QA_REQUIRED")
    return municipalities


def candidate_initial_mappings(categories: list[dict[str, str]]) -> list[dict[str, str]]:
    by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for category in categories:
        for item_id, (scope, pattern) in ITEM_PATTERNS.items():
            texts = {
                "name": category.get("自治体正式名称", ""),
                "representative": category.get("代表品目", ""),
                "all": " ".join(category.get(field, "") for field in ["自治体正式名称", "代表品目", "入れてはいけない物", "出す前の処理", "注意事項"]),
            }
            if re.search(pattern, texts[scope]):
                by_pair[(category["municipality_id"], item_id)].append(category)
    result = []
    for (mid, item_id), cats in sorted(by_pair.items()):
        cats.sort(key=lambda row: (row.get("rule_status") != "CURRENT", int(row.get("表示順") or 0)))
        for branch, category in enumerate(cats, 1):
            result.append({
                "mapping_id": f"MAP-{mid}-{item_id}-{category['category_id']}", "municipality_id": mid,
                "internal_item_id": item_id, "branch_order": str(branch),
                "自治体での品目表記": "既存category代表品目から抽出", "category_id": category["category_id"],
                "分別区分正式名称": category["自治体正式名称"], "条件": category.get("適用条件") or "要品目別確認",
                "前処理": category.get("出す前の処理", ""), "例外分別先": category.get("条件外の扱い", ""),
                "自治体収集外": category.get("自治体収集外か", "FALSE"), "rule_status": category["rule_status"],
                "effective_from": category.get("effective_from", ""), "effective_to": category.get("effective_to", ""),
                "source_id": category["source_id"], "出典URL": category["出典URL"],
                "出典ページ・該当箇所": category["出典ページ・該当箇所"], "確認日": category["確認日"],
                "mapping_status": "INITIAL_REVIEW_REQUIRED", "evidence_scope": "CATEGORY_LEVEL",
                "branch_review_status": "UNREVIEWED", "reviewed_date": "", "reviewed_by": "",
                "備考": "区分レベルデータから機械抽出。品目別公式根拠と条件枝の確認前はAPP_READYにしない。",
            })
    return result


def reconcile_mappings(categories: list[dict[str, str]], existing: list[dict[str, str]]) -> list[dict[str, str]]:
    category_keys = {(r["municipality_id"], r["category_id"]) for r in categories}
    existing_by_id = {r.get("mapping_id", ""): r for r in existing if r.get("mapping_id")}
    existing_by_semantic_key: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in existing:
        existing_by_semantic_key[(
            row.get("municipality_id", ""), row.get("internal_item_id", ""), row.get("category_id", "")
        )].append(row)
    result: list[dict[str, str]] = []
    used_mapping_ids: set[str] = set()
    reserved_mapping_ids = set(existing_by_id)
    for generated in candidate_initial_mappings(categories):
        semantic_key = (generated["municipality_id"], generated["internal_item_id"], generated["category_id"])
        previous = existing_by_id.get(generated["mapping_id"])
        if previous and (
            previous.get("municipality_id"), previous.get("internal_item_id"), previous.get("category_id")
        ) != semantic_key:
            previous = None
        if previous is None:
            candidates = [
                row for row in existing_by_semantic_key.get(semantic_key, [])
                if row.get("mapping_id") not in used_mapping_ids
            ]
            candidates.sort(key=lambda row: (
                row.get("mapping_status") in MANUAL_MAPPING_STATUS,
                int(row.get("branch_order") or 0), row.get("mapping_id", ""),
            ))
            previous = candidates[0] if candidates else None
        if previous:
            generated["mapping_id"] = previous.get("mapping_id") or generated["mapping_id"]
            used_mapping_ids.add(generated["mapping_id"])
            if previous.get("mapping_status") in MANUAL_MAPPING_STATUS:
                generated = {**generated, **previous}
            elif previous.get("備考"):
                generated["備考"] = previous["備考"]
        elif generated["mapping_id"] in reserved_mapping_ids or generated["mapping_id"] in used_mapping_ids:
            base_id = generated["mapping_id"]
            suffix = 2
            while f"{base_id}-AUTO-{suffix:02d}" in reserved_mapping_ids | used_mapping_ids:
                suffix += 1
            generated["mapping_id"] = f"{base_id}-AUTO-{suffix:02d}"
        result.append(generated)
        used_mapping_ids.add(generated["mapping_id"])
    for previous in existing:
        mapping_id = previous.get("mapping_id", "")
        category_key = (previous.get("municipality_id", ""), previous.get("category_id", ""))
        if mapping_id not in used_mapping_ids and previous.get("mapping_status") in MANUAL_MAPPING_STATUS and category_key in category_keys:
            result.append(previous)
            used_mapping_ids.add(mapping_id)
    by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in result:
        by_pair[(row.get("municipality_id", ""), row.get("internal_item_id", ""))].append(row)
    normalized = []
    for pair in sorted(by_pair):
        branches = sorted(by_pair[pair], key=lambda row: (int(row.get("branch_order") or 0), row.get("mapping_id", "")))
        for branch_order, row in enumerate(branches, 1):
            row["branch_order"] = str(branch_order)
            normalized.append(row)
    return normalized


def build_coverage(municipalities, items, mappings, existing=None):
    existing_by_pair = {(r.get("municipality_id", ""), r.get("internal_item_id", "")): r for r in (existing or [])}
    by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mappings:
        by_pair[(row["municipality_id"], row["internal_item_id"])].append(row)
    rows = []
    for municipality in municipalities:
        for item in items:
            pair = (municipality["municipality_id"], item["internal_item_id"])
            branches = by_pair.get(pair, [])
            previous = existing_by_pair.get(pair)
            if previous and previous.get("coverage_status") in MANUAL_COVERAGE_STATUS:
                row = dict(previous)
            elif branches:
                first = branches[0]
                row = {
                    "municipality_id": pair[0], "internal_item_id": pair[1], "coverage_status": "MAPPED_INITIAL",
                    "mapping_branch_count": str(len(branches)), "branch_completeness_confirmed": "FALSE",
                    "evidence_scope": "CATEGORY_LEVEL", "source_id": first.get("source_id", ""),
                    "出典URL": first.get("出典URL", ""), "出典ページ・該当箇所": first.get("出典ページ・該当箇所", ""),
                    "reviewed_date": "", "reviewed_by": "", "notes": "機械抽出。品目別調査と条件枝レビューは未完了。",
                }
            else:
                row = {
                    "municipality_id": pair[0], "internal_item_id": pair[1], "coverage_status": "NOT_RESEARCHED",
                    "mapping_branch_count": "0", "branch_completeness_confirmed": "FALSE", "evidence_scope": "NONE",
                    "source_id": "", "出典URL": "", "出典ページ・該当箇所": "", "reviewed_date": "", "reviewed_by": "",
                    "notes": "未調査。不存在を意味しない。",
                }
            rows.append(row)
    return rows


def migrate_bundle(municipality_path: Path, category_path: Path, source_path: Path, qa_path: Path,
                   mapping_path: Path, coverage_path: Path, registry=None) -> dict[str, int]:
    registry = registry or load_registry()
    _, municipalities = read_csv(municipality_path)
    _, categories = read_csv(category_path)
    _, sources = read_csv(source_path)
    _, old_qa = read_csv(qa_path) if qa_path.exists() else ([], [])
    _, existing_mappings = read_csv(mapping_path) if mapping_path.exists() else ([], [])
    _, existing_coverage = read_csv(coverage_path) if coverage_path.exists() else ([], [])
    _, items = read_csv(MASTER / "04_common_items_master.csv")
    sources = migrate_sources(sources, registry)
    categories = migrate_categories(categories, sources)
    municipalities = migrate_municipalities(municipalities, sources)
    mappings = reconcile_mappings(categories, existing_mappings)
    coverage = build_coverage(municipalities, items, mappings, existing_coverage)
    qa = compute_qa(municipalities, categories, sources, old_qa)
    municipalities = sync_municipality_qa_status(municipalities, qa)
    write_csv(municipality_path, MUNICIPALITY_FIELDS, municipalities)
    write_csv(category_path, CATEGORY_FIELDS, categories)
    write_csv(source_path, SOURCE_FIELDS, sources)
    write_csv(qa_path, QA_FIELDS, qa)
    write_csv(mapping_path, MAPPING_FIELDS, mappings)
    write_csv(coverage_path, COVERAGE_FIELDS, coverage)
    return {"municipalities": len(municipalities), "categories": len(categories), "sources": len(sources), "qa": len(qa), "mappings": len(mappings), "coverage": len(coverage)}


def migrate_batch_dir(batch_dir: Path) -> dict[str, int]:
    prefix = batch_dir.name + "_"
    return migrate_bundle(
        batch_dir / f"{prefix}municipalities.csv", batch_dir / f"{prefix}categories.csv",
        batch_dir / f"{prefix}sources.csv", batch_dir / f"{prefix}qa.csv",
        batch_dir / f"{prefix}item_mapping.csv", batch_dir / f"{prefix}item_coverage.csv",
    )


def batch_dirs_with_files(suffixes: tuple[str, ...], root: Path | None = None) -> list[Path]:
    root = root or RESEARCH / "batches"
    if not root.exists():
        return []
    return [path for path in sorted(root.iterdir()) if path.is_dir() and all(
        (path / f"{path.name}_{suffix}.csv").exists() for suffix in suffixes
    )]


def batch_dirs_for_migration(root: Path | None = None) -> list[Path]:
    """Return candidate bundles with the four research inputs needed to generate v1.2 artifacts."""
    return batch_dirs_with_files(BATCH_MIGRATION_INPUT_SUFFIXES, root)


def completed_batch_dirs(root: Path | None = None) -> list[Path]:
    """Return completed bundles; the definition is exactly the six Workflow artifacts."""
    return batch_dirs_with_files(BATCH_REQUIRED_SUFFIXES, root)
