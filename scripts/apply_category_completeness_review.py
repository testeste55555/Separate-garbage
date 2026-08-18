#!/usr/bin/env python3
"""Apply the 2026-08-18 category-completeness review to the existing 15 municipalities.

This script is intentionally limited to Pilot and Batch 01. It preserves the
original seven corrections, adds Ishinomaki's four official bottle leaves,
records multi-source review evidence, and leaves Batch 02 untouched.
"""

from __future__ import annotations

from pathlib import Path

from schema_v12 import (
    CATEGORY_FIELDS, CATEGORY_REVIEW_EVIDENCE_FIELDS, MUNICIPALITY_FIELDS, RESEARCH,
    SOURCE_FIELDS, read_csv, stable_category_review_id, write_csv,
)


REVIEWED_DATE = "2026-08-18"
REVIEWER = "OPENAI_WORK_MANUAL_INDEX_REVIEW"
OFFICIAL_COUNT_REVIEWER = "OPENAI_WORK_OFFICIAL_COUNT_MATCH"
ISHINOMAKI_PLAN_URL = "https://www.city.ishinomaki.lg.jp/cont/10301000/030/3974/kihonkeikaku2.pdf"


REVIEW = {
    "M001": (
        "S-M001-02", "14",
        "S-M001-02の1ページポスターを「燃やせるごみ」から「紙製容器包装」まで全見出し照合。"
        "CURRENT非EXCLUDED_NOTICEは14区分。家電リサイクル対象製品と町で収集できないごみはEXCLUDED_NOTICEとして件数外。",
    ),
    "M002": (
        "S-M002-01", "20",
        "S-M002-01本文の「燃えるごみ」から「プラスチック類」までと同ページの公式リンクS-M002-02〜04を全件照合。"
        "衣川地域限定の鉄くずを条件付き区分として追加し、CURRENT非EXCLUDED_NOTICEは20区分。市で収集・処理できないものは件数外。",
    ),
    "M003": (
        "S-M003-02", "13",
        "S-M003-02目次P4〜11とP4〜8の「燃えるごみ」「燃えないごみ」「資源ごみ」の全見出しを照合。"
        "紙パックを追加し、CURRENT非EXCLUDED_NOTICEは13区分。P10〜11の町で収集・受入できないものは件数外。",
    ),
    "M004": (
        "S-M004-01", "12",
        "S-M004-01の「ごみの分け方と出し方」カテゴリナビを先頭から末尾まで照合し、S-M004-02〜04の資源・大形不燃・有害危険見出しも照合。"
        "CURRENT非EXCLUDED_NOTICEは12区分。収集・受入しないものは件数外。",
    ),
    "M005": (
        "S-M005-04", "19",
        "S-M005-04（令和8年3月策定）第2編17〜18ページの5種類19分別と表2-1をS-M005-02の現行案内へ照合。"
        "あきびん4種類をC-M005-10の公式SUBCATEGORYとして保持し、公式粒度のCURRENT葉区分は19。"
        "C-M005-10は教材UIの投影親、PLANNEDのプラスチックと市で収集しないごみは件数外。",
    ),
    "M006": (
        "S-M006-02", "16",
        "S-M006-02 P2の分別区分表を「もやせるごみ」から「乾電池」まで照合し、P2〜4の粗大ごみ・小型電子機器・収集外も照合。"
        "布類を追加し、CURRENT非EXCLUDED_NOTICEは16区分。収集しないものは件数外。",
    ),
    "M007": (
        "S-M007-01", "8",
        "S-M007-01の分別種類表を「燃やせるごみ」から「プラスチック」まで全件照合し、燃やせる粗大ごみと使用済み食用油の公式見出しも照合。"
        "CURRENT非EXCLUDED_NOTICEは8区分。町で収集・施設受入できないものは件数外。",
    ),
    "M008": (
        "S-M008-02", "9",
        "S-M008-02全30ページの「ごみの区分」列を先頭から末尾まで照合し、可燃・不燃・容器包装・資源回収4種・有害・粗大の9区分へ集約。"
        "CURRENT非EXCLUDED_NOTICEは9区分。町で収集できないごみは件数外。",
    ),
    "M009": (
        "S-M009-02", "8",
        "S-M009-02目次P1とP1〜15の分別章を「もやせるごみ」から「水銀含有ごみ」まで全件照合。"
        "CURRENT非EXCLUDED_NOTICEは8区分。家電4品目・パソコン・処理不能物は町で収集・処理できないものへ集約し件数外。",
    ),
    "M011": (
        "S-M011-02", "14",
        "S-M011-02の1ページ図解を「燃えるごみ」から資源各区分、危険な物、粗大ごみ、剪定枝まで全見出し照合。"
        "CURRENT非EXCLUDED_NOTICEは14区分。ステーションに出せないごみは件数外。",
    ),
    "M013": (
        "S-M013-01", "9",
        "S-M013-01目次P3とP4〜26の分別章を資源プラスチック、資源4種、可燃、不燃、粗大、拠点回収まで全件照合。"
        "CURRENT非EXCLUDED_NOTICEは9区分。区で収集できないものは件数外。",
    ),
    "M030": (
        "S-M030-01", "10",
        "S-M030-01本文索引を「可燃ごみ」から「市で収集処理しないごみ」まで全件照合。"
        "電池類・蛍光管等は公式の2小見出しへ分け、CURRENT非EXCLUDED_NOTICEは10区分。市で収集処理しないごみは件数外。",
    ),
    "M094": (
        "S-M094-01", "8",
        "S-M094-01のページ内公式索引を「可燃ごみ」から「大型ごみ（有料）」まで全件照合。"
        "CURRENT非EXCLUDED_NOTICEは8区分。市では収集しないごみは件数外。",
    ),
}


