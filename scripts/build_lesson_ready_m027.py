#!/usr/bin/env python3
"""Build M027 大和郡山市 LESSON_READY_10 projections and current evidence.

The fixed-ten audited review is authoritative. Supplemental-five evidence is stored
separately and is not promoted into the guarded 15-item scoring gate here. Company
site activation is routing metadata only and must never be used as household-rule
evidence.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M027"
NAME = "大和郡山市"
CHECKED = "2026-09-11"
REVIEW = ROOT / "data/research/lesson_readiness/m027_item_review.csv"
SUPPLEMENTAL_REVIEW = ROOT / "data/research/lesson_readiness/m027_supplemental_review.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"
PRIORITY = ROOT / "data/master/07_implementation_priority.csv"
COMPANY = ROOT / "data/app/company_municipality_mapping.csv"
VARIANTS = ROOT / "data/app/lesson_variant_groups.csv"
SOURCES_MASTER = ROOT / "data/research/03_sources_master.csv"
BATCH_SOURCES = ROOT / "data/research/batches/batch_03/batch_03_sources.csv"

FIXED_10 = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}
SUPPLEMENTAL_5 = {"I002", "I003", "I010", "I018", "I027"}

SCOPE_FIELDS = [
    "municipality_id", "municipality_name", "lesson_mode", "scoring_status",
    "required_item_count", "required_branch_count", "review_source", "image_mapping_source", "note",
]
BOX_FIELDS = [
    "municipality_id", "teaching_box_id", "class_mode", "box_kind", "category_id",
    "display_name", "display_order", "note", "style_source_category_ids", "style_district_scope",
]
PROJECTION_FIELDS = [
    "municipality_id", "internal_item_id", "teaching_box_id", "projection_kind",
    "category_id", "review_status", "note",
]
SOURCE_FIELDS = [
    "municipality_id", "source_id", "資料名", "資料種別", "公式URL", "発行主体", "対象年度",
    "ページ更新日", "取得確認日", "使用した情報", "優先度", "現行性", "備考",
    "official_verified", "official_basis", "official_linking_url",
]

ONLINE_SPEC = [
    ("C-M027-01", "燃えるごみ"),
    ("C-M027-02", "燃えないごみ"),
    ("C-M027-04", "有害ごみ"),
    ("C-M027-05", "ペットボトル"),
    ("C-M027-06", "資源ごみ"),
]
IN_PERSON_SPEC = [
    ("C-M027-01", "燃えるごみ"),
    ("C-M027-02", "燃えないごみ"),
    ("C-M027-03", "粗大(大型)ごみ"),
    ("C-M027-04", "有害ごみ"),
    ("C-M027-05", "ペットボトル"),
    ("C-M027-06", "資源ごみ"),
]

NEW_SOURCES = [
    {
        "municipality_id": MID, "source_id": "S-M027-04", "資料名": "ごみの分別辞典（品目別50音順）",
        "資料種別": "自治体公式PDF", "公式URL": "https://www.city.yamatokoriyama.lg.jp/material/files/group/22/gomibunbetsu.pdf",
        "発行主体": NAME, "対象年度": "現行公式掲載版", "ページ更新日": "2025-05-02", "取得確認日": CHECKED,
        "使用した情報": "固定10・補助5の品目別分別、電球・ライター等の個別条件", "優先度": "1", "現行性": "現行案内中",
        "備考": "現行のごみ手引ページから案内される品目別辞典。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M027-05", "資料名": "電池・モバイルバッテリー・水銀式体温計等の出し方",
        "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.yamatokoriyama.lg.jp/kurashi_tetsuzuki/seikatu/gomi_recycle/kateigomi/16976.html",
        "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2025-12-22", "取得確認日": CHECKED,
        "使用した情報": "乾電池・充電式電池・モバイルバッテリーの有害ごみ区分、絶縁、赤色・青色回収ボックス", "優先度": "1", "現行性": "現行",
        "備考": "2026年5月版ルールと整合。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M027-06", "資料名": "食品トレーの回収",
        "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.yamatokoriyama.lg.jp/kurashi_tetsuzuki/seikatu/gomi_recycle/recycle/5764.html",
        "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2021-03-19", "取得確認日": CHECKED,
        "使用した情報": "洗浄・乾燥した食品トレーの任意回収ボックスルート", "優先度": "3", "現行性": "現行",
        "備考": "通常収集の教材正答は燃えるごみ。回収BOXは任意ルートとしてのみ保持。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M027-07", "資料名": "『廃棄ライター』などのごみの出し方について",
        "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.yamatokoriyama.lg.jp/soshiki/cleancenter/gomi_recycle/26/1372.html",
        "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2021-03-19", "取得確認日": CHECKED,
        "使用した情報": "使い捨てライターのガス抜き後の燃えるごみ区分、多量排出時の直接持込", "優先度": "2", "現行性": "現行",
        "備考": "現行分別辞典の使い捨てライター行と整合。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M027-08", "資料名": "ごみの分け方と出し方のルール（令和8年5月版）",
        "資料種別": "自治体公式PDF", "公式URL": "https://www.city.yamatokoriyama.lg.jp/material/files/group/22/gomirule_R8.pdf",
        "発行主体": NAME, "対象年度": "令和8年度", "ページ更新日": "2026-05-01", "取得確認日": CHECKED,
        "使用した情報": "PET本体・キャップ・ラベル、電池・モバイルバッテリー、小型プラスチック、生ごみ等の現行ルール", "優先度": "1", "現行性": "現行",
        "備考": "2026年5月発行の現行ルール。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
]


def replace_mid(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    current_fields, existing = read_csv(path)
    if current_fields != fields:
        raise ValueError(f"unexpected schema for {path}: {current_fields}")
    kept = [row for row in existing if row.get("municipality_id") != MID]
    write_csv(path, fields, kept + rows)


def upsert_sources(path: Path) -> None:
    fields, rows = read_csv(path)
    if fields != SOURCE_FIELDS:
        raise ValueError(f"unexpected source schema for {path}: {fields}")
    new_ids = {row["source_id"] for row in NEW_SOURCES}
    rows = [row for row in rows if not (row.get("municipality_id") == MID and row.get("source_id") in new_ids)]
    rows.extend(dict(row) for row in NEW_SOURCES)
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("source_id", "")))
    write_csv(path, fields, rows)


def validate_review(path: Path, expected_items: set[str], require_scoring: bool = True) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    _, rows = read_csv(path)
    if not rows or any(row.get("municipality_id") != MID for row in rows):
        raise ValueError(f"invalid M027 review: {path}")
    if any(row.get("branch_review_status") != "COMPLETE" for row in rows):
        raise ValueError(f"incomplete M027 review branch: {path}")
    by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_item[row["internal_item_id"]].append(row)
    if set(by_item) != expected_items:
        raise ValueError(f"unexpected item set in {path}: {sorted(by_item)}")
    scoring: dict[str, dict[str, str]] = {}
    if require_scoring:
        for iid, item_rows in by_item.items():
            hits = [row for row in item_rows if row.get("scoring_branch") == "TRUE"]
            if len(hits) != 1:
                raise ValueError(f"{MID}/{iid} must have exactly one scoring branch")
            scoring[iid] = hits[0]
    return rows, scoring


def update_priority() -> None:
    fields, rows = read_csv(PRIORITY)
    hits = 0
    for row in rows:
        if row.get("municipality_id") != MID:
            continue
        row["implementation_status"] = "IMPLEMENTED"
        row["readiness_status_snapshot"] = "LESSON_READY_10"
        row["checked_date"] = CHECKED
        row["note"] = "固定10品目LESSON_READY_10。C026-S01本社をroutingのみ有効化。会社所在地は家庭ごみルールの正答根拠に使用しない。"
        hits += 1
    if hits != 1:
        raise ValueError(f"expected one priority row for {MID}, got {hits}")
    write_csv(PRIORITY, fields, rows)


def update_company() -> None:
    fields, rows = read_csv(COMPANY)
    hits = 0
    for row in rows:
        if row.get("company_id") == "C026" and row.get("site_id") == "C026-S01" and row.get("municipality_id") == MID:
            row["active"] = "TRUE"
            row["checked_date"] = CHECKED
            row["identity_resolution_note"] = "ユーザー指定企業マスタの大和郡山市本社を採用。M027はLESSON_READY_10整備済みのため固定10問を利用可能。会社所在地はrouting metadataであり居住地・家庭ごみ正答の根拠ではない。"
            hits += 1
    if hits != 1:
        raise ValueError(f"expected one C026-S01/M027 row, got {hits}")
    write_csv(COMPANY, fields, rows)


def build() -> None:
    fixed_rows, scoring = validate_review(REVIEW, FIXED_10)
    validate_review(SUPPLEMENTAL_REVIEW, SUPPLEMENTAL_5)
    upsert_sources(SOURCES_MASTER)
    upsert_sources(BATCH_SOURCES)

    scope_fields, scope_existing = read_csv(SCOPE)
    if scope_fields != SCOPE_FIELDS:
        raise ValueError(f"unexpected schema for {SCOPE}: {scope_fields}")
    scope_rows = [row for row in scope_existing if row.get("municipality_id") != MID]
    scope_rows.append({
        "municipality_id": MID,
        "municipality_name": NAME,
        "lesson_mode": "ONLINE_CLASS",
        "scoring_status": "LESSON_READY_10",
        "required_item_count": "10",
        "required_branch_count": str(len(fixed_rows)),
        "review_source": "data/research/lesson_readiness/m027_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "固定10品目の通常画像枝をCOMPLETE。補助5品目は公式review済みだが現行15問Gateへは未接続。40品目APP_READYには昇格しない。",
    })
    write_csv(SCOPE, scope_fields, sorted(scope_rows, key=lambda row: row["municipality_id"]))

    boxes: list[dict[str, str]] = []
    for order, (cid, label) in enumerate(ONLINE_SPEC, 1):
        boxes.append({
            "municipality_id": MID,
            "teaching_box_id": f"TB-{MID}-ON-{order:02d}",
            "class_mode": "ONLINE_CLASS",
            "box_kind": "FIXED_10_SCORING",
            "category_id": cid,
            "display_name": label,
            "display_order": str(order),
            "note": "固定10品目採点用。",
            "style_source_category_ids": cid,
            "style_district_scope": "MUNICIPALITY_WIDE",
        })
    for order, (cid, label) in enumerate(IN_PERSON_SPEC, 1):
        boxes.append({
            "municipality_id": MID,
            "teaching_box_id": f"TB-{MID}-IP-{order:02d}",
            "class_mode": "IN_PERSON_CLASS",
            "box_kind": "MAJOR_CATEGORY",
            "category_id": cid,
            "display_name": label,
            "display_order": str(order),
            "note": "対面授業用の主要分別箱。",
            "style_source_category_ids": cid,
            "style_district_scope": "MUNICIPALITY_WIDE",
        })
    replace_mid(BOXES, BOX_FIELDS, boxes)

    online_box_by_category = {
        row["category_id"]: row for row in boxes if row["class_mode"] == "ONLINE_CLASS"
    }
    projection: list[dict[str, str]] = []
    for iid in sorted(scoring):
        row = scoring[iid]
        cid = row["category_id"]
        box = online_box_by_category.get(cid)
        if not box:
            raise ValueError(f"no M027 online teaching box for {iid}/{cid}")
        projection.append({
            "municipality_id": MID,
            "internal_item_id": iid,
            "teaching_box_id": box["teaching_box_id"],
            "projection_kind": "OFFICIAL_CATEGORY",
            "category_id": cid,
            "review_status": "COMPLETE",
            "note": "公式分別区分へ投影。詳細条件・任意回収・例外は教師用reviewに保持。",
        })
    replace_mid(PROJECTION, PROJECTION_FIELDS, projection)

    _, variants = read_csv(VARIANTS)
    if any(row.get("municipality_id") == MID for row in variants):
        raise ValueError("M027 must not receive a learner regional variant; current differences are collection-day only")

    update_priority()
    update_company()
    print(
        f"M027_LESSON_READY_BUILT fixed_items={len(scoring)} fixed_branches={len(fixed_rows)} "
        f"supplemental_reviewed=5 online_boxes={len(ONLINE_SPEC)} in_person_boxes={len(IN_PERSON_SPEC)}"
    )


if __name__ == "__main__":
    build()
