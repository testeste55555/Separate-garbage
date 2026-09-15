#!/usr/bin/env python3
"""Build M070 玉野市 LESSON_READY_10 data from current official rules.

玉野市は地区ごとに収集日カレンダーが異なるが、分別区分そのものは市内共通。
既存Batch07の「ペットボトル・びん類」「缶類・危険性の物」は資料章見出しを
住民向け葉区分として束ねた状態だったため、2026年度カレンダーに合わせて
ペットボトル／びん類、缶類／危険性の物へ分解する。
モバイルバッテリーはごみステーション不可なのでSIMPLIFIED_ACTIONで扱う。
補助5は公式reviewまで完成させるがguarded 15-item Gateへは接続しない。
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from schema_v12 import build_coverage, read_csv, reconcile_mappings, write_csv
from sync_lesson_ready_reviews import synchronize as sync_lesson_reviews

ROOT = Path(__file__).resolve().parents[1]
MID = "M070"
NAME = "玉野市"
CHECKED = "2026-09-15"
REVIEWER = "OPENAI_GPT56_M070_LESSON_READY_15_V1"

REVIEW = ROOT / "data/research/lesson_readiness/m070_item_review.csv"
SUPPLEMENTAL = ROOT / "data/research/lesson_readiness/m070_supplemental_review.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"
VARIANTS = ROOT / "data/app/lesson_variant_groups.csv"
PRIORITY = ROOT / "data/master/07_implementation_priority.csv"

SOURCES = ROOT / "data/research/03_sources_master.csv"
CATEGORIES = ROOT / "data/research/02_categories_master.csv"
MUNICIPALITIES = ROOT / "data/research/04_municipalities_research.csv"
QA = ROOT / "data/research/06_qa_log.csv"
MAPPINGS = ROOT / "data/research/05_item_mapping_master.csv"
COVERAGE = ROOT / "data/research/07_item_mapping_coverage.csv"
CATEGORY_EVIDENCE = ROOT / "data/research/08_category_review_evidence.csv"

BATCH = ROOT / "data/research/batches/batch_07"
BATCH_SOURCES = BATCH / "batch_07_sources.csv"
BATCH_CATEGORIES = BATCH / "batch_07_categories.csv"
BATCH_MUNICIPALITIES = BATCH / "batch_07_municipalities.csv"
BATCH_QA = BATCH / "batch_07_qa.csv"
BATCH_MAPPINGS = BATCH / "batch_07_item_mapping.csv"
BATCH_COVERAGE = BATCH / "batch_07_item_coverage.csv"
BATCH_CATEGORY_EVIDENCE = BATCH / "batch_07_category_review_evidence.csv"

FIXED = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}
SUPP = {"I002", "I003", "I010", "I018", "I027"}

URL_INDEX = "https://www.city.tamano.lg.jp/site/recycle/1630.html"
URL_CAL = "https://www.city.tamano.lg.jp/uploaded/attachment/33595.pdf"
URL_DICT = "https://www.city.tamano.lg.jp/uploaded/attachment/27937.pdf"
URL_LI = "https://www.city.tamano.lg.jp/site/recycle/18110.html"
URL_LIGHTER = "https://www.city.tamano.lg.jp/site/recycle/48873.html"

NEW_SOURCES = [
    {
        "municipality_id": MID, "source_id": "S-M070-01",
        "資料名": "令和8年度ごみカレンダーと玉野市ごみ分別辞典",
        "資料種別": "自治体公式Webページ", "公式URL": URL_INDEX, "発行主体": NAME,
        "対象年度": "令和8年度", "ページ更新日": "2026-06-04", "取得確認日": CHECKED,
        "使用した情報": "令和8年度現行運用、地区別収集日、分別辞典への公式導線。",
        "優先度": "1", "現行性": "現行", "備考": "地区差は収集日のみ。曜日は教材正答に使用しない。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M070-02",
        "資料名": "玉野市ごみ分別収集カレンダー（令和8年度・B地区）",
        "資料種別": "自治体公式PDF", "公式URL": URL_CAL, "発行主体": NAME,
        "対象年度": "令和8年度", "ページ更新日": "2026-06-04", "取得確認日": CHECKED,
        "使用した情報": "可燃、不燃A、不燃B、危険、PET、その他プラ、缶、びん、古紙の9住民区分と代表品目。充電式電池・ボタン電池の拠点回収。",
        "優先度": "1", "現行性": "現行", "備考": "B地区を区分体系の代表資料として使用。A〜Eの差は収集日。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": URL_INDEX,
    },
    {
        "municipality_id": MID, "source_id": "S-M070-03",
        "資料名": "玉野市ごみ分別辞典 分別区分（50音順）",
        "資料種別": "自治体公式PDF", "公式URL": URL_DICT, "発行主体": NAME,
        "対象年度": "現行", "ページ更新日": "2022-02", "取得確認日": CHECKED,
        "使用した情報": "PET、キャップ・ラベル、アルミ缶、びん、食品トレイ、紙パック、電球、菓子袋等の品目別正答と例外。",
        "優先度": "1", "現行性": "現行案内中", "備考": "2026年度公式ページから現行分別辞典として案内。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": URL_INDEX,
    },
    {
        "municipality_id": MID, "source_id": "S-M070-04",
        "資料名": "火災多発！ リチウムイオン電池の出し方にご注意ください",
        "資料種別": "自治体公式Webページ", "公式URL": URL_LI, "発行主体": NAME,
        "対象年度": "現行", "ページ更新日": "2025-11-19", "取得確認日": CHECKED,
        "使用した情報": "小型充電式電池・モバイルバッテリーの絶縁と拠点回収、ごみステーション・小型家電BOX不可。",
        "優先度": "1", "現行性": "現行", "備考": "I029とI027例外の直接根拠。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M070-05",
        "資料名": "使い捨てライターの捨て方について",
        "資料種別": "自治体公式Webページ", "公式URL": URL_LIGHTER, "発行主体": NAME,
        "対象年度": "現行", "ページ更新日": "2025-05-12", "取得確認日": CHECKED,
        "使用した情報": "ガス抜き後、ライターだけを透明・半透明袋に入れて危険性の物の日に排出。",
        "優先度": "1", "現行性": "現行", "備考": "I033の直接根拠。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
]


def cat(cid: str, name: str, group: str, level: str, order: int, channel: str,
        examples: str, excluded: str = "", condition: str = "", outside: str = "",
        prep: str = "", bag: str = "", size: str = "", bulky: str = "FALSE",
        reservation: str = "FALSE", paid: str = "FALSE", fee: str = "",
        not_collected: str = "FALSE", note: str = "", sid: str = "S-M070-02",
        url: str = URL_CAL, locator: str = "", ui: str = "SORT_BUCKET") -> dict[str, str]:
    return {
        "municipality_id": MID, "category_id": cid, "自治体正式名称": name,
        "category_group": group, "parent_category_id": "", "classification_level": level,
        "表示順": str(order), "collection_channel": channel, "代表品目": examples,
        "入れてはいけない物": excluded or "NOT_STATED_IN_CITED_SOURCE",
        "適用条件": condition, "条件外の扱い": outside or "NOT_STATED_IN_CITED_SOURCE",
        "出す前の処理": prep or "NOT_STATED_IN_CITED_SOURCE", "袋・容器のルール": bag,
        "サイズ・条件": size, "粗大ごみ扱いか": bulky, "予約が必要か": reservation,
        "有料か": paid, "料金ルール": fee, "自治体収集外か": not_collected,
        "注意事項": note, "source_id": sid, "出典URL": url,
        "出典ページ・該当箇所": locator or name, "確認日": CHECKED,
        "ui_role": ui, "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
    }


NEW_CATEGORIES = [
    cat("C-M070-01", "燃やせるごみ", "燃やせるごみ", "PRIMARY", 1, "CURBSIDE",
        "生ごみ・ティッシュ類・使い捨てマスク・汚れた食品トレイ等",
        excluded="資源対象物・不燃物", prep="生ごみは十分水切り",
        bag="玉野市有料指定袋", paid="TRUE", fee="有料指定袋を購入",
        locator="令和8年度カレンダー／可燃ごみ"),
    cat("C-M070-02", "不燃物A", "不燃物A", "PRIMARY", 2, "CURBSIDE",
        "せともの・陶器類・ガラス・汚れた缶・汚れたびん・化粧品や油のびん",
        bag="玉野市有料指定袋", paid="TRUE", fee="有料指定袋を購入",
        locator="令和8年度カレンダー／不燃物A"),
    cat("C-M070-03", "不燃物B", "不燃物B", "PRIMARY", 3, "CURBSIDE",
        "厚さ2mm以上のプラスチック類・金属類・小型電気製品",
        bag="玉野市有料指定袋", paid="TRUE", fee="有料指定袋を購入",
        locator="令和8年度カレンダー／不燃物B"),
    cat("C-M070-12", "危険性の物", "危険性の物", "PRIMARY", 4, "CURBSIDE",
        "スプレー缶・乾電池・蛍光灯・電球・使い捨てライター",
        excluded="小型充電式電池・ボタン電池", outside="小型充電式電池・ボタン電池は環境保全課・東清掃センター等へ持参",
        prep="品目別に安全処理", bag="種類ごとに透明・半透明の袋",
        locator="令和8年度カレンダー／危険"),
    cat("C-M070-06", "ペットボトル", "ペットボトル", "PRIMARY", 5, "CURBSIDE",
        "PETマークのあるペットボトル", excluded="キャップ・ラベル・工作したPET",
        outside="キャップ・ラベルはその他プラ。工作したPETは燃やせるごみ",
        prep="中身を使い切って水洗い", bag="透明・半透明の袋（50L以内）",
        sid="S-M070-03", url=URL_DICT, locator="50音順／ペットボトル"),
    cat("C-M070-05", "その他プラスチック製容器包装", "その他プラスチック製容器包装", "PRIMARY", 6, "CURBSIDE",
        "プラマークの容器包装・食品用トレイ・PETキャップ/ラベル・菓子袋",
        excluded="汚れた食品トレイ等", outside="汚れが残る食品トレイ等は燃やせるごみ",
        prep="中身と汚れを除く", bag="透明・半透明の袋（50L以内）",
        locator="令和8年度カレンダー／その他プラ製容器包装"),
    cat("C-M070-07", "缶類", "缶類", "PRIMARY", 7, "CURBSIDE",
        "スチール缶・アルミ缶・のり缶・菓子缶", excluded="ひどく汚れた缶",
        outside="ひどく汚れた缶は不燃物A", prep="中身を空にして水洗い",
        bag="コンテナ", locator="令和8年度カレンダー／缶"),
    cat("C-M070-11", "びん類", "びん類", "PRIMARY", 8, "CURBSIDE",
        "飲食用びん", excluded="化粧品・油のびん・ひどく汚れたびん",
        outside="化粧品・油のびん・ひどく汚れたびんは不燃物A",
        prep="中身を空にして水洗い", bag="コンテナ",
        locator="令和8年度カレンダー／びん"),
    cat("C-M070-04", "古紙類", "古紙類", "PRIMARY", 9, "CURBSIDE",
        "新聞・雑誌・紙箱類・段ボール・牛乳パック・小さな雑がみ",
        prep="種類別に市指定方法でまとめる", bag="紐でしばる。小さな雑がみは紙袋・封筒可",
        locator="令和8年度カレンダー／古紙"),
    cat("C-M070-09", "粗大ごみ", "粗大ごみ", "PRIMARY", 10, "BOOKED_PICKUP",
        "1辺が50cm又は容量20Lを超える家庭ごみ", condition="1辺が50cm又は容量20Lを超える",
        prep="東清掃センター持込又は戸別収集", bulky="TRUE", paid="TRUE",
        fee="品目・収集方法により有料", sid="S-M070-01", url=URL_INDEX,
        locator="玉野市ごみ分別辞典／粗大ごみ", ui="REFERENCE_ONLY"),
    cat("C-M070-08", "古布・廃食用油", "古布・廃食用油", "ALTERNATIVE", 11, "DROP_OFF",
        "リユース可能な古布・植物性廃食用油", condition="指定拠点への持参",
        prep="古布は透明・半透明袋。廃食用油は不純物を除きPETボトルへ",
        note="市民センター・市役所・東清掃センター等で拠点回収",
        locator="令和8年度カレンダー／古布・廃食用油の拠点回収", ui="REFERENCE_ONLY"),
    cat("C-M070-13", "小型充電式電池・ボタン電池（拠点回収）", "小型充電式電池・ボタン電池", "ALTERNATIVE", 12, "DROP_OFF",
        "モバイルバッテリー・リチウムイオン電池等・ボタン電池",
        excluded="ごみステーション・小型家電回収BOX", condition="家庭用の対象充電池等",
        outside="購入店・取扱店への相談又は回収協力店も利用可",
        prep="端子をテープ等で絶縁", bag="窓口・回収協力店へ持参",
        note="モバイルバッテリー等はごみステーションに出さない",
        sid="S-M070-04", url=URL_LI, locator="充電池類の出し方", ui="REFERENCE_ONLY"),
    cat("C-M070-10", "市が取り扱わないもの", "市が取り扱わないもの", "EXCLUDED", 13, "NOT_COLLECTED",
        "処理困難物等", outside="販売店・メーカー・専門業者等へ相談",
        prep="受入先の指示に従う", not_collected="TRUE",
        sid="S-M070-01", url=URL_INDEX, locator="玉野市ごみ分別辞典／市が取り扱わないもの",
        ui="EXCLUDED_NOTICE"),
]

ONLINE_SPEC = [
    ("C-M070-06", "ペットボトル", "FIXED_10_SCORING"),
    ("C-M070-05", "その他プラ製容器包装", "FIXED_10_SCORING"),
    ("C-M070-04", "古紙類", "FIXED_10_SCORING"),
    ("C-M070-07", "缶類", "FIXED_10_SCORING"),
    ("C-M070-11", "びん類", "FIXED_10_SCORING"),
    ("C-M070-12", "危険性の物", "FIXED_10_SCORING"),
    ("C-M070-13", "回収・確認", "SIMPLIFIED_ACTION"),
]
IN_PERSON_SPEC = [
    ("C-M070-01", "燃やせるごみ"),
    ("C-M070-02", "不燃物A"),
    ("C-M070-03", "不燃物B"),
    ("C-M070-12", "危険性の物"),
    ("C-M070-06", "ペットボトル"),
    ("C-M070-05", "その他プラ製容器包装"),
    ("C-M070-07", "缶類"),
    ("C-M070-11", "びん類"),
    ("C-M070-04", "古紙類"),
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


def replace_categories(path: Path) -> None:
    fields, rows = read_csv(path)
    rows = [row for row in rows if row.get("municipality_id") != MID] + [dict(row) for row in NEW_CATEGORIES]
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("category_id", "")))
    write_csv(path, fields, rows)


def refresh_initial_mapping_layer() -> None:
    _, all_categories = read_csv(CATEGORIES)
    mapping_fields, all_mappings = read_csv(MAPPINGS)
    _, all_municipalities = read_csv(MUNICIPALITIES)
    coverage_fields, all_coverage = read_csv(COVERAGE)
    _, items = read_csv(ROOT / "data/master/04_common_items_master.csv")

    categories = [row for row in all_categories if row.get("municipality_id") == MID]
    mappings = [row for row in all_mappings if row.get("municipality_id") == MID]
    municipalities = [row for row in all_municipalities if row.get("municipality_id") == MID]
    coverage = [row for row in all_coverage if row.get("municipality_id") == MID]

    refreshed_mappings = reconcile_mappings(categories, mappings)
    refreshed_coverage = build_coverage(municipalities, items, refreshed_mappings, coverage)

    merged_mappings = [row for row in all_mappings if row.get("municipality_id") != MID] + refreshed_mappings
    merged_mappings.sort(key=lambda row: (
        row.get("municipality_id", ""), row.get("internal_item_id", ""),
        int(row.get("branch_order") or 0), row.get("mapping_id", ""),
    ))
    merged_coverage = [row for row in all_coverage if row.get("municipality_id") != MID] + refreshed_coverage
    merged_coverage.sort(key=lambda row: (row.get("municipality_id", ""), row.get("internal_item_id", "")))

    write_csv(MAPPINGS, mapping_fields, merged_mappings)
    write_csv(COVERAGE, coverage_fields, merged_coverage)


def sync_category_evidence() -> None:
    fields, rows = read_csv(CATEGORY_EVIDENCE)
    rows = [row for row in rows if row.get("municipality_id") != MID]
    rows.extend([
        {
            "review_evidence_id": "CRE-M070-01", "review_id": "CR-M070-CATEGORY-COVERAGE",
            "municipality_id": MID, "source_id": "S-M070-02",
            "locator": "令和8年度カレンダーの可燃・不燃A・不燃B・危険・PET・その他プラ・缶・びん・古紙",
            "evidence_role": "PRIMARY_INDEX",
            "notes": "2026-09-15再監査。資料章見出しではなく住民が排出時に選ぶ9葉区分として確認。",
        },
        {
            "review_evidence_id": "CRE-M070-02", "review_id": "CR-M070-CATEGORY-COVERAGE",
            "municipality_id": MID, "source_id": "S-M070-03",
            "locator": "50音順品目表の区分列",
            "evidence_role": "SUPPLEMENTAL_INDEX",
            "notes": "固定10・補助5の品目別正答と例外条件を照合。",
        },
        {
            "review_evidence_id": "CRE-M070-03", "review_id": "CR-M070-CATEGORY-COVERAGE",
            "municipality_id": MID, "source_id": "S-M070-04",
            "locator": "充電池類の出し方",
            "evidence_role": "SUPPLEMENTAL_INDEX",
            "notes": "小型充電式電池・モバイルバッテリーの拠点回収を通常収集と分離。",
        },
    ])
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("review_evidence_id", "")))
    write_csv(CATEGORY_EVIDENCE, fields, rows)


def validate_review(path: Path, expected: set[str], require_scoring: bool) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    _, rows = read_csv(path)
    if not rows or any(row.get("municipality_id") != MID for row in rows):
        raise ValueError(f"invalid M070 review: {path}")
    if any(row.get("branch_review_status") != "COMPLETE" for row in rows):
        raise ValueError(f"incomplete M070 review branch: {path}")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["internal_item_id"]].append(row)
    if set(grouped) != expected:
        raise ValueError(f"unexpected M070 item set in {path}: {sorted(grouped)}")
    scoring: dict[str, dict[str, str]] = {}
    for iid, branches in grouped.items():
        orders = sorted(int(row["branch_order"]) for row in branches)
        if orders != list(range(1, len(branches) + 1)):
            raise ValueError(f"M070/{iid}: non-contiguous branch order")
        hits = [row for row in branches if row.get("scoring_branch") == "TRUE"]
        if require_scoring:
            if len(hits) != 1:
                raise ValueError(f"M070/{iid}: expected exactly one scoring branch")
            scoring[iid] = hits[0]
        elif hits:
            raise ValueError(f"M070 supplemental/{iid}: must not define scoring branch")
    return rows, scoring


def update_municipality_qa() -> None:
    fields, rows = read_csv(MUNICIPALITIES)
    hits = 0
    for row in rows:
        if row.get("municipality_id") == MID:
            row["最終確認日"] = CHECKED
            row["備考"] = "2026年度カレンダーで9つのステーション分別葉を確認。粗大ごみを加えた10住民区分をPRIMARYとして保持。古布・廃食用油と小型充電式電池は拠点回収ALTERNATIVE。"
            row["reviewed_category_count"] = "10"
            row["category_count_basis"] = "可燃・不燃A・不燃B・危険・PET・その他プラ・缶・びん・古紙の9ステーション葉＋粗大ごみ。拠点回収2系統と収集外は件数外。"
            row["category_count_verified"] = "TRUE"
            row["category_count_check_status"] = "MANUAL_INDEX_REVIEW"
            row["category_count_review_id"] = "CR-M070-CATEGORY-COVERAGE"
            row["category_count_reviewed_date"] = CHECKED
            row["category_count_reviewed_by"] = REVIEWER
            hits += 1
    if hits != 1:
        raise ValueError(f"municipality M070 hit={hits}")
    write_csv(MUNICIPALITIES, fields, rows)

    fields, rows = read_csv(QA)
    hits = 0
    for row in rows:
        if row.get("municipality_id") == MID:
            row["確認日"] = CHECKED
            row["全分別区分"] = "TRUE"
            row["正式名称"] = "TRUE"
            row["参照整合性"] = "TRUE"
            row["Schema検証"] = "TRUE"
            row["category_count_verified"] = "TRUE"
            row["rule_status検証"] = "TRUE"
            row["ui_role検証"] = "TRUE"
            row["確認ステータス"] = "QA_PASSED"
            row["備考"] = "2026-09-15再監査。PET/びん、缶/危険を住民向け葉へ分解し、拠点回収の充電池を通常収集から分離。"
            hits += 1
    if hits != 1:
        raise ValueError(f"QA M070 hit={hits}")
    write_csv(QA, fields, rows)


def update_scope_boxes_projection(fixed_rows: list[dict[str, str]], scoring: dict[str, dict[str, str]]) -> None:
    fields, rows = read_csv(SCOPE)
    rows = [row for row in rows if row.get("municipality_id") != MID]
    rows.append({
        "municipality_id": MID, "municipality_name": NAME, "lesson_mode": "ONLINE_CLASS",
        "scoring_status": "LESSON_READY_10", "required_item_count": "10",
        "required_branch_count": str(len(fixed_rows)),
        "review_source": "data/research/lesson_readiness/m070_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "固定10を市内共通ルールで採点。PET/びん・缶/危険は正式葉へ分解。補助5はreview済み・15問Gate未接続。モバイルバッテリーはSIMPLIFIED_ACTION。",
    })
    rows.sort(key=lambda row: row.get("municipality_id", ""))
    write_csv(SCOPE, fields, rows)

    box_fields, old_boxes = read_csv(BOXES)
    old_boxes = [row for row in old_boxes if row.get("municipality_id") != MID]
    boxes: list[dict[str, str]] = []
    for order, (cid, label, kind) in enumerate(ONLINE_SPEC, 1):
        boxes.append({
            "municipality_id": MID, "teaching_box_id": f"TB-{MID}-ON-{order:02d}",
            "class_mode": "ONLINE_CLASS", "box_kind": kind, "category_id": cid,
            "display_name": label, "display_order": str(order),
            "note": "固定10品目採点用。詳細条件・例外は教師用reviewに保持。" if kind == "FIXED_10_SCORING" else "通常ごみBOXではない教材用簡略行動。詳細な持参先は教師用reviewに保持。",
            "style_source_category_ids": cid if kind == "FIXED_10_SCORING" else "",
            "style_district_scope": "MUNICIPALITY_WIDE" if kind == "FIXED_10_SCORING" else "",
        })
    for order, (cid, label) in enumerate(IN_PERSON_SPEC, 1):
        boxes.append({
            "municipality_id": MID, "teaching_box_id": f"TB-{MID}-IP-{order:02d}",
            "class_mode": "IN_PERSON_CLASS", "box_kind": "MAJOR_CATEGORY", "category_id": cid,
            "display_name": label, "display_order": str(order),
            "note": "対面授業用の主要分別箱。粗大・拠点回収・収集外は実物仕分け箱から除外。",
            "style_source_category_ids": cid, "style_district_scope": "MUNICIPALITY_WIDE",
        })
    old_boxes.extend(boxes)
    old_boxes.sort(key=lambda row: (row.get("municipality_id", ""), row.get("class_mode", ""), int(row.get("display_order") or 999), row.get("teaching_box_id", "")))
    write_csv(BOXES, box_fields, old_boxes)

    online_by_category = {row["category_id"]: row for row in boxes if row["class_mode"] == "ONLINE_CLASS"}
    projection: list[dict[str, str]] = []
    for iid in sorted(scoring):
        row = scoring[iid]
        cid = row["category_id"]
        box = online_by_category.get(cid)
        if not box:
            raise ValueError(f"M070/{iid}: missing online box for {cid}")
        projection.append({
            "municipality_id": MID, "internal_item_id": iid, "teaching_box_id": box["teaching_box_id"],
            "projection_kind": "SIMPLIFIED_ACTION" if iid == "I029" else "OFFICIAL_CATEGORY",
            "category_id": cid, "review_status": "COMPLETE",
            "note": "通常ごみステーション外の拠点回収へ投影。" if iid == "I029" else "公式分別区分へ投影。詳細条件・例外は教師用reviewに保持。",
        })
    replace_mid(PROJECTION, projection)

    _, variants = read_csv(VARIANTS)
    if any(row.get("municipality_id") == MID for row in variants):
        raise ValueError("M070 must not receive a regional lesson variant")


def update_priority() -> None:
    fields, rows = read_csv(PRIORITY)
    hits = 0
    for row in rows:
        if row.get("municipality_id") == MID:
            row["implementation_status"] = "IMPLEMENTED"
            row["readiness_status_snapshot"] = "LESSON_READY_10"
            row["checked_date"] = CHECKED
            row["note"] = "固定10品目LESSON_READY_10。地区差は収集日のみで採点は市内共通。補助5はreview済み・15問Gate未接続。モバイルバッテリーは通常収集BOXへ偽装しない。"
            hits += 1
    if hits != 1:
        raise ValueError(f"priority M070 hit={hits}")
    write_csv(PRIORITY, fields, rows)


def sync_batch_from_canonical() -> None:
    pairs = [
        (SOURCES, BATCH_SOURCES), (CATEGORIES, BATCH_CATEGORIES),
        (MUNICIPALITIES, BATCH_MUNICIPALITIES), (QA, BATCH_QA),
        (MAPPINGS, BATCH_MAPPINGS), (COVERAGE, BATCH_COVERAGE),
        (CATEGORY_EVIDENCE, BATCH_CATEGORY_EVIDENCE),
    ]
    for canonical_path, batch_path in pairs:
        _, canonical_rows = read_csv(canonical_path)
        batch_fields, batch_rows = read_csv(batch_path)
        replacement = [dict(row) for row in canonical_rows if row.get("municipality_id") == MID]
        batch_rows = [row for row in batch_rows if row.get("municipality_id") != MID] + replacement
        batch_rows.sort(key=lambda row: (
            row.get("municipality_id", ""),
            row.get("category_id", row.get("source_id", row.get("internal_item_id", row.get("review_evidence_id", "")))),
            int(row.get("branch_order") or 0) if str(row.get("branch_order", "")).isdigit() else 0,
        ))
        write_csv(batch_path, batch_fields, batch_rows)


def main() -> None:
    fixed_rows, scoring = validate_review(REVIEW, FIXED, True)
    supplemental_rows, _ = validate_review(SUPPLEMENTAL, SUPP, False)
    if len(fixed_rows) != 14:
        raise ValueError(f"M070 fixed10 review must retain 14 audited branches, got {len(fixed_rows)}")
    if len(supplemental_rows) != 5:
        raise ValueError(f"M070 supplemental review must retain 5 branches, got {len(supplemental_rows)}")

    upsert_sources(SOURCES)
    replace_categories(CATEGORIES)
    refresh_initial_mapping_layer()
    sync_category_evidence()
    update_municipality_qa()
    update_scope_boxes_projection(fixed_rows, scoring)
    update_priority()

    pairs, branches, image_updates = sync_lesson_reviews()
    sync_batch_from_canonical()
    print(
        f"M070_LESSON_READY_BUILT fixed_items={len(scoring)} fixed_branches={len(fixed_rows)} "
        f"supplemental={len(supplemental_rows)} sync_pairs={pairs} sync_branches={branches} "
        f"image_updates={image_updates} company_routes=0"
    )


if __name__ == "__main__":
    main()
