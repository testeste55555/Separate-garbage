#!/usr/bin/env python3
"""Build M030 米子市 LESSON_READY_10 projections and current evidence.

The fixed-ten review is authoritative. Supplemental-five evidence is retained separately
until the guarded 15-item gate explicitly admits M030. Company location is routing
metadata only and is never household-waste correctness evidence.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M030"
NAME = "米子市"
CHECKED = "2026-09-11"
REVIEW = ROOT / "data/research/lesson_readiness/m030_item_review.csv"
SUPPLEMENTAL_REVIEW = ROOT / "data/research/lesson_readiness/m030_supplemental_review.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"
PRIORITY = ROOT / "data/master/07_implementation_priority.csv"
COMPANY = ROOT / "data/app/company_municipality_mapping.csv"
VARIANTS = ROOT / "data/app/lesson_variant_groups.csv"
SOURCES_MASTER = ROOT / "data/research/03_sources_master.csv"
QA = ROOT / "data/research/06_qa_log.csv"

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
    ("C-M030-06", "ペットボトル", "FIXED_10_SCORING"),
    ("C-M030-04", "白色発泡スチロール・トレー", "FIXED_10_SCORING"),
    ("C-M030-05", "缶・ビン類", "FIXED_10_SCORING"),
    ("C-M030-07", "古紙類", "FIXED_10_SCORING"),
    ("C-M030-09", "蛍光管・水銀体温計・電球", "FIXED_10_SCORING"),
    ("C-M030-02", "不燃ごみ", "FIXED_10_SCORING"),
    ("C-M030-10", "回収・確認", "SIMPLIFIED_ACTION"),
]
IN_PERSON_SPEC = [
    ("C-M030-01", "可燃ごみ"),
    ("C-M030-02", "不燃ごみ"),
    ("C-M030-03", "不燃性粗大ごみ"),
    ("C-M030-04", "白色発泡スチロール・トレー"),
    ("C-M030-05", "缶・ビン類"),
    ("C-M030-06", "ペットボトル"),
    ("C-M030-07", "古紙類"),
    ("C-M030-08", "乾電池・リチウムイオン充電池類"),
    ("C-M030-09", "蛍光管・水銀体温計・電球"),
]

NEW_SOURCES = [
    {
        "municipality_id": MID,
        "source_id": "S-M030-05",
        "資料名": "モバイルバッテリーの処分方法",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.yonago.lg.jp/48303.htm",
        "発行主体": NAME,
        "対象年度": "現行",
        "ページ更新日": "2026-05-20",
        "取得確認日": CHECKED,
        "使用した情報": "モバイルバッテリーはごみ置場不可、端子絶縁、協力店・小型家電回収BOX・クリーン推進課、破損膨張品はクリーン推進課のみ",
        "優先度": "1",
        "現行性": "現行",
        "備考": "一般の電池収集と混同せず、教材では非通常ルートとして扱う。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    },
    {
        "municipality_id": MID,
        "source_id": "S-M030-06",
        "資料名": "ペットボトルの水平リサイクルへの協力のお願い",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.yonago.lg.jp/45409.htm",
        "発行主体": NAME,
        "対象年度": "現行",
        "ページ更新日": "2025-02-20",
        "取得確認日": CHECKED,
        "使用した情報": "ペットボトルのラベルは可燃ごみ、ふたは不燃ごみ、本体は中をすすぐ",
        "優先度": "1",
        "現行性": "現行",
        "備考": "PET本体から外したキャップ・ラベルの教材正答根拠。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    },
]


def replace_mid(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    current_fields, existing = read_csv(path)
    if current_fields != fields:
        raise ValueError(f"unexpected schema for {path}: {current_fields}")
    kept = [row for row in existing if row.get("municipality_id") != MID]
    write_csv(path, fields, kept + rows)


def upsert_sources() -> None:
    fields, rows = read_csv(SOURCES_MASTER)
    if fields != SOURCE_FIELDS:
        raise ValueError(f"unexpected source schema: {fields}")
    new_ids = {row["source_id"] for row in NEW_SOURCES}
    rows = [row for row in rows if not (row.get("municipality_id") == MID and row.get("source_id") in new_ids)]
    rows.extend(dict(row) for row in NEW_SOURCES)
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("source_id", "")))
    write_csv(SOURCES_MASTER, fields, rows)


def validate_review(path: Path, expected_items: set[str], require_scoring: bool = True) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    _, rows = read_csv(path)
    if not rows or any(row.get("municipality_id") != MID for row in rows):
        raise ValueError(f"invalid M030 review: {path}")
    if any(row.get("branch_review_status") != "COMPLETE" for row in rows):
        raise ValueError(f"incomplete M030 review branch: {path}")
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
        row["note"] = "固定10品目LESSON_READY_10。C012-S01をroutingのみ有効化。モバイルバッテリーは通常収集BOXへ偽装しない。会社所在地は家庭ごみルールの正答根拠に使用しない。"
        hits += 1
    if hits != 1:
        raise ValueError(f"expected one priority row for {MID}, got {hits}")
    write_csv(PRIORITY, fields, rows)


def update_company() -> None:
    fields, rows = read_csv(COMPANY)
    hits = 0
    for row in rows:
        if row.get("company_id") == "C012" and row.get("site_id") == "C012-S01" and row.get("municipality_id") == MID:
            row["active"] = "TRUE"
            row["checked_date"] = CHECKED
            row["identity_resolution_note"] = "ユーザー指定企業マスタの米子市所在地を採用。M030はLESSON_READY_10整備済みのため固定10問を利用可能。会社所在地はrouting metadataであり居住地・家庭ごみ正答の根拠ではない。"
            hits += 1
    if hits != 1:
        raise ValueError(f"expected one C012-S01/M030 row, got {hits}")
    write_csv(COMPANY, fields, rows)


def update_qa_date() -> None:
    fields, rows = read_csv(QA)
    hits = 0
    for row in rows:
        if row.get("municipality_id") == MID:
            row["確認日"] = CHECKED
            hits += 1
    if hits != 1:
        raise ValueError(f"expected one M030 QA row, got {hits}")
    write_csv(QA, fields, rows)


def build() -> None:
    fixed_rows, scoring = validate_review(REVIEW, FIXED_10)
    validate_review(SUPPLEMENTAL_REVIEW, SUPPLEMENTAL_5)
    upsert_sources()
    update_qa_date()

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
        "review_source": "data/research/lesson_readiness/m030_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "固定10品目の画像採点枝をCOMPLETE。補助5品目は公式review済みだが現行15問Gateへは未接続。モバイルバッテリーはSIMPLIFIED_ACTION。40品目APP_READYには昇格しない。",
    })
    write_csv(SCOPE, scope_fields, sorted(scope_rows, key=lambda row: row["municipality_id"]))

    boxes: list[dict[str, str]] = []
    for order, (cid, label, kind) in enumerate(ONLINE_SPEC, 1):
        boxes.append({
            "municipality_id": MID,
            "teaching_box_id": f"TB-{MID}-ON-{order:02d}",
            "class_mode": "ONLINE_CLASS",
            "box_kind": kind,
            "category_id": cid,
            "display_name": label,
            "display_order": str(order),
            "note": "固定10品目採点用。" if kind == "FIXED_10_SCORING" else "自治体正式区分ではない教材用簡略行動。詳細ルートは教師用reviewに保持。",
            "style_source_category_ids": cid if kind == "FIXED_10_SCORING" else "",
            "style_district_scope": "MUNICIPALITY_WIDE" if kind == "FIXED_10_SCORING" else "",
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

    online_box_by_category = {row["category_id"]: row for row in boxes if row["class_mode"] == "ONLINE_CLASS"}
    projection: list[dict[str, str]] = []
    for iid in sorted(scoring):
        row = scoring[iid]
        cid = row["category_id"]
        box = online_box_by_category.get(cid)
        if not box:
            raise ValueError(f"no M030 online teaching box for {iid}/{cid}")
        kind = "SIMPLIFIED_ACTION" if iid == "I029" else "OFFICIAL_CATEGORY"
        projection.append({
            "municipality_id": MID,
            "internal_item_id": iid,
            "teaching_box_id": box["teaching_box_id"],
            "projection_kind": kind,
            "category_id": cid,
            "review_status": "COMPLETE",
            "note": "非通常回収ルートを教材用「回収・確認」へ投影。詳細はreviewに保持。" if kind == "SIMPLIFIED_ACTION" else "公式分別区分へ投影。詳細条件・例外は教師用reviewに保持。",
        })
    replace_mid(PROJECTION, PROJECTION_FIELDS, projection)

    _, variants = read_csv(VARIANTS)
    if any(row.get("municipality_id") == MID for row in variants):
        raise ValueError("M030 must not receive a learner regional variant; current district differences are collection-day only")

    update_priority()
    update_company()
    print(
        f"M030_LESSON_READY_BUILT fixed_items={len(scoring)} fixed_branches={len(fixed_rows)} "
        f"supplemental_reviewed=5 online_boxes={len(ONLINE_SPEC)} in_person_boxes={len(IN_PERSON_SPEC)}"
    )


if __name__ == "__main__":
    build()
