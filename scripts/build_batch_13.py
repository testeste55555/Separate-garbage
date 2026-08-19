#!/usr/bin/env python3
"""Build Batch 13 from current resident-facing official sources.

MASTER scope: M126-M135 (remaining Yamaguchi municipalities).
Active: M126, M128-M135 except M127.
Deferred: M127 Mine because three simultaneous regional CURRENT resident
systems have real category/destination differences, not schedule-only variants.
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
OUT = ROOT / "data" / "research" / "batches" / "batch_13"
CHECKED = "2026-08-19"
REVIEWER = "OPENAI_CHATGPT_BATCH13_REVIEW"
NS = "NOT_STATED_IN_CITED_SOURCE"
TARGETS = {"M126","M128","M129","M130","M131","M132","M133","M134","M135"}
DEFERRED = {"M127"}
REGISTRY_FIELDS = ["municipality_id","host","authority_type","authority_name","verification_url","verified_date","notes"]

municipality_specs = {
    "M126": dict(pref="山口県", city="柳井市", processor="柳井市／周東環境衛生組合", top="https://www.city-yanai.jp/site/gomi-risaikuru/", guide="https://www.city-yanai.jp/site/gomi-risaikuru/list144.html", note="令和8年度カレンダーと現行ごみ出しページを照合。ビンと乾電池、ペットボトルと古紙3種は住民が別袋・別束・別回収ボックスへ分けるため公式葉として保持。"),
    "M128": dict(pref="山口県", city="周南市", processor="周南市", top="https://www.city.shunan.lg.jp/soshiki/19/33474.html", guide="https://www.city.shunan.lg.jp/soshiki/19/33474.html", note="市全域向け現行分別冊子を採用。徳山・新南陽・熊毛・鹿野等の地域ページは収集日程差で、taxonomy差ではない。"),
    "M129": dict(pref="山口県", city="山陽小野田市", processor="山陽小野田市", top="https://www.city.sanyo-onoda.lg.jp/soshiki/14/howtotrash3104.html", guide="https://www.city.sanyo-onoda.lg.jp/soshiki/14/howtotrash3104.html", note="市全域向け家庭ごみの出し方を採用。旧小野田・山陽の差は収集時刻・日程で、resident-facing taxonomyは共通。"),
    "M130": dict(pref="山口県", city="周防大島町", processor="周防大島町", top="https://www.town.suo-oshima.lg.jp/garbage-item/search/search.php", guide="https://www.town.suo-oshima.lg.jp/soshiki/16/1268.html", note="現行公式ごみ検索サービスの『種類でさがす』12区分を公式葉として採用。収集不能2区分はEXCLUDED_NOTICEとして公式葉数へ含めない。"),
    "M131": dict(pref="山口県", city="和木町", processor="和木町", top="https://www.town.waki.lg.jp/soshiki/4/214.html", guide="https://www.town.waki.lg.jp/soshiki/4/214.html", note="令和8年度運用を現行ごみ出しページで照合。ページが明示する11住民区分を保持。"),
    "M132": dict(pref="山口県", city="上関町", processor="上関町／周東環境衛生組合", top="https://www.town.kaminoseki.lg.jp/%E3%81%94%E3%81%BF.html", guide="https://www.town.kaminoseki.lg.jp/%E3%81%94%E3%81%BF%E3%81%AE%E5%87%BA%E3%81%97%E6%96%B9%EF%BC%88%E5%AE%9A%E6%9C%9F%E5%8F%8E%E9%9B%86%EF%BC%89.html", note="町全域向け定期収集表を採用。地区別資料は日程差。古紙・紙パックは種類別結束、PETは専用回収ボックスの別経路として保持。"),
    "M133": dict(pref="山口県", city="田布施町", processor="熊南総合事務組合", top="https://www.town.tabuse.lg.jp/soshiki/35/1948.html", guide="https://www.town.tabuse.lg.jp/soshiki/35/1948.html", note="公式の『7分別』は上位見出し数であり、缶と金属は別袋、資源ごみ5品目は種別ごとに分けるためresident-facing official leafは12としてMANUAL_INDEX_REVIEW。"),
    "M134": dict(pref="山口県", city="平生町", processor="熊南総合事務組合", top="https://www.town.hirao.lg.jp/soshiki/kankyo/gomi/seikatsu/teiki_shushu/index.html", guide="https://www.town.hirao.lg.jp/kurashi/gomi_kankyo/gomi/dashikata/index.html", note="公式の7上位分別をそのまま公式葉数へ流用せず、缶・金属の別袋と古紙・古着5種別をresident-facing child leafとして保持。"),
    "M135": dict(pref="山口県", city="阿武町", processor="阿武町／萩・長門清掃一部事務組合", top="https://www.town.abu.lg.jp/guide/gominosyuusyuunituite/", guide="https://www.town.abu.lg.jp/wp/wp-content/uploads/2025/07/R8-Trash-GuideDouble-Side.pdf", note="令和8年4月1日改定を採用。可燃・不燃・資源の3分別は維持したまま同一曜日に出せる運用へ変更。資源袋内部の缶・びん・PET・容器包装プラを人工的な独立categoryへ増やさない。"),
}

# title, kind, url, updated, used, issuer
source_specs = {
    "M126": [
        ("令和8年度柳井市ごみ収集カレンダー", "自治体公式Webページ", "https://www.city-yanai.jp/site/gomi-risaikuru/list141-1221.html", "2026-03-25", "令和8年度も現行ごみ出し体系が運用されること", "柳井市"),
        ("ごみの出し方（カン・金属類）", "自治体公式Webページ", "https://www.city-yanai.jp/site/gomi-risaikuru/gomidashi3.html", "2021-12-24", "カン・金属類の現行排出方法。スプレー缶は使い切り、屋外で穴を開ける", "柳井市"),
        ("ごみの出し方（ビン・乾電池）", "自治体公式Webページ", "https://www.city-yanai.jp/site/gomi-risaikuru/gomidashi4.html", "2024-03-06", "ガラスビンと乾電池を分け、透明袋へ出す", "柳井市"),
        ("ごみの出し方（ペットボトル・古紙）", "自治体公式Webページ", "https://www.city-yanai.jp/site/gomi-risaikuru/gomidashi5.html", "2017-06-08", "PETは指定回収ボックス。古紙は新聞・チラシ／段ボール／雑誌・本・その他の紙の3種別", "柳井市"),
        ("ごみの出し方（可燃ごみ）", "自治体公式Webページ", "https://www.city-yanai.jp/site/gomi-risaikuru/gomidashi1.html", "2022-07-11", "可燃ごみと粗大ごみ境界", "柳井市"),
        ("ごみの出し方（不燃ごみ）", "自治体公式Webページ", "https://www.city-yanai.jp/site/gomi-risaikuru/gomidashi2.html", "2022-07-11", "不燃ごみと電池取り外し等の前処理", "柳井市"),
        ("粗大ごみの出し方", "自治体公式Webページ", "https://www.city-yanai.jp/site/gomi-risaikuru/list138.html", "現行案内中", "粗大ごみの直接搬入・戸別収集経路", "柳井市"),
    ],
    "M128": [
        ("ごみの分別方法について（2024年4月1日～）", "自治体公式Webページ", municipality_specs["M128"]["top"], "2024-04-11", "市全域向け現行分別冊子索引。燃やせる、古紙・衣類、びん・缶類/PET、プラ2区分、燃やせない、使用済小型家電、処理困難物、粗大ごみ", "周南市"),
        ("カセットボンベ、スプレー缶などのごみ出しについて", "自治体公式Webページ", "https://www.city.shunan.lg.jp/soshiki/19/31412.html", "2024-01-31", "処理困難物。中身を使い切り、穴を開ける", "周南市"),
        ("粗大ごみ戸別収集のご案内", "自治体公式Webページ", "https://www.city.shunan.lg.jp/soshiki/19/39046.html", "2024-03-01", "粗大ごみは戸別予約または自己搬入", "周南市"),
    ],
    "M129": [
        ("家庭ごみの出し方", "自治体公式Webページ", municipality_specs["M129"]["top"], "2025-09-01", "市全域向け現行分別体系。燃やせる・燃やせない・空びん・古紙・PET・空かん・古着布類・発泡スチロール白色トレイ・大型ごみ", "山陽小野田市"),
    ],
    "M130": [
        ("ごみの分け方検索", "自治体公式検索サービス", municipality_specs["M130"]["top"], "現行", "種類でさがすの12現行区分と収集不能2通知区分", "周防大島町"),
        ("ごみ分別の手引きを改訂しました", "自治体公式Webページ", municipality_specs["M130"]["guide"], "2023-11-20", "充電式電池を有害ごみへ変更。スプレー缶は使い切れば穴あけ不要", "周防大島町"),
        ("ごみの収集", "自治体公式Webページ", "https://www.town.suo-oshima.lg.jp/soshiki/16/1282.html", "2025-04-01", "各区分の現行処理経路、特定家庭用機器・家庭用パソコンの特殊経路", "周防大島町"),
    ],
    "M131": [
        ("ごみの出し方と収集", "自治体公式Webページ", municipality_specs["M131"]["top"], "現行案内中", "焼却、プラマーク、金属不燃、粗大、PET、リサイクルびん、陶器ガラス、蛍光灯、電池ライタースプレー、新聞雑誌段ボール、衣類の11区分", "和木町"),
    ],
    "M132": [
        ("ごみの出し方（定期収集）", "自治体公式Webページ", municipality_specs["M132"]["guide"], "2024-09-25", "燃える、古紙紙パック、リサイクルビン、ガラス灰、金属、小型家電、空缶、粗大の町全域向け体系", "上関町"),
        ("ペットボトルを正しく出しましょう", "自治体公式広報PDF", "https://www.town.kaminoseki.lg.jp/wp-content/uploads/2025/06/koho202506.pdf", "2025-06", "PETはキャップ・ラベルを外し、洗い、つぶし、専用回収ボックスへ", "上関町"),
    ],
    "M133": [
        ("家庭ごみの出し方（定期収集）", "自治体公式Webページ", municipality_specs["M133"]["top"], "2025-02-19", "7上位分別と定期収集体系", "田布施町／熊南総合事務組合"),
        ("缶・金属の出し方", "自治体公式Webページ", "https://www.town.tabuse.lg.jp/soshiki/35/2087.html", "2025-02-19", "缶と金属を別々の指定袋へ出す", "田布施町／熊南総合事務組合"),
        ("古紙・古着の出し方", "自治体公式Webページ", "https://www.town.tabuse.lg.jp/soshiki/35/2090.html", "2025-02-19", "新聞・雑誌・段ボール・古着・紙パックを種別ごとに分別", "田布施町／熊南総合事務組合"),
    ],
    "M134": [
        ("ごみ収集の概要", "自治体公式Webページ", "https://www.town.hirao.lg.jp/soshiki/kankyo/gomi/seikatsu/teiki_shushu/2888.html", "2025-02-07", "7上位分別と定期収集体系", "平生町／熊南総合事務組合"),
        ("缶・金属の出し方", "自治体公式Webページ", "https://www.town.hirao.lg.jp/kurashi/gomi_kankyo/gomi/dashikata/kankinzoku.html", "2025-02", "缶と金属を別々に排出。スプレー缶は使い切る", "平生町／熊南総合事務組合"),
        ("古紙・古着の出し方", "自治体公式Webページ", "https://www.town.hirao.lg.jp/kurashi/gomi_kankyo/gomi/dashikata/kosihurugi.html", "2025-02-10", "新聞・雑誌・段ボール・古着・紙パックを種別ごとに分けて結束", "平生町／熊南総合事務組合"),
    ],
    "M135": [
        ("ゴミの収集について（R8.4.1更新）", "自治体公式Webページ", municipality_specs["M135"]["top"], "2026-04-01", "令和8年4月1日版ごみ出しガイドブックへの現行導線", "阿武町"),
        ("阿武町ごみの出し方ガイドブック（R8.4.1）", "自治体公式PDF", municipality_specs["M135"]["guide"], "2026-04-01", "可燃・不燃・資源の3指定袋、古紙等の資源回収、大型ごみの現行経路", "阿武町"),
        ("阿武町広報紙 R8.3月号", "自治体公式PDF", "https://www.town.abu.lg.jp/wp/wp-content/uploads/2026/02/d0accf9d244b0de0326bd307ce086f41.pdf", "2026-03", "令和8年4月からの可燃・不燃・資源指定袋と大型ごみ荷票の現行価格", "阿武町"),
        ("大型ごみ予約受付", "自治体公式Webページ", "https://www.town.abu.lg.jp/15875/", "2025-06-30", "大型ごみのLINE予約経路", "阿武町"),
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

# M126 柳井市 — grouped page headings resolve to resident output leaves.
add("M126", "可燃ごみ", "生ごみ・紙くず・プラスチック製品等", source=5, prep="生ごみは水切り。市指定袋へ入れる")
add("M126", "不燃ごみ", "ガラス・陶器・蛍光灯・小型電気製品等", source=6, prep="電池・バッテリーを外す。市指定袋へ入れる")
add("M126", "カン・金属類", "空き缶・金属製品・スプレー缶等", source=2, prep="汚れを除く。スプレー缶は使い切り、火気のない風通しの良い屋外で穴を開ける")
add("M126", "ビン・乾電池", "ガラスビン・乾電池", source=3)
add("M126", "ガラスビン", "飲食用ガラスびん等", source=3, parent="ビン・乾電池", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="乾電池と分け、透明袋へ入れる")
add("M126", "乾電池", "乾電池", source=3, parent="ビン・乾電池", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="ガラスビンと分け、透明袋へ入れる")
add("M126", "ペットボトル・古紙", "ペットボトル・古紙3種類", source=4)
add("M126", "ペットボトル", "PETマークのペットボトル", source=4, parent="ペットボトル・古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="キャップを外し、中をすすぎ、はがせるラベルを外し、横につぶして指定回収ボックスへ")
add("M126", "新聞・チラシ", "新聞・折込チラシ", source=4, parent="ペットボトル・古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="3種類の古紙を分け、種類ごとにひもで結ぶ")
add("M126", "段ボール", "段ボール", source=4, parent="ペットボトル・古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="3種類の古紙を分け、種類ごとにひもで結ぶ")
add("M126", "雑誌・本・その他の紙", "雑誌・本・菓子箱等のその他の紙", source=4, parent="ペットボトル・古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="3種類の古紙を分け、種類ごとにひもで結ぶ")
add("M126", "粗大ごみ", "指定袋に入らない大型家庭ごみ", source=7, ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE", prep=NS, note="直接搬入または戸別収集の公式経路あり")

# M128 周南市 — citywide taxonomy; grouped booklet chapters contain separate resident streams.
add("M128", "燃やせるごみ", "生ごみ・紙くず等", prep="指定袋へ出す")
add("M128", "古紙・衣類", "古紙・衣類")
add("M128", "古紙", "新聞・雑誌・段ボール等", parent="古紙・衣類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="紙種別にまとめる")
add("M128", "衣類", "衣類等", parent="古紙・衣類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=NS)
add("M128", "びん・缶類、ペットボトル", "びん・缶類・ペットボトル")
add("M128", "びん・缶類", "飲食用びん・缶等", parent="びん・缶類、ペットボトル", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中身を空にする")
add("M128", "ペットボトル", "PETマークのボトル", parent="びん・缶類、ペットボトル", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="キャップ・ラベルを外し、中を洗う")
add("M128", "容器包装プラスチック、その他プラスチック", "容器包装プラスチック・その他プラスチック")
add("M128", "容器包装プラスチック", "プラマークの容器包装", parent="容器包装プラスチック、その他プラスチック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="汚れを落とす")
add("M128", "その他プラスチック", "容器包装以外のプラスチック製品", parent="容器包装プラスチック、その他プラスチック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep=NS)
add("M128", "燃やせないごみ", "燃やせない家庭ごみ", prep="電池等を外す")
add("M128", "使用済小型家電", "小型家電", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="回収ボックス対象品は指定回収場所へ")
add("M128", "処理困難物", "乾電池・刃物・スプレー缶・ガラス陶磁器等", source=2, prep="スプレー缶・カセットボンベは中身を使い切り、穴を開ける。透明または半透明袋へ")
add("M128", "粗大ごみ", "45L指定袋に入らない大型家庭ごみ", source=3, ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE", prep="戸別収集を予約するか指定施設へ自己搬入")

# M129 山陽小野田市 — citywide resident taxonomy; old paper is four output streams.
add("M129", "燃やせるごみ", "生ごみ・紙くず等", prep="指定方法で出す")
add("M129", "燃やせないごみ", "陶磁器・ガラス・金属複合品等", prep="危険物は安全に包む")
add("M129", "空びん", "飲食用びん等", prep="ふたを外し、中を洗う")
add("M129", "古紙類", "新聞・雑誌類・ダンボール・紙パック")
add("M129", "新聞", "新聞・折込チラシ", parent="古紙類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="古紙を種類別に分けてまとめる")
add("M129", "雑誌類", "雑誌・雑がみ等", parent="古紙類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="古紙を種類別に分けてまとめる")
add("M129", "ダンボール", "ダンボール", parent="古紙類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="古紙を種類別に分けてまとめる")
add("M129", "紙パック", "牛乳等の紙パック", parent="古紙類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="洗い、開いて乾かす")
add("M129", "ペットボトル", "PETマークのボトル", prep="キャップ・ラベルを外し、中を洗う")
add("M129", "空かん", "飲食用缶等", prep="中身を空にする")
add("M129", "古着・布類", "古着・布類", prep=NS)
add("M129", "発泡スチロール・白色トレイ", "発泡スチロール・白色食品トレイ", prep="汚れを落とす")
add("M129", "大型ごみ", "大型家庭ごみ", ui="REFERENCE_ONLY", bulky="TRUE", prep=NS)

# M130 周防大島町 — current search service explicitly exposes 12 categories.
add("M130", "燃やせるごみ", "生ごみ・可燃性家庭ごみ", prep="町指定袋へ出す")
add("M130", "容器包装プラスチック", "プラマークの容器包装", prep="汚れを落とす")
add("M130", "その他プラスチック", "容器包装以外のプラスチック製品", prep=NS)
add("M130", "空ビン", "空きびん", prep="中を空にする")
add("M130", "ペットボトル", "PETマークのボトル", prep="キャップ・ラベルを外し、中を洗う")
add("M130", "空カン", "飲食用缶・スプレー缶等", source=2, prep="スプレー缶・カセットボンベは必ず中身を使い切る。穴あけ不要")
add("M130", "金属類", "金属製品・小型家電等", prep="電池を取り外す")
add("M130", "埋立ごみ", "陶磁器・ガラス等", prep="危険物は安全に包む")
add("M130", "有害ごみ", "乾電池・蛍光灯・水銀製品・充電式電池・電池を外せない小型家電等", source=2, prep="電池類はテープ等で絶縁する")
add("M130", "粗大ごみ", "大型家庭ごみ", ui="REFERENCE_ONLY", bulky="TRUE", prep=NS)
add("M130", "特定家庭用機器", "テレビ・エアコン・冷蔵庫等", source=3, ui="REFERENCE_ONLY", channel="RETAILER_OR_MAKER", prep=NS)
add("M130", "家庭用パソコン", "家庭用パソコン", source=3, ui="REFERENCE_ONLY", channel="DROP_OFF", prep="町窓口回収または連携業者の回収を利用")
add("M130", "収集できないごみ", "町が収集しない物", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", outside="TRUE", prep=NS)
add("M130", "収集も処理もできないごみ", "町が収集も処理もできない物", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", outside="TRUE", prep=NS)

# M131 和木町 — exact current 11 resident labels.
add("M131", "焼却ごみ", "生ごみ・可燃性家庭ごみ", prep="指定袋へ出す")
add("M131", "プラマークごみ", "プラマークの容器包装", prep="汚れを落とす")
add("M131", "金属・不燃ごみ", "金属製品・不燃物等", prep=NS)
add("M131", "粗大ごみ", "大型家庭ごみ", ui="REFERENCE_ONLY", bulky="TRUE", prep=NS)
add("M131", "ペットボトル", "PETマークのボトル", prep="キャップ・ラベルを外し、中を洗う")
add("M131", "リサイクルびん", "リサイクル対象びん", prep="中を洗う")
add("M131", "陶器・ガラス類", "陶器・ガラス類", prep="割れ物は安全に出す")
add("M131", "蛍光灯類", "蛍光灯類", prep="購入時の保護箱または中身の見える袋等へ入れる")
add("M131", "電池・ライター・スプレー類", "電池・ライター・スプレー缶等", prep="ボンベ・スプレー缶は使い切り、穴を開けずに出す。使い切れないものは袋に『危険』と表示")
add("M131", "新聞・雑誌、ダンボール", "新聞・雑誌・ダンボール", prep="紙ひもでくくる。粘着テープを除く")
add("M131", "リサイクル衣類", "洗濯済みの衣類", prep="洗濯済みのきれいな衣類を指定透明袋へ")

# M132 上関町 — old paper streams separately tied; PET is a dedicated box route.
add("M132", "燃えるごみ", "生ごみ・紙くず・木くず・繊維くず・皮革・ビニール・プラスチック類", prep="生ごみは水切り。町指定袋へ")
add("M132", "古紙・紙パック", "新聞・チラシ・雑誌・段ボール・紙パック")
add("M132", "新聞紙・チラシ", "新聞紙・チラシ", parent="古紙・紙パック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="種類ごとにひもで縛る")
add("M132", "雑誌", "雑誌", parent="古紙・紙パック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="種類ごとにひもで縛る")
add("M132", "段ボール", "段ボール", parent="古紙・紙パック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="種類ごとにひもで縛る")
add("M132", "紙パック", "紙パック", parent="古紙・紙パック", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="種類ごとにひもで縛る")
add("M132", "リサイクルビン", "飲料・食品等のリサイクルびん", prep="水洗いし、キャップを外す")
add("M132", "ガラス・灰類", "灰・陶磁器・ガラス・蛍光灯・電球等", prep="割れたガラスは袋から飛び出さないようにする")
add("M132", "金属類", "スプレー缶・カセットボンベ・鍋等", prep="スプレー缶・カセットボンベは中身を使い切る。穴あけ有無は当該公式ページに明示なし")
add("M132", "小型家電", "扇風機・炊飯器・電気ポット等", prep="電池類を外す")
add("M132", "空缶", "飲料用空き缶", prep="中身を空にする")
add("M132", "粗大ごみ", "定期収集対象外の大型家庭ごみ", ui="REFERENCE_ONLY", channel="DIRECT_HAUL", bulky="TRUE", prep="周東環境衛生組合へ直接持込むか許可業者へ依頼")
add("M132", "ペットボトル", "PETマークのペットボトル", source=2, ui="REFERENCE_ONLY", channel="DROP_OFF", prep="キャップ・ラベルを外し、中を洗い、つぶして専用回収ボックスへ")

# M133 田布施町 — official seven headings resolve to 12 resident output leaves.
add("M133", "可燃ごみ", "生ごみ・紙くず等", prep="生ごみは水切り。指定袋へ")
add("M133", "ガレキ・陶器類・ガラス", "ガレキ・陶器・ガラス等", prep="割れ物等は安全に出す")
add("M133", "缶・金属類", "缶・金属製品", source=2)
add("M133", "缶", "空き缶・スプレー缶・カセットボンベ等", source=2, parent="缶・金属類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中身を出して軽く水洗い。缶と金属を別々の指定袋へ")
add("M133", "金属類", "フライパン・鍋・小型家電等", source=2, parent="缶・金属類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="缶と金属を別々の指定袋へ")
add("M133", "ビン", "空きびん", prep="中を洗う")
add("M133", "大型ごみ", "大型家庭ごみ", ui="REFERENCE_ONLY", channel="DIRECT_HAUL", bulky="TRUE", prep="周東環境衛生組合へ直接搬入")
add("M133", "資源ごみ", "新聞・雑誌・段ボール・古着・紙パック", source=3)
for name, rep in [("新聞","新聞"),("雑誌","雑誌"),("段ボール","段ボール"),("古着","古着"),("紙パック","紙パック")]:
    add("M133", name, rep, source=3, parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="種別ごとに分けて出す")
add("M133", "ペットボトル", "PETマークのペットボトル", prep="ラベル・キャップを外す")

# M134 平生町 — same shared operation, but separately evidenced on Hirao official pages.
add("M134", "可燃ごみ", "生ごみ・紙くず等", prep="生ごみは水切り。緑色指定袋へ")
add("M134", "ガレキ・陶器類・ガラス", "ガレキ・陶器・ガラス等", prep="透明指定袋へ。割れ物等は安全に出す")
add("M134", "缶・金属類", "缶・金属製品", source=2)
add("M134", "缶", "空き缶・スプレー缶・カセットボンベ等", source=2, parent="缶・金属類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="中身を使い切る。缶と金属を分けて出す")
add("M134", "金属類", "フライパン・鍋・小型家電等", source=2, parent="缶・金属類", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="缶と金属を分けて出す")
add("M134", "ビン", "空きびん", prep="中を洗う")
add("M134", "大型ごみ", "大型家庭ごみ", ui="REFERENCE_ONLY", channel="DIRECT_HAUL", bulky="TRUE", prep="周東環境衛生組合へ直接搬入")
add("M134", "資源ごみ", "新聞・雑誌・段ボール・古着・紙パック", source=3)
for name, rep in [("新聞","新聞"),("雑誌","雑誌"),("段ボール","段ボール"),("古着","古着"),("紙パック","紙パック")]:
    add("M134", name, rep, source=3, parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="分別し、種別ごとにまとめて出す")
add("M134", "ペットボトル", "PETマークのペットボトル", prep="ラベル・キャップを外す")

# M135 阿武町 — April 2026 keeps three resident bags; same-day pickup does not collapse sorting.
add("M135", "可燃ごみ", "燃やせる家庭ごみ", source=2, prep="可燃ごみ指定袋へ", bag="可燃ごみ袋")
add("M135", "不燃ごみ", "家電・電池・蛍光灯・陶磁器・ガラス等", source=2, prep="不燃ごみ指定袋へ", bag="不燃ごみ袋")
add("M135", "資源ごみ", "缶・ビン・ペットボトル・容器包装プラスチック等", source=2, prep="資源ごみ指定袋へ。内部品目を住民用独立categoryへ人工分割しない", bag="資源ごみ袋")
add("M135", "大型ごみ", "大型家庭ごみ", source=4, ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE", prep="大型ごみ荷票を使用し、予約経路を利用")
add("M135", "古紙等", "新聞・雑誌広告・ダンボール・紙パック・紙製容器包装類", source=2, ui="REFERENCE_ONLY", channel="DROP_OFF", prep="現行ガイドの資源回収方法に従い拠点へ出す")


def ensure_deferred() -> None:
    path = MASTER / "05_deferred_municipalities.csv"
    fields, rows = read_csv(path)
    existing = {r.get("municipality_id") for r in rows}
    if "M127" not in existing:
        rows.append({
            "municipality_id":"M127","都道府県":"山口県","市町村":"美祢市","status":"DEFERRED",
            "reason":"美祢地域・美東地域・秋芳地域で同時にCURRENTな住民向け分別体系が併存し、固形燃料化できないごみ／その他のごみ／陶磁器類等の正式区分および同一品目の分別先が実際に異なる。現行municipality単位Schema/UIでは住民の地域scopeを安全に解決できないため一旦対象外。固定IDと公式根拠を保持する。",
            "deferred_date":CHECKED,"decision_source":"SCHEMA_SCOPE_LIMITATION",
        })
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
                "verified_date": CHECKED, "notes": f"Batch 13 official source host ({issuer})",
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
            "品目検索URL": municipality_specs[mid]["top"] if mid == "M130" else "", "やさしい日本語URL": "", "多言語資料URL": "", "対象年度": "令和8年度",
            "最終確認日": CHECKED, "確認ステータス": "QA_REQUIRED", "備考": spec["note"],
            "official_category_count": "", "reviewed_category_count": str(leaf_count(mid)),
            "category_count_basis": "住民が排出時に選択する現行公式分別区分を公式索引・現年度資料で全件照合。上位グループは子葉へ二重計上せず、特殊経路はCURRENT公式葉としてREFERENCE_ONLYで保持。",
            "category_count_verified": "TRUE", "category_count_check_status": "MANUAL_INDEX_REVIEW",
            "category_count_review_id": f"CR-{mid}-CATEGORY-COVERAGE", "category_count_reviewed_date": CHECKED,
            "category_count_reviewed_by": REVIEWER, "search_service_check_status": "OFFICIAL_SERVICE_FOUND" if mid == "M130" else "NOT_CHECKED",
            "search_service_check_evidence": municipality_specs[mid]["top"] if mid == "M130" else "",
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
                "notes": f"{CHECKED} Batch 13 resident-facing category completeness review",
            })
    return rows


def main() -> None:
    if set(municipality_specs) != TARGETS or set(source_specs) != TARGETS:
        raise ValueError("Batch13 target mismatch")
    expected = {"M126":10,"M128":11,"M129":12,"M130":12,"M131":11,"M132":12,"M133":12,"M134":12,"M135":5}
    actual = {mid: leaf_count(mid) for mid in sorted(TARGETS)}
    if actual != expected:
        raise ValueError(f"Batch13 leaf count mismatch: {actual}")
    ensure_deferred()
    ensure_registry()
    OUT.mkdir(parents=True, exist_ok=True)
    p = "batch_13_"
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
