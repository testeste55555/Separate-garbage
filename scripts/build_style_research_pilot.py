#!/usr/bin/env python3
"""Build the additive TOP10 Style Research Pilot bundle.

This script never edits the category, mapping, municipality, or teaching-group
canonical files.  It snapshots canonical category names into a separate style
layer and keeps one-to-many official color observations apart from the single
UI projection decision.
"""

from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/style_research"
CATEGORIES = ROOT / "data/research/02_categories_master.csv"
CHECKED_DATE = "2026-08-20"
REVIEWER = "OPENAI_CODEX_STYLE_RESEARCH_PILOT"

TARGETS = [
    (1, "A", "M094", "広島市", "ACTIVE", "COMPLETED", "FALSE", 7,
     "SS-M094-01;SS-M094-02", "市全域で同じ表面分別表を使用。区別色は公式PDFの区分見出しから近似。"),
    (2, "A", "M099", "福山市", "DEFERRED", "RESEARCHED_CANONICAL_DEFERRED", "TRUE", 0,
     "SS-M099-01;SS-M099-02;SS-M099-03;SS-M099-04",
     "市内一般・内海町・沼隈町で分別単位が異なる。正本category_id未確定のためstyle行は生成しない。"),
    (3, "A", "M104", "東広島市", "ACTIVE", "COMPLETED", "FALSE", 9,
     "SS-M104-01;SS-M104-02", "指定袋色は複数categoryで共有されるため観測として保持し、区分識別にはガイドの反復見出し色を採用。"),
    (4, "A", "M098", "尾道市", "DEFERRED", "RESEARCHED_CANONICAL_DEFERRED", "TRUE", 0,
     "SS-M098-01;SS-M098-02;SS-M098-03;SS-M098-04;SS-M098-05;SS-M098-06",
     "尾道・向島・御調・因島・瀬戸田の5地域variant。正本category_id未確定のためstyle行は生成しない。"),
    (5, "A", "M095", "呉市", "ACTIVE", "COMPLETED", "FALSE", 6,
     "SS-M095-01;SS-M095-02", "地区別日付は異なるが公式カレンダーの区分凡例と色体系は共通。"),
    (6, "B", "M097", "三原市", "ACTIVE", "COMPLETED", "FALSE", 9,
     "SS-M097-01;SS-M097-02", "ステーション看板の反復区分色を優先。"),
    (7, "B", "M105", "廿日市市", "ACTIVE", "COMPLETED", "FALSE", 5,
     "SS-M105-01;SS-M105-02", "指定袋の公式色名を優先。資源ごみ親は排出方法が複数のため単一色を確定しない。"),
    (8, "B", "M106", "安芸高田市", "ACTIVE", "COMPLETED", "FALSE", 5,
     "SS-M106-01;SS-M106-02", "公式ポスターで区分識別性がある行のみ採用。白地・複数子色の親は未確認。"),
    (9, "B", "M109", "海田町", "ACTIVE", "COMPLETED", "FALSE", 4,
     "SS-M109-01;SS-M109-02", "資源物親は白トレイ・資源回収ステーション・品目見出しで色が競合するため未確認。"),
    (10, "B", "M107", "江田島市", "ACTIVE", "COMPLETED", "FALSE", 6,
     "SS-M107-01;SS-M107-02", "令和8年度改定ポスターの反復区分帯色を採用。"),
]

