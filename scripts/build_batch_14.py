#!/usr/bin/env python3
"""Build final Batch 14 from current resident-facing official sources.

MASTER scope: M136-M143.
Active: M137, M138, M140-M143.
Deferred: M136 Yoshinogawa and M139 Marugame because simultaneous regional
CURRENT resident systems have real output-unit / collection-route differences,
not schedule-only variants.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from schema_v12 import (
    CATEGORY_FIELDS, CATEGORY_REVIEW_EVIDENCE_FIELDS, COVERAGE_FIELDS,
    MAPPING_FIELDS, MASTER, MUNICIPALITY_FIELDS, QA_FIELDS, SOURCE_FIELDS,
    migrate_batch_dir, read_csv, write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research" / "batches" / "batch_14"
CHECKED = "2026-08-19"
REVIEWER = "OPENAI_CHATGPT_BATCH14_REVIEW"
NS = "NOT_STATED_IN_CITED_SOURCE"
TARGETS = {"M137","M138","M140","M141","M142","M143"}
DEFERRED = {"M136","M139"}
REGISTRY_FIELDS = ["municipality_id","host","authority_type","authority_name","verification_url","verified_date","notes"]

municipality_specs = {
    "M137": dict(pref="香川県", city="綾川町", processor="綾川町", top="https://www.town.ayagawa.lg.jp/docs/2011071100382/", guide="https://www.town.ayagawa.lg.jp/docs/2011071100382/", note="令和8年度地区別日程表は収集日差でtaxonomyは共通。町例規の住民向け8区分と粗大ごみを現行日程表で照合し、2026年3月開始の小型充電式電池・小型家電拠点回収を別経路で保持。"),
    "M138": dict(pref="香川県", city="多度津町", processor="多度津町", top="https://www.town.tadotsu.kagawa.jp/kurashi_tetsuzuki/gomi_kankyo_pet/gomi_recycle/1/1444.html", guide="https://www.town.tadotsu.kagawa.jp/kurashi_tetsuzuki/gomi_kankyo_pet/gomi_recycle/1/1444.html", note="令和8年度の可燃・不燃・資源・粗大資料を採用。資源ごみは公式持込一覧で住民が品目別に分ける15区分を子葉として保持し、上位『資源ごみ』を二重計上しない。"),
    "M140": dict(pref="香川県", city="三豊市", processor="三豊市", top="https://www.city.mitoyo.lg.jp/kakuka/shiminkankyou/eisei/2/1/1499.html", guide="https://www.city.mitoyo.lg.jp/kakuka/shiminkankyou/eisei/2/1/1511.html", note="市全域の現行12見出しを基礎に、紙類・布類は新聞・雑誌・ダンボール・紙パック・衣類を別束／別袋で出すため子葉化。令和8年の有害・金属収集日も市公式で照合。"),
    "M141": dict(pref="福岡県", city="小竹町", processor="小竹町", top="https://town.kotake.lg.jp/hpkiji/pub/detail.aspx?c_id=3&id=3989&type=top", guide="https://town.kotake.lg.jp/cal_recycle/pub/default.aspx?c_id=6", note="2026年度家庭ごみ資料と現行カレンダーの5分類を採用。2026年4月開始の食品用トレイ類・発泡スチロール拠点回収は、それぞれ別の透明袋へ分ける独立REFERENCE_ONLY葉として追加。"),
    "M142": dict(pref="福岡県", city="北九州市", processor="北九州市", top="https://www.city.kitakyushu.lg.jp/contents/924_10025.html", guide="https://www.city.kitakyushu.lg.jp/contents/924_10025.html", note="現行『資源とごみの分け方・出し方』索引を採用。かん・びんとペットボトルは別指定袋・別車収集なので上位見出しの子葉として保持。拠点回収群と市が収集しないものは通常SORT_BUCKETへ混ぜない。"),
    "M143": dict(pref="大分県", city="佐伯市", processor="佐伯市", top="https://www.city.saiki.oita.jp/kiji0032215/index.html", guide="https://www.city.saiki.oita.jp/kiji0032215/3_2215_32330_up_avmysieh.pdf", note="令和6年4月改定の現行家庭ごみ冊子を令和8年度実施計画で現行確認。資源物は実排出単位を子葉化し、粗大ごみは予約・直接搬入経路、有害物・ガレキ類も独立葉として保持。"),
}

# title, kind, url, updated, used, issuer
source_specs = {
    "M137": [
        ("令和8年度 ごみ収集日程表", "自治体公式Webページ", municipality_specs["M137"]["top"], "2026-03-24", "令和8年度の町内共通分別と地区別日程。プラスチック容器包装、ビン、PET、缶等の現行運用", "綾川町"),
        ("綾川町高齢者等ごみ出しサポートほっと歓事業実施要綱", "自治体公式例規", "https://www.town.ayagawa.lg.jp/reiki02/reiki_honbun/r263RG00001059.html", "現行", "燃やせる、プラスチック容器包装、破砕、PET、ビン類、缶類、古紙類、有害ごみの公式8区分", "綾川町"),
        ("リチウムイオン電池等の回収について", "自治体公式Webページ", "https://www.town.ayagawa.lg.jp/docs/2026031600017/", "2026-04-01", "2026年3月開始の小型充電式電池回収と小型家電回収。充電池は端子絶縁", "綾川町"),
    ],
    "M138": [
        ("令和8年度 ごみの出し方・収集計画表", "自治体公式Webページ", municipality_specs["M138"]["top"], "2026-02-27", "令和8年度の可燃・不燃・資源・粗大・小型家電の現行資料一式への公式導線", "多度津町"),
        ("資源ごみの正しい分け方 出し方 令和8年度", "自治体公式PDF", "https://www.town.tadotsu.kagawa.jp/material/files/group/6/SIGENN.pdf", "2026年度", "缶類等、金属、びん、PET、紙、布、白色トレイ、廃食油、乾電池、蛍光管等の分別・前処理", "多度津町"),
        ("粗大ごみの出し方 令和8年度", "自治体公式PDF", "https://www.town.tadotsu.kagawa.jp/material/files/group/6/SODAI.pdf", "2026年度", "粗大ごみの定義、集積場排出と大型・重量物のリサイクルプラザ搬入条件", "多度津町"),
        ("第3日曜日のごみの持ち込みについて", "自治体公式Webページ", "https://www.town.tadotsu.kagawa.jp/soshikikarasagasu/juminkankyoka/gomi_recycle/1/725.html", "2024-09-17", "資源ごみとして品目別に分けて持ち込む15住民区分", "多度津町"),
        ("可燃・不燃ごみの正しい分け方 出し方", "自治体公式PDF", "https://www.town.tadotsu.kagawa.jp/material/files/group/6/kanennhunenn.pdf", "2026年度", "可燃ごみ・不燃ごみの現行排出区分", "多度津町"),
    ],
    "M140": [
        ("ごみ・資源物の分別種類(詳細)", "自治体公式Webページ", municipality_specs["M140"]["guide"], "2023-12-26", "市全域の12分別見出し、紙類布類の別出力、廃食用油・粗大ごみ等の経路", "三豊市"),
        ("有害ごみ・金属ごみの収集について", "自治体公式Webページ", "https://www.city.mitoyo.lg.jp/kakuka/shiminkankyou/eisei/2/1/1516.html", "2024-10-23", "令和8年の市全域有害・金属ごみ収集日と島しょ部の日程差", "三豊市"),
        ("持込回収（有害・金属・廃食用油及び紙類・布類）について", "自治体公式Webページ", "https://www.city.mitoyo.lg.jp/kakuka/shiminkankyou/eisei/2/1/1515.html", "2026-01-06", "有害・金属・廃食用油・紙類・布類の現行持込経路", "三豊市"),
    ],
    "M141": [
        ("2026年度 家庭ごみの正しい出し方", "自治体公式Webページ", municipality_specs["M141"]["top"], "2026-04-01", "2026年度家庭ごみの排出ルール", "小竹町"),
        ("ゴミ出しカレンダー", "自治体公式Webサービス", municipality_specs["M141"]["guide"], "現行", "固形燃料用ごみ（燃えるごみ）、びん・缶、PET、燃えないゴミ、粗大ごみの5分類", "小竹町"),
        ("食品用トレイ類・発泡スチロールの回収を始めます", "自治体公式Webページ", "https://town.kotake.lg.jp/hpkiji/pub/detail.aspx?c_id=3&id=3963&type=top", "2026-04-01", "2026年4月19日開始。食品用トレイ類と発泡スチロールを別々の透明袋で拠点回収", "小竹町"),
    ],
    "M142": [
        ("『資源』と『ごみ』の分け方・出し方", "自治体公式Webページ", municipality_specs["M142"]["top"], "2025-04-03", "家庭ごみ、資源化物、粗大、拠点回収、市が収集しないものの現行索引", "北九州市"),
        ("かん・びん・ペットボトル", "自治体公式Webページ", "https://www.city.kitakyushu.lg.jp/contents/924_10035.html", "2024-02-05", "かん・びんとPETの別指定袋・別車収集。スプレー缶は穴を開けず家庭ごみ", "北九州市"),
        ("拠点回収ボックス等設置場所", "自治体公式Webページ", "https://www.city.kitakyushu.lg.jp/contents/00800208.html", "2026-05-13", "紙パック・トレイ、蛍光管、小物金属、小型電子機器、食用油、電池、古紙、古着等の拠点回収", "北九州市"),
        ("市が収集しないもの", "自治体公式Webページ", "https://www.city.kitakyushu.lg.jp/contents/924_10085.html", "2026-07-10", "家電4品目等の市収集対象外", "北九州市"),
        ("プラスチック", "自治体公式Webページ", "https://www.city.kitakyushu.lg.jp/contents/924_10030.html", "現行", "容器包装と対象プラスチック製品を同一プラスチック区分で収集", "北九州市"),
    ],
    "M143": [
        ("佐伯市家庭ごみの分け方・出し方について", "自治体公式Webページ", municipality_specs["M143"]["top"], "2024-05-28", "令和6年4月改定の現行家庭ごみ冊子への公式導線", "佐伯市"),
        ("佐伯市家庭ごみの分け方・出し方（令和6年4月～）", "自治体公式PDF", municipality_specs["M143"]["guide"], "2024-04", "燃える、燃えない、有害物、資源物の実排出単位と粗大ごみ経路", "佐伯市"),
        ("第2次佐伯市一般廃棄物（ごみ）処理基本計画", "自治体公式PDF", "https://www.city.saiki.oita.jp/kiji0038696/3_8696_up_xghyp5wr.pdf", "2023-10", "家庭ごみ分別区分。資源物子区分、有害物、ガレキ類", "佐伯市"),
        ("令和8年度 佐伯市一般廃棄物（ごみ）処理実施計画の公表", "自治体公式Webページ", "https://www.city.saiki.oita.jp/kiji00311436/index.html", "2026-03-30", "令和8年度も現行処理体系を運用していること", "佐伯市"),
        ("カセットボンベやスプレー缶の捨て方について(燃えないごみ）", "自治体公式Webページ", "https://www.city.saiki.oita.jp/kiji0037638/index.html", "2024-04-16", "スプレー缶等は使い切り、屋外でガス抜きし、穴を2か所あけて燃えないごみ", "佐伯市"),
        ("多量ごみや粗大ごみの処理について", "自治体公式Webページ", "https://www.city.saiki.oita.jp/kiji0038689/index.html", "2026-04-16", "粗大ごみの自己搬入・戸別収集等の現行経路", "佐伯市"),
    ],
}

categories: list[dict[str, str]] = []

def add(mid: str, name: str, rep: str, *, source: int = 1, parent: str = "", group: str = "", ui: str = "SORT_BUCKET",
        level: str = "PRIMARY", channel: str = "CURBSIDE", forbidden: str = NS, cond: str = "", fallback: str = NS,
        prep: str = NS, bag: str = "", size: str = "", bulky: str = "FALSE", outside: str = "FALSE", note: str = "") -> None:
    categories.append({
        "municipality_id": mid, "自治体正式名称": name, "category_group": group or parent or name, "parent_name": parent,
        "classification_level": level, "collection_channel": channel, "代表品目": rep, "入れてはいけない物": forbidden,
        "適用条件": cond, "条件外の扱い": fallback, "出す前の処理": prep, "袋・容器のルール": bag,
        "サイズ・条件": size, "粗大ごみ扱いか": bulky, "予約が必要か": "TRUE" if channel == "BOOKED_PICKUP" else "FALSE",
        "有料か": "FALSE", "料金ルール": "", "自治体収集外か": outside, "注意事項": note,
        "source_index": str(source), "出典ページ・該当箇所": name, "ui_role": ui, "rule_status": "CURRENT",
        "effective_from": "", "effective_to": "",
    })

# M137 綾川町 — townwide taxonomy; district documents differ by schedule only.
add("M137", "燃やせるごみ", "生ごみ・可燃性家庭ごみ", source=2)
add("M137", "プラスチック容器包装", "プラマークの容器包装", source=2, prep="汚れを落とす")
add("M137", "破砕ごみ", "陶器・ガラス・金属複合品等", source=2)
add("M137", "ペットボトル", "PETマークのペットボトル", source=1, prep="洗って出す")
add("M137", "ビン類", "飲食用びん等", source=2, prep="洗って出す")
add("M137", "缶類", "飲食用缶等", source=2, prep="洗って出す")
add("M137", "古紙類", "新聞・雑誌・段ボール等", source=2)
add("M137", "有害ごみ", "蛍光灯・電球・使い捨てライター・乾電池等", source=2)
add("M137", "粗大ごみ", "大型家庭ごみ", source=1, ui="REFERENCE_ONLY", bulky="TRUE")
add("M137", "小型充電式電池", "ニカド電池・ニッケル水素電池・リチウムイオン電池", source=3, ui="REFERENCE_ONLY", channel="DROP_OFF", prep="端子部分にテープを貼るなど絶縁し、役場本庁・綾上支所の黄色の回収ボックス缶へ")
add("M137", "小型家電", "スマートフォン・携帯型ゲーム機・ハンディファン等", source=3, ui="REFERENCE_ONLY", channel="DROP_OFF", prep="取り外せる小型充電式電池は外す。外せない機器は小型家電回収ボックスへ")

# M138 多度津町 — resource outputs kept as official child leaves.
add("M138", "可燃ごみ", "可燃性家庭ごみ", source=5, prep="町指定袋へ")
add("M138", "不燃ごみ", "不燃性家庭ごみ", source=5, prep="町指定袋へ")
add("M138", "資源ごみ", "缶・金属・布・紙・びん・PET・白色トレイ・廃食油・乾電池・蛍光管・小型家電等", source=4)
resource138 = [
    ("空かん(アルミ・スチール)", "アルミ缶・スチール缶", "中身を出し、洗浄する"),
    ("金属", "鍋・フライパン等の金属製品", NS),
    ("布", "衣類・布類", "透明・半透明の袋へ"),
    ("牛乳パック", "牛乳・ジュースの紙パック", "洗い、開いて乾かす"),
    ("新聞紙", "新聞・広告紙", "種類別にまとめてひもで縛る"),
    ("段ボール", "段ボール", "種類別にまとめてひもで縛る"),
    ("雑誌", "雑誌・紙折箱・厚紙・紙袋・包装紙", "種類別にまとめてひもで縛る"),
    ("生きびん", "ビールびん・一升びん等", NS),
    ("駄ビン", "使い捨てびん", "中身を出し、洗浄する"),
    ("ペットボトル", "PETマークのペットボトル", "キャップを外し、すすぎ洗いして水切りする"),
    ("白色トレイ", "両面が白い食品トレイ", "洗って乾かす"),
    ("廃食油", "家庭の植物性食用油", NS),
    ("乾電池", "アルカリ・マンガン・リチウム乾電池等", NS),
    ("蛍光管", "蛍光管・電球型蛍光灯", "透明なビニール袋へ"),
    ("小型家電", "使用済小型家電", NS),
]
for name, rep, prep in resource138:
    add("M138", name, rep, source=4, parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", channel="DROP_OFF", prep=prep)
add("M138", "粗大ごみ", "指定袋に入らない大型家庭ごみ", source=3, ui="REFERENCE_ONLY", bulky="TRUE", size="大型・重量物にはリサイクルプラザ直接搬入条件あり")

# M140 三豊市 — 12 official headings; paper/clothing resolves to five output leaves.
add("M140", "燃やせるごみ（可燃ごみ）", "生ごみ・紙くず・小型可燃物等", prep="指定袋へ")
add("M140", "燃やせないごみ（不燃ごみ）", "ガラス・陶磁器・複合素材等", prep="指定袋へ")
add("M140", "缶類", "スチール缶・アルミ缶等", prep="中身を使い切り、洗浄する")
add("M140", "びん類", "飲食用びん等", prep="中身を使い切り、洗浄する")
add("M140", "ペットボトル", "PETマークのボトル", prep="キャップ・ラベルを外し、洗浄する")
add("M140", "紙製容器包装", "紙マークの容器包装", prep="中身を使い切り、汚れを取り除く")
add("M140", "プラスチック製容器包装", "プラマークの容器包装", prep="中身を使い切り、汚れを取り除く")
add("M140", "金属ごみ", "鍋・やかん・フライパン等", source=2, prep="金属以外の部分は可能な限り取り除く")
add("M140", "有害ごみ", "乾電池・ボタン電池・充電式電池・蛍光灯・電球・水銀製品・使い捨てライター", source=2, prep="充電式電池はごみステーションに出さず、持込場所の専用容器へ")
add("M140", "廃食用油（天ぷら油）", "菜種油・コーン油・オリーブ油・サラダ油等", source=3, ui="REFERENCE_ONLY", channel="DROP_OFF", prep="家庭の容器で持参し、持込場所のポリ容器へ移す")
add("M140", "紙類・布類", "新聞・雑誌・ダンボール・紙パック・衣類", source=3, channel="DROP_OFF")
for name, rep, prep in [
    ("新聞", "新聞", "紙ひもで十字に束ねる"),
    ("雑誌", "雑誌", "紙ひもで十字に束ねる"),
    ("ダンボール", "ダンボール", "紙ひもで十字に束ねる"),
    ("紙パック", "紙パック", "紙ひもで十字に束ねる"),
    ("衣類", "衣類", "汚れないよう袋へ入れる"),
]:
    add("M140", name, rep, source=1, parent="紙類・布類", level="SUBCATEGORY", ui="REFERENCE_ONLY", channel="DROP_OFF", prep=prep)
add("M140", "粗大ごみ", "最長辺50cm以上の家庭ごみ", ui="REFERENCE_ONLY", channel="DIRECT_HAUL", bulky="TRUE", prep="粗大ごみ持込場所へ持ち込む", size="最長辺50cm以上")

# M141 小竹町 — five calendar classes plus two April 2026 drop-off streams.
add("M141", "固形燃料用ごみ（燃えるごみ）", "生ごみ・ゴムくず・紙くず・プラスチックごみ・木くず・繊維くず・革類", source=2, prep="生ごみは水を切る")
add("M141", "びん・缶", "食品用びん・食品用缶・スプレー缶・カセットボンベ等", source=2)
add("M141", "ペットボトル", "飲料水・醤油・酒類のPET容器", source=2, prep="ラベルとキャップを外す")
add("M141", "燃えないゴミ", "ガラス類・せともの類・金属製品等", source=2)
add("M141", "粗大ごみ", "ふとん・タンス・机・いす・電子レンジ等", source=2, ui="REFERENCE_ONLY", bulky="TRUE")
add("M141", "食品用トレイ類", "冷凍食品トレイ・納豆容器・カップ麺容器・食品パック等", source=3, ui="REFERENCE_ONLY", channel="DROP_OFF", prep="発泡スチロールと分け、中身が見える透明なビニール袋へ")
add("M141", "発泡スチロール", "家庭から出た発泡スチロール", source=3, ui="REFERENCE_ONLY", channel="DROP_OFF", prep="食品用トレイ類と分け、中身が見える透明なビニール袋へ。大きく袋に入らない物はそのまま持参可")

# M142 北九州市 — grouped index, but cans/bottles and PET are separate bags and vehicles.
add("M142", "家庭ごみ", "家庭から出る通常ごみ", source=1)
add("M142", "かん・びん・ペットボトル", "かん・びん・ペットボトル", source=2)
add("M142", "かん・びん", "主に食料品のかん・びん", source=2, parent="かん・びん・ペットボトル", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ふたを外し、軽く水ですすぎ、かん・びん指定袋へ", forbidden="スプレー缶・カセットコンロ用ガスボンベ")
add("M142", "ペットボトル", "PETマークのペットボトル", source=2, parent="かん・びん・ペットボトル", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="キャップ・ラベルを外し、軽く水ですすいでつぶし、ペットボトル指定袋へ")
add("M142", "プラスチック", "対象となるプラスチック容器包装・プラスチック製品", source=5)
add("M142", "粗大ごみ・引っ越しごみ", "粗大ごみ・引っ越し等の多量ごみ", source=1, ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE")
for name, rep in [
    ("紙パック・トレイ", "紙パック・食品トレイ"),
    ("蛍光管", "蛍光管"),
    ("小物金属", "鍋・やかん・フライパン等"),
    ("小型電子機器", "使用済小型電子機器"),
    ("使用済食用油", "家庭の使用済食用油"),
    ("電池", "乾電池・充電式電池等"),
    ("古紙", "新聞・段ボール・雑誌等"),
    ("古着", "再利用可能な古着"),
]:
    add("M142", name, rep, source=3, ui="REFERENCE_ONLY", channel="DROP_OFF")
add("M142", "市が収集しないもの", "家電4品目・事業所から出るごみ等", source=4, ui="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED", outside="TRUE")

# M143 佐伯市 — current leaflet + current-year plan; resource outputs kept separately.
add("M143", "燃えるごみ", "生ごみ・小型可燃物・リサイクルできない紙布・プラスチック製品等", source=2, prep="燃えるごみ用指定袋へ")
add("M143", "燃えないごみ", "家電製品・陶磁器・ガラス・金属・布団等", source=5, prep="カセットボンベ・スプレー缶は中身を使い切り、屋外でガス抜きし、穴を2か所あける")
add("M143", "有害物（乾電池・蛍光灯）", "アルカリ電池・マンガン電池・水銀式体温計・蛍光灯", source=3, prep="燃えるごみの収集日に燃えるごみと分けて透明または半透明袋で出す")
add("M143", "資源物", "飲食用ビン・カン・PET、古紙、布類、小型家電", source=3)
add("M143", "飲食用ビン・カン", "飲食物が入って販売されたビン・カン", source=2, parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="キャップ・栓を外し、中を水洗いし、透明または半透明袋へ")
add("M143", "ペットボトル", "飲食用ペットボトル", source=2, parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="キャップ・ラベルを外し、中を水洗いし、透明または半透明袋へ")
add("M143", "古紙（新聞）", "新聞・折込チラシ", source=3, parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="他の紙類と混ぜず、ひも等で十字に縛る")
add("M143", "古紙（ダンボール）", "ダンボール", source=3, parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="他の紙類と混ぜず、ひも等で十字に縛る")
add("M143", "古紙（その他の紙類）", "古本・古雑誌・包装紙・菓子箱・カレンダー等", source=3, parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="他の紙類と混ぜず、ひも等で十字に縛る")
add("M143", "布類（リサイクル可能なもの）", "タオル・衣類・毛布・シーツ等", source=3, parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="透明または半透明袋へ")
add("M143", "小型家電（使用済小型電子機器）", "パソコン・携帯電話・デジタルカメラ・家庭用ゲーム機等", source=3, parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", channel="DROP_OFF")
add("M143", "粗大ごみ", "大型家具・自転車等", source=6, ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE", prep="戸別収集を予約するか、エコセンター番匠へ自己搬入")
add("M143", "ガレキ類", "レンガ・コンクリートブロック・土・石等の少量", source=3)


def ensure_deferred() -> None:
    path = MASTER / "05_deferred_municipalities.csv"
    fields, rows = read_csv(path)
    existing = {r.get("municipality_id") for r in rows}
    additions = {
        "M136": {"municipality_id":"M136","都道府県":"徳島県","市町村":"吉野川市","status":"DEFERRED",
                 "reason":"鴨島地区と川島・山川・美郷地区で、乾電池・蛍光管等のCURRENTな住民向け排出単位・回収容器・経路が異なる。鴨島では袋・束による排出、他地域では指定ステーションの回収容器を使う品目があり、municipality単位Schema/UIでは地域scopeを安全に解決できないため一旦対象外。固定IDを保持する。",
                 "deferred_date":CHECKED,"decision_source":"SCHEMA_SCOPE_LIMITATION"},
        "M139": {"municipality_id":"M139","都道府県":"香川県","市町村":"丸亀市","status":"DEFERRED",
                 "reason":"令和8年度も旧丸亀地区・綾歌飯山地区・本島町等の島しょ部でCURRENTな住民向け収集体系が併存し、本島・牛島の複合的な資源不燃系排出単位や広島町小手島・手島町の可燃・不燃・資源・ペットボトル体系など、単なる収集日差を超える分類・排出単位差がある。municipality単位Schema/UIでは地域scopeを安全に解決できないため一旦対象外。固定IDを保持する。",
                 "deferred_date":CHECKED,"decision_source":"SCHEMA_SCOPE_LIMITATION"},
    }
    for mid, row in additions.items():
        if mid not in existing:
            rows.append(row)
    rows.sort(key=lambda r: r.get("municipality_id", ""))
    write_csv(path, fields, rows)


def ensure_registry() -> None:
    path = MASTER / "02_official_domain_registry.csv"
    fields, rows = read_csv(path)
    fields = fields or REGISTRY_FIELDS
    existing = {(r.get("municipality_id"), r.get("host")) for r in rows}
    for mid, specs in source_specs.items():
        for _, _, url, _, _, issuer in specs:
            host = (urlparse(url).hostname or "").lower()
            if not host or (mid, host) in existing:
                continue
            rows.append({
                "municipality_id": mid, "host": host, "authority_type": "MUNICIPAL_DOMAIN",
                "authority_name": municipality_specs[mid]["city"], "verification_url": municipality_specs[mid]["top"],
                "verified_date": CHECKED, "notes": f"Batch 14 official source host ({issuer})",
            })
            existing.add((mid, host))
    rows.sort(key=lambda r: (r.get("municipality_id", ""), r.get("host", "")))
    write_csv(path, fields, rows)


def build_sources() -> list[dict[str, str]]:
    rows = []
    for mid in sorted(TARGETS):
        for i, (title, kind, url, updated, used, issuer) in enumerate(source_specs[mid], 1):
            rows.append({
                "municipality_id": mid, "source_id": f"S-{mid}-{i:02d}", "資料名": title, "資料種別": kind,
                "公式URL": url, "発行主体": issuer, "対象年度": "令和8年度", "ページ更新日": updated,
                "取得確認日": CHECKED, "使用した情報": used, "優先度": str(i), "現行性": "現行", "備考": "",
                "official_verified": "", "official_basis": "", "official_linking_url": "",
            })
    return rows


def build_categories() -> list[dict[str, str]]:
    by_mid: dict[str, list[dict[str, str]]] = {}
    for raw in categories:
        by_mid.setdefault(raw["municipality_id"], []).append(raw)
    rows = []
    for mid in sorted(TARGETS):
        raws = by_mid[mid]
        names = [r["自治体正式名称"] for r in raws]
        if len(names) != len(set(names)):
            dup = sorted({n for n in names if names.count(n) > 1})
            raise ValueError(f"duplicate category names in {mid}: {dup}")
        name_to_id = {r["自治体正式名称"]: f"C-{mid}-{i:02d}" for i, r in enumerate(raws, 1)}
        for i, raw in enumerate(raws, 1):
            sidx = int(raw["source_index"])
            src = source_specs[mid][sidx - 1]
            parent_id = name_to_id.get(raw["parent_name"], "")
            if raw["parent_name"] and not parent_id:
                raise ValueError(f"missing parent in {mid}: {raw['parent_name']} for {raw['自治体正式名称']}")
            rows.append({
                "municipality_id": mid, "category_id": name_to_id[raw["自治体正式名称"]],
                "自治体正式名称": raw["自治体正式名称"], "category_group": raw["category_group"],
                "parent_category_id": parent_id, "classification_level": raw["classification_level"],
                "表示順": str(i), "collection_channel": raw["collection_channel"], "代表品目": raw["代表品目"],
                "入れてはいけない物": raw["入れてはいけない物"], "適用条件": raw["適用条件"],
                "条件外の扱い": raw["条件外の扱い"], "出す前の処理": raw["出す前の処理"],
                "袋・容器のルール": raw["袋・容器のルール"], "サイズ・条件": raw["サイズ・条件"],
                "粗大ごみ扱いか": raw["粗大ごみ扱いか"], "予約が必要か": raw["予約が必要か"],
                "有料か": raw["有料か"], "料金ルール": raw["料金ルール"], "自治体収集外か": raw["自治体収集外か"],
                "注意事項": raw["注意事項"], "source_id": f"S-{mid}-{sidx:02d}", "出典URL": src[2],
                "出典ページ・該当箇所": raw["出典ページ・該当箇所"], "確認日": CHECKED,
                "ui_role": raw["ui_role"], "rule_status": raw["rule_status"], "effective_from": raw["effective_from"],
                "effective_to": raw["effective_to"],
            })
    return rows


def leaf_count(mid: str) -> int:
    raws = [r for r in categories if r["municipality_id"] == mid]
    parents = {r["parent_name"] for r in raws if r["parent_name"]}
    return sum(1 for r in raws if r["自治体正式名称"] not in parents and r["ui_role"] != "EXCLUDED_NOTICE" and r["rule_status"] == "CURRENT")


def build_municipalities() -> list[dict[str, str]]:
    rows = []
    for mid in sorted(TARGETS):
        spec = municipality_specs[mid]
        rows.append({
            "municipality_id": mid, "都道府県": spec["pref"], "市町村": spec["city"], "実装区分": "個別指定",
            "ごみ処理主体": spec["processor"], "自治体ごみトップURL": spec["top"], "分別ガイドURL": spec["guide"],
            "品目検索URL": "", "やさしい日本語URL": "", "多言語資料URL": "", "対象年度": "令和8年度",
            "最終確認日": CHECKED, "確認ステータス": "QA_REQUIRED", "備考": spec["note"],
            "official_category_count": "", "reviewed_category_count": str(leaf_count(mid)),
            "category_count_basis": "住民が排出時に選択する現行公式分別区分を公式索引・現年度資料で全件照合。別袋・別束・別容器の子区分は公式葉として保持し、投影親は二重計上しない。特殊経路はCURRENT公式葉としてREFERENCE_ONLYで保持。",
            "category_count_verified": "TRUE", "category_count_check_status": "MANUAL_INDEX_REVIEW",
            "category_count_review_id": f"CR-{mid}-CATEGORY-COVERAGE", "category_count_reviewed_date": CHECKED,
            "category_count_reviewed_by": REVIEWER, "search_service_check_status": "NOT_CHECKED",
            "search_service_check_evidence": "", "easy_japanese_check_status": "NOT_CHECKED", "easy_japanese_check_evidence": "",
            "multilingual_check_status": "NOT_CHECKED", "multilingual_check_evidence": "",
        })
    return rows


def build_review_evidence() -> list[dict[str, str]]:
    rows = []
    for mid in sorted(TARGETS):
        for i, src in enumerate(source_specs[mid], 1):
            rows.append({
                "review_evidence_id": f"CRE-{mid}-{i:02d}", "review_id": f"CR-{mid}-CATEGORY-COVERAGE",
                "municipality_id": mid, "source_id": f"S-{mid}-{i:02d}", "locator": src[4],
                "evidence_role": "PRIMARY_INDEX" if i == 1 else "SUPPLEMENTAL_INDEX",
                "notes": f"{CHECKED} Batch 14 resident-facing category completeness review",
            })
    return rows


def main() -> None:
    if set(municipality_specs) != TARGETS or set(source_specs) != TARGETS:
        raise ValueError("Batch14 target mismatch")
    expected = {"M137":11,"M138":18,"M140":16,"M141":7,"M142":13,"M143":12}
    actual = {mid: leaf_count(mid) for mid in sorted(TARGETS)}
    if actual != expected:
        raise ValueError(f"Batch14 leaf count mismatch: {actual}")
    ensure_deferred()
    ensure_registry()
    OUT.mkdir(parents=True, exist_ok=True)
    p = "batch_14_"
    write_csv(OUT / f"{p}municipalities.csv", MUNICIPALITY_FIELDS, build_municipalities())
    write_csv(OUT / f"{p}categories.csv", CATEGORY_FIELDS, build_categories())
    write_csv(OUT / f"{p}sources.csv", SOURCE_FIELDS, build_sources())
    write_csv(OUT / f"{p}qa.csv", QA_FIELDS, [])
    write_csv(OUT / f"{p}item_mapping.csv", MAPPING_FIELDS, [])
    write_csv(OUT / f"{p}item_coverage.csv", COVERAGE_FIELDS, [])
    write_csv(OUT / f"{p}category_review_evidence.csv", CATEGORY_REVIEW_EVIDENCE_FIELDS, build_review_evidence())
    counts = migrate_batch_dir(OUT)
    print(" ".join(f"{k}={v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
