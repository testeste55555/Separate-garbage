#!/usr/bin/env python3
"""Promote Shizuoka City (M020) to full 40-item APP_READY using current 2026 rules.

This promotion intentionally replaces the older category-level M020 item projections.
The 2026 rule changes are material: used batteries are now handled through the current
不燃・粗大ごみ route (with dedicated separation/labeling), spray cans remain a resource
route, and household PCs are accepted by the city's used-small-appliance program.

District differences in containers/collection channels are retained in evidence notes,
but no learner regional variant is created because the fixed-10 answer categories do
not change between 葵・駿河 and 清水.
"""
from __future__ import annotations

from dataclasses import dataclass
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
MASTER = ROOT / "data/master"
APP = ROOT / "data/app"
MID = "M020"
CHECKED = "2026-08-31"
REVIEWER = "OPENAI_M020_APP_READY_V1"
AUDIT_PATH = RESEARCH / "app_readiness/m020_item_review.csv"
SCOPE_PATH = APP / "lesson_mode_app_ready_scope.csv"
IMAGE_PATH = APP / "item_image_mapping_pilot_top8.csv"
PRIORITY_PATH = MASTER / "07_implementation_priority.csv"
COMPANY_PATH = APP / "company_municipality_mapping.csv"
VARIANT_PATH = APP / "lesson_variant_groups.csv"
BATCH = RESEARCH / "batches/batch_02"

AUDIT_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "canonical_name",
    "display_name", "official_item_wording", "category_id", "category_name",
    "condition", "preparation", "exception_destination", "evidence_basis",
    "item_evidence_source_id", "item_evidence_url", "item_evidence_locator",
    "branch_review_status", "checked_date", "reviewer", "note",
]

IMAGE_FIELDS = [
    "pair_order", "municipality_id", "municipality_name", "internal_item_id",
    "canonical_name", "display_name", "review_status", "evidence_basis",
    "category_id", "category_name", "condition", "preparation",
    "exception_destination", "item_evidence_source_id", "item_evidence_url",
    "item_evidence_locator", "checked_date", "reviewer", "note",
]
IMAGE_ITEMS = ("I001", "I007", "I013", "I004", "I006", "I031", "I029", "I014", "I033", "I017")

# Current category-system sources (ordinary category/evidence layer).
URL_GUIDE = "https://www.city.shizuoka.lg.jp/gomi/s000668.html"
URL_NONBURNABLE = "https://www.city.shizuoka.lg.jp/gomi/s000679.html"
URL_RESOURCES = "https://www.city.shizuoka.lg.jp/gomi/s000677.html"
URL_SMALL_APPLIANCE = "https://www.city.shizuoka.lg.jp/gomi/s000774.html"
URL_HOME_APPLIANCE = "https://www.city.shizuoka.lg.jp/gomi/s000683.html"
URL_PET = "https://www.city.shizuoka.lg.jp/gomi/s012184.html"
URL_PRODUCT_PLASTIC = "https://www.city.shizuoka.lg.jp/s2487/seihinpura.html"

