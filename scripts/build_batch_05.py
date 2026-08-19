#!/usr/bin/env python3
"""Build Batch 05 (M044-M053) from resident-facing current official sources.

Schema v1.2.4 semantics:
- preserve the categories residents actually choose when disposing household waste;
- use current calendars/current official navigation as current-operation evidence;
- never invent details absent from the cited source;
- keep municipality wording even when neighboring municipalities share facilities.
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
OUT = ROOT / "data" / "research" / "batches" / "batch_05"
CHECKED = "2026-08-19"
REVIEWER = "OPENAI_CHATGPT_BATCH05_REVIEW"
NOT_STATED = "NOT_STATED_IN_CITED_SOURCE"
REGISTRY_FIELDS = [
    "municipality_id", "host", "authority_type", "authority_name",
    "verification_url", "verified_date", "notes",
]
TARGETS = {f"M{i:03d}" for i in range(44, 54)}

municipality_specs = {
    "M044": dict(pref="鳥取県", city="伯耆町", processor="伯耆町／南部町・伯耆町清掃施設管理組合／鳥取県西部広域行政管理組合",
        top="https://www.houki-town.jp/new1/10/12/gomi/",
        guide="https://www.houki-town.jp/new1/10/12/gomi/6/c935/",
        current="https://www.houki-town.jp/new1/10/12/gomi/m131-copy/",
        search="https://www.houki-town.jp/new1/10/12/gomi/6/search/",
        multilingual="",
        note="令和5年11月改定冊子の住民向け分別区分を、令和8年度カレンダーと現行公式ごみページで確認。"),
    "M045": dict(pref="鳥取県", city="日南町", processor="日南町／日野町江府町日南町衛生施設組合／鳥取県西部広域行政管理組合",
        top="https://www.town.nichinan.lg.jp/soshikikarasagasu/kankyouenergyka/gomi_kankyo_pet/1/22079.html",
        guide="https://www.town.nichinan.lg.jp/material/files/group/31/nichinantyou_gomibunbetu202503.pdf",
        current="https://www.town.nichinan.lg.jp/soshikikarasagasu/kankyouenergyka/gomi_kankyo_pet/1/22079.html",
        search="", multilingual="",
        note="町公式が明示する26種類をそのまま採用。令和8年度カレンダーで現行運用を確認。"),
    "M046": dict(pref="鳥取県", city="日野町", processor="日野町／日野町江府町日南町衛生施設組合／鳥取県西部広域行政管理組合",
        top="https://www.town.hino.tottori.jp/2653.htm",
        guide="https://www.town.hino.tottori.jp/secure/43691/2026karendagetumoku.pdf",
        current="https://www.town.hino.tottori.jp/2653.htm",
        search="", multilingual="",
        note="令和8年度カレンダーに実際に表示される12収集ラベルを住民向け主体系として採用。"),
    "M047": dict(pref="鳥取県", city="江府町", processor="江府町／日野町江府町日南町衛生施設組合／鳥取県西部広域行政管理組合",
        top="https://www.town-kofu.jp/2/1/4/9/2/",
        guide="https://www.town-kofu.jp/2/1/4/9/2/",
        current="https://www.town-kofu.jp/2/1/4/9/2/",
        search="https://www.town-kofu.jp/2/1/4/9/2/g103/",
        multilingual="",
        note="現行の家庭ごみ分別表にある19住民向け区分を採用し、令和8年度収集案内の同ページで現行性を確認。"),
    "M048": dict(pref="島根県", city="松江市", processor="松江市",
        top="https://www.city.matsue.lg.jp/kurashi_tetsuzuki/gomi_kankyo_pet/6/index.html",
        guide="https://www.city.matsue.lg.jp/kurashi_tetsuzuki/gomi_kankyo_pet/6/2/7883.html",
        current="https://www.city.matsue.lg.jp/kurashi_tetsuzuki/gomi_kankyo_pet/6/R8gominittei/index.html",
        search="", multilingual="https://www.city.matsue.lg.jp/kurashi_tetsuzuki/gomi_kankyo_pet/6/2/7883.html",
        note="住民向け公式ページの7葉区分を採用し、令和8年度家庭ごみ収集日程で現行性を確認。"),
    "M049": dict(pref="島根県", city="浜田市", processor="浜田市",
        top="https://www.city.hamada.shimane.jp/www/genre/1000170010134/index.html",
        guide="https://www.city.hamada.shimane.jp/www/contents/1001000003096/index.html",
        current="https://www.city.hamada.shimane.jp/www/genre/1773704279895/index.html",
        search="", multilingual="https://www.city.hamada.shimane.jp/www/contents/1521173944629/index.html",
        note="一般家庭向け8区分を採用。古着・古布は2016年収集終了のためCURRENT箱に含めず、令和8年度日程で現行性を確認。"),
    "M050": dict(pref="島根県", city="出雲市", processor="出雲市",
        top="https://www.city.izumo.shimane.jp/www/genre/1179814088744/index.html",
        guide="https://www.city.izumo.shimane.jp/www/contents/1751940594041/index.html",
        current="https://www.city.izumo.shimane.jp/www/genre/1179814088744/index.html",
        search="", multilingual="https://www.city.izumo.shimane.jp/www/contents/1746759657207/index.html",
        note="ごみの分類・処理の流れに示される13住民向け葉区分を採用し、2026年度カレンダー公式導線で現行性を確認。"),
    "M051": dict(pref="島根県", city="益田市", processor="益田市／益田地区広域市町村圏事務組合",
        top="https://www.city.masuda.lg.jp/soshikikarasagasu/fukushikankyobu/kankyoeiseika/2/11/2554.html",
        guide="https://www.city.masuda.lg.jp/soshikikarasagau/fukushikankyobu/kankyoeiseika/2/11/2554.html" if False else "https://www.city.masuda.lg.jp/soshikikarasagasu/fukushikankyobu/kankyoeiseika/2/11/2554.html",
        current="https://www.city.masuda.lg.jp/kurashi_tetsuzuki/gomi_recycle/kateikaraderugomi/3/9443.html",
        search="", multilingual="",
        note="公式Web本文の住民向け区分を採用。資源類は実際に別々に出す5葉へ分け、2026年度収集案内で現行性を確認。"),
    "M052": dict(pref="島根県", city="大田市", processor="大田市",
        top="https://www.city.oda.lg.jp/ohda_city/city_organization/33/38/gomi-risaikuru/2028/9495",
        guide="https://www.city.oda.lg.jp/ohda_city/city_organization/33/38/gomi-risaikuru/2028/9495",
        current="https://www.city.oda.lg.jp/ohda_city/city_purpose/138/9407",
        search="", multilingual="",
        note="令和8年度カレンダーで住民が選ぶ資源A/B/C・プラ・可燃・不燃・不燃粗大の7区分を採用。"),
    "M053": dict(pref="島根県", city="安来市", processor="安来市",
        top="https://www.city.yasugi.shimane.jp/kurashi/gomi/gomi-recycle/tebiki.html",
        guide="https://www.city.yasugi.shimane.jp/kurashi/gomi/gomi-recycle/tebiki.html",
        current="https://www.city.yasugi.shimane.jp/kurashi/gomi/gomi-recycle/calendar.html",
        search="", multilingual="",
        note="令和7年2月改訂のごみ分別手引き16葉区分を採用し、令和8年度カレンダーで現行性を確認。"),
}

source_specs = {
    "M044": [
        ("冊子 ごみの分け方と出し方（令和5年11月改定）","自治体公式Webページ",municipality_specs["M044"]["guide"],"2026-03-25","不燃・資源・有害・可燃・粗大・収集外の住民向け索引"),
        ("令和8年度ごみ収集カレンダー","自治体公式Webページ",municipality_specs["M044"]["current"],"2026-03-11","現行分別体系の収集運用確認"),
        ("スプレー缶・カセットガス・ライターの廃棄について","自治体公式Webページ","https://www.houki-town.jp/new1/10/12/gomi/6/2/","現行","不燃収集日の危険物条件")],
    "M045": [
        ("日南町ごみ分別表（令和7年3月現在）","自治体公式PDF",municipality_specs["M045"]["guide"],"2025-03","町公式26種類・処理困難物"),
        ("令和8年度上半期ごみ収集カレンダー","自治体公式Webページ",municipality_specs["M045"]["current"],"2026-03-09","現在26種類で収集していることの明示")],
    "M046": [
        ("令和8年度ごみ収集カレンダー 月・木地区版","自治体公式PDF",municipality_specs["M046"]["guide"],"2026","12住民向け収集ラベル・前処理・充電式小型家電注意"),
        ("ごみ","自治体公式Webページ",municipality_specs["M046"]["current"],"2026","令和8年度カレンダー・ごみ分別アプリへの現行公式導線"),
        ("ごみ分別アプリ さんあ～る","自治体公式Webページ","https://www.town.hino.tottori.jp/4352.htm","現行","分別方法検索の公式案内")],
    "M047": [
        ("家庭ごみの出し方・家庭ごみ分別表","自治体公式Webページ",municipality_specs["M047"]["guide"],"現行","19住民向け分別区分・収集処理不可・令和8年度日程導線"),
        ("ごみ分別検索（50音順）","自治体公式Webページ",municipality_specs["M047"]["search"],"現行","品目別条件の補助根拠")],
    "M048": [
        ("ごみの分別区分と出し方","自治体公式Webページ",municipality_specs["M048"]["guide"],"2025-01-24","もやせる・金属・資源4葉・粗大の住民向け体系"),
        ("令和8年度家庭ごみ収集日程","自治体公式Webページ",municipality_specs["M048"]["current"],"2026","現行収集体系"),
        ("家庭ごみの分別区分と出し方 索引","自治体公式Webページ","https://www.city.matsue.lg.jp/kurashi_tetsuzuki/gomi_kankyo_pet/6/2/index.html","現行","水銀・電池・スプレー缶・収集しないごみの公式導線")],
    "M049": [
        ("ごみの種類と分け方、出し方（一般家庭）","自治体公式Webページ",municipality_specs["M049"]["guide"],"2018-04-01","一般家庭8分別・粗大・収集不可・旧古着収集終了"),
        ("令和8年度家庭ごみ収集日程表","自治体公式Webページ",municipality_specs["M049"]["current"],"2026-03-17","5地域の現行収集運用"),
        ("ごみの分け方・出し方 索引","自治体公式Webページ","https://www.city.hamada.shimane.jp/www/genre/1000170010135/index.html","2026","電池・小型充電式電池等の現行追加案内")],
    "M050": [
        ("ごみの分類・処理の流れ","自治体公式Webページ",municipality_specs["M050"]["guide"],"2025-07-07","家庭ごみ13葉区分・資源化ルート"),
        ("ごみ・リサイクル","自治体公式Webページ",municipality_specs["M050"]["current"],"2026","2026年度ごみ収集カレンダー・最新ガイドへの公式導線"),
        ("出雲市ごみの分け方・出し方ガイドブック","自治体公式Webページ",municipality_specs["M050"]["multilingual"],"2025-11-11","日本語・多言語最新版ガイド")],
    "M051": [
        ("ごみの分別について・ごみの分別大図鑑","自治体公式Webページ",municipality_specs["M051"]["guide"],"2023-05-12","燃やせる・プラ・埋立・資源5葉・家電金属・発泡・廃油・木製家具等"),
        ("2026年度 資源・ごみ収集日について","自治体公式Webページ",municipality_specs["M051"]["current"],"2026-03-02","現行収集運用・分別大図鑑への導線")],
    "M052": [
        ("ごみの分け方・出し方（ガイドブック）","自治体公式Webページ",municipality_specs["M052"]["guide"],"現行","資源A/B/C・プラ・可燃・不燃・不燃粗大の住民向け体系"),
        ("令和8年度 資源物・ごみカレンダー","自治体公式Webページ",municipality_specs["M052"]["current"],"2026","A/B/C・プラ・可燃・不燃の現行収集運用"),
        ("ごみの自己搬入について","自治体公式Webページ","https://www.city.oda.lg.jp/ohda_city/city_organization/33/38/gomi-risaikuru/2028/zikohan/","現行","収集処理不可・不燃粗大・自己搬入条件")],
    "M053": [
        ("ごみの出し方（ごみ分別の手引き・令和7年2月改訂）","自治体公式Webページ",municipality_specs["M053"]["guide"],"2025-02","燃やす・プラ・PET・びん・金属・缶・紙類・衣類・蛍光管・板ガラス・埋立・粗大・収集外"),
        ("令和8年度ごみ収集カレンダー","自治体公式Webページ",municipality_specs["M053"]["current"],"2026","現行収集運用・雑がみ収集頻度変更")],
}

categories=[]
def add(mid,name,rep,*,source=1,locator="分別区分見出し",ui="SORT_BUCKET",level="PRIMARY",channel="CURBSIDE",forbidden=NOT_STATED,fallback=NOT_STATED,prep=NOT_STATED,bag="",size="",bulky="FALSE",excluded="FALSE",note=""):
    categories.append({"municipality_id":mid,"自治体正式名称":name,"category_group":name,"parent_name":"","classification_level":level,"collection_channel":channel,"代表品目":rep,"入れてはいけない物":forbidden,"適用条件":"","条件外の扱い":fallback,"出す前の処理":prep,"袋・容器のルール":bag,"サイズ・条件":size,"粗大ごみ扱いか":bulky,"予約が必要か":"FALSE","有料か":"FALSE","料金ルール":"","自治体収集外か":excluded,"注意事項":note,"source_index":str(source),"出典ページ・該当箇所":locator,"ui_role":ui})
def excluded(mid,name,rep,*,source=1,locator="収集できないごみ"):
    add(mid,name,rep,source=source,locator=locator,ui="EXCLUDED_NOTICE",level="EXCLUDED",channel="NOT_COLLECTED",excluded="TRUE",fallback="販売店・メーカー・専門業者等の公式案内に従う",prep="受入先の指示に従う")

# M044 伯耆町 — booklet headings; resource sub-headings are resident sorting choices.
add("M044","可燃ごみ","生ごみ・紙くず・可燃性の家庭ごみ",locator="冊子／可燃ごみ",prep="生ごみは水切り",bag="町指定袋")
add("M044","不燃ごみ","金属・陶磁器・ガラス・硬質プラスチック等",locator="冊子／不燃ごみ",prep="割れ物・刃物は危険防止")
add("M044","不燃粗大ごみ","指定袋に入らない大型不燃物",locator="冊子／不燃粗大ごみ",bulky="TRUE")
add("M044","缶・ビン","飲食用缶・びん",locator="冊子／資源ごみ（缶・ビン）",prep="中身を空にして洗う")
add("M044","再生利用ビン","再使用できる指定びん",locator="冊子／資源ごみ（再生利用ビン）")
add("M044","古紙類","新聞・雑誌・段ボール・紙パック等",locator="冊子／資源ごみ（古紙類）",prep="種類別にまとめる")
add("M044","発泡スチロール・軟質プラスチック","発泡スチロール・軟質プラスチック類",locator="冊子／資源ごみ（発泡スチロール・軟質プラスチック）",prep="汚れを落とす")
add("M044","ペットボトル","PETマークのボトル",locator="冊子／資源ごみ（ペットボトル）",prep="キャップとラベルを外し中をすすぐ")
add("M044","布類","衣類・タオル・シーツ類",locator="冊子／布類",prep="袋の口をしばる",bag="布類専用袋等")
add("M044","有害ごみ","乾電池・蛍光管・水銀製品等",locator="冊子／有害ごみ",prep="電池は絶縁し、蛍光管は破損防止")
add("M044","混合粗大ごみ","燃える物と燃えない物の混合大型品",locator="冊子／混合粗大ごみ",ui="REFERENCE_ONLY",channel="DROP_OFF",bulky="TRUE")
excluded("M044","町で収集しないごみ","家電4品目・処理困難物等",locator="冊子／町で収集しないごみ")

# M045 日南町 — exactly 26 categories explicitly numbered by the town.
nichinan = [
("可燃","生ごみ・紙おむつ・ゴム皮革・可燃物",dict(prep="生ごみは水切り。プラスチック製容器のふた・ポンプは不燃",bag="可燃ごみ用指定袋")),
("不燃","金属くず・陶磁器・ガラス・硬質プラスチック",dict(prep="刃物は新聞紙で包む。スプレー缶・ガス缶は使い切る",bag="不燃ごみ用指定袋")),
("不燃性粗大","60cm以上の不燃性粗大",dict(bulky="TRUE",size="概ね60cm以上、2m×1m×1m以内")),
("缶類（資源）","飲食用缶",dict(prep="中身を空にして汚れはすすぐ。キャップは不燃",bag="資源ごみ用指定袋")),
("ビン類（資源）","飲食用・調味料等のびん",dict(prep="中身を空にしてよくすすぐ。ふたは不燃",bag="資源ごみ用指定袋")),
("生きビン（資源）","ビールびん・茶色の一升びん",dict(prep="ラベルは取らず洗ってそのまま出す",bag="資源ごみ用指定袋")),
("ペットボトル（資源）","PETマークのボトル",dict(prep="中を洗う。汚れが落ちない物は可燃。キャップは別回収又は不燃",bag="資源ごみ用指定袋")),
("発泡スチロール（資源）","発泡スチロール・食品トレー",dict(prep="汚れを落とす",bag="資源ごみ用指定袋")),
("軟質プラスチック（資源）","レジ袋・卵パック・豆腐容器・菓子袋等",dict(prep="汚れが落ちない物は可燃",bag="資源ごみ用指定袋")),
("布類（資源）","布・衣類",dict(prep="地区ごとの指定回収場所へ",bag="資源ごみ用指定袋")),
("乾電池・ボタン電池","乾電池・ボタン電池",dict(prep="使い切り、ボタン電池はテープで包む",bag="透明袋")),
("蛍光管","蛍光管",dict(prep="破損しないよう保護",bag="透明袋")),
("水銀含有機器","水銀体温計・水銀血圧計等",dict(prep="デジタル式を除き、破損しないよう保護",bag="透明袋")),
("新聞","新聞・折込広告",dict(prep="品目ごとにひもで結束")),
("ダンボール","段ボール",dict(prep="品目ごとにひもで結束")),
("雑誌","雑誌・本類",dict(prep="品目ごとにひもで結束")),
("牛乳パック","飲料用紙パック",dict(prep="中をすすぎ、開いてひもで結束")),
("紙製容器包装","紙製容器包装",dict(prep="臭い・汚れの強い紙は可燃")),
("小型家電（資源）","携帯電話・デジカメ・PC・電子レンジ・プリンター等",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",prep="電池・バッテリーを外し個人情報を消去")),
("廃食油","家庭の植物性廃食油",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",prep="動物油脂を混ぜない")),
("ペットボトルキャップ","ペットボトルのキャップ",dict(ui="REFERENCE_ONLY",channel="DROP_OFF")),
("ビデオテープ・カセットテープ","ビデオテープ・カセットテープ",dict(ui="REFERENCE_ONLY",channel="DROP_OFF")),
("インクカートリッジ","純正インクカートリッジ",dict(ui="REFERENCE_ONLY",channel="DROP_OFF")),
("小型二次充電池","回収対象マーク付き小型充電式電池",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",prep="端子を絶縁")),
("可燃性粗大及び大型不燃性粗大","木製家具・混合粗大・大型不燃物",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",bulky="TRUE",size="可燃粗大は概ね60cm以上。大型不燃は2m×1m×1m以上")),
("家電4品目","テレビ・エアコン・洗濯機衣類乾燥機・冷蔵庫冷凍庫",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",prep="郵便局でリサイクル券を購入")),
]
for name,rep,extra in nichinan: add("M045",name,rep,locator=f"日南町ごみ分別表／{name}",**extra)
excluded("M045","処理困難物","産業廃棄物・ガレキ・消火器・タイヤ・農薬等",locator="日南町ごみ分別表／処理困難物")

# M046 日野町 — labels actually appearing in the FY2026 calendar.
for name,rep,extra in [
("可燃","生ごみ・ゴム・革製品等",dict(prep="生ごみは十分水切り",bag="町指定袋")),
("不燃","硬いプラスチック・ガラス・陶磁器・金属等",dict(prep="危険物は保護")),
("資源","飲食用びん・缶",dict(prep="水洗い。汚れ・さびは不燃。ふたは不燃")),
("古紙","新聞・雑誌・段ボール・紙パック等",dict(prep="種類別にひもで縛り古紙シール。濡らさない")),
("軟プラ","軟質プラスチック類",dict(prep="町の指定条件に従う")),
("ペットボトル","PETマークのボトル",dict(prep="ラベルとキャップを外し水洗い。汚れた本体は可燃、ラベルは軟プラ、キャップは不燃")),
("布畳","布類・畳",dict(prep="町の指定条件に従う")),
("廃油","家庭の使用済み天ぷら油",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",prep="事業所・店舗の油は不可")),
("蛍光管","蛍光管",dict(prep="破損しないよう保護")),
("電池","単1～単4・9V・コイン電池等",dict(prep="町指定袋。小型充電式電池等は役場等へ")),
("可燃粗大","指定袋に入らない可燃ごみ",dict(bulky="TRUE",size="1m×1m×1.8mまでの町基準")),
("不燃粗大","指定袋に入らない不燃ごみ",dict(bulky="TRUE",size="1m×1m×1.8mまでの町基準")),
]: add("M046",name,rep,locator=f"令和8年度ごみ収集カレンダー／{name}",**extra)
add("M046","充電式小型家電","スマートフォン・モバイルバッテリー等",source=1,locator="令和8年度カレンダー／充電式小型家電",ui="REFERENCE_ONLY",channel="DROP_OFF",prep="可燃・不燃に混ぜず役場建設水道課又は黒坂支所へ")

# M047 江府町 — resident-facing table labels.
for name,rep,extra in [
("可燃ごみ","台所ごみ・汚れのひどい軟質プラ・皮ゴム",dict(prep="生ごみは水切り",bag="町指定可燃ごみ袋")),
("可燃粗大ごみ","木製家具類",dict(bulky="TRUE")),
("不燃ごみ","小型家電・金属・陶磁器・ガラス・硬質プラ等",dict(size="概ね60cm以内")),
("不燃粗大ごみ","大型不燃家庭用品・事務機器等",dict(bulky="TRUE",size="概ね60cm超、1m×1m×2m以下")),
("ビン・缶類","飲食用びん・缶",dict(prep="中身を空にして洗う")),
("ペットボトル","飲料・酒・しょうゆ用PET",dict(prep="町の指定方法で出す")),
("家電リサイクル品","テレビ・エアコン・洗濯機乾燥機・冷蔵庫冷凍庫",dict(ui="REFERENCE_ONLY",channel="BOOKED_PICKUP",prep="必要に応じ郵便局でリサイクル券を購入")),
("紙パック","500ml以上の紙パック",dict(prep="紙製容器包装紙の日に出す")),
("ダンボール","段ボール",dict(prep="まとめて出す")),
("紙製容器包装紙","食品空箱・生活用品空箱・包装・台紙",dict(prep="紙以外を外す")),
("新聞・チラシ","新聞・折込広告",dict(prep="まとめて出す")),
("本・雑誌","古本・古雑誌",dict(prep="まとめて出す")),
("発泡スチロール軟質プラスチック","食品トレー・発泡容器・買物袋・卵パック等",dict(prep="汚れを落とす")),
("ビデオ・カセットテープ類","ビデオテープ・カセットテープ",dict()),
("布類","タオル・衣類・シーツ・布団等",dict()),
("乾電池","乾電池",dict(prep="端子を絶縁")),
("小型充電池","小型充電式電池",dict(prep="端子を絶縁")),
("蛍光管・水銀体温計","蛍光管・水銀体温計",dict(prep="破損しないよう保護")),
("小型家電等","携帯電話・デジカメ・PC・電子レンジ等",dict(ui="REFERENCE_ONLY",channel="DROP_OFF",prep="個人情報を消去し電池を外す")),
]: add("M047",name,rep,locator=f"家庭ごみ分別表／{name}",**extra)
excluded("M047","収集・処理できないごみ","分別されていないごみ・産廃・消火器・タイヤ・土砂等",locator="家庭ごみの出し方／収集・処理できないごみ")

# M048 松江市 — 7 resident-facing leaf choices; 資源 is conceptual parent only.
add("M048","もやせるごみ","生ごみ・紙くず・資源化できない可燃物",locator="家庭から出るごみ／もやせるごみ",bag="市指定袋",prep="生ごみは水切り")
add("M048","金属","金属製品・小型金属類",locator="家庭から出るごみ／金属",bag="市指定袋")
add("M048","古紙・古着","新聞・雑誌・段ボール・古着等",locator="家庭から出るごみ／資源／古紙・古着",prep="古紙は種類別にまとめる")
add("M048","紙製容器包装","紙製の容器包装",locator="家庭から出るごみ／資源／紙製容器包装",bag="市指定袋")
add("M048","プラスチック製容器包装","プラマークの容器包装",locator="家庭から出るごみ／資源／プラスチック製容器包装",bag="市指定袋",prep="中身・汚れを除く")
add("M048","缶・びん・ペットボトル","飲食用缶・びん・PETボトル",locator="家庭から出るごみ／資源／缶・びん・ペットボトル",prep="中身を空にしてすすぐ")
add("M048","粗大ごみ","指定袋に入らない大型家庭ごみ",locator="家庭から出るごみ／粗大ごみ",ui="REFERENCE_ONLY",channel="BOOKED_PICKUP",bulky="TRUE")

# M049 浜田市 — old publication remains current via FY2026 schedule and current official index.
add("M049","燃やせるごみ","生ごみ・紙くず・布革ゴム・プラマークなしプラ等",locator="一般家庭／燃やせるごみ",prep="生ごみは水切り。枝木は指定寸法にする",bag="緑色指定袋")
add("M049","燃やせないごみ","ガラス・陶磁器・金属・電気製品等",locator="一般家庭／燃やせないごみ",prep="割れ物・刃物は危険防止",bag="青色指定袋")
add("M049","危険物・有害物","ライター・スプレー缶・ガス缶・乾電池・水銀体温計等",locator="一般家庭／危険物・有害物",prep="ライター・スプレー缶等は使い切る。穴あけは必須でない",bag="透明・半透明袋等")
add("M049","ペットボトル・プラスチック製容器包装","PETボトル・プラマーク容器包装",locator="一般家庭／ペットボトル・プラスチック製容器包装",prep="軽く水洗い。PETはキャップとラベルを外して同袋へ",bag="水色指定袋")
add("M049","びん","飲料・調味料・食品用びん",locator="一般家庭／びん",prep="軽く水洗いしキャップを外す",bag="オレンジ色指定袋")
add("M049","空缶","アルミ缶・スチール缶・缶詰缶等",locator="一般家庭／空缶",prep="軽く水洗い",bag="灰色指定袋")
add("M049","古紙類","新聞・雑誌広告・段ボール・牛乳パック・雑がみ等",locator="一般家庭／古紙類",prep="種類別にひもで十字に結ぶ。紙パックは洗い切り開き乾燥")
add("M049","粗大ごみ","指定袋に入らない大型可燃・不燃ごみ",locator="一般家庭／粗大ごみ",ui="REFERENCE_ONLY",channel="CURBSIDE",bulky="TRUE",prep="粗大ごみシールを貼付")
excluded("M049","収集できないもの","産業廃棄物・医療系廃棄物・自動車部品・処理困難物等",locator="一般家庭／収集できないもの")

# M050 出雲市 — 13 leaf categories shown in the official flow.
for name,rep,extra in [
("燃えるごみ","可燃性家庭ごみ",dict(prep="市の指定方法に従う")),
("破砕ごみ","破砕処理する不燃・複合ごみ",dict()),
("埋立ごみ","埋立処分する不燃ごみ",dict()),
("粗大ごみ","大型家庭ごみ",dict(bulky="TRUE",ui="REFERENCE_ONLY")),
("飲料用空き缶","飲料用空き缶",dict(prep="中身を空にしてすすぐ")),
("空きびん","飲食用空きびん",dict(prep="中身を空にしてすすぐ")),
("ペットボトル","PETマークのボトル",dict(prep="市の指定方法で出す")),
("使用済筒型乾電池","筒型乾電池",dict(prep="端子を絶縁")),
("使用済蛍光管","蛍光管",dict(prep="破損しないよう保護")),
("古紙","新聞・雑誌・段ボール等",dict(prep="種類別にまとめる")),
("古着","衣類・古着",dict(prep="洗って乾かす")),
("使用済割りばし","使用済み割り箸",dict(ui="REFERENCE_ONLY",channel="DROP_OFF")),
("廃食用油","家庭の使用済み食用油",dict(ui="REFERENCE_ONLY",channel="DROP_OFF")),
]: add("M050",name,rep,locator=f"ごみの分類・処理の流れ／{name}",**extra)

# M051 益田市 — resource parent is split into the five leaf choices residents separate.
add("M051","燃やせるごみ","生ごみ・紙くず・枝木等",locator="ごみの分別区分と出し方／燃やせるごみ",prep="生ごみは水切り。枝木は直径又は厚さ10cm以下、長さ1m以下",bag="指定袋")
add("M051","ステーション収集困難物","布団・毛布・カーペット・畳等の指定品",locator="燃やせるごみ／ステーション収集困難物",ui="REFERENCE_ONLY",channel="BOOKED_PICKUP",bulky="TRUE",prep="電話予約し処理券を貼る")
add("M051","容器包装プラスチックごみ","プラマークの容器包装",locator="ごみの分別区分と出し方／容器包装プラスチックごみ",prep="中身・汚れを除く",bag="指定袋")
add("M051","埋め立てるごみ","陶磁器・ガラス・蛍光灯等",locator="ごみの分別区分と出し方／埋め立てるごみ",prep="蛍光灯・陶磁器・ガラスはできるだけ別袋で危険表示",bag="指定袋")
add("M051","カン類","飲食用缶等",locator="資源類／カン類",prep="中身を空にしてすすぐ",bag="透明・半透明袋")
add("M051","びん類","飲食用びん",locator="資源類／びん類",prep="無色・茶色・その他色に分ける",bag="透明・半透明袋")
add("M051","古紙類","新聞・段ボール・雑紙雑誌",locator="資源類／古紙類",prep="新聞・段ボール・雑紙雑誌に分けて紙ひもで束ねる")
add("M051","ペットボトル","PETマークのボトル",locator="資源類／ペットボトル",prep="市の指定方法で出す",bag="透明・半透明袋")
add("M051","紙パック","飲料用紙パック",locator="資源類／紙パック",prep="ひもで束ねる。注ぎ口キャップは容器包装プラ")
add("M051","家電製品・金属類","家電製品・金属類・小型金属・刃物",locator="ごみの分別区分と出し方／家電製品・金属類",prep="刃物は刃を包装し危険表示",bag="小型品は透明・半透明袋")
add("M051","発泡スチロール類","発泡スチロール",locator="ごみの分別区分と出し方／発泡スチロール類",prep="汚れの程度で分ける。ひどい汚れは埋立")
add("M051","廃食用油","家庭の植物性廃食用油",locator="ごみの分別区分と出し方／廃食用油",ui="REFERENCE_ONLY",channel="DROP_OFF",prep="植物性油のみ。異物を混ぜない")
add("M051","木製家具","たんす・机等の木製家具",locator="ごみの分別区分と出し方／木製家具",ui="REFERENCE_ONLY",channel="BOOKED_PICKUP",bulky="TRUE",prep="電話申込又はリサイクルプラザへ直接搬入")

# M052 大田市 — A/B/C groups are the actual resident calendar choices.
add("M052","資源物Aグループ","アルミ缶・スチール缶・ガラス瓶",locator="ごみの分類と出し方／資源物Aグループ",prep="中身を空にしてすすぐ")
add("M052","資源物Bグループ","ペットボトル・廃乾電池・充電式電池・水銀体温計",locator="ごみの分類と出し方／資源物Bグループ",prep="電池類は端子を絶縁")
add("M052","資源物Cグループ","段ボール・新聞折込広告・その他の紙・古布・紙パック",locator="ごみの分類と出し方／資源物Cグループ",prep="紙類は種類別にまとめる")
add("M052","プラスチック製容器包装","プラマークの容器包装",locator="ごみの分類と出し方／プラスチック製容器包装",prep="中身・汚れを除く",bag="指定袋")
add("M052","燃やせるごみ","生ごみ・紙くず等の可燃物",locator="ごみの分類と出し方／燃やせるごみ",prep="生ごみは水切り",bag="指定袋")
add("M052","家庭不燃ごみ","家庭の不燃ごみ",locator="ごみの分類と出し方／家庭不燃ごみ",bag="指定袋")
add("M052","家庭不燃粗大ごみ","指定袋に入らない不燃大型品",locator="ごみの分類と出し方／家庭不燃粗大ごみ",ui="REFERENCE_ONLY",channel="CURBSIDE",bulky="TRUE",size="2m×1m×1m以内",prep="処理券を貼る又は直接搬入")
excluded("M052","市で収集・処理できないごみ","家電4品目・処理困難物等",source=3,locator="ごみの自己搬入について／市では収集も処理もできないごみ")

# M053 安来市 — manual index leaf categories.
for name,rep,extra in [
("燃やすごみ","生ごみ・紙くず・草類等",dict(prep="生ごみは水切り",bag="市指定袋")),
("プラスチック類","プラスチックだけでできた物・指定プラ類",dict(prep="中身・汚れを除く")),
("ペットボトル","PETマークのボトル",dict(prep="キャップ・ラベルを外す")),
("ビン類（飲食用）","飲食用びん",dict(prep="中をすすぐ")),
("金属類","金属容器・工具等",dict()),
("缶類（飲料用）","アルミ缶・スチール缶",dict(prep="つぶさず洗って出す")),
("雑紙（その他の紙類）","封筒・包装紙等の雑がみ",dict(prep="紙以外を取り除く")),
("本（書籍）・雑誌・冊子","本・漫画・週刊誌・パンフレット等",dict(prep="種類別にまとめる")),
("ダンボール","段ボール",dict(prep="紙ひも等でまとめる")),
("牛乳パック","飲料用紙パック",dict(prep="洗って切り開き乾かす")),
("新聞・新聞チラシ","新聞・折込チラシ",dict(prep="まとめて出す")),
("衣類","衣類・古着",dict(prep="洗って乾かす")),
("蛍光管・水銀体温計","蛍光管・水銀体温計",dict(prep="破損しないよう保護")),
("板ガラス","板ガラス",dict(prep="破損防止")),
("埋立ごみ","陶磁器・割れびん・鏡等",dict(prep="危険物は保護")),
("粗大ごみ","指定袋等に入らない大型家庭ごみ",dict(ui="REFERENCE_ONLY",channel="BOOKED_PICKUP",bulky="TRUE")),
]: add("M053",name,rep,locator=f"ごみ分別の手引き／{name}",**extra)
excluded("M053","市では収集・処理しないもの","家電リサイクル法対象品・パソコン・専門業者処理品",locator="ごみ分別の手引き／市では収集・処理しないもの")


def ensure_registry():
    path=MASTER/"02_official_domain_registry.csv"; fields,rows=read_csv(path); fields=fields or REGISTRY_FIELDS
    existing={(r.get("municipality_id"),r.get("host")) for r in rows}
    for mid,specs in source_specs.items():
        for spec in specs:
            host=(urlparse(spec[2]).hostname or "").lower(); key=(mid,host)
            if host and key not in existing:
                rows.append({"municipality_id":mid,"host":host,"authority_type":"MUNICIPAL_DOMAIN","authority_name":municipality_specs[mid]["city"],"verification_url":municipality_specs[mid]["top"],"verified_date":CHECKED,"notes":"Batch 05 official municipal source host"}); existing.add(key)
    rows.sort(key=lambda r:(r.get("municipality_id",""),r.get("host",""))); write_csv(path,fields,rows)


def build_sources():
    rows=[]
    for mid,specs in source_specs.items():
        for i,(title,kind,url,updated,used) in enumerate(specs,1):
            rows.append({"municipality_id":mid,"source_id":f"S-{mid}-{i:02d}","資料名":title,"資料種別":kind,"公式URL":url,"発行主体":municipality_specs[mid]["city"],"対象年度":"令和8年度","ページ更新日":updated,"取得確認日":CHECKED,"使用した情報":used,"優先度":str(i),"現行性":"現行","備考":"","official_verified":"","official_basis":"","official_linking_url":""})
    return rows


def build_categories():
    by_mid={}
    for raw in categories: by_mid.setdefault(raw["municipality_id"],[]).append(raw)
    if set(by_mid)!=TARGETS: raise ValueError(f"Batch05 target mismatch {set(by_mid)}")
    rows=[]
    for mid,raws in by_mid.items():
        name_to_id={r["自治体正式名称"]:f"C-{mid}-{i:02d}" for i,r in enumerate(raws,1)}
        for i,raw in enumerate(raws,1):
            sidx=int(raw["source_index"]); src=source_specs[mid][sidx-1]
            rows.append({"municipality_id":mid,"category_id":name_to_id[raw["自治体正式名称"]],"自治体正式名称":raw["自治体正式名称"],"category_group":raw["category_group"],"parent_category_id":"","classification_level":raw["classification_level"],"表示順":str(i),"collection_channel":raw["collection_channel"],"代表品目":raw["代表品目"],"入れてはいけない物":raw["入れてはいけない物"],"適用条件":"","条件外の扱い":raw["条件外の扱い"],"出す前の処理":raw["出す前の処理"],"袋・容器のルール":raw["袋・容器のルール"],"サイズ・条件":raw["サイズ・条件"],"粗大ごみ扱いか":raw["粗大ごみ扱いか"],"予約が必要か":"FALSE","有料か":"FALSE","料金ルール":"","自治体収集外か":raw["自治体収集外か"],"注意事項":raw["注意事項"],"source_id":f"S-{mid}-{sidx:02d}","出典URL":src[2],"出典ページ・該当箇所":raw["出典ページ・該当箇所"],"確認日":CHECKED,"ui_role":raw["ui_role"],"rule_status":"CURRENT","effective_from":"","effective_to":""})
    return rows


def optional_status(url):
    return ("CHECKED_PRESENT",f"URL:{url}; checked:{CHECKED}") if url else ("NOT_CHECKED","")


def build_municipalities():
    rows=[]
    for mid,spec in municipality_specs.items():
        ss,se=optional_status(spec["search"]); ms,me=optional_status(spec["multilingual"])
        rows.append({"municipality_id":mid,"都道府県":spec["pref"],"市町村":spec["city"],"実装区分":"中国5県全市町村","ごみ処理主体":spec["processor"],"自治体ごみトップURL":spec["top"],"分別ガイドURL":spec["guide"],"品目検索URL":spec["search"],"やさしい日本語URL":"","多言語資料URL":spec["multilingual"],"対象年度":"令和8年度","最終確認日":CHECKED,"確認ステータス":"QA_REQUIRED","備考":spec["note"],"official_category_count":"","reviewed_category_count":"","category_count_basis":"住民が家庭ごみ排出時に選択する公式分別区分を全件照合し、現年度カレンダー・現行公式導線で稼働を確認。処理施設側だけの分類は独立SORT_BUCKETへ昇格させない。","category_count_verified":"TRUE","category_count_check_status":"MANUAL_INDEX_REVIEW","category_count_review_id":f"CR-{mid}-CATEGORY-COVERAGE","category_count_reviewed_date":CHECKED,"category_count_reviewed_by":REVIEWER,"search_service_check_status":ss,"search_service_check_evidence":se,"easy_japanese_check_status":"NOT_CHECKED","easy_japanese_check_evidence":"","multilingual_check_status":ms,"multilingual_check_evidence":me})
    return rows


def build_review_evidence():
    rows=[]
    for mid,specs in source_specs.items():
        for i,src in enumerate(specs,1):
            rows.append({"review_evidence_id":f"CRE-{mid}-{i:02d}","review_id":f"CR-{mid}-CATEGORY-COVERAGE","municipality_id":mid,"source_id":f"S-{mid}-{i:02d}","locator":src[4],"evidence_role":"PRIMARY_INDEX" if i==1 else "SUPPLEMENTAL_INDEX","notes":f"{CHECKED} Batch 05 resident-facing category completeness review"})
    return rows


def main():
    if set(municipality_specs)!=TARGETS or set(source_specs)!=TARGETS: raise ValueError("Batch05 spec target mismatch")
    ensure_registry(); OUT.mkdir(parents=True,exist_ok=True); p="batch_05_"
    write_csv(OUT/f"{p}municipalities.csv",MUNICIPALITY_FIELDS,build_municipalities())
    write_csv(OUT/f"{p}categories.csv",CATEGORY_FIELDS,build_categories())
    write_csv(OUT/f"{p}sources.csv",SOURCE_FIELDS,build_sources())
    write_csv(OUT/f"{p}qa.csv",QA_FIELDS,[])
    write_csv(OUT/f"{p}item_mapping.csv",MAPPING_FIELDS,[])
    write_csv(OUT/f"{p}item_coverage.csv",COVERAGE_FIELDS,[])
    write_csv(OUT/f"{p}category_review_evidence.csv",CATEGORY_REVIEW_EVIDENCE_FIELDS,build_review_evidence())
    counts=migrate_batch_dir(OUT)
    print(" ".join(f"{k}={v}" for k,v in counts.items()))

if __name__=="__main__": main()
