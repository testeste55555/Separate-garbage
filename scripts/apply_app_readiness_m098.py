#!/usr/bin/env python3
"""Promote M098 Onomichi to 40-item APP_READY while preserving the existing single lesson group.

The municipality-wide canonical layer keeps current official action categories as the
auditable routing vocabulary.  Regional presentation/container differences remain in
the existing district_scope / lesson_variant evidence layer and are not exposed as a
learner region selector.

2026 source precedence is deliberate: the April 2026 guidebooks override older HTML
wording when a rule changed (notably bulbs, rechargeable batteries and lighters).
"""
from __future__ import annotations

from pathlib import Path

from schema_v12 import (
    CATEGORY_FIELDS,
    CATEGORY_REVIEW_EVIDENCE_FIELDS,
    COVERAGE_FIELDS,
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
BATCH10 = RESEARCH / "batches/batch_10"
MID = "M098"
CHECKED = "2026-08-31"
REVIEWER = "OPENAI_M098_APP_READY_V1"
REVIEW_PATH = RESEARCH / "app_readiness/m098_item_review.csv"
GUIDE_LANDING_URL = "https://www.city.onomichi.hiroshima.jp/soshiki/16/44213.html"

SOURCE_SPECS = [('S-M098-01',
  'ごみ・資源物の分別方法（向島、御調、因島、瀬戸田以外の地域）',
  'https://www.city.onomichi.hiroshima.jp/soshiki/16/3029.html',
  '家庭ごみ主要区分・前処理・資源回収・有害ごみ・粗大ごみ',
  '2026-04-01',
  '現行'),
 ('S-M098-02',
  'ごみ・資源物の分別方法（向島町）',
  'https://www.city.onomichi.hiroshima.jp/soshiki/16/3020.html',
  '向島町の現行分別体系と資源回収差',
  '2026-04-01',
  '現行'),
 ('S-M098-03',
  'ごみ・資源物の分別方法（御調町地域）',
  'https://www.city.onomichi.hiroshima.jp/soshiki/16/3027.html',
  '御調町の現行分別体系・資源物',
  '2026-04-01',
  '現行'),
 ('S-M098-04',
  'ごみ分別ガイドブック（尾道市全域）',
  'https://www.city.onomichi.hiroshima.jp/soshiki/16/44213.html',
  '令和8年4月版の5地域ガイドへの現行公式導線',
  '2026-04-01',
  '現行'),
 ('S-M098-05',
  '尾道地域版 家庭ごみ分別ガイドブック 令和8年4月',
  'https://www.city.onomichi.hiroshima.jp/uploaded/attachment/57662.pdf',
  '2026年4月改定・50音表・全主要区分・特殊品目',
  '2026-04',
  '現行'),
 ('S-M098-06',
  '因島地域版 家庭ごみ分別ガイドブック 令和8年4月',
  'https://www.city.onomichi.hiroshima.jp/uploaded/attachment/57907.pdf',
  '因島地域の2026年4月改定・50音表・有害ごみ・資源物',
  '2026-04',
  '現行'),
 ('S-M098-07',
  '瀬戸田地域版 家庭ごみ分別ガイドブック 令和8年4月',
  'https://www.city.onomichi.hiroshima.jp/uploaded/attachment/57904.pdf',
  '瀬戸田地域の2026年4月改定・充電式電池・有害ごみ',
  '2026-04',
  '現行'),
 ('S-M098-08',
  '不要になったテレビ・エアコン・洗濯機・衣類乾燥機・冷蔵庫・冷凍庫の処理について',
  'https://www.city.onomichi.hiroshima.jp/soshiki/16/3032.html',
  '家電4品目の市処理不可と指定経路',
  '2025-06-24',
  '現行'),
 ('S-M098-09',
  '家庭用パソコンの処分について',
  'https://www.city.onomichi.hiroshima.jp/soshiki/16/2997.html',
  '家庭用PCのメーカー等回収と周辺機器の扱い',
  '2017-02-06',
  '現行案内中'),
 ('S-M098-10',
  'ライターはどのように出せばよいですか',
  'https://www.city.onomichi.hiroshima.jp/soshiki/16/3014.html',
  'ライターの有害ごみ・使い切り・別袋',
  '2026-04-01',
  '現行'),
 ('S-M098-11',
  '包丁やカミソリなどの刃物類はどのように出すのですか',
  'https://www.city.onomichi.hiroshima.jp/soshiki/16/3004.html',
  '包丁・刃物の保護と分別',
  '2026-04-01',
  '現行'),
 ('S-M098-12',
  '尾道市災害廃棄物処理計画',
  'https://www.city.onomichi.hiroshima.jp/uploaded/attachment/14216.pdf',
  'ボタン電池のリサイクル協力店・ボタン電池回収協力店ルートの補足',
  '2019',
  '補足参照')]


def source(spec: tuple[str, str, str, str, str, str], priority: int) -> dict[str, str]:
    source_id, title, url, used, updated, currency = spec
    return {
        "municipality_id": MID,
        "source_id": source_id,
        "資料名": title,
        "資料種別": "自治体公式PDF" if url.lower().endswith(".pdf") else "自治体公式Webページ",
        "公式URL": url,
        "発行主体": "尾道市",
        "対象年度": "令和8年度／取得時点現行" if source_id != "S-M098-12" else "市公式継続資料",
        "ページ更新日": updated,
        "取得確認日": CHECKED,
        "使用した情報": used,
        "優先度": str(priority),
        "現行性": currency,
        "備考": (
            "M098 APP_READYの教材正答再現・監査に使用。"
            if source_id != "S-M098-12"
            else "2026年版日常ガイドにボタン電池の独立行がないため、乾電池へ推測統合せず、市公式計画が明記する回収協力店ルートのみを内部補足として保持。"
        ),
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": GUIDE_LANDING_URL if source_id in {"S-M098-05", "S-M098-06", "S-M098-07"} else "",
    }


SOURCES = [source(spec, index) for index, spec in enumerate(SOURCE_SPECS, 1)]
SOURCE_BY_ID = {row["source_id"]: row for row in SOURCES}


def category(
    category_id: str,
    name: str,
    order: int,
    representative: str,
    source_id: str,
    locator: str,
    *,
    ui_role: str = "SORT_BUCKET",
    channel: str = "CURBSIDE",
    excluded: str = "FALSE",
    condition: str = "家庭から出る対象品",
    outside: str = "他の公式区分又は指定回収経路を確認",
    prep: str = "品目別の公式出し方に従う",
    bag: str = "地域別の公式出し方に従う",
    size: str = "品目別条件に従う",
    bulky: str = "FALSE",
    paid: str = "FALSE",
    fee: str = "",
    note: str = "",
) -> dict[str, str]:
    src = SOURCE_BY_ID[source_id]
    return {
        "municipality_id": MID,
        "category_id": category_id,
        "自治体正式名称": name,
        "category_group": name,
        "parent_category_id": "",
        "classification_level": "PRIMARY",
        "表示順": str(order),
        "collection_channel": channel,
        "代表品目": representative,
        "入れてはいけない物": "他の公式分別区分・指定回収経路に該当する物",
        "適用条件": condition,
        "条件外の扱い": outside,
        "出す前の処理": prep,
        "袋・容器のルール": bag,
        "サイズ・条件": size,
        "粗大ごみ扱いか": bulky,
        "予約が必要か": "CONDITIONAL" if category_id == "C-M098-07" else "FALSE",
        "有料か": paid,
        "料金ルール": fee,
        "自治体収集外か": excluded,
        "注意事項": note or "地域ごとの容器・資源物細分はdistrict_scope / lesson evidenceで保持する。",
        "source_id": source_id,
        "出典URL": src["公式URL"],
        "出典ページ・該当箇所": locator,
        "確認日": CHECKED,
        "ui_role": ui_role,
        "rule_status": "CURRENT",
        "effective_from": "2026-04-01" if category_id in {"C-M098-06"} else "",
        "effective_to": "",
    }


CATEGORIES = [
    category("C-M098-01", "もやせるごみ", 1, "生ごみ・紙くず・小さい草木・汚れた資源対象外品", "S-M098-01", "『もやせるごみ』", prep="生ごみは水切りし、草木は長さ50cm以下・直径10cm以下等の条件に従う", bag="透明または半透明袋", size="草木類は長さ50cm以下・直径10cm以下"),
    category("C-M098-02", "容器包装プラスチック", 2, "プラマーク付きの洗浄可能な容器・袋・包装", "S-M098-01", "『容器包装プラスチック』", prep="中身を使い切り、洗って汚れを落とす", bag="透明袋"),
    category("C-M098-03", "もやせないごみ", 3, "金属類・小型電気製品・その他プラスチック・傘・ふとん等", "S-M098-01", "『もやせないごみ（金属類、小型電気製品、その他プラスチック）』", prep="電池は外す。刃物等は安全に包む。ふとん等は十文字にしばる", bag="透明袋又は品目別の指定"),
    category("C-M098-04", "ペットボトル", 4, "PETマーク付き飲料・酒類・しょう油等のボトル", "S-M098-01", "『ペットボトル』", prep="ふた・ラベルを外し、簡単に水洗いし、つぶさない", bag="透明袋"),
    category("C-M098-05", "埋立ごみ等", 5, "陶磁器類・割れたガラス・焼却灰・練炭灰", "S-M098-01", "『埋立ごみ等』", prep="割れ物は箱等へ入れて内容物を明記。灰は完全燃焼・異物除去等の指定に従う", bag="箱・土のう袋等、品目別の指定"),
    category("C-M098-06", "有害ごみ", 6, "蛍光灯・電球・LED・乾電池・充電式電池・内蔵電池製品・ライター等", "S-M098-01", "『有害ごみ』", prep="種類ごとに分け、蛍光灯等は割らず、電池・ライター類は別袋", bag="種類ごとの透明袋又は購入時の箱", note="2026年4月1日新設。旧HTML表記より令和8年4月版ガイドを優先。"),
    category("C-M098-07", "粗大ごみ（有料）", 7, "ソファー・たんす・机・自転車等の1辺50cm超", "S-M098-01", "『粗大ごみ（有料）』", ui_role="REFERENCE_ONLY", channel="DIRECT_HAUL", prep="直接持込又は事前申込による有料個別収集の手続に従う", bag="ごみステーションへ出さない", size="原則1辺50cm超", bulky="TRUE", paid="TRUE", fee="品目ごとの処理手数料"),
    category("C-M098-08", "資源回収", 8, "紙類・布類・缶・びん・スプレー缶・天ぷら油", "S-M098-01", "『資源回収』", prep="紙・布・缶・びん・油等を地域の正式な資源区分と容器に従って分ける", bag="資源物専用ステーション・専用網袋・コンテナ等、地域別指定", note="地域により『資源物』『かん・びん』『古紙類』等の正式表示・容器が異なる。詳細は既存district_scopeに保持。"),
    category("C-M098-09", "尾道市では処理できないもの", 9, "家電リサイクル4品目・家庭用パソコン等", "S-M098-05", "8～9頁『尾道市では処理できないもの』", ui_role="EXCLUDED_NOTICE", channel="EXTERNAL", excluded="TRUE", prep="販売店・メーカー・指定引取場所等の公式経路を利用", bag="ごみステーションへ出さない", note="通常の尾道市収集・クリーンセンター処理対象外。"),
    category("C-M098-10", "ボタン電池回収協力店", 10, "使用済みボタン電池", "S-M098-12", "表2.2.11(b)『ボタン電池回収協力店による回収』", ui_role="REFERENCE_ONLY", channel="RETAIL_TAKEBACK", excluded="TRUE", prep="端子を絶縁し回収協力店等へ持ち込む", bag="市の通常ごみ袋へ推測投入しない", note="2026年版日常ガイドに独立行がないため、教材UIには出さず内部回収経路としてのみ保持。"),
]
CATEGORY_BY_ID = {row["category_id"]: row for row in CATEGORIES}

MUNICIPALITY = {
    "municipality_id": MID,
    "都道府県": "広島県",
    "市町村": "尾道市",
    "実装区分": "中国5県全市町村",
    "ごみ処理主体": "尾道市",
    "自治体ごみトップURL": "https://www.city.onomichi.hiroshima.jp/life/1/9/43/",
    "分別ガイドURL": GUIDE_LANDING_URL,
    "品目検索URL": "",
    "やさしい日本語URL": "",
    "多言語資料URL": "https://www.city.onomichi.hiroshima.jp/life/1/9/43/",
    "対象年度": "令和8年度",
    "最終確認日": CHECKED,
    "確認ステータス": "QA_REQUIRED",
    "備考": "令和8年4月改定を採用。5地域のCURRENT資料を照合し、canonicalは教材正答を再現できる市共通行動層、地域別の資源物表示・容器差は既存district_scope/LV-M098-01に保持。",
    "official_category_count": "",
    "reviewed_category_count": "9",
    "category_count_basis": "2026年4月現行資料で主要8行動区分を全地域横断確認し、ボタン電池回収協力店をREFERENCE_ONLY 1葉として補足。EXCLUDED_NOTICEは件数外。地域別資源物の細分はdistrict_scopeへ保持し二重計上しない。",
    "category_count_verified": "TRUE",
    "category_count_check_status": "MANUAL_INDEX_REVIEW",
    "category_count_review_id": "CR-M098-CATEGORY-COVERAGE",
    "category_count_reviewed_date": CHECKED,
    "category_count_reviewed_by": REVIEWER,
    "search_service_check_status": "NOT_CHECKED",
    "search_service_check_evidence": "",
    "easy_japanese_check_status": "NOT_CHECKED",
    "easy_japanese_check_evidence": "",
    "multilingual_check_status": "NOT_CHECKED",
    "multilingual_check_evidence": "",
}

CATEGORY_REVIEW = [
    {"review_evidence_id": "CRE-M098-S-M098-01", "review_id": "CR-M098-CATEGORY-COVERAGE", "municipality_id": MID, "source_id": "S-M098-01", "locator": "2026-04-01現行：主要8区分・資源回収・有害ごみ", "evidence_role": "PRIMARY_INDEX", "notes": "尾道・向島御調因島瀬戸田以外の現行主要区分を基準インデックスとして確認。"},
    {"review_evidence_id": "CRE-M098-S-M098-02", "review_id": "CR-M098-CATEGORY-COVERAGE", "municipality_id": MID, "source_id": "S-M098-02", "locator": "2026-04-01現行：向島町の主要区分・資源回収", "evidence_role": "SUPPLEMENTAL_INDEX", "notes": "向島町で固定10および主要行動先の互換性を確認。"},
    {"review_evidence_id": "CRE-M098-S-M098-03", "review_id": "CR-M098-CATEGORY-COVERAGE", "municipality_id": MID, "source_id": "S-M098-03", "locator": "2026-04-01現行：御調町の主要区分・資源物", "evidence_role": "SUPPLEMENTAL_INDEX", "notes": "御調町の資源物表記差をdistrict evidenceへ保持。"},
    {"review_evidence_id": "CRE-M098-S-M098-06", "review_id": "CR-M098-CATEGORY-COVERAGE", "municipality_id": MID, "source_id": "S-M098-06", "locator": "令和8年4月版：因島地域の全主要区分・50音表", "evidence_role": "SUPPLEMENTAL_INDEX", "notes": "旧HTMLの電球表記を採用せず、2026年4月版を優先。"},
    {"review_evidence_id": "CRE-M098-S-M098-07", "review_id": "CR-M098-CATEGORY-COVERAGE", "municipality_id": MID, "source_id": "S-M098-07", "locator": "令和8年4月版：瀬戸田地域の主要区分・充電式電池", "evidence_role": "SUPPLEMENTAL_INDEX", "notes": "瀬戸田地域の現行有害ごみ・資源物経路を確認。"},
]

RULES = {'I001': [{'category_id': 'C-M098-04', 'official_item_wording': 'ペットボトル', 'condition': 'PETマークのある飲料・酒類・しょう油等のボトルで、中を洗えるもの', 'preparation': 'ふたとラベルを外し、中を簡単に水洗いし、つぶさずに出す', 'exception_destination': '油・ソース等で汚れが落ちないものはもやせるごみ', 'source_id': 'S-M098-05', 'locator': "50音表『ペットボトル』／4頁ペットボトル", 'evidence_basis': 'DIRECT_ITEM'}, {'category_id': 'C-M098-01', 'official_item_wording': '汚れたペットボトル', 'condition': 'PETボトルでも油・ソース等で汚れが落ちず資源化できないもの', 'preparation': '中身を使い切る', 'exception_destination': '洗えるPETマーク品はペットボトル', 'source_id': 'S-M098-05', 'locator': '4頁：油・ソース等の容器や汚れたPETはもやせるごみ', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I002': [{'category_id': 'C-M098-02', 'official_item_wording': 'ペットボトルのふた', 'condition': 'PETボトルから外したプラスチック製キャップ', 'preparation': 'ボトルから外す', 'exception_destination': '金属製のふたは地域の資源物ルールを確認', 'source_id': 'S-M098-01', 'locator': 'ペットボトル：ふた（プラスチック）は容器包装プラスチック', 'evidence_basis': 'DIRECT_ITEM'}],
 'I003': [{'category_id': 'C-M098-02', 'official_item_wording': 'ペットボトルのラベル', 'condition': 'PETボトルから外したプラスチック製ラベル', 'preparation': 'ボトルから外す', 'exception_destination': '材質が異なるものは品目別に確認', 'source_id': 'S-M098-01', 'locator': 'ペットボトル：ラベルは容器包装プラスチック', 'evidence_basis': 'DIRECT_ITEM'}],
 'I004': [{'category_id': 'C-M098-08', 'official_item_wording': 'アルミ缶', 'condition': 'アルミ缶マークのある家庭用飲料・食品缶', 'preparation': '中を簡単に洗う', 'exception_destination': '一斗缶等の対象外缶はもやせないごみ等を確認', 'source_id': 'S-M098-01', 'locator': '資源回収 4.アルミ缶', 'evidence_basis': 'DIRECT_ITEM'}],
 'I005': [{'category_id': 'C-M098-08', 'official_item_wording': 'スチール缶', 'condition': 'スチール缶マークのある家庭用飲料・食品缶', 'preparation': '中を簡単に洗う', 'exception_destination': '一斗缶等の対象外缶はもやせないごみ等を確認', 'source_id': 'S-M098-01', 'locator': '資源回収 3.スチール缶', 'evidence_basis': 'DIRECT_ITEM'}],
 'I006': [{'category_id': 'C-M098-08', 'official_item_wording': 'ガラスびん', 'condition': '飲料・食品等の資源対象びん', 'preparation': 'ふたを外し、中を簡単に洗う', 'exception_destination': 'ガラスコップ・板ガラス・割れたびん等は埋立ごみ等', 'source_id': 'S-M098-01', 'locator': '資源回収 6.生きびん／7.駄びん', 'evidence_basis': 'DIRECT_ITEM'}, {'category_id': 'C-M098-05', 'official_item_wording': '割れたびん・資源対象外のガラス', 'condition': '割れたびん又は資源びんではないガラス製品', 'preparation': 'ダンボール箱等へ入れ、内容物を明記する', 'exception_destination': '割れていない資源対象びんは資源回収', 'source_id': 'S-M098-01', 'locator': '埋立ごみ等：陶磁器類・割れたガラス', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I007': [{'category_id': 'C-M098-02', 'official_item_wording': '白色食品トレー', 'condition': 'プラマークがあり、洗って汚れを落とせる白色食品トレー', 'preparation': '中身を使い切って洗う', 'exception_destination': '汚れが落ちないものはもやせるごみ', 'source_id': 'S-M098-05', 'locator': '5頁 容器包装プラスチック：食品トレー等', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}, {'category_id': 'C-M098-01', 'official_item_wording': '汚れた食品トレー', 'condition': '白色食品トレーでも中身・汚れが残り資源化できないもの', 'preparation': '固形物を除く', 'exception_destination': '洗浄できるプラマーク品は容器包装プラスチック', 'source_id': 'S-M098-01', 'locator': '容器包装プラスチック：汚れたまま出さない／もやせるごみ一般則', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I008': [{'category_id': 'C-M098-02', 'official_item_wording': '色柄付き食品トレー', 'condition': 'プラマークがあり、洗って汚れを落とせる色柄付き食品トレー', 'preparation': '中身を使い切って洗う', 'exception_destination': '汚れが落ちないものはもやせるごみ', 'source_id': 'S-M098-05', 'locator': '5頁 容器包装プラスチック：トレー類', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}, {'category_id': 'C-M098-01', 'official_item_wording': '汚れた色柄付き食品トレー', 'condition': '汚れが落ちない又は容器包装プラ対象外のもの', 'preparation': '固形物を除く', 'exception_destination': '洗浄できるプラマーク品は容器包装プラスチック', 'source_id': 'S-M098-01', 'locator': '容器包装プラスチック条件からの分岐', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I009': [{'category_id': 'C-M098-02', 'official_item_wording': '弁当容器（プラスチック製）', 'condition': 'プラマークがあり、洗って汚れを落とせるプラスチック製弁当容器', 'preparation': '中身を使い切って洗う', 'exception_destination': '汚れが落ちないものはもやせるごみ', 'source_id': 'S-M098-05', 'locator': '5頁 容器包装プラスチック：弁当等の容器包装', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}, {'category_id': 'C-M098-01', 'official_item_wording': '汚れた弁当容器', 'condition': 'プラスチック製でも汚れが落ちない又は対象外のもの', 'preparation': '中身を除く', 'exception_destination': '洗浄できるプラマーク品は容器包装プラスチック', 'source_id': 'S-M098-01', 'locator': '容器包装プラスチック条件からの分岐', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I010': [{'category_id': 'C-M098-02', 'official_item_wording': 'お菓子の袋（プラスチック製）', 'condition': 'プラマークがあり中身を空にしたプラスチック製菓子袋', 'preparation': '中身を空にする', 'exception_destination': '紙製・汚れたものはもやせるごみ', 'source_id': 'S-M098-05', 'locator': '5頁 容器包装プラスチック：袋・包装類', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}, {'category_id': 'C-M098-01', 'official_item_wording': '紙製又は汚れた菓子袋', 'condition': '紙製、プラマークなし、又は汚れが残る菓子袋', 'preparation': '中身を空にする', 'exception_destination': '清潔なプラマーク付き袋は容器包装プラスチック', 'source_id': 'S-M098-01', 'locator': 'もやせるごみ／容器包装プラスチック条件', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I011': [{'category_id': 'C-M098-02', 'official_item_wording': 'レジ袋', 'condition': 'プラマークのある家庭用レジ袋', 'preparation': '中身を空にする', 'exception_destination': '著しく汚れたものはもやせるごみ', 'source_id': 'S-M098-01', 'locator': '容器包装プラスチック 例：レジ袋', 'evidence_basis': 'DIRECT_ITEM'}],
 'I012': [{'category_id': 'C-M098-02', 'official_item_wording': '発泡スチロール製容器包装', 'condition': '容器包装として使われた発泡スチロールで汚れを落とせるもの', 'preparation': '汚れを落とす', 'exception_destination': '劣化・汚れ・容器包装以外はもやせるごみ', 'source_id': 'S-M098-06', 'locator': "50音表『発泡スチロール』／容器包装プラ", 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}, {'category_id': 'C-M098-01', 'official_item_wording': '劣化・汚れた発泡スチロール', 'condition': '汚れが落ちない又は容器包装対象外の発泡スチロール', 'preparation': '必要に応じ小さくする', 'exception_destination': '清潔な容器包装は容器包装プラスチック', 'source_id': 'S-M098-05', 'locator': '2頁：劣化した発泡スチロール等はもやせるごみ', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I013': [{'category_id': 'C-M098-08', 'official_item_wording': '新聞紙', 'condition': '家庭から出る乾いた新聞紙・チラシ', 'preparation': '紙類として十文字にしばる', 'exception_destination': '汚れた紙はもやせるごみ', 'source_id': 'S-M098-01', 'locator': "資源回収 1.紙類『新聞紙（チラシ含む）』", 'evidence_basis': 'DIRECT_ITEM'}],
 'I014': [{'category_id': 'C-M098-08', 'official_item_wording': 'ダンボール', 'condition': '家庭から出る乾いたダンボール', 'preparation': '折りたたみ、紙類として十文字にしばる', 'exception_destination': '濡れ・著しい汚れ等はもやせるごみ', 'source_id': 'S-M098-01', 'locator': "資源回収 1.紙類『ダンボール』", 'evidence_basis': 'DIRECT_ITEM'}],
 'I015': [{'category_id': 'C-M098-08', 'official_item_wording': '雑誌', 'condition': '家庭から出る乾いた雑誌・カタログ等', 'preparation': '紙類として十文字にしばる', 'exception_destination': '汚れた紙はもやせるごみ', 'source_id': 'S-M098-01', 'locator': "資源回収 1.紙類『雑誌』", 'evidence_basis': 'DIRECT_ITEM'}],
 'I016': [{'category_id': 'C-M098-08', 'official_item_wording': '雑紙・紙箱', 'condition': '菓子箱等の清潔で資源化できる紙', 'preparation': '雑誌類と一緒にまとめる', 'exception_destination': '汚れた紙・感熱紙等の対象外紙はもやせるごみ', 'source_id': 'S-M098-01', 'locator': '資源回収：お菓子の紙箱は雑誌と一緒', 'evidence_basis': 'DIRECT_ITEM'}, {'category_id': 'C-M098-01', 'official_item_wording': '資源化できない紙', 'condition': '汚れた紙・資源回収に適さない紙', 'preparation': '必要に応じ異物を除く', 'exception_destination': '清潔な紙箱・雑紙は資源回収', 'source_id': 'S-M098-05', 'locator': '50音表・もやせるごみの紙くず一般則', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I017': [{'category_id': 'C-M098-08', 'official_item_wording': '飲料用紙パック', 'condition': '内側にアルミがなく、洗って資源化できる飲料用紙パック', 'preparation': '水洗いし、開いて、紙類としてまとめる', 'exception_destination': '内側にアルミが貼ってあるものはもやせるごみ', 'source_id': 'S-M098-01', 'locator': "資源回収 1.紙類『飲料用紙パック』", 'evidence_basis': 'DIRECT_ITEM'}, {'category_id': 'C-M098-01', 'official_item_wording': '内側アルミ貼り紙パック', 'condition': '内側にアルミが貼ってある紙パック', 'preparation': '中身を空にする', 'exception_destination': 'アルミなしで洗える飲料用紙パックは資源回収', 'source_id': 'S-M098-01', 'locator': '資源回収：内側にアルミが貼ってある紙パックは燃やせるごみ', 'evidence_basis': 'DIRECT_ITEM'}],
 'I018': [{'category_id': 'C-M098-01', 'official_item_wording': '生ごみ', 'condition': '家庭から出る生ごみ', 'preparation': '水分を切る', 'exception_destination': '一度に大量の場合は直接持込等を確認', 'source_id': 'S-M098-01', 'locator': 'もやせるごみ 例：生ごみ', 'evidence_basis': 'DIRECT_ITEM'}],
 'I019': [{'category_id': 'C-M098-01', 'official_item_wording': '使用済みティッシュ', 'condition': '家庭で通常使用したティッシュ等の汚れた紙', 'preparation': 'そのままもやせるごみへ', 'exception_destination': '感染性廃棄物等は別経路', 'source_id': 'S-M098-01', 'locator': "もやせるごみ『紙くず』からの適用", 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I020': [{'category_id': 'C-M098-01', 'official_item_wording': '紙おむつ', 'condition': '家庭から出る使用済み紙おむつ', 'preparation': '汚物を取り除く', 'exception_destination': '医療系特殊品は市へ確認', 'source_id': 'S-M098-01', 'locator': 'もやせるごみ 例：紙おむつ（汚物は取り除く）', 'evidence_basis': 'DIRECT_ITEM'}],
 'I021': [{'category_id': 'C-M098-08', 'official_item_wording': '衣類', 'condition': '資源回収対象の清潔な衣類・タオル等', 'preparation': 'ひもで十文字にしばるか、地域の透明袋等の出し方に従う', 'exception_destination': '毛糸そのもの・皮革製品・下着・汚れた衣類はもやせるごみ', 'source_id': 'S-M098-01', 'locator': '資源回収 2.布類', 'evidence_basis': 'DIRECT_ITEM'}, {'category_id': 'C-M098-01', 'official_item_wording': '資源回収対象外の衣類', 'condition': '皮革製品・下着・著しく汚れた衣類等', 'preparation': '金具等を外せる場合は外す', 'exception_destination': '清潔な対象衣類は資源回収', 'source_id': 'S-M098-01', 'locator': '資源回収 2.布類の対象外はもやせるごみ', 'evidence_basis': 'DIRECT_ITEM'}],
 'I022': [{'category_id': 'C-M098-03', 'official_item_wording': '傘', 'condition': '家庭から出る通常の傘', 'preparation': '透明または半透明袋等、地域の出し方に従う', 'exception_destination': '特殊大型品は市へ確認', 'source_id': 'S-M098-01', 'locator': 'もやせないごみ 例：傘', 'evidence_basis': 'DIRECT_ITEM'}],
 'I023': [{'category_id': 'C-M098-05', 'official_item_wording': '陶磁器', 'condition': '茶わん・皿・植木鉢等の陶磁器類', 'preparation': '丈夫な箱・袋等に入れ地域の危険表示ルールに従う', 'exception_destination': '建設廃材等は収集外', 'source_id': 'S-M098-01', 'locator': '埋立ごみ等：陶磁器類', 'evidence_basis': 'DIRECT_ITEM'}],
 'I024': [{'category_id': 'C-M098-05', 'official_item_wording': 'ガラス製品', 'condition': '資源びんではないガラスコップ・板ガラス等', 'preparation': 'ダンボール箱等に入れ、内容物を明記する', 'exception_destination': '資源対象びんは資源回収', 'source_id': 'S-M098-01', 'locator': '埋立ごみ等：ガラスコップ・窓ガラス', 'evidence_basis': 'DIRECT_ITEM'}],
 'I025': [{'category_id': 'C-M098-05', 'official_item_wording': '割れたガラス', 'condition': '家庭から出る割れガラス', 'preparation': 'ダンボール箱等に入れ、内容物・危険を明記する', 'exception_destination': '資源対象の割れていないびんは資源回収', 'source_id': 'S-M098-01', 'locator': '埋立ごみ等：割れたガラス', 'evidence_basis': 'DIRECT_ITEM'}],
 'I026': [{'category_id': 'C-M098-03', 'official_item_wording': '包丁・刃物', 'condition': '家庭から出る包丁・カミソリ等の刃物', 'preparation': '刃を紙等で包み、危険が分かるようにして出す', 'exception_destination': '刃を露出させない', 'source_id': 'S-M098-11', 'locator': 'FAQ：刃物類は紙等で包んでもやせないごみ', 'evidence_basis': 'DIRECT_ITEM'}],
 'I027': [{'category_id': 'C-M098-06', 'official_item_wording': '乾電池', 'condition': '家庭用の使用済み乾電池', 'preparation': '乾電池だけを透明袋に入れ、他の種類と混ぜない', 'exception_destination': '充電式電池・ライター等は種類ごとに別袋', 'source_id': 'S-M098-01', 'locator': '有害ごみ：乾電池は乾電池だけを袋に入れる', 'evidence_basis': 'DIRECT_ITEM'}],
 'I028': [{'category_id': 'C-M098-10', 'official_item_wording': 'ボタン電池', 'condition': '家庭用の使用済みボタン電池', 'preparation': '端子を絶縁し、ボタン電池回収協力店等の回収経路を利用', 'exception_destination': '2026年版日常ガイドに独立行がないため、乾電池袋へ推測投入しない', 'source_id': 'S-M098-12', 'locator': '尾道市災害廃棄物処理計画 表2.2.11(b)：ボタン電池回収協力店による回収', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I029': [{'category_id': 'C-M098-06', 'official_item_wording': 'モバイルバッテリー', 'condition': '家庭用モバイルバッテリー。膨張・変形していないもの', 'preparation': '充電式電池として他品目と分け、透明袋で有害ごみへ', 'exception_destination': '膨張・変形したものはごみステーションへ出さず、地域指定施設へ持ち込む', 'source_id': 'S-M098-07', 'locator': '10頁：モバイルバッテリー／充電式電池は有害ごみ、膨張・変形品は持込', 'evidence_basis': 'DIRECT_ITEM'}],
 'I030': [{'category_id': 'C-M098-06', 'official_item_wording': '蛍光管', 'condition': '家庭から出る蛍光管・蛍光灯', 'preparation': '割らずに購入時の箱等に入れる', 'exception_destination': '長さ150cm超は地域指定施設へ持ち込む', 'source_id': 'S-M098-01', 'locator': '有害ごみ：蛍光灯、購入時の箱、150cm超は持込', 'evidence_basis': 'DIRECT_ITEM'}],
 'I031': [{'category_id': 'C-M098-06', 'official_item_wording': '電球・LED', 'condition': '白熱電球・LED電球等の電球類', 'preparation': '割らずに購入時の箱等に入れる', 'exception_destination': '長さ150cm超の特殊品は地域指定施設へ持ち込む', 'source_id': 'S-M098-06', 'locator': '令和8年4月版 4頁：蛍光灯・電球・LEDは有害ごみ', 'evidence_basis': 'DIRECT_ITEM'}],
 'I032': [{'category_id': 'C-M098-08', 'official_item_wording': 'スプレー缶', 'condition': '家庭から出る中身を使い切ったスプレー缶', 'preparation': '中身を使い切り、穴を開けて地域の資源回収へ出す', 'exception_destination': '中身を安全に使い切れない場合は市へ相談', 'source_id': 'S-M098-01', 'locator': '資源回収 5.スプレー缶：使い切り穴を開ける', 'evidence_basis': 'DIRECT_ITEM'}],
 'I033': [{'category_id': 'C-M098-06', 'official_item_wording': 'ガスライター', 'condition': '家庭から出る使い捨てライター等', 'preparation': '中身を使い切り、ライターだけを別の透明袋に入れる', 'exception_destination': '安全に使い切れない場合は清掃事務所へ確認', 'source_id': 'S-M098-10', 'locator': 'FAQ：ライターは有害ごみ、使い切り別袋', 'evidence_basis': 'DIRECT_ITEM'}],
 'I034': [{'category_id': 'C-M098-03', 'official_item_wording': '小型家電（電池を外せるもの）', 'condition': '家電4品目・PC等を除く家庭用小型家電で概ね50cm以下、電池を外せるもの', 'preparation': '乾電池・充電式電池を取り外す', 'exception_destination': '50cm超は粗大ごみ（有料）を確認', 'source_id': 'S-M098-05', 'locator': '50音表の小型電気製品・3頁もやせないごみ', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}, {'category_id': 'C-M098-07', 'official_item_wording': '大型の小型家電相当品', 'condition': '家電4品目等を除く家庭用電気製品で1辺50cmを超えるもの', 'preparation': '電池を外し、粗大ごみの持込・個別収集ルールに従う', 'exception_destination': '家電4品目・PCは市処理外', 'source_id': 'S-M098-01', 'locator': '粗大ごみ（有料）：1辺50cm超', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I035': [{'category_id': 'C-M098-06', 'official_item_wording': '充電式電池が取り外せない製品', 'condition': '充電式電池が製品に内蔵され、無理なく取り外せない小型製品', 'preparation': '無理に外さず、製品ごと透明袋へ。袋に入らない場合は「充電式」と表示', 'exception_destination': '膨張・変形したものはステーションへ出さず地域指定施設へ持ち込む', 'source_id': 'S-M098-07', 'locator': '10頁：充電式電池が取り外せない製品は製品ごと有害ごみ', 'evidence_basis': 'DIRECT_ITEM'}],
 'I036': [{'category_id': 'C-M098-03', 'official_item_wording': 'ふとん・毛布', 'condition': '家庭から出るふとん・毛布・カーテン等', 'preparation': 'ひもで十文字にしばって出す', 'exception_destination': '一時多量の場合は直接持込等を確認', 'source_id': 'S-M098-01', 'locator': 'もやせないごみ：ふとん・毛布・カーテンは十文字にしばる', 'evidence_basis': 'DIRECT_ITEM'}],
 'I037': [{'category_id': 'C-M098-09', 'official_item_wording': '家電リサイクル対象品', 'condition': 'テレビ、エアコン、冷蔵庫・冷凍庫、洗濯機・衣類乾燥機', 'preparation': '販売店・指定引取場所・許可業者等の公式経路を利用', 'exception_destination': '尾道市クリーンセンターでは処分できない', 'source_id': 'S-M098-08', 'locator': '家電リサイクル対象品は尾道市クリーンセンターで処分不可', 'evidence_basis': 'DIRECT_ITEM'}],
 'I038': [{'category_id': 'C-M098-09', 'official_item_wording': '家庭用パソコン', 'condition': 'パソコン本体・ディスプレイ等のPCリサイクル対象品', 'preparation': 'メーカー・PC3R等の回収経路を利用し、個人情報を消去', 'exception_destination': 'マウス・キーボード等の対象外周辺機器は50cm以下ならもやせないごみ', 'source_id': 'S-M098-09', 'locator': '家庭用パソコンはクリーンセンターで処理できずメーカー等へ', 'evidence_basis': 'DIRECT_ITEM'}],
 'I039': [{'category_id': 'C-M098-08', 'official_item_wording': '廃食油（天ぷら油）', 'condition': '家庭から出る植物性の使用済み天ぷら油で資源回収対象のもの', 'preparation': '透明のペットボトルへ入れ、しっかりキャップを締めて指定コンテナへ', 'exception_destination': '動物性油・対象外油は布等に吸わせてもやせるごみ', 'source_id': 'S-M098-01', 'locator': '資源回収 8.天ぷら油', 'evidence_basis': 'DIRECT_ITEM'}, {'category_id': 'C-M098-01', 'official_item_wording': '資源回収対象外の食用油', 'condition': '動物性油等、資源回収対象外又は回収に適さない油', 'preparation': '紙・布等に吸わせる等、漏れない状態にする', 'exception_destination': '対象となる植物性天ぷら油は資源回収', 'source_id': 'S-M098-06', 'locator': '7頁：資源回収対象外油は布等に吸わせてもやせるごみ', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}],
 'I040': [{'category_id': 'C-M098-01', 'official_item_wording': '草木類・剪定枝', 'condition': '家庭から出る長さ50cm以下・太さ直径10cm以下の草木・剪定枝', 'preparation': '指定寸法以下に切り、地域の出し方に従う', 'exception_destination': '50cm超の大型又は一時多量は直接持込・粗大ごみ等を確認', 'source_id': 'S-M098-01', 'locator': 'もやせるごみ：草木類 長さ50cm以下・直径10cm以下', 'evidence_basis': 'DIRECT_ITEM'}, {'category_id': 'C-M098-07', 'official_item_wording': '大きな剪定枝等', 'condition': '1辺50cm超で通常ステーション条件を外れる家庭の剪定枝等', 'preparation': '地域指定施設への持込又は粗大ごみの手続を確認', 'exception_destination': '建設廃材・事業系は家庭ごみ経路外', 'source_id': 'S-M098-05', 'locator': '8頁：粗大ごみ／一時多量ごみ・剪定枝の持込', 'evidence_basis': 'OFFICIAL_RULE_DERIVED'}]}

REVIEW_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "canonical_name", "display_name",
    "official_item_wording", "category_id", "category_name", "condition", "preparation",
    "exception_destination", "evidence_basis", "item_evidence_source_id", "item_evidence_url",
    "item_evidence_locator", "branch_review_status", "checked_date", "reviewer", "note",
]


def not_researched_coverage(item_id: str) -> dict[str, str]:
    return {
        "municipality_id": MID,
        "internal_item_id": item_id,
        "coverage_status": "NOT_RESEARCHED",
        "mapping_branch_count": "0",
        "branch_completeness_confirmed": "FALSE",
        "evidence_scope": "NONE",
        "item_evidence_source_id": "",
        "item_evidence_url": "",
        "item_evidence_locator": "",
        "reviewed_date": "",
        "reviewed_by": "",
        "notes": "Completed Batch 10 stores the ordinary research layer; M098 APP item evidence is canonical-only.",
    }


def ensure_registry() -> None:
    path = ROOT / "data/master/02_official_domain_registry.csv"
    fields, rows = read_csv(path)
    wanted = {
        "municipality_id": MID,
        "host": "www.city.onomichi.hiroshima.jp",
        "authority_type": "MUNICIPAL_DOMAIN",
        "authority_name": "尾道市",
        "verification_url": GUIDE_LANDING_URL,
        "verified_date": CHECKED,
        "notes": "M098 APP_READY promotion: Onomichi municipal official source host",
    }
    rows = [r for r in rows if not (r.get("municipality_id") == MID and r.get("host") == wanted["host"])] + [wanted]
    write_csv(path, fields, sorted(rows, key=lambda r: (r.get("municipality_id", ""), r.get("host", ""))))


def prepare_batch10():
    paths = {
        "municipalities": BATCH10 / "batch_10_municipalities.csv",
        "categories": BATCH10 / "batch_10_categories.csv",
        "sources": BATCH10 / "batch_10_sources.csv",
        "qa": BATCH10 / "batch_10_qa.csv",
        "mapping": BATCH10 / "batch_10_item_mapping.csv",
        "coverage": BATCH10 / "batch_10_item_coverage.csv",
        "review": BATCH10 / "batch_10_category_review_evidence.csv",
    }
    qa_rows = compute_qa([dict(MUNICIPALITY)], [dict(r) for r in CATEGORIES], [dict(r) for r in SOURCES], [dict(r) for r in CATEGORY_REVIEW], [])
    if len(qa_rows) != 1 or qa_rows[0].get("確認ステータス") != "QA_PASSED":
        raise ValueError(f"M098 ordinary research QA did not pass: {qa_rows}")
    municipality = sync_municipality_qa_status([dict(MUNICIPALITY)], qa_rows)[0]

    m_fields, municipalities = read_csv(paths["municipalities"])
    c_fields, categories = read_csv(paths["categories"])
    s_fields, source_rows = read_csv(paths["sources"])
    q_fields, qas = read_csv(paths["qa"])
    map_fields, mappings = read_csv(paths["mapping"])
    cov_fields, coverage = read_csv(paths["coverage"])
    rev_fields, reviews = read_csv(paths["review"])

    municipalities = [r for r in municipalities if r.get("municipality_id") != MID] + [municipality]
    categories = [r for r in categories if r.get("municipality_id") != MID] + [dict(r) for r in CATEGORIES]
    source_rows = [r for r in source_rows if r.get("municipality_id") != MID] + [dict(r) for r in SOURCES]
    qas = [r for r in qas if r.get("municipality_id") != MID] + qa_rows
    reviews = [r for r in reviews if r.get("municipality_id") != MID] + [dict(r) for r in CATEGORY_REVIEW]
    mappings = [r for r in mappings if r.get("municipality_id") != MID]
    coverage = [r for r in coverage if r.get("municipality_id") != MID] + [not_researched_coverage(f"I{i:03d}") for i in range(1, 41)]

    write_csv(paths["municipalities"], m_fields or MUNICIPALITY_FIELDS, sorted(municipalities, key=lambda r: r["municipality_id"]))
    write_csv(paths["categories"], c_fields or CATEGORY_FIELDS, sorted(categories, key=lambda r: (r["municipality_id"], r["category_id"])))
    write_csv(paths["sources"], s_fields or SOURCE_FIELDS, sorted(source_rows, key=lambda r: (r["municipality_id"], r["source_id"])))
    write_csv(paths["qa"], q_fields or QA_FIELDS, sorted(qas, key=lambda r: r["municipality_id"]))
    write_csv(paths["mapping"], map_fields or MAPPING_FIELDS, sorted(mappings, key=lambda r: (r.get("municipality_id", ""), r.get("mapping_id", ""))))
    write_csv(paths["coverage"], cov_fields or COVERAGE_FIELDS, sorted(coverage, key=lambda r: (r["municipality_id"], r["internal_item_id"])))
    write_csv(paths["review"], rev_fields or CATEGORY_REVIEW_EVIDENCE_FIELDS, sorted(reviews, key=lambda r: (r["municipality_id"], r["review_evidence_id"])))
    return municipality, CATEGORIES, SOURCES, qa_rows[0], CATEGORY_REVIEW


def build_app_ready_rows():
    _, items = read_csv(ROOT / "data/master/04_common_items_master.csv")
    item_by = {r["internal_item_id"]: r for r in items}
    expected = {f"I{i:03d}" for i in range(1, 41)}
    if set(RULES) != expected:
        raise ValueError(f"M098 rule scope mismatch missing={sorted(expected - set(RULES))} extra={sorted(set(RULES) - expected)}")
    mappings, coverage, review = [], [], []
    for item_id in sorted(expected):
        master = item_by[item_id]
        branches = RULES[item_id]
        for order, branch in enumerate(branches, 1):
            cat = CATEGORY_BY_ID[branch["category_id"]]
            src = SOURCE_BY_ID[branch["source_id"]]
            mapping_id = f"MAP-{MID}-{item_id}-B{order:02d}-{branch['category_id']}"
            mappings.append({
                "mapping_id": mapping_id,
                "municipality_id": MID,
                "internal_item_id": item_id,
                "branch_order": str(order),
                "自治体での品目表記": branch["official_item_wording"],
                "category_id": branch["category_id"],
                "分別区分正式名称": cat["自治体正式名称"],
                "条件": branch["condition"],
                "前処理": branch["preparation"],
                "例外分別先": branch["exception_destination"],
                "自治体収集外": cat["自治体収集外か"],
                "rule_status": cat["rule_status"],
                "effective_from": cat["effective_from"],
                "effective_to": cat["effective_to"],
                "category_source_id": cat["source_id"],
                "category_source_url": cat["出典URL"],
                "category_source_locator": cat["出典ページ・該当箇所"],
                "item_evidence_source_id": src["source_id"],
                "item_evidence_url": src["公式URL"],
                "item_evidence_locator": branch["locator"],
                "確認日": CHECKED,
                "mapping_status": "APP_READY",
                "evidence_scope": "ITEM_SPECIFIC",
                "branch_review_status": "COMPLETE",
                "reviewed_date": CHECKED,
                "reviewed_by": REVIEWER,
                "備考": "M098 40品目APP_READY。地域別表示・容器差は既存lesson variant evidenceに保持し、学習者地域選択は増やさない。",
            })
            review.append({
                "municipality_id": MID,
                "internal_item_id": item_id,
                "branch_order": str(order),
                "canonical_name": master["一般管理用名称"],
                "display_name": master["教材表示名"],
                "official_item_wording": branch["official_item_wording"],
                "category_id": branch["category_id"],
                "category_name": cat["自治体正式名称"],
                "condition": branch["condition"],
                "preparation": branch["preparation"],
                "exception_destination": branch["exception_destination"],
                "evidence_basis": branch["evidence_basis"],
                "item_evidence_source_id": src["source_id"],
                "item_evidence_url": src["公式URL"],
                "item_evidence_locator": branch["locator"],
                "branch_review_status": "COMPLETE",
                "checked_date": CHECKED,
                "reviewer": REVIEWER,
                "note": "教材UIは既存LV-M098-01の固定10投影を維持。詳細条件は教師・監査層に保持。",
            })
        first_src = SOURCE_BY_ID[branches[0]["source_id"]]
        coverage.append({
            "municipality_id": MID,
            "internal_item_id": item_id,
            "coverage_status": "APP_READY",
            "mapping_branch_count": str(len(branches)),
            "branch_completeness_confirmed": "TRUE",
            "evidence_scope": "ITEM_SPECIFIC",
            "item_evidence_source_id": first_src["source_id"],
            "item_evidence_url": first_src["公式URL"],
            "item_evidence_locator": f"M098 APP_READY review {item_id}: {len(branches)}条件枝を全件確認",
            "reviewed_date": CHECKED,
            "reviewed_by": REVIEWER,
            "notes": "全条件枝COMPLETE。",
        })
    return mappings, coverage, review


def sync_canonical(batch_municipality, batch_categories, batch_sources, batch_qa, batch_review):
    m_fields, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    c_fields, categories = read_csv(RESEARCH / "02_categories_master.csv")
    s_fields, source_rows = read_csv(RESEARCH / "03_sources_master.csv")
    q_fields, qas = read_csv(RESEARCH / "06_qa_log.csv")
    map_fields, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    cov_fields, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")
    rev_fields, reviews = read_csv(RESEARCH / "08_category_review_evidence.csv")

    municipalities = [r for r in municipalities if r.get("municipality_id") != MID] + [batch_municipality]
    categories = [r for r in categories if r.get("municipality_id") != MID] + [dict(r) for r in batch_categories]
    source_rows = [r for r in source_rows if r.get("municipality_id") != MID] + [dict(r) for r in batch_sources]
    qas = [r for r in qas if r.get("municipality_id") != MID] + [dict(batch_qa)]
    reviews = [r for r in reviews if r.get("municipality_id") != MID] + [dict(r) for r in batch_review]
    app_mappings, app_coverage, app_review = build_app_ready_rows()
    mappings = [r for r in mappings if r.get("municipality_id") != MID] + app_mappings
    coverage = [r for r in coverage if r.get("municipality_id") != MID] + app_coverage

    write_csv(RESEARCH / "04_municipalities_research.csv", m_fields or MUNICIPALITY_FIELDS, sorted(municipalities, key=lambda r: r["municipality_id"]))
    write_csv(RESEARCH / "02_categories_master.csv", c_fields or CATEGORY_FIELDS, sorted(categories, key=lambda r: (r["municipality_id"], r["category_id"])))
    write_csv(RESEARCH / "03_sources_master.csv", s_fields or SOURCE_FIELDS, sorted(source_rows, key=lambda r: (r["municipality_id"], r["source_id"])))
    write_csv(RESEARCH / "06_qa_log.csv", q_fields or QA_FIELDS, sorted(qas, key=lambda r: r["municipality_id"]))
    write_csv(RESEARCH / "05_item_mapping_master.csv", map_fields or MAPPING_FIELDS, sorted(mappings, key=lambda r: (r["municipality_id"], r["internal_item_id"], int(r.get("branch_order") or 0), r["mapping_id"])))
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", cov_fields or COVERAGE_FIELDS, sorted(coverage, key=lambda r: (r["municipality_id"], r["internal_item_id"])))
    write_csv(RESEARCH / "08_category_review_evidence.csv", rev_fields or CATEGORY_REVIEW_EVIDENCE_FIELDS, sorted(reviews, key=lambda r: (r["municipality_id"], r["review_evidence_id"])))
    write_csv(REVIEW_PATH, REVIEW_FIELDS, app_review)
    return len(app_review)


def update_application(branch_count: int) -> None:
    scope_path = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
    fields, rows = read_csv(scope_path)
    rows = [r for r in rows if r.get("municipality_id") != MID] + [{
        "municipality_id": MID,
        "municipality_name": "尾道市",
        "lesson_mode": "ONLINE_CLASS",
        "scoring_status": "APP_READY",
        "required_item_count": "40",
        "required_branch_count": str(branch_count),
        "review_source": "data/research/app_readiness/m098_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "40品目canonicalはAPP_READY。固定10画像の正誤判定は既存LV-M098-01を使用し、6 district_scopeを1教材groupのまま維持する。",
    }]
    write_csv(scope_path, fields, sorted(rows, key=lambda r: r["municipality_id"]))

    company_path = ROOT / "data/app/company_municipality_mapping.csv"
    fields, rows = read_csv(company_path)
    for row in rows:
        if row.get("municipality_id") == MID and row.get("mapping_status") == "CONFIRMED":
            row["active"] = "TRUE"
    write_csv(company_path, fields, rows)

    priority_path = ROOT / "data/master/07_implementation_priority.csv"
    fields, rows = read_csv(priority_path)
    for row in rows:
        if row.get("municipality_id") == MID:
            row["implementation_status"] = "IMPLEMENTED"
            row["readiness_status_snapshot"] = "APP_READY"
            row["checked_date"] = CHECKED
            row["note"] = "40品目APP_READY。会社紐付けはrouting metadataのみ。既存単一lesson groupを維持。"
    write_csv(priority_path, fields, rows)

    deferred_path = ROOT / "data/master/05_deferred_municipalities.csv"
    fields, rows = read_csv(deferred_path)
    rows = [r for r in rows if r.get("municipality_id") != MID]
    write_csv(deferred_path, fields, rows)


def main() -> None:
    ensure_registry()
    batch = prepare_batch10()
    branch_count = sync_canonical(*batch)
    update_application(branch_count)
    print(f"M098_APP_READY_BUILT items=40 branches={branch_count} categories={len(CATEGORIES)} sources={len(SOURCES)}")


if __name__ == "__main__":
    main()
