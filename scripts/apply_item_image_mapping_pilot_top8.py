#!/usr/bin/env python3
"""Apply the official item-mapping pilot for 10 image items and 8 municipalities.

The two district-variant municipalities in the Style Research TOP10 (Fukuyama
and Onomichi) are intentionally excluded.  This script is deterministic and
may be rerun safely; it never promotes a branch to APP_READY.
"""

from __future__ import annotations

import csv
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
APP = ROOT / "data" / "app"
CHECKED = "2026-08-24"
REVIEWER = "OPENAI_CODEX_IMAGE_MAPPING_PILOT_V1"

TARGETS = ["M094", "M095", "M097", "M104", "M105", "M106", "M107", "M109"]
ITEMS = ["I001", "I007", "I013", "I004", "I006", "I031", "I029", "I014", "I033", "I017"]
PILOT_FIELDS = [
    "pair_order", "municipality_id", "municipality_name", "internal_item_id",
    "canonical_name", "display_name", "review_status", "evidence_basis",
    "category_id", "category_name", "condition", "preparation",
    "exception_destination", "item_evidence_source_id", "item_evidence_url",
    "item_evidence_locator", "checked_date", "reviewer", "note",
]


def source(mid: str, sid: str, title: str, kind: str, url: str, used: str, issuer: str) -> dict[str, str]:
    return {
        "municipality_id": mid,
        # Supplemental, reviewed item sources use the IS-* namespace so the
        # canonical union remains distinguishable from batch source bundles.
        "source_id": "I" + sid,
        "資料名": title,
        "資料種別": kind,
        "公式URL": url,
        "発行主体": issuer,
        "対象年度": "2026年度／取得時点現行",
        "ページ更新日": "",
        "取得確認日": CHECKED,
        "使用した情報": used,
        "優先度": "1",
        "現行性": "CURRENT",
        "備考": "画像品目mapping Pilotの品目別公式根拠として追加。",
        "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    }


NEW_SOURCES = [
    source("M094", "S-M094-04", "家庭ごみ分別50音事典（か行）", "自治体公式Webページ",
           "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008420.html",
           "紙パック・缶・ガラスびんの分別先と出し方", "広島市"),
    source("M094", "S-M094-05", "家庭ごみ分別50音事典（た行）", "自治体公式Webページ",
           "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008422.html",
           "電球の分別先と破損防止", "広島市"),
    source("M094", "S-M094-06", "家庭ごみ分別50音事典（は行）", "自治体公式Webページ",
           "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008424.html",
           "ペットボトルの対象条件・例外とガラスびんの分別先", "広島市"),
    source("M094", "S-M094-07", "家庭ごみ分別50音事典（や・ら・わ行）", "自治体公式Webページ",
           "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008426.html",
           "使い捨てライターの分別先と別袋表示", "広島市"),
    source("M094", "S-M094-08", "小型充電式電池の出し方", "自治体公式Webページ",
           "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026095/1026096/1046707.html",
           "モバイルバッテリーの有害ごみ・回収ボックス経路", "広島市"),
    source("M095", "S-M095-03", "令和8年度からのごみの出し方", "自治体公式Webページ",
           "https://www.city.kure.lg.jp/soshiki/19/gomidashinew-html.html",
           "資源物・プラスチック資源・有害危険ごみ等の対象品目と出し方", "呉市"),
    source("M097", "S-M097-03", "ごみ分別50音順一覧（24頁）", "自治体公式Webページ",
           "https://www.city.mihara.hiroshima.jp/soshiki/23/112720.html",
           "紙パック・牛乳パックの分別先", "三原市"),
    source("M097", "S-M097-04", "ごみ分別50音順一覧（25頁）", "自治体公式Webページ",
           "https://www.city.mihara.hiroshima.jp/soshiki/23/112724.html",
           "食品トレイ・新聞の分別先", "三原市"),
    source("M097", "S-M097-05", "ごみ分別50音順一覧（26頁）", "自治体公式Webページ",
           "https://www.city.mihara.hiroshima.jp/soshiki/23/112725.html",
           "段ボールの分別先", "三原市"),
    source("M097", "S-M097-06", "ごみ分別50音順一覧（27頁）", "自治体公式Webページ",
           "https://www.city.mihara.hiroshima.jp/soshiki/23/112728.html",
           "電球の分別先", "三原市"),
    source("M104", "S-M104-04", "家庭ごみの出し方（ごみブック）", "自治体公式PDF",
           "https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_all.pdf",
           "10品目の分別区分と排出条件", "東広島市"),
    source("M104", "S-M104-05", "小型充電式電池等の出し方", "自治体公式Webページ",
           "https://www.city.higashihiroshima.lg.jp/soshiki/seikatsukankyo/8/4/1/21260.html",
           "モバイルバッテリーの有害ごみ区分と絶縁", "東広島市"),
    source("M104", "S-M104-06", "雑誌・雑がみ・ダンボールの出し方", "自治体公式Webページ",
           "https://www.city.higashihiroshima.lg.jp/soshiki/seikatsukankyo/8/4/1/15033.html",
           "ダンボール・紙パックの資源回収区分", "東広島市"),
    source("M109", "S-M109-03", "モバイルバッテリー等の捨て方", "自治体公式Webページ",
           "https://www.town.kaita.lg.jp/img/koenokouhou/202404/22.html",
           "モバイルバッテリーの有害ごみ区分と絶縁", "海田町"),
]


# category_id, source_id, locator, condition, preparation, exception, evidence_basis, note
R: dict[str, dict[str, tuple[str, str, str, str, str, str, str, str]]] = {
    "M094": {
        "I001": ("C-M094-02", "S-M094-06", "「ペットボトル」の行", "PETマークのある飲料・酒類・特定調味料用ボトル", "キャップとラベルを外し、中を洗い、つぶす", "油・ソース・洗剤等のボトルはリサイクルプラ", "DIRECT_ITEM", "50音事典の品目行を採用。"),
        "I007": ("C-M094-03", "S-M094-01", "リサイクルプラ欄（食品トレイの例示）", "商品を入れた容器包装で、プラマークのある白色食品トレイ", "中身を除き、洗って乾かす", "汚れが落ちない物は可燃ごみ", "OFFICIAL_CATEGORY_RULE", "容器包装の公式例示と条件を適用。"),
        "I013": ("C-M094-06", "S-M094-01", "資源ごみ欄（紙類・新聞）", "家庭から出る新聞紙", "ひもで縛ってまとめる", "著しく汚れた紙は可燃ごみ", "DIRECT_ITEM", "公式区分欄の新聞表記を採用。"),
        "I004": ("C-M094-06", "S-M094-04", "「空き缶」の行", "飲料・食品等のアルミ製空き缶", "中身を空にして洗う", "スプレー缶は有害ごみ", "DIRECT_ITEM", "50音事典の空き缶行を採用。"),
        "I006": ("C-M094-06", "S-M094-06", "「びん(ガラス) 薬・飲料・食料品等用」の行", "薬・飲料・食料品等用のガラスびん", "中を洗って、じょうぶな袋に入れる", "乳白色の化粧品びん・マニキュアびんは不燃ごみ", "DIRECT_ITEM", "50音事典の用途別ガラスびん行を採用。"),
        "I031": ("C-M094-05", "S-M094-05", "「電球」の行", "白熱電球・LED電球", "新聞紙などに包み、内容を表示する", "蛍光管・電球形蛍光灯は有害ごみ", "DIRECT_ITEM", "50音事典の電球行を採用。"),
        "I029": ("C-M094-07", "S-M094-08", "モバイルバッテリー欄", "家庭で使用した小型充電式電池内蔵のモバイルバッテリー", "端子をテープで絶縁する", "膨張・破損品は収集日に有害ごみ、通常品は回収ボックスも可", "DIRECT_ITEM", "専用公式案内を採用。"),
        "I014": ("C-M094-06", "S-M094-01", "資源ごみ欄（段ボール）", "家庭から出る段ボール", "折りたたみ、ひもで縛る", "汚れた物は可燃ごみ", "DIRECT_ITEM", "公式区分欄の段ボール表記を採用。"),
        "I033": ("C-M094-05", "S-M094-07", "「ライター（使い捨て）」の行", "中身を使い切った使い捨てライター", "火の気のない屋外でガスを抜き、別袋にして『ライター』と表示", "中身が残る場合も他の不燃ごみと混ぜない", "DIRECT_ITEM", "50音事典の使い捨てライター行を採用。"),
        "I017": ("C-M094-01", "S-M094-04", "「紙パック」「紙パック（裏にアルミ箔が貼ってあるもの）」「牛乳パック」の行", "紙パック（裏にアルミ箔が貼ってある物を含む）", "じょうぶな紙袋またはポリ袋に入れる", "牛乳パックはできるだけスーパー等の店頭回収を利用", "DIRECT_ITEM", "50音事典では市収集時は可燃ごみ。"),
    },
    "M095": {
        "I001": ("C-M095-05", "S-M095-03", "資源物（びん類・缶類・ペットボトル）欄", "PETマークのある飲料・調味料用ボトル", "キャップとラベルを外し、中を洗う", "汚れが取れない物は燃えるごみ", "DIRECT_ITEM", "現行分別ページを採用。"),
        "I007": ("C-M095-04", "S-M095-03", "プラスチック資源欄（トレイ）", "プラスチック製の白色食品トレイ", "中身を使い切り、汚れを落とす", "汚れが落ちない物は燃えるごみ", "OFFICIAL_CATEGORY_RULE", "プラスチック資源の対象例と共通条件を適用。"),
        "I013": ("C-M095-06", "S-M095-03", "資源物（紙類）欄（新聞）", "新聞・折込広告", "種類別にまとめ、ひもで十文字に縛る", "汚れ・におい・防水加工等の禁忌紙は燃えるごみ", "DIRECT_ITEM", "紙類の具体的排出方法を採用。"),
        "I004": ("C-M095-05", "S-M095-03", "資源物（缶類）欄", "飲料・食品用のアルミ缶", "中を洗う", "スプレー缶は有害・危険ごみ", "DIRECT_ITEM", "資源物の缶類を採用。"),
        "I006": ("C-M095-05", "S-M095-03", "資源物（びん類）欄", "飲料・食品用のガラスびん", "ふたを外して中を洗う", "割れたびん・耐熱ガラス等は燃えないごみ", "DIRECT_ITEM", "資源物のびん類を採用。"),
        "I031": ("C-M095-02", "S-M095-03", "燃えないごみ欄（電球・LED電球）", "白熱電球・LED電球", "割れないよう購入時の箱等に入れる", "蛍光管・電球形蛍光灯は有害・危険ごみ", "DIRECT_ITEM", "電球と蛍光管の区別を保持。"),
        "I029": ("C-M095-07", "S-M095-03", "有害・危険ごみ欄（小型充電式電池・モバイルバッテリー）", "小型充電式電池を内蔵するモバイルバッテリー", "端子を絶縁する", "膨張・破損品は他の物と分けて市の案内に従う", "DIRECT_ITEM", "有害・危険ごみの品目例を採用。"),
        "I014": ("C-M095-06", "S-M095-03", "資源物（紙類）欄（ダンボール）", "家庭から出るダンボール", "折りたたみ、ひもで十文字に縛る", "汚れ・におい・防水加工のある物は燃えるごみ", "DIRECT_ITEM", "紙類の具体的排出方法を採用。"),
        "I033": ("C-M095-07", "S-M095-03", "有害・危険ごみ欄（ライター）", "中身を使い切った使い捨てライター", "ガスを使い切り、他のごみと分ける", "中身が残る場合は市へ相談", "DIRECT_ITEM", "有害・危険ごみの品目例を採用。"),
        "I017": ("C-M095-06", "S-M095-03", "資源物（紙類）欄（紙パック）", "内側が白い紙パック", "洗い、切り開き、乾かして、ひもで縛る", "内側がアルミ加工の物は燃えるごみ", "DIRECT_ITEM", "紙パック固有の洗浄・展開条件を採用。"),
    },
    "M097": {
        "I001": ("C-M097-04", "S-M097-01", "ペットボトル欄", "PETマークのある飲料・調味料用ボトル", "キャップとラベルを外し、中を洗う", "対象外ボトルは容器包装プラスチック又はもやすごみ", "OFFICIAL_CATEGORY_RULE", "現行区分の対象条件を採用。"),
        "I007": ("C-M097-05", "S-M097-04", "「食品用トレイ」の行", "プラマークのある白色食品トレイ", "中身を除き、汚れを落とす", "汚れが取れない物はもやすごみ", "DIRECT_ITEM", "50音順一覧の品目行を採用。"),
        "I013": ("C-M097-01", "S-M097-04", "「新聞紙」の行", "家庭から出る新聞紙", "指定袋に入る大きさにまとめる", "地域の資源回収を利用できる場合は資源回収を優先", "DIRECT_ITEM", "市収集での分別先を採用。"),
        "I004": ("C-M097-03", "S-M097-01", "びん・飲料缶欄（アルミ缶）", "飲料用のアルミ缶", "中を洗う", "飲料缶以外の金属容器は不燃物", "DIRECT_ITEM", "現行区分名が飲料缶を明示。"),
        "I006": ("C-M097-03", "S-M097-01", "びん・飲料缶欄", "飲料・食品用のガラスびん", "ふたを外し、中を洗う", "割れたびん等は不燃物", "DIRECT_ITEM", "現行区分名がびんを明示。"),
        "I031": ("C-M097-09", "S-M097-06", "「電球」の行", "家庭用の電球", "割れないよう購入時の箱等に入れる", "LED電球等は一覧の材質・製品区分に従う", "DIRECT_ITEM", "50音順一覧の電球行を採用。"),
        "I029": ("C-M097-08", "S-M097-01", "電池の外せない小型家電・充電式小型家電欄", "充電池を内蔵し取り外せないモバイルバッテリー", "端子を絶縁し、他のごみと分ける", "取り外せる電池は電池区分へ", "OFFICIAL_CATEGORY_RULE", "充電式小型家電の公式区分定義を適用。"),
        "I014": ("C-M097-01", "S-M097-05", "「ダンボール」の行", "家庭から出るダンボール", "指定袋に入る大きさにする", "地域の資源回収を利用できる場合は資源回収を優先", "DIRECT_ITEM", "50音順一覧の品目行を採用。"),
        "I033": ("C-M097-06", "S-M097-01", "発火性危険ごみ欄（ライター）", "中身を使い切った使い捨てライター", "ガスを使い切り、他のごみと分ける", "中身が残る場合は市へ相談", "DIRECT_ITEM", "現行の発火性危険ごみ例を採用。"),
        "I017": ("C-M097-01", "S-M097-03", "「紙パック」「牛乳パック」の行", "家庭から出る紙パック", "中を洗い、開いて乾かす", "店頭・地域の資源回収を利用できる場合はそちらを優先", "DIRECT_ITEM", "50音順一覧の市収集区分を採用。"),
    },
    "M104": {
        "I001": ("C-M104-08", "S-M104-04", "ごみブック「ペットボトル」欄", "PETマークのある飲料・特定調味料用ボトル", "キャップとラベルを外し、中を洗う", "対象外のプラスチックボトルはリサイクルプラ又はその他プラ", "DIRECT_ITEM", "公式ごみブックの品目欄を採用。"),
        "I007": ("C-M104-09", "S-M104-04", "ごみブック「白色トレイ」欄", "プラマークのある白色食品トレイ", "中身を除き、洗って乾かす", "汚れが落ちない物は燃やせるごみ", "DIRECT_ITEM", "公式ごみブックの品目欄を採用。"),
        "I013": ("C-M104-05", "S-M104-04", "ごみブック「新聞」欄", "新聞・折込広告", "ひもで縛る", "汚れた紙は燃やせるごみ", "DIRECT_ITEM", "公式ごみブックの品目欄を採用。"),
        "I004": ("C-M104-07", "S-M104-04", "ごみブック「アルミ缶」欄", "飲料・食品用のアルミ缶", "中を洗う", "スプレー缶は有害ごみ", "DIRECT_ITEM", "公式ごみブックの品目欄を採用。"),
        "I006": ("C-M104-07", "S-M104-04", "ごみブック「ビン」欄", "飲料・食品用のガラスびん", "ふたを外し、中を洗う", "割れたびん・耐熱ガラス等は危険ごみ等の該当区分", "DIRECT_ITEM", "公式ごみブックの品目欄を採用。"),
        "I031": ("C-M104-10", "S-M104-04", "ごみブック「電球」欄", "家庭用の電球", "割れないよう箱等に入れる", "製品種別により危険ごみ又は有害ごみの案内に従う", "DIRECT_ITEM", "公式ごみブックの品目欄を採用。"),
        "I029": ("C-M104-10", "S-M104-05", "モバイルバッテリーの出し方欄", "家庭で使用したモバイルバッテリー", "端子をテープで絶縁する", "膨張・破損品は市の個別案内に従う", "DIRECT_ITEM", "小型充電式電池の専用公式案内を採用。"),
        "I014": ("C-M104-06", "S-M104-06", "ダンボールの出し方欄", "家庭から出るダンボール", "折りたたみ、ひもで縛る", "汚れた物は燃やせるごみ", "DIRECT_ITEM", "資源紙の専用公式案内を採用。"),
        "I033": ("C-M104-10", "S-M104-04", "ごみブック「ライター」欄", "中身を使い切った使い捨てライター", "ガスを使い切り、他のごみと分ける", "中身が残る場合は市へ相談", "DIRECT_ITEM", "公式ごみブックの品目欄を採用。"),
        "I017": ("C-M104-06", "S-M104-06", "雑誌・雑がみ・ダンボール欄（紙パックの例示）", "紙製容器包装として回収可能な紙パック", "中を洗い、開いて乾かす", "内側アルミ加工や汚れた物は燃やせるごみ", "OFFICIAL_CATEGORY_RULE", "紙資源の公式対象例と条件を適用。"),
    },
    "M105": {
        "I001": ("C-M105-04", "S-M105-02", "ペットボトルの行", "限定7品目に該当するPETマーク付きボトル", "キャップとラベルを外し、中を洗う", "対象外又は汚れが落ちない物は燃やせるごみ", "DIRECT_ITEM", "令和8年4月版一覧表の品目行を採用。"),
        "I007": ("C-M105-04", "S-M105-02", "白色トレイの行", "白色の発泡スチロール製食品トレイ", "中身を除き、洗って乾かす", "色柄・透明トレイや汚れた物は燃やせるごみ", "DIRECT_ITEM", "限定7品目の白色トレイ条件を採用。"),
        "I013": ("C-M105-05", "S-M105-02", "新聞の行", "新聞・折込広告", "種類別にまとめ、ひもで縛る", "汚れた紙・禁忌紙は燃やせるごみ", "DIRECT_ITEM", "令和8年4月版一覧表の品目行を採用。"),
        "I004": ("C-M105-03", "S-M105-02", "アルミ缶の行", "飲料・食品用のアルミ缶", "中を洗う", "スプレー缶は別の公式区分に従う", "DIRECT_ITEM", "令和8年4月版一覧表の品目行を採用。"),
        "I006": ("C-M105-03", "S-M105-02", "ガラスびんの行", "飲料・食品用のガラスびん", "ふたを外し、中を洗う", "割れたびん・耐熱ガラス等は埋立ごみ", "DIRECT_ITEM", "令和8年4月版一覧表の品目行を採用。"),
        "I031": ("C-M105-08", "S-M105-02", "電球の行", "白熱電球・LED電球", "割れないよう箱等に入れる", "蛍光管・電球形蛍光灯は有害ごみ", "DIRECT_ITEM", "製品種別による分岐を保持。"),
        "I029": ("C-M105-11", "S-M105-02", "モバイルバッテリーの行", "家庭用モバイルバッテリー", "端子をテープで絶縁する", "膨張・破損品は市の案内に従う", "DIRECT_ITEM", "令和8年4月版一覧表の品目行を採用。"),
        "I014": ("C-M105-05", "S-M105-02", "ダンボールの行", "家庭から出るダンボール", "折りたたみ、ひもで縛る", "汚れた物は燃やせるごみ", "DIRECT_ITEM", "令和8年4月版一覧表の品目行を採用。"),
        "I033": ("C-M105-08", "S-M105-02", "ライターの行", "中身を使い切った使い捨てライター", "ガスを使い切り、他のごみと分ける", "中身が残る場合は市へ相談", "DIRECT_ITEM", "令和8年4月版一覧表の品目行を採用。"),
        "I017": ("C-M105-05", "S-M105-02", "紙パックの行", "内側が白い紙パック", "洗い、開いて乾かし、ひもで縛る", "内側アルミ加工や汚れた物は燃やせるごみ", "DIRECT_ITEM", "令和8年4月版一覧表の品目行を採用。"),
    },
    "M106": {
        "I001": ("C-M106-06", "S-M106-01", "ペットボトル欄", "PETマークのある飲料・特定調味料用ボトル", "キャップとラベルを外し、中を洗う", "汚れが落ちない物は燃えるごみ", "DIRECT_ITEM", "公式家庭ごみページの品目欄を採用。"),
        "I007": ("C-M106-05", "S-M106-01", "プラスチック製容器包装欄（食品トレイ）", "プラマークのある白色食品トレイ", "中身を除き、洗って乾かす", "汚れが落ちない物は燃えるごみ", "OFFICIAL_CATEGORY_RULE", "公式対象例と共通条件を適用。"),
        "I013": ("C-M106-02", "S-M106-01", "古紙類欄（新聞）", "新聞・折込広告", "種類別にまとめ、ひもで縛る", "汚れた紙・禁忌紙は燃えるごみ", "DIRECT_ITEM", "公式家庭ごみページの品目欄を採用。"),
        "I004": ("C-M106-08", "S-M106-01", "かん類欄", "飲料・食品用のアルミ缶", "中を洗う", "スプレー缶は有害ごみ", "DIRECT_ITEM", "公式家庭ごみページの品目欄を採用。"),
        "I006": ("C-M106-09", "S-M106-01", "びん類欄", "飲料・食品用のガラスびん", "ふたを外し、中を洗う", "割れたびん等は陶器・ガラス類", "DIRECT_ITEM", "公式家庭ごみページの品目欄を採用。"),
        "I031": ("C-M106-12", "S-M106-01", "有害ごみ欄（電球）", "家庭用電球", "割れないよう箱等に入れる", "製品種別により燃えないごみ又は有害ごみの案内に従う", "DIRECT_ITEM", "公式家庭ごみページの品目欄を採用。"),
        "I029": ("C-M106-12", "S-M106-01", "有害ごみ欄（小型充電式電池）", "小型充電式電池を内蔵するモバイルバッテリー", "端子をテープで絶縁する", "膨張・破損品は市へ相談", "OFFICIAL_CATEGORY_RULE", "小型充電式電池の公式ルールを適用。"),
        "I014": ("C-M106-02", "S-M106-01", "古紙類欄（ダンボール）", "家庭から出るダンボール", "折りたたみ、ひもで縛る", "汚れた物は燃えるごみ", "DIRECT_ITEM", "公式家庭ごみページの品目欄を採用。"),
        "I033": ("C-M106-10", "S-M106-01", "小型家電、電源コード、金物など欄（ライター）", "中身を使い切った使い捨てライター", "ガスを使い切り、他のごみと分ける", "中身が残る場合は市へ相談", "DIRECT_ITEM", "公式家庭ごみページの品目欄を採用。"),
        "I017": ("C-M106-04", "S-M106-01", "紙パック欄", "内側が白い紙パック", "洗い、開いて乾かす", "内側アルミ加工や汚れた物は燃えるごみ", "DIRECT_ITEM", "公式家庭ごみページの専用区分を採用。"),
    },
    "M107": {
        "I001": ("C-M107-07", "S-M107-01", "資源ごみ（ペットボトル）欄", "PETマークのある飲料・特定調味料用ボトル", "キャップとラベルを外し、中を洗う", "汚れが落ちない物は燃えるごみ", "DIRECT_ITEM", "令和8年度改定版の区分欄を採用。"),
        "I007": ("C-M107-01", "S-M107-01", "燃えるごみ欄（プラスチック類）", "白色食品トレイを含む家庭のプラスチック類", "中身を除き、汚れを落とす", "店頭回収を利用する場合は回収先の条件に従う", "OFFICIAL_CATEGORY_RULE", "市のプラスチック類収集ルールを適用。"),
        "I013": ("C-M107-06", "S-M107-01", "資源ごみ（古紙・布類）欄（新聞）", "新聞・折込広告", "種類別にまとめ、ひもで縛る", "汚れた紙・禁忌紙は燃えるごみ", "DIRECT_ITEM", "令和8年度改定版の区分欄を採用。"),
        "I004": ("C-M107-05", "S-M107-01", "資源ごみ（びん・缶）欄", "飲料・食品用のアルミ缶", "中を洗う", "スプレー缶は有害・危険ごみ", "DIRECT_ITEM", "令和8年度改定版の区分欄を採用。"),
        "I006": ("C-M107-05", "S-M107-01", "資源ごみ（びん・缶）欄", "飲料・食品用のガラスびん", "ふたを外し、中を洗う", "割れたびん等は燃えないごみ", "DIRECT_ITEM", "令和8年度改定版の区分欄を採用。"),
        "I029": ("C-M107-08", "S-M107-01", "有害・危険ごみ欄（モバイルバッテリー）", "家庭用モバイルバッテリー", "端子をテープで絶縁する", "膨張・破損品は市へ相談", "DIRECT_ITEM", "令和8年度改定版の品目例を採用。"),
        "I014": ("C-M107-06", "S-M107-01", "資源ごみ（古紙・布類）欄（ダンボール）", "家庭から出るダンボール", "折りたたみ、ひもで縛る", "汚れた物は燃えるごみ", "DIRECT_ITEM", "令和8年度改定版の区分欄を採用。"),
        "I017": ("C-M107-06", "S-M107-01", "資源ごみ（古紙・布類）欄（紙パック）", "内側が白い紙パック", "洗い、開いて乾かす", "内側アルミ加工や汚れた物は燃えるごみ", "DIRECT_ITEM", "令和8年度改定版の品目例を採用。"),
    },
    "M109": {
        "I001": ("C-M109-07", "S-M109-01", "1頁 資源物「ペットボトル」欄", "PETマークのある飲料・特定調味料用ボトル", "中を洗い、キャップとラベルを外す", "汚れが落ちない物は可燃ごみ", "DIRECT_ITEM", "令和8年度公式PDFの専用子区分を採用。"),
        "I007": ("C-M109-08", "S-M109-01", "1頁 資源物「その他」白色トレイ欄", "白色の食品トレイ", "洗って乾かす", "白色以外又は汚れた物は可燃ごみ", "DIRECT_ITEM", "令和8年度公式PDFの品目例を採用。"),
        "I013": ("C-M109-06", "S-M109-01", "1頁 資源物「紙・布類」新聞欄", "新聞・折込広告", "種類別にまとめ、ひもで縛る", "汚れた紙・禁忌紙は可燃ごみ", "DIRECT_ITEM", "令和8年度公式PDFの品目例を採用。"),
        "I004": ("C-M109-04", "S-M109-01", "1頁 資源物「缶・金属類」欄", "飲料・食品用のアルミ缶", "中を洗う", "スプレー缶は穴を開けず同欄の個別条件に従う", "DIRECT_ITEM", "令和8年度公式PDFの子区分を採用。"),
        "I006": ("C-M109-05", "S-M109-01", "1頁 資源物「ビン類」欄", "飲料・食品用のガラスびん", "ふたを外し、中を洗う", "割れたびん等は埋立ごみ", "DIRECT_ITEM", "令和8年度公式PDFの子区分を採用。"),
        "I029": ("C-M109-09", "S-M109-03", "モバイルバッテリー・小型充電式電池欄", "家庭用モバイルバッテリー", "端子をテープで絶縁する", "膨張・破損品は町へ相談", "DIRECT_ITEM", "町の専用公式案内を採用。"),
        "I014": ("C-M109-06", "S-M109-01", "1頁 資源物「紙・布類」ダンボール欄", "家庭から出るダンボール", "折りたたみ、種類別にまとめる", "汚れた物は可燃ごみ", "DIRECT_ITEM", "令和8年度公式PDFの品目例を採用。"),
        "I017": ("C-M109-06", "S-M109-01", "1頁 資源物「紙・布類」紙パック欄", "内側が白い紙パック", "洗い、開いて乾かす", "内側アルミ加工や汚れた物は可燃ごみ", "DIRECT_ITEM", "令和8年度公式PDFの品目例を採用。"),
    },
}

UNRESOLVED = {
    ("M107", "I031"): "令和8年度版資料で『電球』の品目単位の分別先を確証できない。蛍光管の記載から推測しない。",
    ("M107", "I033"): "令和8年度版資料で『使い捨てライター』の品目単位の分別先を確証できない。危険物一般から推測しない。",
    ("M109", "I031"): "令和8年度版資料で『電球』の品目単位の分別先を確証できない。蛍光管の記載から推測しない。",
    ("M109", "I033"): "令和8年度版資料で『使い捨てライター』の品目単位の分別先を確証できない。危険物一般から推測しない。",
}


def load_rows(path: Path) -> list[dict[str, str]]:
    return read_csv(path)[1]


def main() -> None:
    municipality_rows = load_rows(RESEARCH / "04_municipalities_research.csv")
    item_rows = load_rows(ROOT / "data" / "master" / "04_common_items_master.csv")
    asset_rows = load_rows(APP / "item_image_assets.csv")
    category_rows = load_rows(RESEARCH / "02_categories_master.csv")
    source_rows = load_rows(RESEARCH / "03_sources_master.csv")
    mapping_rows = load_rows(RESEARCH / "05_item_mapping_master.csv")
    coverage_rows = load_rows(RESEARCH / "07_item_mapping_coverage.csv")

    municipalities = {r["municipality_id"]: r for r in municipality_rows}
    items = {r["internal_item_id"]: r for r in item_rows}
    assets = {r["internal_item_id"]: r for r in asset_rows}
    categories = {(r["municipality_id"], r["category_id"]): r for r in category_rows}

    source_by_key = {(r["municipality_id"], r["source_id"]): r for r in source_rows}
    for row in NEW_SOURCES:
        source_by_key[(row["municipality_id"], row["source_id"])] = row
    source_rows = sorted(source_by_key.values(), key=lambda r: (r["municipality_id"], r["source_id"]))
    source_by_key = {(r["municipality_id"], r["source_id"]): r for r in source_rows}

    map_by_pair: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in mapping_rows:
        map_by_pair.setdefault((row["municipality_id"], row["internal_item_id"]), []).append(row)
    coverage_by_pair = {(r["municipality_id"], r["internal_item_id"]): r for r in coverage_rows}

    pilot_rows: list[dict[str, str]] = []
    order = 0
    verified = 0
    for mid in TARGETS:
        for iid in ITEMS:
            order += 1
            item = items[iid]
            base = {
                "pair_order": str(order),
                "municipality_id": mid,
                "municipality_name": municipalities[mid]["市町村"],
                "internal_item_id": iid,
                "canonical_name": item["一般管理用名称"],
                "display_name": item["教材表示名"],
                "checked_date": CHECKED,
                "reviewer": REVIEWER,
            }
            if (mid, iid) in UNRESOLVED:
                pilot_rows.append({
                    **base, "review_status": "UNRESOLVED", "evidence_basis": "UNRESOLVED",
                    "category_id": "", "category_name": "", "condition": "",
                    "preparation": "", "exception_destination": "",
                    "item_evidence_source_id": "", "item_evidence_url": "",
                    "item_evidence_locator": "", "note": UNRESOLVED[(mid, iid)],
                })
                continue

            category_id, source_id, locator, condition, preparation, exception, basis, note = R[mid][iid]
            supplemental_id = "I" + source_id
            if (mid, supplemental_id) in source_by_key:
                source_id = supplemental_id
            category = categories[(mid, category_id)]
            evidence_source = source_by_key[(mid, source_id)]
            pilot_rows.append({
                **base, "review_status": "VERIFIED", "evidence_basis": basis,
                "category_id": category_id, "category_name": category["自治体正式名称"],
                "condition": condition, "preparation": preparation,
                "exception_destination": exception,
                "item_evidence_source_id": source_id,
                "item_evidence_url": evidence_source["公式URL"],
                "item_evidence_locator": locator, "note": note,
            })

            pair = (mid, iid)
            branches = map_by_pair.get(pair, [])
            matching = [b for b in branches if b["category_id"] == category_id]
            if matching:
                branch = matching[0]
                # The pilot establishes one reviewed branch for these pairs.  Any
                # stale auto-generated alternatives remain outside APP_READY but
                # are not expected in the current canonical data.
            else:
                branch = {field: "" for field in MAPPING_FIELDS}
                branch.update({
                    "mapping_id": f"MAP-{mid}-{iid}-PILOT-01",
                    "municipality_id": mid,
                    "internal_item_id": iid,
                    "branch_order": str(len(branches) + 1),
                })
                mapping_rows.append(branch)
                branches.append(branch)
                map_by_pair[pair] = branches

            category_source = source_by_key[(mid, category["source_id"])]
            branch.update({
                "自治体での品目表記": item["一般管理用名称"],
                "category_id": category_id,
                "分別区分正式名称": category["自治体正式名称"],
                "条件": condition,
                "前処理": preparation,
                "例外分別先": exception,
                "自治体収集外": category["自治体収集外か"],
                "rule_status": category["rule_status"],
                "effective_from": category["effective_from"],
                "effective_to": category["effective_to"],
                "category_source_id": category["source_id"],
                "category_source_url": category["出典URL"],
                "category_source_locator": category["出典ページ・該当箇所"],
                "item_evidence_source_id": source_id,
                "item_evidence_url": evidence_source["公式URL"],
                "item_evidence_locator": locator,
                "確認日": CHECKED,
                "mapping_status": "VERIFIED",
                "evidence_scope": "ITEM_SPECIFIC",
                "branch_review_status": "INCOMPLETE",
                "reviewed_date": CHECKED,
                "reviewed_by": REVIEWER,
                "備考": f"画像品目mapping Pilot。{basis}。APP_READY未昇格。",
            })

            coverage = coverage_by_pair[pair]
            coverage.update({
                "coverage_status": "VERIFIED",
                "mapping_branch_count": str(len(branches)),
                "branch_completeness_confirmed": "FALSE",
                "evidence_scope": "ITEM_SPECIFIC",
                "item_evidence_source_id": source_id,
                "item_evidence_url": evidence_source["公式URL"],
                "item_evidence_locator": locator,
                "reviewed_date": CHECKED,
                "reviewed_by": REVIEWER,
                "notes": "画像品目mapping Pilotで公式根拠を確認。条件枝完全性は未確定。",
            })
            verified += 1

    assert order == 80
    assert verified == 76
    assert all(iid in assets and assets[iid]["asset_status"] == "CONFIRMED" for iid in ITEMS)
    assert not ({"M098", "M099"} & set(R))

    mapping_rows.sort(key=lambda r: (r["municipality_id"], r["internal_item_id"], int(r.get("branch_order") or 0), r["mapping_id"]))
    coverage_rows.sort(key=lambda r: (r["municipality_id"], r["internal_item_id"]))
    write_csv(RESEARCH / "03_sources_master.csv", SOURCE_FIELDS, source_rows)
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mapping_rows)
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", COVERAGE_FIELDS, coverage_rows)
    write_csv(APP / "item_image_mapping_pilot_top8.csv", PILOT_FIELDS, pilot_rows)

    print("Item image mapping pilot written: 80 pairs (76 VERIFIED, 4 UNRESOLVED, 0 APP_READY)")


if __name__ == "__main__":
    main()
