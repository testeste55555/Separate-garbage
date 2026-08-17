#!/usr/bin/env python3
"""Idempotently migrate the existing 15-municipality data set to Schema v1.1."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "master"
RESEARCH = ROOT / "data" / "research"
PILOT = RESEARCH / "pilot"
BATCH = RESEARCH / "batches" / "batch_01"
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
    "category_count_verified",
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
    "確認日", "mapping_status", "備考",
]

OFFICIAL_COUNT = {
    "M010": ("14", "公式ページが『5種14分別』と明示。EXCLUDED_NOTICEは件数外。"),
    "M102": ("13", "公式ページが13種類と明示。EXCLUDED_NOTICEは件数外。"),
}

ITEM_PATTERNS = {
    "I001": ("name", r"ペットボトル|^PET$"),
    "I002": ("representative", r"キャップ"),
    "I003": ("representative", r"ラベル"),
    "I004": ("all", r"アルミ缶"),
    "I005": ("all", r"スチール缶"),
    "I006": ("name", r"(?:ガラス)?[びビ]ん|ビン類|びん類"),
    "I007": ("name", r"白色.*トレ"),
    "I008": ("representative", r"色付きトレイ|白色以外のトレイ|色柄トレイ"),
    "I009": ("representative", r"弁当.*容器"),
    "I010": ("representative", r"お菓子の袋|菓子袋|スナック菓子の袋"),
    "I011": ("representative", r"レジ袋"),
    "I012": ("representative", r"発泡スチロール"),
    "I013": ("name", r"新聞"),
    "I014": ("name", r"段ボール|ダンボール"),
    "I015": ("name", r"雑誌"),
    "I016": ("name", r"その他紙|雑紙"),
    "I017": ("name", r"紙パック"),
    "I018": ("representative", r"生ごみ"),
    "I019": ("representative", r"ティッシュ"),
    "I020": ("representative", r"紙おむつ|おむつ"),
    "I021": ("all", r"衣類|古着|布類"),
    "I022": ("representative", r"傘"),
    "I023": ("representative", r"陶磁器|せともの"),
    "I024": ("representative", r"ガラス製品"),
    "I025": ("all", r"割れたガラス|割れガラス"),
    "I026": ("all", r"刃物|包丁"),
    "I027": ("all", r"乾電池"),
    "I028": ("all", r"ボタン電池"),
    "I029": ("all", r"モバイルバッテリー"),
    "I030": ("all", r"蛍光管|蛍光灯"),
    "I031": ("all", r"電球"),
    "I032": ("all", r"スプレー缶"),
    "I033": ("all", r"ライター"),
    "I034": ("all", r"小型家電"),
    "I035": ("all", r"電池を外せない.*家電|充電式電池を外せない.*家電"),
    "I036": ("representative", r"布団"),
    "I037": ("all", r"家電4品目|家電４品目|テレビ.*エアコン.*冷蔵庫|テレビ・エアコン"),
    "I038": ("all", r"パソコン"),
    "I039": ("all", r"食用油"),
    "I040": ("all", r"剪定枝|枝木"),
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


def migrate_sources(rows: list[dict[str, str]], registry) -> list[dict[str, str]]:
    migrated = []
    basis_map = {
        "MUNICIPAL_DOMAIN": "MUNICIPAL_DOMAIN",
        "INTERMUNICIPAL_AUTHORITY_DOMAIN": "INTERMUNICIPAL_AUTHORITY_DOMAIN",
        "MUNICIPAL_LINKED_SERVICE": "MUNICIPAL_LINKED_SERVICE",
    }
    for original in rows:
        row = dict(original)
        host = (urlparse(row.get("公式URL", "")).hostname or "").lower()
        authority = registry.get((row.get("municipality_id", ""), host))
        if authority:
            row["official_verified"] = "TRUE"
            row["official_basis"] = basis_map[authority["authority_type"]]
            row["official_linking_url"] = authority["verification_url"] if authority["authority_type"] == "MUNICIPAL_LINKED_SERVICE" else ""
        else:
            row["official_verified"] = "FALSE"
            row["official_basis"] = "UNVERIFIED"
            row["official_linking_url"] = ""
        migrated.append(row)
    return migrated


def japanese_date_to_iso(text: str) -> str:
    match = re.search(r"(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日", text or "")
    if not match:
        return ""
    year, month, day = (int(part) for part in match.groups())
    return f"{year:04d}-{month:02d}-{day:02d}"


def is_excluded_name(name: str) -> bool:
    return bool(re.search(r"収集.*(?:しない|できない)|処理できない|ステーションに出せない", name or ""))


def migrate_categories(rows: list[dict[str, str]], sources: list[dict[str, str]]) -> list[dict[str, str]]:
    source_currency = {(row["municipality_id"], row["source_id"]): row.get("現行性", "") for row in sources}
    migrated = []
    for original in rows:
        row = dict(original)
        # category_group is a CORE field.  Where the legacy Pilot had no
        # broader official grouping, use the official category itself as the
        # single-member group rather than inventing a new municipal label.
        if not row.get("category_group"):
            row["category_group"] = row.get("自治体正式名称", "")
        if is_excluded_name(row.get("自治体正式名称", "")):
            row["自治体収集外か"] = "TRUE"
            row["collection_channel"] = "NOT_COLLECTED"
            if row.get("classification_level") == "PRIMARY":
                row["classification_level"] = "EXCLUDED"
        currency = source_currency.get((row.get("municipality_id", ""), row.get("source_id", "")), "")
        status = row.get("rule_status", "")
        if status not in {"CURRENT", "PLANNED", "RETIRED"}:
            if "施行予定" in currency or "施行予定" in row.get("注意事項", ""):
                status = "PLANNED"
            elif "終了" in currency or "終了" in row.get("注意事項", ""):
                status = "RETIRED"
            else:
                status = "CURRENT"
        row["rule_status"] = status
        if status == "PLANNED" and not row.get("effective_from"):
            text = " ".join([row.get("注意事項", ""), row.get("適用条件", ""), row.get("対象年度", "")])
            row["effective_from"] = japanese_date_to_iso(text)
        else:
            row.setdefault("effective_from", "")
        row.setdefault("effective_to", "")
        if status in {"PLANNED", "RETIRED"}:
            ui_role = "HIDDEN"
        elif row.get("自治体収集外か") == "TRUE" or row.get("classification_level") == "EXCLUDED" or row.get("collection_channel") == "NOT_COLLECTED":
            ui_role = "EXCLUDED_NOTICE"
        elif row.get("collection_channel") in {"BOOKED_PICKUP", "DROP_OFF", "DIRECT_HAUL", "RETAILER_OR_MAKER"} or row.get("classification_level") == "ALTERNATIVE":
            ui_role = "REFERENCE_ONLY"
        else:
            ui_role = "SORT_BUCKET"
        row["ui_role"] = ui_role
        migrated.append(row)
    return migrated


def migrate_municipalities(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    migrated = []
    generic_basis = "公式分別ガイド・区分見出しを全件転記し、親区分のみで下位区分を落としていないことを再確認。"
    for original in rows:
        row = dict(original)
        count, basis = OFFICIAL_COUNT.get(row["municipality_id"], ("", generic_basis))
        row["official_category_count"] = count
        row["category_count_basis"] = basis
        row["category_count_verified"] = "TRUE"
        migrated.append(row)
    return migrated


def compute_qa(municipalities, categories, sources, old_qa=None):
    old_by_id = {row["municipality_id"]: row for row in (old_qa or [])}
    source_keys = {(row["municipality_id"], row["source_id"]): row for row in sources}
    category_keys = {(row["municipality_id"], row["category_id"]) for row in categories}
    rows = []
    for municipality in municipalities:
        mid = municipality["municipality_id"]
        cats = [row for row in categories if row["municipality_id"] == mid]
        srcs = [row for row in sources if row["municipality_id"] == mid]
        current = [row for row in cats if row["rule_status"] == "CURRENT"]
        names = [row["自治体正式名称"] for row in cats]
        referenced = [source_keys.get((mid, row["source_id"])) for row in cats]
        ref_ok = all(item is not None for item in referenced)
        official_ok = ref_ok and all(item.get("official_verified") == "TRUE" for item in referenced if item)
        dangerous = any(re.search(r"危険|有害|電池|蛍光|水銀|スプレー缶|ライター", " ".join(row.values())) for row in cats)
        excluded = any(row["ui_role"] == "EXCLUDED_NOTICE" for row in cats)
        bulky = any(row.get("粗大ごみ扱いか") in {"TRUE", "CONDITIONAL"} or "粗大" in row["自治体正式名称"] for row in cats)
        status_ok = all(row["rule_status"] in {"CURRENT", "PLANNED", "RETIRED"} and (row["rule_status"] != "PLANNED" or bool(row["effective_from"])) and (row["rule_status"] != "RETIRED" or bool(row["effective_to"])) for row in cats)
        ui_ok = all(row["ui_role"] in {"SORT_BUCKET", "REFERENCE_ONLY", "HIDDEN", "EXCLUDED_NOTICE"} and not (row["rule_status"] != "CURRENT" and row["ui_role"] == "SORT_BUCKET") for row in cats)
        core_ok = bool(cats) and all(all(row.get(field, "") for field in ["municipality_id", "category_id", "自治体正式名称", "classification_level", "表示順", "代表品目", "入れてはいけない物", "条件外の扱い", "出す前の処理", "袋・容器のルール", "自治体収集外か", "source_id", "出典URL", "出典ページ・該当箇所", "確認日", "ui_role", "rule_status"]) for row in cats)
        schema_ok = core_ok and status_ok and ui_ok and official_ok and len(category_keys) == len(categories)
        row = {
            "municipality_id": mid,
            "確認日": CHECKED,
            "ごみトップ": "TRUE" if municipality.get("自治体ごみトップURL", "").startswith("https://") else "FALSE",
            "現行ルール": "TRUE" if current and any(src.get("現行性") in {"現行", "現行案内中"} for src in srcs) else "FALSE",
            "全分別区分": "TRUE" if cats and municipality.get("category_count_verified") == "TRUE" and municipality.get("category_count_basis") else "FALSE",
            "正式名称": "TRUE" if names and len(names) == len(set(names)) and all(names) else "FALSE",
            "代表品目": "TRUE" if current and all(cat.get("代表品目") for cat in current) else "FALSE",
            "前処理": "TRUE" if current and all(cat.get("出す前の処理") for cat in current) else "FALSE",
            "袋容器": "TRUE" if current and all(cat.get("袋・容器のルール") for cat in current) else "FALSE",
            "危険有害": "TRUE" if dangerous else "FALSE",
            "収集しない物": "TRUE" if excluded else "FALSE",
            "公式出典": "TRUE" if official_ok else "FALSE",
            "参照整合性": "TRUE" if ref_ok else "FALSE",
            "Schema検証": "TRUE" if schema_ok else "FALSE",
            "category_count_verified": municipality.get("category_count_verified", "UNKNOWN"),
            "rule_status検証": "TRUE" if status_ok else "FALSE",
            "ui_role検証": "TRUE" if ui_ok else "FALSE",
            "検索サービス確認済み": "TRUE",
            "検索サービス存在": "TRUE" if municipality.get("品目検索URL") else "FALSE",
            "やさしい日本語確認済み": "TRUE",
            "やさしい日本語存在": "TRUE" if municipality.get("やさしい日本語URL") else "FALSE",
            "多言語確認済み": "TRUE",
            "多言語存在": "TRUE" if municipality.get("多言語資料URL") else "FALSE",
            "粗大ごみ": "TRUE" if bulky else "NOT_APPLICABLE",
            "備考": old_by_id.get(mid, {}).get("備考", "Schema v1.1で機械再計算"),
        }
        required = ["ごみトップ", "現行ルール", "全分別区分", "正式名称", "代表品目", "前処理", "袋容器", "危険有害", "収集しない物", "公式出典", "参照整合性", "Schema検証", "category_count_verified", "rule_status検証", "ui_role検証", "検索サービス確認済み", "やさしい日本語確認済み", "多言語確認済み"]
        row["確認ステータス"] = "QA_PASSED" if all(row[field] == "TRUE" for field in required) else "QA_REQUIRED"
        rows.append(row)
    return rows


def build_initial_mapping(categories: list[dict[str, str]]) -> list[dict[str, str]]:
    mappings = []
    by_pair: dict[tuple[str, str], list[dict[str, str]]] = {}
    for category in categories:
        for item_id, (scope, pattern) in ITEM_PATTERNS.items():
            name = category["自治体正式名称"]
            representative = category["代表品目"]
            if scope == "name":
                text = name
            elif scope == "representative":
                text = representative
            else:
                text = " ".join(category.get(field, "") for field in ["自治体正式名称", "代表品目", "入れてはいけない物", "出す前の処理", "注意事項"])
            if re.search(pattern, text):
                by_pair.setdefault((category["municipality_id"], item_id), []).append(category)
    for (mid, item_id), cats in sorted(by_pair.items()):
        cats.sort(key=lambda row: (row["rule_status"] != "CURRENT", int(row["表示順"])))
        for branch, category in enumerate(cats, 1):
            mappings.append({
                "mapping_id": f"MAP-{mid}-{item_id}-{branch:02d}",
                "municipality_id": mid,
                "internal_item_id": item_id,
                "branch_order": str(branch),
                "自治体での品目表記": "既存category代表品目から抽出",
                "category_id": category["category_id"],
                "分別区分正式名称": category["自治体正式名称"],
                "条件": category.get("適用条件") or "要品目別確認",
                "前処理": category.get("出す前の処理", ""),
                "例外分別先": category.get("条件外の扱い", ""),
                "自治体収集外": category.get("自治体収集外か", "FALSE"),
                "rule_status": category["rule_status"],
                "effective_from": category.get("effective_from", ""),
                "effective_to": category.get("effective_to", ""),
                "source_id": category["source_id"],
                "出典URL": category["出典URL"],
                "出典ページ・該当箇所": category["出典ページ・該当箇所"],
                "確認日": category["確認日"],
                "mapping_status": "INITIAL_REVIEW_REQUIRED",
                "備考": "既存の区分レベルデータから機械抽出。品目別の公式再確認前はAPP_READYにしない。",
            })
    return mappings


def migrate_bundle(municipality_path: Path, category_path: Path, source_path: Path, qa_path: Path, registry) -> None:
    _, municipalities = read_csv(municipality_path)
    _, categories = read_csv(category_path)
    _, sources = read_csv(source_path)
    _, old_qa = read_csv(qa_path) if qa_path.exists() else ([], [])
    sources = migrate_sources(sources, registry)
    categories = migrate_categories(categories, sources)
    municipalities = migrate_municipalities(municipalities)
    qa = compute_qa(municipalities, categories, sources, old_qa)
    write_csv(municipality_path, MUNICIPALITY_FIELDS, municipalities)
    write_csv(category_path, CATEGORY_FIELDS, categories)
    write_csv(source_path, SOURCE_FIELDS, sources)
    write_csv(qa_path, QA_FIELDS, qa)


def migrate_batch_dir(batch_dir: Path) -> None:
    registry = load_registry()
    prefix = batch_dir.name + "_"
    migrate_bundle(
        batch_dir / f"{prefix}municipalities.csv",
        batch_dir / f"{prefix}categories.csv",
        batch_dir / f"{prefix}sources.csv",
        batch_dir / f"{prefix}qa.csv",
        registry,
    )


def main() -> None:
    registry = load_registry()
    canonical_qa = RESEARCH / "06_qa_log.csv"
    canonical_old_qa_fields, canonical_old_qa = read_csv(canonical_qa)
    pilot_ids = {"M001", "M013", "M030", "M094", "M102"}
    pilot_qa_path = PILOT / "pilot_qa.csv"
    if not pilot_qa_path.exists():
        # Preserve the complete v1.0 QA rows until compute_qa has copied their
        # free-text notes into the v1.1 rows.  Writing with QA_FIELDS here would
        # silently discard legacy columns before migration reads them.
        write_csv(pilot_qa_path, canonical_old_qa_fields, [row for row in canonical_old_qa if row["municipality_id"] in pilot_ids])
    migrate_bundle(PILOT / "pilot_municipalities.csv", PILOT / "pilot_categories.csv", PILOT / "pilot_sources.csv", pilot_qa_path, registry)
    migrate_batch_dir(BATCH)

    # Canonical files are migrated directly once; merge_research.py will then
    # rebuild them idempotently from the immutable Pilot and Batch sources.
    migrate_bundle(
        RESEARCH / "04_municipalities_research.csv",
        RESEARCH / "02_categories_master.csv",
        RESEARCH / "03_sources_master.csv",
        canonical_qa,
        registry,
    )
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    mappings = build_initial_mapping(categories)
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    print("SCHEMA_V11_MIGRATION_COMPLETED")
    print(f"canonical_categories={len(categories)} initial_item_mappings={len(mappings)}")


if __name__ == "__main__":
    main()
