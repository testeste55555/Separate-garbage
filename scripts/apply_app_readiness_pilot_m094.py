#!/usr/bin/env python3
"""Apply the first municipality-wide 40-item APP readiness review (M094).

The review is intentionally separate from category completeness.  It preserves
every existing mapping_id, adds only the missing conditional branches, and
promotes Hiroshima City atomically only after all 40 pairs are represented by
item-specific official evidence and complete condition branches.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from schema_v12 import (
    COVERAGE_FIELDS,
    MAPPING_FIELDS,
    SOURCE_FIELDS,
    read_csv,
    write_csv,
)


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data" / "research"
MASTER = ROOT / "data" / "master"
AUDIT_PATH = RESEARCH / "app_readiness" / "m094_item_review.csv"
CHECKED = "2026-08-24"
REVIEWER = "OPENAI_CODEX_M094_APP_READINESS_V1"
MID = "M094"

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
    "S-M094-01": "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026095/1026096/1003182.html",
    "IS-M094-04": "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008420.html",
    "IS-M094-05": "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008422.html",
    "IS-M094-06": "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008424.html",
    "IS-M094-07": "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008426.html",
    "IS-M094-08": "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026095/1026096/1046707.html",
    "IS-M094-09": "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008419.html",
    "IS-M094-10": "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008421.html",
    "IS-M094-11": "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008423.html",
}


def source(source_id: str, title: str, used: str) -> dict[str, str]:
    return {
        "municipality_id": MID,
        "source_id": source_id,
        "資料名": title,
        "資料種別": "自治体公式Webページ",
        "公式URL": URLS[source_id],
        "発行主体": "広島市",
        "対象年度": "2026年度／取得時点現行",
        "ページ更新日": "2026-04-01",
        "取得確認日": CHECKED,
        "使用した情報": used,
        "優先度": "1",
        "現行性": "CURRENT",
        "備考": "M094 40品目APP readiness手動レビューの品目別公式根拠。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    }


NEW_SOURCES = [
    source("IS-M094-09", "家庭ごみ分別50音事典（あ行）",
           "アルミ缶・衣類・剪定枝・LED電球／LED蛍光管の分別先と条件"),
    source("IS-M094-10", "家庭ごみ分別50音事典（さ行）",
           "雑誌・新聞・スチール缶・スプレー缶・食用油・陶磁器の分別先と条件"),
    source("IS-M094-11", "家庭ごみ分別50音事典（な行）",
           "ナイフ・布類の分別先と危険物の排出条件"),
]


# All materially different official destinations/conditions are separate
# branches, including two branches with the same destination when the
# preparation rule differs.  This is the evidence reviewed by the Pilot
# validator and mutation RED TEAM.
BRANCHES: dict[str, list[Branch]] = {
    "I001": [b("C-M094-02", "IS-M094-06", "「ペットボトル」2行", "ペットボトル",
        "飲料・酒類・みりん類・酢類・しょうゆ類等の対象PETボトル",
        "キャップとラベルを外し、中を洗い、軽くつぶして透明・半透明袋へ入れる",
        "食用油・ソース・洗剤等のボトルはリサイクルプラ")],
    "I002": [b("C-M094-03", "S-M094-01", "ペットボトル／ごみの出し方（キャップ）", "プラ製のキャップ",
        "ペットボトルから外したプラスチック製キャップ",
        "本体から外し、付着物を取り除いて透明・半透明袋へ入れる",
        "金属製のふたは不燃ごみ、汚れが取れない物は可燃ごみ")],
    "I003": [
        b("C-M094-03", "S-M094-01", "ペットボトル／ごみの出し方（ラベル）", "プラ製のラベル",
          "ペットボトルから外したプラスチック製ラベル", "本体から外し、透明・半透明袋へ入れる",
          "紙製ラベルは可燃ごみ"),
        b("C-M094-01", "IS-M094-10", "「しょうゆの容器 ペットボトル」の備考（紙ラベル）", "紙ラベル",
          "ペットボトルから外した紙製ラベル", "本体から外し、じょうぶな紙袋またはポリ袋へ入れる",
          "プラスチック製ラベルはリサイクルプラ"),
    ],
    "I004": [b("C-M094-06", "IS-M094-09", "「アルミ缶」の行", "アルミ缶",
        "中身を使い切ったアルミ缶", "中を洗ってきれいにし、じょうぶな袋へ入れる",
        "スプレー缶は同じ資源ごみだが、屋外ガス抜き等の個別条件に従う")],
    "I005": [b("C-M094-06", "IS-M094-10", "「スチール缶」の行", "スチール缶",
        "中身を使い切ったスチール缶", "中を洗ってきれいにし、じょうぶな袋へ入れる",
        "中身の残る油缶・塗料缶等は市で収集しない")],
    "I006": [b("C-M094-06", "IS-M094-06", "「びん(ガラス) 薬・飲料・食料品等用」の行", "びん(ガラス) 薬・飲料・食料品等用",
        "薬・飲料・食料品等用のガラスびん", "ふたを外し、中を洗って、じょうぶな袋へ入れる",
        "乳白色化粧品びん・マニキュアびん・耐熱ガラスは不燃ごみ")],
    "I007": [
        b("C-M094-03", "S-M094-01", "リサイクルプラ／食品トレーの例示とごみの出し方", "トレイ 発泡トレイ",
          "白色の食品用発泡トレイで付着物を取り除ける物", "きれいに洗い、透明・半透明袋へ入れる",
          "汚れが取り除けない物は可燃ごみ。店頭回収も利用可"),
        b("C-M094-01", "S-M094-01", "リサイクルプラ／ごみの出し方（汚れが取れない場合）", "汚れが取れない食品トレイ",
          "付着物を水洗い・拭き取りで取り除けない白色食品トレイ", "中身を空にし、じょうぶな紙袋またはポリ袋へ入れる",
          "汚れを取り除ける物はリサイクルプラ"),
    ],
    "I008": [
        b("C-M094-03", "IS-M094-05", "「トレイ 発泡トレイ」「トレイ プラスチック製」の行", "トレイ 発泡トレイ／プラスチック製",
          "色柄を問わず、食品用プラスチックトレイで付着物を取り除ける物", "きれいに洗い、透明・半透明袋へ入れる",
          "汚れが取り除けない物は可燃ごみ。公式区分は色で分けない"),
        b("C-M094-01", "S-M094-01", "リサイクルプラ／ごみの出し方（汚れが取れない場合）", "汚れが取れない食品トレイ",
          "付着物を水洗い・拭き取りで取り除けない色柄食品トレイ", "中身を空にし、じょうぶな紙袋またはポリ袋へ入れる",
          "汚れを取り除ける物はリサイクルプラ"),
    ],
    "I009": [
        b("C-M094-03", "IS-M094-06", "「弁当ガラ(プラスチック製容器)」の行", "弁当ガラ(プラスチック製容器)",
          "商品包装のプラスチック製弁当容器で汚れを取り除ける物", "きれいに洗い、透明・半透明袋へ入れる",
          "汚れが取り除けない物・紙製容器は可燃ごみ"),
        b("C-M094-01", "S-M094-01", "リサイクルプラ／ごみの出し方（汚れが取れない場合）", "汚れが取れない弁当容器",
          "付着物を水洗い・拭き取りで取り除けないプラスチック製弁当容器", "中身を空にし、じょうぶな紙袋またはポリ袋へ入れる",
          "汚れを取り除ける物はリサイクルプラ"),
        b("C-M094-01", "S-M094-01", "リサイクルプラ／カップ類（紙製は可燃ごみ）", "紙製の食品容器",
          "紙製の弁当・食品容器", "中身を空にし、じょうぶな紙袋またはポリ袋へ入れる",
          "プラスチック製で汚れを取り除ける物はリサイクルプラ", "OFFICIAL_RULE_DERIVED"),
    ],
    "I010": [
        b("C-M094-03", "IS-M094-04", "「菓子袋 プラスチック製」の行", "菓子袋 プラスチック製",
          "プラスチック製の菓子袋で中身・汚れを取り除ける物", "中身を残さず、透明・半透明袋へ入れる",
          "紙製又は汚れが取り除けない物は可燃ごみ"),
        b("C-M094-01", "IS-M094-04", "「菓子袋 紙製」の行", "菓子袋 紙製",
          "紙製の菓子袋", "中身を空にし、じょうぶな紙袋またはポリ袋へ入れる",
          "プラスチック製で汚れを取り除ける物はリサイクルプラ"),
        b("C-M094-01", "S-M094-01", "リサイクルプラ／ごみの出し方（汚れが取れない場合）", "汚れが取れない菓子袋",
          "中身・汚れを取り除けないプラスチック製菓子袋", "中身が飛散しないよう紙袋またはポリ袋へ入れる",
          "汚れを取り除ける物はリサイクルプラ"),
    ],
    "I011": [b("C-M094-03", "IS-M094-07", "「レジ袋」の行", "レジ袋",
        "商品の包装に使われたレジ袋", "中身を空にし、透明・半透明袋へ入れる",
        "家庭で包装以外に使用したプラスチック袋はその他プラ")],
    "I012": [
        b("C-M094-03", "IS-M094-06", "「発泡スチロール 商品を保護するもの」の行", "発泡スチロール 商品を保護するもの",
          "商品を保護する容器包装・梱包材", "付着物を取り除き、透明・半透明袋へ入れる",
          "商品保護用でない発泡スチロールはその他プラ"),
        b("C-M094-04", "IS-M094-06", "「発泡スチロール 商品を保護するもの以外」の行", "発泡スチロール 商品を保護するもの以外",
          "商品を保護する容器包装ではない発泡スチロール製品", "透明・半透明袋へ入れる",
          "商品を保護する容器包装・梱包材はリサイクルプラ"),
    ],
    "I013": [b("C-M094-06", "S-M094-01", "資源ごみ／出せる物の例（新聞紙）", "新聞紙",
        "家庭から出る新聞紙", "ひもでしばってまとめる",
        "再生できない・著しく汚れた紙は可燃ごみ")],
    "I014": [b("C-M094-06", "S-M094-01", "資源ごみ／出せる物の例（段ボール）", "段ボール",
        "家庭から出る段ボール", "折りたたみ、ひもでしばってまとめる",
        "再生できない・著しく汚れた物は可燃ごみ")],
    "I015": [b("C-M094-06", "IS-M094-10", "「雑誌」の行", "雑誌",
        "家庭から出る雑誌", "ひもでしばってまとめる",
        "再生できない・著しく汚れた紙は可燃ごみ")],
    "I016": [
        b("C-M094-06", "IS-M094-04", "「菓子箱」の行", "菓子箱",
          "名刺大以上の再生可能な雑紙・菓子箱", "箱は折り畳み、紙類としてひもでしばってまとめる",
          "名刺大未満又は再生できない・汚れた紙は可燃ごみ"),
        b("C-M094-01", "S-M094-01", "可燃ごみ／再生できない紙くず・資源ごみの紙サイズ条件", "再生できない紙くず",
          "名刺大未満又は再生できない・著しく汚れた雑紙", "じょうぶな紙袋またはポリ袋へ入れる",
          "名刺大以上の再生可能な雑紙・菓子箱は資源ごみ", "OFFICIAL_RULE_DERIVED"),
    ],
    "I017": [b("C-M094-01", "IS-M094-04", "「紙パック」「牛乳パック」の行", "紙パック／牛乳パック",
        "紙パック（裏にアルミ箔が貼られた物を含む）", "じょうぶな紙袋またはポリ袋へ入れる",
        "牛乳パックはスーパー等の店頭回収も利用可")],
    "I018": [b("C-M094-01", "S-M094-01", "可燃ごみ／生ごみ・ごみの出し方", "生ごみ",
        "家庭から出る台所の生ごみ", "よく水を切り、新聞紙などに包んで紙袋またはポリ袋へ入れる",
        "多量の場合は通常収集に出さず自己搬入又は許可業者へ依頼")],
    "I019": [b("C-M094-01", "IS-M094-05", "「ティッシュペーパー」の行", "ティッシュペーパー",
        "使用済みティッシュペーパー", "じょうぶな紙袋またはポリ袋へ入れる",
        "未使用の紙箱はフィルムを外し資源ごみ")],
    "I020": [b("C-M094-01", "IS-M094-04", "「紙おむつ」の行", "紙おむつ",
        "家庭で使用した紙おむつ", "汚物を便所へ捨て、じょうぶな紙袋またはポリ袋へ入れる",
        "事業活動に伴う物は家庭ごみ収集へ出さない")],
    "I021": [b("C-M094-06", "IS-M094-09", "「衣類」の行", "衣類",
        "再使用又は資源化できる家庭の衣類", "ひもでしばるか、じょうぶな袋へ入れる",
        "まだ着られる服は譲渡・再利用も検討。布団は大型ごみ")],
    "I022": [b("C-M094-05", "IS-M094-04", "「傘」の行", "傘",
        "家庭で使用した傘", "ひもでしばるか、透明・半透明のじょうぶなポリ袋へ入れる",
        "事業活動に伴う物は家庭ごみ収集へ出さない")],
    "I023": [
        b("C-M094-05", "IS-M094-05", "「陶磁器」の行", "陶磁器",
          "食料品・飲料用の陶磁器、又は最長辺・最大径30cm未満の陶磁器", "透明・半透明のじょうぶなポリ袋へ入れる",
          "食料品・飲料用以外で30cm以上の物は大型ごみ"),
        b("C-M094-08", "IS-M094-05", "「陶磁器」の備考（30cm以上）", "陶磁器（大型）",
          "食料品・飲料用以外で最長辺又は最大径30cm以上", "大きさを測り、大型ごみ受付センターへ予約する",
          "30cm未満又は食料品・飲料用は不燃ごみ"),
    ],
    "I024": [
        b("C-M094-05", "IS-M094-04", "「ガラス 耐熱ガラス」の行", "ガラス 耐熱ガラス",
          "最長辺・最大径30cm未満の耐熱ガラス製品", "透明・半透明のじょうぶなポリ袋へ入れる",
          "30cm以上は大型ごみ。耐熱ガラス以外は資源ごみ"),
        b("C-M094-06", "IS-M094-04", "「ガラス その他のガラス」の行", "ガラス その他のガラス",
          "最長辺・最大径30cm未満の耐熱ガラス以外のガラス製品", "じょうぶな袋へ入れる",
          "耐熱ガラスは不燃ごみ、30cm以上は大型ごみ"),
        b("C-M094-08", "IS-M094-04", "「ガラス」2行の備考（30cm以上）", "ガラス製品（大型）",
          "最長辺又は最大径30cm以上のガラス製品", "破損防止措置をして大型ごみ受付センターへ予約する",
          "30cm未満は材質により不燃ごみ又は資源ごみ"),
    ],
    "I025": [
        b("C-M094-06", "S-M094-01", "資源ごみ／ガラスくず・割れたガラスの出し方", "割れたガラス",
          "耐熱ガラス以外の割れたガラス・ガラスくず", "新聞紙などに包み、じょうぶな袋へ入れて「危険」と書く",
          "耐熱ガラスの破片は不燃ごみ"),
        b("C-M094-05", "IS-M094-04", "「ガラス 耐熱ガラス」の行", "割れた耐熱ガラス",
          "割れた耐熱ガラス", "新聞紙などに包み、透明・半透明のじょうぶな袋へ入れて「危険」と書く",
          "耐熱ガラス以外のガラスくずは資源ごみ"),
    ],
    "I026": [
        b("C-M094-06", "IS-M094-11", "「ナイフ」の行", "ナイフ／包丁",
          "包丁・ナイフ等の金属製刃物", "刃を新聞紙などで包み、じょうぶな袋へ入れて「危険」と書く",
          "かみそり・カッターナイフの替刃は不燃ごみ"),
        b("C-M094-05", "IS-M094-04", "「かみそりの刃／カッターナイフの刃」の行", "かみそりの刃／カッターナイフの刃",
          "かみそり又はカッターナイフの替刃", "新聞紙などに包み、透明・半透明のじょうぶな袋へ入れて「危険」と書く",
          "包丁・ナイフ等は資源ごみ"),
    ],
    "I027": [b("C-M094-07", "IS-M094-05", "「電池 その他」の行", "電池 その他",
        "家庭用の乾電池", "端子をテープで覆い、資源ごみと別の袋へ入れて「有害」と書く",
        "小型家電本体は電池を取り外し、製品区分に従う")],
    "I028": [b("C-M094-07", "IS-M094-05", "「電池 ボタン型電池」の行", "電池 ボタン型電池",
        "家庭用のボタン電池・コイン電池", "端子をテープで覆い、資源ごみと別の袋へ入れて「有害」と書く",
        "機器本体は電池を取り外し、製品区分に従う")],
    "I029": [b("C-M094-07", "IS-M094-08", "小型充電式電池・モバイルバッテリーの出し方", "モバイルバッテリー",
        "家庭で使用したモバイルバッテリー（破損・膨張品を含む）", "端子をテープで覆い、有害ごみとして別袋・有害表示で出す",
        "破損・膨張していない小型品は区役所等の回収ボックスも利用可")],
    "I030": [
        b("C-M094-07", "IS-M094-04", "「蛍光管」の行", "蛍光管",
          "水銀を使用した蛍光管", "箱又は新聞紙で包み、資源ごみと別の袋へ入れて「有害」と書く",
          "LED蛍光管は不燃ごみ"),
        b("C-M094-05", "IS-M094-09", "「LED電球・LED蛍光管」の行", "LED蛍光管",
          "LED式の蛍光管形照明", "透明・半透明のじょうぶなポリ袋へ入れる",
          "水銀を使用した蛍光管は有害ごみ"),
    ],
    "I031": [
        b("C-M094-05", "IS-M094-05", "「電球」の行", "電球",
          "白熱電球又はLED電球", "新聞紙などに包み、透明・半透明のじょうぶな袋へ入れる",
          "蛍光式（水銀使用）の電球は有害ごみ"),
        b("C-M094-07", "IS-M094-05", "「電球」の備考（蛍光式は有害ごみ）", "蛍光式電球",
          "水銀を使用した電球形蛍光灯", "箱又は新聞紙で包み、資源ごみと別の袋へ入れて「有害」と書く",
          "白熱電球・LED電球は不燃ごみ"),
    ],
    "I032": [
        b("C-M094-06", "IS-M094-10", "「スプレー缶」の行", "スプレー缶",
          "使い切るか中身を空にした家庭用スプレー缶", "火気のない風通しのよい屋外でガスを抜き、穴を開けず、じょうぶな袋へ入れる",
          "中身を空にできない物は市で収集しない"),
        b("C-M094-09", "IS-M094-10", "「スプレー缶」の備考（中身が残る物は収集不可）", "中身が残るスプレー缶",
          "中身を安全に空にできないスプレー缶", "製造メーカーへ相談するか、処分業者へ依頼する",
          "中身を空にできた物は穴を開けず資源ごみ"),
    ],
    "I033": [b("C-M094-05", "IS-M094-07", "「ライター(使い捨てライター)」の行", "ライター(使い捨てライター)",
        "家庭用の使い捨てライター", "他の不燃ごみと袋を分け、透明・半透明のじょうぶな袋へ入れて「ライター」と書く",
        "他の不燃ごみと同じ袋へ混ぜない")],
    "I034": [
        b("C-M094-05", "S-M094-01", "不燃ごみ／小型家電・大型ごみの定義", "小型家電",
          "最長辺・最大径30cm未満の小型家電（棒状・板状の特則を除く）", "電池を取り外し、透明・半透明のじょうぶな袋へ入れる",
          "30cm以上は大型ごみ。取り外した電池は有害ごみ", "OFFICIAL_RULE_DERIVED"),
        b("C-M094-08", "S-M094-01", "大型ごみ／定義・家電製品", "家電製品（大型ごみ基準以上）",
          "最長辺又は最大径30cm以上の家電製品", "大きさを測り、大型ごみ受付センターへ予約する",
          "30cm未満は不燃ごみ。家庭用パソコン・家電4品目は別経路", "OFFICIAL_RULE_DERIVED"),
    ],
    "I035": [b("C-M094-05", "S-M094-01", "不燃ごみ／充電式電池を取り外せない家電製品", "充電式電池を取り外せない家電製品",
        "大型ごみ基準未満で充電式電池を安全に取り外せない小型家電",
        "他の不燃ごみと袋を分け、透明・半透明のじょうぶな袋へ入れて「危険」と書く",
        "大型ごみ基準以上は大型ごみ。取り外せる場合は電池を有害ごみへ")],
    "I036": [b("C-M094-08", "IS-M094-06", "「ふとん」の行", "ふとん",
        "家庭で使用した布団", "大型ごみ受付センターへ排出日・場所を予約し、案内に従う",
        "布団の中綿だけを少量出す場合は可燃ごみ")],
    "I037": [b("C-M094-08", "S-M094-01", "大型ごみ／家電リサイクル法対象機器", "家電リサイクル法対象機器",
        "エアコン、テレビ、冷蔵庫・冷凍庫、洗濯機・衣類乾燥機",
        "販売店引取、指定引取場所への自己搬入、又は市の大型ごみを選び、必要なリサイクル料金手続を行う",
        "家庭用パソコンは市で収集せず、メーカー等の回収へ")],
    "I038": [b("C-M094-09", "IS-M094-06", "「パソコン(本体・ディスプレイ)」の行", "パソコン(本体・ディスプレイ)",
        "家庭用パソコン本体又はディスプレイ", "メーカー又はパソコン3R推進協会へ回収を依頼する",
        "回収ボックス投入口に入る小型品は小型家電回収も利用可")],
    "I039": [b("C-M094-01", "IS-M094-10", "「食用油(てんぷら油)」の行", "食用油(てんぷら油)",
        "家庭で使用した食用油", "布や新聞紙などへ染み込ませて出す",
        "回収可能な店舗へ持参するリサイクル経路も利用可")],
    "I040": [
        b("C-M094-01", "IS-M094-09", "「枝(庭木の剪定ごみ)」の行", "枝(庭木の剪定ごみ)",
          "長さ約50cm、太さが概ね生木5cm以下・乾燥木10cm以下で少量の剪定枝", "約50cmに切り、ひもで束ね、1回2束程度まで出す",
          "太い枝又は一時多量の剪定枝は通常収集へ出さず自己搬入・許可業者へ依頼"),
        b("C-M094-09", "IS-M094-09", "「枝(庭木の剪定ごみ)」の備考（多量は収集不可）", "通常収集条件外の剪定枝",
          "太さ上限を超える又は一時に多量となる剪定枝", "市指定施設へ自己搬入するか、許可業者へ収集を依頼する",
          "規定内の少量の枝は約50cmに切り可燃ごみ"),
    ],
}


def main() -> None:
    _, items = read_csv(MASTER / "04_common_items_master.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")

    item_by = {r["internal_item_id"]: r for r in items}
    expected_items = {f"I{i:03d}" for i in range(1, 41)}
    assert set(BRANCHES) == expected_items
    assert all(BRANCHES[iid] for iid in expected_items)
    category_by = {(r["municipality_id"], r["category_id"]): r for r in categories}

    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    for row in NEW_SOURCES:
        source_by[(MID, row["source_id"])] = row
    sources = sorted(source_by.values(), key=lambda r: (r["municipality_id"], r["source_id"]))
    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    for sid, url in URLS.items():
        row = source_by[(MID, sid)]
        assert row["公式URL"] == url and row["official_verified"] == "TRUE"

    existing_by_pair: dict[str, list[dict[str, str]]] = {}
    for row in mappings:
        if row["municipality_id"] == MID:
            existing_by_pair.setdefault(row["internal_item_id"], []).append(row)
    for rows in existing_by_pair.values():
        rows.sort(key=lambda r: (int(r.get("branch_order") or 0), r["mapping_id"]))

    retained = [r for r in mappings if r["municipality_id"] != MID]
    generated: list[dict[str, str]] = []
    audit: list[dict[str, str]] = []
    used_mapping_ids = {r["mapping_id"] for r in retained}

    for iid in sorted(expected_items):
        old = existing_by_pair.get(iid, [])
        for order, spec in enumerate(BRANCHES[iid], start=1):
            category = category_by[(MID, spec.category_id)]
            evidence_source = source_by[(MID, spec.source_id)]
            if order <= len(old):
                mapping_id = old[order - 1]["mapping_id"]
            else:
                mapping_id = f"MAP-{MID}-{iid}-APP-{order:02d}"
            assert mapping_id not in used_mapping_ids
            used_mapping_ids.add(mapping_id)
            row = {field: "" for field in MAPPING_FIELDS}
            row.update({
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
                "item_evidence_url": evidence_source["公式URL"],
                "item_evidence_locator": spec.locator,
                "確認日": CHECKED,
                "mapping_status": "APP_READY",
                "evidence_scope": "ITEM_SPECIFIC",
                "branch_review_status": "COMPLETE",
                "reviewed_date": CHECKED,
                "reviewed_by": REVIEWER,
                "備考": (f"M094 40品目APP readiness手動レビュー。{spec.basis}。" +
                         (f" {spec.note}" if spec.note else "")).strip(),
            })
            generated.append(row)
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
                "item_evidence_url": evidence_source["公式URL"],
                "item_evidence_locator": spec.locator,
                "branch_review_status": "COMPLETE",
                "checked_date": CHECKED,
                "reviewer": REVIEWER,
                "note": spec.note or "公式品目行又は公式区分ルールと例外条件を手動照合。",
            })

    assert len(generated) == 59
    mappings = sorted(retained + generated,
                      key=lambda r: (r["municipality_id"], r["internal_item_id"],
                                     int(r.get("branch_order") or 0), r["mapping_id"]))

    coverage_by = {(r["municipality_id"], r["internal_item_id"]): r for r in coverage}
    for iid in sorted(expected_items):
        first = BRANCHES[iid][0]
        evidence_source = source_by[(MID, first.source_id)]
        row = coverage_by[(MID, iid)]
        row.update({
            "coverage_status": "APP_READY",
            "mapping_branch_count": str(len(BRANCHES[iid])),
            "branch_completeness_confirmed": "TRUE",
            "evidence_scope": "ITEM_SPECIFIC",
            "item_evidence_source_id": first.source_id,
            "item_evidence_url": evidence_source["公式URL"],
            "item_evidence_locator": first.locator,
            "reviewed_date": CHECKED,
            "reviewed_by": REVIEWER,
            "notes": "M094の全40品目・全条件枝を公式資料へ手動照合し、自治体単位でatomic APP_READY昇格。",
        })
    coverage = sorted(coverage_by.values(), key=lambda r: (r["municipality_id"], r["internal_item_id"]))

    write_csv(RESEARCH / "03_sources_master.csv", SOURCE_FIELDS, sources)
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", COVERAGE_FIELDS, coverage)
    write_csv(AUDIT_PATH, AUDIT_FIELDS, audit)
    print("M094_APP_READINESS_APPLIED items=40 branches=59 app_ready_pairs=40 sources_added=3")


if __name__ == "__main__":
    main()
