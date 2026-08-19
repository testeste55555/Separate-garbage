#!/usr/bin/env python3
"""Build Batch 06 (M054-M063) from current resident-facing official sources.

Schema v1.2.4 policy:
- model the categories residents actually choose when disposing household waste;
- preserve municipality wording and region-specific official systems;
- use parent/child rows when official leaf detail is finer than the learner-facing box;
- never invent source details: use NOT_STATED_IN_CITED_SOURCE.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from schema_v12 import (
    CATEGORY_FIELDS, CATEGORY_REVIEW_EVIDENCE_FIELDS, COVERAGE_FIELDS, MAPPING_FIELDS,
    MASTER, MUNICIPALITY_FIELDS, QA_FIELDS, SOURCE_FIELDS, migrate_batch_dir,
    read_csv, write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research" / "batches" / "batch_06"
CHECKED = "2026-08-19"
REVIEWER = "OPENAI_CHATGPT_BATCH06_REVIEW"
NOT_STATED = "NOT_STATED_IN_CITED_SOURCE"
REGISTRY_FIELDS = [
    "municipality_id", "host", "authority_type", "authority_name",
    "verification_url", "verified_date", "notes",
]
TARGETS = {f"M{i:03d}" for i in range(54, 64)}

municipality_specs = {
    "M054": dict(pref="島根県", city="江津市", processor="江津市",
        top="https://www.city.gotsu.lg.jp/soshiki/12/39048.html",
        guide="https://www.city.gotsu.lg.jp/soshiki/12/8529.html", current="https://www.city.gotsu.lg.jp/soshiki/12/39048.html",
        search="", multilingual="", note="令和8年度収集案内と家庭ごみ分け方から、非資源5ラベルと資源7品目を住民向け区分として保持。"),
    "M055": dict(pref="島根県", city="雲南市", processor="雲南市／雲南市・飯南町事務組合",
        top="https://www.city.unnan.shimane.jp/unnan/kurashi/kankyou/recycle/garbage02.html",
        guide="https://www.unnan-yume.net/kankyo/gomi/gomibunbetu.php", current="https://www.unnan-yume.net/kankyo/gomi-calendar/calendar.php",
        search="", multilingual="", note="大東・加茂・木次・三刀屋系と吉田・掛合系の両公式手引きを照合。共通する住民向け区分を保持し、地域差は条件として残す。"),
    "M056": dict(pref="島根県", city="奥出雲町", processor="奥出雲町",
        top="https://www.town.okuizumo.shimane.jp/kurashi/gomi-recycle/1773388412727.html",
        guide="https://www.town.okuizumo.shimane.jp/www/contents/1773388412727/files/r8gomibunbetsu.pdf", current="https://www.town.okuizumo.shimane.jp/kurashi/gomi-recycle/1773388412727.html",
        search="https://www.town.okuizumo.shimane.jp/kurashi/gomi-recycle/1773388367729.html", multilingual="", note="令和8年4月版の住民向け分類を採用。スプレー缶は中身を使い切り穴を開けて空き缶。"),
    "M057": dict(pref="島根県", city="飯南町", processor="飯南町／雲南市・飯南町事務組合",
        top="https://www.iinan.jp/soshiki/8/1865.html", guide="https://www.unnan-yume.net/kankyo/gomi/gomibunbetu.php",
        current="https://www.unnan-yume.net/kankyo/gomi-calendar/calendar.php", search="", multilingual="", note="町公式が雲南市・飯南町事務組合を正式案内。いいしクリーンセンター管内の住民向け区分を令和8年度頓原・赤来カレンダーで現行確認。"),
    "M058": dict(pref="島根県", city="川本町", processor="川本町／邑智クリーンセンター",
        top="https://www.town.shimane-kawamoto.lg.jp/gyosei/gyosei_environment/environment/",
        guide="https://www.town.shimane-kawamoto.lg.jp/gyosei/gyosei_environment/environment/4377", current="https://www.town.shimane-kawamoto.lg.jp/files/original/20260331171521171fa6559a6.pdf",
        search="", multilingual="", note="令和6年12月改訂しおりと令和8年度日程を照合。公式13分別を保持し、古紙4葉は親箱配下に保持。"),
    "M059": dict(pref="島根県", city="美郷町", processor="美郷町／邑智クリーンセンター",
        top="https://gov.town.shimane-misato.lg.jp/kurasi/kankyo/246/", guide="https://gov.town.shimane-misato.lg.jp/kurasi/kankyo/246/guide",
        current="https://gov.town.shimane-misato.lg.jp/kurasi/kankyo/246/1482", search="", multilingual="", note="令和7年3月更新の分別しおりと令和8年度日程を照合。邑智方式の13分別と有害ごみ拡大を反映。"),
    "M060": dict(pref="島根県", city="邑南町", processor="邑南町／邑智クリーンセンター",
        top="https://www.town.ohnan.lg.jp/soshiki/4/1072.html", guide="https://www.town.ohnan.lg.jp/soshiki/4/1072.html",
        current="https://www.town.ohnan.lg.jp/soshiki/4/1267.html", search="", multilingual="", note="2026年更新の住民向け出し方と令和8年度日程を採用。10種13分別を親子構造で保持。スプレー缶は必ず穴あけ。"),
    "M061": dict(pref="島根県", city="津和野町", processor="津和野町／鹿足郡不燃物処理組合／益田地区広域市町村圏事務組合",
        top="https://www.town.tsuwano.lg.jp/www/contents/1000000358000/index.html",
        guide="https://www.town.tsuwano.lg.jp/www/contents/1000000358000/simple/gominowakekatadasikatanotebikisyo.pdf", current="https://www.town.tsuwano.lg.jp/www/contents/1000000358000/index.html",
        search="", multilingual="https://www.town.tsuwano.lg.jp/www/contents/1000000358000/index.html", note="2026年3月公開R8.4改訂手引きと公式リサイクル運用から8住民区分を保持。"),
    "M062": dict(pref="島根県", city="吉賀町", processor="吉賀町／鹿足郡不燃物処理組合／益田地区広域市町村圏事務組合",
        top="https://www.town.yoshika.lg.jp/kurashi/seikatsu/gomi/", guide="https://www.town.yoshika.lg.jp/kurashi/seikatsu/gomi/gomi.html",
        current="https://www.town.yoshika.lg.jp/kurashi/seikatsu/gomi/gomikarennda-.html", search="", multilingual="https://www.town.yoshika.lg.jp/kurashi/seikatsu/gomi/gomi.html", note="2026年度カレンダーの8住民区分を採用。令和8年3月1日からライター類は有害ごみ。スプレー缶は穴あけ不要。"),
    "M063": dict(pref="島根県", city="海士町", processor="海士町",
        top="https://www.town.ama.shimane.jp/kurashi-tetsuduki/kurashi/gomi-recycle/r44t8e7yf3",
        guide="https://www.town.ama.shimane.jp/kurashi-tetsuduki/kurashi/gomi-recycle/r44t8e7yf3", current="https://www.town.ama.shimane.jp/kurashi-tetsuduki/kurashi/gomi-recycle/r44t8e7yf3",
        search="", multilingual="", note="2026年公式カレンダーに表示される7収集ラベルをそのまま住民向け体系として採用。複合ラベルを人工分割しない。"),
}

source_specs = {
    "M054": [
        ("令和8年度家庭ごみの収集日","自治体公式Webページ",municipality_specs["M054"]["current"],"2026-03-02","現行収集ラベル・資源7品目・粗大基準"),
        ("家庭ごみの分け方・出し方（令和6年度～）","自治体公式Webページ",municipality_specs["M054"]["guide"],"現行","資源品目別条件・前処理")],
    "M055": [
        ("雲南市 ごみの分別・収集案内","自治体公式Webページ",municipality_specs["M055"]["top"],"現行","雲南市・飯南町事務組合への公式導線"),
        ("ごみの分別方法（雲南EC管内）","一部事務組合公式PDF","https://www.unnan-yume.net/files/format/kankyo_ebook_enesen.pdf","現行","大東・加茂・木次・三刀屋地域の分別区分"),
        ("ごみの分別方法（いいしCC管内）","一部事務組合公式PDF","https://www.unnan-yume.net/files/format/kankyo_ebook_iishi.pdf","現行","吉田・掛合地域の分別区分"),
        ("令和8年度ごみ収集カレンダー","一部事務組合公式Webページ",municipality_specs["M055"]["current"],"2026","市内6地域の現行運用")],
    "M056": [
        ("家庭ごみの分け方・出し方（令和8年4月版）","自治体公式PDF",municipality_specs["M056"]["guide"],"2026-04-21","現行収集分類・持込・収集外"),
        ("スプレー缶・カセットボンベの捨て方","自治体公式Webページ","https://www.town.okuizumo.shimane.jp/kurashi/gomi-recycle/1001000000397.html","2026-03-26","中身を使い切り穴を開けて資源ごみ（空き缶）"),
        ("家庭ごみの分け方・出し方（現行案内）","自治体公式Webページ",municipality_specs["M056"]["top"],"2026-04-21","令和8年4月版への公式導線")],
    "M057": [
        ("飯南町 ごみの出し方","自治体公式Webページ",municipality_specs["M057"]["top"],"現行","雲南市・飯南町事務組合への公式導線"),
        ("ごみの分別方法（いいしCC管内）","一部事務組合公式PDF","https://www.unnan-yume.net/files/format/kankyo_ebook_iishi.pdf","現行","飯南町の住民向け分別区分"),
        ("令和8年度ごみ収集カレンダー","一部事務組合公式Webページ",municipality_specs["M057"]["current"],"2026","飯南町頓原・赤来の現行運用")],
    "M058": [
        ("ごみの種類と分別方法（令和6年12月改訂）","自治体公式Webページ",municipality_specs["M058"]["guide"],"2025-03","しおり・ポスターへの公式導線"),
        ("令和8年度川本町ごみ収集日程表","自治体公式PDF",municipality_specs["M058"]["current"],"2026","現行収集区分・指定袋"),
        ("指定ごみ袋・粗大ごみシール","自治体公式Webページ","https://www.town.shimane-kawamoto.lg.jp/gyosei/gyosei_environment/environment/gomibukuro","現行","可燃・不燃・容器プラ・PET・容器紙・缶・びんの独立袋")],
    "M059": [
        ("ごみの種類と分別の仕方","自治体公式Webページ",municipality_specs["M059"]["guide"],"2025-03-13","分別しおり・ポスター、有害ごみ拡大"),
        ("令和8年度家庭ごみ収集日程表","自治体公式Webページ",municipality_specs["M059"]["current"],"2026","現行収集体系"),
        ("ごみ収集よくある質問と回答","自治体公式Webページ","https://gov.town.shimane-misato.lg.jp/kurasi/kankyo/246/qa","現行","スプレー缶穴あけ・電池等の具体条件")],
    "M060": [
        ("ごみの出し方","自治体公式Webページ",municipality_specs["M060"]["guide"],"2026-01-13","住民向け分別・袋・前処理"),
        ("令和8年度家庭ごみ収集等計画","自治体公式Webページ",municipality_specs["M060"]["current"],"2026-01-13","現行運用確認"),
        ("一般廃棄物処理実施計画の分別区分","自治体公式資料","https://www.town.ohnan.lg.jp/www/contents/1725430530282/simple/keikaku.pdf","現行体系","10種13分別・古紙4葉の構造")],
    "M061": [
        ("ごみの分別・出し方について","自治体公式Webページ",municipality_specs["M061"]["top"],"2026-03-27","R8.4改訂手引きへの公式導線"),
        ("ごみの分け方・出し方の手引書（R8.4改訂版）","自治体公式PDF",municipality_specs["M061"]["guide"],"2026-04","現行住民向け分類"),
        ("廃棄物集積施設への粗大ゴミ等の自己搬入","自治体公式Webページ","https://www.town.tsuwano.lg.jp/www/contents/1000000356000/index.html","現行","容器包装プラ・商品プラ・缶・びん・有害・粗大・資源の現行導線")],
    "M062": [
        ("ごみの分け方・出し方について","自治体公式Webページ",municipality_specs["M062"]["guide"],"現行","分別大図鑑・2026年ライター変更・外国語版"),
        ("2026年度ごみ収集カレンダー","自治体公式Webページ",municipality_specs["M062"]["current"],"2026","現行収集ラベル"),
        ("資源ごみについて","自治体公式Webページ","https://www.town.yoshika.lg.jp/kurashi/seikatsu/gomi/shigengomi.html","現行","新聞・雑誌雑紙・段ボール・紙パック・衣類"),
        ("ライター類分別変更","自治体公式PDF","https://www.town.yoshika.lg.jp/kurashi/seikatsu/gomi/gomi.data/raitabunnbetu.pdf","2026-03-01","ライター類を有害ごみへ変更")],
    "M063": [
        ("ゴミの出し方・分け方","自治体公式Webページ",municipality_specs["M063"]["top"],"2026-01-13","早見表・2026年カレンダーへの公式導線"),
        ("2026年 海士町ごみ収集カレンダー","自治体公式リンク資料",municipality_specs["M063"]["top"],"2026","可燃物・PET・びんガラス陶器・蛍光灯水銀・廃食用油・缶金物・粗大乾電池の7ラベル")],
}

categories = []
def add(mid,name,rep,*,source=1,locator="分別区分",parent="",ui="SORT_BUCKET",level="PRIMARY",channel="CURBSIDE",forbidden=NOT_STATED,fallback=NOT_STATED,prep=NOT_STATED,bag="",size="",bulky="FALSE",excluded="FALSE",note=""):
    categories.append({"municipality_id":mid,"自治体正式名称":name,"category_group":name,"parent_name":parent,"classification_level":level,"collection_channel":channel,"代表品目":rep,"入れてはいけない物":forbidden,"適用条件":"","条件外の扱い":fallback,"出す前の処理":prep,"袋・容器のルール":bag,"サイズ・条件":size,"粗大ごみ扱いか":bulky,"予約が必要か":"FALSE","有料か":"FALSE","料金ルール":"","自治体収集外か":excluded,"注意事項":note,"source_index":str(source),"出典ページ・該当箇所":locator,"ui_role":ui})
def excluded(mid,name,rep,*,source=1,locator="収集・処理できないもの"):
    add(mid,name,rep,source=source,locator=locator,ui="EXCLUDED_NOTICE",level="EXCLUDED",channel="NOT_COLLECTED",excluded="TRUE",fallback="販売店・メーカー・専門業者等の公式案内に従う",prep="受入先の指示に従う")
def paper_tree(mid, source=1, prefix=""):
    parent = f"{prefix}古紙類・紙パック" if prefix else "古紙類・紙パック"
    add(mid,parent,"新聞・雑誌・段ボール・紙パック",source=source,locator=f"分別区分／{parent}",ui="SORT_BUCKET",level="PRIMARY",prep="種類別にまとめる")
    add(mid,"新聞紙・折込広告","新聞紙・折込広告",source=source,locator="古紙類・紙パック／新聞紙・折込広告",parent=parent,ui="REFERENCE_ONLY",level="SUBCATEGORY",prep="ひもで十字にくくる")
    add(mid,"広告・雑誌・書籍","広告・雑誌・書籍",source=source,locator="古紙類・紙パック／広告・雑誌・書籍",parent=parent,ui="REFERENCE_ONLY",level="SUBCATEGORY",prep="ひもで十字にくくる")
    add(mid,"段ボール","段ボール",source=source,locator="古紙類・紙パック／段ボール",parent=parent,ui="REFERENCE_ONLY",level="SUBCATEGORY",prep="ひもで十字にくくる")
    add(mid,"紙パック","牛乳・ジュース等の紙パック",source=source,locator="古紙類・紙パック／紙パック",parent=parent,ui="REFERENCE_ONLY",level="SUBCATEGORY",prep="洗って開き乾かし、ひもでまとめる")

# M054 江津市
add("M054","金物類（粗大ごみを含む）","金属製品・金属を含む粗大品",locator="令和8年度収集日／金物類（粗大ごみを含む）")
add("M054","有害ごみ（粗大ごみを含む）","電池類・蛍光灯・電球等",locator="令和8年度収集日／有害ごみ（粗大ごみを含む）",prep="品目別の市指定方法に従う")
add("M054","ガラス・陶器類（粗大ごみを含む）","ガラス・陶器類",locator="令和8年度収集日／ガラス・陶器類（粗大ごみを含む）",prep="割れ物は危険防止")
add("M054","燃やせるごみ","生ごみ・紙くず等",locator="令和8年度収集日／燃やせるごみ",bag="市指定袋",prep="生ごみは水切り")
add("M054","燃やせる粗大ごみ","指定袋に入らない可燃大型品",locator="令和8年度収集日／燃やせる粗大ごみ",bulky="TRUE",prep="市指定ごみ券を貼る",size="長さ2m程度まで等の市基準")
for n,r,p in [
    ("ビン類","飲食用びん","中身を空にして洗い、ふたを外す"),("缶類","飲料用アルミ缶・スチール缶","中身を空にして洗い、つぶさない"),
    ("容器包装プラスチック類","プラマークの容器包装","汚れを落とす。汚れが残る物は燃やせるごみ"),("ペットボトル","PETマークのボトル","ふたとラベルを外し、つぶさない"),
    ("発泡スチロール","発泡スチロール","テープ・シールを外し汚れを落とす"),("白色トレイ","白色食品トレイ","汚れを落とす"),("紙類","新聞・チラシ・雑誌・書籍・箱紙等","紙種別の市指定方法でまとめる")]:
    add("M054",n,r,source=2,locator=f"家庭ごみの分け方／{n}",prep=p)

# M055 雲南市（両処理区域の公式手引きを照合）
for name,rep,extra in [
    ("燃やせるごみ","可燃性家庭ごみ",dict()),("資源ごみ（ビン・カン）","飲食用びん・缶",dict(prep="中身を空にし洗う")),
    ("資源ごみ（古紙）","新聞・雑誌・段ボール等",dict(prep="種類別にまとめる")),("陶器・ガラス類","陶器・ガラス類",dict()),
    ("くつ類・プラスチック類","靴・プラスチック製品等",dict()),("金属類（小型家電類含む）","金属・小型家電類",dict(prep="取り外せる電池を外す")),
    ("灰類","家庭から出る灰",dict()),("有害ごみ1","蛍光灯類",dict(prep="破損しないよう保護")),
    ("有害ごみ2","乾電池・水銀製品・電子たばこ等",dict(prep="電池類は端子を絶縁")),
    ("粗大ごみ（直接持込み）","大型家庭ごみ",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",bulky="TRUE")),
    ("特定家電","家電4品目",dict(ui="REFERENCE_ONLY",channel="DROP_OFF"))]:
    add("M055",name,rep,source=2 if name not in {"有害ごみ1","有害ごみ2"} else 3,locator=f"公式分別手引き／{name}",**extra)
excluded("M055","収集・処理しないもの","処理困難物・事業系対象外品等",source=2,locator="公式分別手引き／収集・処理しないもの")

# M056 奥出雲町
for name,rep,extra in [
    ("燃やせるごみ","生ごみ・紙・布・革ゴム・非容器プラ等",dict(prep="生ごみは水切り",bag="町指定袋")),
    ("プラ容器包装","プラマークの容器包装",dict(prep="汚れをすすいで落とす")),
    ("ペットボトル","PETマークのボトル",dict(prep="キャップとラベルを外し、すすぐ")),
    ("空き缶","飲料缶・スプレー缶・カセットボンベ",dict(source=2,prep="スプレー缶・カセットボンベは中身を使い切り、火気のない所で穴を開ける")),
    ("空きびん","飲食物・化粧品・家庭常備薬のびん",dict(prep="ふたを外し、すすぐ")),
    ("不燃ごみ","金属・陶器・ガラス・小型家電等",dict(prep="小型家電は取り外せる乾電池類を外す")),
    ("有害ごみ","蛍光灯・乾電池類",dict(prep="蛍光灯と乾電池類は別々にする")),
    ("古紙類","新聞・段ボール・雑誌雑紙・牛乳パック・シュレッダー紙",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",prep="古紙回収日程に従う")),
    ("粗大ごみ","袋に入らない可燃・不燃大型品",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",bulky="TRUE")),
    ("水銀使用製品","水銀体温計・温度計・血圧計",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",prep="破損しないよう回収ボックスへ"))]:
    src=extra.pop("source",1); add("M056",name,rep,source=src,locator=f"令和8年4月版／{name}",**extra)
excluded("M056","町で処理できないごみ","家電4品目・産廃・農機具・農薬・処理困難物等",locator="令和8年4月版／町で処理できないごみ")

# M057 飯南町（いいしCC管内）
for name,rep,extra in [
    ("燃やせるごみ","可燃性家庭ごみ",dict()),("資源ごみ（ビン・カン）","飲食用びん・缶",dict(prep="中身を空にし洗う")),
    ("資源ごみ（古紙）","新聞・雑誌・段ボール等",dict(prep="種類別にまとめる")),("陶器・ガラス類","陶器・ガラス類",dict()),
    ("くつ類・プラスチック類","靴・プラスチック製品等",dict()),("金属類（小型家電類含む）","金属・小型家電類",dict(prep="取り外せる電池を外す")),
    ("灰類","家庭から出る灰",dict()),("有害ごみ1","蛍光灯類",dict(prep="破損しないよう保護")),
    ("有害ごみ2","乾電池・水銀製品・電子たばこ等",dict(prep="電池類は端子を絶縁")),
    ("粗大ごみ（直接持込み）","大型家庭ごみ",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",bulky="TRUE")),
    ("特定家電","家電4品目",dict(ui="REFERENCE_ONLY",channel="DROP_OFF"))]: add("M057",name,rep,source=2,locator=f"いいしCC分別手引き／{name}",**extra)
excluded("M057","処理できないごみ","処理困難物・対象外品",source=2,locator="いいしCC分別手引き／処理できないごみ")

# M058-M060 邑智3町: official 10種13分別; UI parent keeps four paper leaves together.
for mid,src in [("M058",1),("M059",1),("M060",3)]:
    add(mid,"燃えるごみ","生ごみ・紙くず・非容器プラ等",source=src,locator="分別区分／燃えるごみ",prep="生ごみは水切り")
    paper_tree(mid,source=src)
    add(mid,"容器包装紙","紙マークの容器包装",source=src,locator="分別区分／容器包装紙",prep="異物を除き、汚れが取れない物は燃えるごみ")
    add(mid,"容器包装プラスチック","プラマークの容器包装",source=src,locator="分別区分／容器包装プラスチック",prep="異物を除き洗って水切り。汚れが取れない物は燃えるごみ")
    add(mid,"ビン","食品・飲料用びん",source=src,locator="分別区分／ビン",prep="ふたを外し中をすすぐ")
    add(mid,"カン","飲料用缶",source=src,locator="分別区分／カン",prep="中をすすぎ、つぶさない")
    add(mid,"ペットボトル","PETマークのボトル",source=src,locator="分別区分／ペットボトル",prep="ふたとラベルを分別し中をすすぐ")
    spray="スプレー缶は中身を使い切り、屋外で穴を開ける" if mid in {"M059","M060"} else "スプレー缶等の危険品は公式しおりの方法に従う"
    add(mid,"不燃ごみ","ガラス・陶磁器・金属・小型電化製品等",source=src,locator="分別区分／不燃ごみ",prep=spray)
    add(mid,"有害ごみ","電池・蛍光管・水銀製品等",source=src,locator="分別区分／有害ごみ",prep="中身の見える袋等、公式指定方法に従う")
    add(mid,"粗大ごみ","寝具・家具・大型電化製品等",source=src,locator="分別区分／粗大ごみ",bulky="TRUE",prep="燃料・電池を取り除く")
    excluded(mid,"収集・処理できないもの","家電4品目・処理困難物等",source=src,locator="分別案内／収集・処理できないもの")

# M061 津和野町 — current calendar/guide labels.
for name,rep,extra in [
    ("もやせるごみ","台所ごみ・紙くず・布類・草木類等",dict(prep="生ごみは水切り")),
    ("容器包装プラスチック","PETボトル・トレイ・カップ・袋・発泡スチロール等",dict(prep="町指定方法で汚れを除く")),
    ("商品プラスチック","文具・玩具・プラスチック製品・ビニールゴム製品",dict(prep="乾電池・充電池を外す")),
    ("びん・ガラス・陶器類","飲食用びん・ガラス・陶器類",dict(prep="キャップ等を外し洗う")),
    ("缶類","飲食用缶・小型金属類",dict(prep="中身を空にする")),
    ("有害ごみ","蛍光灯・電球・水銀体温計・乾電池・鏡等",dict(prep="破損しないよう保護")),
    ("粗大ごみ","やかん・鍋・自転車・小型家電・布団等",dict(bulky="TRUE")),
    ("資源ごみ","新聞・雑誌・段ボール・紙パック・衣類等",dict(prep="品目別にまとめる"))]: add("M061",name,rep,source=2,locator=f"R8.4手引書／{name}",**extra)
excluded("M061","収集・搬入できないもの","処理困難物・対象外品",source=1,locator="R8.4手引書／収集・搬入できないもの")

# M062 吉賀町 — R8 current change: lighters -> hazardous; spray cans no hole.
for name,rep,extra in [
    ("可燃ごみ","台所ごみ・紙類・布類・草木類等",dict(prep="生ごみは水切り")),
    ("容器包装プラスチック","PETボトル・トレイ・容器包装・袋・発泡スチロール等",dict(prep="中身を使い切り洗い乾燥。PETはふた・ラベルを外す")),
    ("商品プラスチック","文具・玩具・プラスチック製品・ビニールゴム製品",dict(prep="乾電池・充電池を外す")),
    ("ビン・陶器類","飲食用びん・陶器・ガラス類",dict(prep="ふたを外し洗う。割れ物は危険防止")),
    ("カン類","飲食用缶・小型缶・小型金属類・スプレー缶",dict(prep="スプレー缶は中身を使い切る。穴はあけなくてよい")),
    ("有害ごみ","乾電池・充電池・蛍光灯・水銀製品・ライター類",dict(source=4,prep="ライターは中身を使い切り別袋に入れ『有害ごみ』と表記。他の有害ごみと混ぜない")),
    ("粗大ごみ","鍋・自転車・家具・小型家電等",dict(bulky="TRUE")),
    ("資源ごみ","新聞・雑誌雑紙・段ボール・紙パック・布製衣類",dict(source=3,prep="種類ごとに紙ひも等でまとめる"))]:
    src=extra.pop("source",1); add("M062",name,rep,source=src,locator=f"現行分別案内／{name}",**extra)
excluded("M062","排出禁止ごみ","家電リサイクル品・タイヤ・農薬・処理困難物等",locator="2026年度カレンダー／排出禁止ごみ")

# M063 海士町 — exact combined current calendar labels.
for name,rep,extra in [
    ("可燃物","家庭の可燃ごみ",dict()),("ペットボトル","PETボトル",dict(prep="町の早見表に従う")),
    ("びん・ガラス/陶器","びん・ガラス・陶器類",dict()),("蛍光灯/水銀","蛍光灯・水銀製品",dict(prep="破損しないよう保護")),
    ("廃食用油","家庭の廃食用油",dict()),("缶・金物","缶・金属類",dict()),
    ("粗大・乾電池","粗大ごみ・乾電池",dict(bulky="TRUE",prep="乾電池は端子を絶縁。粗大ごみは品目別料金・方法を確認"))]: add("M063",name,rep,source=2,locator=f"2026年海士町ごみカレンダー／{name}",**extra)


def ensure_registry():
    path=MASTER/"02_official_domain_registry.csv"; fields,rows=read_csv(path); fields=fields or REGISTRY_FIELDS
    existing={(r.get("municipality_id"),r.get("host")) for r in rows}
    for mid,specs in source_specs.items():
        for title,kind,url,updated,used in specs:
            host=(urlparse(url).hostname or "").lower(); key=(mid,host)
            if not host or key in existing: continue
            if host == "www.unnan-yume.net": atype="INTERMUNICIPAL_AUTHORITY_DOMAIN"; aname="雲南市・飯南町事務組合"
            else: atype="MUNICIPAL_DOMAIN"; aname=municipality_specs[mid]["city"]
            rows.append({"municipality_id":mid,"host":host,"authority_type":atype,"authority_name":aname,"verification_url":municipality_specs[mid]["top"],"verified_date":CHECKED,"notes":"Batch 06 official resident-facing source host"}); existing.add(key)
    rows.sort(key=lambda r:(r.get("municipality_id",""),r.get("host",""))); write_csv(path,fields,rows)

def build_sources():
    rows=[]
    for mid,specs in source_specs.items():
        for i,(title,kind,url,updated,used) in enumerate(specs,1):
            rows.append({"municipality_id":mid,"source_id":f"S-{mid}-{i:02d}","資料名":title,"資料種別":kind,"公式URL":url,"発行主体":municipality_specs[mid]["city"] if "事務組合" not in kind else "雲南市・飯南町事務組合","対象年度":"令和8年度","ページ更新日":updated,"取得確認日":CHECKED,"使用した情報":used,"優先度":str(i),"現行性":"現行","備考":"","official_verified":"","official_basis":"","official_linking_url":municipality_specs[mid]["top"] if urlparse(url).hostname=="www.unnan-yume.net" else ""})
    return rows

def build_categories():
    by_mid={}
    for raw in categories: by_mid.setdefault(raw["municipality_id"],[]).append(raw)
    if set(by_mid)!=TARGETS: raise ValueError(f"Batch06 target mismatch {set(by_mid)}")
    rows=[]
    for mid,raws in by_mid.items():
        name_to_id={r["自治体正式名称"]:f"C-{mid}-{i:02d}" for i,r in enumerate(raws,1)}
        if len(name_to_id)!=len(raws): raise ValueError(f"duplicate category names {mid}")
        for i,raw in enumerate(raws,1):
            sidx=int(raw["source_index"]); src=source_specs[mid][sidx-1]
            rows.append({"municipality_id":mid,"category_id":name_to_id[raw["自治体正式名称"]],"自治体正式名称":raw["自治体正式名称"],"category_group":raw["category_group"],"parent_category_id":name_to_id.get(raw["parent_name"],"") if raw["parent_name"] else "","classification_level":raw["classification_level"],"表示順":str(i),"collection_channel":raw["collection_channel"],"代表品目":raw["代表品目"],"入れてはいけない物":raw["入れてはいけない物"],"適用条件":raw["適用条件"],"条件外の扱い":raw["条件外の扱い"],"出す前の処理":raw["出す前の処理"],"袋・容器のルール":raw["袋・容器のルール"],"サイズ・条件":raw["サイズ・条件"],"粗大ごみ扱いか":raw["粗大ごみ扱いか"],"予約が必要か":raw["予約が必要か"],"有料か":raw["有料か"],"料金ルール":raw["料金ルール"],"自治体収集外か":raw["自治体収集外か"],"注意事項":raw["注意事項"],"source_id":f"S-{mid}-{sidx:02d}","出典URL":src[2],"出典ページ・該当箇所":raw["出典ページ・該当箇所"],"確認日":CHECKED,"ui_role":raw["ui_role"],"rule_status":"CURRENT","effective_from":"","effective_to":""})
    return rows

def build_municipalities():
    return [{"municipality_id":mid,"都道府県":spec["pref"],"市町村":spec["city"],"実装区分":"中国5県全市町村","ごみ処理主体":spec["processor"],"自治体ごみトップURL":spec["top"],"分別ガイドURL":spec["guide"],"品目検索URL":spec["search"],"やさしい日本語URL":"","多言語資料URL":spec["multilingual"],"対象年度":"令和8年度","最終確認日":CHECKED,"確認ステータス":"QA_REQUIRED","備考":spec["note"],"official_category_count":"","reviewed_category_count":"","category_count_basis":"住民が家庭ごみ排出時に実際に選択する公式分別区分を全件照合し、現年度カレンダー・現行公式導線で稼働を確認。親子構造は公式葉と教材投影を両立するために使用。","category_count_verified":"TRUE","category_count_check_status":"MANUAL_INDEX_REVIEW","category_count_review_id":f"CR-{mid}-CATEGORY-COVERAGE","category_count_reviewed_date":CHECKED,"category_count_reviewed_by":REVIEWER,"search_service_check_status":"CHECKED_PRESENT" if spec["search"] else "NOT_CHECKED","search_service_check_evidence":f"URL:{spec['search']}; checked:{CHECKED}" if spec["search"] else "","easy_japanese_check_status":"NOT_CHECKED","easy_japanese_check_evidence":"","multilingual_check_status":"CHECKED_PRESENT" if spec["multilingual"] else "NOT_CHECKED","multilingual_check_evidence":f"URL:{spec['multilingual']}; checked:{CHECKED}" if spec["multilingual"] else ""} for mid,spec in municipality_specs.items()]

def build_review_evidence():
    rows=[]
    for mid,specs in source_specs.items():
        for i,src in enumerate(specs,1):
            rows.append({"review_evidence_id":f"CRE-{mid}-{i:02d}","review_id":f"CR-{mid}-CATEGORY-COVERAGE","municipality_id":mid,"source_id":f"S-{mid}-{i:02d}","locator":src[4],"evidence_role":"PRIMARY_INDEX" if i==1 else "SUPPLEMENTAL_INDEX","notes":f"{CHECKED} Batch 06 resident-facing category completeness review"})
    return rows

def main():
    if set(municipality_specs)!=TARGETS or set(source_specs)!=TARGETS: raise ValueError("Batch06 spec target mismatch")
    ensure_registry(); OUT.mkdir(parents=True,exist_ok=True); p="batch_06_"
    write_csv(OUT/f"{p}municipalities.csv",MUNICIPALITY_FIELDS,build_municipalities())
    write_csv(OUT/f"{p}categories.csv",CATEGORY_FIELDS,build_categories())
    write_csv(OUT/f"{p}sources.csv",SOURCE_FIELDS,build_sources())
    write_csv(OUT/f"{p}qa.csv",QA_FIELDS,[])
    write_csv(OUT/f"{p}item_mapping.csv",MAPPING_FIELDS,[])
    write_csv(OUT/f"{p}item_coverage.csv",COVERAGE_FIELDS,[])
    write_csv(OUT/f"{p}category_review_evidence.csv",CATEGORY_REVIEW_EVIDENCE_FIELDS,build_review_evidence())
    counts=migrate_batch_dir(OUT); print(" ".join(f"{k}={v}" for k,v in counts.items()))
if __name__=="__main__": main()
