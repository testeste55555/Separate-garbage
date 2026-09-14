#!/usr/bin/env python3
"""Build M056 奥出雲町 LESSON_READY_10 data from audited fixed10/supplemental reviews.

Old paper is an official DROP_OFF / REFERENCE_ONLY route, so the learner projection uses
one simplified action (古紙回収) instead of pretending it is a normal curbside sorting box.
Supplemental-five evidence stays review-only until the guarded 15-item gate admits M056.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M056"
NAME = "奥出雲町"
CHECKED = "2026-09-14"
REVIEWER = "OPENAI_GPT56_M056_LESSON_READY_15_V1"
REVIEW = ROOT / "data/research/lesson_readiness/m056_item_review.csv"
SUPPLEMENTAL = ROOT / "data/research/lesson_readiness/m056_supplemental_review.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"
VARIANTS = ROOT / "data/app/lesson_variant_groups.csv"
SOURCES = ROOT / "data/research/03_sources_master.csv"
BATCH_SOURCES = ROOT / "data/research/batches/batch_06/batch_06_sources.csv"
QA = ROOT / "data/research/06_qa_log.csv"
BATCH_QA = ROOT / "data/research/batches/batch_06/batch_06_qa.csv"
MUNICIPALITIES = ROOT / "data/research/04_municipalities_research.csv"
BATCH_MUNICIPALITIES = ROOT / "data/research/batches/batch_06/batch_06_municipalities.csv"
PRIORITY = ROOT / "data/master/07_implementation_priority.csv"
COMPANY = ROOT / "data/app/company_municipality_mapping.csv"

FIXED = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}
SUPP = {"I002", "I003", "I010", "I018", "I027"}
SIMPLIFIED_ITEMS = {"I013", "I014", "I017"}

NEW_SOURCES = [
    {
        "municipality_id": MID, "source_id": "S-M056-04",
        "資料名": "リチウムイオン電池の捨て方について", "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.town.okuizumo.shimane.jp/kurashi/gomi-recycle/1765772698153.html",
        "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2026-03-26", "取得確認日": CHECKED,
        "使用した情報": "リチウムイオン電池・モバイルバッテリーは乾電池類として回収。取り外せない一体型家電は不燃ごみ。膨張品は端子を絶縁。",
        "優先度": "1", "現行性": "現行", "備考": "固定10 I029の品目別条件枝根拠。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M056-05",
        "資料名": "令和8年度 古紙回収日程", "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.town.okuizumo.shimane.jp/kurashi/gomi-recycle/1773391288583.html",
        "発行主体": NAME, "対象年度": "令和8年度", "ページ更新日": "2026-03-25", "取得確認日": CHECKED,
        "使用した情報": "新聞・段ボール・牛乳パック等は地区別の古紙回収日・指定場所へ持ち出す現行運用。",
        "優先度": "1", "現行性": "現行", "備考": "固定10古紙3品目の特別回収経路を補強。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M056-06",
        "資料名": "ごみ分別辞典 R8.4", "資料種別": "自治体公式PDF",
        "公式URL": "https://www.town.okuizumo.shimane.jp/assets/%E3%81%94%E3%81%BF%E5%88%86%E5%88%A5%E8%BE%9E%E5%85%B8%20R8.4_1.pdf",
        "発行主体": NAME, "対象年度": "令和8年度", "ページ更新日": "2026-04-21", "取得確認日": CHECKED,
        "使用した情報": "LED電球・乾電池・牛乳パック・新聞・充電式電池・包装フィルム等の品目別分別。",
        "優先度": "1", "現行性": "現行", "備考": "令和8年4月現在の現行品目辞典。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "https://www.town.okuizumo.shimane.jp/kurashi/gomi-recycle/1610005288925.html",
    },
]

ONLINE_SPEC = [
    ("C-M056-01", "燃やせるごみ", "FIXED_10_SCORING"),
    ("C-M056-02", "プラ容器包装", "FIXED_10_SCORING"),
    ("C-M056-03", "ペットボトル", "FIXED_10_SCORING"),
    ("C-M056-04", "空き缶", "FIXED_10_SCORING"),
    ("C-M056-05", "空きびん", "FIXED_10_SCORING"),
    ("C-M056-06", "不燃ごみ", "FIXED_10_SCORING"),
    ("C-M056-07", "有害ごみ", "FIXED_10_SCORING"),
    ("C-M056-08", "古紙回収", "SIMPLIFIED_ACTION"),
]
IN_PERSON_SPEC = [
    ("C-M056-01", "燃やせるごみ"),
    ("C-M056-02", "プラ容器包装"),
    ("C-M056-03", "ペットボトル"),
    ("C-M056-04", "空き缶"),
    ("C-M056-05", "空きびん"),
    ("C-M056-06", "不燃ごみ"),
    ("C-M056-07", "有害ごみ"),
]


def replace_mid(path: Path, new_rows: list[dict[str, str]]) -> None:
    fields, rows = read_csv(path)
    rows = [row for row in rows if row.get("municipality_id") != MID] + new_rows
    write_csv(path, fields, rows)


def upsert_sources(path: Path) -> None:
    fields, rows = read_csv(path)
    ids = {row["source_id"] for row in NEW_SOURCES}
    rows = [row for row in rows if not (row.get("municipality_id") == MID and row.get("source_id") in ids)]
    rows.extend(dict(row) for row in NEW_SOURCES)
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("source_id", "")))
    write_csv(path, fields, rows)


def validate_review(path: Path, expected: set[str]) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    _, rows = read_csv(path)
    if not rows or any(row.get("municipality_id") != MID for row in rows):
        raise ValueError(f"invalid M056 review: {path}")
    if any(row.get("branch_review_status") != "COMPLETE" for row in rows):
        raise ValueError(f"incomplete M056 review branch: {path}")
    by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_item[row["internal_item_id"]].append(row)
    if set(by_item) != expected:
        raise ValueError(f"unexpected M056 item set in {path}: {sorted(by_item)}")
    scoring: dict[str, dict[str, str]] = {}
    for iid, branches in by_item.items():
        orders = sorted(int(row["branch_order"]) for row in branches)
        if orders != list(range(1, len(branches) + 1)):
            raise ValueError(f"M056/{iid}: non-contiguous branch order")
        hits = [row for row in branches if row.get("scoring_branch") == "TRUE"]
        if len(hits) != 1:
            raise ValueError(f"M056/{iid}: expected exactly one scoring branch")
        scoring[iid] = hits[0]
    return rows, scoring


def sync_qa() -> None:
    fields, rows = read_csv(QA)
    hit = [row for row in rows if row.get("municipality_id") == MID]
    if len(hit) != 1:
        raise ValueError("expected one canonical M056 QA row")
    hit[0]["確認日"] = CHECKED
    write_csv(QA, fields, rows)
    canonical = dict(hit[0])
    bfields, brows = read_csv(BATCH_QA)
    if bfields != fields:
        raise ValueError("batch06 QA schema differs from canonical")
    count = 0
    for i, row in enumerate(brows):
        if row.get("municipality_id") == MID:
            brows[i] = dict(canonical); count += 1
    if count != 1:
        raise ValueError("expected one batch06 M056 QA row")
    write_csv(BATCH_QA, bfields, brows)


def sync_municipality_dates() -> None:
    for path in (MUNICIPALITIES, BATCH_MUNICIPALITIES):
        fields, rows = read_csv(path)
        hits = 0
        for row in rows:
            if row.get("municipality_id") == MID:
                row["最終確認日"] = CHECKED
                hits += 1
        if hits != 1:
            raise ValueError(f"expected one M056 municipality row in {path}")
        write_csv(path, fields, rows)


def update_priority() -> None:
    fields, rows = read_csv(PRIORITY)
    hits = 0
    for row in rows:
        if row.get("municipality_id") == MID:
            row["implementation_status"] = "IMPLEMENTED"
            row["readiness_status_snapshot"] = "LESSON_READY_10"
            row["checked_date"] = CHECKED
            row["note"] = "固定10品目LESSON_READY_10。C017-S06をroutingのみ有効化。古紙3品目は古紙回収へ簡略投影。補助5品目はreview完了だが15問Gate未接続。APP_READYには昇格しない。"
            hits += 1
    if hits != 1:
        raise ValueError("expected one M056 priority row")
    write_csv(PRIORITY, fields, rows)


def update_company() -> None:
    fields, rows = read_csv(COMPANY)
    hits = 0
    for row in rows:
        if row.get("company_id") == "C017" and row.get("site_id") == "C017-S06" and row.get("municipality_id") == MID:
            row["active"] = "TRUE"
            row["checked_date"] = CHECKED
            row["lesson_variant_group_id"] = ""
            row["identity_resolution_note"] = "公式営業拠点一覧で確認した奥出雲営業所（奥出雲町三成）をrouting metadataとして採用。M056はLESSON_READY_10整備済みのため固定10問を利用可能。会社所在地は居住地・家庭ごみ正答の根拠ではない。"
            hits += 1
    if hits != 1:
        raise ValueError("expected one C017-S06 M056 site")
    write_csv(COMPANY, fields, rows)


def build() -> None:
    fixed_rows, scoring = validate_review(REVIEW, FIXED)
    validate_review(SUPPLEMENTAL, SUPP)
    if len(fixed_rows) != 16:
        raise ValueError(f"M056 fixed10 review must retain 16 audited branches, got {len(fixed_rows)}")

    upsert_sources(SOURCES)
    upsert_sources(BATCH_SOURCES)
    sync_qa()
    sync_municipality_dates()

    fields, rows = read_csv(SCOPE)
    rows = [row for row in rows if row.get("municipality_id") != MID]
    rows.append({
        "municipality_id": MID, "municipality_name": NAME, "lesson_mode": "ONLINE_CLASS",
        "scoring_status": "LESSON_READY_10", "required_item_count": "10", "required_branch_count": "16",
        "review_source": "data/research/lesson_readiness/m056_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "固定10品目16条件枝COMPLETE。古紙3品目は通常収集BOXに偽装せず古紙回収へ簡略投影。補助5はreview済みだが15問Gate未接続。APP_READYには昇格しない。",
    })
    rows.sort(key=lambda row: row.get("municipality_id", ""))
    write_csv(SCOPE, fields, rows)

    boxes: list[dict[str, str]] = []
    for order, (cid, label, kind) in enumerate(ONLINE_SPEC, 1):
        boxes.append({
            "municipality_id": MID, "teaching_box_id": f"TB-{MID}-ON-{order:02d}",
            "class_mode": "ONLINE_CLASS", "box_kind": kind, "category_id": cid,
            "display_name": label, "display_order": str(order),
            "note": "固定10品目採点用。詳細条件・例外は教師用reviewに保持。" if kind == "FIXED_10_SCORING" else "古紙類は公式の指定日・指定場所回収。通常収集BOXとして扱わない。",
            "style_source_category_ids": cid if kind == "FIXED_10_SCORING" else "",
            "style_district_scope": "MUNICIPALITY_WIDE" if kind == "FIXED_10_SCORING" else "",
        })
    for order, (cid, label) in enumerate(IN_PERSON_SPEC, 1):
        boxes.append({
            "municipality_id": MID, "teaching_box_id": f"TB-{MID}-IP-{order:02d}",
            "class_mode": "IN_PERSON_CLASS", "box_kind": "MAJOR_CATEGORY", "category_id": cid,
            "display_name": label, "display_order": str(order),
            "note": "対面授業用の通常分別箱。古紙回収・粗大ごみ等の特別経路は実物仕分け箱から除外。",
            "style_source_category_ids": cid, "style_district_scope": "MUNICIPALITY_WIDE",
        })
    replace_mid(BOXES, boxes)

    online_by_category = {row["category_id"]: row for row in boxes if row["class_mode"] == "ONLINE_CLASS"}
    projection: list[dict[str, str]] = []
    for iid in sorted(scoring):
        row = scoring[iid]
        cid = row["category_id"]
        box = online_by_category.get(cid)
        if not box:
            raise ValueError(f"M056/{iid}: missing online box for {cid}")
        simplified = iid in SIMPLIFIED_ITEMS
        projection.append({
            "municipality_id": MID, "internal_item_id": iid, "teaching_box_id": box["teaching_box_id"],
            "projection_kind": "SIMPLIFIED_ACTION" if simplified else "OFFICIAL_CATEGORY",
            "category_id": cid, "review_status": "COMPLETE",
            "note": "古紙類は公式の指定日・指定場所回収のため『古紙回収』へ簡略投影。" if simplified else "公式分別区分へ投影。詳細条件・例外は教師用reviewに保持。",
        })
    replace_mid(PROJECTION, projection)

    _, variants = read_csv(VARIANTS)
    if any(row.get("municipality_id") == MID for row in variants):
        raise ValueError("M056 must not receive a regional lesson variant")

    update_priority()
    update_company()
    print(f"M056_LESSON_READY_BUILT fixed_items={len(scoring)} fixed_branches={len(fixed_rows)} supplemental=5 online_boxes={len(ONLINE_SPEC)} in_person_boxes={len(IN_PERSON_SPEC)} sites=1")


if __name__ == "__main__":
    build()
