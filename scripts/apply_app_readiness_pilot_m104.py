#!/usr/bin/env python3
"""Apply Higashihiroshima City's complete 40-item APP readiness review."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from schema_v12 import (
    CATEGORY_FIELDS, COVERAGE_FIELDS, MAPPING_FIELDS, MUNICIPALITY_FIELDS,
    QA_FIELDS, SOURCE_FIELDS, compute_qa, read_csv, sync_municipality_qa_status,
    write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data/research"
MASTER = ROOT / "data/master"
AUDIT_PATH = RESEARCH / "app_readiness/m104_item_review.csv"
CHECKED = "2026-08-24"
REVIEWER = "OPENAI_CODEX_M104_APP_READINESS_V1"
MID = "M104"

AUDIT_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "canonical_name",
    "display_name", "official_item_wording", "category_id", "category_name",
    "condition", "preparation", "exception_destination", "evidence_basis",
    "item_evidence_source_id", "item_evidence_url", "item_evidence_locator",
    "branch_review_status", "checked_date", "reviewer", "note",
]


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
    return Branch(category_id, source_id, locator, wording, condition,
                  preparation, exception, basis, note)


URLS = {
    "IS-M104-04": "https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_all.pdf",
    "IS-M104-05": "https://www.city.higashihiroshima.lg.jp/soshiki/seikatsukankyo/8/4/1/21260.html",
    "IS-M104-06": "https://www.city.higashihiroshima.lg.jp/soshiki/seikatsukankyo/8/4/1/15033.html",
    "IS-M104-07": "https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p33-62.pdf",
    "IS-M104-08": "https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p23-24.pdf",
    "IS-M104-09": "https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p25-26.pdf",
    "IS-M104-10": "https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p27-28.pdf",
    "IS-M104-11": "https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p63.pdf",
    "IS-M104-12": "https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p64.pdf",
    "IS-M104-13": "https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p65-66.pdf",
    "S-M104-04": "https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p63.pdf",
}


def source(source_id: str, title: str, used: str) -> dict[str, str]:
    return {
        "municipality_id": MID, "source_id": source_id, "資料名": title,
        "資料種別": "自治体公式PDF", "公式URL": URLS[source_id], "発行主体": "東広島市",
        "対象年度": "令和8年度／取得時点現行", "ページ更新日": "",
        "取得確認日": CHECKED, "使用した情報": used, "優先度": "1",
        "現行性": "CURRENT", "備考": "M104 40品目APP readiness手動レビューの品目別公式根拠。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    }


NEW_SOURCES = [
    source("S-M104-04", "市が収集・処理しないごみ（63頁）", "参照区分『市が収集・処理しないごみ』の正本根拠"),
    source("IS-M104-07", "家庭ごみの出し方 ごみ分別早見表（33～62頁）", "40共通品目の分別先・条件・例外"),
    source("IS-M104-08", "家庭から出た剪定枝・伐採木の出し方（23～24頁）", "剪定枝の直径・長さ別排出条件"),
    source("IS-M104-09", "小型家電回収ボックス（25～26頁）", "小型家電回収対象・投入口寸法・電池取外し"),
    source("IS-M104-10", "古布・古着の回収について（27～28頁）", "衣類の回収条件と対象外品"),
    source("IS-M104-11", "市が収集・処理しないごみ（63頁）", "家電4品目・パソコン等の市収集対象外"),
    source("IS-M104-12", "パソコンのリサイクルについて（64頁）", "メーカー・パソコン3R推進協会による回収"),
    source("IS-M104-13", "家電4品目の処理について（65～66頁）", "家電リサイクル法の対象と処分経路"),
]


BRANCHES: dict[str, list[Branch]] = {
    "I001": [b("C-M104-08", "IS-M104-07", "早見表59頁『ペットボトル』", "ペットボトル",
        "飲料・酒類・しょうゆ等のPETマーク付きボトル", "キャップとラベルを外し、中を軽くすすいで紫色指定袋へ入れる", "キャップ・ラベルはリサイクルプラ")],
    "I002": [b("C-M104-09", "IS-M104-07", "早見表57頁『ペットボトル』備考・『ペットボトルの蓋』", "ペットボトルのキャップ",
        "ペットボトルから外したプラスチック製キャップ", "本体から外し、汚れを取って紫色指定袋へ入れる", "金属製のびん・ボトルのふたはビン・缶")],
    "I003": [b("C-M104-09", "IS-M104-07", "早見表57頁『ペットボトル』備考", "ペットボトルのラベル",
        "ペットボトルから外したプラスチック製ラベル", "本体から外し、紫色指定袋へ入れる", "本体はペットボトル")],
    "I004": [b("C-M104-07", "IS-M104-07", "早見表33頁『アルミ缶（飲食物用）』", "アルミ缶（飲食物用）",
        "飲食物用のアルミ缶", "中身を使い切り、軽くすすいで紫色指定袋へ入れる", "できるだけ資源回収ステーションも利用する")],
    "I005": [b("C-M104-07", "IS-M104-07", "早見表45頁『スチール缶（飲料・食品用）』", "スチール缶（飲料・食品用）",
        "飲料・食品用のスチール缶", "中身を使い切り、軽くすすいで紫色指定袋へ入れる", "一斗缶以上の大きさは燃やせない粗大ごみ")],
    "I006": [
        b("C-M104-07", "IS-M104-07", "早見表の飲料・食品用びん各行", "飲料・食品用のびん", "飲料・食品用のガラスびん", "ふたを外し、中を軽くすすいで紫色指定袋へ入れる", "化粧品びん・果実酒用びん・ガラス製品は危険ごみ"),
        b("C-M104-02", "IS-M104-07", "早見表40頁『果実酒をつくるびん』・44頁『化粧品のびん』", "飲食物用以外のガラスびん", "化粧品びん又は果実酒をつくる大型びん", "新聞紙などに包み、オレンジ色指定袋へ入れる", "飲料・食品用びんはビン・缶"),
    ],
    "I007": [
        b("C-M104-09", "IS-M104-07", "早見表51頁『トレイ（食品用）』", "白色食品トレイ", "プラマークのある白色食品トレイで汚れが取れる物", "中身と汚れを取り、紫色指定袋へ入れる", "プラマークがない物はその他プラ、汚れが取れない物は燃やせるごみ"),
        b("C-M104-03", "IS-M104-07", "早見表51頁『トレイ（食品用）』備考", "プラマークのない白色食品トレイ", "プラマークのない白色食品トレイ", "中身を空にして紫色指定袋へ入れる", "プラマーク付きはリサイクルプラ、汚れが取れない物は燃やせるごみ"),
        b("C-M104-01", "IS-M104-07", "早見表のリサイクルプラ品目共通『汚れが取れないもの』", "汚れが取れない白色食品トレイ", "洗っても汚れが取れない白色食品トレイ", "中身を空にしてオレンジ色指定袋へ入れる", "汚れが取れるプラマーク付きはリサイクルプラ"),
    ],
    "I008": [
        b("C-M104-09", "IS-M104-07", "早見表51頁『トレイ（食品用）』", "色柄食品トレイ", "プラマークのある色柄食品トレイで汚れが取れる物", "中身と汚れを取り、紫色指定袋へ入れる", "プラマークがない物はその他プラ、汚れが取れない物は燃やせるごみ"),
        b("C-M104-03", "IS-M104-07", "早見表51頁『トレイ（食品用）』備考", "プラマークのない色柄食品トレイ", "プラマークのない色柄食品トレイ", "中身を空にして紫色指定袋へ入れる", "プラマーク付きはリサイクルプラ、汚れが取れない物は燃やせるごみ"),
        b("C-M104-01", "IS-M104-07", "早見表のリサイクルプラ品目共通『汚れが取れないもの』", "汚れが取れない色柄食品トレイ", "洗っても汚れが取れない色柄食品トレイ", "中身を空にしてオレンジ色指定袋へ入れる", "汚れが取れるプラマーク付きはリサイクルプラ"),
    ],
    "I009": [
        b("C-M104-09", "IS-M104-07", "早見表57頁『弁当の容器（プラスチック製・コンビニなど）』", "弁当の容器（プラスチック製）", "商品包装のプラスチック製弁当容器で汚れが取れる物", "中身と汚れを取り、紫色指定袋へ入れる", "汚れが取れない物は燃やせるごみ"),
        b("C-M104-03", "IS-M104-07", "早見表57頁『弁当箱（プラスチック製）』", "弁当箱（プラスチック製）", "商品包装ではないプラスチック製弁当箱", "中身を空にして紫色指定袋へ入れる", "商品包装の弁当容器はリサイクルプラ"),
        b("C-M104-01", "IS-M104-07", "早見表57頁『弁当の容器』備考", "汚れが取れない弁当容器", "洗っても汚れが取れないプラスチック製弁当容器", "中身を空にしてオレンジ色指定袋へ入れる", "汚れが取れる商品包装容器はリサイクルプラ"),
    ],
    "I010": [
        b("C-M104-09", "IS-M104-07", "早見表36頁『菓子袋（プラスチック製）』", "菓子袋（プラスチック製）", "プラスチック製菓子袋で汚れが取れる物", "中身を空にして紫色指定袋へ入れる", "紙製又は汚れが取れない物は燃やせるごみ"),
        b("C-M104-01", "IS-M104-07", "早見表のリサイクルプラ品目共通『汚れが取れないもの』", "汚れが取れない菓子袋", "汚れが取れないプラスチック製菓子袋", "中身が飛散しないようオレンジ色指定袋へ入れる", "汚れが取れる物はリサイクルプラ"),
        b("C-M104-01", "IS-M104-07", "早見表の紙製防水加工容器・紙くず各行", "紙製の菓子袋", "紙製の菓子袋", "中身を空にしてオレンジ色指定袋へ入れる", "紙製の菓子箱は雑誌・雑がみ・ダンボール", "OFFICIAL_RULE_DERIVED"),
    ],
    "I011": [
        b("C-M104-09", "IS-M104-07", "早見表61頁『レジ袋』・60頁『ラップ』備考", "商品の包装に使われたレジ袋", "購入した商品の包装として使われたレジ袋で汚れが取れる物", "中身を空にして紫色指定袋へ入れる", "家庭で包装以外に使った物はその他プラ、汚れが取れない物は燃やせるごみ"),
        b("C-M104-03", "IS-M104-07", "早見表61頁『レジ袋』・60頁『ラップ』備考", "包装以外に使ったレジ袋", "家庭で商品包装以外の用途に使ったプラスチック袋", "中身を空にして紫色指定袋へ入れる", "購入商品の包装はリサイクルプラ"),
        b("C-M104-01", "IS-M104-07", "早見表60頁『ラップ』備考（汚れが取れないもの）", "汚れが取れないレジ袋", "汚れが取れないプラスチック袋", "中身が飛散しないようオレンジ色指定袋へ入れる", "汚れが取れる物は用途によりリサイクルプラ又はその他プラ", "OFFICIAL_RULE_DERIVED"),
    ],
    "I012": [
        b("C-M104-09", "IS-M104-07", "早見表38頁『緩衝材（プラスチック製）』", "商品保護用の発泡スチロール", "商品を保護するプラスチック製緩衝材で汚れが取れる物", "汚れを取り、紫色指定袋へ入れる", "紙製又は汚れが取れない物は燃やせるごみ"),
        b("C-M104-03", "IS-M104-07", "早見表のプラマークのないプラスチック製品ルール", "容器包装でない発泡スチロール製品", "商品を保護する容器包装ではないプラスチックのみの発泡製品", "指定袋に入る大きさにして紫色指定袋へ入れる", "商品保護用はリサイクルプラ、指定袋に入らない物は燃やせない粗大ごみ", "OFFICIAL_RULE_DERIVED"),
        b("C-M104-11", "IS-M104-07", "早見表のプラスチック製品サイズ共通ルール", "指定袋に入らない発泡スチロール製品", "容器包装でなく40L指定袋に入らない発泡スチロール製品", "散乱しないようまとめて燃やせない粗大ごみとして出す", "指定袋に入る物はその他プラ", "OFFICIAL_RULE_DERIVED"),
        b("C-M104-01", "IS-M104-07", "早見表38頁『緩衝材』備考", "紙製又は汚れが取れない緩衝材", "紙製の緩衝材又は汚れが取れないプラスチック製緩衝材", "オレンジ色指定袋へ入れる", "汚れが取れるプラスチック製商品保護材はリサイクルプラ"),
    ],
    "I013": [b("C-M104-05", "IS-M104-07", "早見表44頁『新聞』", "新聞", "新聞・折込チラシ", "高さ20cmまでにしてひもで縛る", "PTA・自治会・店舗の資源回収も利用する")],
    "I014": [b("C-M104-06", "IS-M104-07", "早見表47頁『ダンボール』", "ダンボール", "家庭から出るダンボール", "50cm×100cm以下に畳み、ガムテープ・伝票を外し、高さ20cmまでひもで縛る", "汚れた物は燃やせるごみ")],
    "I015": [b("C-M104-06", "IS-M104-07", "早見表42頁『雑誌』", "雑誌", "家庭から出る雑誌", "高さ20cmまでにしてひもで縛る", "PTA・自治会・店舗の資源回収も利用する")],
    "I016": [
        b("C-M104-06", "IS-M104-07", "早見表36頁『菓子箱（紙製）』・紙袋等", "雑がみ・紙製菓子箱", "再生可能な紙製の箱・包装紙・紙袋等", "異物を外し、高さ20cmまでにしてひもで縛る", "感熱紙・圧着はがき・防水加工紙・汚れた紙は燃やせるごみ"),
        b("C-M104-01", "IS-M104-07", "早見表38頁『感熱紙』・57頁『圧着はがき』等", "再生できない雑紙", "感熱紙・圧着はがき・防水加工紙又は汚れた紙", "オレンジ色指定袋へ入れる", "再生可能な紙製の箱・包装紙等は雑誌・雑がみ・ダンボール", "OFFICIAL_RULE_DERIVED"),
    ],
    "I017": [
        b("C-M104-06", "IS-M104-07", "早見表37頁『紙パック（飲料用）』", "紙パック（飲料用）", "内側がアルミ加工されていない飲料用紙パック", "切り開き、高さ20cmまでひもで縛る", "内部がアルミ加工された物は燃やせるごみ"),
        b("C-M104-01", "IS-M104-07", "早見表37頁『紙パック』備考", "内部がアルミ加工された紙パック", "内部がアルミ加工された飲料用紙パック", "中身を空にしてオレンジ色指定袋へ入れる", "アルミ加工のない物は切り開いて雑誌・雑がみ・ダンボール"),
    ],
    "I018": [b("C-M104-01", "IS-M104-04", "ごみブック7頁『燃やせるごみ』台所ごみ", "生ごみ", "家庭から出る調理くず・残飯等の生ごみ", "十分に水切りし、オレンジ色指定袋へ入れる", "家庭菜園用コンポスト等による減量も可", "OFFICIAL_RULE_DERIVED")],
    "I019": [b("C-M104-01", "IS-M104-07", "早見表49頁『ティッシュペーパー』", "ティッシュペーパー", "使用済みティッシュペーパー", "オレンジ色指定袋へ入れる", "紙箱はフィルムを外し雑誌・雑がみ・ダンボール")],
    "I020": [b("C-M104-01", "IS-M104-07", "早見表37頁『紙おむつ』", "紙おむつ", "家庭で使用した紙おむつ", "汚物を取り除き、オレンジ色指定袋へ入れる", "汚物はトイレへ流す")],
    "I021": [b("C-M104-01", "IS-M104-07", "早見表34頁『衣類』・ごみブック27頁", "衣類", "家庭から出る衣類", "オレンジ色指定袋へ入れる", "再利用可能品は洗濯し、ひも又はビニール袋で古布・古着回収ボックスへ出せる")],
    "I022": [b("C-M104-11", "IS-M104-07", "早見表36頁『傘』", "傘", "家庭で使用した傘", "燃やせない粗大ごみとして出す", "分解した部材は材質ごとの案内に従う")],
    "I023": [
        b("C-M104-02", "IS-M104-07", "早見表48頁『茶碗』・42頁『皿（陶磁器製）』", "陶磁器製の茶碗・皿", "40L指定袋に入る陶磁器", "新聞紙などに包み、オレンジ色指定袋へ入れる", "プラスチック製・木製品は材質別、指定袋に入らない物は燃やせる粗大ごみ"),
        b("C-M104-04", "IS-M104-04", "ごみブック19頁『燃やせる粗大ごみ』大型陶磁器", "指定袋に入らない陶磁器", "40L指定袋に入らない大型陶磁器", "破損しないようまとめて燃やせる粗大ごみとして出す", "指定袋に入る物は危険ごみ"),
    ],
    "I024": [
        b("C-M104-02", "IS-M104-07", "早見表41頁『コップ（ガラス製）』", "ガラス製品", "40L指定袋に入るガラス製コップ等", "新聞紙などに包み、オレンジ色指定袋へ入れる", "飲料・食品用びんはビン・缶、指定袋に入らない物は粗大ごみ"),
        b("C-M104-04", "IS-M104-04", "ごみブック19頁『燃やせる粗大ごみ』大型ガラス", "指定袋に入らないガラス製品", "40L指定袋に入らない大型ガラス製品（主に非金属枠）", "破損しないようまとめて燃やせる粗大ごみとして出す", "指定袋に入る物は危険ごみ、金属枠の大型品は燃やせない粗大ごみ"),
    ],
    "I025": [b("C-M104-02", "IS-M104-07", "早見表のガラス製コップ・皿等の危険ごみ行", "割れたガラス", "指定袋に入る割れたガラス・ガラス片", "新聞紙などに包み、オレンジ色指定袋へ入れる", "飲料・食品用びんも割れた場合は危険防止のため包む", "OFFICIAL_RULE_DERIVED")],
    "I026": [b("C-M104-02", "IS-M104-07", "早見表57頁『包丁』", "包丁", "包丁・カッター・かみそり等の刃物", "刃を新聞紙などに包み、オレンジ色指定袋へ入れる", "指定袋に入らない剪定ばさみ等は燃やせない粗大ごみ")],
    "I027": [b("C-M104-10", "IS-M104-07", "早見表38頁『乾電池』", "乾電池", "家庭用の使い切り乾電池", "端子を絶縁し、オレンジ色指定袋で有害ごみとして出す", "市役所等の電池回収ボックスも利用できる")],
    "I028": [b("C-M104-10", "IS-M104-07", "早見表58頁『ボタン電池』", "ボタン電池", "家庭用のボタン電池・コイン電池", "端子を絶縁し、オレンジ色指定袋で有害ごみとして出す", "市役所等の電池回収ボックスも利用できる")],
    "I029": [
        b("C-M104-10", "IS-M104-05", "小型充電式電池等『ごみステーション』・『窓口回収』", "モバイルバッテリー", "40L指定袋に入る家庭用モバイルバッテリー（膨張・破損品を含む）", "端子をテープで絶縁し、オレンジ色指定袋の有害ごみ又は市窓口へ手渡す", "窓口回収では職員へ直接手渡し、回収ボックスへ入れない"),
        b("C-M104-11", "IS-M104-05", "小型充電式電池等『40L指定袋に入らないもの』", "大型のモバイルバッテリー", "40L指定袋に入らないモバイルバッテリー", "端子を絶縁し、燃やせない粗大ごみとして出す", "40L指定袋に入る物は有害ごみ又は市窓口回収"),
    ],
    "I030": [b("C-M104-10", "IS-M104-07", "早見表40頁『蛍光管・蛍光灯』", "蛍光管（環型・直型）・蛍光灯（電球型）", "家庭用の蛍光管・蛍光灯", "割らずにオレンジ色指定袋へ入れる。40L袋からはみ出してもよい", "割れた物は新聞紙などに包む")],
    "I031": [b("C-M104-10", "IS-M104-07", "早見表50頁『電球』", "電球", "白熱電球・LED電球を含む家庭用電球", "割らずにオレンジ色指定袋へ入れる", "照明器具本体は燃やせない粗大ごみ")],
    "I032": [b("C-M104-07", "IS-M104-07", "早見表45頁『スプレー缶』", "スプレー缶", "家庭用スプレー缶", "必ず中身のガスを使い切り、紫色指定袋へ入れる", "プラスチック製キャップはリサイクルプラ")],
    "I033": [b("C-M104-10", "IS-M104-07", "早見表61頁『ライター』", "ライター", "使い捨てライター等の家庭用ライター", "必ず中身のガスを使い切り、オレンジ色指定袋へ入れる", "市役所等のライター回収ボックスも利用できる")],
    "I034": [b("C-M104-11", "IS-M104-09", "ごみブック25頁『小型家電回収ボックス』", "小型家電", "家庭用の小型家電", "電池を外して燃やせない粗大ごみとして出す。40cm×18cm投入口に入る対象品は回収ボックスも利用可", "外した電池は有害ごみ。パソコン・家電4品目は専用回収経路")],
    "I035": [
        b("C-M104-10", "IS-M104-05", "小型充電式電池等『電池を取り外せない製品』", "小型充電式電池を取り外せない製品", "電池を外せず40L指定袋に入る小型家電", "オレンジ色指定袋へ入れ、有害ごみとして出す", "燃やせない粗大ごみにも出せる。安全に外せる場合は本体と電池を分別する"),
        b("C-M104-11", "IS-M104-05", "小型充電式電池等『40L指定袋に入らない製品』", "大型の電池内蔵製品", "電池を外せず40L指定袋に入らない家電", "燃やせない粗大ごみとして出し、見える位置に『危険 電池あり』と表示する", "40L指定袋に入る物は有害ごみを推奨"),
    ],
    "I036": [
        b("C-M104-01", "IS-M104-07", "早見表56頁『布団』", "布団", "40L指定袋に入る布団", "オレンジ色指定袋へ入れる", "指定袋に入らない物はひもで縛って燃やせる粗大ごみ"),
        b("C-M104-04", "IS-M104-07", "早見表56頁『布団』備考", "指定袋に入らない布団", "40L指定袋に入らない布団", "ひもで縛って燃やせる粗大ごみとして出す", "指定袋に入る物は燃やせるごみ"),
    ],
    "I037": [b("C-M104-12", "IS-M104-13", "ごみブック65頁『家電4品目の処理について』", "家電4品目", "エアコン、テレビ、冷蔵庫・冷凍庫、洗濯機・衣類乾燥機", "販売店へ依頼するか、家電リサイクル券を用意して指定引取場所へ持ち込む", "市のごみステーション・処理施設では収集処理しない")],
    "I038": [b("C-M104-12", "IS-M104-12", "ごみブック64頁『パソコンのリサイクルについて』", "家庭用パソコン", "デスクトップ・ノート・対象ディスプレイ等の家庭用パソコン", "メーカー又はパソコン3R推進協会へ回収を申し込む", "回収ボックス投入口に入る対象小型品は小型家電回収も利用できる")],
    "I039": [b("C-M104-01", "IS-M104-07", "早見表33頁『油（食用油）』・53頁『廃油（食用）』", "使用済み食用油", "家庭で使用した食用油", "布や紙に染み込ませるか固形化し、オレンジ色指定袋へ入れる", "食用以外の廃油は市で収集せず販売店へ相談する")],
    "I040": [
        b("C-M104-01", "IS-M104-08", "ごみブック23頁『燃やせるごみ（直径8cm未満）』", "剪定枝（直径8cm未満）", "家庭から出た直径8cm未満の枝・葉", "指定袋に入る大きさに切り、オレンジ色指定袋へ入れる", "直径8cm以上は燃やせる粗大ごみ。業者施工分は業者が引き取る"),
        b("C-M104-04", "IS-M104-08", "ごみブック23頁『直径8cm以上20cm以下』", "剪定枝（直径8cm以上20cm以下）", "家庭から出た直径8cm以上20cm以下の剪定枝", "長さ150cm以下に切り、燃やせる粗大ごみとして出す", "直径8cm未満は指定袋、直径20cm超は長さ30cm以下"),
        b("C-M104-04", "IS-M104-08", "ごみブック23頁『直径20cm超』", "剪定枝（直径20cm超）", "家庭から出た直径20cmを超える剪定枝", "長さ30cm以下に切り、燃やせる粗大ごみとして出す", "業者施工分は家庭ごみに出せない。直径20cm以下は別の長さ条件"),
    ],
}


def excluded_category() -> dict[str, str]:
    return {
        "municipality_id": MID, "category_id": "C-M104-12", "自治体正式名称": "市が収集・処理しないごみ",
        "category_group": "市が収集・処理しないごみ", "parent_category_id": "", "classification_level": "EXCLUDED",
        "表示順": "12", "collection_channel": "NOT_COLLECTED", "代表品目": "家電4品目・家庭用パソコン",
        "入れてはいけない物": "市の通常収集対象ごみ", "適用条件": "市が収集・処理しない指定品",
        "条件外の扱い": "品目ごとの市収集区分", "出す前の処理": "販売店・メーカー等の指定回収経路を確認",
        "袋・容器のルール": "市指定袋へ入れない", "サイズ・条件": "家電リサイクル法対象品・家庭用パソコン等",
        "粗大ごみ扱いか": "FALSE", "予約が必要か": "CONDITIONAL", "有料か": "CONDITIONAL",
        "料金ルール": "回収経路・製品により異なる", "自治体収集外か": "TRUE",
        "注意事項": "家電4品目と家庭用パソコンは専用リサイクル経路を利用",
        "source_id": "S-M104-04", "出典URL": URLS["S-M104-04"], "出典ページ・該当箇所": "63頁 市が収集・処理しないごみ",
        "確認日": CHECKED, "ui_role": "EXCLUDED_NOTICE", "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
    }


def main() -> None:
    _, items = read_csv(MASTER / "04_common_items_master.csv")
    _, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, qa = read_csv(RESEARCH / "06_qa_log.csv")
    _, review_evidence = read_csv(RESEARCH / "08_category_review_evidence.csv")
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")

    expected_items = {f"I{i:03d}" for i in range(1, 41)}
    assert set(BRANCHES) == expected_items and all(BRANCHES.values())
    item_by = {r["internal_item_id"]: r for r in items}

    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    for row in NEW_SOURCES:
        source_by[(MID, row["source_id"])] = row
    sources = sorted(source_by.values(), key=lambda r: (r["municipality_id"], r["source_id"]))
    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    for sid, url in URLS.items():
        source_row = source_by[(MID, sid)]
        assert source_row["公式URL"] == url and source_row["official_verified"] == "TRUE"

    category_by = {(r["municipality_id"], r["category_id"]): r for r in categories}
    category_by[(MID, "C-M104-12")] = excluded_category()
    categories = sorted(category_by.values(), key=lambda r: (r["municipality_id"], r["category_id"]))
    category_by = {(r["municipality_id"], r["category_id"]): r for r in categories}

    existing_by_pair: dict[str, list[dict[str, str]]] = {}
    for row in mappings:
        if row["municipality_id"] == MID:
            existing_by_pair.setdefault(row["internal_item_id"], []).append(row)
    for rows in existing_by_pair.values():
        rows.sort(key=lambda r: (int(r.get("branch_order") or 0), r["mapping_id"]))

    retained = [r for r in mappings if r["municipality_id"] != MID]
    used_ids = {r["mapping_id"] for r in retained}
    generated: list[dict[str, str]] = []
    audit: list[dict[str, str]] = []
    for iid in sorted(expected_items):
        old = existing_by_pair.get(iid, [])
        for order, spec in enumerate(BRANCHES[iid], start=1):
            category = category_by[(MID, spec.category_id)]
            evidence = source_by[(MID, spec.source_id)]
            mapping_id = old[order - 1]["mapping_id"] if order <= len(old) else f"MAP-{MID}-{iid}-APP-{order:02d}"
            assert mapping_id not in used_ids
            used_ids.add(mapping_id)
            row = {field: "" for field in MAPPING_FIELDS}
            row.update({
                "mapping_id": mapping_id, "municipality_id": MID, "internal_item_id": iid, "branch_order": str(order),
                "自治体での品目表記": spec.wording, "category_id": spec.category_id,
                "分別区分正式名称": category["自治体正式名称"], "条件": spec.condition, "前処理": spec.preparation,
                "例外分別先": spec.exception, "自治体収集外": category["自治体収集外か"], "rule_status": category["rule_status"],
                "effective_from": category["effective_from"], "effective_to": category["effective_to"],
                "category_source_id": category["source_id"], "category_source_url": category["出典URL"],
                "category_source_locator": category["出典ページ・該当箇所"], "item_evidence_source_id": spec.source_id,
                "item_evidence_url": evidence["公式URL"], "item_evidence_locator": spec.locator, "確認日": CHECKED,
                "mapping_status": "APP_READY", "evidence_scope": "ITEM_SPECIFIC", "branch_review_status": "COMPLETE",
                "reviewed_date": CHECKED, "reviewed_by": REVIEWER,
                "備考": (f"M104 40品目APP readiness手動レビュー。{spec.basis}。 " + spec.note).strip(),
            })
            generated.append(row)
            item = item_by[iid]
            audit.append({
                "municipality_id": MID, "internal_item_id": iid, "branch_order": str(order),
                "canonical_name": item["一般管理用名称"], "display_name": item["教材表示名"],
                "official_item_wording": spec.wording, "category_id": spec.category_id,
                "category_name": category["自治体正式名称"], "condition": spec.condition,
                "preparation": spec.preparation, "exception_destination": spec.exception,
                "evidence_basis": spec.basis, "item_evidence_source_id": spec.source_id,
                "item_evidence_url": evidence["公式URL"], "item_evidence_locator": spec.locator,
                "branch_review_status": "COMPLETE", "checked_date": CHECKED, "reviewer": REVIEWER,
                "note": spec.note or "公式品目行又は公式区分ルールと例外条件を手動照合。",
            })

    assert len(generated) == 63
    mappings = sorted(retained + generated, key=lambda r: (r["municipality_id"], r["internal_item_id"], int(r.get("branch_order") or 0), r["mapping_id"]))
    coverage_by = {(r["municipality_id"], r["internal_item_id"]): r for r in coverage}
    for iid in sorted(expected_items):
        first = BRANCHES[iid][0]
        evidence = source_by[(MID, first.source_id)]
        coverage_by[(MID, iid)].update({
            "coverage_status": "APP_READY", "mapping_branch_count": str(len(BRANCHES[iid])),
            "branch_completeness_confirmed": "TRUE", "evidence_scope": "ITEM_SPECIFIC",
            "item_evidence_source_id": first.source_id, "item_evidence_url": evidence["公式URL"],
            "item_evidence_locator": first.locator, "reviewed_date": CHECKED, "reviewed_by": REVIEWER,
            "notes": "M104の全40品目・全条件枝を公式資料へ手動照合し、自治体単位でatomic APP_READY昇格。",
        })
    coverage = sorted(coverage_by.values(), key=lambda r: (r["municipality_id"], r["internal_item_id"]))

    # C-M104-12 is a correction to Batch 10's reference layer, not a new
    # resident sorting bucket. Keep the completed-batch source/category/QA
    # bundle aligned with canonical while leaving its 11 counted buckets intact.
    batch = RESEARCH / "batches/batch_10"
    _, batch_municipalities = read_csv(batch / "batch_10_municipalities.csv")
    _, batch_categories = read_csv(batch / "batch_10_categories.csv")
    _, batch_sources = read_csv(batch / "batch_10_sources.csv")
    _, batch_qa = read_csv(batch / "batch_10_qa.csv")
    _, batch_review_evidence = read_csv(batch / "batch_10_category_review_evidence.csv")
    batch_category_by = {(r["municipality_id"], r["category_id"]): r for r in batch_categories}
    batch_category_by[(MID, "C-M104-12")] = excluded_category()
    batch_categories = sorted(batch_category_by.values(), key=lambda r: (r["municipality_id"], r["category_id"]))
    batch_source_by = {(r["municipality_id"], r["source_id"]): r for r in batch_sources}
    batch_source_by.pop((MID, "IS-M104-11"), None)
    batch_source_by[(MID, "S-M104-04")] = source_by[(MID, "S-M104-04")]
    batch_sources = sorted(batch_source_by.values(), key=lambda r: (r["municipality_id"], r["source_id"]))
    batch_qa = compute_qa(batch_municipalities, batch_categories, batch_sources, batch_review_evidence, batch_qa)
    batch_municipalities = sync_municipality_qa_status(batch_municipalities, batch_qa)

    qa = compute_qa(municipalities, categories, sources, review_evidence, qa)
    municipalities = sync_municipality_qa_status(municipalities, qa)
    write_csv(RESEARCH / "02_categories_master.csv", CATEGORY_FIELDS, categories)
    write_csv(RESEARCH / "03_sources_master.csv", SOURCE_FIELDS, sources)
    write_csv(RESEARCH / "04_municipalities_research.csv", MUNICIPALITY_FIELDS, municipalities)
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    write_csv(RESEARCH / "06_qa_log.csv", QA_FIELDS, qa)
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", COVERAGE_FIELDS, coverage)
    write_csv(AUDIT_PATH, AUDIT_FIELDS, audit)
    write_csv(batch / "batch_10_municipalities.csv", MUNICIPALITY_FIELDS, batch_municipalities)
    write_csv(batch / "batch_10_categories.csv", CATEGORY_FIELDS, batch_categories)
    write_csv(batch / "batch_10_sources.csv", SOURCE_FIELDS, batch_sources)
    write_csv(batch / "batch_10_qa.csv", QA_FIELDS, batch_qa)
    print("M104_APP_READINESS_APPLIED items=40 branches=63 app_ready_pairs=40 sources_added=8 excluded_reference=1")


if __name__ == "__main__":
    main()