SOURCES = [
    ("SS-M094-01", "M094", "MUNICIPALITY_WIDE", "令和8年度版 家庭ごみの正しい出し方", "自治体公式PDF",
     "https://www.city.hiroshima.lg.jp/_res/projects/default_project/_page_/001/003/182/2026.pdf",
     "表面・左端の可燃ごみから有害ごみまでの区分見出し帯", "OFFICIAL_POSTER_GUIDE", 2, "CURRENT", "PDFの区分帯色を視覚近似。"),
    ("SS-M094-02", "M094", "MUNICIPALITY_WIDE", "家庭ごみの正しい出し方", "自治体公式Webページ",
     "https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026095/1026096/1003182.html",
     "令和8年度版PDFへの公式導線と9見出し", "OFFICIAL_WEB_INDEX", 4, "CURRENT", "PDFの現行性確認。"),
    ("SS-M099-01", "M099", "CITY_GENERAL", "家庭ごみの分け方出し方B3ポスター 市内版", "自治体公式PDF",
     "https://www.city.fukuyama.hiroshima.jp/uploaded/attachment/274722.pdf",
     "市内版・左端の分別区分帯", "OFFICIAL_POSTER_GUIDE", 3, "CURRENT", "地域variant調査用。category未確定のためstyle参照には未使用。"),
    ("SS-M099-02", "M099", "UCHIUMI", "家庭ごみの分け方出し方B3ポスター 内海町版", "自治体公式PDF",
     "https://www.city.fukuyama.hiroshima.jp/uploaded/attachment/274723.pdf",
     "内海町版・左端の分別区分帯", "OFFICIAL_POSTER_GUIDE", 3, "CURRENT", "市内版と紙類の扱いが異なる地域variant。"),
    ("SS-M099-03", "M099", "MUNICIPALITY_MULTISCOPE", "ごみの分け方・出し方", "自治体公式Webページ",
     "https://www.city.fukuyama.hiroshima.jp/site/kankyo/328268.html",
     "市内版と内海町版の2公式PDFへの導線", "OFFICIAL_WEB_INDEX", 4, "CURRENT", "2地域版の併存を確認。"),
    ("SS-M099-04", "M099", "NUMAKUMA", "沼隈町の紙類", "自治体公式Webページ",
     "https://www.city.fukuyama.hiroshima.jp/site/kankyo/314393.html",
     "沼隈町で回収する紙類4区分", "OFFICIAL_WEB_INDEX", 4, "CURRENT", "沼隈町固有の紙類区分を確認。"),
    ("SS-M104-01", "M104", "MUNICIPALITY_WIDE", "家庭ごみの分別と出し方 ごみブック", "自治体公式PDF",
     "https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_all.pdf",
     "5-6頁の分別一覧区分枠・7頁以降の指定袋説明", "OFFICIAL_POSTER_GUIDE;DESIGNATED_BAG", 3, "CURRENT", "見出し色と指定袋色を用途別に保持。"),
    ("SS-M104-02", "M104", "MUNICIPALITY_WIDE", "家庭から出るごみの分別・出し方について", "自治体公式Webページ",
     "https://www.city.higashihiroshima.lg.jp/soshiki/seikatsukankyo/8/4/1/index.html",
     "現行ごみブックへの公式導線", "OFFICIAL_WEB_INDEX", 4, "CURRENT", "PDFの現行性確認。"),
    ("SS-M098-01", "M098", "MUNICIPALITY_MULTISCOPE", "ごみ分別ガイドブック 尾道市全域", "自治体公式Webページ",
     "https://www.city.onomichi.hiroshima.jp/soshiki/16/44213.html",
     "尾道・向島・御調・因島・瀬戸田の5地域版への導線", "OFFICIAL_WEB_INDEX", 4, "CURRENT", "5地域variantの併存を確認。"),
    ("SS-M098-02", "M098", "ONOMICHI", "ごみ分別ガイドブック 尾道地域", "自治体公式PDF",
     "https://www.city.onomichi.hiroshima.jp/uploaded/attachment/57662.pdf",
     "表紙・分別区分ページ", "OFFICIAL_POSTER_GUIDE", 3, "CURRENT", "地域variant調査用。"),
    ("SS-M098-03", "M098", "MUKAISHIMA", "ごみ分別ガイドブック 向島地域", "自治体公式PDF",
     "https://www.city.onomichi.hiroshima.jp/uploaded/attachment/57663.pdf",
     "表紙・分別区分ページ", "OFFICIAL_POSTER_GUIDE", 3, "CURRENT", "地域variant調査用。"),
    ("SS-M098-04", "M098", "MITSUGI", "ごみ分別ガイドブック 御調地域", "自治体公式PDF",
     "https://www.city.onomichi.hiroshima.jp/uploaded/attachment/57665.pdf",
     "表紙・分別区分ページ", "OFFICIAL_POSTER_GUIDE", 3, "CURRENT", "地域variant調査用。"),
    ("SS-M098-05", "M098", "INNOSHIMA", "ごみ分別ガイドブック 因島地域", "自治体公式PDF",
     "https://www.city.onomichi.hiroshima.jp/uploaded/attachment/57907.pdf",
     "表紙・分別区分ページ", "OFFICIAL_POSTER_GUIDE", 3, "CURRENT", "地域variant調査用。"),
    ("SS-M098-06", "M098", "SETODA", "ごみ分別ガイドブック 瀬戸田地域", "自治体公式PDF",
     "https://www.city.onomichi.hiroshima.jp/uploaded/attachment/57904.pdf",
     "表紙・分別区分ページ", "OFFICIAL_POSTER_GUIDE", 3, "CURRENT", "地域variant調査用。"),
    ("SS-M095-01", "M095", "MUNICIPALITY_WIDE", "令和8年度版 ごみ出しカレンダー No.1", "自治体公式PDF",
     "https://www.city.kure.lg.jp/uploaded/attachment/108241.pdf",
     "上部凡例と各月セルで反復する7区分色", "OFFICIAL_CALENDAR", 2, "CURRENT", "昭和地区版で共通テンプレートの区分色を確認。"),
    ("SS-M095-02", "M095", "MUNICIPALITY_WIDE", "ごみ出しカレンダー 令和8年度版", "自治体公式Webページ",
     "https://www.city.kure.lg.jp/soshiki/19/gomidasicalender2026.html",
     "全地区PDF一覧と共通7区分列", "OFFICIAL_WEB_INDEX", 4, "CURRENT", "地区差は日付であり区分凡例は共通。"),
    ("SS-M097-01", "M097", "MUNICIPALITY_WIDE", "ごみステーション用看板 令和2年10月実施", "自治体公式PDF",
     "https://www.city.mihara.hiroshima.jp/uploaded/life/115378_353536_misc.pdf",
     "看板全体・10分別の背景帯", "STATION_SIGN", 1, "CURRENT", "現行分別案内が参照するステーション看板。"),
    ("SS-M097-02", "M097", "MUNICIPALITY_WIDE", "ごみステーション用看板", "自治体公式Webページ",
     "https://www.city.mihara.hiroshima.jp/soshiki/23/115378.html",
     "令和2年10月実施PDFへの公式導線", "OFFICIAL_WEB_INDEX", 4, "CURRENT", "PDFの公式性確認。"),
    ("SS-M105-01", "M105", "MUNICIPALITY_WIDE", "家庭ごみの正しい分け方と収集日 ポスター", "自治体公式PDF",
     "https://www.city.hatsukaichi.hiroshima.jp/uploaded/attachment/81152.pdf",
     "指定袋欄の黄色・白色・緑色と区分行", "DESIGNATED_BAG;OFFICIAL_POSTER_GUIDE", 1, "CURRENT", "公式色名と袋画像を照合。"),
    ("SS-M105-02", "M105", "MUNICIPALITY_WIDE", "家庭ごみの正しい分け方の早見表 令和8年4月版・ポスター", "自治体公式Webページ",
     "https://www.city.hatsukaichi.hiroshima.jp/soshiki/31/78499.html",
     "現行ポスターPDFへの公式導線", "OFFICIAL_WEB_INDEX", 4, "CURRENT", "令和8年版の現行性確認。"),
    ("SS-M106-01", "M106", "MUNICIPALITY_WIDE", "ごみの分け方・出し方", "自治体公式PDF",
     "https://www.akitakata.jp/akitakata-media/filer_public/71/1c/711ce7e9-446c-47c7-bc0c-f55db381fc25/gomino-wake-hou-dashikata-20214.pdf",
     "区分別の背景帯と専用袋見本", "OFFICIAL_POSTER_GUIDE;DESIGNATED_BAG", 3, "CURRENT", "現行公式ページ掲載資料。"),
    ("SS-M106-02", "M106", "MUNICIPALITY_WIDE", "家庭ごみの出し方", "自治体公式Webページ",
     "https://www.akitakata.jp/ja/shisei/section/siminseikatu/gomi22/",
     "分別表と公式PDFへの導線", "OFFICIAL_WEB_INDEX", 4, "CURRENT", "PDFの現行性確認。"),
    ("SS-M109-01", "M109", "MUNICIPALITY_WIDE", "令和8年度 家庭ごみの正しい出し方", "自治体公式PDF",
     "https://www.town.kaita.lg.jp/uploaded/life/44980_122640_misc.pdf",
     "1頁のステーション帯・種別見出し・各区分表", "OFFICIAL_POSTER_GUIDE;STATION_SIGN", 2, "CURRENT", "資源物は同一資料内で複数の意味色が併存。"),
    ("SS-M109-02", "M109", "MUNICIPALITY_WIDE", "令和8年度 家庭ごみの正しい出し方", "自治体公式Webページ",
     "https://www.town.kaita.lg.jp/soshiki/10/135455.html",
     "令和8年度PDFへの公式導線", "OFFICIAL_WEB_INDEX", 4, "CURRENT", "PDFの現行性確認。"),
    ("SS-M107-01", "M107", "MUNICIPALITY_WIDE", "家庭ごみの種類と正しい出し方 令和8年度改定版", "自治体公式PDF",
     "https://www.city.etajima.hiroshima.jp/cms/articles/download/11923/1/R8_nihonngo.pdf",
     "区分別の左見出し帯", "OFFICIAL_POSTER_GUIDE", 3, "CURRENT", "令和8年度改定版の反復区分色。"),
    ("SS-M107-02", "M107", "MUNICIPALITY_WIDE", "家庭ごみの種類と正しい出し方 ポスターをご利用ください", "自治体公式Webページ",
     "https://www.city.etajima.hiroshima.jp/cms/articles/show/11923",
     "令和8年度改定版PDFへの公式導線", "OFFICIAL_WEB_INDEX", 4, "CURRENT", "PDFの現行性確認。"),
]

