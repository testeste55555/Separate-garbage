#!/usr/bin/env python3
"""Build Batch 04 (M034-M043) from resident-facing current official sources.

Schema v1.2.4 semantics:
- store the official categories residents actually choose when disposing household waste;
- use current calendars/notices as current-operation evidence;
- never invent details absent from cited source;
- preserve regional wording and rules rather than normalizing them.
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
OUT = ROOT / "data" / "research" / "batches" / "batch_04"
CHECKED = "2026-08-19"
REVIEWER = "OPENAI_CHATGPT_BATCH04_REVIEW"
NOT_STATED = "NOT_STATED_IN_CITED_SOURCE"
REGISTRY_FIELDS = [
    "municipality_id", "host", "authority_type", "authority_name",
    "verification_url", "verified_date", "notes",
]
TARGETS = {f"M{i:03d}" for i in range(34, 44)}

municipality_specs = {
    "M034": dict(pref="鳥取県", city="若桜町", processor="若桜町／鳥取県東部広域行政管理組合",
        top="https://www.town.wakasa.tottori.jp/soshikikarasagasu/zeimujuminka/gyoumuannai/chominka/1/1/1/574.html",
        guide="https://www.town.wakasa.tottori.jp/soshikikarasagasu/zeimujuminka/gyoumuannai/chominka/1/1/1/574.html",
        current="https://www.town.wakasa.tottori.jp/soshikikarasagasu/zeimujuminka/gyoumuannai/chominka/1/1/1/574.html",
        note="住民向け分別ページの8区分と収集不可案内を照合。令和6年4月変更を反映。"),
    "M035": dict(pref="鳥取県", city="智頭町", processor="智頭町／鳥取県東部広域行政管理組合",
        top="https://www1.town.chizu.tottori.jp/chizu/zeimu/gomi/bunbetsu/bunrui/",
        guide="https://www1.town.chizu.tottori.jp/chizu/zeimu/gomi/bunbetsu/bunrui/",
        current="https://www1.town.chizu.tottori.jp/chizu/zeimu/gomi/p624-copy-2/",
        note="公式分類ページ8区分を、令和8年度収集カレンダーで現行運用確認。"),
    "M036": dict(pref="鳥取県", city="八頭町", processor="八頭町／鳥取県東部広域行政管理組合",
        top="https://www.town.yazu.tottori.jp/site/gomi/",
        guide="https://www.town.yazu.tottori.jp/site/gomi/1048.html",
        current="https://www.town.yazu.tottori.jp/site/gomi/1047.html",
        note="令和6年4月版手引き8区分を、令和8年度カレンダーと現行公式ごみサイトで確認。"),
    "M037": dict(pref="鳥取県", city="三朝町", processor="三朝町／鳥取中部ふるさと広域連合",
        top="https://www.town.misasa.tottori.jp/315/319/324/764/1901/1906/",
        guide="https://www.town.misasa.tottori.jp/315/319/324/764/1901/1906/",
        current="https://www.town.misasa.tottori.jp/315/319/324/764/1901/1906/20959.html",
        note="令和8年度前期収集日程の住民向け11ラベルを採用。充電式電池の有害ごみ化を反映。"),
    "M038": dict(pref="鳥取県", city="湯梨浜町", processor="湯梨浜町／鳥取中部ふるさと広域連合",
        top="https://www.yurihama.jp/soshiki/4/1431.html",
        guide="https://www.yurihama.jp/soshiki/4/1431.html",
        current="https://www.yurihama.jp/soshiki/4/26990.html",
        note="住民向け冊子の12区分を採用し、令和8年度日程と有害ごみ現行運用を照合。"),
    "M039": dict(pref="鳥取県", city="琴浦町", processor="琴浦町／鳥取中部ふるさと広域連合",
        top="https://www.town.kotoura.tottori.jp/docs/2012121300677/",
        guide="https://www.town.kotoura.tottori.jp/docs/2012121300677/",
        current="https://www.town.kotoura.tottori.jp/docs/2025030400055/",
        note="2026年7月更新の家庭ごみページ13区分と令和8年度日程を照合。"),
    "M040": dict(pref="鳥取県", city="北栄町", processor="北栄町／鳥取中部ふるさと広域連合",
        top="https://www.e-hokuei.net/soshiki/5/1341.html",
        guide="https://www.e-hokuei.net/soshiki/5/1341.html",
        current="https://www.e-hokuei.net/soshiki/5/1337.html",
        note="住民向け12区分を採用。令和8年度から充電池を有害ごみとして新規回収する現行変更を反映。"),
    "M041": dict(pref="鳥取県", city="日吉津村", processor="日吉津村",
        top="https://www.hiezu.jp/%E5%AE%B6%E5%BA%AD%E3%82%B4%E3%83%9F%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6/",
        guide="https://www.hiezu.jp/%E5%90%84%E8%AA%B2%E4%B8%80%E8%A6%A7/%E4%BD%8F%E6%B0%91%E8%AA%B2/%E7%92%B0%E5%A2%83%E3%83%BB%E3%82%B4%E3%83%9F/%E3%82%B4%E3%83%9F/%E3%82%B4%E3%83%9F%E3%81%AE%E5%88%86%E3%81%91%E6%96%B9%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6/",
        current="https://www.hiezu.jp/%E3%82%B4%E3%83%9F%E3%81%AE%E5%8F%8E%E9%9B%86%E6%97%A5%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6/",
        note="現在の収集案内で住民が選択する7ラベルを採用。詳細50音表は品目条件の補助根拠。"),
    "M042": dict(pref="鳥取県", city="大山町", processor="大山町／鳥取県西部広域行政管理組合",
        top="https://www.daisen.jp/10/4/4/m855/n462/",
        guide="https://www.daisen.jp/user/filer_public/b1/61/b1611d62-e336-4068-8123-b4ec28cb25f6/gomi-funbetu-tebiki-kaiteiban.pdf",
        current="https://www.daisen.jp/10/4/4/r100/s542/",
        note="令和8年1月改訂版手引きを主根拠とし、令和8年4月変更・現行日程を反映。廃止2区分は除外。"),
    "M043": dict(pref="鳥取県", city="南部町", processor="南部町／南部町・伯耆町清掃施設管理組合",
        top="https://www.town.nanbu.tottori.jp/admin/chouminseikatsuka/gomi1/",
        guide="https://www.town.nanbu.tottori.jp/admin/chouminseikatsuka/gomi1/g141/",
        current="https://www.town.nanbu.tottori.jp/admin/chouminseikatsuka/gomi1/y145/",
        note="住民向け分別表の公式区分を令和8年度カレンダーで現行確認。"),
}

source_specs = {
    "M034": [("ごみの分別","自治体公式Webページ",municipality_specs["M034"]["guide"],"2024-06-13","住民向け8分別区分・前処理・収集不可品")],
    "M035": [
        ("家庭ごみの分類","自治体公式Webページ",municipality_specs["M035"]["guide"],"現行","住民向け8分別区分と収集不可導線"),
        ("令和8年度ごみ収集カレンダー","自治体公式Webページ",municipality_specs["M035"]["current"],"2026","現行運用確認"),
        ("可燃ごみ・資源ごみ・プラスチックごみ・ペットボトル","自治体公式Webページ","https://www1.town.chizu.tottori.jp/chizu/zeimu/gomi/bunbetsu/gomi01/","現行","4区分の具体ルール"),
        ("小型破砕ごみ・乾電池類・大型資源ごみ・有害ごみ","自治体公式Webページ","https://www1.town.chizu.tottori.jp/chizu/zeimu/gomi/bunbetsu/gomi02/","現行","4区分の具体ルール")],
    "M036": [
        ("家庭ごみの分別表","自治体公式Webページ",municipality_specs["M036"]["guide"],"2025-06-02","令和6年4月版手引き・50音表への公式導線"),
        ("令和8年度家庭ごみ収集カレンダー","自治体公式Webページ",municipality_specs["M036"]["current"],"2026-04-01","現行収集体系"),
        ("令和6年4月から分別区分が一部変わります","自治体公式Webページ","https://www.town.yazu.tottori.jp/site/gomi/7845.html","2024-01-30","有害ごみ新設・白色トレイ統合・PET変更")],
    "M037": [
        ("ごみの区分と出し方","自治体公式Webページ",municipality_specs["M037"]["guide"],"現行","住民向け分別・広域手引きへの公式導線"),
        ("令和8年度前期ごみ収集日程表","自治体公式Webページ",municipality_specs["M037"]["current"],"2026-02-13","11収集ラベル・充電池有害ごみ化")],
    "M038": [
        ("ごみの分別と出し方","自治体公式Webページ",municipality_specs["M038"]["guide"],"2022-04-01","住民向け冊子12区分への公式索引"),
        ("令和8年度ごみ収集日程","自治体公式Webページ",municipality_specs["M038"]["current"],"2026-02-10","現行12区分・有害ごみ運用")],
    "M039": [
        ("家庭ごみの分け方・出し方","自治体公式Webページ",municipality_specs["M039"]["guide"],"2026-07-06","住民向け13分別区分・詳細"),
        ("令和8年度ごみ収集日程表","自治体公式Webページ",municipality_specs["M039"]["current"],"2026-07-02","現行運用確認")],
    "M040": [
        ("ごみの出し方など","自治体公式Webページ",municipality_specs["M040"]["guide"],"2026-01-06","住民向け手引き・日程への公式索引"),
        ("ごみ・リサイクル","自治体公式Webページ",municipality_specs["M040"]["current"],"2026-04-13","現行ごみ体系・有害ごみ導線"),
        ("令和8年度施政方針","自治体公式Webページ","https://www.e-hokuei.net/soshiki/2/4862.html","2026","令和8年度から充電池を有害ごみとして回収")],
    "M041": [
        ("ゴミの分け方について","自治体公式Webページ",municipality_specs["M041"]["guide"],"現行","分別ポスター・詳細50音表への公式索引"),
        ("ごみの収集日について","自治体公式Webページ",municipality_specs["M041"]["current"],"現行","住民が排出時に選択する7収集ラベル"),
        ("家庭ゴミの分け方詳細版","自治体公式PDF","https://www.hiezu.jp/user/filer_public/68/02/6802772b-964a-4a93-8ce0-9594e1ca9fa8/r4gomifen-kefang-zao-jian-biao.pdf","令和5年3月改定","品目別分別区分・収集不可")],
    "M042": [
        ("ごみ分別収集の手引き 改訂版（令和8年1月～）","自治体公式PDF",municipality_specs["M042"]["guide"],"2026-01","住民向け分別区分・前処理・収集外"),
        ("令和8年4月からごみの出し方を一部変更","自治体公式Webページ",municipality_specs["M042"]["current"],"2026-03-18","紙製容器包装・指定びん廃止、発泡スチロール条件変更"),
        ("令和8年度ごみ収集日程表","自治体公式Webページ","https://www.daisen.jp/10/4/4/m855/n462/x191/","2026-05-25","現行運用確認"),
        ("電池の出し方","自治体公式Webページ","https://www.daisen.jp/10/4/4/r100/m165/","2026-02-19","乾電池・充電池の現行分別")],
    "M043": [
        ("南部町ごみの分け方・出し方","自治体公式Webページ",municipality_specs["M043"]["guide"],"令和7年度改訂","住民向け分別収集の区分見出し"),
        ("令和8年度ごみ収集カレンダー・分別表","自治体公式Webページ",municipality_specs["M043"]["current"],"2026","現行運用確認")],
}

categories=[]
def add(mid,name,rep,*,source=1,locator="分別区分見出し",ui="SORT_BUCKET",level="PRIMARY",channel="CURBSIDE",forbidden=NOT_STATED,fallback=NOT_STATED,prep=NOT_STATED,bag="",size="",bulky="FALSE",excluded="FALSE",note=""):
    categories.append({"municipality_id":mid,"自治体正式名称":name,"category_group":name,"parent_name":"","classification_level":level,"collection_channel":channel,"代表品目":rep,"入れてはいけない物":forbidden,"適用条件":"","条件外の扱い":fallback,"出す前の処理":prep,"袋・容器のルール":bag,"サイズ・条件":size,"粗大ごみ扱いか":bulky,"予約が必要か":"FALSE","有料か":"FALSE","料金ルール":"","自治体収集外か":excluded,"注意事項":note,"source_index":str(source),"出典ページ・該当箇所":locator,"ui_role":ui})
def excluded(mid,name,rep,*,source=1,locator="収集できないごみ"):
    add(mid,name,rep,source=source,locator=locator,ui="EXCLUDED_NOTICE",level="EXCLUDED",channel="NOT_COLLECTED",excluded="TRUE",fallback="販売店・メーカー・専門業者等の公式案内に従う",prep="受入先の指示に従う")

add("M034","可燃ゴミ","生ごみ・紙くず・革ゴム・やわらかいプラスチック",locator="ごみの分別／可燃ゴミ",prep="生ごみは十分水切り。不燃物や付属金属を外す",bag="町指定袋")
add("M034","缶・ビン","飲食用缶・びん",locator="ごみの分別／缶・ビン",prep="中身を使い切り軽く洗い、ふたを外す",bag="専用カゴへ直接")
add("M034","プラスチックごみ","プラスチック・ビニール製品・白色トレイ",locator="ごみの分別／プラスチックごみ",prep="汚れを軽く水洗いし、異素材を外す",bag="無色透明の中身が見える袋")
add("M034","ペットボトル","PETマークのボトル",locator="ごみの分別／ペットボトル",prep="キャップとラベルを外し水洗い。つぶしても可",bag="専用回収容器")
add("M034","小型破砕ごみ","ガラス・刃物・電球・小型不燃物",locator="ごみの分別／小型破砕ごみ",prep="危険物は透明袋に入れ「キケン」と表示",size="50cm未満")
add("M034","大型資源ごみ","50cm以上の不燃物・自転車・ストーブ等",locator="ごみの分別／大型資源ごみ",bulky="TRUE",size="原則50cm以上")
add("M034","乾電池類","乾電池・ボタン電池・小型充電式電池・蛍光管等",locator="ごみの分別／乾電池類",prep="電池は端子を絶縁。蛍光管は破損防止")
add("M034","有害ごみ","スプレー缶・カセットボンベ・ライター・電池を外せない充電式製品",locator="ごみの分別／有害ごみ",prep="スプレー缶等は中身を使い切る。穴あけ不要")
excluded("M034","収集できないゴミ","家電4品目・処理困難物等",locator="ごみの分別／収集できないゴミ")

add("M035","可燃ごみ","生ごみ・紙くず・革ゴム等",source=3,locator="可燃ごみ",prep="生ごみは水切り",bag="町指定袋")
add("M035","資源ごみ","飲食用缶・びん",source=3,locator="資源ごみ",prep="ふたを外し、さっと洗う",bag="専用容器へ直接")
add("M035","プラスチックごみ","50cm以下のプラスチック・ビニール製品",source=3,locator="プラスチックごみ",prep="汚れを軽く水洗いし異素材を外す",bag="中身が見える袋")
add("M035","ペットボトル","PETマークのボトル",source=3,locator="ペットボトル",prep="キャップとラベルを外し水洗い")
add("M035","小型破砕ごみ","50cm未満の小型不燃物・割れびん・刃物",source=4,locator="小型破砕ごみ",prep="危険物は透明袋で保護",size="50cm未満")
add("M035","乾電池類","乾電池・水銀製品・蛍光管・ボタン電池・小型充電式電池",source=4,locator="乾電池類",prep="電池は両極を絶縁。蛍光管はケース又は新聞紙で保護")
add("M035","大型資源ごみ","50cm以上1.8m未満の不燃物",source=4,locator="大型資源ごみ",prep="ストーブは油を抜き、電池を外す",bulky="TRUE",size="50cm以上1.8m未満")
add("M035","有害ごみ","スプレー缶・カセットボンベ・ライター・電池を外せない充電式製品",source=4,locator="有害ごみ",prep="スプレー缶等は中身を使い切る")
excluded("M035","収集できないごみ","特定家電・処理困難物等",source=1,locator="家庭ごみの分類／収集できないごみ")

add("M036","可燃ごみ","生ごみ・紙くず・革ゴム等",locator="令和6年4月版手引き／可燃ごみ",prep="生ごみは水切り",bag="町指定袋")
add("M036","缶・ビン","飲食用缶・びん",locator="令和6年4月版手引き／缶・ビン",prep="ふたを外し中を洗う",bag="専用カゴ")
add("M036","プラスチックごみ","プラスチック製品・白色/色付きトレイ",source=3,locator="変更点2／白色トレイをプラスチックごみへ",prep="軽く水洗い",bag="町指定袋")
add("M036","ペットボトル","PETマークのボトル",source=3,locator="変更点3／ペットボトル",prep="キャップとラベルを外し水洗い。つぶしても可")
add("M036","小型破砕ごみ","50cm未満の小型不燃物・刃物・ガラス",locator="家庭ごみ手引き／小型破砕ごみ",prep="危険物は透明袋に入れキケン表示",size="50cm未満")
add("M036","大型資源ごみ","50cm以上1.8m未満の不燃物",locator="家庭ごみ手引き／大型資源ごみ",bulky="TRUE",size="50cm以上1.8m未満")
add("M036","乾電池類","乾電池・小型充電式電池等",locator="家庭ごみ手引き／乾電池類",prep="端子を絶縁")
add("M036","有害ごみ","スプレー缶・カセットボンベ・ライター・電池を外せない充電式製品",source=3,locator="変更点1／有害ごみ",prep="中身を使い切る。穴あけ不要")
excluded("M036","収集しないごみ","処理困難物・家電4品目等",source=1,locator="家庭ごみ手引き／収集しないごみ")

add("M037","可燃ごみ","生ごみ・紙くず等",source=2,locator="令和8年度前期日程／可燃ごみ",prep="生ごみはしっかり水切り",bag="町指定袋")
add("M037","不燃ごみ","金属・陶磁器・ガラス等",source=2,locator="令和8年度前期日程／不燃ごみ")
add("M037","小型家電","町指定の小型家電",source=2,locator="令和8年度前期日程／小型家電")
add("M037","有害ごみ","充電式電池・乾電池類・蛍光管・電池を外せない小型家電",source=2,locator="令和8年度前期日程／有害ごみ",prep="令和8年4月から充電式電池も有害ごみ")
add("M037","可燃性粗大ごみ","可燃性の大型品",source=2,locator="令和8年度前期日程／可燃性粗大",bulky="TRUE")
add("M037","不燃性粗大ごみ","不燃性の大型品",source=2,locator="令和8年度前期日程／不燃性粗大",bulky="TRUE")
add("M037","ペットボトル","PETマークのボトル",source=2,locator="令和8年度前期日程／ペットボトル")
add("M037","びん類","飲食用びん",source=2,locator="令和8年度前期日程／びん類")
add("M037","アルミ缶","飲食用アルミ缶",source=2,locator="令和8年度前期日程／アルミ缶")
add("M037","スチール缶・スプレー缶","スチール缶・スプレー缶",source=2,locator="令和8年度前期日程／スチール缶・スプレー缶")
add("M037","資源ごみ","古紙・古着布等の再生資源",source=2,locator="令和8年度前期日程／資源ごみ")

for name,rep,extra in [("可燃ごみ","生ごみ・紙くず等",dict(prep="生ごみは水切り")),("不燃ごみ","金属・陶磁器・ガラス等",{}),("小型家電","町指定の小型家電",{}),("びん類","飲食用びん",dict(prep="中をすすぐ")),("缶類","飲食用缶・スプレー缶",{}),("紙・布類","新聞・雑誌・段ボール・布類",dict(prep="種類別にまとめる")),("牛乳パック","飲料用紙パック",dict(prep="洗って切り開き乾かす")),("発泡スチロール、トレー","発泡スチロール・食品トレー",dict(prep="汚れを落とす")),("ペットボトル","PETマークのボトル",dict(prep="キャップとラベルを外し中をすすぐ")),("可燃性粗大ごみ","可燃性の大型品",dict(bulky="TRUE")),("不燃性粗大ごみ","不燃性の大型品",dict(bulky="TRUE")),("有害ごみ","蛍光管・乾電池・充電池一体型製品",dict(prep="電池端子を絶縁し、蛍光管は破損防止"))]: add("M038",name,rep,locator=f"冊子P1-2／{name}",**extra)
excluded("M038","町で収集しないもの","家電4品目・処理困難物等",locator="冊子／専門業者で処理するもの")

for name,rep,extra in [("可燃ごみ","生ごみ・紙くず・木くず等",dict(prep="生ごみは水切り",bag="町指定もえるごみ袋")),("プラスチック","包装プラスチック等",{}),("不燃ごみ","陶磁器・ガラス・金属等",{}),("小型家電","町指定の小型家電",{}),("びん類","飲食用びん",dict(prep="中をすすぐ")),("缶類","飲食用缶・スプレー缶",{}),("紙・布類","新聞・雑誌・段ボール・布類",dict(prep="種類別にまとめる")),("紙パック類","飲料用紙パック",dict(prep="洗って切り開き乾かす")),("発泡スチロール・トレー","発泡スチロール・食品トレー",dict(prep="汚れを落とす")),("ペットボトル","PETマークのボトル",dict(prep="キャップとラベルを外し中をすすぐ")),("可燃性粗大ごみ","可燃性大型品",dict(bulky="TRUE")),("不燃性粗大ごみ","不燃性大型品",dict(bulky="TRUE")),("有害ごみ","蛍光管・電池・充電池一体型製品等",dict(prep="電池端子を絶縁"))]: add("M039",name,rep,locator=f"家庭ごみの分け方・出し方／{name}",**extra)
excluded("M039","町で収集しないもの","自動車関係品・家電4品目・処理困難物等",locator="家庭ごみの分け方・出し方／収集対象外")

for name,rep,extra in [("可燃ごみ","生ごみ・紙くず等",dict(prep="生ごみは水切り")),("不燃ごみ","陶磁器・ガラス・金属等",{}),("小型家電","町指定の小型家電",{}),("びん類","飲食用びん",dict(prep="中をすすぐ")),("缶類","飲食用缶・スプレー缶",{}),("紙・布類","新聞・雑誌・段ボール・布類",dict(prep="種類別にまとめる")),("牛乳パック類","飲料用紙パック",dict(prep="洗って切り開き乾かす")),("発泡スチロール、トレー","発泡スチロール・食品トレー",dict(prep="汚れを落とす")),("ペットボトル","PETマークのボトル",dict(prep="キャップとラベルを外し中をすすぐ")),("可燃性粗大ごみ","可燃性大型品",dict(bulky="TRUE")),("不燃性粗大ごみ","不燃性大型品",dict(bulky="TRUE")),("有害ごみ","蛍光管・乾電池・充電池等",dict(source=3,prep="令和8年度から充電池も有害ごみとして回収。端子を絶縁"))]: add("M040",name,rep,locator=f"ごみの区分と出し方／{name}",**extra)

add("M041","もえるゴミ","生ごみ・紙くず・可燃物",source=2,locator="ごみの収集日／もえるゴミ")
add("M041","もえないゴミ","金属・陶磁器・ガラス・小型家電等",source=2,locator="ごみの収集日／もえないゴミ")
add("M041","布・プラスチック類（資源ゴミ）","布類・軟質プラスチック類",source=2,locator="ごみの収集日／布・プラスチック類（資源ゴミ）")
add("M041","発泡スチロール（資源ゴミ）","発泡スチロール",source=2,locator="ごみの収集日／発泡スチロール（資源ゴミ）")
add("M041","その他資源ゴミ","びん・缶・ペットボトル・古紙等の村指定資源",source=2,locator="ごみの収集日／その他資源ゴミ")
add("M041","蛍光灯","蛍光管",source=2,locator="ごみの収集日／蛍光灯",prep="破損しないよう保護")
add("M041","乾電池","乾電池類",source=2,locator="ごみの収集日／乾電池",prep="端子を絶縁")
excluded("M041","持ち出しできません","家電4品目・耐火金庫・処理困難物等",source=3,locator="家庭ゴミの分け方詳細版／持ち出しできません")

add("M042","可燃（もやせる）ごみ","生ごみ・紙くず・やわらかいプラスチック等",locator="手引きp4 可燃ごみ",prep="生ごみは十分水切り。硬い異素材を外す",bag="大山町指定可燃用袋")
add("M042","可燃（もやせる）粗大ごみ","袋に入らない木製家具・布団等",locator="手引きp5 可燃粗大ごみ",ui="REFERENCE_ONLY",channel="DROP_OFF",bulky="TRUE",size="長さ2m以下等の持込基準")
add("M042","不燃（もえない）ごみ","金属・陶磁器・ガラス・硬いプラスチック等",locator="手引きp6 不燃ごみ",prep="割れ物・刃物は包んで表示。スプレー缶等は使い切る",bag="大山町指定分別用袋")
add("M042","不燃（もえない）粗大ごみ","指定袋に入らない不燃物",locator="手引きp7 不燃粗大ごみ",bulky="TRUE",bag="不燃粗大ごみシール")
add("M042","古紙類","新聞・段ボール・紙パック・雑誌類・紙製容器包装",source=2,locator="令和8年4月変更／紙製容器包装は雑誌類（古紙類）へ",prep="種類別にまとめる")
add("M042","缶・びん","飲食用缶・びん・旧指定びん",source=2,locator="令和8年4月変更／指定びんは缶・びんへ",prep="中身を空にして洗う")
add("M042","発泡スチロール","白色の発泡スチロール",source=2,locator="令和8年4月変更／白色のみ",fallback="白色以外・汚れが落ちない物は可燃ごみ",prep="洗って乾かし、シール等を外す")
add("M042","ペットボトル","PETマークの飲料・調味料ボトル",locator="手引きp12 ペットボトル",prep="キャップとラベルを外し洗う")
add("M042","電池","乾電池・コイン型・ボタン型電池",source=4,locator="電池の出し方／乾電池等",prep="金属端子を絶縁",bag="透明または半透明袋")
add("M042","蛍光管","丸型・直管・電球型蛍光管",locator="手引きp13 蛍光管",prep="破損防止。LED等は不燃ごみ")
add("M042","小型充電式電池","ニカド・ニッケル水素・リチウムイオン電池・モバイルバッテリー",source=4,locator="電池の出し方／小型充電式電池",ui="REFERENCE_ONLY",channel="DROP_OFF",prep="端子を絶縁し回収ボックスへ")
add("M042","バッテリー","自家用自動車・バイク用バッテリー",locator="手引きp14 バッテリー",ui="REFERENCE_ONLY",channel="DROP_OFF")
add("M042","混合粗大ごみ","燃える物と燃えない物が分離困難な大型品",locator="手引きp14 混合粗大ごみ",ui="REFERENCE_ONLY",channel="DROP_OFF",bulky="TRUE")
add("M042","小型家電","回収対象の小型家電・電池を外せない充電式製品",locator="手引きp15 小型家電",ui="REFERENCE_ONLY",channel="DROP_OFF",prep="取り外せる電池・バッテリーは外す")
excluded("M042","収集・処理できないごみ","家電4品目・危険有害物・処理困難物等",locator="手引きp17 収集・処理できないごみ")

for name,rep,extra in [("可燃ごみ","生ごみ・紙くず等",dict(prep="生ごみは水切り")),("不燃ごみ","金属・陶磁器・ガラス・小型家電等",{}),("不燃粗大ごみ","ストーブ・自転車等の大型不燃物",dict(bulky="TRUE")),("古紙類","新聞・段ボール・紙パック・雑誌等",dict(prep="種類別にまとめる")),("小雑紙","小型の雑がみ",dict(prep="指定方法でまとめる")),("ビン・缶類","飲食用びん・缶",dict(prep="中をすすぐ")),("再利用ビン","大手4社等の再利用可能びん",{}),("軟質プラスチック類","発泡スチロール・軟質プラスチック・布団庭木等の指定品",{}),("ペットボトル","PETマークのボトル",dict(prep="キャップとラベルを外し中をすすぐ")),("電池","マンガン・アルカリ電池等",dict(prep="端子を絶縁")),("蛍光管","蛍光管",dict(prep="破損しないよう保護")),("木質類","町指定の木質類",{}),("布類","衣類・古布等",dict(prep="洗って乾かす"))]: add("M043",name,rep,locator=f"家庭ごみ分別／{name}",**extra)
add("M043","使用済み小型家電","回収対象の使用済み小型家電",ui="REFERENCE_ONLY",channel="DROP_OFF",locator="家庭ごみ分別／小型家電リサイクル",prep="個人情報を消去し電池を外す")
excluded("M043","収集しないもの","家電4品目・処理困難物等",locator="家庭ごみ分別／収集しないもの")

def ensure_registry():
    path=MASTER/"02_official_domain_registry.csv"; fields,rows=read_csv(path); fields=fields or REGISTRY_FIELDS
    existing={(r.get("municipality_id"),r.get("host")) for r in rows}
    for mid,specs in source_specs.items():
        for spec in specs:
            host=(urlparse(spec[2]).hostname or "").lower(); key=(mid,host)
            if host and key not in existing:
                rows.append({"municipality_id":mid,"host":host,"authority_type":"MUNICIPAL_DOMAIN","authority_name":municipality_specs[mid]["city"],"verification_url":municipality_specs[mid]["top"],"verified_date":CHECKED,"notes":"Batch 04 official municipal source host"}); existing.add(key)
    rows.sort(key=lambda r:(r.get("municipality_id",""),r.get("host",""))); write_csv(path,fields,rows)

def build_sources():
    rows=[]
    for mid,specs in source_specs.items():
        for i,(title,kind,url,updated,used) in enumerate(specs,1): rows.append({"municipality_id":mid,"source_id":f"S-{mid}-{i:02d}","資料名":title,"資料種別":kind,"公式URL":url,"発行主体":municipality_specs[mid]["city"],"対象年度":"令和8年度","ページ更新日":updated,"取得確認日":CHECKED,"使用した情報":used,"優先度":str(i),"現行性":"現行","備考":"","official_verified":"","official_basis":"","official_linking_url":""})
    return rows

def build_categories():
    by_mid={}
    for raw in categories: by_mid.setdefault(raw["municipality_id"],[]).append(raw)
    if set(by_mid)!=TARGETS: raise ValueError(f"Batch04 target mismatch {set(by_mid)}")
    rows=[]
    for mid,raws in by_mid.items():
        name_to_id={r["自治体正式名称"]:f"C-{mid}-{i:02d}" for i,r in enumerate(raws,1)}
        for i,raw in enumerate(raws,1):
            sidx=int(raw["source_index"]); src=source_specs[mid][sidx-1]
            rows.append({"municipality_id":mid,"category_id":name_to_id[raw["自治体正式名称"]],"自治体正式名称":raw["自治体正式名称"],"category_group":raw["category_group"],"parent_category_id":"","classification_level":raw["classification_level"],"表示順":str(i),"collection_channel":raw["collection_channel"],"代表品目":raw["代表品目"],"入れてはいけない物":raw["入れてはいけない物"],"適用条件":"","条件外の扱い":raw["条件外の扱い"],"出す前の処理":raw["出す前の処理"],"袋・容器のルール":raw["袋・容器のルール"],"サイズ・条件":raw["サイズ・条件"],"粗大ごみ扱いか":raw["粗大ごみ扱いか"],"予約が必要か":"FALSE","有料か":"FALSE","料金ルール":"","自治体収集外か":raw["自治体収集外か"],"注意事項":raw["注意事項"],"source_id":f"S-{mid}-{sidx:02d}","出典URL":src[2],"出典ページ・該当箇所":raw["出典ページ・該当箇所"],"確認日":CHECKED,"ui_role":raw["ui_role"],"rule_status":"CURRENT","effective_from":"","effective_to":""})
    return rows

def build_municipalities():
    return [{"municipality_id":mid,"都道府県":spec["pref"],"市町村":spec["city"],"実装区分":"中国5県全市町村","ごみ処理主体":spec["processor"],"自治体ごみトップURL":spec["top"],"分別ガイドURL":spec["guide"],"品目検索URL":"","やさしい日本語URL":"","多言語資料URL":"","対象年度":"令和8年度","最終確認日":CHECKED,"確認ステータス":"QA_REQUIRED","備考":spec["note"],"official_category_count":"","reviewed_category_count":"","category_count_basis":"住民が家庭ごみ排出時に選択する公式分別区分を全件照合し、現行カレンダー・公式更新情報で稼働を確認。REFERENCE_ONLYやEXCLUDED_NOTICEは住民向け補助経路として保持。","category_count_verified":"TRUE","category_count_check_status":"MANUAL_INDEX_REVIEW","category_count_review_id":f"CR-{mid}-CATEGORY-COVERAGE","category_count_reviewed_date":CHECKED,"category_count_reviewed_by":REVIEWER,"search_service_check_status":"NOT_CHECKED","search_service_check_evidence":"","easy_japanese_check_status":"NOT_CHECKED","easy_japanese_check_evidence":"","multilingual_check_status":"NOT_CHECKED","multilingual_check_evidence":""} for mid,spec in municipality_specs.items()]

def build_review_evidence():
    rows=[]
    for mid,specs in source_specs.items():
        for i,src in enumerate(specs,1): rows.append({"review_evidence_id":f"CRE-{mid}-{i:02d}","review_id":f"CR-{mid}-CATEGORY-COVERAGE","municipality_id":mid,"source_id":f"S-{mid}-{i:02d}","locator":src[4],"evidence_role":"PRIMARY_INDEX" if i==1 else "SUPPLEMENTAL_INDEX","notes":f"{CHECKED} Batch 04 resident-facing category completeness review"})
    return rows

def main():
    if set(municipality_specs)!=TARGETS or set(source_specs)!=TARGETS: raise ValueError("Batch04 spec target mismatch")
    ensure_registry(); OUT.mkdir(parents=True,exist_ok=True); p="batch_04_"
    write_csv(OUT/f"{p}municipalities.csv",MUNICIPALITY_FIELDS,build_municipalities()); write_csv(OUT/f"{p}categories.csv",CATEGORY_FIELDS,build_categories()); write_csv(OUT/f"{p}sources.csv",SOURCE_FIELDS,build_sources()); write_csv(OUT/f"{p}qa.csv",QA_FIELDS,[]); write_csv(OUT/f"{p}item_mapping.csv",MAPPING_FIELDS,[]); write_csv(OUT/f"{p}item_coverage.csv",COVERAGE_FIELDS,[]); write_csv(OUT/f"{p}category_review_evidence.csv",CATEGORY_REVIEW_EVIDENCE_FIELDS,build_review_evidence()); counts=migrate_batch_dir(OUT); print(" ".join(f"{k}={v}" for k,v in counts.items()))
if __name__=="__main__": main()
