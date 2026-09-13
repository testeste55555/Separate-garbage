#!/usr/bin/env python3
"""Build M048 松江市 LESSON_READY_10 projections and current evidence.

M048 belongs to completed research batch_05, so any ordinary source/QA refresh is
written identically to both the canonical layer and the batch bundle. Supplemental-five
review remains evidence-only until the guarded 15-item gate explicitly admits M048.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M048"
NAME = "松江市"
CHECKED = "2026-09-14"
REVIEW = ROOT / "data/research/lesson_readiness/m048_item_review.csv"
SUPPLEMENTAL_REVIEW = ROOT / "data/research/lesson_readiness/m048_supplemental_review.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"
PRIORITY = ROOT / "data/master/07_implementation_priority.csv"
COMPANY = ROOT / "data/app/company_municipality_mapping.csv"
VARIANTS = ROOT / "data/app/lesson_variant_groups.csv"
SOURCES_MASTER = ROOT / "data/research/03_sources_master.csv"
BATCH_SOURCES = ROOT / "data/research/batches/batch_05/batch_05_sources.csv"
QA = ROOT / "data/research/06_qa_log.csv"
BATCH_QA = ROOT / "data/research/batches/batch_05/batch_05_qa.csv"

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
    ("C-M048-06", "缶・びん・ペットボトル"),
    ("C-M048-05", "プラスチック製容器包装"),
    ("C-M048-03", "古紙・古着"),
    ("C-M048-02", "金属"),
    ("C-M048-01", "もやせるごみ"),
]
IN_PERSON_SPEC = [
    ("C-M048-01", "もやせるごみ"),
    ("C-M048-02", "金属"),
    ("C-M048-03", "古紙・古着"),
    ("C-M048-04", "紙製容器包装"),
    ("C-M048-05", "プラスチック製容器包装"),
    ("C-M048-06", "缶・びん・ペットボトル"),
]

NEW_SOURCES = [
    {
        "municipality_id": MID,
        "source_id": "S-M048-04",
        "資料名": "缶・びん・ペットボトルの出し方",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.matsue.lg.jp/kurashi_tetsuzuki/gomi_kankyo_pet/6/2/5701.html",
        "発行主体": NAME,
        "対象年度": "現行",
        "ページ更新日": "2026-06-01",
        "取得確認日": CHECKED,
        "使用した情報": "飲食用缶・びん・PETの対象、PETキャップ・ラベル、破損・汚れたびんの例外",
        "優先度": "1",
        "現行性": "現行",
        "備考": "固定10と補助5のPET・缶・びんの品目別根拠。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    },
    {
        "municipality_id": MID,
        "source_id": "S-M048-05",
        "資料名": "プラスチック製容器包装の出し方",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.matsue.lg.jp/soshikikarasagasu/kankyoenergybu_recycletoshisuishinka/5/2/242.html",
        "発行主体": NAME,
        "対象年度": "現行",
        "ページ更新日": "2026-06-01",
        "取得確認日": CHECKED,
        "使用した情報": "袋類・キャップ・ラベル・トレイ類、プラマーク、汚れ条件",
        "優先度": "1",
        "現行性": "現行",
        "備考": "白色食品トレー・PETキャップ/ラベル・菓子袋の教材根拠。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    },
    {
        "municipality_id": MID,
        "source_id": "S-M048-06",
        "資料名": "古紙・古着の出し方",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.matsue.lg.jp/kurashi_tetsuzuki/gomi_kankyo_pet/6/2/5711.html",
        "発行主体": NAME,
        "対象年度": "現行",
        "ページ更新日": "2025-02-18",
        "取得確認日": CHECKED,
        "使用した情報": "新聞・段ボール・内側が白い紙パックの出し方",
        "優先度": "1",
        "現行性": "現行",
        "備考": "固定10の古紙3品目の品目別根拠。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    },
    {
        "municipality_id": MID,
        "source_id": "S-M048-07",
        "資料名": "金属の出し方",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.matsue.lg.jp/kurashi_tetsuzuki/gomi_kankyo_pet/6/2/5706.html",
        "発行主体": NAME,
        "対象年度": "現行",
        "ページ更新日": "2026-02-04",
        "取得確認日": CHECKED,
        "使用した情報": "乾電池・モバイルバッテリー・ライターを金属の主な収集品目として明示",
        "優先度": "1",
        "現行性": "現行",
        "備考": "充電式電池の詳細条件はS-M048-08を優先。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    },
    {
        "municipality_id": MID,
        "source_id": "S-M048-08",
        "資料名": "リチウムイオン電池（小型充電式電池）の適切な処理について（お願い）",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.matsue.lg.jp/kurashi_tetsuzuki/gomi_kankyo_pet/6/2/12542.html",
        "発行主体": NAME,
        "対象年度": "現行",
        "ページ更新日": "2026-01-30",
        "取得確認日": CHECKED,
        "使用した情報": "モバイルバッテリー、回収協力店条件、市収集時の金属ごみ・絶縁・表示方法",
        "優先度": "1",
        "現行性": "現行",
        "備考": "回収協力店で引取可能な電池と市収集対象を分けて保持。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    },
    {
        "municipality_id": MID,
        "source_id": "S-M048-09",
        "資料名": "もやせるごみの出し方",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.matsue.lg.jp/soshikikarasagasu/kankyoenergybu_recycletoshisuishinka/5/2/213.html",
        "発行主体": NAME,
        "対象年度": "現行",
        "ページ更新日": "2025-04-01",
        "取得確認日": CHECKED,
        "使用した情報": "生ごみ・ガラス類等のもやせるごみ、水切り・割れ物の処理",
        "優先度": "1",
        "現行性": "現行",
        "備考": "生ごみおよび条件外資源の補助根拠。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    },
    {
        "municipality_id": MID,
        "source_id": "S-M048-10",
        "資料名": "蛍光管などの水銀を含む製品の回収",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.matsue.lg.jp/kurashi_tetsuzuki/gomi_kankyo_pet/6/1/16068.html",
        "発行主体": NAME,
        "対象年度": "現行",
        "ページ更新日": "2026-04-20",
        "取得確認日": CHECKED,
        "使用した情報": "白熱電球・LED・ハロゲン・割れた蛍光管はもやせるごみ、蛍光管は専用回収箱",
        "優先度": "1",
        "現行性": "現行",
        "備考": "固定画像の一般電球と蛍光管の例外を分離。",
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


def upsert_sources(path: Path) -> None:
    fields, rows = read_csv(path)
    if fields != SOURCE_FIELDS:
        raise ValueError(f"unexpected source schema for {path}: {fields}")
    new_ids = {row["source_id"] for row in NEW_SOURCES}
    rows = [row for row in rows if not (row.get("municipality_id") == MID and row.get("source_id") in new_ids)]
    rows.extend(dict(row) for row in NEW_SOURCES)
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("source_id", "")))
    write_csv(path, fields, rows)


def sync_qa_pair() -> None:
    fields, rows = read_csv(QA)
    hits = [row for row in rows if row.get("municipality_id") == MID]
    if len(hits) != 1:
        raise ValueError(f"expected one canonical QA row for {MID}, got {len(hits)}")
    hits[0]["確認日"] = CHECKED
    write_csv(QA, fields, rows)
    canonical_row = dict(hits[0])

    batch_fields, batch_rows = read_csv(BATCH_QA)
    if batch_fields != fields:
        raise ValueError("batch_05 QA schema differs from canonical QA")
    batch_hits = 0
    for index, row in enumerate(batch_rows):
        if row.get("municipality_id") == MID:
            batch_rows[index] = dict(canonical_row)
            batch_hits += 1
    if batch_hits != 1:
        raise ValueError(f"expected one batch_05 QA row for {MID}, got {batch_hits}")
    write_csv(BATCH_QA, batch_fields, batch_rows)


def validate_review(path: Path, expected_items: set[str]) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    _, rows = read_csv(path)
    if not rows or any(row.get("municipality_id") != MID for row in rows):
        raise ValueError(f"invalid M048 review: {path}")
    if any(row.get("branch_review_status") != "COMPLETE" for row in rows):
        raise ValueError(f"incomplete M048 review branch: {path}")
    by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_item[row["internal_item_id"]].append(row)
    if set(by_item) != expected_items:
        raise ValueError(f"unexpected item set in {path}: {sorted(by_item)}")
    scoring: dict[str, dict[str, str]] = {}
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
        row["note"] = "固定10品目LESSON_READY_10。C017-S01/S03/S04をroutingのみ有効化。補助5品目はreview完了だが15問Gateへは未接続。会社所在地は家庭ごみ正答根拠に使用しない。"
        hits += 1
    if hits != 1:
        raise ValueError(f"expected one priority row for {MID}, got {hits}")
    write_csv(PRIORITY, fields, rows)


def update_company() -> None:
    fields, rows = read_csv(COMPANY)
    target_sites = {"C017-S01", "C017-S03", "C017-S04"}
    hits = set()
    for row in rows:
        if row.get("company_id") == "C017" and row.get("site_id") in target_sites and row.get("municipality_id") == MID:
            row["active"] = "TRUE"
            row["checked_date"] = CHECKED
            row["identity_resolution_note"] = (
                f"公式営業拠点一覧で確認した{row.get('site_display_name')}の松江市所在地をrouting metadataとして採用。"
                "M048はLESSON_READY_10整備済みのため固定10問を利用可能。会社所在地は居住地・家庭ごみ正答の根拠ではない。"
            )
            hits.add(row["site_id"])
    if hits != target_sites:
        raise ValueError(f"expected M048 C017 sites {sorted(target_sites)}, got {sorted(hits)}")
    write_csv(COMPANY, fields, rows)


def build() -> None:
    fixed_rows, scoring = validate_review(REVIEW, FIXED_10)
    validate_review(SUPPLEMENTAL_REVIEW, SUPPLEMENTAL_5)
    upsert_sources(SOURCES_MASTER)
    upsert_sources(BATCH_SOURCES)
    sync_qa_pair()

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
        "review_source": "data/research/lesson_readiness/m048_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "固定10品目の画像採点枝をCOMPLETE。補助5品目は公式review済みだが現行15問Gateへは未接続。40品目APP_READYには昇格しない。",
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
            "note": "固定10品目採点用。詳細条件・例外は教師用reviewに保持。",
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
            "note": "対面授業用の主要分別箱。粗大ごみは今回の実物仕分け箱から除外。",
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
            raise ValueError(f"no M048 online teaching box for {iid}/{cid}")
        projection.append({
            "municipality_id": MID,
            "internal_item_id": iid,
            "teaching_box_id": box["teaching_box_id"],
            "projection_kind": "OFFICIAL_CATEGORY",
            "category_id": cid,
            "review_status": "COMPLETE",
            "note": "公式分別区分へ投影。詳細条件・例外は教師用reviewに保持。",
        })
    replace_mid(PROJECTION, PROJECTION_FIELDS, projection)

    _, variants = read_csv(VARIANTS)
    if any(row.get("municipality_id") == MID for row in variants):
        raise ValueError("M048 must not receive a learner regional variant; current differences are collection schedule only")

    update_priority()
    update_company()
    print(
        f"M048_LESSON_READY_BUILT fixed_items={len(scoring)} fixed_branches={len(fixed_rows)} "
        f"supplemental_reviewed=5 online_boxes={len(ONLINE_SPEC)} in_person_boxes={len(IN_PERSON_SPEC)} sites=3"
    )


if __name__ == "__main__":
    build()
