#!/usr/bin/env python3
"""Build Batch 09 from current resident-facing official sources.

Active municipalities: M084, M085, M087-M093.
M086 新庄村 is deferred: the current official link is known, but the full
resident-facing category body cannot be reliably retrieved, so no categories
are synthesized from regional processing plans.
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
OUT = ROOT / "data" / "research" / "batches" / "batch_09"
CHECKED = "2026-08-19"
REVIEWER = "OPENAI_CHATGPT_BATCH09_REVIEW"
NS = "NOT_STATED_IN_CITED_SOURCE"
TARGETS = {"M084", "M085", "M087", "M088", "M089", "M090", "M091", "M092", "M093"}
DEFERRED_MID = "M086"
REGISTRY_FIELDS = ["municipality_id", "host", "authority_type", "authority_name", "verification_url", "verified_date", "notes"]

municipality_specs = {
    "M084": dict(pref="岡山県", city="里庄町", processor="里庄町／井笠広域資源化センター", top="https://www.town.satosho.okayama.jp/site/recycle/", guide="https://www.town.satosho.okayama.jp/site/recycle/1248.html", note="2025年12月改定の住民向け公式案内を採用。燃える・燃えない、資源7系統、粗大を住民選択単位として保持。"),
    "M085": dict(pref="岡山県", city="矢掛町", processor="矢掛町／井笠広域資源化センター", top="https://www.town.yakage.okayama.jp/life/kankyo/gomi.html", guide="https://www.town.yakage.okayama.jp/life/kankyo/gomi.html", note="現行公式ページのトップレベル住民区分を保持。家庭大型ごみ収集サービスを既存の大型不燃区分と二重計上しない。"),
    "M087": dict(pref="岡山県", city="鏡野町", processor="鏡野町", top="https://www.town.kagamino.lg.jp/soshiki/1/1091.html", guide="https://www.town.kagamino.lg.jp/uploaded/attachment/10954.pdf", note="現行ガイド・令和8年度カレンダー・現行基本計画を照合。資源ごみ親＋4公式子葉を保持。"),
    "M088": dict(pref="岡山県", city="勝央町", processor="勝央町／津山圏域クリーンセンター", top="https://www.town.shoo.lg.jp/soshiki/16/1248.html", guide="https://www.town.shoo.lg.jp/soshiki/16/1248.html", note="町公式が明示する7種分別収集をそのまま採用。粗大ごみは7種の通常分別へ人工追加しない。"),
    "M089": dict(pref="岡山県", city="奈義町", processor="奈義町／津山圏域クリーンセンター", top="https://www.town.nagi.okayama.jp/gyousei/kurashi/shinyou_gomi_risaikuru/gomi_risaikuru/gomi_shushu.html", guide="https://www.town.nagi.okayama.jp/gyousei/kurashi/shinyou_gomi_risaikuru/gomi_risaikuru/gomi_shushu.html", note="2026年3月更新ページの定期収集ラベルを採用。複合ラベルを資源・小型不燃・有害の3箱へ人工分割しない。"),
    "M090": dict(pref="岡山県", city="西粟倉村", processor="西粟倉村／美作市", top="https://www.vill.nishiawakura.okayama.jp/wp/%E3%81%94%E3%81%BF%E3%81%AE%E5%87%BA%E3%81%97%E6%96%B9%E3%81%A8%E3%81%94%E3%81%BF%E5%8F%8E%E9%9B%86%E3%82%AB%E3%83%AC%E3%83%B3%E3%83%80%E3%83%BC/", guide="https://www.vill.nishiawakura.okayama.jp/wp/wp-content/uploads/2023/03/0ca6f4a15b068ee9f193023d607dc9f0.pdf", note="村公式令和8年度カレンダーの5収集グループを保持。委託先美作市の詳細区分へ過剰展開しない。"),
    "M091": dict(pref="岡山県", city="久米南町", processor="久米南町", top="https://www.town.kumenan.lg.jp/living/dust_recycle/dust_recycle/bunbetsu.html", guide="https://www.town.kumenan.lg.jp/living/dust_recycle/dust_recycle/bunbetsu.html", note="現行公式分別ページを全件照合。資源9細分を親子構造で保持し、適正処理ごみを独立葉として保持。"),
    "M092": dict(pref="岡山県", city="美咲町", processor="美咲町／津山圏域クリーンセンター", top="https://www.town.okayama-misaki.lg.jp/kurashi/gomi-kankyo/1/1/1916.html", guide="https://www.town.okayama-misaki.lg.jp/kurashi/gomi-kankyo/1/1/1916.html", note="2026年3月更新ページと令和8年度日程表を照合。全町統一の5住民区分を採用。"),
    "M093": dict(pref="岡山県", city="吉備中央町", processor="吉備中央町", top="https://www.town.kibichuo.lg.jp/soshiki/7/4401.html", guide="https://www.town.kibichuo.lg.jp/soshiki/7/4401.html", note="2026年4月更新ページと令和8年度日程表を照合。資源ごみ親＋6公式子葉、粗大2葉、蛍光管を保持。"),
}

source_specs = {
    "M084": [
        ("里庄町でのごみの出し方", "自治体公式Webページ", municipality_specs["M084"]["top"], "2025-12-01", "現行家庭ごみ案内の公式索引"),
        ("資源ごみの分別収集", "自治体公式Webページ", municipality_specs["M084"]["guide"], "2025-12-15", "缶・びん・PET・その他プラ・製品プラ・紙類・古布の7資源区分"),
        ("ごみの出し方（まずこちらをご確認ください）", "自治体公式Webページ", "https://www.town.satosho.okayama.jp/site/recycle/2040.html", "2024-04-01", "燃える・燃えない指定袋と粗大ごみ処理制度"),
    ],
    "M085": [
        ("ごみ", "自治体公式Webページ", municipality_specs["M085"]["guide"], "現行案内中", "ビン・カン・紙・布・ボトル・可燃小/大型・不燃小/大型・水銀・ガレキの住民区分と前処理"),
    ],
    "M087": [
        ("家庭用ごみの分別・出し方ガイドブック", "自治体公式PDF", municipality_specs["M087"]["guide"], "現行配布", "家庭ごみの分別体系・代表品目・前処理"),
        ("令和8年度ごみ収集カレンダー", "自治体公式Webページ", municipality_specs["M087"]["top"], "2026-03-10", "令和8年度に同体系が稼働すること"),
        ("鏡野町一般廃棄物処理基本計画", "自治体公式PDF", "https://www.town.kagamino.lg.jp/uploaded/attachment/14008.pdf", "現行", "可燃・不燃・プラ容器包装・資源4系統・粗大の区分確認"),
    ],
    "M088": [
        ("家庭ごみの出し方", "自治体公式Webページ", municipality_specs["M088"]["guide"], "2024-12-16", "7種分別収集の公式総数と7正式名称"),
        ("環境班／令和8年度ごみカレンダー", "自治体公式Webページ", "https://www.town.shoo.lg.jp/soshiki/16/", "2026-04-01", "令和8年度も家庭ごみ区分が現行であること"),
    ],
    "M089": [
        ("ごみ収集", "自治体公式Webページ", municipality_specs["M089"]["guide"], "2026-03-18", "可燃ごみ、資源ごみ・小型不燃ごみ・有害なごみの現行定期収集ラベル"),
    ],
    "M090": [
        ("ごみの出し方とごみ収集カレンダー", "自治体公式Webページ", municipality_specs["M090"]["top"], "現行案内中", "美作市委託と令和8年度村版カレンダーへの公式導線"),
        ("令和8年度ごみカレンダー（西粟倉版）", "自治体公式PDF", municipality_specs["M090"]["guide"], "令和8年度", "可燃・資源・かん・びん等・古紙の5収集グループ"),
    ],
    "M091": [
        ("ごみの分別", "自治体公式Webページ", municipality_specs["M091"]["guide"], "現行案内中", "資源紙4・資源容器5・適正処理・燃やす・プラ・燃えない・粗大の全区分と前処理"),
    ],
    "M092": [
        ("ごみについて", "自治体公式Webページ", municipality_specs["M092"]["guide"], "2026-03-30", "全町統一分別、指定袋3種、粗大ごみ、令和8年度日程表への公式導線"),
        ("令和8年度ごみ収集日程表（中央地域）", "自治体公式PDF", "https://www.town.okayama-misaki.lg.jp/material/files/group/8/R8gomicalendar_chuo.pdf", "令和8年度", "可燃・不燃・プラ容器包装・資源・粗大の現行収集ラベル"),
    ],
    "M093": [
        ("ごみ（収集・分別）", "自治体公式Webページ", municipality_specs["M093"]["guide"], "2026-04-23", "可燃・不燃・資源各品目・可燃/不燃粗大・蛍光管の現行案内"),
        ("令和8年度吉備中央町ごみ収集日程表", "自治体公式PDF", "https://www.town.kibichuo.lg.jp/uploaded/attachment/12948.pdf", "令和8年度", "11の住民向け収集葉を全件照合"),
    ],
}

categories: list[dict[str, str]] = []

def add(mid: str, name: str, rep: str, *, source: int = 1, parent: str = "", ui: str = "SORT_BUCKET",
        level: str = "PRIMARY", channel: str = "CURBSIDE", forbidden: str = NS, cond: str = "",
        fallback: str = NS, prep: str = NS, bag: str = "", size: str = "", bulky: str = "FALSE",
        note: str = "") -> None:
    categories.append({
        "municipality_id": mid, "自治体正式名称": name, "category_group": parent or name,
        "parent_name": parent, "classification_level": level, "collection_channel": channel,
        "代表品目": rep, "入れてはいけない物": forbidden, "適用条件": cond,
        "条件外の扱い": fallback, "出す前の処理": prep, "袋・容器のルール": bag,
        "サイズ・条件": size, "粗大ごみ扱いか": bulky,
        "予約が必要か": "TRUE" if channel == "BOOKED_PICKUP" else "FALSE",
        "有料か": "FALSE", "料金ルール": "", "自治体収集外か": "FALSE", "注意事項": note,
        "source_index": str(source), "出典ページ・該当箇所": name, "ui_role": ui,
        "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
    })

# M084 Satosho: 2 ordinary + 7 resource + bulky = 10 resident-facing leaves.
add("M084", "燃えるごみ", "可燃性家庭ごみ", source=3, bag="町指定燃えるごみ袋")
add("M084", "燃えないごみ", "不燃性家庭ごみ", source=3, bag="町指定燃えないごみ袋")
for name, rep, prep in [
    ("缶", "アルミ缶・スチール缶", "中身を空にし、品目条件に従って出す"),
    ("びん類", "無色・茶色・緑色・その他色のびん", "中身を空にし、色別条件に従って出す"),
    ("ペットボトル", "PETマークのボトル", "中身を空にし、町指定方法で出す"),
    ("その他プラスチック", "プラスチック製容器包装類", "汚れ等の町指定条件に従って出す"),
    ("製品プラスチック", "対象となるプラスチック製品", "町指定の対象条件に従って出す"),
    ("紙類", "新聞・雑誌/その他紙・段ボール・飲料用紙パック", "紙の種類別条件に従って出す"),
    ("古布", "対象古布", "町指定方法で出す"),
]: add("M084", name, rep, source=2, prep=prep)
add("M084", "粗大ごみ", "指定ごみ袋へ入らない大きな家庭ごみ", source=3, ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE", prep="事前申込み・処理券等、町の粗大ごみ制度に従う")

# M085 Yakage: retain top-level resident headings; do not double count pickup service.
for name, rep, prep, extra in [
    ("ビン（ガラスビン）", "飲食用ガラスびん", "キャップを外し水洗いし、無色透明・茶色・緑色・その他に分ける", {}),
    ("カン（空き缶）", "飲食用アルミ缶・スチール缶", "中身を抜き水洗いし、アルミ缶とスチール缶に分ける", {}),
    ("紙（古紙）", "牛乳パック・段ボール・新聞/チラシ・雑誌/その他", "4種類に分け、各種類をひもで十文字に結束する", {}),
    ("布（古布）", "対象となる古布", "ひもで十文字に結束する", {}),
    ("ボトル（ペットボトル・その他のプラスチック）", "PETボトル・対象プラスチック", "品目別に洗浄・分別条件へ従う", {}),
    ("可燃ごみ［30cm以下の焼却処理のできるごみ］", "30cm以下の可燃性家庭ごみ", "町指定可燃ごみ袋で出す", {}),
    ("可燃ごみ［大型］", "30cmを超える可燃性大型ごみ", "町指定の大型可燃ごみ方法に従う", {"ui":"REFERENCE_ONLY", "channel":"DIRECT_HAUL", "bulky":"TRUE"}),
    ("不燃ごみ［30cm以下の焼却処理のできないごみ］", "30cm以下の不燃性家庭ごみ", "町指定不燃ごみ袋で出す", {}),
    ("不燃ごみ［大型］", "30cmを超える不燃性大型ごみ", "町指定の大型不燃ごみ方法に従う", {"ui":"REFERENCE_ONLY", "channel":"DIRECT_HAUL", "bulky":"TRUE"}),
    ("水銀使用廃製品", "蛍光管・水銀使用製品等", "破損防止など町指定方法に従う", {}),
    ("ガレキ類", "町が受入対象とする家庭由来ガレキ", "指定受入先・条件に従う", {"ui":"REFERENCE_ONLY", "channel":"DIRECT_HAUL"}),
]: add("M085", name, rep, prep=prep, **extra)

# M087 Kagamino: parent resource projection + four official resource leaves.
add("M087", "可燃ごみ", "家庭の可燃ごみ", source=1, prep="町指定方法で出す")
add("M087", "不燃ごみ", "家庭の不燃ごみ", source=1, prep="危険物は安全に保護し町指定方法で出す")
add("M087", "プラスチック容器包装", "プラマークの容器包装", source=1, prep="汚れ等の町指定条件に従う")
add("M087", "資源ごみ", "缶・びん・有害資源・ペットボトル", source=3, level="PRIMARY")
for name, rep, prep in [
    ("缶", "スチール缶・アルミ缶・スプレー缶", "飲食缶は洗う。スプレー缶は中身を使い切る"),
    ("びん", "透明・茶色・その他色のびん", "キャップを外し水洗いし色別に分ける"),
    ("その他（乾電池・蛍光灯・水銀式体温計）", "乾電池・蛍光灯・水銀式体温計", "破損・短絡を避け町指定方法で出す"),
    ("ペットボトル", "PETマークのボトル", "キャップ・ラベルを外し水洗いする"),
]: add("M087", name, rep, source=3, parent="資源ごみ", ui="REFERENCE_ONLY", level="SUBCATEGORY", prep=prep)
add("M087", "粗大ごみ", "指定袋に入らない又は重量のある家庭ごみ", source=1, ui="REFERENCE_ONLY", channel="CURBSIDE", bulky="TRUE", prep="粗大ごみシール等、町指定方法に従う")

# M088 Shoo: official numeric total = seven; bulky route is not an eighth leaf.
for name, rep in [
    ("可燃ごみ", "台所生ごみ・木くず・ゴム・ビニール・皮革・プラスチック製品等"),
    ("資源ごみA", "透明びん・茶色びん・その他びん"),
    ("資源ごみB", "透明PET・アルミ缶・スチール缶・金属類"),
    ("資源ごみC", "紙パック・新聞広告・段ボール・雑誌・雑がみ・古布等"),
    ("資源ごみD", "プラスチック製容器包装・プラスチックのみの製品"),
    ("資源ごみE", "蛍光灯・水銀式体温計・電池類"),
    ("不燃ごみ", "小型家電・ガラス陶磁器・混合素材・刃物等"),
]: add("M088", name, rep, prep="町の7種分別の品目別条件に従う")

# M089 Nagi: preserve current composite collection label instead of synthetic split.
add("M089", "可燃ごみ", "家庭の可燃ごみ", prep="生ごみは水切りし奈義町指定袋で出す", bag="奈義町指定ごみ袋")
add("M089", "資源ごみ・小型不燃ごみ・有害なごみ", "資源物・小型不燃物・有害物", prep="ガイドブックの品目別分別・安全条件に従う")

# M090 Nishiawakura: FY2026 village calendar five resident groups.
for name, rep in [
    ("可燃ごみ", "家庭の可燃ごみ"),
    ("資源ごみ", "プラ製容器包装・発泡スチロール・紙製容器包装・PET等"),
    ("かん類・乾電池類・ライター・スプレー缶", "缶・乾電池・ライター・スプレー缶"),
    ("３色びん・生びん・蛍光灯類・ガラス類・陶器類・廃天ぷら油・刃物・突鋭物等・小型金属類", "びん・蛍光灯・ガラス陶器・廃油・刃物・小型金属等"),
    ("古紙類", "段ボール・新聞紙・雑誌等"),
]: add("M090", name, rep, source=2, prep="令和8年度村版カレンダーおよび委託先の品目別条件に従う")

# M091 Kumenan: resource parent with nine official resource children + five other leaves.
add("M091", "資源ごみ", "紙類・容器類", level="PRIMARY")
for name, rep, prep in [
    ("新聞紙", "新聞紙・折込広告", "紙類4種類の一つとして10kg以下でまとめる"),
    ("段ボール", "段ボール", "紙類4種類の一つとして10kg以下でまとめる"),
    ("紙パック", "対象紙パック", "紙類4種類の一つとして10kg以下でまとめる"),
    ("書籍・雑誌及び資源となる紙類", "書籍・雑誌・資源となる紙", "紙類4種類の一つとして10kg以下でまとめる"),
    ("ペットボトル", "飲料・調味料等の対象PET", "中身・汚れを除き水洗いする"),
    ("アルミ缶及びスチール缶", "飲食用アルミ缶・スチール缶", "中身・汚れを除き水洗いする"),
    ("茶色びん", "飲食用茶色びん", "中身を空にし洗う"),
    ("無色透明びん", "飲食用無色透明びん", "中身を空にし洗う"),
    ("その他の色びん", "飲食用その他色びん", "中身を空にし洗う"),
]: add("M091", name, rep, parent="資源ごみ", ui="REFERENCE_ONLY", level="SUBCATEGORY", prep=prep)
add("M091", "適正処理ごみ", "充電式電池・ボタン電池・乾電池・蛍光管・電球・体温計・スプレー缶等", prep="スプレー缶は必ず使い切り、穴を開けない")
add("M091", "燃やすごみ", "生ごみ・紙くず・ゴム革・汚れたプラスチック等", prep="生ごみは水切り。指定袋10kg以下")
add("M091", "プラスチック類ごみ", "容器包装・対象プラスチック製品", prep="汚れを落とし水切りし、プラスチック以外の部材を外す")
add("M091", "燃えないごみ", "陶磁器・ガラス・金属・小型家電等", prep="割れ物・刃物は紙に包むなど安全に出す")
add("M091", "粗大ごみ", "家具・自転車・中大型電気製品等", ui="REFERENCE_ONLY", bulky="TRUE", prep="1品につき粗大ごみ札1枚。ストーブ等は燃料を抜く")

# M092 Misaki: current townwide five collection labels.
add("M092", "可燃ごみ", "家庭の可燃ごみ", source=1, bag="町指定可燃ごみ袋")
add("M092", "不燃ごみ", "家庭の不燃ごみ", source=1, bag="町指定不燃ごみ袋")
add("M092", "プラスチック製容器包装ごみ", "対象プラスチック製容器包装", source=1, bag="町指定プラスチック製容器包装ごみ袋", note="令和8年度日程表では『プラ容器包装』と短縮表示")
add("M092", "資源ごみ", "缶・びん・PET・古紙・乾電池等", source=2, prep="資源品目ごとの町指定方法で出す")
add("M092", "粗大ごみ", "町指定の大型家庭ごみ", source=1, ui="REFERENCE_ONLY", bulky="TRUE", prep="粗大ごみシールを用いる")

# M093 Kibichuo: resource projection parent + six resource leaves, two coarse leaves, fluorescent.
add("M093", "可燃ごみ", "家庭の可燃ごみ", source=2, bag="町指定可燃ごみ袋")
add("M093", "不燃ごみ", "家庭の不燃ごみ", source=2, bag="町指定不燃ごみ袋")
add("M093", "資源ごみ", "缶・びん・PET・紙・プラスチック・古紙", source=1, level="PRIMARY")
for name, rep, prep in [
    ("缶類", "缶類", "大型収集バッグへ出す"),
    ("びん類", "びん類", "収集コンテナへ出す"),
    ("ペットボトル", "PETボトル", "大型収集バッグへ出す"),
    ("紙パック・段ボール", "紙パック・段ボール", "町指定方法でまとめる"),
    ("その他プラスチック", "その他プラスチック", "大型収集バッグへ出す"),
    ("古新聞・古雑誌", "古新聞・古雑誌", "町指定方法でまとめる"),
]: add("M093", name, rep, source=2, parent="資源ごみ", ui="REFERENCE_ONLY", level="SUBCATEGORY", prep=prep)
add("M093", "可燃粗大", "可燃性粗大ごみ", source=2, ui="REFERENCE_ONLY", bulky="TRUE", prep="町の粗大収集条件に従う")
add("M093", "不燃粗大", "不燃性粗大ごみ", source=2, ui="REFERENCE_ONLY", bulky="TRUE", prep="町の粗大収集条件に従う")
add("M093", "蛍光管", "蛍光管", source=2, prep="年3回の指定回収に破損しないよう出す")


def ensure_deferred() -> None:
    path = MASTER / "05_deferred_municipalities.csv"
    fields, rows = read_csv(path)
    if any(r.get("municipality_id") == DEFERRED_MID for r in rows):
        return
    rows.append({
        "municipality_id": "M086", "都道府県": "岡山県", "市町村": "新庄村", "status": "DEFERRED",
        "reason": "県の現行公式案内から村のごみ収集公式ページへの導線は確認できるが、村公式ページ本文の取得が安定せず住民向け全分別区分を一次資料で全件照合できない。固定IDを保持し後日再開する。",
        "deferred_date": CHECKED, "decision_source": "OFFICIAL_SOURCE_BODY_UNAVAILABLE",
    })
    rows.sort(key=lambda r: r.get("municipality_id", ""))
    write_csv(path, fields, rows)


def ensure_registry() -> None:
    path = MASTER / "02_official_domain_registry.csv"
    fields, rows = read_csv(path)
    fields = fields or REGISTRY_FIELDS
    existing = {(r.get("municipality_id"), r.get("host")) for r in rows}
    for mid, specs in source_specs.items():
        for _, _, url, _, _ in specs:
            host = (urlparse(url).hostname or "").lower()
            if not host or (mid, host) in existing:
                continue
            rows.append({
                "municipality_id": mid, "host": host, "authority_type": "MUNICIPAL_DOMAIN",
                "authority_name": municipality_specs[mid]["city"], "verification_url": municipality_specs[mid]["top"],
                "verified_date": CHECKED, "notes": "Batch 09 official source host",
            })
            existing.add((mid, host))
    rows.sort(key=lambda r: (r.get("municipality_id", ""), r.get("host", "")))
    write_csv(path, fields, rows)


def build_sources() -> list[dict[str, str]]:
    rows = []
    for mid in sorted(TARGETS):
        for i, (title, kind, url, updated, used) in enumerate(source_specs[mid], 1):
            rows.append({
                "municipality_id": mid, "source_id": f"S-{mid}-{i:02d}", "資料名": title, "資料種別": kind,
                "公式URL": url, "発行主体": municipality_specs[mid]["city"], "対象年度": "令和8年度",
                "ページ更新日": updated, "取得確認日": CHECKED, "使用した情報": used, "優先度": str(i),
                "現行性": "現行", "備考": "", "official_verified": "", "official_basis": "", "official_linking_url": "",
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
                "parent_category_id": name_to_id.get(raw["parent_name"], ""),
                "classification_level": raw["classification_level"], "表示順": str(i),
                "collection_channel": raw["collection_channel"], "代表品目": raw["代表品目"],
                "入れてはいけない物": raw["入れてはいけない物"], "適用条件": raw["適用条件"],
                "条件外の扱い": raw["条件外の扱い"], "出す前の処理": raw["出す前の処理"],
                "袋・容器のルール": raw["袋・容器のルール"], "サイズ・条件": raw["サイズ・条件"],
                "粗大ごみ扱いか": raw["粗大ごみ扱いか"], "予約が必要か": raw["予約が必要か"],
                "有料か": raw["有料か"], "料金ルール": raw["料金ルール"], "自治体収集外か": raw["自治体収集外か"],
                "注意事項": raw["注意事項"], "source_id": f"S-{mid}-{sidx:02d}", "出典URL": src[2],
                "出典ページ・該当箇所": raw["出典ページ・該当箇所"], "確認日": CHECKED,
                "ui_role": raw["ui_role"], "rule_status": raw["rule_status"], "effective_from": raw["effective_from"], "effective_to": raw["effective_to"],
            })
    return rows


def leaf_count(mid: str) -> int:
    raws = [r for r in categories if r["municipality_id"] == mid]
    parent_names = {r["parent_name"] for r in raws if r["parent_name"]}
    return sum(1 for r in raws if r["自治体正式名称"] not in parent_names and r["ui_role"] != "EXCLUDED_NOTICE" and r["rule_status"] == "CURRENT")


def build_municipalities() -> list[dict[str, str]]:
    rows = []
    for mid in sorted(TARGETS):
        spec = municipality_specs[mid]
        official_count = "7" if mid == "M088" else ""
        status = "OFFICIAL_COUNT_MATCHED" if mid == "M088" else "MANUAL_INDEX_REVIEW"
        count = leaf_count(mid)
        rows.append({
            "municipality_id": mid, "都道府県": spec["pref"], "市町村": spec["city"], "実装区分": "中国5県全市町村",
            "ごみ処理主体": spec["processor"], "自治体ごみトップURL": spec["top"], "分別ガイドURL": spec["guide"],
            "品目検索URL": "", "やさしい日本語URL": "", "多言語資料URL": "", "対象年度": "令和8年度",
            "最終確認日": CHECKED, "確認ステータス": "QA_REQUIRED", "備考": spec["note"],
            "official_category_count": official_count, "reviewed_category_count": str(count),
            "category_count_basis": "住民が排出時に選択する現行公式分別区分を公式索引・現年度資料で全件照合。",
            "category_count_verified": "TRUE", "category_count_check_status": status,
            "category_count_review_id": f"CR-{mid}-CATEGORY-COVERAGE", "category_count_reviewed_date": CHECKED,
            "category_count_reviewed_by": REVIEWER,
            "search_service_check_status": "NOT_CHECKED", "search_service_check_evidence": "",
            "easy_japanese_check_status": "NOT_CHECKED", "easy_japanese_check_evidence": "",
            "multilingual_check_status": "NOT_CHECKED", "multilingual_check_evidence": "",
        })
    return rows


def build_review_evidence() -> list[dict[str, str]]:
    rows = []
    for mid in sorted(TARGETS):
        for i, src in enumerate(source_specs[mid], 1):
            role = "OFFICIAL_TOTAL" if mid == "M088" and i == 1 else ("PRIMARY_INDEX" if i == 1 else "SUPPLEMENTAL_INDEX")
            rows.append({
                "review_evidence_id": f"CRE-{mid}-{i:02d}", "review_id": f"CR-{mid}-CATEGORY-COVERAGE",
                "municipality_id": mid, "source_id": f"S-{mid}-{i:02d}", "locator": src[4],
                "evidence_role": role, "notes": f"{CHECKED} Batch 09 resident-facing category completeness review",
            })
    return rows


def main() -> None:
    if set(municipality_specs) != TARGETS or set(source_specs) != TARGETS:
        raise ValueError("Batch09 active target mismatch")
    ensure_deferred()
    ensure_registry()
    OUT.mkdir(parents=True, exist_ok=True)
    p = "batch_09_"
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
