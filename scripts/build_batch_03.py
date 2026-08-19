#!/usr/bin/env python3
"""Build Batch 03 (M023-M029, M031-M033) from current official sources.

The generator is intentionally conservative: when a cited source does not state a
category detail, it writes NOT_STATED_IN_CITED_SOURCE rather than filling the cell
with a generic sentence. M028 (Yura Town) is kept NOT_REVIEWED/QA_REQUIRED because
the current official web material available to this research pass confirms the
calendar labels but not a complete all-category index.
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
OUT = ROOT / "data" / "research" / "batches" / "batch_03"
CHECKED = "2026-08-19"
REVIEWER = "OPENAI_CHATGPT_BATCH03_REVIEW"
NOT_STATED = "NOT_STATED_IN_CITED_SOURCE"
REGISTRY_FIELDS = [
    "municipality_id", "host", "authority_type", "authority_name",
    "verification_url", "verified_date", "notes",
]

TARGETS = {"M023", "M024", "M025", "M026", "M027", "M028", "M029", "M031", "M032", "M033"}

municipality_specs = {
    "M023": dict(pref="大阪府", city="大阪市", impl="個別指定", processor="大阪市",
        top="https://www.city.osaka.lg.jp/kankyo/page/0000009337.html",
        guide="https://www.city.osaka.lg.jp/kankyo/page/0000009337.html",
        search="https://www.city.osaka.lg.jp/kankyo/page/0000201907.html", year="令和8年度",
        note="定曜日4区分と粗大・拠点回収・電池等の公式導線を照合", review=True),
    "M024": dict(pref="兵庫県", city="神戸市", impl="個別指定", processor="神戸市",
        top="https://www.city.kobe.lg.jp/a04164/kurashi/recycle/gomi/dashikata/index.html",
        guide="https://www.city.kobe.lg.jp/a04164/kurashi/recycle/gomi/dashikata/bunbetsukubun/bunbetsuflowchart.html",
        search="", year="令和8年度", note="家庭ごみ主要6区分と資源・回収協力店の公式導線を照合", review=True),
    "M025": dict(pref="兵庫県", city="豊岡市", impl="個別指定", processor="豊岡市／北但行政事務組合",
        top="https://www.city.toyooka.lg.jp/kurashi/gomikankyo/gomi/1000944/1000945.html",
        guide="https://www.city.toyooka.lg.jp/kurashi/gomikankyo/gomi/1000944/1000945.html",
        search="", year="現行（市の分別区分9分別）", note="公式ページが明示する9分別を全件照合", review=True),
    "M026": dict(pref="兵庫県", city="姫路市", impl="個別指定", processor="姫路市",
        top="https://www.city.himeji.lg.jp/kurashi/category/2-10-3-5-0-0-0-0-0-0.html",
        guide="https://www.city.himeji.lg.jp/kurashi/category/2-10-3-5-0-0-0-0-0-0.html",
        search="https://www.city.himeji.lg.jp/kurashi/0000000097.html", year="令和8年度",
        note="市域共通区分と旧市域・合併地域の地域条件付き区分を分離", review=True),
    "M027": dict(pref="奈良県", city="大和郡山市", impl="個別指定", processor="大和郡山市",
        top="https://www.city.yamatokoriyama.lg.jp/soshiki/cleancenter/gomi_recycle/26/1374.html",
        guide="https://www.city.yamatokoriyama.lg.jp/soshiki/cleancenter/gomi_recycle/26/1374.html",
        search="", year="令和8年度", note="公式ページの可燃・不燃・粗大・有害・PET・資源の6区分を照合", review=True),
    "M028": dict(pref="和歌山県", city="由良町", impl="個別指定", processor="由良町",
        top="https://www.town.yura.wakayama.jp/",
        guide="https://www.town.yura.wakayama.jp/docs/2025122500014/files/202603.pdf",
        search="", year="令和8年度", note="2026年3月公式広報で可燃・プラスチック・不燃・資源・粗大を確認。全区分索引は未確認のためQA_REQUIRED", review=False),
    "M029": dict(pref="鳥取県", city="鳥取市", impl="中国5県全市町村", processor="鳥取市／鳥取県東部広域行政管理組合",
        top="https://www.city.tottori.lg.jp/page/4083.html", guide="https://www.city.tottori.lg.jp/page/4083.html",
        search="", year="令和8年度", note="鳥取地域の現行分別区分と令和8年度収集区分を照合", review=True),
    "M031": dict(pref="鳥取県", city="倉吉市", impl="中国5県全市町村", processor="倉吉市／鳥取中部ふるさと広域連合",
        top="https://www.city.kurayoshi.lg.jp/1878.htm", guide="https://www.city.kurayoshi.lg.jp/1878.htm",
        search="", year="令和8年度", note="保存版分別案内と令和8年度日程表の再生資源・粗大・有害区分を照合", review=True),
    "M032": dict(pref="鳥取県", city="境港市", impl="中国5県全市町村", processor="境港市",
        top="https://www.city.sakaiminato.lg.jp/index.php?view=108858",
        guide="https://www.city.sakaiminato.lg.jp/index.php?view=108858", search="", year="令和8年度",
        note="家庭ごみ案内と市公式モバイル版の分類一覧を照合", review=True),
    "M033": dict(pref="鳥取県", city="岩美町", impl="中国5県全市町村", processor="岩美町／鳥取県東部広域行政管理組合",
        top="https://www.iwami.gr.jp/1112.htm", guide="https://www.iwami.gr.jp/1112.htm", search="", year="令和8年度",
        note="家庭ごみ分別一覧・ごみの出し方と現行実施計画の区分を照合", review=True),
}

source_specs = {
    "M023": [
        ("ごみの出し方", "自治体公式Webページ", "https://www.city.osaka.lg.jp/kankyo/page/0000009337.html", "2026-02-12", "定曜日4区分・粗大・拠点回収への公式索引"),
        ("ごみ分別検索（50音順）", "自治体公式Webページ", "https://www.city.osaka.lg.jp/kankyo/page/0000201907.html", "2026-05-22", "品目別分別導線"),
        ("普通ごみ収集", "自治体公式Webページ", "https://www.city.osaka.lg.jp/kankyo/page/0000009139.html", "2025-10-15", "普通ごみの30cm・棒状1m基準、収集しない物・電池導線"),
    ],
    "M024": [
        ("家庭ごみの出し方・分別", "自治体公式Webページ", "https://www.city.kobe.lg.jp/a04164/kurashi/recycle/gomi/dashikata/calendar/suma/jinbucho.html", "2026", "主要6区分・市で収集しない物・資源回収・協力店回収"),
        ("分別に関するよくあるQ&A", "自治体公式Webページ", "https://www.city.kobe.lg.jp/a04164/kurashi/recycle/gomi/faq/qa.html", "2025", "PETキャップ・ラベル、びん缶等の品目別条件"),
        ("2026年度ワケトンカレンダーパターン一覧", "自治体公式Webページ", "https://www.city.kobe.lg.jp/a04164/kurashi/recycle/gomi/dashikata/calendar/pattern.html", "2026-02-05", "現行主要収集区分"),
    ],
    "M025": [
        ("家庭ごみの出し方", "自治体公式Webページ", "https://www.city.toyooka.lg.jp/kurashi/gomikankyo/gomi/1000944/1000945.html", "2022-07-04", "市の分別区分9分別・指定袋・手引きへの公式索引"),
        ("ごみ出し・分別でよくある間違い", "自治体公式Webページ", "https://www.city.toyooka.lg.jp/kurashi/gomikankyo/gomi/1000944/1009335.html", "2021", "スプレー缶・PET等の条件"),
    ],
    "M026": [
        ("家庭ごみの分け方と出し方", "自治体公式Webページ", "https://www.city.himeji.lg.jp/kurashi/category/2-10-3-5-0-0-0-0-0-0.html", "2026", "全分別見出し・地域条件"),
        ("ごみ分別一覧表", "自治体公式Webページ", "https://www.city.himeji.lg.jp/kurashi/0000000097.html", "2024", "地域別品目・条件・収集外"),
        ("指定ごみ袋制度", "自治体公式Webページ", "https://www.city.himeji.lg.jp/kurashi/0000000255.html", "2026", "可燃・容器包装プラ・ミックスペーパーの袋ルール"),
    ],
    "M027": [
        ("ごみの収集・分別", "自治体公式Webページ", "https://www.city.yamatokoriyama.lg.jp/soshiki/cleancenter/gomi_recycle/26/1374.html", "2025-12-03", "公式6区分・PET・資源・有害"),
        ("ごみの分け方と出し方のルール", "自治体公式Webページ", "https://www.city.yamatokoriyama.lg.jp/soshiki/cleancenter/gomi_recycle/26/15036.html", "2026-05-01", "現行ルール・リチウムイオン電池・収集処理外"),
        ("ごみの出し方、チェックポイント", "自治体公式Webページ", "https://www.city.yamatokoriyama.lg.jp/soshiki/cleancenter/gomi_recycle/26/1376.html", "2021-03-19", "前処理・キャップ・ラベル"),
    ],
    "M028": [
        ("広報ゆら 2026年3月号", "自治体公式PDF", "https://www.town.yura.wakayama.jp/docs/2025122500014/files/202603.pdf", "2026-03", "現行カレンダー上の可燃・プラスチック・不燃・資源・粗大のラベル"),
        ("由良町公式ホームページ", "自治体公式Webページ", "https://www.town.yura.wakayama.jp/", "2026", "生活環境・ごみリサイクル公式導線"),
    ],
    "M029": [
        ("家庭ごみの分別・出し方", "自治体公式Webページ", "https://www.city.tottori.lg.jp/page/4083.html", "2025-10-20", "可燃・プラ・PET・資源・小型破砕・古紙・乾電池蛍光管・有害・大型等"),
        ("令和8年度 収集曜日一覧（鳥取地域）", "自治体公式Webページ", "https://www.city.tottori.lg.jp/page/31552.html", "2026", "現行収集区分・有害ごみ・乾電池等の変更確認"),
    ],
    "M031": [
        ("ごみの分別区分と出し方", "自治体公式Webページ", "https://www.city.kurayoshi.lg.jp/1878.htm", "2026", "保存版パンフレット・個別品目・有害・小型家電・廃食用油への公式索引"),
        ("令和8年度 ごみ収集日程表", "自治体公式Webページ", "https://www.city.kurayoshi.lg.jp/1897.htm", "2026-02-02", "可燃・不燃・再生資源・粗大の現行性"),
    ],
    "M032": [
        ("家庭ごみの分け方出し方", "自治体公式Webページ", "https://www.city.sakaiminato.lg.jp/index.php?view=108858", "2026", "分別カレンダー・軟質プラ・分別早見表への公式索引"),
        ("ごみの分類方法（市公式モバイル版）", "自治体公式Webページ", "https://www.city.sakaiminato.lg.jp/m/index.php?view=1695", "2026", "可燃・資源・不燃・有害・廃食油・粗大・収集外等の分類一覧"),
    ],
    "M033": [
        ("家庭ごみ分別一覧", "自治体公式Webページ", "https://www.iwami.gr.jp/1112.htm", "2026", "家庭ごみガイド・小型家電・乾電池・古紙への公式索引"),
        ("ごみの出し方", "自治体公式Webページ", "https://www.iwami.gr.jp/1111.htm", "2026", "指定袋・資源・PET・乾電池類の出し方"),
    ],
}

categories: list[dict[str, str]] = []


def add(mid: str, name: str, rep: str, *, group: str = "", source: int = 1,
        locator: str = "公式分別見出し", parent: str = "", ui: str = "SORT_BUCKET",
        level: str = "PRIMARY", channel: str = "CURBSIDE", forbidden: str = NOT_STATED,
        fallback: str = NOT_STATED, prep: str = NOT_STATED, bag: str = "", condition: str = "",
        size: str = "", bulky: str = "FALSE", booked: str = "FALSE", paid: str = "FALSE",
        fee: str = "", excluded: str = "FALSE", note: str = "") -> None:
    categories.append({
        "municipality_id": mid, "自治体正式名称": name, "category_group": group or name,
        "parent_name": parent, "classification_level": level, "collection_channel": channel,
        "代表品目": rep, "入れてはいけない物": forbidden, "適用条件": condition,
        "条件外の扱い": fallback, "出す前の処理": prep, "袋・容器のルール": bag,
        "サイズ・条件": size, "粗大ごみ扱いか": bulky, "予約が必要か": booked,
        "有料か": paid, "料金ルール": fee, "自治体収集外か": excluded,
        "注意事項": note, "source_index": str(source), "出典ページ・該当箇所": locator,
        "ui_role": ui,
    })


# M023 大阪市
add("M023", "普通ごみ", "生ごみ・資源化対象外の家庭ごみ", source=3, locator="普通ごみ収集／対象となるごみ", forbidden="資源ごみ・プラスチック資源・古紙衣類・粗大ごみ対象", fallback="各分別区分または粗大ごみ", prep="生ごみは水分を切る", bag="透明または半透明の中身が見える袋", size="最大辺・径30cm以内、棒状1m以内")
add("M023", "資源ごみ", "空き缶・空きびん・ペットボトル・金属製生活用品", locator="定曜日に収集するごみ／資源ごみ", prep="中身を使い切り、容器は軽くすすぐ")
add("M023", "プラスチック資源", "プラマーク容器包装・対象プラスチック製品", locator="定曜日に収集するごみ／プラスチック資源", prep="中身や汚れを取り除く", fallback="汚れが取れない物等は普通ごみ")
add("M023", "古紙・衣類", "新聞・段ボール・紙パック・雑誌その他の紙・衣類", locator="定曜日に収集するごみ／古紙・衣類", prep="古紙は種類別にまとめ、衣類は洗濯して乾かす")
add("M023", "粗大ごみ", "30cmを超える家具等・棒状1m超", locator="粗大ごみへの公式導線", ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE", booked="TRUE", paid="TRUE")
add("M023", "リチウムイオン電池等", "小型充電式電池・モバイルバッテリー・電池内蔵機器", source=3, locator="普通ごみ収集／リチウムイオン電池等の回収", ui="REFERENCE_ONLY", channel="DROP_OFF", forbidden="普通ごみへの混入", fallback="市指定の回収方法", prep="端子を絶縁する")
add("M023", "小型家電回収", "回収対象の使用済小型家電", locator="小型家電リサイクル回収への公式導線", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="個人情報を消去し電池を外す")
add("M023", "拠点回収", "市が指定する資源物", locator="拠点回収への公式導線", ui="REFERENCE_ONLY", channel="DROP_OFF")
add("M023", "大阪市で収集しないもの", "家電4品目・処理困難物等", source=3, locator="普通ごみ収集／大阪市で収集しないもの", ui="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED", excluded="TRUE", forbidden="市の家庭ごみ収集への排出", fallback="販売店・メーカー等へ相談", prep="受入先の指示に従う")

# M024 神戸市
add("M024", "大型ごみ", "指定袋に入らない又は一定重量以上の大型品", locator="ごみの出し方・分別／大型ごみ", ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE", booked="TRUE", paid="TRUE")
add("M024", "燃えないごみ", "陶磁器・ガラス・金属製品等", locator="ごみの出し方・分別／燃えないごみ")
add("M024", "カセットボンベ・スプレー缶", "カセットボンベ・スプレー缶", locator="ごみの出し方・分別／カセットボンベ・スプレー缶", forbidden="燃えないごみ指定袋への混入", prep="中身を使い切る", bag="指定袋以外の中身が見える袋")
add("M024", "燃えるごみ", "生ごみ・紙くず・対象外プラスチック製品等", locator="ごみの出し方・分別／燃えるごみ", prep="生ごみは水切り")
add("M024", "容器包装プラスチック", "プラマーク付き容器包装・PETのキャップとラベル", source=2, locator="Q&A／PETキャップ・ラベル、容器包装プラスチック", forbidden="汚れが簡単に取れない物・製品プラスチック", fallback="燃えるごみ", prep="中身を使い切り汚れを取り除く")
add("M024", "缶・びん・ペットボトル", "飲食用缶・びん・PETマークのボトル", source=2, locator="Q&A／缶・びん・ペットボトル", forbidden="割れたびん・化粧品びん", fallback="燃えないごみ", prep="中身を使い切り軽くすすぐ。PETはキャップとラベルを外す")
add("M024", "資源集団回収", "新聞・段ボール・古着・古布", locator="地域での資源回収", ui="REFERENCE_ONLY", channel="DROP_OFF")
add("M024", "電池類回収ボックス", "モバイルバッテリー・リチウムイオン電池・ボタン電池等", locator="家庭ごみ関連トピックス／電池類回収ボックス", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="端子を絶縁する")
add("M024", "小型家電リサイクル回収", "回収対象の使用済小型家電", locator="回収協力店などで回収／小型家電", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="個人情報を消去し電池を外す")
add("M024", "蛍光管回収", "蛍光管・蛍光灯", locator="回収協力店などで回収／蛍光管", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="破損しないよう保護")
add("M024", "水銀使用製品回収", "水銀式体温計・温度計・血圧計", locator="回収協力店などで回収／水銀式製品", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="破損しないよう保護")
add("M024", "市では収集しないもの", "家電4品目・パソコン・処理困難物等", locator="市では収集しないもの", ui="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED", excluded="TRUE", forbidden="クリーンステーションへの排出", fallback="販売店・メーカー等の指定ルート", prep="受入先の指示に従う")

# M025 豊岡市：公式9分別
add("M025", "燃やすごみ", "生ごみ・紙くず等", locator="市の分別区分9分別／燃やすごみ", bag="燃やすごみ指定袋（赤）", prep="生ごみは水切り")
add("M025", "燃やさないごみ", "陶磁器・ガラス・金属製品等", locator="市の分別区分9分別／燃やさないごみ", bag="燃やさないごみ指定袋（黒）")
add("M025", "蛍光管", "蛍光管・水銀使用製品", locator="市の分別区分9分別／蛍光管", prep="破損しないよう保護")
add("M025", "乾電池類", "乾電池・電池類", locator="市の分別区分9分別／乾電池類", prep="端子を絶縁する")
add("M025", "粗大ごみ", "指定袋に入らない大型品", locator="市の分別区分9分別／粗大ごみ", ui="REFERENCE_ONLY", bulky="TRUE", bag="指定ステッカー", size="収集対象は3辺合計3m以内")
add("M025", "びん・かん", "飲食用びん・缶・使い切ったスプレー缶等", source=2, locator="よくある間違い／びん・缶・スプレー缶", prep="容器は中を空にする。スプレー缶等は使い切り屋外で穴を開ける", bag="資源ごみ指定袋（緑）")
add("M025", "ペットボトル", "PETマークのボトル", source=2, locator="ペットボトルの分別方法", forbidden="キャップ・ラベル", fallback="キャップとラベルはプラスチック製容器包装", prep="キャップとラベルを外し中をすすぐ", bag="資源ごみ指定袋（緑）")
add("M025", "プラスチック製容器包装", "プラマーク付き容器包装", locator="市の分別区分9分別／プラスチック製容器包装", bag="資源ごみ指定袋（緑）")
add("M025", "紙製容器包装", "紙マーク付き容器包装", locator="市の分別区分9分別／紙製容器包装", bag="資源ごみ指定袋（緑）")
add("M025", "市で収集しないもの", "家電リサイクル品・パソコン・危険物・適正処理困難物等", locator="家庭ごみの手引き／市で収集しないものへの公式索引", ui="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー・許可業者等", prep="受入先の指示に従う")

# M026 姫路市：公式メニューの分別見出し。地域限定区分は条件を保持してREFERENCE_ONLY。
for name, rep, locator, bag in [
    ("可燃ごみ", "生ごみ・紙くず等", "家庭ごみ／可燃ごみ", "姫路市可燃ごみ専用指定袋"),
    ("プラスチック製容器包装", "プラマーク付き容器包装", "家庭ごみ／プラスチック製容器包装", "姫路市プラスチック製容器包装指定袋"),
    ("ミックスペーパー", "菓子箱・包装紙等の対象紙", "家庭ごみ／ミックスペーパー", "家庭の紙袋または推奨袋"),
    ("空カン類", "飲食用缶", "家庭ごみ／空カン類", ""),
    ("空ビン類", "飲食用びん", "家庭ごみ／空ビン類", ""),
    ("ペットボトル", "PETマークのボトル", "家庭ごみ／ペットボトル", ""),
    ("紙パック", "飲料用紙パック", "家庭ごみ／紙パック", ""),
    ("古紙類（新聞紙・ダンボール・雑誌類）", "新聞紙・段ボール・雑誌類", "家庭ごみ／古紙類", ""),
    ("乾電池等", "乾電池等", "家庭ごみ／乾電池等", ""),
    ("蛍光管", "蛍光管・電球", "家庭ごみ／蛍光管", ""),
]:
    add("M026", name, rep, locator=locator, bag=bag)
add("M026", "使用済小型家電のリサイクル", "回収対象の使用済小型家電", locator="家庭ごみ／使用済小型家電", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="個人情報を消去し電池類を外す")
regional = [
    ("木製品類（旧姫路市域）", "木製家具・木切れ等", "旧姫路市域"),
    ("金属複合製品類（旧姫路市域）", "金属を含む複合製品・小型家電等", "旧姫路市域"),
    ("プラスチック複合製品類（旧姫路市域）", "容器包装以外の複合プラスチック製品", "旧姫路市域"),
    ("ふとん・ジュータン類", "ふとん・じゅうたん類", "旧姫路市域・夢前町域・香寺町域・安富町域"),
    ("陶磁器類・空ビン以外のガラス類（旧姫路市域）", "陶磁器・ガラス製品", "旧姫路市域"),
    ("大型ごみ（夢前町域・香寺町域・安富町域）", "大型家具等", "夢前町域・香寺町域・安富町域"),
    ("大型ごみ等（家島町域）", "大型品・地域指定品", "家島町域"),
    ("不燃ごみ（夢前町域・香寺町域・安富町域）", "陶磁器・ガラス・金属複合製品等", "夢前町域・香寺町域・安富町域"),
]
for name, rep, cond in regional:
    add("M026", name, rep, locator=f"家庭ごみ／{name}", ui="REFERENCE_ONLY", condition=cond, bulky="TRUE" if "大型" in name or "ふとん" in name else "FALSE")
add("M026", "珪藻土製品（アスベスト含有）", "アスベスト含有の珪藻土製品", locator="家庭ごみ／珪藻土製品（アスベスト含有）", ui="REFERENCE_ONLY", channel="DROP_OFF", note="通常の家庭ごみに混入しない")
add("M026", "市では収集しないもの", "家電4品目・ガスボンベ・液体の油等", source=2, locator="ごみ分別一覧表／市では収集しません", ui="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店等へ相談", prep="受入先の指示に従う")

# M027 大和郡山市：公式6区分
add("M027", "燃えるごみ", "生ごみ・紙くず等", locator="分け方と出し方／燃えるごみ", prep="生ごみは水分をよく切る", bag="ビニール袋")
add("M027", "燃えないごみ", "陶磁器・ガラス・金属等", locator="分け方と出し方／燃えないごみ", bag="ビニール袋")
add("M027", "粗大(大型)ごみ", "家具等の大型品", locator="分け方と出し方／粗大(大型)ごみ", ui="REFERENCE_ONLY", bulky="TRUE")
add("M027", "有害ごみ", "乾電池・蛍光灯・水銀製品・リチウムイオン電池使用製品", source=2, locator="ごみの分け方と出し方のルール／有害ごみ・電池類", forbidden="燃えるごみ・燃えないごみへの混入", prep="電池類は有害ごみ又は専用回収ボックス。膨張品は清掃センターへ直接持参", bag="中身が見える透明系袋")
add("M027", "ペットボトル", "PETマークの飲料・酒・しょうゆ用ボトル", locator="分け方と出し方／ペットボトル", prep="中を洗い、キャップとラベルを外す", bag="中身が見える透明系袋", fallback="キャップは別袋で同時収集")
add("M027", "資源ごみ", "段ボール・古新聞・古雑誌・古布・牛乳パック", locator="分け方と出し方／資源ごみ", channel="DROP_OFF", prep="地域の資源回収等へ出す")
add("M027", "市では収集・処理できないごみ", "家電4品目・処理困難物等", source=2, locator="ごみの分け方と出し方のルール／市では収集、処理できないごみ", ui="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー等", prep="受入先の指示に従う")

# M028 由良町：現行公式広報で確認できるラベルのみ。網羅性はNOT_REVIEWED。
add("M028", "可燃ごみ", NOT_STATED, locator="広報ゆら2026年3月号カレンダー／可燃1・可燃2")
add("M028", "プラスチック", NOT_STATED, locator="広報ゆら2026年3月号カレンダー／プラスチック")
add("M028", "不燃ごみ", NOT_STATED, locator="広報ゆら2026年3月号カレンダー／不燃")
add("M028", "資源ごみ", NOT_STATED, locator="広報ゆら2026年3月号カレンダー／資源1・資源2")
add("M028", "粗大ごみ", NOT_STATED, locator="広報ゆら2026年3月号カレンダー／粗大ごみ", ui="REFERENCE_ONLY", bulky="TRUE")

# M029 鳥取市
add("M029", "可燃ごみ", "生ごみ・紙くず等", locator="家庭ごみ／可燃ごみ", prep="生ごみは水切り")
add("M029", "プラスチックごみ", "プラスチック類の市指定対象物", locator="家庭ごみ／プラスチックごみ")
add("M029", "ペットボトル", "PETマークのボトル", locator="家庭ごみ／ペットボトル", prep="キャップとラベルを外し中をすすぐ")
add("M029", "資源ごみ（ビン・缶）", "飲食用びん・缶", locator="家庭ごみ／資源ごみ（ビン・缶）", prep="中をすすぐ")
add("M029", "小型破砕ごみ", "陶磁器・ガラス・金属・小型製品等", locator="家庭ごみ／小型破砕ごみ")
add("M029", "古紙類", "新聞・雑誌雑がみ・段ボール等", locator="家庭ごみ／古紙類", prep="種類別にまとめる")
add("M029", "乾電池・蛍光管等", "乾電池・ボタン電池・充電式電池・蛍光管等", source=2, locator="令和8年度収集曜日一覧／乾電池等", prep="電池端子を絶縁し蛍光管は破損防止")
add("M029", "有害ごみ", "市指定の有害ごみ対象品", source=2, locator="令和8年度収集曜日一覧／有害ごみ", note="令和6年4月1日開始の区分")
add("M029", "大型ごみ", "大型家具等", locator="家庭ごみ／大型ごみ", ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE")
add("M029", "市で収集・処理しないもの", "家電4品目・処理困難物等", locator="家庭ごみ／市で収集しないもの", ui="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー等", prep="受入先の指示に従う")

# M031 倉吉市。再生資源を教材親にし、公式内訳を葉として保持。
add("M031", "可燃ごみ", "生ごみ・紙くず等", source=2, locator="令和8年度日程表／可燃ごみ", prep="生ごみは水切り")
add("M031", "びん類", "飲食用びん", locator="保存版分別案内／びん類", prep="中をすすぐ")
add("M031", "缶類", "飲食用缶", locator="保存版分別案内／缶類", prep="中をすすぐ")
add("M031", "小型家電", "市指定の小型家電", locator="保存版分別案内／小型家電", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="個人情報を消去し電池を外す")
add("M031", "不燃ごみ", "陶磁器・ガラス・金属等", source=2, locator="令和8年度日程表／不燃ごみ")
add("M031", "有害ごみ", "乾電池・充電池・スプレー缶等の市指定有害品", locator="ごみの出し方／有害ごみ", prep="電池端子を絶縁する")
add("M031", "再生資源", "新聞・雑誌雑紙・段ボール・布類・牛乳パック・発泡スチロール・白色トレー・ペットボトル", source=2, locator="令和8年度日程表／再生資源", ui="SORT_BUCKET")
for name, rep, prep in [
    ("新聞・チラシ広告", "新聞・折込広告", "種類別にまとめる"),
    ("雑誌・雑紙類", "雑誌・雑がみ", "紙以外を外してまとめる"),
    ("段ボール", "段ボール", "折りたたむ"),
    ("布類", "衣類・古布", "洗って乾かす"),
    ("牛乳パック", "飲料用紙パック", "洗って切り開き乾かす"),
    ("発泡スチロール", "発泡スチロール", "汚れを落とす"),
    ("白色トレー", "白色食品トレー", "洗って乾かす"),
    ("ペットボトル", "PETマークのボトル", "キャップとラベルを外し中をすすぐ"),
]:
    add("M031", name, rep, group="再生資源", parent="再生資源", level="SUBCATEGORY", ui="REFERENCE_ONLY", locator=f"保存版分別案内／再生資源／{name}", prep=prep)
add("M031", "可燃性粗大ごみ", "可燃性の大型家具・寝具等", source=2, locator="令和8年度日程表／粗大ごみ", ui="REFERENCE_ONLY", bulky="TRUE")
add("M031", "不燃性粗大ごみ", "不燃性の大型品", source=2, locator="令和8年度日程表／粗大ごみ", ui="REFERENCE_ONLY", bulky="TRUE")
add("M031", "廃食用油", "家庭の使用済み食用油", locator="ごみの出し方／廃食用油のリサイクル", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="異物を除き指定方法で回収へ")
add("M031", "市で収集・処理できないもの", "家電4品目・処理困難物等", locator="家庭電化製品のリサイクル等への公式導線", ui="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー等", prep="受入先の指示に従う")

# M032 境港市
add("M032", "可燃ゴミ", "生ごみ・紙くず等", source=2, locator="市公式モバイル版／可燃ゴミ", prep="生ごみは水切り")
add("M032", "資源ゴミ（ビン缶類）", "飲食用びん・缶", source=2, locator="市公式モバイル版／資源ゴミ（ビン缶類）", prep="中をすすぐ")
add("M032", "資源ゴミ（古紙類）", "新聞・雑誌雑紙・段ボール等", source=2, locator="市公式モバイル版／資源ゴミ（古紙類）", prep="種類別にまとめる")
add("M032", "資源ゴミ（プラスチック）", "市指定の資源プラスチック", source=2, locator="市公式モバイル版／資源ゴミ（プラスチック）")
add("M032", "軟質プラスチック類", "家庭の軟質プラスチック類", locator="家庭ごみの分け方出し方／軟質プラスチック類")
add("M032", "不燃ゴミ", "陶磁器・ガラス・金属等", source=2, locator="市公式モバイル版／不燃ゴミ")
add("M032", "有害ゴミ", "乾電池・蛍光管・水銀製品等", source=2, locator="市公式モバイル版／有害ゴミ", prep="電池を絶縁し破損しやすい物は保護")
add("M032", "廃食油", "家庭の使用済み食用油", source=2, locator="市公式モバイル版／廃食油", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="指定容器・指定方法で回収へ")
add("M032", "粗大ゴミ", "家具・寝具等の大型品", source=2, locator="市公式モバイル版／粗大ゴミ", ui="REFERENCE_ONLY", bulky="TRUE")
add("M032", "収集しないゴミ", "市の収集対象外品", source=2, locator="市公式モバイル版／収集しないゴミ", ui="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー等", prep="受入先の指示に従う")

# M033 岩美町
add("M033", "可燃ごみ", "生ごみ・紙くず等", locator="家庭ごみガイド／可燃ごみ", prep="生ごみは水切り", bag="町指定袋")
add("M033", "古紙類", "新聞・雑誌雑紙・段ボール等", locator="家庭ごみガイド／古紙類", prep="種類別にまとめる")
add("M033", "プラスチックごみ", "町指定のプラスチックごみ", source=2, locator="ごみの出し方／プラスチックごみ", bag="透明または半透明の中身が見える袋")
add("M033", "資源ごみ", "びん・缶等の資源物", source=2, locator="ごみの出し方／資源ごみ", bag="専用容器に直接入れる")
add("M033", "小型破砕ごみ", "陶磁器・ガラス・小型金属製品等", source=2, locator="ごみの出し方／小型破砕ごみ", bag="透明または半透明の中身が見える袋")
add("M033", "大型資源ごみ", "町指定の大型資源物", locator="家庭ごみガイド／大型資源ごみ", ui="REFERENCE_ONLY", bulky="TRUE")
add("M033", "ペットボトル", "PETマークのボトル", source=2, locator="ごみの出し方／ペットボトル", prep="キャップとラベルを外し中をすすぐ", bag="専用容器に直接入れる")
add("M033", "有害ごみ", "蛍光管・水銀製品等の町指定有害品", locator="家庭ごみガイド／有害ごみ", prep="破損しないよう保護")
add("M033", "乾電池類", "乾電池・電池類", source=2, locator="ごみの出し方／乾電池類", prep="端子を絶縁する", bag="透明または半透明の中身が見える袋")
add("M033", "使用済小型電子機器等", "回収対象の使用済小型家電", locator="家庭ごみ分別一覧／小型家電リサイクル", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="個人情報を消去し電池を外す")
add("M033", "衣類等", "衣類・古布等", locator="家庭ごみ分別一覧／衣類等の受け入れ", ui="REFERENCE_ONLY", channel="DROP_OFF", prep="洗って乾かす")
add("M033", "町で収集・処理できないもの", "家電4品目・パソコン・処理困難物等", locator="家庭ごみ分別一覧／家電・パソコン等の公式導線", ui="EXCLUDED_NOTICE", level="EXCLUDED", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー等", prep="受入先の指示に従う")


def ensure_registry() -> None:
    path = MASTER / "02_official_domain_registry.csv"
    fields, rows = read_csv(path)
    fields = fields or REGISTRY_FIELDS
    existing = {(row.get("municipality_id"), row.get("host")) for row in rows}
    for mid, sources in source_specs.items():
        spec = municipality_specs[mid]
        for source in sources:
            host = (urlparse(source[2]).hostname or "").lower()
            key = (mid, host)
            if not host or key in existing:
                continue
            rows.append({
                "municipality_id": mid, "host": host, "authority_type": "MUNICIPAL_DOMAIN",
                "authority_name": spec["city"], "verification_url": spec["top"],
                "verified_date": CHECKED, "notes": "Batch 03 official municipal source host",
            })
            existing.add(key)
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("host", "")))
    write_csv(path, fields, rows)


def build_sources() -> list[dict[str, str]]:
    rows = []
    for mid, specs in source_specs.items():
        for index, (title, kind, url, updated, used) in enumerate(specs, 1):
            rows.append({
                "municipality_id": mid, "source_id": f"S-{mid}-{index:02d}", "資料名": title,
                "資料種別": kind, "公式URL": url, "発行主体": municipality_specs[mid]["city"],
                "対象年度": municipality_specs[mid]["year"], "ページ更新日": updated,
                "取得確認日": CHECKED, "使用した情報": used, "優先度": str(index),
                "現行性": "現行", "備考": "", "official_verified": "",
                "official_basis": "", "official_linking_url": "",
            })
    return rows


def build_categories() -> list[dict[str, str]]:
    rows = []
    by_mid: dict[str, list[dict[str, str]]] = {}
    for raw in categories:
        by_mid.setdefault(raw["municipality_id"], []).append(raw)
    if set(by_mid) != TARGETS:
        raise ValueError(f"Batch 03 target mismatch: {set(by_mid)}")
    for mid, raws in by_mid.items():
        name_to_id = {raw["自治体正式名称"]: f"C-{mid}-{pos:02d}" for pos, raw in enumerate(raws, 1)}
        for pos, raw in enumerate(raws, 1):
            source_index = int(raw["source_index"])
            source = source_specs[mid][source_index - 1]
            rows.append({
                "municipality_id": mid, "category_id": name_to_id[raw["自治体正式名称"]],
                "自治体正式名称": raw["自治体正式名称"], "category_group": raw["category_group"],
                "parent_category_id": name_to_id.get(raw["parent_name"], ""),
                "classification_level": raw["classification_level"], "表示順": str(pos),
                "collection_channel": raw["collection_channel"], "代表品目": raw["代表品目"],
                "入れてはいけない物": raw["入れてはいけない物"], "適用条件": raw["適用条件"],
                "条件外の扱い": raw["条件外の扱い"], "出す前の処理": raw["出す前の処理"],
                "袋・容器のルール": raw["袋・容器のルール"], "サイズ・条件": raw["サイズ・条件"],
                "粗大ごみ扱いか": raw["粗大ごみ扱いか"], "予約が必要か": raw["予約が必要か"],
                "有料か": raw["有料か"], "料金ルール": raw["料金ルール"],
                "自治体収集外か": raw["自治体収集外か"], "注意事項": raw["注意事項"],
                "source_id": f"S-{mid}-{source_index:02d}", "出典URL": source[2],
                "出典ページ・該当箇所": raw["出典ページ・該当箇所"], "確認日": CHECKED,
                "ui_role": raw["ui_role"], "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
            })
    return rows


def optional_status(url: str) -> tuple[str, str]:
    if url:
        return "CHECKED_PRESENT", f"URL:{url}; checked:{CHECKED}"
    return "NOT_CHECKED", ""


def build_municipalities() -> list[dict[str, str]]:
    rows = []
    for mid, spec in municipality_specs.items():
        reviewed = spec["review"]
        search_status, search_evidence = optional_status(spec["search"])
        rows.append({
            "municipality_id": mid, "都道府県": spec["pref"], "市町村": spec["city"],
            "実装区分": spec["impl"], "ごみ処理主体": spec["processor"],
            "自治体ごみトップURL": spec["top"], "分別ガイドURL": spec["guide"],
            "品目検索URL": spec["search"], "やさしい日本語URL": "", "多言語資料URL": "",
            "対象年度": spec["year"], "最終確認日": CHECKED, "確認ステータス": "QA_REQUIRED",
            "備考": spec["note"], "official_category_count": "", "reviewed_category_count": "",
            "category_count_basis": (
                "公式分別見出し・索引と補足資料を全件照合し、CURRENTかつ非EXCLUDED_NOTICEの公式葉区分を記録。"
                if reviewed else "現行公式広報で収集ラベルは確認したが、全区分索引を確認できていない。"
            ),
            "category_count_verified": "TRUE" if reviewed else "FALSE",
            "category_count_check_status": "MANUAL_INDEX_REVIEW" if reviewed else "NOT_REVIEWED",
            "category_count_review_id": f"CR-{mid}-CATEGORY-COVERAGE" if reviewed else "",
            "category_count_reviewed_date": CHECKED if reviewed else "",
            "category_count_reviewed_by": REVIEWER if reviewed else "",
            "search_service_check_status": search_status, "search_service_check_evidence": search_evidence,
            "easy_japanese_check_status": "NOT_CHECKED", "easy_japanese_check_evidence": "",
            "multilingual_check_status": "NOT_CHECKED", "multilingual_check_evidence": "",
        })
    return rows


def build_review_evidence() -> list[dict[str, str]]:
    rows = []
    for mid, specs in source_specs.items():
        if not municipality_specs[mid]["review"]:
            continue
        for index, source in enumerate(specs, 1):
            rows.append({
                "review_evidence_id": f"CRE-{mid}-{index:02d}",
                "review_id": f"CR-{mid}-CATEGORY-COVERAGE", "municipality_id": mid,
                "source_id": f"S-{mid}-{index:02d}", "locator": source[4],
                "evidence_role": "PRIMARY_INDEX" if index == 1 else "SUPPLEMENTAL_INDEX",
                "notes": f"{CHECKED} Batch 03 category completeness review",
            })
    return rows


def main() -> None:
    if set(municipality_specs) != TARGETS:
        raise ValueError(f"municipality spec target mismatch: {set(municipality_specs)}")
    ensure_registry()
    OUT.mkdir(parents=True, exist_ok=True)
    prefix = "batch_03_"
    write_csv(OUT / f"{prefix}municipalities.csv", MUNICIPALITY_FIELDS, build_municipalities())
    write_csv(OUT / f"{prefix}categories.csv", CATEGORY_FIELDS, build_categories())
    write_csv(OUT / f"{prefix}sources.csv", SOURCE_FIELDS, build_sources())
    write_csv(OUT / f"{prefix}qa.csv", QA_FIELDS, [])
    write_csv(OUT / f"{prefix}item_mapping.csv", MAPPING_FIELDS, [])
    write_csv(OUT / f"{prefix}item_coverage.csv", COVERAGE_FIELDS, [])
    write_csv(OUT / f"{prefix}category_review_evidence.csv", CATEGORY_REVIEW_EVIDENCE_FIELDS, build_review_evidence())
    counts = migrate_batch_dir(OUT)
    print(" ".join(f"{key}={value}" for key, value in counts.items()))


if __name__ == "__main__":
    main()
