#!/usr/bin/env python3
"""Build M099 Fukuyama full 40-item APP_READY data without collapsing regional rules.

Evidence hierarchy:
- 2026 municipal plan: seven regular household collection divisions and Hashirijima paper exclusion.
- 2026 Utsumi calendar (327009.pdf): current Utsumi scope, five displayed regular divisions and drop-off reminder.
- Current item dictionary / dedicated official pages: item-specific branches and preparation rules.
- Existing lesson variants remain the learner-facing regional projection.

The completed Batch 10 bundle receives the ordinary municipality/category/source layer and
40 NOT_RESEARCHED coverage placeholders.  The reviewed 40-item APP_READY mappings live in
canonical, so item evidence does not weaken the completed-batch union contract.
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
    migrate_bundle,
    read_csv,
    write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data/research"
BATCH10 = RESEARCH / "batches/batch_10"
MID = "M099"
CHECKED = "2026-08-31"
REVIEWER = "OPENAI_M099_APP_READY_V1"
REVIEW_PATH = RESEARCH / "app_readiness/m099_item_review.csv"

PLAN_URL = "https://www.city.fukuyama.hiroshima.jp/uploaded/life/395517_2433553_misc.pdf"
GUIDE_LANDING_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/89267.html"
UTSUMI_GUIDE_URL = "https://www.city.fukuyama.hiroshima.jp/uploaded/attachment/273294.pdf"
NUMAKUMA_PAPER_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/314393.html"
SCHEDULE_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/390886.html"
DICTIONARY_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/314133.html"
BULB_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/1430.html"
UTSUMI_2026_URL = "https://www.city.fukuyama.hiroshima.jp/uploaded/attachment/327009.pdf"
BATTERY_WARNING_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/213349.html"
EMBEDDED_BATTERY_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/353535.html"
DROPOFF_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/388247.html"
PC_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/243721.html"
HOME_APPLIANCE_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/1452.html"
OLD_PAPER_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/1449.html"
PRUNING_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/340035.html"
PAPER_CHANGE_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/246451.html"
PET_URL = "https://www.city.fukuyama.hiroshima.jp/site/kankyo/342276.html"


def source(source_id: str, title: str, url: str, used: str, *, updated: str = "", priority: str = "1") -> dict[str, str]:
    return {
        "municipality_id": MID,
        "source_id": source_id,
        "資料名": title,
        "資料種別": "自治体公式PDF" if url.lower().endswith(".pdf") else "自治体公式Webページ",
        "公式URL": url,
        "発行主体": "福山市",
        "対象年度": "令和8年度／取得時点現行",
        "ページ更新日": updated,
        "取得確認日": CHECKED,
        "使用した情報": used,
        "優先度": priority,
        "現行性": "現行",
        "備考": "M099 APP_READYの教材正答再現・監査に使用。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    }


SOURCES = [
    source("S-M099-01", "2026年度 福山市一般廃棄物処理実施計画", PLAN_URL, "家庭ごみ7区分・主要品目・紙類地域差・市収集外品", updated="2026-04-01"),
    source("S-M099-02", "ごみ分別ガイドブック", GUIDE_LANDING_URL, "市内版・内海町版ガイドへの公式導線", updated="2024-03-31", priority="2"),
    source("S-M099-03", "福山市ごみ分別ガイドブック 内海町版", UTSUMI_GUIDE_URL, "内海町の品目別出し方・紙類・特殊品目の補足", updated="2024-04", priority="2"),
    source("S-M099-04", "沼隈町の紙類", NUMAKUMA_PAPER_URL, "沼隈町の新聞・雑誌等・段ボール・紙パック", updated="2024-02-01"),
    source("S-M099-05", "2026年度家庭ごみ収集日程表", SCHEDULE_URL, "2026年度の地域別収集体系と年4回特殊品目収集", updated="2026-02-20"),
    source("S-M099-06", "ごみ分別辞典", DICTIONARY_URL, "40品目の通常分別・材質条件・前処理", updated="2025-03-31"),
    source("S-M099-08", "『蛍光灯』や『ストーブ類』の出し方", BULB_URL, "蛍光灯・白熱電球・LED電球の分別", updated="2025-04-01"),
    source("S-M099-09", "2026年度（令和8年度）家庭ごみ収集日程表（内海町）", UTSUMI_2026_URL, "内海町の現行5区分・収集日程・小型家電/充電式電池/古紙の拠点回収案内", updated="2026"),
    source("S-M099-10", "スプレー缶・ライター類・電池等をごみで出すときのお願い", BATTERY_WARNING_URL, "乾電池・ボタン電池・充電式電池・ライター・スプレー缶の現行出し方", updated="2025-04-01"),
    source("S-M099-11", "充電式電池が取り外せない小型家電の分別について", EMBEDDED_BATTERY_URL, "内蔵充電池小型家電の2024年12月以降の分別変更", updated="2025-11-04"),
    source("S-M099-12", "ごみの持込と拠点回収について", DROPOFF_URL, "小型家電・充電式電池・古紙等の公共施設拠点回収", updated="2026"),
    source("S-M099-13", "家庭用パソコンの出し方", PC_URL, "家庭用PCの宅配・メーカー回収・市持込回収", updated="2025-04-01"),
    source("S-M099-14", "家電リサイクルについて", HOME_APPLIANCE_URL, "家電4品目は市収集・処理施設持込不可", updated="2024-04-01"),
    source("S-M099-15", "公共施設での古紙拠点回収", OLD_PAPER_URL, "新聞・雑誌/雑紙・段ボールの拠点回収", updated="2024-08-27"),
    source("S-M099-16", "家庭から出る草・庭木の剪定枝のごみ処理施設等への持ち込みについて", PRUNING_URL, "剪定枝の寸法・少量ステーション収集・施設持込", updated="2025-10-22"),
    source("S-M099-17", "ごみの分別一部変更のお知らせ", PAPER_CHANGE_URL, "一般地域の紙類対象品・牛乳パック/雑紙の拠点回収", updated="2022-04-01"),
    source("S-M099-18", "ペットボトルのリサイクル及びベール品質調査結果", PET_URL, "PETボトルの容器包装プラ収集・キャップ/ラベル除去", updated="2025-04-01"),
]
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
    level: str = "PRIMARY",
    channel: str = "CURBSIDE",
    excluded: str = "FALSE",
    condition: str = "家庭から出る対象品",
    outside: str = "他の公式区分又は指定回収経路を確認",
    prep: str = "品目別の公式出し方に従う",
    prohibited: str = "他の分別区分・指定回収経路に該当する物",
    size: str = "",
    bulky: str = "FALSE",
    note: str = "",
) -> dict[str, str]:
    src = SOURCE_BY_ID[source_id]
    return {
        "municipality_id": MID,
        "category_id": category_id,
        "自治体正式名称": name,
        "category_group": name,
        "parent_category_id": "",
        "classification_level": level,
        "表示順": str(order),
        "collection_channel": channel,
        "代表品目": representative,
        "入れてはいけない物": prohibited,
        "適用条件": condition,
        "条件外の扱い": outside,
        "出す前の処理": prep,
        "袋・容器のルール": "品目別の公式案内に従う",
        "サイズ・条件": size,
        "粗大ごみ扱いか": bulky,
        "予約が必要か": "FALSE",
        "有料か": "FALSE",
        "料金ルール": "",
        "自治体収集外か": excluded,
        "注意事項": note or "収集日・地域差は2026年度日程表を確認",
        "source_id": source_id,
        "出典URL": src["公式URL"],
        "出典ページ・該当箇所": locator,
        "確認日": CHECKED,
        "ui_role": ui_role,
        "rule_status": "CURRENT",
        "effective_from": "",
        "effective_to": "",
    }


CATEGORIES = [
    category("C-M099-01", "燃やせるごみ", 1, "生ごみ・紙くず・紙おむつ・衣類・草木等", "S-M099-01", "1頁『燃やせるごみ』", prep="生ごみは水切りし、危険物・資源物を混ぜない", size="原則一辺50cm以下"),
    category("C-M099-02", "容器包装プラスチックごみ", 2, "PETボトル・トレイ・カップ・袋等の容器包装", "S-M099-01", "1頁『容器包装プラスチックごみ』", prep="中身を使い切り、必要に応じてすすぐ。PETはふた・ラベルを外す", size="原則一辺50cm以下"),
    category("C-M099-03", "紙類", 3, "新聞・雑誌・段ボール。内海町・沼隈町は紙パック等を含む地域差あり", "S-M099-01", "1頁『紙類（走島町を除く。）』・4頁地域別収集", condition="走島町を除く。内海町・沼隈町は紙類の対象品・回収頻度に地域差あり", outside="走島町又は通常紙類対象外の紙は拠点回収・燃やせるごみ等の公式経路", prep="紙種別にまとめ、ひもで束ねる等の地域別出し方に従う", prohibited="汚れた紙・走島町の通常紙類収集対象外品"),
    category("C-M099-04", "資源ごみ", 4, "びん・缶・金属類・スプレー缶等", "S-M099-01", "1頁『資源ごみ』", prep="中身を空にし、品目別の安全処理を行う", size="原則一辺50cm以下"),
    category("C-M099-05", "不燃（破砕）ごみ", 5, "ガラス・陶磁器・電池を外した小型家電・傘等", "S-M099-01", "1頁『不燃（破砕）ごみ』", prep="刃物・割れ物は包んで『キケン』と表示。電池は外す", size="原則一辺2m以下"),
    category("C-M099-06", "燃やせる粗大ごみ", 6, "木製家具・寝具等", "S-M099-01", "1頁『燃やせる粗大ごみ』", prep="品目別にひもで束ねる・付属品を外す等の指定に従う", size="原則一辺2m以下", bulky="TRUE"),
    category("C-M099-07", "使用済乾電池等", 7, "蛍光灯・乾電池・ボタン電池・充電式電池・充電池内蔵小型家電・ライター等", "S-M099-01", "1頁『使用済乾電池等』・2026年度特殊品目収集", prep="電池は絶縁し種類別に袋を分ける。ライターはガスを抜く。蛍光灯は割れないよう保護", note="年4回の特殊品目収集。充電式電池等は公共施設への拠点回収も利用可能"),
    category("C-M099-08", "拠点回収（小型家電・充電式電池等・古紙）", 8, "小型家電・充電式電池・古紙・家庭用パソコン等", "S-M099-12", "『拠点回収について』持ち込み場所・対象品目表", ui_role="REFERENCE_ONLY", level="ALTERNATIVE", channel="DROP_OFF", condition="家庭から出る拠点回収対象品", outside="通常収集区分・メーカー回収・家電リサイクル等の品目別経路", prep="個人情報を消去し、電池類は安全措置を行う等、対象品別条件に従う", prohibited="家電リサイクル法対象4品目・拠点回収対象外品", note="内海町2026年度日程表も小型家電・充電式電池・古紙の公共施設等拠点回収を案内"),
    category("C-M099-09", "家電リサイクル対象品目（市収集・処理対象外）", 9, "エアコン・テレビ・冷蔵庫/冷凍庫・洗濯機/衣類乾燥機", "S-M099-14", "『家電リサイクルについて』対象品目・処理方法", ui_role="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED", excluded="TRUE", condition="家電リサイクル法対象4品目", outside="対象外の小型家電は通常分別又は拠点回収", prep="販売店・許可業者・指定引取場所等の公式経路を利用", prohibited="市の通常収集対象品", note="ごみステーション・市ごみ処理施設へは出せない"),
]
CATEGORY_BY_ID = {row["category_id"]: row for row in CATEGORIES}

MUNICIPALITY = {
    "municipality_id": MID,
    "都道府県": "広島県",
    "市町村": "福山市",
    "実装区分": "中国5県全市町村",
    "ごみ処理主体": "福山市",
    "自治体ごみトップURL": "https://www.city.fukuyama.hiroshima.jp/site/kankyo/",
    "分別ガイドURL": DICTIONARY_URL,
    "品目検索URL": "",
    "やさしい日本語URL": "",
    "多言語資料URL": "",
    "対象年度": "令和8年度",
    "最終確認日": CHECKED,
    "確認ステータス": "QA_REQUIRED",
    "備考": "2026年度7通常区分と地域差を保持。内海町は327009.pdfで現行収集体系を確認。拠点回収をREFERENCE_ONLYで追加。",
    "official_category_count": "",
    "reviewed_category_count": "8",
    "category_count_basis": "2026年度実施計画の7通常収集区分を全件照合し、現行公式の小型家電・充電式電池等・古紙の拠点回収をREFERENCE_ONLY運用葉として1件追加。家電4品目EXCLUDED_NOTICEは件数外。",
    "category_count_verified": "TRUE",
    "category_count_check_status": "MANUAL_INDEX_REVIEW",
    "category_count_review_id": "CR-M099-CATEGORY-COVERAGE",
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
    {
        "review_evidence_id": "CRE-M099-S-M099-01",
        "review_id": "CR-M099-CATEGORY-COVERAGE",
        "municipality_id": MID,
        "source_id": "S-M099-01",
        "locator": "1頁の家庭ごみ7区分と4頁の地域別収集体系",
        "evidence_role": "PRIMARY_INDEX",
        "notes": "7通常収集区分を2026年度実施計画で全件照合。",
    },
    {
        "review_evidence_id": "CRE-M099-S-M099-12",
        "review_id": "CR-M099-CATEGORY-COVERAGE",
        "municipality_id": MID,
        "source_id": "S-M099-12",
        "locator": "拠点回収の対象品目・持ち込み場所表",
        "evidence_role": "SUPPLEMENTAL_INDEX",
        "notes": "通常7区分と別の現行拠点回収経路をREFERENCE_ONLYとして確認。",
    },
]


def b(category_id: str, wording: str, condition: str, preparation: str, fallback: str, source_id: str, locator: str, basis: str = "DIRECT_ITEM") -> dict[str, str]:
    return {
        "category_id": category_id,
        "official_item_wording": wording,
        "condition": condition,
        "preparation": preparation,
        "exception_destination": fallback,
        "source_id": source_id,
        "locator": locator,
        "evidence_basis": basis,
    }


RULES: dict[str, list[dict[str, str]]] = {
    "I001": [
        b("C-M099-02", "ペットボトル（プラマークがあるもの）", "プラマークのあるPETボトルで中身を空にし汚れを落とせるもの", "ふた・ラベルを外して水で軽くゆすぐ", "汚れが落ちないものは燃やせるごみ", "S-M099-06", "分別辞典『ペットボトル』"),
        b("C-M099-01", "汚れが落ちない容器包装プラスチック", "PETボトルでも汚れが落ちず容器包装プラとして出せないもの", "中身を使い切って出す", "洗浄できるPETボトルは容器包装プラスチックごみ", "S-M099-01", "1頁『燃やせるごみ』汚れが落ちない容器包装プラスチック", "OFFICIAL_RULE_DERIVED"),
    ],
    "I002": [b("C-M099-02", "ペットボトルのふた", "PETボトルから外したプラスチック製キャップ", "ボトルから外し、ボトル・ラベルと同じ袋へ入れる", "材質が異なる場合は品目別に確認", "S-M099-03", "内海町版『容器包装プラスチックごみ』：ボトル・ふた・ラベルは同じ袋", "OFFICIAL_RULE_DERIVED")],
    "I003": [b("C-M099-02", "ペットボトルのラベル", "PETボトルから外したプラスチック製ラベル", "ボトルから外し、ボトル・ふたと同じ袋へ入れる", "材質が異なる場合は品目別に確認", "S-M099-03", "内海町版『容器包装プラスチックごみ』：ボトル・ふた・ラベルは同じ袋", "OFFICIAL_RULE_DERIVED")],
    "I004": [
        b("C-M099-04", "アルミ缶", "中身を空にした家庭用アルミ缶", "中身を空にして出す", "さびたりボロボロの缶は不燃（破砕）ごみ", "S-M099-06", "分別辞典『缶』『アルミ缶』"),
        b("C-M099-05", "さびたりボロボロになった缶", "腐食・破損が進み資源缶として扱えないアルミ缶", "中身を完全に除く", "通常状態のアルミ缶は資源ごみ", "S-M099-06", "分別辞典『缶』：さびたりボロボロになった缶", "DIRECT_ITEM"),
    ],
    "I005": [
        b("C-M099-04", "スチール缶", "中身を空にした家庭用スチール缶", "中身を空にして出す", "さびたりボロボロの缶は不燃（破砕）ごみ", "S-M099-06", "分別辞典『スチール缶』『缶』"),
        b("C-M099-05", "さびたりボロボロになった缶", "腐食・破損が進み資源缶として扱えないスチール缶", "中身を完全に除く", "通常状態のスチール缶は資源ごみ", "S-M099-06", "分別辞典『缶』：さびたりボロボロになった缶"),
    ],
    "I006": [
        b("C-M099-04", "びん（ガラス製）", "家庭から出る飲食物等の割れていないガラスびん", "中身・ふたを取り除く", "陶磁器製びん・ガラス製品・割れ物は不燃（破砕）ごみ", "S-M099-06", "分別辞典『びん』『薬びん（飲み薬）』"),
        b("C-M099-05", "ガラス製品・割れ物", "資源びんとして扱わないガラス製品又は割れたガラスびん", "割れて危険な場合は新聞紙等で包み『キケン』と表示", "割れていない資源対象びんは資源ごみ", "S-M099-06", "分別辞典『花瓶』『湯のみ』等のガラス・陶磁器扱い", "OFFICIAL_RULE_DERIVED"),
    ],
    "I007": [
        b("C-M099-02", "食品トレイ（プラマークがあるもの）", "プラマークがあり固形物・汚れを落とせる白色食品トレイ", "水で軽くゆすいで固形物を落とす", "汚れが落ちないものは燃やせるごみ。店頭回収も利用可", "S-M099-06", "分別辞典のプラマーク付き容器・2026年3月広報の食品トレー", "OFFICIAL_RULE_DERIVED"),
        b("C-M099-01", "汚れが落ちない容器包装プラスチック", "白色食品トレイでも汚れが落ちないもの", "中身を除いて出す", "洗浄できるプラマーク付きトレイは容器包装プラスチックごみ", "S-M099-01", "1頁『燃やせるごみ』汚れが落ちない容器包装プラスチック", "OFFICIAL_RULE_DERIVED"),
    ],
    "I008": [
        b("C-M099-02", "食品トレイ（プラマークがあるもの）", "色・柄付きでもプラマークがあり汚れを落とせる食品トレイ", "水で軽くゆすぐ", "プラマークがない又は汚れが落ちないものは燃やせるごみ", "S-M099-06", "分別辞典のプラマーク付き容器包装・食品トレイ", "OFFICIAL_RULE_DERIVED"),
        b("C-M099-01", "プラマークがない又は汚れが落ちないプラスチック製品", "容器包装プラ対象外又は汚れが落ちない色柄トレイ", "中身を除く", "対象となる清潔なプラマーク付きトレイは容器包装プラスチックごみ", "S-M099-06", "分別辞典のプラスチック製品・容器包装条件", "OFFICIAL_RULE_DERIVED"),
    ],
    "I009": [
        b("C-M099-02", "弁当容器（プラマークがあるプラスチック製）", "プラマークがあり汚れを落とせるプラスチック製弁当容器", "固形物を除き水ですすぐ", "プラマークなしは燃やせるごみ、アルミ製は資源ごみ", "S-M099-06", "分別辞典のカップ・パック・プラマーク条件", "OFFICIAL_RULE_DERIVED"),
        b("C-M099-01", "プラスチック製品（プラマークなし）", "プラマークのないプラスチック製弁当容器又は汚れが落ちないもの", "中身を除く", "プラマーク付きで洗浄できるものは容器包装プラ", "S-M099-06", "分別辞典のプラスチック製商品・汚れ条件", "OFFICIAL_RULE_DERIVED"),
        b("C-M099-04", "アルミ製弁当容器", "家庭から出るアルミ製の弁当容器", "中身を除く", "プラスチック製はマーク・汚れ条件で分別", "S-M099-01", "1頁『資源ごみ』金属類", "OFFICIAL_RULE_DERIVED"),
    ],
    "I010": [
        b("C-M099-02", "お菓子の袋（プラマークがあるもの）", "プラマーク付きで中身を空にしたプラスチック製菓子袋", "中身を空にする", "紙製・対象外・汚れが落ちないものは燃やせるごみ", "S-M099-06", "分別辞典の包装フィルム・袋類・プラマーク条件", "OFFICIAL_RULE_DERIVED"),
        b("C-M099-01", "紙製又は容器包装プラ対象外の菓子袋", "紙製、プラマークなし、又は汚れが落ちない菓子袋", "中身を空にする", "清潔なプラマーク付き袋は容器包装プラスチックごみ", "S-M099-06", "分別辞典の紙製容器・プラマークなし製品", "OFFICIAL_RULE_DERIVED"),
    ],
    "I011": [
        b("C-M099-02", "レジ袋（プラマークがあるもの）", "プラマーク付きのレジ袋", "中身を空にする", "対象外又は汚れが落ちないものは燃やせるごみ", "S-M099-06", "分別辞典『レジ袋』"),
        b("C-M099-01", "プラマーク対象外又は汚れが落ちない袋", "容器包装プラ対象外又は著しく汚れた袋", "中身を空にする", "清潔なプラマーク付きレジ袋は容器包装プラスチックごみ", "S-M099-01", "1頁『燃やせるごみ』汚れが落ちない容器包装プラスチック", "OFFICIAL_RULE_DERIVED"),
    ],
    "I012": [
        b("C-M099-02", "発泡スチロール（プラマークあり）", "プラマークがあり一辺50cm以下で汚れを落とせる発泡スチロール", "汚れを落とし50cm以下にする", "プラマークなしは燃やせるごみ", "S-M099-06", "分別辞典『発泡スチロール』プラマークあり"),
        b("C-M099-01", "発泡スチロール（プラマークなし）", "プラマークのない発泡スチロール又は容器包装プラ対象外", "必要に応じ50cm以下にする", "プラマーク付き対象品は容器包装プラスチックごみ", "S-M099-06", "分別辞典『発泡スチロール』プラマークなし"),
    ],
    "I013": [
        b("C-M099-03", "新聞（チラシを含む）", "走島町を除く地域で家庭から出る乾いた新聞", "ひもでまとめて地域別紙類日に出す", "走島町では通常紙類収集へ出さず拠点回収等を利用", "S-M099-01", "1頁『紙類（走島町を除く。）』新聞・4頁地域差", "OFFICIAL_RULE_DERIVED"),
        b("C-M099-08", "新聞（古紙拠点回収）", "走島町又は拠点回収を利用する市内の新聞", "新聞・チラシとして分けて持ち込む", "通常紙類収集対象地域では紙類日に出すことも可能", "S-M099-15", "公共施設での古紙拠点回収：新聞（チラシを含む）", "DIRECT_ITEM"),
    ],
    "I014": [
        b("C-M099-03", "段ボール", "走島町を除く地域で家庭から出る乾いた段ボール", "折りたたみ、ひもでまとめる", "走島町では通常紙類収集へ出さず拠点回収等を利用", "S-M099-01", "1頁『紙類（走島町を除く。）』段ボール・4頁地域差", "OFFICIAL_RULE_DERIVED"),
        b("C-M099-08", "段ボール（古紙拠点回収）", "走島町又は拠点回収を利用する市内の段ボール", "段ボールとして分けて持ち込む", "通常紙類収集対象地域では紙類日に出すことも可能", "S-M099-15", "公共施設での古紙拠点回収：ダンボール", "DIRECT_ITEM"),
    ],
    "I015": [
        b("C-M099-03", "雑誌・本", "走島町を除く地域で家庭から出る乾いた雑誌・本", "ひもでまとめる", "走島町では通常紙類収集へ出さず拠点回収等を利用", "S-M099-17", "『紙類』対象品目：雑誌（本）、走島町除外", "OFFICIAL_RULE_DERIVED"),
        b("C-M099-08", "雑誌（古紙拠点回収）", "走島町又は拠点回収を利用する市内の雑誌", "雑誌・雑紙として分けて持ち込む", "通常紙類収集対象地域では紙類日に出すことも可能", "S-M099-15", "公共施設での古紙拠点回収：雑誌（雑紙を含む）"),
    ],
    "I016": [
        b("C-M099-03", "紙箱・包装紙等", "沼隈町で回収対象となる清潔な紙箱・包装紙等", "雑誌・本・包装紙又は段ボール・紙箱の区分でひもでまとめる", "汚れた紙は燃やせるごみ", "S-M099-04", "『沼隈町で回収する紙類』雑誌・本・包装紙／段ボール・紙箱"),
        b("C-M099-08", "雑紙（古紙拠点回収）", "市内で資源化できる菓子箱・封筒などの清潔な雑紙を拠点回収へ出す場合", "雑誌・雑紙として分けて持ち込む", "ごみとして捨てる場合や汚れた紙は燃やせるごみ", "S-M099-15", "公共施設での古紙拠点回収：雑誌（菓子箱や封筒などの雑紙を含む）"),
        b("C-M099-01", "コピー用紙・封筒・包装紙等を通常ごみとして出す場合", "通常紙類の対象外となる雑紙を資源回収せずごみとして出す場合又は汚れた紙", "金具等を外す", "資源化できる清潔な雑紙は拠点回収を利用可能", "S-M099-06", "分別辞典『コピー用紙』『封筒』『包装紙』"),
    ],
    "I017": [
        b("C-M099-03", "紙パック", "内海町で紙類として回収する洗浄可能な飲料用紙パック", "中を洗い切り開き、紙類の出し方に従う", "対象外・汚れたものは燃やせるごみ等を確認", "S-M099-03", "内海町版5頁『紙類』紙パック", "DIRECT_ITEM"),
        b("C-M099-03", "紙パック", "沼隈町で紙類として回収する洗浄可能な飲料用紙パック", "中を洗って切り開き、十字にしばる", "対象外・汚れたものは燃やせるごみ等を確認", "S-M099-04", "『沼隈町で回収する紙類』紙パック", "DIRECT_ITEM"),
        b("C-M099-08", "牛乳パック等（拠点回収）", "内海町・沼隈町以外で清潔な牛乳パック等を資源化する場合", "洗浄・乾燥等、回収先の条件に従う", "通常紙類の日には出さない。汚れたもの等は燃やせるごみ", "S-M099-17", "一般地域の紙類対象外：牛乳パックは拠点回収等を利用", "OFFICIAL_RULE_DERIVED"),
        b("C-M099-01", "紙パックを燃やせるごみとして出す場合", "汚れ等で資源回収に適さない紙パック又は一般地域で資源回収を利用しない場合", "中身を空にする", "内海町・沼隈町の対象紙パックは紙類、清潔なものは拠点回収も可", "S-M099-17", "紙類対象外の牛乳パック等をごみとして出す場合は燃やせるごみ", "OFFICIAL_RULE_DERIVED"),
    ],
    "I018": [b("C-M099-01", "生ごみ", "家庭から出る生ごみ", "水分をよく切る", "多量の場合は一度に出さず市案内を確認", "S-M099-01", "1頁『燃やせるごみ』台所ごみ", "OFFICIAL_RULE_DERIVED")],
    "I019": [b("C-M099-01", "ティッシュペーパー", "使用済みティッシュペーパー", "そのまま燃やせるごみへ", "危険物・医療系感染性廃棄物は別経路", "S-M099-06", "分別辞典『ティッシュペーパー』")],
    "I020": [b("C-M099-01", "紙おむつ", "家庭から出る使用済み紙おむつ", "排泄物をトイレへ流してから出す", "医療系の特殊品は公式案内を確認", "S-M099-01", "1頁『燃やせるごみ』紙おむつ", "OFFICIAL_RULE_DERIVED")],
    "I021": [b("C-M099-01", "衣類", "家庭から出る通常の衣類", "金具等を外せる場合は外す", "衣類乾燥機は家電リサイクル対象", "S-M099-06", "分別辞典『衣類』")],
    "I022": [b("C-M099-05", "傘", "家庭から出る通常の傘", "そのまま不燃（破砕）ごみへ", "2mを超える特殊品は市へ確認", "S-M099-01", "1頁『不燃（破砕）ごみ』金属・複合製品", "OFFICIAL_RULE_DERIVED")],
    "I023": [b("C-M099-05", "陶磁器製品", "家庭から出る茶碗・皿・花瓶等の陶磁器", "割れて危険な場合は新聞紙等で包み『キケン』と表示", "金属製品は資源ごみ等、材質別に確認", "S-M099-06", "分別辞典『かめ』『花瓶』『湯のみ』")],
    "I024": [b("C-M099-05", "ガラス製品", "資源びんではない家庭用ガラス製品", "割れて危険な場合は新聞紙等で包み『キケン』と表示", "飲食物用等の資源対象びんは資源ごみ", "S-M099-06", "分別辞典『クリスタルガラス』『風鈴（ガラス製）』等", "OFFICIAL_RULE_DERIVED")],
    "I025": [b("C-M099-05", "割れたガラス", "家庭から出る割れたガラス・割れた食器", "新聞紙などに包み『キケン』と表示し、破片や刃先が出ないようにする", "割れていない資源対象びんは資源ごみ", "S-M099-06", "分別辞典の割れ物・2026年3月広報『割れたお皿』", "OFFICIAL_RULE_DERIVED")],
    "I026": [b("C-M099-05", "包丁・刃物", "家庭から出る包丁等の刃物", "新聞紙などに包み『キケン』と表示する", "金属でも刃先を露出させて資源ごみに出さない", "S-M099-06", "分別辞典『包丁』『刃物』")],
    "I027": [b("C-M099-07", "使用済乾電池", "家庭用の使用済み乾電池", "端子をセロハンテープ等で絶縁し、別袋に入れる", "充電式電池は乾電池と別袋。鉛蓄電池等は対象外", "S-M099-10", "『使用済乾電池』：絶縁・別袋・燃やせる粗大ごみの日", "DIRECT_ITEM")],
    "I028": [b("C-M099-07", "ボタン電池", "家庭用の使用済みボタン電池", "セロハンテープ等で巻いて絶縁し、別袋に入れる", "充電式電池等は種類別に分ける", "S-M099-06", "分別辞典『ボタン電池』")],
    "I029": [
        b("C-M099-07", "モバイルバッテリー", "破損・膨張等の異常がない家庭用モバイルバッテリーを収集日に出す場合", "なるべく使い切り、金属部分を絶縁し、使用済乾電池と別袋にする", "公共施設への拠点回収も利用可能。鉛バッテリー等は対象外", "S-M099-10", "『充電式電池・充電式電池が取り外せない小型家電』対象品目：モバイルバッテリー"),
        b("C-M099-08", "モバイルバッテリー（拠点回収）", "家庭用モバイルバッテリーを公共施設へ直接持ち込む場合", "なるべく使い切り、金属部分を絶縁する", "持込困難な場合は年4回の特殊品目収集を利用", "S-M099-12", "拠点回収対象：充電式電池等（リチウムイオン電池等）", "DIRECT_ITEM"),
    ],
    "I030": [b("C-M099-07", "蛍光灯", "家庭から出る蛍光灯・蛍光管", "割れないよう買い替え時の箱などに入れる", "白熱球・LED電球は不燃（破砕）ごみ", "S-M099-06", "分別辞典『蛍光灯』")],
    "I031": [
        b("C-M099-05", "電球（白熱球・LED）", "白熱電球又はLED電球", "割れた場合は新聞紙等で包み『キケン』と表示", "蛍光灯式のものは使用済乾電池等の特殊品目収集", "S-M099-06", "分別辞典『電球 白熱球・LED』"),
        b("C-M099-07", "電球型蛍光灯・蛍光灯", "蛍光灯式の電球", "割れないよう箱等に入れる", "白熱球・LED電球は不燃（破砕）ごみ", "S-M099-08", "『蛍光灯』や『ストーブ類』の出し方：蛍光灯と白熱/LEDの区分", "OFFICIAL_RULE_DERIVED"),
    ],
    "I032": [b("C-M099-04", "スプレー缶", "家庭から出る中身を使い切ったスプレー缶", "中身を使い切って穴を開け、必ず別袋に入れる", "中身を抜けない場合は市へ相談", "S-M099-06", "分別辞典『スプレー缶』")],
    "I033": [b("C-M099-07", "ライター", "家庭から出る使い捨てライター等", "ガスを抜いてライター類だけを別袋に入れる", "ガスを安全に抜けない場合は市へ相談", "S-M099-06", "分別辞典『ライター』")],
    "I034": [
        b("C-M099-05", "小型家電（電池を取り外せるもの）", "家電4品目等を除く家庭用小型家電で電池を容易に取り外せるものを通常収集へ出す場合", "電池を取り外す", "充電式電池が取り外せないものは使用済乾電池等の特殊品目収集又は拠点回収", "S-M099-06", "分別辞典のカメラ・小型家電等：電池を取り外して不燃（破砕）ごみ", "OFFICIAL_RULE_DERIVED"),
        b("C-M099-08", "使用済小型家電（拠点回収）", "拠点回収対象の家庭用小型家電を公共施設へ持ち込む場合", "個人情報を消去し、外せる電池は外す等の対象条件に従う", "家電4品目等の対象外品は指定経路へ", "S-M099-12", "拠点回収対象：小型家電"),
    ],
    "I035": [
        b("C-M099-07", "充電式電池が取り外せない小型家電", "充電式電池が製品に内蔵され容易に取り外せない小型家電を収集日に出す場合", "なるべく電池を使い切り、別袋に入れる", "公共施設への拠点回収も利用可能。不燃（破砕）ごみには出さない", "S-M099-11", "2024年12月から年4回の燃やせる粗大ごみの日へ分別変更"),
        b("C-M099-08", "充電式電池が取り外せない小型家電（拠点回収）", "内蔵充電池小型家電を公共施設へ直接持ち込む場合", "なるべく電池を使い切り、本体ごと対象窓口へ持ち込む", "持込困難な場合は年4回の特殊品目収集を利用", "S-M099-12", "拠点回収対象：充電式電池等が取り外せない小型家電"),
    ],
    "I036": [b("C-M099-06", "布団", "家庭から出る布団", "ひも等でまとめる", "布団カバー等の小さい布類は燃やせるごみ", "S-M099-06", "分別辞典『布団』")],
    "I037": [b("C-M099-09", "家電リサイクル対象品目", "エアコン、テレビ、冷蔵庫・冷凍庫、洗濯機・衣類乾燥機", "販売店・許可業者・指定引取場所等の公式経路を利用", "ごみステーション及び市ごみ処理施設へは出せない", "S-M099-14", "『家電リサイクルについて』対象4品目・市では収集しない")],
    "I038": [b("C-M099-08", "家庭用パソコン", "家庭で不用になったパソコン・ディスプレイ", "個人情報を消去し、市持込回収・宅配便回収・メーカー回収のいずれかを利用", "ごみステーションには出さない", "S-M099-13", "『家庭用パソコンの出し方』3つの回収方法")],
    "I039": [b("C-M099-01", "使用済み食用油", "家庭から出る少量の使用済み食用油を通常ごみとして処分する場合", "紙・布に吸わせる又は固める等、漏れない状態にする", "容器は材質・プラマーク等に応じて別分別", "S-M099-01", "1頁『燃やせるごみ』台所ごみ・紙くず等からの家庭用少量処理", "OFFICIAL_RULE_DERIVED")],
    "I040": [
        b("C-M099-01", "庭木の剪定枝", "家庭から出る剪定枝で直径10cm・長さ50cm以下、ステーションへ出す量がごみ袋2袋程度まで", "直径10cm・長さ50cm以下に切ってひもで束ねる", "多量の場合は市ごみ処理施設等への持込を利用", "S-M099-16", "剪定枝：直径10cm・長さ50cm以下、燃やせるごみ収集日にも排出可"),
        b("C-M099-08", "剪定枝の施設持込", "家庭から出る草・剪定枝を市指定施設へ直接持ち込む場合", "草は袋へ、剪定枝は直径10cm・長さ50cm以下に切り束ねる", "通常少量は燃やせるごみ収集日にも排出可", "S-M099-16", "家庭から出る草・庭木の剪定枝の受入場所・条件", "OFFICIAL_RULE_DERIVED"),
    ],
}

REVIEW_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "canonical_name", "display_name",
    "official_item_wording", "category_id", "category_name", "condition", "preparation",
    "exception_destination", "evidence_basis", "item_evidence_source_id", "item_evidence_url",
    "item_evidence_locator", "branch_review_status", "checked_date", "reviewer", "note",
]


def upsert(rows: list[dict[str, str]], row: dict[str, str], keys: tuple[str, ...]) -> list[dict[str, str]]:
    key = tuple(row.get(field, "") for field in keys)
    return [existing for existing in rows if tuple(existing.get(field, "") for field in keys) != key] + [row]


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
        "notes": "Completed Batch 10 holds only the ordinary source/category layer; APP item review is canonical-only.",
    }


def prepare_batch10() -> tuple[dict[str, str], list[dict[str, str]], list[dict[str, str]], dict[str, str], list[dict[str, str]]]:
    paths = {
        "municipalities": BATCH10 / "batch_10_municipalities.csv",
        "categories": BATCH10 / "batch_10_categories.csv",
        "sources": BATCH10 / "batch_10_sources.csv",
        "qa": BATCH10 / "batch_10_qa.csv",
        "mapping": BATCH10 / "batch_10_item_mapping.csv",
        "coverage": BATCH10 / "batch_10_item_coverage.csv",
        "review": BATCH10 / "batch_10_category_review_evidence.csv",
    }
    m_fields, municipalities = read_csv(paths["municipalities"])
    c_fields, categories = read_csv(paths["categories"])
    s_fields, sources = read_csv(paths["sources"])
    q_fields, qa = read_csv(paths["qa"])
    map_fields, mappings = read_csv(paths["mapping"])
    cov_fields, coverage = read_csv(paths["coverage"])
    rev_fields, review = read_csv(paths["review"])

    municipalities = [r for r in municipalities if r.get("municipality_id") != MID] + [MUNICIPALITY]
    categories = [r for r in categories if r.get("municipality_id") != MID] + CATEGORIES
    sources = [r for r in sources if r.get("municipality_id") != MID] + SOURCES
    review = [r for r in review if r.get("municipality_id") != MID] + CATEGORY_REVIEW

    write_csv(paths["municipalities"], m_fields or MUNICIPALITY_FIELDS, sorted(municipalities, key=lambda r: r["municipality_id"]))
    write_csv(paths["categories"], c_fields or CATEGORY_FIELDS, sorted(categories, key=lambda r: (r["municipality_id"], r["category_id"])))
    write_csv(paths["sources"], s_fields or SOURCE_FIELDS, sorted(sources, key=lambda r: (r["municipality_id"], r["source_id"])))
    write_csv(paths["review"], rev_fields or CATEGORY_REVIEW_EVIDENCE_FIELDS, sorted(review, key=lambda r: (r["municipality_id"], r["review_evidence_id"])))

    migrate_bundle(
        paths["municipalities"], paths["categories"], paths["sources"], paths["qa"],
        paths["mapping"], paths["coverage"], paths["review"],
    )

    m_fields, municipalities = read_csv(paths["municipalities"])
    c_fields, categories = read_csv(paths["categories"])
    s_fields, sources = read_csv(paths["sources"])
    q_fields, qa = read_csv(paths["qa"])
    map_fields, mappings = read_csv(paths["mapping"])
    cov_fields, coverage = read_csv(paths["coverage"])
    rev_fields, review = read_csv(paths["review"])

    # The completed batch proves the ordinary research layer, not APP item evidence.
    mappings = [r for r in mappings if r.get("municipality_id") != MID]
    coverage = [r for r in coverage if r.get("municipality_id") != MID] + [not_researched_coverage(f"I{i:03d}") for i in range(1, 41)]
    write_csv(paths["mapping"], map_fields or MAPPING_FIELDS, sorted(mappings, key=lambda r: (r["municipality_id"], r["mapping_id"])))
    write_csv(paths["coverage"], cov_fields or COVERAGE_FIELDS, sorted(coverage, key=lambda r: (r["municipality_id"], r["internal_item_id"])))

    m099_municipality = next(r for r in municipalities if r.get("municipality_id") == MID)
    m099_qa = next(r for r in qa if r.get("municipality_id") == MID)
    return (
        m099_municipality,
        [r for r in categories if r.get("municipality_id") == MID],
        [r for r in sources if r.get("municipality_id") == MID],
        m099_qa,
        [r for r in review if r.get("municipality_id") == MID],
    )


def build_app_ready_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    _, items = read_csv(ROOT / "data/master/04_common_items_master.csv")
    item_by = {r["internal_item_id"]: r for r in items}
    expected = {f"I{i:03d}" for i in range(1, 41)}
    if set(RULES) != expected:
        raise ValueError(f"M099 rule scope mismatch missing={sorted(expected - set(RULES))} extra={sorted(set(RULES) - expected)}")

    mappings: list[dict[str, str]] = []
    coverage: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    for item_id in sorted(expected):
        master = item_by[item_id]
        branches = RULES[item_id]
        for order, branch in enumerate(branches, 1):
            category_row = CATEGORY_BY_ID[branch["category_id"]]
            evidence = SOURCE_BY_ID[branch["source_id"]]
            mapping_id = f"MAP-{MID}-{item_id}-B{order:02d}-{branch['category_id']}"
            mappings.append({
                "mapping_id": mapping_id,
                "municipality_id": MID,
                "internal_item_id": item_id,
                "branch_order": str(order),
                "自治体での品目表記": branch["official_item_wording"],
                "category_id": branch["category_id"],
                "分別区分正式名称": category_row["自治体正式名称"],
                "条件": branch["condition"],
                "前処理": branch["preparation"],
                "例外分別先": branch["exception_destination"],
                "自治体収集外": category_row["自治体収集外か"],
                "rule_status": category_row["rule_status"],
                "effective_from": category_row["effective_from"],
                "effective_to": category_row["effective_to"],
                "category_source_id": category_row["source_id"],
                "category_source_url": category_row["出典URL"],
                "category_source_locator": category_row["出典ページ・該当箇所"],
                "item_evidence_source_id": evidence["source_id"],
                "item_evidence_url": evidence["公式URL"],
                "item_evidence_locator": branch["locator"],
                "確認日": CHECKED,
                "mapping_status": "APP_READY",
                "evidence_scope": "ITEM_SPECIFIC",
                "branch_review_status": "COMPLETE",
                "reviewed_date": CHECKED,
                "reviewed_by": REVIEWER,
                "備考": "M099 40品目APP_READY。地域差・材質差・特殊回収差を必要最小限の条件枝で保持。",
            })
            review.append({
                "municipality_id": MID,
                "internal_item_id": item_id,
                "branch_order": str(order),
                "canonical_name": master["一般管理用名称"],
                "display_name": master["教材表示名"],
                "official_item_wording": branch["official_item_wording"],
                "category_id": branch["category_id"],
                "category_name": category_row["自治体正式名称"],
                "condition": branch["condition"],
                "preparation": branch["preparation"],
                "exception_destination": branch["exception_destination"],
                "evidence_basis": branch["evidence_basis"],
                "item_evidence_source_id": evidence["source_id"],
                "item_evidence_url": evidence["公式URL"],
                "item_evidence_locator": branch["locator"],
                "branch_review_status": "COMPLETE",
                "checked_date": CHECKED,
                "reviewer": REVIEWER,
                "note": "教材UIには詳細条件を出さず、既存の地域variantを学習者向け正答として維持。",
            })
        evidence = SOURCE_BY_ID[branches[0]["source_id"]]
        coverage.append({
            "municipality_id": MID,
            "internal_item_id": item_id,
            "coverage_status": "APP_READY",
            "mapping_branch_count": str(len(branches)),
            "branch_completeness_confirmed": "TRUE",
            "evidence_scope": "ITEM_SPECIFIC",
            "item_evidence_source_id": evidence["source_id"],
            "item_evidence_url": evidence["公式URL"],
            "item_evidence_locator": f"M099 APP_READY review {item_id}: {len(branches)}条件枝を全件確認",
            "reviewed_date": CHECKED,
            "reviewed_by": REVIEWER,
            "notes": "全条件枝COMPLETE。",
        })
    return mappings, coverage, review


def sync_canonical(batch_municipality, batch_categories, batch_sources, batch_qa, batch_review) -> int:
    m_fields, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    c_fields, categories = read_csv(RESEARCH / "02_categories_master.csv")
    s_fields, sources = read_csv(RESEARCH / "03_sources_master.csv")
    q_fields, qa = read_csv(RESEARCH / "06_qa_log.csv")
    map_fields, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    cov_fields, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")
    rev_fields, review_evidence = read_csv(RESEARCH / "08_category_review_evidence.csv")

    municipalities = [r for r in municipalities if r.get("municipality_id") != MID] + [batch_municipality]
    categories = [r for r in categories if r.get("municipality_id") != MID] + batch_categories
    sources = [r for r in sources if r.get("municipality_id") != MID] + batch_sources
    qa = [r for r in qa if r.get("municipality_id") != MID] + [batch_qa]
    review_evidence = [r for r in review_evidence if r.get("municipality_id") != MID] + batch_review

    app_mappings, app_coverage, app_review = build_app_ready_rows()
    mappings = [r for r in mappings if r.get("municipality_id") != MID] + app_mappings
    coverage = [r for r in coverage if r.get("municipality_id") != MID] + app_coverage

    write_csv(RESEARCH / "04_municipalities_research.csv", m_fields or MUNICIPALITY_FIELDS, sorted(municipalities, key=lambda r: r["municipality_id"]))
    write_csv(RESEARCH / "02_categories_master.csv", c_fields or CATEGORY_FIELDS, sorted(categories, key=lambda r: (r["municipality_id"], r["category_id"])))
    write_csv(RESEARCH / "03_sources_master.csv", s_fields or SOURCE_FIELDS, sorted(sources, key=lambda r: (r["municipality_id"], r["source_id"])))
    write_csv(RESEARCH / "06_qa_log.csv", q_fields or QA_FIELDS, sorted(qa, key=lambda r: r["municipality_id"]))
    write_csv(RESEARCH / "05_item_mapping_master.csv", map_fields or MAPPING_FIELDS, sorted(mappings, key=lambda r: (r["municipality_id"], r["internal_item_id"], int(r.get("branch_order") or 0), r["mapping_id"])))
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", cov_fields or COVERAGE_FIELDS, sorted(coverage, key=lambda r: (r["municipality_id"], r["internal_item_id"])))
    write_csv(RESEARCH / "08_category_review_evidence.csv", rev_fields or CATEGORY_REVIEW_EVIDENCE_FIELDS, sorted(review_evidence, key=lambda r: (r["municipality_id"], r["review_evidence_id"])))
    write_csv(REVIEW_PATH, REVIEW_FIELDS, app_review)
    return len(app_review)


def update_application(branch_count: int) -> None:
    # Standard scoring scope is used as the APP_READY gate; learner scoring remains regional.
    scope_path = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
    fields, rows = read_csv(scope_path)
    rows = [r for r in rows if r.get("municipality_id") != MID]
    rows.append({
        "municipality_id": MID,
        "municipality_name": "福山市",
        "lesson_mode": "ONLINE_CLASS",
        "scoring_status": "APP_READY",
        "required_item_count": "40",
        "required_branch_count": str(branch_count),
        "review_source": "data/research/app_readiness/m099_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "40品目canonicalはAPP_READY。固定10画像の正誤判定は既存3地域variantを使用し、municipality-wideの仮正答を作らない。",
    })
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
    write_csv(priority_path, fields, rows)

    deferred_path = ROOT / "data/master/05_deferred_municipalities.csv"
    fields, rows = read_csv(deferred_path)
    rows = [r for r in rows if r.get("municipality_id") != MID]
    write_csv(deferred_path, fields, rows)

    # Register the user-provided current Utsumi calendar in the regional evidence layer.
    variant_sources_path = RESEARCH / "lesson_readiness/lesson_variant_sources.csv"
    fields, rows = read_csv(variant_sources_path)
    s09 = SOURCE_BY_ID["S-M099-09"]
    rows = [r for r in rows if not (r.get("municipality_id") == MID and r.get("source_id") == "S-M099-09")] + [s09]
    write_csv(variant_sources_path, fields, rows)

    district_path = ROOT / "data/app/district_scopes.csv"
    fields, rows = read_csv(district_path)
    for row in rows:
        if row.get("district_scope_id") == "DS-M099-02":
            row["official_source_id"] = "S-M099-09"
            row["official_url"] = UTSUMI_2026_URL
            row["official_locator"] = "1頁『2026年度（令和8年度）家庭ごみ収集日程表（内海町）』分別凡例・拠点回収案内"
            row["note"] = "2026年度内海町日程表で現行区分を固定。沼隈町と固定10主要正答が同じため同一lesson group。"
    write_csv(district_path, fields, rows)


def main() -> None:
    batch_municipality, batch_categories, batch_sources, batch_qa, batch_review = prepare_batch10()
    branch_count = sync_canonical(batch_municipality, batch_categories, batch_sources, batch_qa, batch_review)
    update_application(branch_count)
    print(f"M099_APP_READY_BUILT items=40 branches={branch_count} categories={len(CATEGORIES)} ordinary_sources={len(SOURCES)}")


if __name__ == "__main__":
    main()