SOURCE_ADDITIONS = {
    "S-M005-04": {
        "municipality_id": "M005", "source_id": "S-M005-04",
        "資料名": "石巻市一般廃棄物処理基本計画", "資料種別": "自治体公式計画",
        "公式URL": ISHINOMAKI_PLAN_URL, "発行主体": "石巻市",
        "対象年度": "令和8年度〜令和17年度", "ページ更新日": "2026-04-01",
        "取得確認日": REVIEWED_DATE, "使用した情報": "5種類19分別・あきびん4種類・紙類5種類",
        "優先度": "1", "現行性": "現行", "備考": "令和8年3月策定、第2編17〜18ページ表2-1",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
}


REVIEW_EVIDENCE = {
    "M001": [("S-M001-02", "PRIMARY_INDEX", "1ページポスターの全分別見出し")],
    "M002": [
        ("S-M002-01", "PRIMARY_INDEX", "本文の燃えるごみ〜プラスチック類と地域別見出し"),
        ("S-M002-02", "SUPPLEMENTAL_INDEX", "粗大ごみ収集見出し"),
        ("S-M002-03", "SUPPLEMENTAL_INDEX", "電池類・蛍光管の見出し"),
        ("S-M002-04", "SUPPLEMENTAL_INDEX", "小型充電式電池の見出し"),
    ],
    "M003": [("S-M003-02", "PRIMARY_INDEX", "目次P4〜11とP4〜8の全分別見出し")],
    "M004": [
        ("S-M004-01", "PRIMARY_INDEX", "ごみの分け方と出し方カテゴリナビ全件"),
        ("S-M004-02", "SUPPLEMENTAL_INDEX", "資源ごみ見出し"),
        ("S-M004-03", "SUPPLEMENTAL_INDEX", "大形・不燃ごみ見出し"),
        ("S-M004-04", "SUPPLEMENTAL_INDEX", "有害・危険ごみ及び乾電池見出し"),
    ],
    "M005": [
        ("S-M005-04", "OFFICIAL_TOTAL", "第2編17〜18ページ：5種類19分別、表2-1のあきびん4種類"),
        ("S-M005-02", "SUPPLEMENTAL_INDEX", "現行家庭ごみ案内の全区分見出し"),
    ],
    "M006": [("S-M006-02", "PRIMARY_INDEX", "P2〜4の収集区分・粗大・小型家電・収集外")],
    "M007": [("S-M007-01", "PRIMARY_INDEX", "分別種類表と燃やせる粗大ごみ・食用油見出し")],
    "M008": [("S-M008-02", "PRIMARY_INDEX", "全30ページのごみの区分列")],
    "M009": [("S-M009-02", "PRIMARY_INDEX", "目次P1とP1〜15の分別章")],
    "M010": [("S-M010-01", "OFFICIAL_TOTAL", "家庭系ごみの出し方：5種14分別")],
    "M011": [("S-M011-02", "PRIMARY_INDEX", "令和8年度1ページ図解の全分別見出し")],
    "M013": [("S-M013-01", "PRIMARY_INDEX", "目次P3とP4〜26の分別章")],
    "M030": [("S-M030-01", "PRIMARY_INDEX", "本文索引の可燃ごみ〜市で収集処理しないごみ")],
    "M094": [("S-M094-01", "PRIMARY_INDEX", "ページ内公式索引の可燃ごみ〜大型ごみ")],
    "M102": [("S-M102-01", "OFFICIAL_TOTAL", "ごみの分別：13種類")],
}


def category(**values: str) -> dict[str, str]:
    bag_rule = values.pop("bag_rule", "")
    locator = values.pop("locator", "")
    row = {field: "" for field in CATEGORY_FIELDS}
    row.update({
        "parent_category_id": "", "classification_level": "PRIMARY", "サイズ・条件": "",
        "粗大ごみ扱いか": "FALSE", "予約が必要か": "FALSE", "有料か": "FALSE", "料金ルール": "",
        "自治体収集外か": "FALSE", "注意事項": "", "確認日": REVIEWED_DATE,
        "ui_role": "SORT_BUCKET", "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
    })
    row.update(values)
    row["袋・容器のルール"] = bag_rule
    row["出典ページ・該当箇所"] = locator
    return row


ADDITIONS = {
    "C-M002-21": category(
        municipality_id="M002", category_id="C-M002-21", 自治体正式名称="鉄くず（衣川地域のみ）",
        category_group="金属資源", 表示順="16", collection_channel="CURBSIDE",
        代表品目="トタン・針金・金属製品", 入れてはいけない物="衣川地域以外の鉄くず・危険物・処理困難物",
        適用条件="衣川地域のリサイクルステーションに出す場合のみ",
        条件外の扱い="衣川地域以外は材質・大きさに応じて燃えないごみ又は許可業者へ相談",
        出す前の処理="異物を除き指定コンテナへ直接入れる", bag_rule="指定コンテナへ直接投入",
        source_id="S-M002-01", 出典URL="https://www.city.oshu.iwate.jp/soshiki/5/1051/2/3/316.html",
        locator="リサイクルの出し方／金属類／鉄くず（衣川地域のみ）",
    ),
    "C-M003-14": category(
        municipality_id="M003", category_id="C-M003-14", 自治体正式名称="紙パック",
        category_group="資源ごみ（紙類）", 表示順="6", collection_channel="CURBSIDE",
        代表品目="牛乳パック・飲料用紙パック", 入れてはいけない物="内側がアルミ加工された紙パック・汚れた紙パック",
        適用条件="洗浄して乾燥できる紙パック", 条件外の扱い="燃えるごみ",
        出す前の処理="水洗いして乾燥し平たく伸ばす", bag_rule="紙ひもで束ねる",
        source_id="S-M003-02", 出典URL="https://www.town.nishiwaga.lg.jp/material/files/group/5/0604gomihyakka.pdf",
        locator="8ページ 資源ごみ／紙パック",
    ),
    "C-M005-15": category(
        municipality_id="M005", category_id="C-M005-15", 自治体正式名称="スプレー缶・ガスカートリッジ",
        category_group="資源ごみ", 表示順="5", collection_channel="CURBSIDE",
        代表品目="スプレー缶・カセットボンベ・ガスカートリッジ", 入れてはいけない物="中身が残っているもの・飲食用缶",
        適用条件="中身を使い切ったスプレー缶・ガスカートリッジ", 条件外の扱い="中身が残る場合は販売店等へ相談",
        出す前の処理="中身を使い切る", bag_rule="黄色の指定袋",
        注意事項="火気のない場所で中身が空であることを確認",
        source_id="S-M005-02", 出典URL="https://www.city.ishinomaki.lg.jp/cont/10210000/1582/kateigomi-wakekata-dasikata.pdf",
        locator="資源ごみ／スプレー缶・ガスカートリッジ",
    ),
    "C-M005-16": category(
        municipality_id="M005", category_id="C-M005-16", 自治体正式名称="古着・布類",
        category_group="資源ごみ", 表示順="9", collection_channel="CURBSIDE",
        代表品目="古着・タオル・シーツ・布類", 入れてはいけない物="ぬれた物・汚れた物・綿入り製品",
        適用条件="再利用できる清潔な古着・布類", 条件外の扱い="燃やせるごみ",
        出す前の処理="洗濯し乾かす", bag_rule="古着・布類の指定袋",
        source_id="S-M005-02", 出典URL="https://www.city.ishinomaki.lg.jp/cont/10210000/1582/kateigomi-wakekata-dasikata.pdf",
        locator="資源ごみ／古着・布類",
    ),
    "C-M005-17": category(
        municipality_id="M005", category_id="C-M005-17", 自治体正式名称="紙パック",
        category_group="資源ごみ（紙類）", 表示順="14", collection_channel="CURBSIDE",
        代表品目="牛乳パック・飲料用紙パック", 入れてはいけない物="内側がアルミ加工された紙パック・汚れた紙パック",
        適用条件="洗浄して乾燥できる紙パック", 条件外の扱い="燃やせるごみ",
        出す前の処理="水洗いし乾かして開く", bag_rule="紙ひもで結束",
        source_id="S-M005-02", 出典URL="https://www.city.ishinomaki.lg.jp/cont/10210000/1582/kateigomi-wakekata-dasikata.pdf",
        locator="資源ごみ／紙類／紙パック",
    ),
    "C-M005-18": category(
        municipality_id="M005", category_id="C-M005-18", 自治体正式名称="使用済小型家電",
        category_group="拠点回収", 表示順="15", collection_channel="DROP_OFF",
        代表品目="スマートフォン・デジタルカメラ・携帯ゲーム機・電卓", 入れてはいけない物="家電4品目・回収ボックスに入らない物",
        適用条件="回収対象品目で投入口横40cm×縦20cmに入るもの", 条件外の扱い="市の通常区分又は販売店・メーカーへ相談",
        出す前の処理="電池を外し個人情報を消去", bag_rule="回収ボックスへ投入",
        ui_role="REFERENCE_ONLY",
        source_id="S-M005-02", 出典URL="https://www.city.ishinomaki.lg.jp/cont/10210000/1582/kateigomi-wakekata-dasikata.pdf",
        locator="使用済小型家電（できるだけ回収ボックスへ）",
    ),
    "C-M005-19": category(
        municipality_id="M005", category_id="C-M005-19",
        自治体正式名称="一升びん・ビールびん・リターナブルびん",
        category_group="資源物（あきびん）", parent_category_id="C-M005-10",
        classification_level="SUBCATEGORY", 表示順="8", collection_channel="CURBSIDE",
        代表品目="一升びん・ビールびん・リターナブルびん",
        入れてはいけない物="びんの蓋や栓・せともの・ガラス製品・電球・薬びん",
        適用条件="一升びん・ビールびん等の繰り返し使用できるびん",
        条件外の扱い="色に応じたあきびん区分又は燃やせないごみ",
        出す前の処理="蓋や栓を外し中をすすぐ", bag_rule="収集日に指定コンテナへ",
        ui_role="REFERENCE_ONLY", source_id="S-M005-04", 出典URL=ISHINOMAKI_PLAN_URL,
        locator="第2編18ページ 表2-1／あきびん／一升びん・ビールびん・リターナブルびん",
    ),
    "C-M005-20": category(
        municipality_id="M005", category_id="C-M005-20", 自治体正式名称="無色透明びん",
        category_group="資源物（あきびん）", parent_category_id="C-M005-10",
        classification_level="SUBCATEGORY", 表示順="9", collection_channel="CURBSIDE",
        代表品目="無色透明の飲料・食品用びん",
        入れてはいけない物="びんの蓋や栓・せともの・ガラス製品・電球・薬びん",
        適用条件="無色透明のあきびん", 条件外の扱い="びんの色又は用途に応じた公式区分",
        出す前の処理="蓋や栓を外し中をすすぐ", bag_rule="収集日に指定コンテナへ",
        ui_role="REFERENCE_ONLY", source_id="S-M005-04", 出典URL=ISHINOMAKI_PLAN_URL,
        locator="第2編18ページ 表2-1／あきびん／無色透明びん",
    ),
    "C-M005-21": category(
        municipality_id="M005", category_id="C-M005-21", 自治体正式名称="茶色びん",
        category_group="資源物（あきびん）", parent_category_id="C-M005-10",
        classification_level="SUBCATEGORY", 表示順="10", collection_channel="CURBSIDE",
        代表品目="茶色の飲料・食品用びん",
        入れてはいけない物="びんの蓋や栓・せともの・ガラス製品・電球・薬びん",
        適用条件="茶色のあきびん", 条件外の扱い="びんの色又は用途に応じた公式区分",
        出す前の処理="蓋や栓を外し中をすすぐ", bag_rule="収集日に指定コンテナへ",
        ui_role="REFERENCE_ONLY", source_id="S-M005-04", 出典URL=ISHINOMAKI_PLAN_URL,
        locator="第2編18ページ 表2-1／あきびん／茶色びん",
    ),
    "C-M005-22": category(
        municipality_id="M005", category_id="C-M005-22", 自治体正式名称="その他色びん",
        category_group="資源物（あきびん）", parent_category_id="C-M005-10",
        classification_level="SUBCATEGORY", 表示順="11", collection_channel="CURBSIDE",
        代表品目="青・緑・黒等のその他色の飲料・食品用びん",
        入れてはいけない物="びんの蓋や栓・せともの・ガラス製品・電球・薬びん",
        適用条件="無色透明・茶色以外のあきびん", 条件外の扱い="びんの色又は用途に応じた公式区分",
        出す前の処理="蓋や栓を外し中をすすぐ", bag_rule="収集日に指定コンテナへ",
        ui_role="REFERENCE_ONLY", source_id="S-M005-04", 出典URL=ISHINOMAKI_PLAN_URL,
        locator="第2編18ページ 表2-1／あきびん／その他色びん",
    ),
    "C-M006-17": category(
        municipality_id="M006", category_id="C-M006-17", 自治体正式名称="布類",
        category_group="紙類・布類", 表示順="13", collection_channel="CURBSIDE",
        代表品目="綿50%以上の衣類・布類", 入れてはいけない物="綿50%未満・汚れた物・濡れた物",
        適用条件="綿50%以上の布類", 条件外の扱い="もやせるごみ",
        出す前の処理="洗濯し乾かす", bag_rule="ひもで束ねる又は指定方法に従う",
        source_id="S-M006-02", 出典URL="https://www.town.ogawara.miyagi.jp/secure/1106/R8ippannhaikibutusyorizissikeikaku.pdf",
        locator="2ページ 5 一般廃棄物の収集・運搬及び排出方法／紙類・布類",
    ),
}


ORDER_OVERRIDES = {
    "M002": {f"C-M002-{n:02d}": str(n + 1) for n in range(16, 21)},
    "M003": {f"C-M003-{n:02d}": str(n + 1) for n in range(6, 14)},
    "M005": {
        "C-M005-09": "6", "C-M005-10": "7", "C-M005-11": "12", "C-M005-16": "13",
        "C-M005-05": "14", "C-M005-06": "15", "C-M005-07": "16", "C-M005-08": "17",
        "C-M005-17": "18", "C-M005-18": "19", "C-M005-12": "20",
        "C-M005-13": "21", "C-M005-14": "22",
    },
    "M006": {"C-M006-13": "14", "C-M006-14": "15", "C-M006-15": "16", "C-M006-16": "17"},
}


def update_categories(path: Path) -> int:
    fields, rows = read_csv(path)
    by_id = {row["category_id"]: row for row in rows}
    for mid, overrides in ORDER_OVERRIDES.items():
        for category_id, display_order in overrides.items():
            if category_id in by_id:
                by_id[category_id]["表示順"] = display_order
    if "C-M005-04" in by_id:
        by_id["C-M005-04"]["代表品目"] = "乾電池・蛍光管・水銀製品"
        by_id["C-M005-04"]["出す前の処理"] = "蛍光管を保護・電池端子を絶縁"
    if "C-M005-10" in by_id:
        by_id["C-M005-10"].update({
            "category_group": "資源物（あきびん）", "parent_category_id": "",
            "classification_level": "PRIMARY", "ui_role": "SORT_BUCKET",
            "注意事項": "教材UI投影親。公式区分数はCURRENTの4子区分を数え、この親は重複計上しない。",
        })
    dataset_mids = {row["municipality_id"] for row in rows}
    for category_id, row in ADDITIONS.items():
        if row["municipality_id"] in dataset_mids:
            by_id[category_id] = dict(row)
    result = sorted(by_id.values(), key=lambda row: (row["municipality_id"], int(row["表示順"]), row["category_id"]))
    write_csv(path, fields or CATEGORY_FIELDS, result)
    return len(result)


def update_municipalities(path: Path) -> int:
    _, rows = read_csv(path)
    for row in rows:
        review = REVIEW.get(row["municipality_id"])
        if review:
            _, reviewed_count, basis = review
            row.update({
                "最終確認日": REVIEWED_DATE, "official_category_count": "",
                "reviewed_category_count": reviewed_count, "category_count_basis": basis,
                "category_count_verified": "TRUE", "category_count_check_status": "MANUAL_INDEX_REVIEW",
                "category_count_review_id": stable_category_review_id(row["municipality_id"]),
                "category_count_reviewed_date": REVIEWED_DATE, "category_count_reviewed_by": REVIEWER,
            })
        elif row.get("category_count_check_status") != "NOT_REVIEWED":
            row["category_count_review_id"] = stable_category_review_id(row["municipality_id"])
        if row["municipality_id"] == "M005":
            row.update({
                "official_category_count": "19", "reviewed_category_count": "",
                "category_count_check_status": "OFFICIAL_COUNT_MATCHED",
                "category_count_reviewed_by": OFFICIAL_COUNT_REVIEWER,
            })
    write_csv(path, MUNICIPALITY_FIELDS, rows)
    return len(rows)


def update_sources(path: Path) -> int:
    fields, rows = read_csv(path)
    dataset_mids = {row["municipality_id"] for row in rows}
    by_id = {row["source_id"]: row for row in rows}
    for source_id, row in SOURCE_ADDITIONS.items():
        if row["municipality_id"] in dataset_mids:
            by_id[source_id] = dict(row)
    evidence_ids = {
        source_id for mid in dataset_mids
        for source_id, _, _ in REVIEW_EVIDENCE.get(mid, [])
    }
    for row in by_id.values():
        if row["source_id"] in evidence_ids:
            row["取得確認日"] = REVIEWED_DATE
    result = sorted(by_id.values(), key=lambda row: (row["municipality_id"], row["source_id"]))
    write_csv(path, fields or SOURCE_FIELDS, result)
    return len(result)


def update_review_evidence(path: Path, municipality_path: Path) -> int:
    _, municipalities = read_csv(municipality_path)
    dataset_mids = {row["municipality_id"] for row in municipalities}
    rows = []
    for mid in sorted(dataset_mids):
        review_id = stable_category_review_id(mid)
        for index, (source_id, role, locator) in enumerate(REVIEW_EVIDENCE.get(mid, []), 1):
            rows.append({
                "review_evidence_id": f"CRE-{mid}-{index:02d}", "review_id": review_id,
                "municipality_id": mid, "source_id": source_id, "locator": locator,
                "evidence_role": role, "notes": "2026-08-18 category completeness review",
            })
    write_csv(path, CATEGORY_REVIEW_EVIDENCE_FIELDS, rows)
    return len(rows)


def main() -> None:
    bundles = [
        (
            RESEARCH / "pilot" / "pilot_municipalities.csv", RESEARCH / "pilot" / "pilot_categories.csv",
            RESEARCH / "pilot" / "pilot_sources.csv", RESEARCH / "pilot" / "pilot_category_review_evidence.csv",
        ),
        (
            RESEARCH / "batches" / "batch_01" / "batch_01_municipalities.csv",
            RESEARCH / "batches" / "batch_01" / "batch_01_categories.csv",
            RESEARCH / "batches" / "batch_01" / "batch_01_sources.csv",
            RESEARCH / "batches" / "batch_01" / "batch_01_category_review_evidence.csv",
        ),
        (
            RESEARCH / "04_municipalities_research.csv", RESEARCH / "02_categories_master.csv",
            RESEARCH / "03_sources_master.csv", RESEARCH / "08_category_review_evidence.csv",
        ),
    ]
    for municipality_path, category_path, source_path, review_evidence_path in bundles:
        print(
            municipality_path.parent.relative_to(RESEARCH),
            f"municipalities={update_municipalities(municipality_path)}",
            f"categories={update_categories(category_path)}",
            f"sources={update_sources(source_path)}",
            f"review_evidence={update_review_evidence(review_evidence_path, municipality_path)}",
        )


if __name__ == "__main__":
    main()
