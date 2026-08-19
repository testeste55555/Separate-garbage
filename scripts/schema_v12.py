#!/usr/bin/env python3
"""Schema v1.2.3 migration and mapping reconciliation helpers.

Schema v1.2.3 adds dated QA derivation, multi-source category-review evidence,
and official-leaf counting independent from learner-facing UI projection.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "master"
RESEARCH = ROOT / "data" / "research"

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
    "最終確認日", "確認ステータス", "備考", "official_category_count", "reviewed_category_count",
    "category_count_basis",
    "category_count_verified", "category_count_check_status", "category_count_review_id",
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
    "rule_status", "effective_from", "effective_to",
    "category_source_id", "category_source_url", "category_source_locator",
    "item_evidence_source_id", "item_evidence_url", "item_evidence_locator",
    "確認日", "mapping_status", "evidence_scope", "branch_review_status", "reviewed_date", "reviewed_by", "備考",
]
COVERAGE_FIELDS = [
    "municipality_id", "internal_item_id", "coverage_status", "mapping_branch_count",
    "branch_completeness_confirmed", "evidence_scope", "item_evidence_source_id",
    "item_evidence_url", "item_evidence_locator", "reviewed_date", "reviewed_by", "notes",
]
CATEGORY_REVIEW_EVIDENCE_FIELDS = [
    "review_evidence_id", "review_id", "municipality_id", "source_id", "locator",
    "evidence_role", "notes",
]

CHECK_STATUS = {"CHECKED_PRESENT", "CHECKED_ABSENT", "NOT_CHECKED"}
COUNT_STATUS = {"OFFICIAL_COUNT_MATCHED", "MANUAL_INDEX_REVIEW", "NOT_REVIEWED"}
REVIEW_EVIDENCE_ROLE = {"OFFICIAL_TOTAL", "PRIMARY_INDEX", "SUPPLEMENTAL_INDEX"}
UI_ROLE = {"SORT_BUCKET", "REFERENCE_ONLY", "HIDDEN", "EXCLUDED_NOTICE"}
MANUAL_MAPPING_STATUS = {"VERIFIED", "APP_READY"}
MANUAL_COVERAGE_STATUS = {"VERIFIED", "VERIFIED_NOT_APPLICABLE", "APP_READY"}
BATCH_MIGRATION_INPUT_SUFFIXES = ("municipalities", "categories", "sources", "qa")
BATCH_REQUIRED_SUFFIXES = (
    *BATCH_MIGRATION_INPUT_SUFFIXES, "item_mapping", "item_coverage", "category_review_evidence",
)

POSITIVE_EVIDENCE_FIELDS = {
    "name": ("自治体正式名称",),
    "representative": ("代表品目",),
    "positive": ("自治体正式名称", "代表品目"),
}
NEGATIVE_CONTEXT_FIELDS = ("入れてはいけない物", "条件外の扱い", "出す前の処理", "注意事項")

ITEM_PATTERNS = {
    "I001": ("name", r"ペットボトル|^PET$"), "I002": ("representative", r"キャップ"),
    "I003": ("representative", r"ラベル"), "I004": ("positive", r"アルミ缶"),
    "I005": ("positive", r"スチール缶"), "I006": ("name", r"(?:ガラス)?[びビ]ん|ビン類|びん類"),
    "I007": ("name", r"白色.*トレ"),
    "I008": ("representative", r"色付きトレ(?:イ|ー)|白色以外のトレ(?:イ|ー)|色柄(?:食品)?トレ(?:イ|ー)"),
    "I009": ("representative", r"弁当.*容器"), "I010": ("representative", r"お菓子の袋|菓子袋|スナック菓子の袋"),
    "I011": ("representative", r"レジ袋"), "I012": ("representative", r"発泡スチロール"),
    "I013": ("name", r"新聞"), "I014": ("name", r"段ボール|ダンボール"),
    "I015": ("name", r"雑誌"), "I016": ("name", r"その他紙|雑紙"),
    "I017": ("name", r"紙パック"), "I018": ("representative", r"生ごみ"),
    "I019": ("representative", r"ティッシュ"), "I020": ("representative", r"紙おむつ|おむつ"),
    "I021": ("positive", r"衣類|古着|布類"), "I022": ("representative", r"傘"),
    "I023": ("representative", r"陶磁器|せともの"), "I024": ("representative", r"ガラス製品"),
    "I025": ("positive", r"割れたガラス|割れガラス"), "I026": ("positive", r"刃物|包丁"),
    "I027": ("positive", r"乾電池"), "I028": ("positive", r"ボタン電池"),
    "I029": ("positive", r"モバイルバッテリー"), "I030": ("positive", r"蛍光管|蛍光灯"),
    "I031": ("positive", r"電球"), "I032": ("positive", r"スプレー缶"),
    "I033": ("positive", r"ライター"), "I034": ("positive", r"小型家電"),
    "I035": ("positive", r"(?:充電式?電池|充電池|電池)を外せない.*家電"),
    "I036": ("representative", r"布団"),
    "I037": ("positive", r"家電4品目|家電４品目|テレビ.*エアコン.*冷蔵庫|テレビ・エアコン"),
    "I038": ("positive", r"パソコン"),
    "I039": ("positive", r"(?:使用済み|廃)食用油|家庭(?:用)?の?植物性食用油"),
    "I040": ("positive", r"剪定枝|枝木"),
}

# Longer compounds that contain another common-item term but do not denote that
# item.  Matches overlapping these spans are ignored; a second, independent
# positive mention in the same category still remains eligible.
ITEM_COLLISION_PATTERNS = {
    "I007": r"白色以外(?:の)?(?:食品)?トレ(?:イ|ー)",
    "I021": r"衣類乾燥機",
    "I030": r"(?:LED|ＬＥＤ)\s*蛍光(?:管|灯)|電球型蛍光灯",
    "I034": r"(?:充電式?電池|充電池|電池)を外せない.*?家電",
    "I038": r"パソコン周辺機器",
    "I039": r"食用油(?:用)?(?:ボトル|容器)",
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
        return "CHECKED_PRESENT", f"URL:{url}; checked:{checked_date}"
    return "NOT_CHECKED", ""


def current_official_leaf_rows(mid: str, categories: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return official current leaf divisions, independent from UI projection parents."""
    current = [
        row for row in categories
        if row.get("municipality_id") == mid
        and row.get("rule_status") == "CURRENT"
        and row.get("ui_role") != "EXCLUDED_NOTICE"
    ]
    current_parent_ids = {row.get("parent_category_id") for row in current if row.get("parent_category_id")}
    return [row for row in current if row.get("category_id") not in current_parent_ids]


