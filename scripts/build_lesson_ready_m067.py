#!/usr/bin/env python3
"""Build M067 岡山市 LESSON_READY_10 data from audited fixed10/supplemental reviews.

岡山市は市内共通の5つの固定10採点系統（可燃・不燃・プラスチック資源・資源化物・
廃乾電池/体温計）で扱える。品目条件差はreview枝に保持し、地域variantは作らない。
Supplemental-five evidence stays review-only until the guarded 15-item gate admits M067.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M067"
NAME = "岡山市"
CHECKED = "2026-09-14"
REVIEWER = "OPENAI_GPT56_M067_LESSON_READY_15_V1"
REVIEW = ROOT / "data/research/lesson_readiness/m067_item_review.csv"
SUPPLEMENTAL = ROOT / "data/research/lesson_readiness/m067_supplemental_review.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"
VARIANTS = ROOT / "data/app/lesson_variant_groups.csv"
SOURCES = ROOT / "data/research/03_sources_master.csv"
BATCH_SOURCES = ROOT / "data/research/batches/batch_07/batch_07_sources.csv"
QA = ROOT / "data/research/06_qa_log.csv"
BATCH_QA = ROOT / "data/research/batches/batch_07/batch_07_qa.csv"
MUNICIPALITIES = ROOT / "data/research/04_municipalities_research.csv"
BATCH_MUNICIPALITIES = ROOT / "data/research/batches/batch_07/batch_07_municipalities.csv"
PRIORITY = ROOT / "data/master/07_implementation_priority.csv"
COMPANY = ROOT / "data/app/company_municipality_mapping.csv"

FIXED = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}
SUPP = {"I002", "I003", "I010", "I018", "I027"}

NEW_SOURCES = [
    {"municipality_id": MID, "source_id": "S-M067-05", "資料名": "ペットボトルの出し方", "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.okayama.jp/kurashi/0000005203.html", "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2013-10-22", "取得確認日": CHECKED, "使用した情報": "PETマーク、本体の資源化物、キャップ・ラベル分離、水洗い", "優先度": "1", "現行性": "現行", "備考": "固定10 I001と補助I002/I003の直接根拠。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": ""},
    {"municipality_id": MID, "source_id": "S-M067-06", "資料名": "プラスチック資源の出し方（令和6年3月から）", "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.okayama.jp/kurashi/0000052989.html", "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2025-09-05", "取得確認日": CHECKED, "使用した情報": "食品トレイ、菓子袋、PETキャップ・ラベル、汚れが落ちないプラの可燃分岐", "優先度": "1", "現行性": "現行", "備考": "2024年3月開始後の現行プラスチック資源ルール。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": ""},
    {"municipality_id": MID, "source_id": "S-M067-07", "資料名": "古紙の出し方", "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.okayama.jp/kurashi/0000005263.html", "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2013-10-22", "取得確認日": CHECKED, "使用した情報": "新聞・段ボール・500ml以上紙パックの資源化物条件", "優先度": "1", "現行性": "現行", "備考": "固定10古紙3品目の主要根拠。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": ""},
    {"municipality_id": MID, "source_id": "S-M067-08", "資料名": "廃乾電池（リチウムイオン電池等を含む）・体温計等の出し方", "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.okayama.jp/kurashi/0000005238.html", "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2013-10-22", "取得確認日": CHECKED, "使用した情報": "乾電池・充電式電池・モバイルバッテリー・一体型製品の灰色コンテナ回収", "優先度": "1", "現行性": "現行", "備考": "I029/I027の直接根拠。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": ""},
    {"municipality_id": MID, "source_id": "S-M067-09", "資料名": "空き缶・スプレー缶の出し方", "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.okayama.jp/kurashi/0000005251.html", "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2013-10-22", "取得確認日": CHECKED, "使用した情報": "飲料用アルミ缶・スチール缶の資源化物排出", "優先度": "1", "現行性": "現行", "備考": "固定10 I004の直接根拠。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": ""},
    {"municipality_id": MID, "source_id": "S-M067-10", "資料名": "使い捨てガラスびんの出し方", "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.okayama.jp/kurashi/0000005224.html", "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2013-10-22", "取得確認日": CHECKED, "使用した情報": "通常びんの資源化物、油びん・耐熱ガラス・乳白色びん・汚れたびんの不燃分岐", "優先度": "1", "現行性": "現行", "備考": "固定10 I006の条件枝根拠。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": ""},
    {"municipality_id": MID, "source_id": "S-M067-11", "資料名": "分かりにくい資源・ごみの分別区分［ら行］", "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.okayama.jp/kurashi/0000059844.html", "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2025-03-01", "取得確認日": CHECKED, "使用した情報": "プラスチック製ライターは可燃、金属製ライターは不燃、中身を使い切る", "優先度": "1", "現行性": "現行", "備考": "固定10 I033の材質差根拠。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": ""},
    {"municipality_id": MID, "source_id": "S-M067-12", "資料名": "分かりにくい資源・ごみの分別区分［は行］", "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.okayama.jp/kurashi/0000059832.html", "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2026-04-01", "取得確認日": CHECKED, "使用した情報": "白熱球（LED等）は不燃ごみ、紙や箱で保護", "優先度": "1", "現行性": "現行", "備考": "固定10 I031の直接根拠。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": ""},
    {"municipality_id": MID, "source_id": "S-M067-13", "資料名": "分かりにくい資源・ごみの分別区分［か行］", "資料種別": "自治体公式Webページ", "公式URL": "https://www.city.okayama.jp/kurashi/0000059565.html", "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2025-03-01", "取得確認日": CHECKED, "使用した情報": "紙パック500ml以上内側白は資源化物、500ml未満・アルミコーティングは可燃", "優先度": "1", "現行性": "現行", "備考": "固定10 I017の条件枝根拠。", "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": ""},
]

ONLINE_SPEC = [
    ("C-M067-01", "可燃ごみ"),
    ("C-M067-02", "不燃ごみ"),
    ("C-M067-03", "プラスチック資源"),
    ("C-M067-04", "資源化物"),
    ("C-M067-05", "廃乾電池・体温計"),
]
IN_PERSON_SPEC = list(ONLINE_SPEC)


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
        raise ValueError(f"invalid M067 review: {path}")
    if any(row.get("branch_review_status") != "COMPLETE" for row in rows):
        raise ValueError(f"incomplete M067 review branch: {path}")
    by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_item[row["internal_item_id"]].append(row)
    if set(by_item) != expected:
        raise ValueError(f"unexpected M067 item set in {path}: {sorted(by_item)}")
    scoring: dict[str, dict[str, str]] = {}
    for iid, branches in by_item.items():
        orders = sorted(int(row["branch_order"]) for row in branches)
        if orders != list(range(1, len(branches) + 1)):
            raise ValueError(f"M067/{iid}: non-contiguous branch order")
        hits = [row for row in branches if row.get("scoring_branch") == "TRUE"]
        if len(hits) != 1:
            raise ValueError(f"M067/{iid}: expected exactly one scoring branch")
        scoring[iid] = hits[0]
    return rows, scoring


def sync_qa() -> None:
    fields, rows = read_csv(QA)
    hit = [row for row in rows if row.get("municipality_id") == MID]
    if len(hit) != 1:
        raise ValueError("expected one canonical M067 QA row")
    hit[0]["確認日"] = CHECKED
    write_csv(QA, fields, rows)
    canonical = dict(hit[0])
    bfields, brows = read_csv(BATCH_QA)
    if bfields != fields:
        raise ValueError("batch07 QA schema differs from canonical")
    count = 0
    for i, row in enumerate(brows):
        if row.get("municipality_id") == MID:
            brows[i] = dict(canonical)
            count += 1
    if count != 1:
        raise ValueError("expected one batch07 M067 QA row")
    write_csv(BATCH_QA, bfields, brows)


def sync_municipality_dates() -> None:
    for path in (MUNICIPALITIES, BATCH_MUNICIPALITIES):
        fields, rows = read_csv(path)
        hits = 0
        for row in rows:
            if row.get("municipality_id") == MID:
                row["最終確認日"] = CHECKED
                row["category_count_reviewed_date"] = CHECKED
                row["category_count_reviewed_by"] = REVIEWER
                hits += 1
        if hits != 1:
            raise ValueError(f"expected one M067 municipality row in {path}")
        write_csv(path, fields, rows)


def update_priority() -> None:
    fields, rows = read_csv(PRIORITY)
    hits = 0
    for row in rows:
        if row.get("municipality_id") == MID:
            row["implementation_status"] = "IMPLEMENTED"
            row["readiness_status_snapshot"] = "LESSON_READY_10"
            row["checked_date"] = CHECKED
            row["note"] = "固定10品目LESSON_READY_10。C027-S01/S02・C029-S01をroutingのみ有効化。補助5品目はreview完了だが15問Gate未接続。APP_READYには昇格しない。"
            hits += 1
    if hits != 1:
        raise ValueError("expected one M067 priority row")
    write_csv(PRIORITY, fields, rows)


def update_company() -> None:
    fields, rows = read_csv(COMPANY)
    target_sites = {"C027-S01", "C027-S02", "C029-S01"}
    hits: set[str] = set()
    for row in rows:
        site = row.get("site_id")
        if row.get("municipality_id") == MID and site in target_sites:
            row["active"] = "TRUE"
            row["checked_date"] = CHECKED
            row["lesson_variant_group_id"] = ""
            row["identity_resolution_note"] = (
                f"既存の公式会社・店舗情報で確認済みの岡山市拠点（{row.get('site_display_name')}）をrouting metadataとして採用。"
                "M067はLESSON_READY_10整備済みのため固定10問を利用可能。会社所在地は居住地・家庭ごみ正答の根拠ではない。"
            )
            hits.add(site)
    if hits != target_sites:
        raise ValueError(f"expected M067 target sites {sorted(target_sites)}, got {sorted(hits)}")
    write_csv(COMPANY, fields, rows)


def build() -> None:
    fixed_rows, scoring = validate_review(REVIEW, FIXED)
    validate_review(SUPPLEMENTAL, SUPP)
    if len(fixed_rows) != 15:
        raise ValueError(f"M067 fixed10 review must retain 15 audited branches, got {len(fixed_rows)}")

    upsert_sources(SOURCES)
    upsert_sources(BATCH_SOURCES)
    sync_qa()
    sync_municipality_dates()

    fields, rows = read_csv(SCOPE)
    rows = [row for row in rows if row.get("municipality_id") != MID]
    rows.append({
        "municipality_id": MID, "municipality_name": NAME, "lesson_mode": "ONLINE_CLASS",
        "scoring_status": "LESSON_READY_10", "required_item_count": "10", "required_branch_count": "15",
        "review_source": "data/research/lesson_readiness/m067_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "固定10品目15条件枝COMPLETE。市内共通5採点区分。補助5はreview済みだが15問Gate未接続。APP_READYには昇格しない。",
    })
    rows.sort(key=lambda row: row.get("municipality_id", ""))
    write_csv(SCOPE, fields, rows)

    boxes: list[dict[str, str]] = []
    for order, (cid, label) in enumerate(ONLINE_SPEC, 1):
        boxes.append({
            "municipality_id": MID, "teaching_box_id": f"TB-{MID}-ON-{order:02d}",
            "class_mode": "ONLINE_CLASS", "box_kind": "FIXED_10_SCORING", "category_id": cid,
            "display_name": label, "display_order": str(order),
            "note": "固定10品目採点用。詳細条件・例外は教師用reviewに保持。",
            "style_source_category_ids": cid, "style_district_scope": "MUNICIPALITY_WIDE",
        })
    for order, (cid, label) in enumerate(IN_PERSON_SPEC, 1):
        boxes.append({
            "municipality_id": MID, "teaching_box_id": f"TB-{MID}-IP-{order:02d}",
            "class_mode": "IN_PERSON_CLASS", "box_kind": "MAJOR_CATEGORY", "category_id": cid,
            "display_name": label, "display_order": str(order),
            "note": "対面授業用の主要分別箱。粗大ごみ・収集不可は実物仕分け箱から除外。",
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
            raise ValueError(f"M067/{iid}: missing online box for {cid}")
        projection.append({
            "municipality_id": MID, "internal_item_id": iid, "teaching_box_id": box["teaching_box_id"],
            "projection_kind": "OFFICIAL_CATEGORY", "category_id": cid, "review_status": "COMPLETE",
            "note": "公式分別区分へ投影。詳細条件・例外は教師用reviewに保持。",
        })
    replace_mid(PROJECTION, projection)

    _, variants = read_csv(VARIANTS)
    if any(row.get("municipality_id") == MID for row in variants):
        raise ValueError("M067 must not receive a regional lesson variant")

    update_priority()
    update_company()
    print(f"M067_LESSON_READY_BUILT fixed_items={len(scoring)} fixed_branches={len(fixed_rows)} supplemental=5 online_boxes={len(ONLINE_SPEC)} in_person_boxes={len(IN_PERSON_SPEC)} sites=3")


if __name__ == "__main__":
    build()