# category_id: (official label, derived HEX or blank, status, evidence role,
# source_id, locator, semantic fit, basis, note)
PRIMARY = {
    "C-M094-01": ("橙色系", "#F5A900", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M094-01", "表面 可燃ごみ見出し帯", "CATEGORY_DISCRIMINATOR", "公式PDF区分帯の視覚表現", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M094-02": ("青色系", "#1565B3", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M094-01", "表面 ペットボトル見出し帯", "CATEGORY_DISCRIMINATOR", "公式PDF区分帯の視覚表現", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M094-03": ("赤色系", "#E43136", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M094-01", "表面 リサイクルプラ見出し帯", "CATEGORY_DISCRIMINATOR", "公式PDF区分帯の視覚表現", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M094-04": ("水色系", "#0EA5D8", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M094-01", "表面 その他プラ見出し帯", "CATEGORY_DISCRIMINATOR", "公式PDF区分帯の視覚表現", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M094-05": ("朱色系", "#F26A21", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M094-01", "表面 不燃ごみ見出し帯", "CATEGORY_DISCRIMINATOR", "公式PDF区分帯の視覚表現", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M094-06": ("緑色系", "#2BB24C", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M094-01", "表面 資源ごみ見出し帯", "CATEGORY_DISCRIMINATOR", "公式PDF区分帯の視覚表現", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M094-07": ("紫色系", "#7443A0", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M094-01", "表面 有害ごみ見出し帯", "CATEGORY_DISCRIMINATOR", "公式PDF区分帯の視覚表現", "PDF画像からの近似値。自治体公式HEXではない。"),

    "C-M104-01": ("黄色系", "#F4D548", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M104-01", "5頁 燃やせるごみ区分枠", "CATEGORY_DISCRIMINATOR", "公式ごみブック区分枠の視覚表現", "PDF画像からの近似値。オレンジ指定袋は別の共有観測として保持。"),
    "C-M104-02": ("灰色系", "#9A9A9A", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M104-01", "5頁 危険ごみ区分枠", "CATEGORY_DISCRIMINATOR", "公式ごみブック区分枠の視覚表現", "PDF画像からの近似値。オレンジ指定袋は別の共有観測として保持。"),
    "C-M104-03": ("藤色系", "#B56EA7", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M104-01", "5頁 その他プラ区分枠", "CATEGORY_DISCRIMINATOR", "公式ごみブック区分枠の視覚表現", "PDF画像からの近似値。紫指定袋は別の共有観測として保持。"),
    "C-M104-05": ("茶色系", "#B76A3E", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M104-01", "6頁 新聞区分枠", "CATEGORY_DISCRIMINATOR", "公式ごみブック区分枠の視覚表現", "PDF画像からの近似値。"),
    "C-M104-06": ("深緑色系", "#3E8B55", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M104-01", "6頁 雑誌・雑がみ・ダンボール区分枠", "CATEGORY_DISCRIMINATOR", "公式ごみブック区分枠の視覚表現", "PDF画像からの近似値。"),
    "C-M104-07": ("桃色系", "#E63E96", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M104-01", "5頁 ビン・缶区分枠", "CATEGORY_DISCRIMINATOR", "公式ごみブック区分枠の視覚表現", "PDF画像からの近似値。紫指定袋は別の共有観測として保持。"),
    "C-M104-08": ("緑色系", "#30A459", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M104-01", "5頁 ペットボトル区分枠", "CATEGORY_DISCRIMINATOR", "公式ごみブック区分枠の視覚表現", "PDF画像からの近似値。紫指定袋は別の共有観測として保持。"),
    "C-M104-09": ("水色系", "#35B8D2", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M104-01", "5頁 リサイクルプラ区分枠", "CATEGORY_DISCRIMINATOR", "公式ごみブック区分枠の視覚表現", "PDF画像からの近似値。紫指定袋は別の共有観測として保持。"),
    "C-M104-10": ("淡桃色系", "#F294A8", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M104-01", "5頁 有害ごみ区分枠", "CATEGORY_DISCRIMINATOR", "公式ごみブック区分枠の視覚表現", "PDF画像からの近似値。オレンジ指定袋は別の共有観測として保持。"),

    "C-M095-01": ("桃色系", "#F29091", "OFFICIAL_DERIVED", "OFFICIAL_CALENDAR", "SS-M095-01", "上部凡例 もえるごみ・各月反復セル", "CATEGORY_DISCRIMINATOR", "公式カレンダー凡例の反復色", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M095-02": ("淡青色系", "#B8D3E8", "OFFICIAL_DERIVED", "OFFICIAL_CALENDAR", "SS-M095-01", "上部凡例 もえないごみ・各月反復セル", "CATEGORY_DISCRIMINATOR", "公式カレンダー凡例の反復色", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M095-04": ("淡緑色系", "#ABCD93", "OFFICIAL_DERIVED", "OFFICIAL_CALENDAR", "SS-M095-01", "上部凡例 プラ資源・各月反復セル", "CATEGORY_DISCRIMINATOR", "公式カレンダー凡例の反復色", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M095-05": ("灰白色系", "#D5D5D5", "OFFICIAL_DERIVED", "OFFICIAL_CALENDAR", "SS-M095-01", "上部凡例 缶・びん・ペットボトル・各月反復セル", "CATEGORY_DISCRIMINATOR", "公式カレンダー凡例の反復色", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M095-06": ("黄色系", "#F1D56D", "OFFICIAL_DERIVED", "OFFICIAL_CALENDAR", "SS-M095-01", "上部凡例 紙類・各月反復セル", "CATEGORY_DISCRIMINATOR", "公式カレンダー凡例の反復色", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M095-07": ("赤色系", "#D74A4A", "OFFICIAL_DERIVED", "OFFICIAL_CALENDAR", "SS-M095-01", "上部凡例 有害・危険・各月反復セル", "CATEGORY_DISCRIMINATOR", "公式カレンダー凡例の反復色", "PDF画像からの近似値。自治体公式HEXではない。"),

    "C-M097-01": ("桃色系", "#E8B8DE", "OFFICIAL_DERIVED", "STATION_SIGN", "SS-M097-01", "看板 もやすごみ背景帯", "CATEGORY_DISCRIMINATOR", "公式ステーション看板の背景帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M097-02": ("淡黄色系", "#EDF1AE", "OFFICIAL_DERIVED", "STATION_SIGN", "SS-M097-01", "看板 不燃物背景帯", "CATEGORY_DISCRIMINATOR", "公式ステーション看板の背景帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M097-03": ("淡緑色系", "#B6DEB0", "OFFICIAL_DERIVED", "STATION_SIGN", "SS-M097-01", "看板 びん・飲料缶背景帯", "CATEGORY_DISCRIMINATOR", "公式ステーション看板の背景帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M097-04": ("淡水色系", "#A8E1EF", "OFFICIAL_DERIVED", "STATION_SIGN", "SS-M097-01", "看板 ペットボトル背景帯", "CATEGORY_DISCRIMINATOR", "公式ステーション看板の背景帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M097-05": ("黄緑色系", "#DDEEC6", "OFFICIAL_DERIVED", "STATION_SIGN", "SS-M097-01", "看板 容器包装プラスチック背景帯", "CATEGORY_DISCRIMINATOR", "公式ステーション看板の背景帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M097-06": ("黄緑色系", "#91CE52", "OFFICIAL_DERIVED", "STATION_SIGN", "SS-M097-01", "看板 発火性危険ごみ小区分", "CATEGORY_DISCRIMINATOR", "公式ステーション看板の小区分帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M097-07": ("青色系", "#60A5C3", "OFFICIAL_DERIVED", "STATION_SIGN", "SS-M097-01", "看板 電池小区分", "CATEGORY_DISCRIMINATOR", "公式ステーション看板の小区分帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M097-08": ("灰色系", "#A19F9F", "OFFICIAL_DERIVED", "STATION_SIGN", "SS-M097-01", "看板 電池の外せない小型家電小区分", "CATEGORY_DISCRIMINATOR", "公式ステーション看板の小区分帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M097-09": ("黄色系", "#F0DF36", "OFFICIAL_DERIVED", "STATION_SIGN", "SS-M097-01", "看板 蛍光灯小区分", "CATEGORY_DISCRIMINATOR", "公式ステーション看板の小区分帯", "PDF画像からの近似値。自治体公式HEXではない。"),

    "C-M105-01": ("黄色", "#DFCDA2", "OFFICIAL_DERIVED", "DESIGNATED_BAG", "SS-M105-01", "ポスター 燃やせるごみ・黄色の指定袋", "CATEGORY_DISCRIMINATOR", "公式色名と指定袋画像", "黄色という公式記載を確認し、表示値はPDF画像からの近似値。自治体公式HEXではない。"),
    "C-M105-02": ("", "", "NOT_CONFIRMED", "OFFICIAL_POSTER_GUIDE", "SS-M105-01", "ポスター 資源ごみ(1)から(5)", "MULTI_METHOD_CATEGORY", "資源ごみ親は白色袋・ひも束・複数排出方法", "単一の親色を確認できない。空欄を維持し推測しない。"),
    "C-M105-08": ("白色", "#FFFFFF", "OFFICIAL_DERIVED", "DESIGNATED_BAG", "SS-M105-01", "ポスター 埋立ごみ・白色の指定袋", "CATEGORY_DISCRIMINATOR", "公式色名と指定袋画像", "白色という公式記載を確認し、表示値はPDF画像からの近似値。自治体公式HEXではない。"),
    "C-M105-10": ("緑色", "#B6DEB0", "OFFICIAL_DERIVED", "DESIGNATED_BAG", "SS-M105-01", "ポスター 小型および複雑ごみ・緑色の指定袋", "CATEGORY_DISCRIMINATOR", "公式色名と指定袋画像", "緑色という公式記載を確認し、表示値はPDF画像からの近似値。自治体公式HEXではない。"),
    "C-M105-11": ("白色", "#FFFFFF", "OFFICIAL_DERIVED", "DESIGNATED_BAG", "SS-M105-01", "ポスター 有害ごみ・白色の指定袋", "CATEGORY_DISCRIMINATOR", "公式色名と指定袋画像", "白色という公式記載を確認し、表示値はPDF画像からの近似値。自治体公式HEXではない。"),

    "C-M106-01": ("", "", "NOT_CONFIRMED", "OFFICIAL_POSTER_GUIDE", "SS-M106-01", "ポスター 燃えるごみ行", "NO_SEMANTIC_COLOR", "公式ポスターは白地で専用色を識別できない", "単なる紙面地色を公式分別色にしない。"),
    "C-M106-02": ("淡黄色系", "#F3E8B8", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M106-01", "ポスター 古紙類背景帯", "CATEGORY_DISCRIMINATOR", "公式ポスターの区分背景帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M106-03": ("", "", "NOT_CONFIRMED", "OFFICIAL_POSTER_GUIDE", "SS-M106-01", "ポスター 容器包装類の紙パック・プラ・PET各行", "MULTI_METHOD_CATEGORY", "投影親の子区分で桃色と青色が併存", "単一の親色を確認できない。空欄を維持し推測しない。"),
    "C-M106-07": ("青色系", "#2C6AAC", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M106-01", "ポスター 燃えないごみ4小区分の見出し帯", "CATEGORY_DISCRIMINATOR", "公式ポスターで4子区分に反復する青色", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M106-12": ("黄色系", "#D4C32A", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M106-01", "ポスター 有害ごみ背景帯", "CATEGORY_DISCRIMINATOR", "公式ポスターの区分背景帯", "PDF画像からの近似値。自治体公式HEXではない。"),

    "C-M109-01": ("赤色系", "#E50713", "OFFICIAL_DERIVED", "STATION_SIGN", "SS-M109-01", "1頁 可燃ごみステーション左帯", "CATEGORY_DISCRIMINATOR", "公式資料のステーション識別帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M109-02": ("紫色系", "#8D4C9B", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M109-01", "1頁 埋立ごみ種別帯", "CATEGORY_DISCRIMINATOR", "公式資料の区分識別帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M109-03": ("", "", "NOT_CONFIRMED", "OFFICIAL_POSTER_GUIDE", "SS-M109-01", "1頁 資源物の白トレイ・資源回収ステーション・品目帯", "CONFLICTING_EVIDENCE", "同一category内で緑・青・黄橙の意味色が併存", "単一色へ誤統合せず未確認とする。"),
    "C-M109-09": ("緑色系", "#4CA13C", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M109-01", "1頁 有害ごみ種別帯", "CATEGORY_DISCRIMINATOR", "公式資料の区分識別帯", "PDF画像からの近似値。自治体公式HEXではない。"),

    "C-M107-01": ("赤橙色系", "#E63C12", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M107-01", "区分帯 燃えるごみ", "CATEGORY_DISCRIMINATOR", "令和8年度公式ポスターの区分帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M107-02": ("青色系", "#1E5AA8", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M107-01", "区分帯 燃えないごみ", "CATEGORY_DISCRIMINATOR", "令和8年度公式ポスターの区分帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M107-05": ("緑色系", "#009E70", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M107-01", "区分帯 資源ごみ びん・缶", "CATEGORY_DISCRIMINATOR", "令和8年度公式ポスターの区分帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M107-06": ("緑色系", "#009E70", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M107-01", "区分帯 資源ごみ 古紙・布類", "CATEGORY_DISCRIMINATOR", "令和8年度公式ポスターの区分帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M107-07": ("緑色系", "#009E70", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M107-01", "区分帯 資源ごみ ペットボトル", "CATEGORY_DISCRIMINATOR", "令和8年度公式ポスターの区分帯", "PDF画像からの近似値。自治体公式HEXではない。"),
    "C-M107-08": ("紫色系", "#92278F", "OFFICIAL_DERIVED", "OFFICIAL_POSTER_GUIDE", "SS-M107-01", "区分帯 有害・危険ごみ", "CATEGORY_DISCRIMINATOR", "令和8年度公式ポスターの区分帯", "PDF画像からの近似値。自治体公式HEXではない。"),
}

SUPPORTING = [
    # East Hiroshima: bag colors are official labels, but shared across categories.
    (cid, label, "DESIGNATED_BAG", "SS-M104-01", locator, "SHARED_COLLECTION_GROUP", note)
    for cid, label, locator, note in [
        ("C-M104-01", "オレンジ色", "7頁 燃やせるごみ指定袋", "燃やせるごみ・危険ごみ・有害ごみで共通。"),
        ("C-M104-02", "オレンジ色", "9頁 危険ごみ指定袋", "燃やせるごみ・危険ごみ・有害ごみで共通。"),
        ("C-M104-10", "オレンジ色", "10頁 有害ごみ指定袋", "燃やせるごみ・危険ごみ・有害ごみで共通。"),
        ("C-M104-03", "紫色", "13頁 その他プラ指定袋", "その他プラ・ビン缶・PET・リサイクルプラで共通。"),
        ("C-M104-07", "紫色", "15頁 ビン・缶指定袋", "その他プラ・ビン缶・PET・リサイクルプラで共通。"),
        ("C-M104-08", "紫色", "16頁 ペットボトル指定袋", "その他プラ・ビン缶・PET・リサイクルプラで共通。"),
        ("C-M104-09", "紫色", "11頁 リサイクルプラ指定袋", "その他プラ・ビン缶・PET・リサイクルプラで共通。"),
    ]
] + [
    # Kaita: retain all three genuine observations and refuse one false parent color.
    ("C-M109-03", "緑色系", "OFFICIAL_POSTER_GUIDE", "SS-M109-01", "1頁上段 白トレイの資源物帯", "CONFLICTING_EVIDENCE", "白トレイ経路では緑。"),
    ("C-M109-03", "青色系", "STATION_SIGN", "SS-M109-01", "1頁下段 資源回収ステーション左帯", "CONFLICTING_EVIDENCE", "資源回収ステーションでは青。"),
    ("C-M109-03", "黄橙色系", "OFFICIAL_POSTER_GUIDE", "SS-M109-01", "1頁下段 資源物種別帯", "CONFLICTING_EVIDENCE", "資源品目見出しでは黄橙。"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="raise",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def darken(hex_color: str, factor: float = 0.55) -> str:
    values = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(value * factor):02X}" for value in values)


def luminance(hex_color: str) -> float:
    values = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in values]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def text_color(hex_color: str) -> str:
    lum = luminance(hex_color)
    contrast_black = (lum + 0.05) / 0.05
    contrast_white = 1.05 / (lum + 0.05)
    return "#000000" if contrast_black >= contrast_white else "#FFFFFF"


def main() -> None:
    categories = read_csv(CATEGORIES)
    category_index = {row["category_id"].strip(): row for row in categories}
    target_by_municipality = {row[2]: row for row in TARGETS}
    stage_by_municipality = {row[2]: row[1] for row in TARGETS}
    rank_by_municipality = {row[2]: row[0] for row in TARGETS}
    source_by_id = {row[0]: row for row in SOURCES}

    target_rows = [
        {
            "rank": rank,
            "stage": stage,
            "municipality_id": mid,
            "municipality_name": name,
            "canonical_status": canonical_status,
            "style_research_status": research_status,
            "district_scope_required": district_required,
            "current_sort_bucket_count": expected,
            "source_ids": source_ids,
            "note": note,
        }
        for rank, stage, mid, name, canonical_status, research_status, district_required, expected, source_ids, note in TARGETS
    ]

    source_rows = [
        {
            "source_id": sid,
            "municipality_id": mid,
            "district_scope": scope,
            "source_title": title,
            "source_type": source_type,
            "source_url": url,
            "source_locator": locator,
            "evidence_roles": roles,
            "priority": priority,
            "currentness": currentness,
            "official_verified": "TRUE",
            "official_basis": "MUNICIPAL_DOMAIN",
            "checked_date": CHECKED_DATE,
            "note": note,
        }
        for sid, mid, scope, title, source_type, url, locator, roles, priority, currentness, note in SOURCES
    ]

    observations: list[dict[str, object]] = []
    primary_id_by_category: dict[str, str] = {}
    counters: dict[str, int] = {}

    for category_id, spec in PRIMARY.items():
        row = category_index[category_id]
        mid = row["municipality_id"].strip()
        label, display, status, role, source_id, locator, semantic_fit, basis, note = spec
        counters[mid] = counters.get(mid, 0) + 1
        style_id = f"STY-{mid}-{counters[mid]:03d}"
        ui_selection = "PRIMARY" if semantic_fit == "CATEGORY_DISCRIMINATOR" else "NOT_APPLICABLE"
        observations.append({
            "style_id": style_id,
            "rank": rank_by_municipality[mid],
            "stage": stage_by_municipality[mid],
            "municipality_id": mid,
            "district_scope": "MUNICIPALITY_WIDE",
            "category_id": category_id,
            "自治体正式名称": row["自治体正式名称"].strip(),
            "evidence_role": role,
            "official_color_label": label,
            "display_color": display,
            "color_status": status,
            "color_basis": basis,
            "semantic_fit": semantic_fit,
            "ui_selection": ui_selection,
            "source_id": source_id,
            "source_url": source_by_id[source_id][5],
            "source_locator": locator,
            "checked_date": CHECKED_DATE,
            "reviewer": REVIEWER,
            "note": note,
        })
        if ui_selection == "PRIMARY":
            primary_id_by_category[category_id] = style_id

    for category_id, label, role, source_id, locator, semantic_fit, note in SUPPORTING:
        row = category_index[category_id]
        mid = row["municipality_id"].strip()
        counters[mid] = counters.get(mid, 0) + 1
        style_id = f"STY-{mid}-{counters[mid]:03d}"
        supporting_hex = ""
        status = "OFFICIAL_CONFIRMED"
        basis = "公式資料に記載された色名"
        if mid == "M109":
            status = "OFFICIAL_DERIVED"
            basis = "同一公式PDF内の用途別視覚表現"
            supporting_hex = {
                "緑色系": "#4CA13C",
                "青色系": "#2B9DD5",
                "黄橙色系": "#CFAB40",
            }[label]
            note = note + " PDF画像からの近似値。自治体公式HEXではない。"
        observations.append({
            "style_id": style_id,
            "rank": rank_by_municipality[mid],
            "stage": stage_by_municipality[mid],
            "municipality_id": mid,
            "district_scope": "MUNICIPALITY_WIDE",
            "category_id": category_id,
            "自治体正式名称": row["自治体正式名称"].strip(),
            "evidence_role": role,
            "official_color_label": label,
            "display_color": supporting_hex,
            "color_status": status,
            "color_basis": basis,
            "semantic_fit": semantic_fit,
            "ui_selection": "SUPPORTING",
            "source_id": source_id,
            "source_url": source_by_id[source_id][5],
            "source_locator": locator,
            "checked_date": CHECKED_DATE,
            "reviewer": REVIEWER,
            "note": note,
        })

    observations.sort(key=lambda row: (int(row["rank"]), str(row["category_id"]), str(row["style_id"])))

    eligible_ids = {row[2] for row in TARGETS if row[4] == "ACTIVE"}
    expected_categories = [
        row for row in categories
        if row["municipality_id"].strip() in eligible_ids
        and row["ui_role"].strip() == "SORT_BUCKET"
        and row["rule_status"].strip() == "CURRENT"
    ]
    projections: list[dict[str, object]] = []
    for row in sorted(expected_categories, key=lambda item: (rank_by_municipality[item["municipality_id"].strip()], int(item["表示順"]))):
        category_id = row["category_id"].strip()
        mid = row["municipality_id"].strip()
        spec = PRIMARY[category_id]
        label, display, status, _role, _source_id, _locator, semantic_fit, basis, note = spec
        selected = primary_id_by_category.get(category_id, "")
        if status == "NOT_CONFIRMED":
            border = ""
            text = ""
        else:
            border = darken(display)
            text = text_color(display)
        projections.append({
            "projection_id": f"STP-{mid}-{category_id.rsplit('-', 1)[-1]}",
            "rank": rank_by_municipality[mid],
            "municipality_id": mid,
            "district_scope": "MUNICIPALITY_WIDE",
            "category_id": category_id,
            "自治体正式名称": row["自治体正式名称"].strip(),
            "display_color": display,
            "border_color": border,
            "text_color": text,
            "color_status": status,
            "color_basis": basis,
            "selected_style_id": selected,
            "accessibility_label_required": "TRUE",
            "icon_status": "NOT_RESEARCHED_AS_OFFICIAL",
            "checked_date": CHECKED_DATE,
            "reviewer": REVIEWER,
            "note": note if semantic_fit == "CATEGORY_DISCRIMINATOR" else note + " UI接続時はFALLBACKを別状態として適用する。",
        })

    target_fields = ["rank", "stage", "municipality_id", "municipality_name", "canonical_status", "style_research_status", "district_scope_required", "current_sort_bucket_count", "source_ids", "note"]
    source_fields = ["source_id", "municipality_id", "district_scope", "source_title", "source_type", "source_url", "source_locator", "evidence_roles", "priority", "currentness", "official_verified", "official_basis", "checked_date", "note"]
    observation_fields = ["style_id", "rank", "stage", "municipality_id", "district_scope", "category_id", "自治体正式名称", "evidence_role", "official_color_label", "display_color", "color_status", "color_basis", "semantic_fit", "ui_selection", "source_id", "source_url", "source_locator", "checked_date", "reviewer", "note"]
    projection_fields = ["projection_id", "rank", "municipality_id", "district_scope", "category_id", "自治体正式名称", "display_color", "border_color", "text_color", "color_status", "color_basis", "selected_style_id", "accessibility_label_required", "icon_status", "checked_date", "reviewer", "note"]

    write_csv(OUT / "03_top10_targets.csv", target_fields, target_rows)
    write_csv(OUT / "04_stage_a_style_observations.csv", observation_fields, [row for row in observations if row["stage"] == "A"])
    write_csv(OUT / "07_stage_b_style_observations.csv", observation_fields, [row for row in observations if row["stage"] == "B"])
    write_csv(OUT / "08_style_color_observations.csv", observation_fields, observations)
    write_csv(OUT / "08_style_ui_projection.csv", projection_fields, projections)
    write_csv(OUT / "09_style_sources.csv", source_fields, source_rows)

    print("BUILT Style Research Pilot")
    print(f"targets={len(target_rows)}")
    print(f"sources={len(source_rows)}")
    print(f"observations={len(observations)}")
    print(f"projections={len(projections)}")
    print(f"derived={sum(row['color_status'] == 'OFFICIAL_DERIVED' for row in projections)}")
    print(f"not_confirmed={sum(row['color_status'] == 'NOT_CONFIRMED' for row in projections)}")


if __name__ == "__main__":
    main()
