#!/usr/bin/env python3
"""Build Batch 11 from current resident-facing official sources.

Targets: M106-M115 (remaining Hiroshima municipalities before M116).
All targets remain active in this batch. Regional schedule differences are not
used as category differences unless the resident-facing taxonomy itself differs.
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
OUT = ROOT / "data" / "research" / "batches" / "batch_11"
CHECKED = "2026-08-19"
M106_PREFLIGHT_CHECKED = "2026-08-26"
REVIEWER = "OPENAI_CHATGPT_BATCH11_REVIEW"
NS = "NOT_STATED_IN_CITED_SOURCE"
TARGETS = {f"M{i:03d}" for i in range(106, 116)}
REGISTRY_FIELDS = ["municipality_id","host","authority_type","authority_name","verification_url","verified_date","notes"]

municipality_specs = {
    "M106": dict(pref="広島県", city="安芸高田市", processor="芸北広域環境施設組合", top="https://www.akitakata.jp/ja/shisei/section/siminseikatu/gomi22/", guide="https://www.akitakata.jp/ja/shisei/section/siminseikatu/gomi22/", note="現行公式ページの住民向け区分を採用。容器包装類と燃えないごみは『分類ごとに袋を分ける』ため公式子葉を保持。モバイルバッテリーの直接案内は非BOX経路として保持。"),
    "M107": dict(pref="広島県", city="江田島市", processor="江田島市", top="https://www.city.etajima.hiroshima.jp/cms/articles/show/11923", guide="https://www.city.etajima.hiroshima.jp/cms/articles/download/11923/1/R8_nihonngo.pdf", note="令和8年度改定ポスターを採用。古紙・布類は現行ポスターで一つの資源ごみ区分として扱う。"),
    "M108": dict(pref="広島県", city="府中町", processor="府中町", top="https://www.town.fuchu.hiroshima.jp/site/kankyousenta/34617.html", guide="https://www.town.fuchu.hiroshima.jp/uploaded/attachment/31359.pdf", note="令和8年度ごみの正しい出し方を採用。有価物は品目ごとに分けて順番に収集するため4公式子葉を保持。"),
    "M109": dict(pref="広島県", city="海田町", processor="海田町", top="https://www.town.kaita.lg.jp/soshiki/10/135455.html", guide="https://www.town.kaita.lg.jp/uploaded/life/44980_122640_misc.pdf", note="令和8年度家庭ごみの正しい出し方を採用。資源物内の5住民区分を公式子葉として保持。"),
    "M110": dict(pref="広島県", city="熊野町", processor="熊野町", top="https://www.town.kumano.lg.jp/8/1/3/2/3569.html", guide="https://www.town.kumano.lg.jp/8/1/3/2/3569.html", note="令和8年度の現行6区分を保持。資源物(1)(2)内部の小分類を人工的な独立categoryへ増やさない。"),
    "M111": dict(pref="広島県", city="坂町", processor="坂町", top="https://www.town.saka.lg.jp/2014/04/01/gomi_dashikata/", guide="https://www.town.saka.lg.jp/2014/04/01/gomi_dashikata/", note="令和8年度現行ページを採用。資源ごみは住民が8品目に分けて出すため公式子葉を保持。"),
    "M112": dict(pref="広島県", city="安芸太田町", processor="安芸太田町／ポックルくろだおクリーンセンター", top="https://www.akiota.jp/soshiki/13/2397.html", guide="https://www.akiota.jp/uploaded/attachment/9505.pdf", note="令和8年版家庭ごみ分別五十音事典を採用。資源・燃えない・プラスチックは区分ごとに分けるため12公式葉を保持。"),
    "M113": dict(pref="広島県", city="北広島町", processor="芸北広域環境施設組合", top="https://www.town.kitahiroshima.lg.jp/soshiki/14/17696.html", guide="https://www.town.kitahiroshima.lg.jp/uploaded/attachment/23637.pdf", note="町公式が芸北広域環境施設組合の収集を明示し、令和8年度の分け方・出し方一覧表を現行資料として案内。"),
    "M114": dict(pref="広島県", city="大崎上島町", processor="大崎上島町", top="https://www.town.osakikamijima.hiroshima.jp/soshiki/joge_suido/1_1/1/1133.html", guide="https://www.town.osakikamijima.hiroshima.jp/soshiki/joge_suido/1_1/1/1133.html", note="令和8年4月の変更後ルールを採用。公式6上位分類のうち不燃・資源は住民向け2子葉ずつを保持。"),
    "M115": dict(pref="広島県", city="世羅町", processor="世羅町", top="https://www.town.sera.hiroshima.jp/soshiki/4/317.html", guide="https://www.town.sera.hiroshima.jp/soshiki/4/317.html", note="令和8年度現行ページを採用。不燃ごみは『それぞれ別々の袋』の5公式子葉を保持。地域差は日程のみ。"),
}

# title, kind, url, updated, used, issuer
source_specs = {
    "M106": [
        ("家庭ごみの出し方", "自治体公式Webページ", municipality_specs["M106"]["top"], "2025-11-06", "燃える・古紙・容器包装・燃えない・有害・粗大と、分類ごとに袋を分ける子区分・前処理", "安芸高田市"),
        ("リチウムイオン電池からの火災に注意！！", "自治体公式Webページ", "https://www.akitakata.jp/ja/shisei/section/119/m148-copy-5/", "2025-08-07", "モバイルバッテリーを一般ごみ・小型家電回収ボックスへ出せないことと販売店等の引取経路", "安芸高田市"),
    ],
    "M107": [
        ("家庭ごみの種類と正しい出し方（令和8年度改定版）", "自治体公式PDF", municipality_specs["M107"]["guide"], "2026-04-30", "令和8年度の現行8住民区分、代表品目、資源ごみ3系統", "江田島市"),
        ("スプレー缶のごみ出しについて", "自治体公式Webページ", "https://www.city.etajima.hiroshima.jp/cms/articles/show/11608", "2026-01-05", "有害・危険ごみ。使い切り必須、穴を開けずに出す場合の表示方法", "江田島市"),
        ("『家庭ごみの種類と正しい出し方』ポスターをご利用ください", "自治体公式Webページ", municipality_specs["M107"]["top"], "2026-04-30", "令和8年度改定版が現行であること、5言語版の公開", "江田島市"),
    ],
    "M108": [
        ("令和8年度 ごみの正しい出し方", "自治体公式PDF", municipality_specs["M108"]["guide"], "令和8年度", "普通ごみ・有価物4子葉・埋立・有害・PET・紙パック・白色トレイ・大型ごみ", "府中町"),
        ("令和8年度 ごみの正しい出し方", "自治体公式Webページ", municipality_specs["M108"]["top"], "2026-03-01", "令和8年度版が現行であること", "府中町"),
    ],
    "M109": [
        ("令和8年度 家庭ごみの正しい出し方", "自治体公式PDF", municipality_specs["M109"]["guide"], "令和8年度", "可燃・埋立・資源物5子葉・有害・大型ごみと前処理", "海田町"),
        ("令和8年度 家庭ごみの正しい出し方", "自治体公式Webページ", municipality_specs["M109"]["top"], "2026-03-12", "令和8年度日本語版と外国語版が現行であること", "海田町"),
    ],
    "M110": [
        ("熊野町 ごみの正しい出し方", "自治体公式Webページ", municipality_specs["M110"]["top"], "2026-07-01", "可燃・資源物(1)・資源物(2)・埋立・有害・大型の現行6区分", "熊野町"),
        ("資源物（1）", "自治体公式Webページ", "https://www.town.kumano.lg.jp/8/1/3/2/1/3572.html", "2026-03-31", "紙・衣類・PET・プラ容器包装の内部小分類と前処理", "熊野町"),
    ],
    "M111": [("ごみの出し方", "自治体公式Webページ", municipality_specs["M111"]["top"], "2026-03-27", "もやせる・粗大2種・埋立・有害・資源8子葉と前処理", "坂町")],
    "M112": [
        ("ごみ（一般廃棄物）の分別収集と処理について", "自治体公式Webページ", municipality_specs["M112"]["top"], "2026-06-22", "現行の上位分別体系と令和8年版資料への公式導線", "安芸太田町"),
        ("令和8年版 安芸太田町 家庭ごみ分別五十音事典", "自治体公式PDF", municipality_specs["M112"]["guide"], "令和8年版", "12住民区分、区分ごとの指定袋、前処理・穴あけ不要ルール", "安芸太田町"),
    ],
    "M113": [
        ("家庭ごみの分け方・出し方", "自治体公式Webページ", municipality_specs["M113"]["top"], "2026-04-13", "芸北広域環境施設組合が収集主体であること、令和8年度資料・分別アプリへの現行導線", "北広島町"),
        ("ごみの分け方出し方一覧表", "自治体公式PDF", municipality_specs["M113"]["guide"], "令和8年度案内中", "芸北広域の住民向け分別体系と子区分", "北広島町"),
    ],
    "M114": [("家庭ごみの分け方・出し方", "自治体公式Webページ", municipality_specs["M114"]["top"], "2026-04-01", "令和8年4月変更後の6上位分類と不燃・資源の住民向け子区分", "大崎上島町")],
    "M115": [("ごみの分け方・出し方", "自治体公式Webページ", municipality_specs["M115"]["top"], "2026-04-01", "可燃・容器包装プラ・びん缶・PET・不燃5子葉の現行住民区分と前処理", "世羅町")],
}

categories: list[dict[str, str]] = []

def add(mid: str, name: str, rep: str, *, source: int = 1, parent: str = "", ui: str = "SORT_BUCKET",
        level: str = "PRIMARY", channel: str = "CURBSIDE", forbidden: str = NS, cond: str = "", fallback: str = NS,
        prep: str = NS, bag: str = "", size: str = "", bulky: str = "FALSE", note: str = "",
        excluded: str = "FALSE", reservation: str | None = None, paid: str = "FALSE",
        checked: str = CHECKED) -> None:
    categories.append({
        "municipality_id": mid, "自治体正式名称": name, "category_group": parent or name, "parent_name": parent,
        "classification_level": level, "collection_channel": channel, "代表品目": rep, "入れてはいけない物": forbidden,
        "適用条件": cond, "条件外の扱い": fallback, "出す前の処理": prep, "袋・容器のルール": bag,
        "サイズ・条件": size, "粗大ごみ扱いか": bulky,
        "予約が必要か": reservation if reservation is not None else ("TRUE" if channel == "BOOKED_PICKUP" else "FALSE"),
        "有料か": paid, "料金ルール": "", "自治体収集外か": excluded, "注意事項": note,
        "source_index": str(source), "出典ページ・該当箇所": name, "ui_role": ui, "rule_status": "CURRENT",
        "effective_from": "", "effective_to": "", "確認日": checked,
    })

# M106 安芸高田市 — two projection parents, 11 official resident leaves.
add("M106", "燃えるごみ", "生ごみ・古着・布・紙くず・木の枝等", prep="生ごみは水切り。ロープ・木の枝等は50cm以下。液体は吸わせるか固形化。重さ10kg以下")
add("M106", "古紙類", "新聞・ダンボール・雑誌・ざつ紙等", prep="長さ50cm・10kg以下。紙種別に分け、ひもで十文字にくくり処理券を貼る")
add("M106", "容器包装類", "紙パック・プラスチック製容器包装・ペットボトル")
add("M106", "紙パック", "紙パックマークのあるもの", parent="容器包装類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中を洗い、開いて乾かす。内側アルミ箔は燃えるごみ")
add("M106", "プラスチック製容器包装", "プラマークのある容器包装", parent="容器包装類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="汚れを拭き取るか洗う。落ちないものは燃えるごみ")
add("M106", "ペットボトル", "PETマークの飲料・酒・しょうゆ等", parent="容器包装類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中を水洗いし、キャップ・ラベルを外してプラスチック製容器包装へ")
add("M106", "燃えないごみ", "かん・びん・小型家電・金物・陶器・ガラス")
add("M106", "かん類", "飲料缶・食品缶・スプレー缶等", parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中を洗う。スプレー缶・カセットボンベは使い切る。穴あけ不要。重さ10kg以下")
add("M106", "びん類", "飲食用・化粧品・薬品びん等", parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中を洗い、ふた・キャップを外す。重さ10kg以下")
add("M106", "小型家電、電源コード、金物など", "なべ・フライパン・小型家電・電源コード等", parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="電源コードを器具から切り取って束ねる。釘・かみそり等は紙で包む。袋に入らない物は粗大ごみ")
add("M106", "陶器 ガラス類", "食器・茶碗・皿・植木鉢・ガラス等", parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="破片・かけらは袋が破れないよう紙などに包む。重さ10kg以下")
add("M106", "有害ごみ", "乾電池・蛍光管・電球・水銀式体温計・ボタン電池・小型充電式電池", prep="蛍光管は壊さず10本以内にくくり指定袋を付ける。乾電池は指定袋に入れ口を固くしばる")
add("M106", "粗大ごみ", "家具・寝具・自転車・ストーブ・カーペット等", ui="REFERENCE_ONLY", bulky="TRUE", prep="粗大ごみ処理券を使用。ストーブ等は燃料を抜く。電源コードは器具から切り取る")
add(
    "M106", "販売店やリサイクル業者に引き取ってもらう",
    "モバイルバッテリー・リチウムイオン電池・ニッカド電池",
    source=2, ui="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED",
    forbidden="一般ごみ・小型家電回収ボックス", cond="家庭から廃棄する対象電池",
    fallback="市の通常収集区分へ出さない", prep="購入した販売店等へ引取を依頼する",
    bag="市指定袋・小型家電回収ボックスへ入れない", excluded="TRUE", paid="CONDITIONAL",
    note="火災防止のため一般ごみ及び小型家電回収ボックスでは回収不可",
    checked=M106_PREFLIGHT_CHECKED,
)

# M107 江田島市 — 2026 poster combines old-paper and cloth resources: 8 current leaves.
add("M107", "燃えるごみ", "生ごみ・木くず・再生できない紙類・布類・プラスチック類等", source=1, prep="生ごみは水切り。枝木等は現行ポスターの寸法条件に従う")
add("M107", "燃えないごみ（埋立てるごみ）", "陶磁器類・土砂類・ガラス類・植木鉢等", source=1, prep=NS)
add("M107", "燃える粗大ごみ", "家具類・寝具類・家庭電器製品・小型家電等", source=1, ui="REFERENCE_ONLY", bulky="TRUE", prep="コード等の市指定前処理を行う")
add("M107", "燃えない粗大ごみ", "自転車類・金属製品類・ガステーブル・ストーブ等", source=1, ui="REFERENCE_ONLY", bulky="TRUE", prep="ストーブ等は燃料を完全に抜く")
add("M107", "資源ごみ（びん・缶）", "飲食用びん・缶等", source=1, prep="中身を空にする")
add("M107", "資源ごみ（古紙・布類）", "古紙・衣類等", source=1, prep="古紙は種類別にまとめる")
add("M107", "資源ごみ（ペットボトル）", "PETマークのペットボトル", source=1, prep="中を洗い、ふた・ラベルを外す")
add("M107", "有害・危険ごみ", "乾電池・モバイルバッテリー・蛍光管・水銀製品・スプレー缶等", source=2, prep="スプレー缶は中身を使い切る。穴を開けずに出す場合は袋に入れ、穴を開けていない旨を表示する")

# M108 府中町 — 有価物 is a projection parent with four separately collected leaves.
add("M108", "普通ごみ", "台所ごみ・紙くず・木くず・革・ゴム・プラスチック等", prep="生ごみは水切り。指定寸法を超える物は大型ごみ")
add("M108", "有価物", "新聞・雑誌・雑がみ・ダンボール・衣類・ビン・缶等")
add("M108", "新聞・雑誌・雑がみ", "新聞・雑誌・雑がみ", parent="有価物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="紙類は種類に応じてひもでしばる")
add("M108", "ダンボール", "ダンボール", parent="有価物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="たたんでひもでしばる")
add("M108", "衣類", "衣類", parent="有価物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="透明または半透明の袋で出し、雨天時は避ける")
add("M108", "ビン・缶", "飲食用びん・缶・小型金属等", parent="有価物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中身を空にし、びんのふたを外す。スプレー缶・カセットボンベは中身を使い切る")
add("M108", "埋立ごみ", "陶磁器・ガラス・土砂等", prep="割れたガラス等は安全に包み内容を表示する")
add("M108", "有害ごみ", "乾電池・充電式電池・蛍光管・充電池を外せない小型家電等", prep="電池の電極をテープで絶縁。蛍光管と電池類は別袋で出す")
add("M108", "ペットボトル", "PETマークのペットボトル", prep="キャップ・ラベルを外す。汚れが落ちないものは普通ごみ")
add("M108", "紙パック", "牛乳等の紙パック", prep="ストロー等を外す。アルミ箔付きは普通ごみ")
add("M108", "白色トレイ", "白色食品トレイ", prep="汚れを落とす")
add("M108", "大型ごみ", "30cmを超える等の大型家庭ごみ", ui="REFERENCE_ONLY", bulky="TRUE", prep=NS)

# M109 海田町 — 資源物 projection parent with five official resident leaves.
add("M109", "可燃ごみ", "生ごみ・紙くず・木くず・革・ゴム・プラスチック等", prep="透明・半透明袋で口をしばる。生ごみは水切り")
add("M109", "埋立ごみ", "陶磁器・ガラス・土砂等", prep="透明・半透明袋で出し、袋の口は閉じない")
add("M109", "資源物", "缶・金属・びん・紙・布・ペットボトル・その他")
add("M109", "缶・金属類", "飲食用缶・小型金属・スプレー缶等", parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中を洗う。スプレー缶は使い切り、穴を開けない")
add("M109", "ビン類", "飲食用びん等", parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ふた等を外し、中を洗う")
add("M109", "紙・布類", "新聞・ダンボール・雑誌・紙パック・衣類等", parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="紙は種類別にまとめ、衣類は透明・半透明袋で出す")
add("M109", "ペットボトル", "PETマークのボトル", parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中を洗い、キャップ・ラベルを外す")
add("M109", "その他", "白色トレイ", parent="資源物", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="白色トレイのみ。洗って出す")
add("M109", "有害ごみ", "乾電池・充電式電池・蛍光管等", prep="充電式電池等は電極をテープで絶縁")
add("M109", "大型ごみ", "おおむね50cm以上の大型家庭ごみ", ui="REFERENCE_ONLY", bulky="TRUE", prep="燃料・電池等を除く")

# M110 熊野町 — exact six current collection labels; internal small classifications are not promoted.
add("M110", "可燃ごみ", "生ごみ・可燃性家庭ごみ", prep="生ごみは水切り。透明袋等の現行指定方法で出す")
add("M110", "資源物（1）", "紙類・衣類・ペットボトル・プラスチック製容器包装", source=2, prep="紙類は小分類ごとにひもでしばる。PETとプラ容器包装は別々の透明袋。PETはキャップ・ラベルを外し洗って乾かす")
add("M110", "資源物（2）", "びん・飲料缶・金属類", prep=NS)
add("M110", "埋立ごみ", "陶磁器・ガラス等", prep="危険物は安全に包む")
add("M110", "有害ごみ", "乾電池・蛍光管・水銀製品等", prep="小分類ごとに分け、蛍光管は破損を防ぐ")
add("M110", "大型ごみ", "大型家庭ごみ", ui="REFERENCE_ONLY", bulky="TRUE", prep="電池・燃料等を外す")

# M111 坂町 — 資源ごみ projection parent with eight resident leaves.
add("M111", "もやせるごみ", "生ごみ・紙くず・可燃性家庭ごみ", prep="生ごみは水切り。透明・半透明袋で出す")
add("M111", "もえる粗大ごみ", "大型木製品・布団等", ui="REFERENCE_ONLY", bulky="TRUE", prep="金属類を可能な範囲で外す")
add("M111", "もえない粗大ごみ", "大型金属・家電・自転車等", ui="REFERENCE_ONLY", bulky="TRUE", prep="ストーブ等は燃料を抜く。刃物類は包む")
add("M111", "埋立ごみ", "陶磁器・ガラス・耐熱ガラス等", prep="割れ物等は安全に包む")
add("M111", "有害ごみ", "乾電池・蛍光管・水銀体温計等", prep=NS)
add("M111", "資源ごみ", "缶・びん・紙・牛乳パック・ダンボール・衣類・PET・白色トレイ")
add("M111", "缶類", "アルミ缶・スチール缶・スプレー缶等", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中を洗う。スプレー缶は中身を使い切り、穴を開ける")
add("M111", "びん類", "飲食用びん等", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ふたを外し中を洗い、指定色等に分ける")
add("M111", "紙類", "新聞・雑誌・雑がみ等", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="新聞とその他の紙を分け、ひもでしばる")
add("M111", "牛乳パック", "牛乳等の紙パック", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="洗い、開いて乾かす")
add("M111", "ダンボール", "ダンボール", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="たたんでひもでしばる")
add("M111", "衣類", "古着等", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="透明・半透明袋で出す")
add("M111", "ペットボトル", "飲料用PETボトル", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ふたを外して洗う。ラベルは外さなくてもよい")
add("M111", "白色トレイ", "白色食品トレイ", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="洗って乾かす。白色のみ")

# M112 安芸太田町 — 12 resident leaves under three projection parents plus burnable/bulky.
add("M112", "燃えるごみ", "生ごみ・紙くず・木竹製品等", source=2, prep="水切りする。木・竹製品は原則30cm以下。指定袋1袋10kg未満")
add("M112", "資源ごみ", "缶・ビン・古紙類・衣類・布類", source=2)
add("M112", "缶", "飲食用缶・スプレー缶等", source=2, parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="缶はつぶさない。スプレー缶は使い切り、穴あけ不要")
add("M112", "ビン", "飲食用びん等", source=2, parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="びんは割らず、内容物・付着物を除き洗う")
add("M112", "古紙類", "新聞・雑誌・ダンボール・はがき等", source=2, parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ひもでくくって資源ごみ指定袋を付けるか、指定袋へ入れる")
add("M112", "衣類・布類", "衣類・カーテン・ぬいぐるみ等", source=2, parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="カーテン等の金属は外して金属類へ")
add("M112", "燃えないごみ", "金属・小型電化製品・有害物・陶器・ガラス・その他不燃物", source=2)
add("M112", "金属類", "鍋・フライパン・刃物・金属ふた等", source=2, parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="区分ごとに別指定袋。刃物等は紙で包み内容を表示")
add("M112", "小型電化製品及び有害物", "携帯電話・小型電化製品・蛍光灯・電池・ライター等", source=2, parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="電池を取り外し絶縁。電池とライターは別々の見える小袋。電気製品のコードは切る")
add("M112", "陶器・ガラス類", "陶器・ガラス食器・割れガラス・温度計等", source=2, parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="割れて危険なものは紙等で包み内容を表示")
add("M112", "その他不燃物", "はきもの・保冷剤・使い捨てカイロ・混合素材品等", source=2, parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="区分ごとに別指定袋")
add("M112", "プラスチックごみ", "ペットボトル・その他プラスチック", source=2)
add("M112", "ペットボトル", "PETマークのペットボトル", source=2, parent="プラスチックごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="内容物・付着物を除き洗う。キャップ・ラベルはその他プラスチックへ")
add("M112", "その他プラスチック", "対象プラスチック類", source=2, parent="プラスチックごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ボトル・チューブ類は中身を使い切り、キャップ・ふたを外す")
add("M112", "粗大ごみ", "指定袋に入らない・10kg以上等の大型家庭ごみ", source=2, ui="REFERENCE_ONLY", bulky="TRUE", prep="粗大ごみ利用券を貼る。70kg以上は直接持込み")

# M113 北広島町 — same Geihoku intermunicipal resident taxonomy, evidenced by town's current 2026 guide.
add("M113", "燃えるごみ", "生ごみ・布・紙くず・木の枝等", source=2, prep=NS)
add("M113", "古紙類", "新聞・ダンボール・雑誌・ざつ紙等", source=2, prep=NS)
add("M113", "容器包装類", "紙パック・プラスチック製容器包装・ペットボトル", source=2)
add("M113", "紙パック", "紙パック", source=2, parent="容器包装類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=NS)
add("M113", "プラスチック製容器包装", "プラマークの容器包装", source=2, parent="容器包装類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=NS)
add("M113", "ペットボトル", "PETマークのペットボトル", source=2, parent="容器包装類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=NS)
add("M113", "燃えないごみ", "かん・びん・小型家電・金物・陶器・ガラス", source=2)
add("M113", "かん類", "缶・スプレー缶等", source=2, parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=NS)
add("M113", "びん類", "びん類", source=2, parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=NS)
add("M113", "小型家電、電源コード、金物など", "小型家電・金属類・電源コード等", source=2, parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=NS)
add("M113", "陶器 ガラス類", "陶器・ガラス類", source=2, parent="燃えないごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=NS)
add("M113", "有害ごみ", "乾電池・蛍光管・水銀製品等", source=2, prep=NS)
add("M113", "粗大ごみ", "大型家庭ごみ", source=2, ui="REFERENCE_ONLY", bulky="TRUE", prep=NS)

# M114 大崎上島町 — six top groups, with two resident substreams under nonburnable/resource.
add("M114", "可燃ごみ", "生ごみ・紙・布・プラスチック等", prep="町指定袋で出す。小型充電式電池は取り外して有害ごみへ")
add("M114", "不燃ごみ", "びん・陶磁器・缶・刃物等")
add("M114", "ビン・陶磁器類", "びん・陶磁器類", parent="不燃ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="びんはふたを外し中をすすぐ")
add("M114", "缶類・刃物類", "缶・刃物・スプレー缶等", parent="不燃ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="缶はすすぎ、つぶさない。スプレー缶・カセットボンベは使い切り穴を開ける。刃物は包む")
add("M114", "資源ごみ", "紙類・ペットボトル")
add("M114", "紙類", "新聞・チラシ・雑誌・雑がみ・ダンボール等", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="種類別に分けてひもでしばる。汚れた紙は可燃ごみ")
add("M114", "ペットボトル", "PETマークのペットボトル", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="キャップ・ラベルを外し、すすいでつぶす。汚れたものは可燃ごみ")
add("M114", "大型可燃ごみ", "大型の可燃性家庭ごみ", ui="REFERENCE_ONLY", bulky="TRUE", prep=NS)
add("M114", "粗大ごみ", "大型の不燃性・複合家庭ごみ", ui="REFERENCE_ONLY", bulky="TRUE", prep=NS)
add("M114", "有害ごみ", "乾電池・充電式電池・蛍光管・充電池を外せない小型家電等", prep="電池は専用容器へ。充電池を外せない小型家電は本体ごと有害ごみ")

# M115 世羅町 — 不燃ごみ projection parent with five separately bagged leaves.
add("M115", "可燃ごみ", "生ごみ・紙くず・汚れた容器包装プラスチック等", prep="指定袋で出す。容器包装プラで汚れが落ちないものはこちら")
add("M115", "容器包装プラスチック", "プラマークのきれいな容器包装", prep="汚れを落とす。汚れが落ちないものは可燃ごみ")
add("M115", "びん・缶", "飲食用びん・缶等", prep="ふたを外し、中を洗う。汚れた・割れたびん等は不燃物")
add("M115", "ペットボトル", "PETマークのペットボトル", prep="キャップ・ラベルを外して容器包装プラスチックへ。汚れたものは可燃ごみ")
add("M115", "不燃ごみ", "不燃物・発火性危険ごみ・充電式小型家電・電池類・蛍光灯類")
add("M115", "不燃物", "金属・ガラス・陶磁器・その他プラスチック等", parent="不燃ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="針・刃物・割れガラス等は安全に包む")
add("M115", "発火性危険ごみ", "カセットボンベ・スプレー缶・ガスライター", parent="不燃ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中身を使い切る。使い切った場合は穴を開ける必要はない")
add("M115", "充電式小型家電", "ゲーム機・電気かみそり・電子たばこ・モバイルバッテリー等", parent="不燃ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="充電器・ケーブルは不燃物。取り外した充電式電池は電池類へ")
add("M115", "電池類", "乾電池・ボタン電池・リチウム電池等", parent="不燃ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="電極をテープで絶縁する")
add("M115", "蛍光灯類", "蛍光灯・電球・水銀体温計・LED等", parent="不燃ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="箱または新聞紙等で包み破損を防ぐ")


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
            authority_type = "MUNICIPAL_DOMAIN"
            authority_name = municipality_specs[mid]["city"]
            if "geihokukouiki.jp" in host:
                authority_type = "INTERMUNICIPAL_AUTHORITY_DOMAIN"
                authority_name = "芸北広域環境施設組合"
            rows.append({
                "municipality_id": mid, "host": host, "authority_type": authority_type,
                "authority_name": authority_name, "verification_url": municipality_specs[mid]["top"],
                "verified_date": CHECKED, "notes": f"Batch 11 official source host ({issuer})",
            })
            existing.add((mid, host))
    rows.sort(key=lambda r: (r.get("municipality_id", ""), r.get("host", "")))
    write_csv(path, fields, rows)


def build_sources() -> list[dict[str, str]]:
    rows = []
    for mid in sorted(TARGETS):
        for i, (title, kind, url, updated, used, issuer) in enumerate(source_specs[mid], 1):
            preflight_source = mid == "M106" and i == 2
            rows.append({
                "municipality_id": mid, "source_id": f"S-{mid}-{i:02d}", "資料名": title, "資料種別": kind,
                "公式URL": url, "発行主体": issuer,
                "対象年度": "2026年度／取得時点現行" if preflight_source else "令和8年度",
                "ページ更新日": updated, "取得確認日": M106_PREFLIGHT_CHECKED if preflight_source else CHECKED,
                "使用した情報": used, "優先度": str(i), "現行性": "CURRENT" if preflight_source else "現行",
                "備考": "M106 LESSON_READY_10 scoring viability preflightで確認した非BOX経路のcategory根拠。" if preflight_source else "",
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
        name_to_id = {r["自治体正式名称"]: f"C-{mid}-{i:02d}" for i, r in enumerate(raws, 1)}
        for i, raw in enumerate(raws, 1):
            sidx = int(raw["source_index"])
            src = source_specs[mid][sidx - 1]
            rows.append({
                "municipality_id": mid, "category_id": name_to_id[raw["自治体正式名称"]],
                "自治体正式名称": raw["自治体正式名称"], "category_group": raw["category_group"],
                "parent_category_id": name_to_id.get(raw["parent_name"], ""), "classification_level": raw["classification_level"],
                "表示順": str(i), "collection_channel": raw["collection_channel"], "代表品目": raw["代表品目"],
                "入れてはいけない物": raw["入れてはいけない物"], "適用条件": raw["適用条件"],
                "条件外の扱い": raw["条件外の扱い"], "出す前の処理": raw["出す前の処理"],
                "袋・容器のルール": raw["袋・容器のルール"], "サイズ・条件": raw["サイズ・条件"],
                "粗大ごみ扱いか": raw["粗大ごみ扱いか"], "予約が必要か": raw["予約が必要か"],
                "有料か": raw["有料か"], "料金ルール": raw["料金ルール"], "自治体収集外か": raw["自治体収集外か"],
                "注意事項": raw["注意事項"], "source_id": f"S-{mid}-{sidx:02d}", "出典URL": src[2],
                "出典ページ・該当箇所": "3.廃棄方法" if mid == "M106" and sidx == 2 else raw["出典ページ・該当箇所"],
                "確認日": raw["確認日"],
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
        count = leaf_count(mid)
        rows.append({
            "municipality_id": mid, "都道府県": spec["pref"], "市町村": spec["city"], "実装区分": "中国5県全市町村",
            "ごみ処理主体": spec["processor"], "自治体ごみトップURL": spec["top"], "分別ガイドURL": spec["guide"],
            "品目検索URL": "", "やさしい日本語URL": "", "多言語資料URL": "", "対象年度": "令和8年度",
            "最終確認日": CHECKED, "確認ステータス": "QA_REQUIRED", "備考": spec["note"],
            "official_category_count": "", "reviewed_category_count": str(count),
            "category_count_basis": "住民が排出時に選択する現行公式分別区分を公式索引・現年度資料で全件照合。上位グループは子葉へ二重計上しない。",
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
                "notes": f"{M106_PREFLIGHT_CHECKED if mid == 'M106' and i == 2 else CHECKED} Batch 11 resident-facing category completeness review",
            })
    return rows


def main() -> None:
    if set(municipality_specs) != TARGETS or set(source_specs) != TARGETS:
        raise ValueError("Batch11 target mismatch")
    expected = {"M106": 11, "M107": 8, "M108": 11, "M109": 9, "M110": 6, "M111": 13, "M112": 12, "M113": 11, "M114": 8, "M115": 9}
    actual = {mid: leaf_count(mid) for mid in sorted(TARGETS)}
    if actual != expected:
        raise ValueError(f"Batch11 leaf count mismatch: {actual}")
    ensure_registry()
    OUT.mkdir(parents=True, exist_ok=True)
    p = "batch_11_"
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