# Item-specific current official sources.
ITEM_URLS = {
    "IS-M020-04": ("ペットボトル", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/00258.html", "PETボトルの分別区分"),
    "IS-M020-05": ("ペットボトルキャップの捨て方について", "https://www.city.shizuoka.lg.jp/s2487/faq/s000010.html", "キャップは可燃ごみ"),
    "IS-M020-06": ("ペットボトルのラベル", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/03591.html", "ラベルは可燃ごみ"),
    "IS-M020-07": ("アルミ缶", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/00121.html", "アルミ缶は資源物（缶）"),
    "IS-M020-08": ("スチール缶", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/01988.html", "スチール缶は資源物（缶）"),
    "IS-M020-09": ("びん・缶・スプレー缶・小物金属類の出し方", URL_RESOURCES, "びんと割れたびんの分岐"),
    "IS-M020-10": ("食品トレイ", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/01860.html", "食品トレイは可燃ごみ"),
    "IS-M020-11": ("使用済プラスチック製品のリサイクル", URL_PRODUCT_PLASTIC, "白色トレイ・弁当容器・容器包装プラは製品プラBOX対象外"),
    "IS-M020-12": ("レジ袋", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/04259.html", "レジ袋は可燃ごみ"),
    "IS-M020-13": ("発泡スチロール", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/03084.html", "発泡スチロールは可燃ごみ"),
    "IS-M020-14": ("2026年3月改訂 ごみの分け方早見表（葵・駿河）", "https://www.city.shizuoka.lg.jp/documents/667/p17-22gominowakekatahayamihyouaosuru.pdf", "新聞・紙おむつ・刃物・剪定枝等の現行早見表"),
    "IS-M020-15": ("段ボール（アルミ加工なし）", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/02362.html", "通常段ボールは資源物（古紙・雑がみ類）"),
    "IS-M020-16": ("雑誌", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/01530.html", "雑誌は資源物（古紙・雑がみ類）"),
    "IS-M020-17": ("菓子箱（紙製）", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/00708.html", "紙製菓子箱は資源物（古紙・雑がみ類）"),
    "IS-M020-18": ("紙パック（アルミ加工なし）", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/00831.html", "アルミ加工なし紙パックは資源物"),
    "IS-M020-19": ("紙パック（アルミ加工あり）", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/00830.html", "アルミ加工あり紙パックは可燃ごみ"),
    "IS-M020-20": ("生ごみ", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/02832.html", "生ごみは可燃ごみ・水切り"),
    "IS-M020-21": ("感染症対策を伴う家庭ごみの出し方", "https://www.city.shizuoka.lg.jp/gomi/s009160.html", "鼻水等が付着したティッシュは袋を密閉して可燃ごみ"),
    "IS-M020-22": ("紙おむつ", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/00815.html", "紙おむつは可燃ごみ"),
    "IS-M020-23": ("衣類", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/00210.html", "衣類は可燃ごみ・古着回収も利用可"),
    "IS-M020-24": ("傘", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/00695.html", "傘は不燃・粗大ごみ"),
    "IS-M020-25": ("陶磁器", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/02399.html", "陶磁器は不燃・粗大ごみ"),
    "IS-M020-26": ("ガラスコップ", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/01367.html", "ガラス製品は不燃・粗大ごみ"),
    "IS-M020-27": ("びん・缶・スプレー缶・小物金属類の出し方", URL_RESOURCES, "割れたびん・コップ・耐熱ガラスは不燃・粗大ごみ"),
    "IS-M020-28": ("包丁", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/03713.html", "包丁は不燃・粗大ごみ・刃を紙で包む"),
    "IS-M020-29": ("使用済電池類の排出方法の拡充", "https://www.city.shizuoka.lg.jp/documents/57503/20251210010.pdf", "2026年の乾電池・充電式電池等の不燃・粗大ごみルートと回収BOX"),
    "IS-M020-30": ("電池（ボタン型：型式SR・PR・LR）", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/02629.html", "ボタン電池は不燃・粗大ごみ・協力店/回収BOX併用可"),
    "IS-M020-31": ("モバイルバッテリー", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/04089.html", "モバイルバッテリーは不燃・粗大ごみ"),
    "IS-M020-32": ("蛍光管", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/01177.html", "蛍光管は不燃・粗大ごみ・別出し"),
    "IS-M020-33": ("白熱電球", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/02990.html", "白熱電球は不燃・粗大ごみ"),
    "IS-M020-34": ("LED電球", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/00393.html", "LED電球は不燃・粗大ごみ"),
    "IS-M020-35": ("スプレー缶", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/02049.html", "スプレー缶は資源物・使い切り・穴あけ不要"),
    "IS-M020-36": ("使い捨てライター", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/04161.html", "ライターは不燃・粗大ごみ・別袋"),
    "IS-M020-37": ("使用済小型家電リサイクル", URL_SMALL_APPLIANCE, "パソコン以外は不燃・粗大ごみでも排出可"),
    "IS-M020-38": ("不燃・粗大ごみの出し方", URL_NONBURNABLE, "充電式電池を取り外せない電化製品は電話申込"),
    "IS-M020-39": ("布団", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/03413.html", "布団は可燃ごみ"),
    "IS-M020-40": ("不用になった家電4品目", URL_HOME_APPLIANCE, "家電4品目は家電リサイクル法ルート"),
    "IS-M020-41": ("家庭用パソコン", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/03029.html", "家庭用PCは使用済小型家電リサイクル・不燃粗大不可"),
    "IS-M020-42": ("使用済み食用油", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/02950.html", "食用油は固化・吸収して可燃ごみ、廃食油回収も可"),
    "IS-M020-43": ("剪定枝", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/02186.html", "直径20cm以下・長さ1m以下にして可燃ごみ"),
    "IS-M020-44": ("段ボール（アルミ加工あり）", "https://www.city.shizuoka.lg.jp/gomi/hinmoku/02361.html", "アルミ加工段ボールは可燃ごみ"),
}


@dataclass(frozen=True)
class Branch:
    category_id: str
    source_id: str
    locator: str
    wording: str
    condition: str
    preparation: str
    exception: str
    basis: str = "DIRECT_ITEM"
    note: str = ""


def b(category_id: str, source_id: str, locator: str, wording: str,
      condition: str, preparation: str, exception: str,
      basis: str = "DIRECT_ITEM", note: str = "") -> Branch:
    return Branch(category_id, source_id, locator, wording, condition, preparation, exception, basis, note)


RULES: dict[str, list[Branch]] = {
    "I001": [b("C-M020-10", "IS-M020-04", "分別区分：葵区・駿河区/清水区ともペットボトル", "ペットボトル", "PETボトル識別表示のある飲料等のボトル", "キャップ・ラベルを外し、水洗いする", "葵・駿河区は回収拠点、清水区は集積所の専用回収箱")],
    "I002": [b("C-M020-01", "IS-M020-05", "回答：ペットボトルキャップは可燃ごみ", "ペットボトルのキャップ", "ペットボトルから外したプラスチック製キャップ", "ボトルから外して可燃ごみへ出す", "ペットボトル・製品プラ回収BOXには入れない")],
    "I003": [b("C-M020-01", "IS-M020-06", "分別区分：両地域とも可燃ごみ", "ペットボトルのラベル", "ペットボトルから外したラベル", "ボトルから外して可燃ごみへ出す", "ペットボトル回収には混ぜない")],
    "I004": [b("C-M020-09", "IS-M020-07", "分別区分：資源物（缶）", "アルミ缶", "家庭の飲料・食品用アルミ缶", "中身を空にして出す", "スプレー缶は別に分ける")],
    "I005": [b("C-M020-09", "IS-M020-08", "分別区分：資源物（缶）", "スチール缶", "家庭の飲料・食品用スチール缶", "中身を空にして出す", "スプレー缶は別に分ける")],
    "I006": [b("C-M020-08", "IS-M020-09", "びんの出し方・回収対象外", "ガラスびん", "飲食用等のびんで割れていないもの", "キャップを外し、中を水洗いする", "割れたびん・コップ・耐熱ガラス等は不燃・粗大ごみ")],
    "I007": [b("C-M020-01", "IS-M020-10", "分別区分：両地域とも可燃ごみ", "白色食品トレー", "白色の食品トレイ", "食品残渣を除いて可燃ごみへ出す", "製品プラスチック回収BOXの対象外")],
    "I008": [b("C-M020-01", "IS-M020-10", "食品トレイの分別区分：両地域とも可燃ごみ", "色柄食品トレー", "色柄の食品トレイ", "食品残渣を除いて可燃ごみへ出す", "製品プラスチック回収BOXの対象外", "OFFICIAL_CATEGORY_RULE")],
    "I009": [b("C-M020-01", "IS-M020-11", "回収BOXに持込できないもの：お弁当の容器", "弁当容器", "プラスチック製の弁当容器", "食品残渣を除いて可燃ごみへ出す", "製品プラスチック回収BOXの対象外", "OFFICIAL_RULE_DERIVED")],
    "I010": [b("C-M020-01", "IS-M020-11", "容器包装プラスチックは製品プラ回収対象外という現行ルール", "お菓子の袋", "菓子のプラスチック製容器包装袋", "中身を除いて可燃ごみへ出す", "製品プラスチック回収BOXの対象外", "OFFICIAL_RULE_DERIVED")],
    "I011": [b("C-M020-01", "IS-M020-12", "分別区分：両地域とも可燃ごみ", "レジ袋", "家庭から出るレジ袋", "中身を除いて可燃ごみへ出す", "製品プラスチック回収BOXには入れない")],
    "I012": [b("C-M020-01", "IS-M020-13", "分別区分：両地域とも可燃ごみ", "発泡スチロール", "家庭から出る発泡スチロール", "テープ等の異物を除いて可燃ごみへ出す", "発泡スチロールカッター等の製品は別品目")],
    "I013": [b("C-M020-12", "IS-M020-14", "早見表：新聞紙→古紙・雑がみ", "新聞", "新聞・折込広告", "種類別にまとめて古紙回収へ出す", "汚れ・加工等で古紙回収できない紙は可燃ごみ")],
    "I014": [
        b("C-M020-14", "IS-M020-15", "分別区分：資源物（古紙・雑がみ類）", "段ボール", "アルミ加工のない通常の段ボール", "折りたたみ、古紙回収へ出す", "アルミ加工ありは可燃ごみ"),
        b("C-M020-01", "IS-M020-44", "分別区分：アルミ加工ありは可燃ごみ", "アルミ加工段ボール", "内側等にアルミ加工がある段ボール", "可燃ごみとして出す", "アルミ加工なしは資源物（古紙・雑がみ類）"),
    ],
    "I015": [b("C-M020-13", "IS-M020-16", "分別区分：資源物（古紙・雑がみ類）", "雑誌", "家庭から出る雑誌", "紙以外の付属物を外して古紙回収へ出す", "汚れ・加工等で古紙回収できない紙は可燃ごみ")],
    "I016": [b("C-M020-13", "IS-M020-17", "分別区分：資源物（古紙・雑がみ類）", "紙製菓子箱", "紙製で資源化できる菓子箱・紙箱", "紙以外の付属物を外して古紙回収へ出す", "汚れ・加工等で古紙回収できないものは可燃ごみ")],
    "I017": [
        b("C-M020-15", "IS-M020-18", "分別区分：アルミ加工なしは資源物（古紙・雑がみ類）", "紙パック（アルミ加工なし）", "内側にアルミ加工のない飲料用紙パック", "洗浄・乾燥し、紙以外の付属物を外して回収へ出す", "アルミ加工ありは可燃ごみ"),
        b("C-M020-01", "IS-M020-19", "分別区分：アルミ加工ありは可燃ごみ", "紙パック（アルミ加工あり）", "内側にアルミ加工がある紙パック", "可燃ごみとして出す", "アルミ加工なしは資源物（古紙・雑がみ類）"),
    ],
    "I018": [b("C-M020-01", "IS-M020-20", "分別区分・注意点", "生ごみ", "家庭から出る生ごみ", "水分をよく切って指定袋へ入れる", "資源回収対象物を混ぜない")],
    "I019": [b("C-M020-01", "IS-M020-21", "鼻水等が付着したティッシュの排出方法", "使用済みティッシュ", "鼻水等が付着した使用済みティッシュ", "必要に応じ小袋を密閉し、指定の可燃ごみ袋へ入れる", "在宅医療の注射針等は混ぜない")],
    "I020": [b("C-M020-01", "IS-M020-22", "分別区分：可燃ごみ", "紙おむつ", "家庭から出る紙おむつ", "汚物を取り除いて可燃ごみへ出す", "衛生上、使用済み実物は教材に使用しない")],
    "I021": [b("C-M020-01", "IS-M020-23", "分別区分：可燃ごみ", "衣類", "家庭から出る衣類", "指定袋へ入れて可燃ごみへ出す", "地域の古着回収を利用できる場合はそちらも可")],
    "I022": [b("C-M020-02", "IS-M020-24", "分別区分：不燃・粗大ごみ", "傘", "家庭から出る傘", "複数本はまとめ、戸別/集積所の不燃・粗大ルールに従う", "小物金属類の資源回収には出さない")],
    "I023": [b("C-M020-02", "IS-M020-25", "分別区分：不燃・粗大ごみ", "陶磁器", "茶わん等の陶磁器", "不燃・粗大ごみとして出す", "割れて危険な部分は安全に保護する")],
    "I024": [b("C-M020-02", "IS-M020-26", "分別区分：不燃・粗大ごみ", "ガラス製品", "コップ等のガラス製品", "不燃・粗大ごみとして出す", "飲食用の割れていないびんは資源物（びん）")],
    "I025": [b("C-M020-02", "IS-M020-27", "びん回収対象外：割れたびん・コップ等は不燃・粗大ごみ", "割れたガラス", "割れたびん・ガラス製品", "危険がないよう紙等で保護して不燃・粗大ごみへ出す", "割れていない飲食用びんは資源物（びん）", "OFFICIAL_RULE_DERIVED")],
    "I026": [b("C-M020-02", "IS-M020-28", "分別区分・注意点：刃を紙等で包む", "包丁", "家庭用の包丁・刃物", "刃を紙等で包んで不燃・粗大ごみへ出す", "小物金属類の資源回収には出さない")],
    "I027": [b("C-M020-02", "IS-M020-29", "令和8年1月以降：乾電池等を不燃・粗大ごみとして分別", "乾電池", "乾電池（使い切り電池）", "電池だけを中が見える袋に入れ『電池入り』と表示し、他のごみと分ける", "令和8年4月から端子を絶縁して使用済小型家電回収BOXにも出せる")],
    "I028": [b("C-M020-02", "IS-M020-30", "分別区分・注意点：ボタン電池", "ボタン電池", "型式SR・PR・LRのボタン電池", "中が見える小袋に入れ『電池入り』と表示して他のものと分ける", "絶縁して使用済小型家電回収BOX、又は回収協力店も利用可")],
    "I029": [b("C-M020-02", "IS-M020-31", "分別区分・注意点：モバイルバッテリー", "モバイルバッテリー", "家庭で使用したモバイルバッテリー", "不燃・粗大ごみの申込ルールに従い、他のごみと分けて安全に出す", "リサイクルマークが確認でき膨張・破損していないものは回収協力店等も利用可")],
    "I030": [b("C-M020-02", "IS-M020-32", "分別区分・注意点：蛍光管", "蛍光管", "家庭用の蛍光管・蛍光灯", "購入時の箱等で保護するか中が見える袋に入れ、他のごみと分ける", "電球は同じ不燃・粗大ごみでも蛍光管とは別品目として確認")],
    "I031": [
        b("C-M020-02", "IS-M020-33", "分別区分：白熱電球は不燃・粗大ごみ", "白熱電球", "白熱電球", "破損しないよう扱い、不燃・粗大ごみへ出す", "蛍光管は蛍光管の別出しルールに従う"),
        b("C-M020-02", "IS-M020-34", "分別区分：LED電球は不燃・粗大ごみ", "LED電球", "LED電球", "破損しないよう扱い、不燃・粗大ごみへ出す", "蛍光管は蛍光管の別出しルールに従う"),
    ],
    "I032": [b("C-M020-07", "IS-M020-35", "分別区分・注意点：資源物（スプレー缶）", "スプレー缶", "家庭から出るスプレー缶・カセットボンベ", "中身を必ず使い切り、穴を開けずに出す", "飲料缶等とは分け、地区指定の袋/専用ネットへ出す")],
    "I033": [b("C-M020-02", "IS-M020-36", "分別区分・注意点：ライター", "使い捨てライター", "家庭から出る使い捨てライター", "中が見える小袋に入れ、他の不燃・粗大ごみと分けて出す", "他の不燃・粗大ごみと同じ袋に混ぜない")],
    "I034": [b("C-M020-02", "IS-M020-37", "注意事項：パソコン以外の小型家電は不燃・粗大ごみとしても排出可", "小型家電", "パソコン以外の家庭用小型家電", "取り外せる電池は外して不燃・粗大ごみへ出す", "対象17品目は使用済小型家電回収も利用可")],
    "I035": [b("C-M020-02", "IS-M020-38", "電話申込対象：充電式電池の取りはずしが困難な電化製品", "充電池を外せない小型家電", "充電式電池を取り外すことが困難な電化製品", "不燃・粗大ごみ受付へ電話で申し込み、指示に従って分けて出す", "回収対象かつ膨張等がない製品は小型家電回収ルートを利用できる場合がある")],
    "I036": [b("C-M020-01", "IS-M020-39", "分別区分・注意点：布団", "布団", "家庭から出る布団", "指定袋に入れるか、ひもで縛り『不用』表示して可燃ごみへ出す", "一度に多量の場合は市の持込等を確認")],
    "I037": [b("C-M020-17", "IS-M020-40", "家電リサイクル法対象4品目", "家電4品目", "エアコン・テレビ・冷蔵庫/冷凍庫・洗濯機/衣類乾燥機", "市の通常収集へ出さず家電リサイクル法の手続を行う", "販売店・指定引取場所等の家電リサイクル法ルートを利用")],
    "I038": [b("C-M020-16", "IS-M020-41", "分別区分：使用済小型家電リサイクル（不燃・粗大ごみ不可）", "家庭用パソコン", "家庭用パソコン・対象モニター", "個人情報を消去して市の使用済小型家電回収へ出す", "市回収を利用しない場合はメーカー・PC3R等の回収ルート")],
    "I039": [b("C-M020-01", "IS-M020-42", "分別区分・注意点：食用油", "使用済み食用油", "家庭から出る使用済み食用油", "固化剤で固めるか紙・布等に染み込ませて可燃ごみへ出す", "地域の廃食油回収を利用できる場合はそちらも可")],
    "I040": [b("C-M020-01", "IS-M020-43", "分別区分・注意点：剪定枝", "剪定枝", "直径20cm以下・長さ1m以下にした家庭の剪定枝", "指定寸法以下に切り、袋に入れるか束ねて可燃ごみへ出す", "条件を超える枝はそのまま出さず指定寸法以下にする")],
}


def source_row(source_id: str, title: str, url: str, used: str, *, item: bool = False) -> dict[str, str]:
    return {
        "municipality_id": MID,
        "source_id": source_id,
        "資料名": title,
        "資料種別": "自治体公式PDF" if url.lower().endswith(".pdf") else "自治体公式Webページ",
        "公式URL": url,
        "発行主体": "静岡市",
        "対象年度": "令和8年度／取得時点現行",
        "ページ更新日": "",
        "取得確認日": CHECKED,
        "使用した情報": used,
        "優先度": "1" if not item else "2",
        "現行性": "現行",
        "備考": "M020 40品目APP_READYの品目別公式根拠。" if item else "M020 2026現行区分体系の再監査根拠。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    }


NORMAL_SOURCES = [
    source_row("S-M020-04", "不燃・粗大ごみの出し方", URL_NONBURNABLE, "2026年使用済電池類・不燃粗大・申込ルール"),
    source_row("S-M020-05", "びん・缶・スプレー缶・小物金属類の出し方", URL_RESOURCES, "資源物4系統と地区別排出方法"),
    source_row("S-M020-06", "使用済小型家電リサイクルの回収品目・方法・場所", URL_SMALL_APPLIANCE, "小型家電・PC・電池・回収BOX"),
    source_row("S-M020-07", "不用になった家電4品目", URL_HOME_APPLIANCE, "家電リサイクル法対象品"),
    source_row("S-M020-08", "ペットボトルの出し方", URL_PET, "PETの現行区分と葵駿河/清水の出し方差"),
    source_row("S-M020-09", "使用済プラスチック製品のリサイクル", URL_PRODUCT_PLASTIC, "製品プラBOX対象と容器包装等の対象外"),
]
ITEM_SOURCES = [source_row(source_id, title, url, used, item=True) for source_id, (title, url, used) in ITEM_URLS.items()]
NEW_SOURCES = NORMAL_SOURCES + ITEM_SOURCES


def updated_category(row: dict[str, str]) -> dict[str, str]:
    row = dict(row)
    cid = row["category_id"]
    if cid == "C-M020-01":
        row.update({
            "自治体正式名称": "可燃ごみ", "category_group": "可燃ごみ",
            "代表品目": "生ごみ・紙くず・衣類・容器包装プラスチック・布団・剪定枝",
            "入れてはいけない物": "資源物・不燃粗大ごみ・電池類・家電4品目",
            "適用条件": "家庭から出る可燃ごみ", "条件外の扱い": "品目別の現行区分へ",
            "出す前の処理": "生ごみは水切りし、品目別の前処理を行う",
            "袋・容器のルール": "静岡市家庭用指定袋又は認定袋",
            "注意事項": "区・地区ごとの収集ルールに従う", "source_id": "S-M020-01",
            "出典URL": URL_GUIDE, "出典ページ・該当箇所": "2026年3月改訂ガイド・可燃ごみ",
            "確認日": CHECKED, "rule_status": "CURRENT", "effective_to": "", "ui_role": "SORT_BUCKET",
        })
    elif cid == "C-M020-02":
        row.update({
            "自治体正式名称": "不燃・粗大ごみ", "category_group": "不燃・粗大ごみ",
            "代表品目": "陶磁器・ガラス製品・傘・刃物・電池類・蛍光管・ライター・小型家電",
            "入れてはいけない物": "スプレー缶・資源びん缶・家電4品目・家庭用パソコン",
            "適用条件": "家庭から出る不燃物・粗大ごみ及び指定された電池等",
            "条件外の扱い": "資源物・小型家電・家電リサイクル等の指定経路へ",
            "出す前の処理": "電池・蛍光管・ライター等は他のごみと分け、品目別の安全処理を行う",
            "袋・容器のルール": "地区の戸別/集積所ルールと品目別の別袋・表示に従う",
            "注意事項": "2026年1月から電池類の出し方変更、2026年4月から金属/その他不燃物は同袋可",
            "source_id": "S-M020-04", "出典URL": URL_NONBURNABLE,
            "出典ページ・該当箇所": "不燃・粗大ごみの収集／2026年使用済電池類・分別変更",
            "確認日": CHECKED, "rule_status": "CURRENT", "effective_to": "", "ui_role": "SORT_BUCKET",
        })
    elif cid == "C-M020-03":
        row.update({
            "自治体正式名称": "小物金属類", "category_group": "資源物",
            "代表品目": "なべ・やかん・フライパン・金属の多い小型家電等",
            "入れてはいけない物": "刃物・釘・ねじ・傘・家電4品目・パソコン",
            "適用条件": "家庭から出る対象小物金属類", "条件外の扱い": "不燃・粗大ごみ等へ",
            "出す前の処理": "電池を抜き、地区指定の出し方に従う",
            "袋・容器のルール": "指定袋・認定袋又は不用表示",
            "source_id": "S-M020-05", "出典URL": URL_RESOURCES,
            "出典ページ・該当箇所": "小物金属類の出し方・対象品・対象外品",
            "確認日": CHECKED, "rule_status": "CURRENT", "effective_to": "", "ui_role": "SORT_BUCKET",
        })
    elif cid in {"C-M020-04", "C-M020-05", "C-M020-06"}:
        # Old separate 危険・有害 leaves are kept only as history.  Current 2026
        # resident-facing routing is the broad 不燃・粗大 category with mandatory
        # item-specific separation, which is encoded in the 40-item branches.
        row.update({"rule_status": "RETIRED", "ui_role": "HIDDEN", "effective_to": "2025-12-31"})
    elif cid == "C-M020-07":
        row.update({
            "自治体正式名称": "スプレー缶", "category_group": "資源物",
            "代表品目": "スプレー缶・カセットボンベ", "入れてはいけない物": "飲料缶等の一般缶",
            "適用条件": "中身を使い切った家庭用スプレー缶等", "条件外の扱い": "中身を使い切ってから出す",
            "出す前の処理": "中身を使い切り、穴を開けない",
            "袋・容器のルール": "葵・駿河は中が見える別袋表示、清水は専用回収ネット",
            "source_id": "S-M020-05", "出典URL": URL_RESOURCES,
            "出典ページ・該当箇所": "スプレー缶の出し方",
            "確認日": CHECKED, "rule_status": "CURRENT", "effective_to": "", "ui_role": "SORT_BUCKET",
        })
    elif cid in {"C-M020-08", "C-M020-09"}:
        name = "びん" if cid.endswith("08") else "缶"
        row.update({
            "自治体正式名称": name, "category_group": "資源物",
            "source_id": "S-M020-05", "出典URL": URL_RESOURCES,
            "出典ページ・該当箇所": f"{name}の出し方",
            "確認日": CHECKED, "rule_status": "CURRENT", "effective_to": "", "ui_role": "SORT_BUCKET",
        })
    elif cid == "C-M020-10":
        row.update({
            "自治体正式名称": "ペットボトル", "category_group": "資源物",
            "collection_channel": "DISTRICT_DEPENDENT",
            "代表品目": "PETボトル識別表示のある飲料等のボトル",
            "入れてはいけない物": "キャップ・ラベル・汚れが落ちない対象外ボトル",
            "適用条件": "PETボトル識別表示の対象品", "条件外の扱い": "品目別に可燃ごみ等へ",
            "出す前の処理": "キャップ・ラベルを外し水洗いする",
            "袋・容器のルール": "葵・駿河は回収拠点、清水は集積所の専用回収箱",
            "source_id": "S-M020-08", "出典URL": URL_PET,
            "出典ページ・該当箇所": "葵・駿河区／清水区のペットボトルの出し方",
            "確認日": CHECKED, "rule_status": "CURRENT", "effective_to": "", "ui_role": "SORT_BUCKET",
        })
    elif cid == "C-M020-16":
        row.update({
            "自治体正式名称": "使用済小型家電", "category_group": "使用済小型家電",
            "代表品目": "パソコン・携帯電話・デジタルカメラ等の対象17品目",
            "入れてはいけない物": "家電4品目・膨張した電池内蔵製品・電球・蛍光灯",
            "適用条件": "家庭から出る回収対象小型家電", "条件外の扱い": "パソコン以外は不燃・粗大ごみも可",
            "出す前の処理": "個人情報を消去し、取り外せる電池は外す",
            "袋・容器のルール": "回収ボックス又は直接回収場所のルールに従う",
            "source_id": "S-M020-06", "出典URL": URL_SMALL_APPLIANCE,
            "出典ページ・該当箇所": "回収品目・注意事項・回収方法",
            "確認日": CHECKED, "rule_status": "CURRENT", "effective_to": "", "ui_role": "REFERENCE_ONLY",
        })
    elif cid == "C-M020-17":
        row.update({
            "自治体正式名称": "市では収集・処理できないごみ", "category_group": "市では収集・処理できないごみ",
            "代表品目": "家電4品目・処理困難物", "入れてはいけない物": "市の通常収集対象ごみ・家庭用パソコン",
            "適用条件": "市が収集・処理しない指定品", "条件外の扱い": "品目ごとの通常区分へ",
            "出す前の処理": "販売店・メーカー・指定引取場所等の指定経路を確認",
            "袋・容器のルール": "市の通常収集へ出さない",
            "注意事項": "家庭用パソコンは使用済小型家電回収対象であり、この区分に含めない",
            "source_id": "S-M020-01", "出典URL": URL_GUIDE,
            "出典ページ・該当箇所": "市では収集・処理できないごみ",
            "確認日": CHECKED, "rule_status": "CURRENT", "effective_to": "", "ui_role": "EXCLUDED_NOTICE",
        })
    else:
        # Paper parent/subcategories remain structurally valid; refresh their audit date.
        row["確認日"] = CHECKED
    return row


def update_municipality_review(row: dict[str, str]) -> dict[str, str]:
    row = dict(row)
    if row["municipality_id"] != MID:
        return row
    row["最終確認日"] = CHECKED
    row["備考"] = "2026年3月改訂ガイドと2026年電池類変更を再監査。地区差は収集方法に保持し、固定10の分別正答は市内共通。"
    row["reviewed_category_count"] = "12"
    row["category_count_basis"] = "2026年3月改訂ガイドの現行葉区分を再監査。旧『危険・有害』3行は2025年末で履歴化し、2026年は不燃・粗大ごみ内の品目別分離として扱う。"
    row["category_count_verified"] = "TRUE"
    row["category_count_check_status"] = "MANUAL_INDEX_REVIEW"
    row["category_count_review_id"] = "CR-M020-CATEGORY-COVERAGE"
    row["category_count_reviewed_date"] = CHECKED
    row["category_count_reviewed_by"] = REVIEWER
    return row


def add_review_evidence(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    evidence_id = "CRE-M020-2026-CURRENT-INDEX"
    rows = [dict(row) for row in rows if row.get("review_evidence_id") != evidence_id]
    rows.append({
        "review_evidence_id": evidence_id,
        "review_id": "CR-M020-CATEGORY-COVERAGE",
        "municipality_id": MID,
        "source_id": "S-M020-04",
        "locator": "2026年現行『不燃・粗大ごみの出し方』と3月改訂ガイドの区分体系を照合",
        "evidence_role": "PRIMARY_INDEX",
        "notes": "2026年の電池類・不燃粗大の変更を反映し、旧危険有害3行を現行葉区分から除外。",
    })
    return sorted(rows, key=lambda r: (r.get("municipality_id", ""), r.get("review_id", ""), r.get("review_evidence_id", "")))


def update_scope(branch_count: int) -> None:
    fields, rows = read_csv(SCOPE_PATH)
    rows = [row for row in rows if row.get("municipality_id") != MID]
    rows.append({
        "municipality_id": MID,
        "municipality_name": "静岡市",
        "lesson_mode": "ONLINE_CLASS",
        "scoring_status": "APP_READY",
        "required_item_count": "40",
        "required_branch_count": str(branch_count),
        "review_source": "data/research/app_readiness/m020_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "40品目全条件枝COMPLETE。固定10の分別正答は市内共通で、地区差は収集容器・回収場所としてエビデンス層に保持。",
    })
    rows.sort(key=lambda r: r["municipality_id"])
    write_csv(SCOPE_PATH, fields, rows)


def update_priority_and_company() -> None:
    fields, rows = read_csv(PRIORITY_PATH)
    for row in rows:
        if row["municipality_id"] == MID:
            row["implementation_status"] = "IMPLEMENTED"
            row["readiness_status_snapshot"] = "APP_READY"
            row["checked_date"] = CHECKED
            row["note"] = "40品目APP_READY。会社紐付けはrouting metadataであり、ごみルール根拠には使用しない。"
    write_csv(PRIORITY_PATH, fields, rows)

    fields, rows = read_csv(COMPANY_PATH)
    for row in rows:
        if row.get("company_id") == "C009" and row.get("municipality_id") == MID:
            row["active"] = "TRUE"
    write_csv(COMPANY_PATH, fields, rows)


def write_image_rows(item_by: dict[str, dict[str, str]], category_by: dict[tuple[str, str], dict[str, str]],
                     source_by: dict[tuple[str, str], dict[str, str]]) -> None:
    fields, rows = read_csv(IMAGE_PATH)
    if fields != IMAGE_FIELDS:
        raise ValueError(f"image mapping header mismatch: {fields}")
    rows = [row for row in rows if row.get("municipality_id") != MID]
    for iid in IMAGE_ITEMS:
        spec = RULES[iid][0]
        item = item_by[iid]
        category = category_by[(MID, spec.category_id)]
        evidence = source_by[(MID, spec.source_id)]
        rows.append({
            "pair_order": "",
            "municipality_id": MID,
            "municipality_name": "静岡市",
            "internal_item_id": iid,
            "canonical_name": item["一般管理用名称"],
            "display_name": item["教材表示名"],
            "review_status": "VERIFIED",
            "evidence_basis": spec.basis,
            "category_id": spec.category_id,
            "category_name": category["自治体正式名称"],
            "condition": spec.condition,
            "preparation": spec.preparation,
            "exception_destination": spec.exception,
            "item_evidence_source_id": spec.source_id,
            "item_evidence_url": evidence["公式URL"],
            "item_evidence_locator": spec.locator,
            "checked_date": CHECKED,
            "reviewer": REVIEWER,
            "note": spec.note or "M020 APP_READY reviewの固定10通常状態を採用。地区差は分別正答を変えない。",
        })
    for order, row in enumerate(rows, start=1):
        row["pair_order"] = str(order)
    write_csv(IMAGE_PATH, fields, rows)


def main() -> None:
    expected = {f"I{i:03d}" for i in range(1, 41)}
    if set(RULES) != expected or any(not RULES[iid] for iid in expected):
        raise ValueError(f"M020 rules must cover exact 40 items: missing={sorted(expected-set(RULES))}")

    _, items = read_csv(MASTER / "04_common_items_master.csv")
    item_by = {row["internal_item_id"]: row for row in items}
    _, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, qa = read_csv(RESEARCH / "06_qa_log.csv")
    _, review_evidence = read_csv(RESEARCH / "08_category_review_evidence.csv")
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")

    source_by = {(row["municipality_id"], row["source_id"]): dict(row) for row in sources}
    for row in NEW_SOURCES:
        source_by[(MID, row["source_id"])] = row
    sources = sorted(source_by.values(), key=lambda r: (r["municipality_id"], r["source_id"]))
    source_by = {(row["municipality_id"], row["source_id"]): row for row in sources}

    category_by = {(row["municipality_id"], row["category_id"]): dict(row) for row in categories}
    for key, row in list(category_by.items()):
        if key[0] == MID:
            category_by[key] = updated_category(row)
    categories = sorted(category_by.values(), key=lambda r: (r["municipality_id"], r["category_id"]))
    category_by = {(row["municipality_id"], row["category_id"]): row for row in categories}

    municipalities = [update_municipality_review(row) for row in municipalities]
    review_evidence = add_review_evidence(review_evidence)

    existing_by_item: dict[str, list[dict[str, str]]] = {}
    for row in mappings:
        if row["municipality_id"] == MID:
            existing_by_item.setdefault(row["internal_item_id"], []).append(row)
    for rows in existing_by_item.values():
        rows.sort(key=lambda r: (int(r.get("branch_order") or 0), r["mapping_id"]))

    retained = [row for row in mappings if row["municipality_id"] != MID]
    used_ids = {row["mapping_id"] for row in retained}
    generated: list[dict[str, str]] = []
    audit: list[dict[str, str]] = []

    for iid in sorted(expected):
        old_rows = existing_by_item.get(iid, [])
        for order, spec in enumerate(RULES[iid], start=1):
            category = category_by[(MID, spec.category_id)]
            if category.get("rule_status") != "CURRENT":
                raise ValueError(f"{iid}: mapping cannot target non-current category {spec.category_id}")
            evidence = source_by[(MID, spec.source_id)]
            mapping_id = old_rows[order - 1]["mapping_id"] if order <= len(old_rows) else f"MAP-{MID}-{iid}-APP-{order:02d}"
            if mapping_id in used_ids:
                mapping_id = f"MAP-{MID}-{iid}-APP-{order:02d}"
            if mapping_id in used_ids:
                raise ValueError(f"duplicate mapping id {mapping_id}")
            used_ids.add(mapping_id)

            mapping = {field: "" for field in MAPPING_FIELDS}
            mapping.update({
                "mapping_id": mapping_id,
                "municipality_id": MID,
                "internal_item_id": iid,
                "branch_order": str(order),
                "自治体での品目表記": spec.wording,
                "category_id": spec.category_id,
                "分別区分正式名称": category["自治体正式名称"],
                "条件": spec.condition,
                "前処理": spec.preparation,
                "例外分別先": spec.exception,
                "自治体収集外": category["自治体収集外か"],
                "rule_status": category["rule_status"],
                "effective_from": category["effective_from"],
                "effective_to": category["effective_to"],
                "category_source_id": category["source_id"],
                "category_source_url": category["出典URL"],
                "category_source_locator": category["出典ページ・該当箇所"],
                "item_evidence_source_id": spec.source_id,
                "item_evidence_url": evidence["公式URL"],
                "item_evidence_locator": spec.locator,
                "確認日": CHECKED,
                "mapping_status": "APP_READY",
                "evidence_scope": "ITEM_SPECIFIC",
                "branch_review_status": "COMPLETE",
                "reviewed_date": CHECKED,
                "reviewed_by": REVIEWER,
                "備考": (f"M020 40品目APP_READY手動レビュー。{spec.basis}。{spec.note}").strip(),
            })
            generated.append(mapping)
            item = item_by[iid]
            audit.append({
                "municipality_id": MID,
                "internal_item_id": iid,
                "branch_order": str(order),
                "canonical_name": item["一般管理用名称"],
                "display_name": item["教材表示名"],
                "official_item_wording": spec.wording,
                "category_id": spec.category_id,
                "category_name": category["自治体正式名称"],
                "condition": spec.condition,
                "preparation": spec.preparation,
                "exception_destination": spec.exception,
                "evidence_basis": spec.basis,
                "item_evidence_source_id": spec.source_id,
                "item_evidence_url": evidence["公式URL"],
                "item_evidence_locator": spec.locator,
                "branch_review_status": "COMPLETE",
                "checked_date": CHECKED,
                "reviewer": REVIEWER,
                "note": spec.note or "現行公式品目ページ又は公式区分ルールで必要条件枝を照合。",
            })

    mappings = sorted(retained + generated, key=lambda r: (
        r["municipality_id"], r["internal_item_id"], int(r.get("branch_order") or 0), r["mapping_id"]
    ))

    coverage_by = {(row["municipality_id"], row["internal_item_id"]): dict(row) for row in coverage}
    for iid in sorted(expected):
        first = RULES[iid][0]
        evidence = source_by[(MID, first.source_id)]
        row = coverage_by.get((MID, iid), {field: "" for field in COVERAGE_FIELDS})
        row.update({
            "municipality_id": MID,
            "internal_item_id": iid,
            "coverage_status": "APP_READY",
            "mapping_branch_count": str(len(RULES[iid])),
            "branch_completeness_confirmed": "TRUE",
            "evidence_scope": "ITEM_SPECIFIC",
            "item_evidence_source_id": first.source_id,
            "item_evidence_url": evidence["公式URL"],
            "item_evidence_locator": first.locator,
            "reviewed_date": CHECKED,
            "reviewed_by": REVIEWER,
            "notes": "M020全40品目の必要条件枝を2026現行公式資料へ照合しatomic APP_READY昇格。",
        })
        coverage_by[(MID, iid)] = row
    coverage = sorted(coverage_by.values(), key=lambda r: (r["municipality_id"], r["internal_item_id"]))

    # Keep Batch 02's ordinary source/category/QA union aligned with canonical.
    _, batch_municipalities = read_csv(BATCH / "batch_02_municipalities.csv")
    _, batch_categories = read_csv(BATCH / "batch_02_categories.csv")
    _, batch_sources = read_csv(BATCH / "batch_02_sources.csv")
    _, batch_qa = read_csv(BATCH / "batch_02_qa.csv")
    _, batch_review_evidence = read_csv(BATCH / "batch_02_category_review_evidence.csv")

    batch_source_by = {(row["municipality_id"], row["source_id"]): dict(row) for row in batch_sources}
    for row in NEW_SOURCES:
        batch_source_by[(MID, row["source_id"])] = row
    batch_sources = sorted(batch_source_by.values(), key=lambda r: (r["municipality_id"], r["source_id"]))

    batch_category_by = {(row["municipality_id"], row["category_id"]): dict(row) for row in batch_categories}
    for key, row in category_by.items():
        if key[0] == MID:
            batch_category_by[key] = dict(row)
    batch_categories = sorted(batch_category_by.values(), key=lambda r: (r["municipality_id"], r["category_id"]))
    batch_municipalities = [update_municipality_review(row) for row in batch_municipalities]
    batch_review_evidence = add_review_evidence(batch_review_evidence)

    qa = compute_qa(municipalities, categories, sources, review_evidence, qa)
    municipalities = sync_municipality_qa_status(municipalities, qa)
    batch_qa = compute_qa(batch_municipalities, batch_categories, batch_sources, batch_review_evidence, batch_qa)
    batch_municipalities = sync_municipality_qa_status(batch_municipalities, batch_qa)

    write_csv(RESEARCH / "02_categories_master.csv", CATEGORY_FIELDS, categories)
    write_csv(RESEARCH / "03_sources_master.csv", SOURCE_FIELDS, sources)
    write_csv(RESEARCH / "04_municipalities_research.csv", MUNICIPALITY_FIELDS, municipalities)
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    write_csv(RESEARCH / "06_qa_log.csv", QA_FIELDS, qa)
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", COVERAGE_FIELDS, coverage)
    write_csv(RESEARCH / "08_category_review_evidence.csv", CATEGORY_REVIEW_EVIDENCE_FIELDS, review_evidence)
    write_csv(AUDIT_PATH, AUDIT_FIELDS, audit)

    write_csv(BATCH / "batch_02_municipalities.csv", MUNICIPALITY_FIELDS, batch_municipalities)
    write_csv(BATCH / "batch_02_categories.csv", CATEGORY_FIELDS, batch_categories)
    write_csv(BATCH / "batch_02_sources.csv", SOURCE_FIELDS, batch_sources)
    write_csv(BATCH / "batch_02_qa.csv", QA_FIELDS, batch_qa)
    write_csv(BATCH / "batch_02_category_review_evidence.csv", CATEGORY_REVIEW_EVIDENCE_FIELDS, batch_review_evidence)

    update_scope(len(generated))
    update_priority_and_company()
    write_image_rows(item_by, category_by, source_by)

    # This promotion must not invent a learner regional selector for collection-channel
    # differences that do not change the fixed-10 answer category.
    _, variants = read_csv(VARIANT_PATH)
    if any(row.get("municipality_id") == MID for row in variants):
        raise ValueError("M020 must not receive a learner regional variant")

    print(
        f"M020_APP_READY_APPLIED items=40 branches={len(generated)} "
        f"sources_added={len(NEW_SOURCES)} current_category_leaves=12 image_pairs=10"
    )


if __name__ == "__main__":
    main()
