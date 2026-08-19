#!/usr/bin/env python3
"""Build Batch 12 from current resident-facing official sources.

MASTER scope: M116-M125.
Active: M116, M117, M118, M119, M121, M122, M124, M125.
Deferred: M120 Hagi and M123 Iwakuni because current resident-facing category
systems differ by region and the current municipality-level schema cannot
resolve a resident's regional scope safely.
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
OUT = ROOT / "data" / "research" / "batches" / "batch_12"
CHECKED = "2026-08-19"
REVIEWER = "OPENAI_CHATGPT_BATCH12_REVIEW"
NS = "NOT_STATED_IN_CITED_SOURCE"
TARGETS = {"M116","M117","M118","M119","M121","M122","M124","M125"}
DEFERRED = {"M120","M123"}
REGISTRY_FIELDS = ["municipality_id","host","authority_type","authority_name","verification_url","verified_date","notes"]

municipality_specs = {
    "M116": dict(pref="広島県", city="神石高原町", processor="神石高原町", top="https://www.jinsekigun.jp/town/formation/kankyoueisei/03/gomi/", guide="https://www.jinsekigun.jp/town/formation/kankyoueisei/03/gomi/", note="現行家庭ごみページの住民向け体系を採用。空きカン・空きビン・容器包装プラ・不燃系は、実際に住民が別区分へ分ける子葉を保持。"),
    "M117": dict(pref="山口県", city="下関市", processor="下関市", top="https://www.city.shimonoseki.lg.jp/site/gomi/143543.html", guide="https://www.city.shimonoseki.lg.jp/site/gomi/143543.html", note="令和8年度ごみの分け方・出し方ガイドを採用。古紙3区分と戸別収集の粗大ごみを公式葉として保持。"),
    "M118": dict(pref="山口県", city="宇部市", processor="宇部市", top="https://www.city.ube.yamaguchi.jp/kurashi/gomi/dashikata/index.html", guide="https://www.city.ube.yamaguchi.jp/kurashi/gomi/dashikata/1001956/index.html", note="現行ごみ区分に加え、ステーション外の粗大ごみ戸別収集と充電式電池回収をREFERENCE_ONLYの公式経路として保持。"),
    "M119": dict(pref="山口県", city="山口市", processor="山口市", top="https://www.city.yamaguchi.lg.jp/site/gomisigen/188479.html", guide="https://www.city.yamaguchi.lg.jp/site/gomisigen/161801.html", note="令和8年度資料と2026年7月改定の有害ごみ(1)(2)を優先。有害系を旧来の一括区分へ戻さない。"),
    "M121": dict(pref="山口県", city="防府市", processor="防府市", top="https://www.city.hofu.yamaguchi.jp/soshiki/16/calendar-.html", guide="https://www.city.hofu.yamaguchi.jp/soshiki/16/atarashiigomi-sasshi.html", note="令和8年度カレンダーと現行分別冊子を照合。地域差は収集日程で、住民向けtaxonomyは共通。"),
    "M122": dict(pref="山口県", city="下松市", processor="下松市／周南地区衛生施設組合・周南東部環境施設組合", top="https://www.city.kudamatsu.lg.jp/kankyou/seikatsu/kankyou/gomi/index.html", guide="https://www.city.kudamatsu.lg.jp/kankyou/documents/r8jissikeikaku.pdf", note="令和8年度一般廃棄物処理実施計画を採用。可燃系資源4区分を種類別排出の公式子葉として保持。"),
    "M124": dict(pref="山口県", city="光市", processor="光市／周南地区衛生施設組合・周南東部環境施設組合", top="https://www.city.hikari.lg.jp/kurashi_tetsuzuki/gomi/bunbetu/8851.html", guide="https://www.city.hikari.lg.jp/soshiki/3/kankyo_jigyo/recycle/haiki/946.html", note="令和8年度現行ページと現行基本計画期間内の14分別構造を照合。古紙は新聞類・雑誌類雑がみ・段ボールの3葉。"),
    "M125": dict(pref="山口県", city="長門市", processor="長門市／萩・長門清掃一部事務組合", top="https://www.city.nagato.yamaguchi.jp/soshiki/8/66178.html", guide="https://www.city.nagato.yamaguchi.jp/uploaded/attachment/37628.pdf", note="令和8年度ガイドと現行計画上の17分別を照合。地区差はカレンダー日程でtaxonomyは共通。"),
}

# title, kind, url, updated, used, issuer
source_specs = {
    "M116": [
        ("家庭ごみの分け方・出し方", "自治体公式Webページ", municipality_specs["M116"]["top"], "現行案内中", "燃やしてよいごみ、空きカン3区分、空きビン3区分、容器包装プラ3区分、不燃系4区分、資源化ごみ、粗大、特定家電、有害ごみ", "神石高原町"),
        ("粗大ごみ", "自治体公式Webページ", "https://www.jinsekigun.jp/town/formation/kankyoueisei/03/sodai/sodai/", "現行案内中", "粗大ごみの対象と排出経路", "神石高原町"),
        ("有害ごみ", "自治体公式Webページ", "https://www.jinsekigun.jp/town/formation/kankyoueisei/03/sodai/yugai/", "現行案内中", "乾電池・ボタン電池・充電式電池・蛍光灯・水銀製品等の現行経路", "神石高原町"),
    ],
    "M117": [
        ("令和8年（2026年）度ごみの分け方・出し方ガイド", "自治体公式Webページ", municipality_specs["M117"]["top"], "2026-06-25", "令和8年度のステーション収集・戸別収集体系と古紙等の現行案内", "下関市"),
        ("令和8年度ごみの分け方・出し方ガイド 前半", "自治体公式PDF", "https://www.city.shimonoseki.lg.jp/uploaded/attachment/93751.pdf", "令和8年度", "燃やせるごみ、資源ごみ、古紙の区分と前処理", "下関市"),
        ("令和8年度ごみの分け方・出し方ガイド 後半", "自治体公式PDF", "https://www.city.shimonoseki.lg.jp/uploaded/attachment/93738.pdf", "令和8年度", "燃やせないごみ、有害ごみ、粗大ごみ等の現行ルール", "下関市"),
    ],
    "M118": [
        ("家庭ごみの出し方", "自治体公式Webページ", municipality_specs["M118"]["guide"], "現行案内中", "燃やせる、プラ容器包装、燃やせない、月1回燃やせる、危険、びん缶、PET、紙製容器包装、古紙3区分", "宇部市"),
        ("びん・缶", "自治体公式Webページ", "https://www.city.ube.yamaguchi.jp/kurashi/gomi/dashikata/1001956/1001961.html", "2025-11-26", "びん・缶の前処理とスプレー缶の穴あけ必須", "宇部市"),
        ("充電式電池の出し方", "自治体公式Webページ", "https://www.city.ube.yamaguchi.jp/kurashi/gomi/dashikata/1001966/1014463.html", "現行案内中", "充電式電池はステーション外の回収ボックス等へ出す現行経路", "宇部市"),
        ("粗大ごみの戸別収集", "自治体公式Webページ", "https://www.city.ube.yamaguchi.jp/kurashi/gomi/dashikata/1001966/index.html", "現行案内中", "予約制有料の粗大ごみ戸別収集", "宇部市"),
    ],
    "M119": [
        ("令和8年度ごみ・資源収集カレンダー", "自治体公式Webページ", municipality_specs["M119"]["top"], "2026-01-27", "令和8年度に運用される住民向け分別体系", "山口市"),
        ("古紙の出し方", "自治体公式Webページ", "https://www.city.yamaguchi.lg.jp/site/gomisigen/69641.html", "現行案内中", "紙製容器包装・新聞・ダンボール・紙パック・雑がみの5品目を品目別に排出", "山口市"),
        ("金属・小型家電製品", "自治体公式Webページ", "https://www.city.yamaguchi.lg.jp/site/gomisigen/69645.html", "現行案内中", "金属・小型家電製品の現行区分", "山口市"),
        ("有害ごみ(1)", "自治体公式Webページ", "https://www.city.yamaguchi.lg.jp/site/gomisigen/79591.html", "2026-07-15", "スプレー缶・カセットボンベ・蛍光管・乾電池・水銀体温計等の現行DROP_OFF区分", "山口市"),
        ("有害ごみ(2)", "自治体公式Webページ", "https://www.city.yamaguchi.lg.jp/site/gomisigen/92657.html", "2026-07-15", "充電式電池・モバイルバッテリー・ボタン電池・電子たばこ等の現行DROP_OFF区分", "山口市"),
        ("ごみの出し方", "自治体公式Webページ", municipality_specs["M119"]["guide"], "現行案内中", "燃やせる・燃やせない・びん・缶・PET・プラ容器包装・粗大等の現行索引", "山口市"),
    ],
    "M121": [
        ("令和8年度家庭ごみ分別収集カレンダー", "自治体公式Webページ", municipality_specs["M121"]["top"], "2026-04-01", "令和8年度も共通の燃やせる・プラ容器包装・資源・危険・燃やせない体系が運用されること", "防府市"),
        ("新しいごみの分け方・出し方", "自治体公式Webページ", municipality_specs["M121"]["guide"], "2024-04-01", "可燃、資源7区分、危険6区分、不燃、粗大・埋立・一時多量ごみの現行分別冊子索引", "防府市"),
        ("ごみの分け方・出し方", "自治体公式Webページ", "https://www.city.hofu.yamaguchi.jp/soshiki/16/gomi-wakekatadashikata.html", "2024-04-01", "可燃・プラ容器包装等の具体的な現行前処理", "防府市"),
    ],
    "M122": [
        ("令和8年度一般廃棄物処理実施計画", "自治体公式PDF", municipality_specs["M122"]["guide"], "令和8年度", "燃やす袋ごみ、大型可燃、可燃系資源4区分、びん缶、PET、金属、小型家電、プラ2区分、大型不燃、有害、埋立の現行体系", "下松市"),
        ("金属類の出し方", "自治体公式Webページ", "https://www.city.kudamatsu.lg.jp/kankyou/seikatsu/kankyou/kannrikakari/kinzokuhaiki.html", "2026-06", "スプレー缶は使い切り、穴を開けて金属類へ出す現行ルール", "下松市"),
        ("スプレー缶・カセットボンベにガスが残っている場合", "自治体公式Webページ", "https://www.city.kudamatsu.lg.jp/kankyou/spraybombe.html", "現行案内中", "ガスが残る場合の市窓口経路", "下松市"),
    ],
    "M124": [
        ("令和8年度ごみ収集カレンダー", "自治体公式Webページ", municipality_specs["M124"]["top"], "令和8年度", "令和8年度も現行分別体系が運用されること", "光市"),
        ("ごみの分け方・出し方", "自治体公式Webページ", municipality_specs["M124"]["guide"], "現行案内中", "住民向け現行分別の品目・出し方", "光市"),
        ("一般廃棄物処理実施計画", "自治体公式PDF", "https://www.city.hikari.lg.jp/material/files/group/57/r06zisshikeikaku.pdf", "現行基本計画期間内", "14分別の構造と古紙3区分を照合する補強証拠", "光市"),
        ("スプレー缶・カセットボンベの出し方", "自治体公式Webページ", "https://www.city.hikari.lg.jp/soshiki/3/kankyo_jigyo/recycle/haiki/2344.html", "2026-02-10", "中身を使い切り必ず穴を開け、金属類へ出す現行ルール", "光市"),
    ],
    "M125": [
        ("令和8年度ごみ収集カレンダー・分別ガイド", "自治体公式Webページ", municipality_specs["M125"]["top"], "2026-02-27", "令和8年度の全地区で共通する住民向け分別体系と現行ガイドへの導線", "長門市"),
        ("令和8年度ごみの分け方・出し方ガイド", "自治体公式PDF", municipality_specs["M125"]["guide"], "令和8年度", "燃える、古紙・衣類5区分、紙容器、プラ容器、びん3色、缶、PET、不燃、電池、蛍光灯、粗大の現行体系", "長門市"),
        ("長門市一般廃棄物処理基本計画", "自治体公式PDF", "https://www.city.nagato.yamaguchi.jp/uploaded/life/39628_163300_misc.pdf", "現行計画", "17分別の構成を補強する公式計画", "長門市"),
    ],
}

categories: list[dict[str, str]] = []

def add(mid: str, name: str, rep: str, *, source: int = 1, parent: str = "", ui: str = "SORT_BUCKET",
        level: str = "PRIMARY", channel: str = "CURBSIDE", forbidden: str = NS, cond: str = "", fallback: str = NS,
        prep: str = NS, bag: str = "", size: str = "", bulky: str = "FALSE", note: str = "") -> None:
    categories.append({
        "municipality_id": mid, "自治体正式名称": name, "category_group": parent or name, "parent_name": parent,
        "classification_level": level, "collection_channel": channel, "代表品目": rep, "入れてはいけない物": forbidden,
        "適用条件": cond, "条件外の扱い": fallback, "出す前の処理": prep, "袋・容器のルール": bag,
        "サイズ・条件": size, "粗大ごみ扱いか": bulky, "予約が必要か": "TRUE" if channel == "BOOKED_PICKUP" else "FALSE",
        "有料か": "FALSE", "料金ルール": "", "自治体収集外か": "FALSE", "注意事項": note,
        "source_index": str(source), "出典ページ・該当箇所": name, "ui_role": ui, "rule_status": "CURRENT",
        "effective_from": "", "effective_to": "",
    })

# M116 神石高原町 — four projection parents; 18 resident-facing official leaves.
add("M116", "燃やしてよいごみ", "生ごみ・紙くず・木くず・布類等", prep="生ごみは水切りする")
add("M116", "空きカン", "スチール缶・アルミ缶・その他の缶")
add("M116", "スチール缶", "飲食用スチール缶", parent="空きカン", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中を洗う")
add("M116", "アルミ缶", "飲食用アルミ缶", parent="空きカン", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中を洗う")
add("M116", "その他の缶", "スプレー缶・カセットボンベ等", parent="空きカン", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中身を使い切る。つぶさない")
add("M116", "空きビン", "無色ビン・茶色ビン・その他のビン")
add("M116", "無色ビン", "無色の飲食用びん等", parent="空きビン", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ふたを外し、中を洗う")
add("M116", "茶色ビン", "茶色の飲食用びん等", parent="空きビン", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ふたを外し、中を洗う")
add("M116", "その他のビン", "無色・茶色以外のびん", parent="空きビン", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ふたを外し、中を洗う")
add("M116", "容器や包装のプラスチック", "ペットボトル・容器包装プラスチック・白色トレー")
add("M116", "ペットボトル", "PETマークの飲料等ボトル", parent="容器や包装のプラスチック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="キャップ・ラベルを外し、中を洗う")
add("M116", "容器や包装のプラスチック", "プラマークの容器包装", parent="容器や包装のプラスチック（親）", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="汚れを落として乾かす")
# The official page uses the same wording for the parent concept and one child stream. Rename projection parent internally without counting it as a leaf.
categories[-2]["自治体正式名称"] = "ペットボトル"
categories[-1]["自治体正式名称"] = "容器や包装のプラスチック（プラマーク）"
categories[-1]["parent_name"] = "容器や包装のプラスチック"
add("M116", "白色トレー", "白色食品トレー", parent="容器や包装のプラスチック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="白色のみ。汚れを落として乾かす")
add("M116", "不燃物・容器包装以外のプラスチック", "金属類・容器包装外プラスチック・不燃物・食用油")
add("M116", "金属類", "刃物・金属製品等", parent="不燃物・容器包装以外のプラスチック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="刃物等は安全に包む")
add("M116", "容器包装外のプラスチック", "プラスチック製品等", parent="不燃物・容器包装以外のプラスチック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=NS)
add("M116", "不燃物", "陶磁器・ガラス等", parent="不燃物・容器包装以外のプラスチック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="割れ物等は安全に包む")
add("M116", "天ぷら油（食用油）", "家庭の食用油", parent="不燃物・容器包装以外のプラスチック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ペットボトルへ入れ、しっかりふたをする")
add("M116", "資源化しているごみ", "新聞・雑誌・段ボール・牛乳パック・古着類", prep="紙類等は荷崩れしないようひもで十字に縛る")
add("M116", "粗大ごみ", "家具・大型電気製品・自転車・布団等", source=2, ui="REFERENCE_ONLY", bulky="TRUE", prep="ガラス等は分別して外す")
add("M116", "特定家庭用機器廃棄物", "テレビ・エアコン・冷蔵庫・冷凍庫・洗濯機", ui="REFERENCE_ONLY", channel="RETAILER_OR_MAKER", prep=NS, note="リサイクル料金と町の収集運搬手数料が必要")
add("M116", "有害ごみ", "乾電池・充電式電池・蛍光灯・水銀式体温計等", source=3, ui="REFERENCE_ONLY", channel="DROP_OFF", prep=NS)

# M117 下関市 — 10 official leaves; old paper parent has three separately bundled child leaves.
add("M117", "燃やせるごみ", "生ごみ・紙くず・可燃性家庭ごみ", source=2, prep="生ごみは水切りする")
add("M117", "資源ごみ（びん・缶）", "飲食用びん・缶等", source=2, prep="中身を空にする")
add("M117", "資源ごみ（ペットボトル）", "PETマークのペットボトル", source=2, prep="中をすすぎ、キャップ・ラベルを外す")
add("M117", "資源ごみ（プラスチック製容器包装）", "プラマークの容器包装", source=2, prep="汚れを落とす")
add("M117", "古紙", "新聞紙・雑誌類・ダンボール", source=2)
add("M117", "新聞紙", "新聞・折込チラシ", source=2, parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ひもで束ねる")
add("M117", "雑誌類", "雑誌・雑がみ等", source=2, parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ひもで束ねる")
add("M117", "ダンボール", "ダンボール", source=2, parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="たたんでひもで束ねる")
add("M117", "燃やせないごみ", "陶磁器・ガラス・金属製品・小型家電等", source=3, prep="危険物は安全に包む")
add("M117", "有害ごみ", "乾電池・蛍光管・水銀製品・モバイルバッテリー等", source=3, prep="電池類は安全措置を行う")
add("M117", "粗大ごみ", "指定袋に入らない大型家庭ごみ", source=3, ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE", prep=NS)

# M118 宇部市 — 11 station leaves + booked bulky + rechargeable-battery drop-off = 13 leaves.
add("M118", "月・水・金の燃やせるごみ", "生ごみ・紙くず等", prep="生ごみは水切りする")
add("M118", "プラスチック製容器包装", "プラマークの容器包装", prep="中身を使い切り、汚れを落とす")
add("M118", "燃やせないごみ", "陶磁器・ガラス・金属複合品等", prep="危険物は安全に包む")
add("M118", "月1回収集の燃やせるごみ", "指定寸法の枝木・大型可燃物等", prep=NS)
add("M118", "危険ごみ", "乾電池・蛍光管等", prep=NS)
add("M118", "びん・缶", "飲食用びん・缶・スプレー缶等", source=2, prep="中を空にする。スプレー缶は中身を使い切り、屋外で必ず穴を開ける")
add("M118", "ペットボトル", "PETマークのボトル", prep="キャップ・ラベルを外し、中を洗う")
add("M118", "紙製容器包装", "紙マークの容器包装", prep="汚れを除く")
add("M118", "古紙", "新聞・雑誌雑がみ・ダンボール")
add("M118", "古紙（新聞）", "新聞・折込チラシ", parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ひもで束ねる")
add("M118", "古紙（雑誌・雑がみ）", "雑誌・雑がみ", parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ひもで束ねる")
add("M118", "古紙（ダンボール）", "ダンボール", parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="たたんでひもで束ねる")
add("M118", "粗大ごみ", "大型家庭ごみ", source=4, ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE", prep=NS, note="予約制有料の戸別収集")
add("M118", "充電式電池", "小型充電式電池・モバイルバッテリー等", source=3, ui="REFERENCE_ONLY", channel="DROP_OFF", prep="端子を絶縁して回収ボックス等へ出す")

# M119 山口市 — fresh July 2026 hazardous split is authoritative; 15 current official leaves.
add("M119", "古紙", "紙製容器包装・新聞・ダンボール・紙パック・雑がみ", source=2)
add("M119", "紙製容器包装", "紙マークの容器包装", source=2, parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="品目別にまとめて出す")
add("M119", "新聞", "新聞・折込チラシ", source=2, parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ひもで束ねる")
add("M119", "ダンボール", "ダンボール", source=2, parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="たたんでひもで束ねる")
add("M119", "紙パック", "牛乳等の紙パック", source=2, parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="洗い、開いて乾かす")
add("M119", "雑がみ", "雑がみ", source=2, parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="品目別にまとめて出す")
add("M119", "ペットボトル", "PETマークのボトル", source=6, prep="キャップ・ラベルを外し、中を洗う")
add("M119", "プラスチック製容器包装", "プラマークの容器包装", source=6, prep="中身を使い切り、汚れを落とす")
add("M119", "びん", "飲食用びん等", source=6, prep="中を洗う")
add("M119", "缶", "飲食用缶等", source=6, prep="中を洗う")
add("M119", "金属・小型家電製品", "金属製品・小型家電等", source=3, prep="電池等を外す")
add("M119", "有害ごみ(1)", "スプレー缶・カセットボンベ・蛍光管・乾電池・水銀体温計等", source=4, ui="REFERENCE_ONLY", channel="DROP_OFF", prep="スプレー缶等は中身を使い切り、屋外で穴を開ける")
add("M119", "有害ごみ(2)", "小型充電式電池・モバイルバッテリー・ボタン電池・電子たばこ等", source=5, ui="REFERENCE_ONLY", channel="DROP_OFF", prep="電池類は端子を絶縁する")
add("M119", "燃やせるごみ", "生ごみ・紙くず等", source=6, prep="生ごみは水切りする")
add("M119", "燃やせないごみ", "陶磁器・ガラス等", source=6, prep="危険物は安全に包む")
add("M119", "粗大ごみ", "大型家庭ごみ", source=6, ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE", prep=NS)

# M121 防府市 — 18 leaves under resource/dangerous/paid projection parents.
add("M121", "燃やせるごみ（可燃ごみ）", "生ごみ・紙くず・革ゴム・プラスチック製品等", source=3, prep="生ごみは水切り。一辺50cm以内等の条件に従う", bag="防府市指定ごみ袋")
add("M121", "資源ごみ", "プラスチック・紙・紙パック・古紙・PET・缶・びん")
for name, rep, prep in [
    ("プラスチック製容器包装", "プラマークの容器包装", "中身を使い切り、汚れを落として水気を切る"),
    ("紙製容器包装", "紙マークの容器包装", "汚れを除く"),
    ("紙パック", "牛乳等の紙パック", "洗い、開いて乾かす"),
    ("古紙類", "新聞・雑誌・ダンボール等", "紙種別にまとめる"),
    ("ペットボトル", "PETマークのボトル", "キャップ・ラベルを外し、中を洗う"),
    ("缶", "飲食用缶等", "中を空にする"),
    ("びん類", "飲食用びん等", "ふたを外し、中を洗う"),
]: add("M121", name, rep, source=2, parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=prep)
add("M121", "危険ごみ", "スプレー缶・電池・水銀体温計・蛍光管・ライター・陶磁器ガラス類")
for name, rep, prep in [
    ("スプレー缶類", "スプレー缶・カセットボンベ", "中身を使い切り、屋外で穴を開ける"),
    ("乾電池類", "乾電池等", "電池類を分けて出す"),
    ("水銀体温計", "水銀体温計", "破損を防ぐ"),
    ("蛍光管", "蛍光管", "破損を防ぐ"),
    ("ライター類", "ライター等", "中身を使い切る"),
    ("陶磁器、ガラス類", "陶磁器・ガラス類", "割れ物等は安全に包む"),
]: add("M121", name, rep, source=2, parent="危険ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=prep)
add("M121", "燃やせないごみ（不燃ごみ）", "金属製品・小型家電等", source=2, prep="電池等を外す")
add("M121", "粗大ごみ・埋立ごみ・一時多量ごみ（有料収集）", "粗大ごみ・埋立ごみ・一時多量ごみ", source=2, ui="REFERENCE_ONLY")
add("M121", "粗大ごみ", "大型家庭ごみ", source=2, parent="粗大ごみ・埋立ごみ・一時多量ごみ（有料収集）", level="SUBCATEGORY", ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE", prep=NS)
add("M121", "埋立ごみ", "埋立処分対象の家庭ごみ", source=2, parent="粗大ごみ・埋立ごみ・一時多量ごみ（有料収集）", level="SUBCATEGORY", ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", prep=NS)
add("M121", "一時多量ごみ", "引越し等で一時的に多量となる家庭ごみ", source=2, parent="粗大ごみ・埋立ごみ・一時多量ごみ（有料収集）", level="SUBCATEGORY", ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", prep=NS)

# M122 下松市 — 15 leaves, including four separately bundled combustible resources.
add("M122", "燃やす袋ごみ", "生ごみ・可燃性家庭ごみ", source=1, prep="生ごみは水切りする")
add("M122", "大型可燃ごみ", "大型可燃性家庭ごみ", source=1, ui="REFERENCE_ONLY", bulky="TRUE", prep=NS)
add("M122", "可燃系資源", "新聞紙・雑誌類雑がみ・ダンボール・衣類", source=1)
add("M122", "新聞紙", "新聞・折込チラシ", source=1, parent="可燃系資源", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ひもで結束して種類別に出す")
add("M122", "雑誌類・雑がみ", "雑誌・雑がみ", source=1, parent="可燃系資源", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ひもで結束して種類別に出す")
add("M122", "ダンボール", "ダンボール", source=1, parent="可燃系資源", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="たたみ、ひもで結束して出す")
add("M122", "衣類", "衣類等", source=1, parent="可燃系資源", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="種類別に出す")
add("M122", "びん・かん類", "飲食用びん・缶等", source=1, prep="中を空にする")
add("M122", "ペットボトル", "PETマークのボトル", source=1, prep="キャップ・ラベルを外し、中を洗う")
add("M122", "金属類", "金属製品・スプレー缶等", source=2, prep="スプレー缶は中身を使い切り、必ず穴を開ける")
add("M122", "小型家電品", "小型家電等", source=1, prep="電池等を外す")
add("M122", "プラスチック製容器包装", "プラマークの容器包装", source=1, prep="汚れを落とす")
add("M122", "その他プラスチック類", "容器包装以外のプラスチック製品等", source=1, prep=NS)
add("M122", "大型不燃ごみ", "大型不燃性家庭ごみ", source=1, ui="REFERENCE_ONLY", bulky="TRUE", prep=NS)
add("M122", "有害ごみ", "乾電池・蛍光管等", source=1, prep=NS)
add("M122", "埋立ごみ", "陶磁器・ガラス等の埋立対象物", source=1, prep="危険物は安全に包む")

# M124 光市 — official plan explicitly maintains 14 divisions; old paper has exactly three leaves.
add("M124", "可燃ごみ", "生ごみ・紙くず等", source=2, prep="生ごみは水切りする")
add("M124", "可燃粗大ごみ", "大型可燃性家庭ごみ", source=2, ui="REFERENCE_ONLY", bulky="TRUE", prep=NS)
add("M124", "古紙類", "新聞類・雑誌類雑がみ・段ボール", source=3)
add("M124", "新聞類", "新聞・折込チラシ", source=3, parent="古紙類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="種類別にまとめる")
add("M124", "雑誌類・雑がみ", "雑誌・雑がみ", source=3, parent="古紙類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="種類別にまとめる")
add("M124", "段ボール", "段ボール", source=3, parent="古紙類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="たたんでまとめる")
add("M124", "古布類", "衣類・古布等", source=3, prep=NS)
add("M124", "びん・缶類", "びん・缶等", source=3, prep="中を空にする")
add("M124", "金属類", "金属製品・スプレー缶等", source=4, prep="スプレー缶等は中身を使い切り、必ず穴を開ける")
add("M124", "ペットボトル", "PETマークのボトル", source=3, prep="キャップ・ラベルを外し、中を洗う")
add("M124", "小型家電製品", "小型家電等", source=3, prep="電池等を外す")
add("M124", "容器・包装用プラスチック類", "プラマークの容器包装", source=3, prep="汚れを落とす")
add("M124", "その他プラスチック類", "容器包装以外のプラスチック製品等", source=3, prep=NS)
add("M124", "有害ごみ", "乾電池・蛍光管等", source=3, prep=NS)
add("M124", "陶磁器・ガラス・ゴム類", "陶磁器・ガラス・ゴム製品等", source=3, prep="割れ物等は安全に包む")

# M125 長門市 — 17 official divisions; five paper/clothing + three bottle-color child leaves.
add("M125", "燃えるごみ", "生ごみ・紙くず等", source=2, prep="生ごみは水切りする")
add("M125", "古紙・衣類", "新聞・ダンボール・雑誌雑紙・牛乳パック・衣類", source=2)
add("M125", "新聞", "新聞・折込チラシ", source=2, parent="古紙・衣類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ひもで束ねる")
add("M125", "ダンボール", "ダンボール", source=2, parent="古紙・衣類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="たたんでひもで束ねる")
add("M125", "雑誌・雑紙", "雑誌・雑紙", source=2, parent="古紙・衣類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ひもで束ねる")
add("M125", "牛乳パック", "牛乳等の紙パック", source=2, parent="古紙・衣類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="洗い、開いて乾かす")
add("M125", "衣類", "衣類等", source=2, parent="古紙・衣類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=NS)
add("M125", "紙製容器包装類", "紙マークの容器包装", source=2, prep="汚れを除く")
add("M125", "プラスチック製容器包装類", "プラマークの容器包装", source=2, prep="汚れを落とす")
add("M125", "ビン", "無色・茶色・その他色のびん", source=2)
add("M125", "無色", "無色びん", source=2, parent="ビン", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ふたを外し、中を洗う")
add("M125", "茶色", "茶色びん", source=2, parent="ビン", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ふたを外し、中を洗う")
add("M125", "その他色", "無色・茶色以外のびん", source=2, parent="ビン", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ふたを外し、中を洗う")
add("M125", "缶", "飲食用缶等", source=2, prep="中を空にする")
add("M125", "ペットボトル", "PETマークのボトル", source=2, prep="キャップ・ラベルを外し、中を洗う")
add("M125", "燃えないごみ", "金属・陶磁器・ガラス・小型家電等", source=2, prep="危険物は安全に包む")
add("M125", "電池類", "乾電池・充電式電池等", source=2, prep="電池類を分けて出す")
add("M125", "蛍光灯（管）", "蛍光灯・蛍光管等", source=2, prep="破損を防ぐ")
add("M125", "粗大ごみ", "大型家庭ごみ", source=2, ui="REFERENCE_ONLY", bulky="TRUE", prep=NS)


def ensure_deferred() -> None:
    path = MASTER / "05_deferred_municipalities.csv"
    fields, rows = read_csv(path)
    additions = {
        "M120": {"municipality_id":"M120","都道府県":"山口県","市町村":"萩市","status":"DEFERRED","reason":"令和8年度も大島・見島・相島地区では一部分別区分が異なることを萩市公式50音表が明示し、地域別CURRENT分別資料が併存する。現行municipality単位Schema/UIでは住民の地域scopeを安全に解決できないため一旦対象外。固定IDと公式根拠を保持する。","deferred_date":CHECKED,"decision_source":"SCHEMA_SCOPE_LIMITATION"},
        "M123": {"municipality_id":"M123","都道府県":"山口県","市町村":"岩国市","status":"DEFERRED","reason":"令和8年度に岩国・由宇・周東・玖珂と錦・美川・美和・本郷等で住民向けCURRENTルールが併存し、食品トレー等で実際の分別先・排出方法が異なる。現行municipality単位Schema/UIでは安全に単一体系化できないため一旦対象外。固定IDと公式根拠を保持する。","deferred_date":CHECKED,"decision_source":"SCHEMA_SCOPE_LIMITATION"},
    }
    existing = {r.get("municipality_id") for r in rows}
    for mid in sorted(DEFERRED):
        if mid not in existing:
            rows.append(additions[mid])
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
                "verified_date": CHECKED, "notes": f"Batch 12 official source host ({issuer})",
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
            "municipality_id": mid, "都道府県": spec["pref"], "市町村": spec["city"], "実装区分": "中国5県全市町村",
            "ごみ処理主体": spec["processor"], "自治体ごみトップURL": spec["top"], "分別ガイドURL": spec["guide"],
            "品目検索URL": "", "やさしい日本語URL": "", "多言語資料URL": "", "対象年度": "令和8年度",
            "最終確認日": CHECKED, "確認ステータス": "QA_REQUIRED", "備考": spec["note"],
            "official_category_count": "", "reviewed_category_count": str(leaf_count(mid)),
            "category_count_basis": "住民が排出時に選択する現行公式分別区分を公式索引・現年度資料で全件照合。上位グループは子葉へ二重計上せず、特殊経路はCURRENT公式葉としてREFERENCE_ONLYで保持。",
            "category_count_verified": "TRUE", "category_count_check_status": "MANUAL_INDEX_REVIEW",
            "category_count_review_id": f"CR-{mid}-CATEGORY-COVERAGE", "category_count_reviewed_date": CHECKED,
            "category_count_reviewed_by": REVIEWER, "search_service_check_status": "NOT_CHECKED", "search_service_check_evidence": "",
            "easy_japanese_check_status": "NOT_CHECKED", "easy_japanese_check_evidence": "",
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
                "notes": f"{CHECKED} Batch 12 resident-facing category completeness review",
            })
    return rows


def main() -> None:
    if set(municipality_specs) != TARGETS or set(source_specs) != TARGETS:
        raise ValueError("Batch12 target mismatch")
    expected = {"M116":18,"M117":10,"M118":13,"M119":15,"M121":18,"M122":15,"M124":14,"M125":17}
    actual = {mid: leaf_count(mid) for mid in sorted(TARGETS)}
    if actual != expected:
        raise ValueError(f"Batch12 leaf count mismatch: {actual}")
    ensure_deferred()
    ensure_registry()
    OUT.mkdir(parents=True, exist_ok=True)
    p = "batch_12_"
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