def counted_category_total(mid: str, categories: list[dict[str, str]]) -> int:
    return len(current_official_leaf_rows(mid, categories))


def stable_category_review_id(mid: str) -> str:
    return f"CR-{mid}-CATEGORY-COVERAGE"


def migrate_category_review_evidence(municipalities: list[dict[str, str]],
                                     existing: list[dict[str, str]]) -> list[dict[str, str]]:
    """Migrate legacy single-source evidence without inventing additional sources."""
    by_id = {row.get("review_evidence_id", ""): dict(row) for row in existing if row.get("review_evidence_id")}
    for municipality in municipalities:
        mid = municipality.get("municipality_id", "")
        status = municipality.get("category_count_check_status", "")
        if status == "NOT_REVIEWED":
            continue
        review_id = municipality.get("category_count_review_id") or stable_category_review_id(mid)
        municipality["category_count_review_id"] = review_id
        legacy_source = municipality.get("category_count_evidence_source_id", "")
        if legacy_source and not any(
            row.get("review_id") == review_id and row.get("source_id") == legacy_source
            for row in by_id.values()
        ):
            evidence_id = f"CRE-{mid}-{legacy_source}"
            by_id[evidence_id] = {
                "review_evidence_id": evidence_id,
                "review_id": review_id,
                "municipality_id": mid,
                "source_id": legacy_source,
                "locator": municipality.get("category_count_basis", ""),
                "evidence_role": "OFFICIAL_TOTAL" if status == "OFFICIAL_COUNT_MATCHED" else "PRIMARY_INDEX",
                "notes": "Schema v1.2.3 migration from legacy single-source category review evidence.",
            }
    valid_review_ids = {
        row.get("category_count_review_id") for row in municipalities
        if row.get("category_count_check_status") != "NOT_REVIEWED"
    }
    return sorted(
        (row for row in by_id.values() if row.get("review_id") in valid_review_ids),
        key=lambda row: (row.get("municipality_id", ""), row.get("review_id", ""), row.get("review_evidence_id", "")),
    )


def category_review_rows(municipality: dict[str, str],
                         review_evidence: list[dict[str, str]]) -> list[dict[str, str]]:
    review_id = municipality.get("category_count_review_id", "")
    mid = municipality.get("municipality_id", "")
    return [
        row for row in review_evidence
        if row.get("review_id") == review_id and row.get("municipality_id") == mid
    ]


