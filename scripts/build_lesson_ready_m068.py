#!/usr/bin/env python3
"""Build M068 倉敷市 fixed-10 regional lesson data.

倉敷市は真備地区とそれ以外で住民向け正式区分が異なり、固定10でも
白色トレイ・電球・モバイルバッテリー等の正答BOXが変わる。
そのため municipality-wide scoring branch は作らず、2 lesson variant groupへ投影する。
補助5は公式reviewまで完成させるが guarded 15-item Gate へは接続しない。
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from schema_v12 import build_coverage, read_csv, reconcile_mappings, write_csv
from sync_lesson_ready_reviews import VARIANT_ONLY_LESSON_READY, synchronize as sync_lesson_reviews

ROOT = Path(__file__).resolve().parents[1]
MID = "M068"
CHECKED = "2026-09-15"
REVIEWER = "OPENAI_GPT56_M068_LESSON_READY_15_V1"
REVIEW = ROOT / "data/research/lesson_readiness/m068_item_review.csv"
SUPPLEMENTAL = ROOT / "data/research/lesson_readiness/m068_supplemental_review.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
GROUPS = ROOT / "data/app/lesson_variant_groups.csv"
SCOPES = ROOT / "data/app/district_scopes.csv"
BOXES = ROOT / "data/app/lesson_variant_teaching_boxes.csv"
SCORING = ROOT / "data/app/lesson_variant_item_scoring.csv"
VARIANT_SOURCES = ROOT / "data/research/lesson_readiness/lesson_variant_sources.csv"
SOURCES = ROOT / "data/research/03_sources_master.csv"
CATEGORIES = ROOT / "data/research/02_categories_master.csv"
MUNICIPALITIES = ROOT / "data/research/04_municipalities_research.csv"
QA = ROOT / "data/research/06_qa_log.csv"
MAPPINGS = ROOT / "data/research/05_item_mapping_master.csv"
COVERAGE = ROOT / "data/research/07_item_mapping_coverage.csv"
CATEGORY_EVIDENCE = ROOT / "data/research/08_category_review_evidence.csv"
PRIORITY = ROOT / "data/master/07_implementation_priority.csv"
COMPANY = ROOT / "data/app/company_municipality_mapping.csv"

BATCH = ROOT / "data/research/batches/batch_07"
BATCH_SOURCES = BATCH / "batch_07_sources.csv"
BATCH_CATEGORIES = BATCH / "batch_07_categories.csv"
BATCH_MUNICIPALITIES = BATCH / "batch_07_municipalities.csv"
BATCH_QA = BATCH / "batch_07_qa.csv"
BATCH_MAPPINGS = BATCH / "batch_07_item_mapping.csv"
BATCH_COVERAGE = BATCH / "batch_07_item_coverage.csv"
BATCH_CATEGORY_EVIDENCE = BATCH / "batch_07_category_review_evidence.csv"

FIXED = ["I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"]
SUPP = {"I002", "I003", "I010", "I018", "I027"}

URL03 = "https://www.city.kurashiki.okayama.jp/kurashi/kankyo/1003645/1013690/1003647/1003648.html"
URL04 = "https://www.city.kurashiki.okayama.jp/kurashi/kankyo/1003645/1013690/1003647/1003662.html"
URL05 = "https://www.city.kurashiki.okayama.jp/kurashi/kankyo/1003645/1013690/1003647/1003663.html"
URL06 = "https://www.city.kurashiki.okayama.jp/kurashi/kankyo/1003645/1013690/1013715/1003713.html"
URL07 = "https://www.city.kurashiki.okayama.jp/kurashi/kankyo/1003645/1013690/1003664/1003665.html"
URL08 = "https://www.city.kurashiki.okayama.jp/kurashi/kankyo/1003645/1022731/1023374.html"
URL09 = "https://www.city.kurashiki.okayama.jp/kurashi/kankyo/1003645/1013690/1013715/1003683.html"
URL10 = "https://www.city.kurashiki.okayama.jp/kurashi/kankyo/1003645/1013690/1013715/1003680.html"

NEW_SOURCES = [
    {
        "municipality_id": MID, "source_id": "S-M068-03", "資料名": "燃やせるごみ・資源ごみ・埋立ごみ・使用済乾電池",
        "資料種別": "自治体公式Webページ", "公式URL": URL03, "発行主体": "倉敷市", "対象年度": "令和8年度",
        "ページ更新日": "2026-02-20", "取得確認日": CHECKED,
        "使用した情報": "真備地区以外の燃やせるごみ・資源ごみ・埋立ごみ・使用済乾電池、缶・びん・古紙・紙パック・PET・電球等の条件。",
        "優先度": "1", "現行性": "現行", "備考": "真備地区以外の固定10・補助5の主根拠。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M068-04", "資料名": "ごみの分別区分と出し方（あ～そ）",
        "資料種別": "自治体公式Webページ", "公式URL": URL04, "発行主体": "倉敷市", "対象年度": "現行",
        "ページ更新日": "2025-03-12", "取得確認日": CHECKED,
        "使用した情報": "空き缶・空きびん・紙パック・プラスチック製キャップ等の品目別条件。",
        "優先度": "1", "現行性": "現行", "備考": "品目別条件の補強証拠。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M068-05", "資料名": "ごみの分別区分と出し方（た～わ）",
        "資料種別": "自治体公式Webページ", "公式URL": URL05, "発行主体": "倉敷市", "対象年度": "現行",
        "ページ更新日": "2026-03-04", "取得確認日": CHECKED,
        "使用した情報": "トレイ、使い捨てライター、ペットボトル・キャップ等の品目別条件。",
        "優先度": "1", "現行性": "現行", "備考": "トレイ・ライターの直接品目根拠。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M068-06", "資料名": "ペットボトルのリサイクル",
        "資料種別": "自治体公式Webページ", "公式URL": URL06, "発行主体": "倉敷市", "対象年度": "現行",
        "ページ更新日": "2026-08-03", "取得確認日": CHECKED,
        "使用した情報": "PET1対象、キャップ・ラベル除去、水洗い、つぶす、対象外ボトルの燃える系分岐。",
        "優先度": "1", "現行性": "現行", "備考": "PET本体と付属物の現行手順。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M068-07", "資料名": "ごみステーションに出せるもの（真備地区）",
        "資料種別": "自治体公式Webページ", "公式URL": URL07, "発行主体": "倉敷市", "対象年度": "令和8年度",
        "ページ更新日": "2026-01-30", "取得確認日": CHECKED,
        "使用した情報": "真備地区の燃えるごみ・燃えないごみ・資源ごみ・体温計/乾電池と、PET・白色トレイ・古紙・びん・モバイルバッテリー等の条件。",
        "優先度": "1", "現行性": "現行", "備考": "真備地区の地域variant正本。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M068-08", "資料名": "ごみステーションでリチウムイオン充電池等の回収を開始します",
        "資料種別": "自治体公式Webページ", "公式URL": URL08, "発行主体": "倉敷市", "対象年度": "令和8年度",
        "ページ更新日": "2026-03-25", "取得確認日": CHECKED,
        "使用した情報": "2026年4月からモバイルバッテリー等を使用済み電池として回収。真備地区は従来どおり乾電池・体温計。絶縁・透明袋。",
        "優先度": "1", "現行性": "現行", "備考": "I029/I027の2026年度現行ルール。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M068-09", "資料名": "水銀を含むごみの出し方",
        "資料種別": "自治体公式Webページ", "公式URL": URL09, "発行主体": "倉敷市", "対象年度": "現行",
        "ページ更新日": "2025-02-05", "取得確認日": CHECKED,
        "使用した情報": "LED・白熱電球は埋立ごみ、真備地区は燃えないごみという地域差。",
        "優先度": "1", "現行性": "現行", "備考": "I031の地域差を直接明示。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M068-10", "資料名": "発火の危険性があるごみの出し方",
        "資料種別": "自治体公式Webページ", "公式URL": URL10, "発行主体": "倉敷市", "対象年度": "現行",
        "ページ更新日": "2026-03-16", "取得確認日": CHECKED,
        "使用した情報": "充電池の安全処理と使い捨てライター等の発火危険物への注意。",
        "優先度": "1", "現行性": "現行", "備考": "発火危険物ルールの補強証拠。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
]

NEW_CATEGORIES = [
    {
        "municipality_id": MID, "category_id": "C-M068-07", "自治体正式名称": "燃えるごみ", "category_group": "燃えるごみ",
        "parent_category_id": "", "classification_level": "PRIMARY", "表示順": "7", "collection_channel": "CURBSIDE",
        "代表品目": "生ごみ・プラスチック・ビニール製品・ゴム製品・革製品・木くず", "入れてはいけない物": "資源ごみ・燃えないごみ・電池類",
        "適用条件": "真備地区", "条件外の扱い": "真備地区以外はC-M068-01 燃やせるごみ等の現行区分に従う",
        "出す前の処理": "品目ごとの条件に従う", "袋・容器のルール": "指定ごみ袋又は透明・半透明の市販ごみ袋",
        "サイズ・条件": "45L又は20L袋に入る大きさ", "粗大ごみ扱いか": "FALSE", "予約が必要か": "FALSE", "有料か": "FALSE",
        "料金ルール": "", "自治体収集外か": "FALSE", "注意事項": "真備地区の正式区分。",
        "source_id": "S-M068-07", "出典URL": URL07, "出典ページ・該当箇所": "真備地区／燃えるごみ", "確認日": CHECKED,
        "ui_role": "SORT_BUCKET", "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
    },
    {
        "municipality_id": MID, "category_id": "C-M068-08", "自治体正式名称": "燃えないごみ", "category_group": "燃えないごみ",
        "parent_category_id": "", "classification_level": "PRIMARY", "表示順": "8", "collection_channel": "CURBSIDE",
        "代表品目": "金属類・磁器類・ガラス類・LED/白熱電球", "入れてはいけない物": "資源ごみ・電池類",
        "適用条件": "真備地区", "条件外の扱い": "真備地区以外の該当品は埋立ごみ等の現行区分に従う",
        "出す前の処理": "危険物は安全に扱い品目ごとの条件に従う", "袋・容器のルール": "指定ごみ袋又は透明・半透明の市販ごみ袋",
        "サイズ・条件": "45L又は20L袋に入る大きさ", "粗大ごみ扱いか": "FALSE", "予約が必要か": "FALSE", "有料か": "FALSE",
        "料金ルール": "", "自治体収集外か": "FALSE", "注意事項": "真備地区の正式区分。",
        "source_id": "S-M068-07", "出典URL": URL07, "出典ページ・該当箇所": "真備地区／燃えないごみ", "確認日": CHECKED,
        "ui_role": "SORT_BUCKET", "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
    },
    {
        "municipality_id": MID, "category_id": "C-M068-09", "自治体正式名称": "体温計・乾電池", "category_group": "体温計・乾電池",
        "parent_category_id": "", "classification_level": "PRIMARY", "表示順": "9", "collection_channel": "CURBSIDE",
        "代表品目": "水銀体温計・乾電池・モバイルバッテリー等の充電式電池", "入れてはいけない物": "電子体温計",
        "適用条件": "真備地区", "条件外の扱い": "真備地区以外は使用済み乾電池等の現行回収区分に従う",
        "出す前の処理": "ボタン電池・角型電池は絶縁。充電池は安全処理する", "袋・容器のルール": "ごみステーション内の所定の収集箱",
        "サイズ・条件": "対象電池類", "粗大ごみ扱いか": "FALSE", "予約が必要か": "FALSE", "有料か": "FALSE",
        "料金ルール": "", "自治体収集外か": "FALSE", "注意事項": "真備地区は充電式電池もこの区分。",
        "source_id": "S-M068-07", "出典URL": URL07, "出典ページ・該当箇所": "真備地区／体温計 乾電池", "確認日": CHECKED,
        "ui_role": "SORT_BUCKET", "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
    },
]

GROUP_ROWS = [
    {"lesson_variant_group_id": "LV-M068-01", "municipality_id": MID, "display_name": "真備地区以外", "learner_selection_required": "TRUE", "display_order": "1", "readiness_status": "LESSON_READY_10", "note": "燃やせるごみ・埋立ごみ・使用済み乾電池体系。固定10の白色トレイ・電球・電池等が真備地区と異なる。"},
    {"lesson_variant_group_id": "LV-M068-02", "municipality_id": MID, "display_name": "真備地区", "learner_selection_required": "TRUE", "display_order": "2", "readiness_status": "LESSON_READY_10", "note": "燃えるごみ・燃えないごみ・資源ごみ・体温計/乾電池体系。"},
]

DISTRICT_ROWS = [
    {
        "district_scope_id": "DS-M068-01", "municipality_id": MID, "district_name": "真備地区以外", "lesson_variant_group_id": "LV-M068-01",
        "display_order": "1", "learner_visible": "FALSE", "official_source_id": "S-M068-03", "official_url": URL03,
        "official_locator": "燃やせるごみ・資源ごみ・埋立ごみ・使用済乾電池（真備地区以外）",
        "fixed_10_answer_set_id": "M068-FIXED10-NON-MABI", "fixed_10_confirmation_status": "CONFIRMED", "i031_answer_family": "埋立ごみ",
        "i031_evidence_source_id": "S-M068-09", "i031_evidence_url": URL09, "i031_evidence_locator": "LED・白熱電球は埋立ごみ（真備地区は燃えないごみ）",
        "note": "固定10の地域別正答セットを公式資料で確認。",
    },
    {
        "district_scope_id": "DS-M068-02", "municipality_id": MID, "district_name": "真備地区", "lesson_variant_group_id": "LV-M068-02",
        "display_order": "2", "learner_visible": "FALSE", "official_source_id": "S-M068-07", "official_url": URL07,
        "official_locator": "真備地区／燃えるごみ・燃えないごみ・資源ごみ・体温計 乾電池",
        "fixed_10_answer_set_id": "M068-FIXED10-MABI", "fixed_10_confirmation_status": "CONFIRMED", "i031_answer_family": "燃えないごみ",
        "i031_evidence_source_id": "S-M068-09", "i031_evidence_url": URL09, "i031_evidence_locator": "LED・白熱電球は埋立ごみ（真備地区は燃えないごみ）",
        "note": "固定10の地域別正答セットを公式資料で確認。",
    },
]

ANSWERS = {
    "LV-M068-01": {
        "I001": ("C-M068-02", "資源ごみ"), "I004": ("C-M068-02", "資源ごみ"), "I006": ("C-M068-02", "資源ごみ"),
        "I007": ("C-M068-01", "燃やせるごみ"), "I013": ("C-M068-02", "資源ごみ"), "I014": ("C-M068-02", "資源ごみ"),
        "I017": ("C-M068-02", "資源ごみ"), "I029": ("C-M068-04", "使用済み乾電池"), "I031": ("C-M068-03", "埋立ごみ"),
        "I033": ("C-M068-01", "燃やせるごみ"),
    },
    "LV-M068-02": {
        "I001": ("C-M068-02", "資源ごみ"), "I004": ("C-M068-02", "資源ごみ"), "I006": ("C-M068-02", "資源ごみ"),
        "I007": ("C-M068-02", "資源ごみ"), "I013": ("C-M068-02", "資源ごみ"), "I014": ("C-M068-02", "資源ごみ"),
        "I017": ("C-M068-02", "資源ごみ"), "I029": ("C-M068-09", "体温計・乾電池"), "I031": ("C-M068-08", "燃えないごみ"),
        "I033": ("C-M068-07", "燃えるごみ"),
    },
}

VARIANT_ITEM = {
    "LV-M068-01": {
        "I001": ("PET1表示の通常のペットボトル", "キャップ・ラベルを外し水洗いしてつぶす", "対象外PETは燃やせるごみ", "S-M068-06", URL06, "PETボトルの出し方"),
        "I004": ("飲料・食品用アルミ缶", "中身を空にし水洗いする", "スプレー缶は別手順", "S-M068-03", URL03, "資源ごみ／空き缶・金属類"),
        "I006": ("通常の空きびん", "キャップを外し水洗いする", "耐熱・乳白色等は埋立ごみ", "S-M068-03", URL03, "資源ごみ／空きびん"),
        "I007": ("白色食品トレー", "内容物を除く", "店頭回収への協力も可", "S-M068-05", URL05, "50音順『トレイ』燃やせるごみ"),
        "I013": ("新聞・折込広告", "ひもで十文字に縛る", "再生不適紙は公式案内を確認", "S-M068-03", URL03, "資源ごみ／古紙類／新聞"),
        "I014": ("ダンボール", "折りたたみひもで十文字に縛る", "再生不適紙は公式案内を確認", "S-M068-03", URL03, "資源ごみ／古紙類／ダンボール"),
        "I017": ("500ml以上の通常紙パック", "洗って開いて乾かし縛る", "500ml未満・内側アルミは燃やせるごみ", "S-M068-03", URL03, "資源ごみ／古紙類／紙パック"),
        "I029": ("取り外したモバイルバッテリー", "使い切り端子を絶縁し透明袋へ", "電池を外せない製品は粗大ごみ等", "S-M068-08", URL08, "令和8年4月から使用済み電池"),
        "I031": ("LED・白熱電球", "割れないよう扱う", "蛍光管は資源ごみ", "S-M068-09", URL09, "LED・白熱電球は埋立ごみ"),
        "I033": ("中身を使い切った使い捨てライター", "安全にガスを抜く", "中身が残る場合は公式案内を確認", "S-M068-05", URL05, "使い捨てライター／燃やせるごみ"),
    },
    "LV-M068-02": {
        "I001": ("PET1表示の通常のペットボトル", "キャップ・ラベルを外し水洗いしてつぶす", "対象外PETは燃えるごみ", "S-M068-07", URL07, "真備地区／資源ごみ／ペットボトル"),
        "I004": ("飲料・食品用アルミ缶", "中身を空にし水洗いする", "スプレー缶は別手順", "S-M068-07", URL07, "真備地区／資源ごみ／空き缶"),
        "I006": ("通常の空きびん", "キャップを外し水洗いする", "耐熱・乳白色等は燃えないごみ", "S-M068-07", URL07, "真備地区／資源ごみ／空きびん"),
        "I007": ("食品用白色トレイ", "水洗いし乾かす", "色付き・カップ麺・弁当容器は対象外", "S-M068-07", URL07, "真備地区／資源ごみ／白色トレイ"),
        "I013": ("新聞・折込広告", "ひもで十文字に縛る", "再生不適紙は公式案内を確認", "S-M068-07", URL07, "真備地区／資源ごみ／古紙／新聞"),
        "I014": ("ダンボール", "折りたたみひもで十文字に縛る", "再生不適紙は公式案内を確認", "S-M068-07", URL07, "真備地区／資源ごみ／古紙／ダンボール"),
        "I017": ("500ml以上の通常紙パック", "洗って開いて乾かし縛る", "500ml未満等は燃えるごみ", "S-M068-07", URL07, "真備地区／資源ごみ／古紙／紙パック"),
        "I029": ("取り外したモバイルバッテリー", "端子を絶縁し所定収集箱へ", "電池を外せない製品は粗大ごみ等", "S-M068-07", URL07, "真備地区／体温計 乾電池"),
        "I031": ("LED・白熱電球", "割れないよう扱う", "蛍光管は資源ごみ", "S-M068-09", URL09, "真備地区は燃えないごみ"),
        "I033": ("中身を使い切った使い捨てライター", "安全にガスを抜く", "中身が残る場合は公式案内を確認", "S-M068-07", URL07, "真備地区／燃えるごみ＋品目別ライター規則"),
    },
}


def replace_mid(path: Path, new_rows: list[dict[str, str]], *, mid_field: str = "municipality_id") -> None:
    fields, rows = read_csv(path)
    rows = [row for row in rows if row.get(mid_field) != MID] + new_rows
    if mid_field == "municipality_id":
        rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("category_id", row.get("source_id", row.get("internal_item_id", "")))))
    write_csv(path, fields, rows)


def upsert_sources(path: Path) -> None:
    fields, rows = read_csv(path)
    source_ids = {row["source_id"] for row in NEW_SOURCES}
    rows = [row for row in rows if not (row.get("municipality_id") == MID and row.get("source_id") in source_ids)]
    rows.extend(dict(row) for row in NEW_SOURCES)
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("source_id", "")))
    write_csv(path, fields, rows)


def upsert_categories(path: Path) -> None:
    fields, rows = read_csv(path)
    new_ids = {row["category_id"] for row in NEW_CATEGORIES}
    for row in rows:
        if row.get("municipality_id") != MID:
            continue
        cid = row.get("category_id")
        if cid == "C-M068-01":
            row.update({"適用条件": "真備地区以外", "条件外の扱い": "真備地区はC-M068-07 燃えるごみ", "確認日": CHECKED})
        elif cid == "C-M068-02":
            row.update({"適用条件": "市内（品目・排出方法は地域別公式資料に従う）", "確認日": CHECKED})
        elif cid == "C-M068-03":
            row.update({"適用条件": "真備地区以外", "条件外の扱い": "真備地区の該当品はC-M068-08 燃えないごみ", "確認日": CHECKED})
        elif cid == "C-M068-04":
            row.update({"適用条件": "真備地区以外", "条件外の扱い": "真備地区はC-M068-09 体温計・乾電池", "代表品目": "乾電池・モバイルバッテリー等の対象使用済み電池", "確認日": CHECKED})
    rows = [row for row in rows if not (row.get("municipality_id") == MID and row.get("category_id") in new_ids)]
    rows.extend(dict(row) for row in NEW_CATEGORIES)
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("category_id", "")))
    write_csv(path, fields, rows)


def refresh_initial_mapping_layer() -> None:
    """Refresh only M068 category-derived initial mappings and coverage.

    The new M068 regional categories create legitimate automatic candidates for
    non-lesson items. Reconcile only M068 so unrelated municipalities and their
    manually reviewed coverage remain byte-for-byte untouched.
    """
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


def sync_category_evidence(path: Path) -> None:
    fields, rows = read_csv(path)
    evidence_id = "CRE-M068-03"
    rows = [row for row in rows if row.get("review_evidence_id") != evidence_id]
    rows.append({
        "review_evidence_id": evidence_id, "review_id": "CR-M068-CATEGORY-COVERAGE", "municipality_id": MID,
        "source_id": "S-M068-07", "locator": "真備地区の燃えるごみ・燃えないごみ・資源ごみ・体温計 乾電池",
        "evidence_role": "SUPPLEMENTAL_INDEX", "notes": "2026-09-15 地域variant再監査。真備地区固有の正式区分をcanonicalへ追加。",
    })
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("review_evidence_id", "")))
    write_csv(path, fields, rows)


def validate_review() -> list[dict[str, str]]:
    _, rows = read_csv(REVIEW)
    if {row.get("internal_item_id") for row in rows} != set(FIXED):
        raise ValueError("M068 fixed review must contain exactly fixed10 item IDs")
    if len(rows) != 20 or any(row.get("branch_review_status") != "COMPLETE" for row in rows):
        raise ValueError("M068 fixed review must contain 20 COMPLETE branches")
    if any(row.get("scoring_branch") != "FALSE" for row in rows):
        raise ValueError("M068 regional review must not invent municipality-wide scoring")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["internal_item_id"]].append(row)
    for iid, branches in grouped.items():
        orders = sorted(int(row["branch_order"]) for row in branches)
        if orders != list(range(1, len(branches) + 1)):
            raise ValueError(f"M068 {iid} branch order is not contiguous")
    _, supplemental = read_csv(SUPPLEMENTAL)
    if {row.get("internal_item_id") for row in supplemental} != SUPP or len(supplemental) != 10:
        raise ValueError("M068 supplemental review must contain 10 branches across supplemental five")
    if any(row.get("branch_review_status") != "COMPLETE" or row.get("scoring_branch") != "FALSE" for row in supplemental):
        raise ValueError("M068 supplemental review must be COMPLETE and non-scoring")
    return rows


def source_row(source_id: str) -> dict[str, str]:
    _, rows = read_csv(SOURCES)
    return next(row for row in rows if row.get("municipality_id") == MID and row.get("source_id") == source_id)


def sync_variant_sources() -> None:
    fields, rows = read_csv(VARIANT_SOURCES)
    rows = [row for row in rows if row.get("municipality_id") != MID]
    rows.extend(source_row(source_id) for source_id in ["S-M068-03", "S-M068-04", "S-M068-05", "S-M068-06", "S-M068-07", "S-M068-08", "S-M068-09"])
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("source_id", "")))
    write_csv(VARIANT_SOURCES, fields, rows)


def build_variants() -> None:
    replace_mid(GROUPS, GROUP_ROWS)
    replace_mid(SCOPES, DISTRICT_ROWS)
    box_fields, old_boxes = read_csv(BOXES)
    old_boxes = [row for row in old_boxes if not row.get("lesson_variant_group_id", "").startswith("LV-M068-")]
    scoring_rows: list[dict[str, str]] = []
    box_rows: list[dict[str, str]] = []
    for gid in ["LV-M068-01", "LV-M068-02"]:
        unique: list[tuple[str, str]] = []
        for iid in FIXED:
            answer = ANSWERS[gid][iid]
            if answer not in unique:
                unique.append(answer)
        box_by_category: dict[str, str] = {}
        group_no = gid[-2:]
        for order, (category_id, label) in enumerate(unique, 1):
            box_id = f"TB-M068-{group_no}-ON-{order:02d}"
            box_by_category[category_id] = box_id
            box_rows.append({
                "lesson_variant_group_id": gid, "teaching_box_id": box_id, "class_mode": "ONLINE_CLASS", "box_kind": "FIXED_10_SCORING",
                "display_name": label, "display_order": str(order), "note": "固定10品目の地域別採点用", "style_source_category_ids": category_id,
                "style_district_scope": "DS-M068-01" if gid == "LV-M068-01" else "DS-M068-02",
            })
        for order, (category_id, label) in enumerate(unique, 1):
            box_rows.append({
                "lesson_variant_group_id": gid, "teaching_box_id": f"TB-M068-{group_no}-IP-{order:02d}", "class_mode": "IN_PERSON_CLASS", "box_kind": "MAJOR_CATEGORY",
                "display_name": label, "display_order": str(order), "note": "対面授業用の主要分別箱。固定10で使用する区分のみ。", "style_source_category_ids": category_id,
                "style_district_scope": "DS-M068-01" if gid == "LV-M068-01" else "DS-M068-02",
            })
        for iid in FIXED:
            condition, prep, exc, sid, url, locator = VARIANT_ITEM[gid][iid]
            category_id, _ = ANSWERS[gid][iid]
            scoring_rows.append({
                "lesson_variant_group_id": gid, "municipality_id": MID, "internal_item_id": iid, "teaching_box_id": box_by_category[category_id],
                "condition": condition, "preparation": prep, "exception_destination": exc, "evidence_source_id": sid, "evidence_url": url,
                "evidence_locator": locator, "review_status": "COMPLETE", "checked_date": CHECKED, "reviewer": REVIEWER,
                "note": "画像の通常状態を地域groupの公式正答で採点。municipality-wide採点は作らない。",
            })
    old_boxes.extend(box_rows)
    old_boxes.sort(key=lambda row: (row.get("lesson_variant_group_id", ""), row.get("class_mode", ""), int(row.get("display_order") or 999), row.get("teaching_box_id", "")))
    write_csv(BOXES, box_fields, old_boxes)
    replace_mid(SCORING, scoring_rows)


def update_scope() -> None:
    fields, rows = read_csv(SCOPE)
    rows = [row for row in rows if row.get("municipality_id") != MID]
    rows.append({
        "municipality_id": MID, "municipality_name": "倉敷市", "lesson_mode": "ONLINE_CLASS", "scoring_status": "LESSON_READY_10",
        "required_item_count": "10", "required_branch_count": "20", "review_source": "data/research/lesson_readiness/m068_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "固定10は真備地区以外/真備地区の2地域groupで採点。白色トレイ・電球・電池等の実在地域差を保持。補助5はreview済みだが15問Gate未接続。",
    })
    rows.sort(key=lambda row: row.get("municipality_id", ""))
    write_csv(SCOPE, fields, rows)


def update_company_priority() -> None:
    fields, rows = read_csv(COMPANY)
    targets = {"C029-S02", "C029-S03", "C029-S04"}
    hits = 0
    for row in rows:
        if row.get("site_id") in targets and row.get("municipality_id") == MID:
            row["lesson_variant_group_id"] = "LV-M068-01"
            row["active"] = "TRUE"
            row["checked_date"] = CHECKED
            row["identity_resolution_note"] = (
                f"{row.get('site_display_name')}の倉敷市内所在地をrouting metadataとして採用。M068はLESSON_READY_10整備済みで"
                "真備地区以外のLV-M068-01へ一意にrouting。会社所在地は居住地・家庭ごみ正答の根拠ではない。"
            )
            hits += 1
    if hits != 3:
        raise ValueError(f"expected three M068 C029 routing rows, got {hits}")
    write_csv(COMPANY, fields, rows)

    fields, rows = read_csv(PRIORITY)
    hits = 0
    for row in rows:
        if row.get("municipality_id") == MID:
            row["implementation_status"] = "IMPLEMENTED"
            row["readiness_status_snapshot"] = "LESSON_READY_10"
            row["checked_date"] = CHECKED
            row["note"] = "固定10を真備地区以外/真備地区の2地域groupでLESSON_READY_10化。C029-S02/S03/S04はroutingのみ有効化。補助5はreview済み・15問Gate未接続。"
            hits += 1
    if hits != 1:
        raise ValueError(f"priority M068 hit={hits}")
    write_csv(PRIORITY, fields, rows)


def update_municipality_qa() -> None:
    fields, rows = read_csv(MUNICIPALITIES)
    hits = 0
    for row in rows:
        if row.get("municipality_id") == MID:
            row["最終確認日"] = CHECKED
            row["備考"] = "真備地区以外の4ステーション区分＋粗大ごみに加え、真備地区固有の燃える/燃えない/体温計・乾電池を地域variantとして保持。資源ごみは共通正式名。"
            row["reviewed_category_count"] = "8"
            row["category_count_basis"] = "真備地区以外の5住民区分（燃やせる・資源・埋立・使用済み乾電池・粗大）と、真備地区固有の燃える・燃えない・体温計/乾電池の3正式区分を重複なく統合。出せないはEXCLUDED_NOTICEで件数外。"
            row["category_count_verified"] = "TRUE"
            row["category_count_check_status"] = "MANUAL_INDEX_REVIEW"
            row["category_count_review_id"] = "CR-M068-CATEGORY-COVERAGE"
            row["category_count_reviewed_date"] = CHECKED
            row["category_count_reviewed_by"] = REVIEWER
            hits += 1
    if hits != 1:
        raise ValueError(f"municipality M068 hit={hits}")
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
            row["備考"] = "2026-09-15地域再監査。真備地区固有の燃えるごみ・燃えないごみ・体温計/乾電池を追加し、固定10の地域variantを確認。"
            hits += 1
    if hits != 1:
        raise ValueError(f"QA M068 hit={hits}")
    write_csv(QA, fields, rows)


def sync_batch_from_canonical() -> None:
    pairs = [
        (SOURCES, BATCH_SOURCES), (CATEGORIES, BATCH_CATEGORIES), (MUNICIPALITIES, BATCH_MUNICIPALITIES),
        (QA, BATCH_QA), (MAPPINGS, BATCH_MAPPINGS), (COVERAGE, BATCH_COVERAGE),
        (CATEGORY_EVIDENCE, BATCH_CATEGORY_EVIDENCE),
    ]
    for canonical_path, batch_path in pairs:
        _, canonical_rows = read_csv(canonical_path)
        batch_fields, batch_rows = read_csv(batch_path)
        replacement = [dict(row) for row in canonical_rows if row.get("municipality_id") == MID]
        batch_rows = [row for row in batch_rows if row.get("municipality_id") != MID] + replacement
        batch_rows.sort(key=lambda row: (
            row.get("municipality_id", ""), row.get("category_id", row.get("source_id", row.get("internal_item_id", row.get("review_evidence_id", "")))),
            int(row.get("branch_order") or 0) if str(row.get("branch_order", "")).isdigit() else 0,
        ))
        write_csv(batch_path, batch_fields, batch_rows)


def main() -> None:
    review_rows = validate_review()
    if MID not in VARIANT_ONLY_LESSON_READY:
        raise ValueError("sync_lesson_ready_reviews.py must classify M068 as variant-only before running builder")
    upsert_sources(SOURCES)
    upsert_categories(CATEGORIES)
    refresh_initial_mapping_layer()
    sync_category_evidence(CATEGORY_EVIDENCE)
    update_municipality_qa()
    sync_variant_sources()
    build_variants()
    update_scope()
    update_company_priority()
    pairs, branches, image_updates = sync_lesson_reviews()
    if image_updates and any(row.get("municipality_id") == MID for row in read_csv(ROOT / "data/app/item_image_mapping_pilot_top8.csv")[1]):
        raise ValueError("M068 variant-only scoring leaked into municipality-wide image mapping")
    sync_batch_from_canonical()
    print(
        f"M068_LESSON_READY_BUILT review_branches={len(review_rows)} groups=2 variant_scoring=20 supplemental=10 "
        f"sync_pairs={pairs} sync_branches={branches}"
    )


if __name__ == "__main__":
    main()
