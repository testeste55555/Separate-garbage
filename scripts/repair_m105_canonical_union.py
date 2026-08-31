#!/usr/bin/env python3
"""Repair M105 APP_READY bundle alignment after generation.

M105 belongs to completed Batch 10. Item-specific IS-* sources remain canonical-only;
ordinary category/reference sources are mirrored into Batch 10 so canonical identity
continues to equal Pilot + completed-batch union. The abnormal lithium-ion route is
kept as a dedicated EXCLUDED_NOTICE rather than overloading the household-PC route.
"""
from __future__ import annotations

from pathlib import Path

from schema_v12 import (
    CATEGORY_FIELDS,
    MAPPING_FIELDS,
    MUNICIPALITY_FIELDS,
    QA_FIELDS,
    SOURCE_FIELDS,
    compute_qa,
    read_csv,
    sync_municipality_qa_status,
    write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data/research"
MID = "M105"
CHECKED = "2026-08-31"
EXCLUDED_URL = "https://www.city.hatsukaichi.hiroshima.jp/soshiki/31/12524.html"
BATTERY_URL = "https://www.city.hatsukaichi.hiroshima.jp/soshiki/31/128679.html"
AUDIT_PATH = RESEARCH / "app_readiness/m105_item_review.csv"


def source_row(source_id: str, title: str, url: str, used: str) -> dict[str, str]:
    return {
        "municipality_id": MID,
        "source_id": source_id,
        "資料名": title,
        "資料種別": "自治体公式Webページ",
        "公式URL": url,
        "発行主体": "廿日市市",
        "対象年度": "令和8年度／取得時点現行",
        "ページ更新日": "",
        "取得確認日": CHECKED,
        "使用した情報": used,
        "優先度": "1",
        "現行性": "CURRENT",
        "備考": "M105 APP_READYで追加した公式参照ソース。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    }


ORDINARY_SOURCES = [
    source_row(
        "S-M105-04",
        "市が処理・収集しないごみ",
        EXCLUDED_URL,
        "特定家電製品・家庭用パソコンなど市の通常収集外品の処理経路",
    ),
    source_row(
        "S-M105-05",
        "リチウムイオン電池は正しく捨てましょう",
        BATTERY_URL,
        "破損・膨張・発熱など異常がある場合はごみステーション・回収ボックスへ出さず処理施設へ直接持込",
    ),
]


def excluded_category(
    category_id: str,
    name: str,
    representative: str,
    source_id: str,
    url: str,
    locator: str,
) -> dict[str, str]:
    return {
        "municipality_id": MID,
        "category_id": category_id,
        "自治体正式名称": name,
        "category_group": name,
        "parent_category_id": "",
        "classification_level": "EXCLUDED",
        "表示順": category_id.rsplit("-", 1)[-1],
        "collection_channel": "NOT_COLLECTED",
        "代表品目": representative,
        "入れてはいけない物": "市の通常収集対象ごみ",
        "適用条件": "通常のごみステーション収集では扱わない指定品",
        "条件外の扱い": "品目ごとの通常区分",
        "出す前の処理": "市公式案内の指定回収・処理経路を確認",
        "袋・容器のルール": "市指定袋へ入れない",
        "サイズ・条件": "",
        "粗大ごみ扱いか": "FALSE",
        "予約が必要か": "CONDITIONAL",
        "有料か": "CONDITIONAL",
        "料金ルール": "回収経路により異なる",
        "自治体収集外か": "TRUE",
        "注意事項": "通常のごみステーションへ出さず、市公式案内の処理経路を利用",
        "source_id": source_id,
        "出典URL": url,
        "出典ページ・該当箇所": locator,
        "確認日": CHECKED,
        "ui_role": "EXCLUDED_NOTICE",
        "rule_status": "CURRENT",
        "effective_from": "",
        "effective_to": "",
    }


def main() -> None:
    municipality_fields, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    category_fields, categories = read_csv(RESEARCH / "02_categories_master.csv")
    source_fields, sources = read_csv(RESEARCH / "03_sources_master.csv")
    qa_fields, qa = read_csv(RESEARCH / "06_qa_log.csv")
    _, review_evidence = read_csv(RESEARCH / "08_category_review_evidence.csv")
    mapping_fields, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    audit_fields, audit = read_csv(AUDIT_PATH)

    category_by = {(r["municipality_id"], r["category_id"]): r for r in categories}
    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    for row in ORDINARY_SOURCES:
        source_by[(MID, row["source_id"])] = row

    category_by[(MID, "C-M105-12")] = excluded_category(
        "C-M105-12",
        "特定家電製品",
        "エアコン・テレビ・冷蔵庫/冷凍庫・洗濯機/衣類乾燥機",
        "S-M105-04",
        EXCLUDED_URL,
        "市が処理・収集しないごみ：特定家電製品",
    )
    category_by[(MID, "C-M105-13")] = excluded_category(
        "C-M105-13",
        "家庭用パソコン",
        "デスクトップ・ノートパソコン・ディスプレイ等",
        "S-M105-04",
        EXCLUDED_URL,
        "市が処理・収集しないごみ：家庭用パソコン",
    )
    category_by[(MID, "C-M105-14")] = excluded_category(
        "C-M105-14",
        "処理施設へ直接持込（異常のあるリチウムイオン電池等）",
        "破損・膨張・発熱など異常のあるリチウムイオン電池・内蔵機器",
        "S-M105-05",
        BATTERY_URL,
        "【注意】リチウムイオン電池に異常がある場合",
    )

    # Repoint the abnormal embedded-battery branch to its own audited route.
    for row in audit:
        if row.get("municipality_id") != MID:
            continue
        if row.get("internal_item_id") == "I035" and "異常" in row.get("condition", ""):
            row["category_id"] = "C-M105-14"
            row["category_name"] = category_by[(MID, "C-M105-14")]["自治体正式名称"]
        elif row.get("category_id") in {"C-M105-12", "C-M105-13"}:
            row["category_name"] = category_by[(MID, row["category_id"])]["自治体正式名称"]

    for row in mappings:
        if row.get("municipality_id") != MID:
            continue
        if row.get("internal_item_id") == "I035" and "異常" in row.get("条件", ""):
            row["category_id"] = "C-M105-14"
        category = category_by.get((MID, row.get("category_id", "")))
        if category and row.get("category_id") in {"C-M105-12", "C-M105-13", "C-M105-14"}:
            row["分別区分正式名称"] = category["自治体正式名称"]
            row["自治体収集外"] = category["自治体収集外か"]
            row["category_source_id"] = category["source_id"]
            row["category_source_url"] = category["出典URL"]
            row["category_source_locator"] = category["出典ページ・該当箇所"]

    categories = sorted(category_by.values(), key=lambda r: (r["municipality_id"], r["category_id"]))
    sources = sorted(source_by.values(), key=lambda r: (r["municipality_id"], r["source_id"]))
    mappings.sort(key=lambda r: (
        r["municipality_id"], r["internal_item_id"], int(r.get("branch_order") or 0), r["mapping_id"]
    ))
    audit.sort(key=lambda r: (r["municipality_id"], r["internal_item_id"], int(r["branch_order"])))

    # M105 is a Batch 10 municipality. Mirror ordinary category/reference changes there.
    batch10 = RESEARCH / "batches/batch_10"
    b10_municipality_fields, b10_municipalities = read_csv(batch10 / "batch_10_municipalities.csv")
    b10_category_fields, b10_categories = read_csv(batch10 / "batch_10_categories.csv")
    b10_source_fields, b10_sources = read_csv(batch10 / "batch_10_sources.csv")
    b10_qa_fields, b10_qa = read_csv(batch10 / "batch_10_qa.csv")
    _, b10_review_evidence = read_csv(batch10 / "batch_10_category_review_evidence.csv")

    b10_category_by = {(r["municipality_id"], r["category_id"]): r for r in b10_categories}
    for cid in ("C-M105-12", "C-M105-13", "C-M105-14"):
        b10_category_by[(MID, cid)] = category_by[(MID, cid)]
    b10_categories = sorted(b10_category_by.values(), key=lambda r: (r["municipality_id"], r["category_id"]))

    b10_source_by = {(r["municipality_id"], r["source_id"]): r for r in b10_sources}
    # Item-specific sources must never enter the completed-batch union.
    for key in [k for k in b10_source_by if k[0] == MID and k[1].startswith("IS-")]:
        b10_source_by.pop(key)
    for row in ORDINARY_SOURCES:
        b10_source_by[(MID, row["source_id"])] = row
    b10_sources = sorted(b10_source_by.values(), key=lambda r: (r["municipality_id"], r["source_id"]))

    b10_qa = compute_qa(b10_municipalities, b10_categories, b10_sources, b10_review_evidence, b10_qa)
    b10_municipalities = sync_municipality_qa_status(b10_municipalities, b10_qa)

    # Undo the generator's accidental Batch 11 synchronization.
    batch11 = RESEARCH / "batches/batch_11"
    b11_category_fields, b11_categories = read_csv(batch11 / "batch_11_categories.csv")
    b11_source_fields, b11_sources = read_csv(batch11 / "batch_11_sources.csv")
    b11_categories = [r for r in b11_categories if r.get("municipality_id") != MID]
    b11_sources = [r for r in b11_sources if r.get("municipality_id") != MID]

    qa = compute_qa(municipalities, categories, sources, review_evidence, qa)
    municipalities = sync_municipality_qa_status(municipalities, qa)

    write_csv(RESEARCH / "02_categories_master.csv", category_fields or CATEGORY_FIELDS, categories)
    write_csv(RESEARCH / "03_sources_master.csv", source_fields or SOURCE_FIELDS, sources)
    write_csv(RESEARCH / "04_municipalities_research.csv", municipality_fields or MUNICIPALITY_FIELDS, municipalities)
    write_csv(RESEARCH / "05_item_mapping_master.csv", mapping_fields or MAPPING_FIELDS, mappings)
    write_csv(RESEARCH / "06_qa_log.csv", qa_fields or QA_FIELDS, qa)
    write_csv(AUDIT_PATH, audit_fields, audit)

    write_csv(batch10 / "batch_10_municipalities.csv", b10_municipality_fields or MUNICIPALITY_FIELDS, b10_municipalities)
    write_csv(batch10 / "batch_10_categories.csv", b10_category_fields or CATEGORY_FIELDS, b10_categories)
    write_csv(batch10 / "batch_10_sources.csv", b10_source_fields or SOURCE_FIELDS, b10_sources)
    write_csv(batch10 / "batch_10_qa.csv", b10_qa_fields or QA_FIELDS, b10_qa)
    write_csv(batch11 / "batch_11_categories.csv", b11_category_fields or CATEGORY_FIELDS, b11_categories)
    write_csv(batch11 / "batch_11_sources.csv", b11_source_fields or SOURCE_FIELDS, b11_sources)

    print("M105_CANONICAL_UNION_REPAIRED batch=10 ordinary_sources=2 item_sources=canonical_only excluded_routes=3")


if __name__ == "__main__":
    main()