def category_count_review_valid(municipality: dict[str, str], categories: list[dict[str, str]],
                                sources: list[dict[str, str]],
                                review_evidence: list[dict[str, str]]) -> bool:
    """Validate count evidence without requiring an official total for manual index review."""
    mid = municipality.get("municipality_id", "")
    status = municipality.get("category_count_check_status", "")
    if status not in {"OFFICIAL_COUNT_MATCHED", "MANUAL_INDEX_REVIEW"}:
        return False
    if municipality.get("category_count_verified") != "TRUE":
        return False
    evidence_rows = category_review_rows(municipality, review_evidence)
    source_by_key = {(row.get("municipality_id"), row.get("source_id")): row for row in sources}
    if not municipality.get("category_count_review_id") or not evidence_rows:
        return False
    if any(
        row.get("evidence_role") not in REVIEW_EVIDENCE_ROLE
        or not row.get("locator")
        or source_by_key.get((mid, row.get("source_id")), {}).get("official_verified") != "TRUE"
        for row in evidence_rows
    ):
        return False
    if not all(municipality.get(field) for field in [
        "category_count_basis", "category_count_reviewed_date", "category_count_reviewed_by",
    ]):
        return False
    actual = counted_category_total(mid, categories)
    official_count = municipality.get("official_category_count", "")
    reviewed_count = municipality.get("reviewed_category_count", "")
    if status == "OFFICIAL_COUNT_MATCHED":
        return (
            official_count.isdigit() and int(official_count) == actual
            and any(row.get("evidence_role") == "OFFICIAL_TOTAL" for row in evidence_rows)
        )
    if not reviewed_count.isdigit() or int(reviewed_count) != actual:
        return False
    return (
        any(row.get("evidence_role") == "PRIMARY_INDEX" for row in evidence_rows)
        and (not official_count or (official_count.isdigit() and int(official_count) == actual))
    )


def migrate_municipalities(rows: list[dict[str, str]], sources: list[dict[str, str]],
                           categories: list[dict[str, str]]) -> list[dict[str, str]]:
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
                row["category_count_reviewed_date"] = row.get("最終確認日", "")
                row["category_count_reviewed_by"] = "AUTOMATED_OFFICIAL_COUNT_MATCH"
            else:
                status = "NOT_REVIEWED"
        row["category_count_check_status"] = status
        row["category_count_review_id"] = (
            row.get("category_count_review_id") or stable_category_review_id(mid)
        ) if status != "NOT_REVIEWED" else ""
        if status == "NOT_REVIEWED":
            row["category_count_verified"] = "FALSE"
            row["reviewed_category_count"] = ""
            row["category_count_reviewed_date"] = ""
            row["category_count_reviewed_by"] = ""
        else:
            row["category_count_verified"] = "TRUE"
            if status == "MANUAL_INDEX_REVIEW" and not row.get("reviewed_category_count"):
                row["reviewed_category_count"] = str(counted_category_total(mid, categories))
            elif status == "OFFICIAL_COUNT_MATCHED":
                row["reviewed_category_count"] = ""
            else:
                row.setdefault("reviewed_category_count", "")
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


def valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""))
    except (TypeError, ValueError):
        return False


def latest_qa_evidence_date(municipality: dict[str, str], categories: list[dict[str, str]],
                            sources: list[dict[str, str]]) -> str:
    """Derive QA date from the newest persisted evidence date for one municipality."""
    mid = municipality.get("municipality_id", "")
    values = [municipality.get("最終確認日", ""), municipality.get("category_count_reviewed_date", "")]
    values.extend(
        row.get("確認日", "") for row in categories if row.get("municipality_id") == mid
    )
    values.extend(
        row.get("取得確認日", "") for row in sources if row.get("municipality_id") == mid
    )
    dates = [value for value in values if valid_iso_date(value)]
    return max(dates) if dates else ""


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


def compute_qa(municipalities, categories, sources, review_evidence, old_qa=None):
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
        count_ok = category_count_review_valid(municipality, categories, sources, review_evidence)
        row = {
            "municipality_id": mid, "確認日": latest_qa_evidence_date(municipality, categories, sources),
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
            "備考": old_by_id.get(mid, {}).get("備考", "Schema v1.2.3で機械再計算"),
        }
        # Category QA asks whether the resident-facing sorting system is faithfully
        # represented. A municipality does not need a *separate* hazardous-waste or
        # not-collected bucket to pass this gate; those two QA columns remain
        # informational. Safety/excluded-route correctness is verified item-by-item
        # before APP_READY (batteries, spray cans, appliances, PCs, etc.).
        required = [
            "ごみトップ", "現行ルール", "全分別区分", "正式名称", "代表品目", "前処理",
            "公式出典", "参照整合性", "Schema検証", "category_count_verified",
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


def item_pattern_matches(item_id: str, category: dict[str, str]) -> bool:
    """Match only positive category evidence and ignore known compound collisions."""
    scope, pattern = ITEM_PATTERNS[item_id]
    text = " ".join(category.get(field, "") for field in POSITIVE_EVIDENCE_FIELDS[scope])
    collision_pattern = ITEM_COLLISION_PATTERNS.get(item_id)
    collision_spans = [
        match.span() for match in re.finditer(collision_pattern, text)
    ] if collision_pattern else []
    for match in re.finditer(pattern, text):
        start, end = match.span()
        if not any(start < collision_end and collision_start < end for collision_start, collision_end in collision_spans):
            return True
    return False


def candidate_initial_mappings(categories: list[dict[str, str]]) -> list[dict[str, str]]:
    by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    current_parent_ids = {
        (row.get("municipality_id", ""), row.get("parent_category_id", ""))
        for row in categories
        if row.get("rule_status") == "CURRENT" and row.get("parent_category_id")
    }
    for category in categories:
        if (category.get("municipality_id", ""), category.get("category_id", "")) in current_parent_ids:
            continue
        for item_id in ITEM_PATTERNS:
            if item_pattern_matches(item_id, category):
                by_pair[(category["municipality_id"], item_id)].append(category)
    result = []
    for (mid, item_id), cats in sorted(by_pair.items()):
        cats.sort(key=lambda row: (row.get("rule_status") != "CURRENT", int(row.get("表示順") or 0)))
        for branch, category in enumerate(cats, 1):
            result.append({
                "mapping_id": f"MAP-{mid}-{item_id}-{category['category_id']}", "municipality_id": mid,
                "internal_item_id": item_id, "branch_order": str(branch),
                "自治体での品目表記": "category正式名称・代表品目から機械抽出", "category_id": category["category_id"],
                "分別区分正式名称": category["自治体正式名称"], "条件": category.get("適用条件") or "要品目別確認",
                "前処理": category.get("出す前の処理", ""), "例外分別先": category.get("条件外の扱い", ""),
                "自治体収集外": category.get("自治体収集外か", "FALSE"), "rule_status": category["rule_status"],
                "effective_from": category.get("effective_from", ""), "effective_to": category.get("effective_to", ""),
                "category_source_id": category["source_id"], "category_source_url": category["出典URL"],
                "category_source_locator": category["出典ページ・該当箇所"],
                "item_evidence_source_id": "", "item_evidence_url": "", "item_evidence_locator": "",
                "確認日": category["確認日"],
                "mapping_status": "INITIAL_REVIEW_REQUIRED", "evidence_scope": "CATEGORY_LEVEL",
                "branch_review_status": "UNREVIEWED", "reviewed_date": "", "reviewed_by": "",
                "備考": "Positive evidence（category正式名称・代表品目）から機械抽出。品目別公式根拠と条件枝の確認前はAPP_READYにしない。",
            })
    return result


def migrate_mapping_evidence(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Split legacy category citations from item-specific evidence without inventing evidence."""
    result = []
    for original in rows:
        row = dict(original)
        legacy_source = row.get("source_id", "")
        legacy_url = row.get("出典URL", "")
        legacy_locator = row.get("出典ページ・該当箇所", "")
        row["category_source_id"] = row.get("category_source_id") or legacy_source
        row["category_source_url"] = row.get("category_source_url") or legacy_url
        row["category_source_locator"] = row.get("category_source_locator") or legacy_locator
        if row.get("evidence_scope") == "ITEM_SPECIFIC" and row.get("mapping_status") in MANUAL_MAPPING_STATUS:
            row["item_evidence_source_id"] = row.get("item_evidence_source_id") or legacy_source
            row["item_evidence_url"] = row.get("item_evidence_url") or legacy_url
            row["item_evidence_locator"] = row.get("item_evidence_locator") or legacy_locator
        else:
            row.setdefault("item_evidence_source_id", "")
            row.setdefault("item_evidence_url", "")
            row.setdefault("item_evidence_locator", "")
        result.append(row)
    return result


def migrate_coverage_evidence(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Move reviewed legacy coverage citations into explicit item-evidence fields."""
    result = []
    for original in rows:
        row = dict(original)
        if row.get("evidence_scope") == "ITEM_SPECIFIC" and row.get("coverage_status") in MANUAL_COVERAGE_STATUS:
            row["item_evidence_source_id"] = row.get("item_evidence_source_id") or row.get("source_id", "")
            row["item_evidence_url"] = row.get("item_evidence_url") or row.get("出典URL", "")
            row["item_evidence_locator"] = row.get("item_evidence_locator") or row.get("出典ページ・該当箇所", "")
        else:
            row.setdefault("item_evidence_source_id", "")
            row.setdefault("item_evidence_url", "")
            row.setdefault("item_evidence_locator", "")
        result.append(row)
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
                row = {
                    "municipality_id": pair[0], "internal_item_id": pair[1], "coverage_status": "MAPPED_INITIAL",
                    "mapping_branch_count": str(len(branches)), "branch_completeness_confirmed": "FALSE",
                    "evidence_scope": "CATEGORY_LEVEL", "item_evidence_source_id": "",
                    "item_evidence_url": "", "item_evidence_locator": "",
                    "reviewed_date": "", "reviewed_by": "", "notes": "機械抽出。品目別調査と条件枝レビューは未完了。",
                }
            else:
                row = {
                    "municipality_id": pair[0], "internal_item_id": pair[1], "coverage_status": "NOT_RESEARCHED",
                    "mapping_branch_count": "0", "branch_completeness_confirmed": "FALSE", "evidence_scope": "NONE",
                    "item_evidence_source_id": "", "item_evidence_url": "", "item_evidence_locator": "",
                    "reviewed_date": "", "reviewed_by": "",
                    "notes": "未調査。不存在を意味しない。",
                }
            rows.append(row)
    return rows


def migrate_bundle(municipality_path: Path, category_path: Path, source_path: Path, qa_path: Path,
                   mapping_path: Path, coverage_path: Path, review_evidence_path: Path,
                   registry=None) -> dict[str, int]:
    registry = registry or load_registry()
    _, municipalities = read_csv(municipality_path)
    _, categories = read_csv(category_path)
    _, sources = read_csv(source_path)
    _, old_qa = read_csv(qa_path) if qa_path.exists() else ([], [])
    _, existing_mappings = read_csv(mapping_path) if mapping_path.exists() else ([], [])
    _, existing_coverage = read_csv(coverage_path) if coverage_path.exists() else ([], [])
    _, existing_review_evidence = read_csv(review_evidence_path) if review_evidence_path.exists() else ([], [])
    _, items = read_csv(MASTER / "04_common_items_master.csv")
    sources = migrate_sources(sources, registry)
    categories = migrate_categories(categories, sources)
    municipalities = migrate_municipalities(municipalities, sources, categories)
    review_evidence = migrate_category_review_evidence(municipalities, existing_review_evidence)
    existing_mappings = migrate_mapping_evidence(existing_mappings)
    existing_coverage = migrate_coverage_evidence(existing_coverage)
    mappings = reconcile_mappings(categories, existing_mappings)
    coverage = build_coverage(municipalities, items, mappings, existing_coverage)
    qa = compute_qa(municipalities, categories, sources, review_evidence, old_qa)
    municipalities = sync_municipality_qa_status(municipalities, qa)
    write_csv(municipality_path, MUNICIPALITY_FIELDS, municipalities)
    write_csv(category_path, CATEGORY_FIELDS, categories)
    write_csv(source_path, SOURCE_FIELDS, sources)
    write_csv(qa_path, QA_FIELDS, qa)
    write_csv(mapping_path, MAPPING_FIELDS, mappings)
    write_csv(coverage_path, COVERAGE_FIELDS, coverage)
    write_csv(review_evidence_path, CATEGORY_REVIEW_EVIDENCE_FIELDS, review_evidence)
    return {
        "municipalities": len(municipalities), "categories": len(categories), "sources": len(sources),
        "qa": len(qa), "mappings": len(mappings), "coverage": len(coverage),
        "review_evidence": len(review_evidence),
    }


def migrate_batch_dir(batch_dir: Path) -> dict[str, int]:
    prefix = batch_dir.name + "_"
    return migrate_bundle(
        batch_dir / f"{prefix}municipalities.csv", batch_dir / f"{prefix}categories.csv",
        batch_dir / f"{prefix}sources.csv", batch_dir / f"{prefix}qa.csv",
        batch_dir / f"{prefix}item_mapping.csv", batch_dir / f"{prefix}item_coverage.csv",
        batch_dir / f"{prefix}category_review_evidence.csv",
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
    """Return completed bundles; the definition is exactly the seven Workflow artifacts."""
    return batch_dirs_with_files(BATCH_REQUIRED_SUFFIXES, root)
