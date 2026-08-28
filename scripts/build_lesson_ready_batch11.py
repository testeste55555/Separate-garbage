#!/usr/bin/env python3
"""Build Batch 11 LESSON_READY_10 reviews and learner projections.

This builder starts with M110-M112 and is intentionally data-driven so the
remaining Batch 11 municipalities can be added without cloning another wave
script.  Detailed official rules stay in the review/canonical layer while the
learner projection remains limited to the fixed ten images and major boxes.
"""
from __future__ import annotations

from pathlib import Path

from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "data/research/lesson_readiness"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"
CHECKED = "2026-08-28"
REVIEWER = "OPENAI_CHATGPT_BATCH11_M110_M112_LESSON_READY_10_V1"
TARGETS = {"M110": "熊野町", "M111": "坂町", "M112": "安芸太田町"}

REVIEW_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "canonical_name", "display_name",
    "official_item_wording", "category_id", "category_name", "condition", "preparation",
    "exception_destination", "evidence_basis", "item_evidence_source_id", "item_evidence_url",
    "item_evidence_locator", "branch_review_status", "checked_date", "reviewer", "note",
    "scoring_branch", "exception_evidence_source_id", "exception_evidence_url",
    "exception_evidence_locator",
]
SCOPE_FIELDS = [
    "municipality_id", "municipality_name", "lesson_mode", "scoring_status",
    "required_item_count", "required_branch_count", "review_source", "image_mapping_source", "note",
]
BOX_FIELDS = [
    "municipality_id", "teaching_box_id", "class_mode", "box_kind", "category_id",
    "display_name", "display_order", "note",
]
PROJECTION_FIELDS = [
    "municipality_id", "internal_item_id", "teaching_box_id", "projection_kind",
    "category_id", "review_status", "note",
]

URL = {
    "M110-01": "https://www.town.kumano.lg.jp/8/1/3/2/3569.html",
    "M110-02": "https://www.town.kumano.lg.jp/8/1/3/2/1/3572.html",
    "M110-03": "https://www.town.kumano.lg.jp/material/files/group/4/6903ebcd016.pdf",
    "M110-04": "https://www.town.kumano.lg.jp/material/files/group/11/bunbetsu50onn.xls",
    "M111-01": "https://www.town.saka.lg.jp/2014/04/01/gomi_dashikata/",
    "M111-02": "https://www.town.saka.lg.jp/wp-content/uploads/2014/04/%E3%81%94%E3%81%BF%E5%88%86%E5%88%A5%E8%A1%A8.pdf",
    "M112-02": "https://www.akiota.jp/uploaded/attachment/9504.pdf",
    "M112-03": "https://www.akiota.jp/soshiki/13/17462.html",
}


def review_rows() -> list[dict[str, str]]:
    item_rows = read_csv(ROOT / "data/master/04_common_items_master.csv")[1]
    item_by_id = {row["internal_item_id"]: row for row in item_rows}
    rows: list[dict[str, str]] = []

    def add(
        mid: str, iid: str, wording: str, cid: str, cname: str, condition: str,
        preparation: str, exception: str, basis: str, source_number: str, locator: str,
        note: str, *, scoring: bool = False, exception_locator: str = "",
    ) -> None:
        branch_order = str(1 + sum(r["municipality_id"] == mid and r["internal_item_id"] == iid for r in rows))
        source_id = f"S-{mid}-{source_number}"
        source_url = URL[f"{mid}-{source_number}"]
        item = item_by_id[iid]
        rows.append({
            "municipality_id": mid, "internal_item_id": iid, "branch_order": branch_order,
            "canonical_name": item["一般管理用名称"], "display_name": item["教材表示名"],
            "official_item_wording": wording, "category_id": cid, "category_name": cname,
            "condition": condition, "preparation": preparation, "exception_destination": exception,
            "evidence_basis": basis, "item_evidence_source_id": source_id,
            "item_evidence_url": source_url, "item_evidence_locator": locator,
            "branch_review_status": "COMPLETE", "checked_date": CHECKED, "reviewer": REVIEWER,
            "note": note, "scoring_branch": "TRUE" if scoring else "FALSE",
            "exception_evidence_source_id": source_id, "exception_evidence_url": source_url,
            "exception_evidence_locator": exception_locator or locator,
        })

    # M110 熊野町。I029のみ通常ステーション収集外のため簡略行動へ投影。
    add("M110", "I001", "ペットボトル", "C-M110-02", "資源物（1）", "PETマークの飲料等のボトル", "キャップ・ラベルを外し、洗って乾かす", "汚れが落ちないものは可燃ごみ", "DIRECT_ITEM", "02", "資源物（1）ペットボトル欄", "通常のPETボトルを採点。", scoring=True)
    add("M110", "I001", "汚れが落ちないペットボトル", "C-M110-01", "可燃ごみ", "洗っても汚れが落ちないもの", "中身を除いて可燃ごみへ出す", "洗浄できるPETは資源物（1）", "OFFICIAL_RULE_DERIVED", "02", "資源物（1）ペットボトルの対象外条件", "汚れ条件のみ保持。")
    add("M110", "I004", "飲料用アルミ缶", "C-M110-03", "資源物（2）", "中身を空にした飲料用アルミ缶", "中を洗って出す", "スプレー缶は同区分の個別条件に従う", "DIRECT_ITEM", "04", "50音一覧『アルミ缶』", "通常の飲料缶を採点。", scoring=True)
    add("M110", "I004", "スプレー缶", "C-M110-03", "資源物（2）", "中身を使い切ったスプレー缶", "中身を使い切って指定方法で出す", "飲料缶は洗って出す", "DIRECT_ITEM", "04", "50音一覧『スプレー缶』", "類似缶の条件を保持。")
    add("M110", "I006", "ガラスびん", "C-M110-03", "資源物（2）", "割れていない飲食用ガラスびん", "ふたを外し中を洗う", "割れたガラスは埋立ごみ", "DIRECT_ITEM", "04", "50音一覧『びん』", "通常びんを採点。", scoring=True)
    add("M110", "I006", "割れたガラス", "C-M110-04", "埋立ごみ", "破損したガラスびん", "危険がないよう包んで出す", "割れていない飲食用びんは資源物（2）", "DIRECT_ITEM", "04", "50音一覧『ガラス』", "破損枝を保持。")
    add("M110", "I007", "白色食品トレー", "C-M110-02", "資源物（1）", "汚れを落とした白色食品トレー", "洗って乾かす", "汚れが落ちないものは可燃ごみ", "DIRECT_ITEM", "02", "資源物（1）プラスチック製容器包装欄", "固定画像の白色トレーを採点。", scoring=True)
    add("M110", "I007", "汚れが落ちない食品トレー", "C-M110-01", "可燃ごみ", "汚れが落ちず資源化条件を満たさないもの", "中身を除き可燃ごみへ出す", "洗浄できる対象品は資源物（1）", "DIRECT_ITEM", "02", "資源物（1）の汚れ条件", "汚れ枝を保持。")
    add("M110", "I013", "新聞", "C-M110-02", "資源物（1）", "家庭から出る汚れのない新聞", "新聞としてまとめてひもでしばる", "汚れた紙は可燃ごみ", "DIRECT_ITEM", "02", "資源物（1）新聞欄", "通常新聞を採点。", scoring=True)
    add("M110", "I013", "汚れた新聞", "C-M110-01", "可燃ごみ", "資源化できない汚れた新聞", "可燃ごみへ出す", "資源化できる新聞は資源物（1）", "OFFICIAL_RULE_DERIVED", "04", "50音一覧『新聞』と可燃ごみ条件", "資源化不可枝を保持。")
    add("M110", "I014", "ダンボール", "C-M110-02", "資源物（1）", "家庭から出る汚れのないダンボール", "たたんでひもでしばる", "汚れたものは可燃ごみ", "DIRECT_ITEM", "02", "資源物（1）ダンボール欄", "通常段ボールを採点。", scoring=True)
    add("M110", "I014", "汚れたダンボール", "C-M110-01", "可燃ごみ", "資源化できない汚れたダンボール", "可燃ごみへ出す", "資源化できるものは資源物（1）", "OFFICIAL_RULE_DERIVED", "04", "50音一覧『ダンボール』と可燃ごみ条件", "資源化不可枝を保持。")
    add("M110", "I017", "牛乳パック", "C-M110-02", "資源物（1）", "資源化できる牛乳等の紙パック", "洗い、開いて乾かし、まとめる", "資源化できないものは可燃ごみ", "DIRECT_ITEM", "02", "資源物（1）牛乳パック欄", "通常紙パックを採点。", scoring=True)
    add("M110", "I017", "資源化できない紙パック", "C-M110-01", "可燃ごみ", "汚れや加工で資源化条件を満たさないもの", "中身を除き可燃ごみへ出す", "資源化できる紙パックは資源物（1）", "OFFICIAL_RULE_DERIVED", "04", "50音一覧『紙パック』", "条件外枝を保持。")
    add("M110", "I029", "リチウムイオン電池・モバイルバッテリー", "C-M110-07", "環境事務所へ直接搬入（リチウムイオン電池等）", "家庭から出るモバイルバッテリー", "端子を絶縁し環境事務所へ直接搬入する", "ごみステーションには出さない", "DIRECT_ITEM", "03", "リチウムイオン電池の出し方欄", "非通常経路は正本に保持し教材では回収・確認。", scoring=True)
    add("M110", "I031", "電球", "C-M110-04", "埋立ごみ", "家庭用の電球", "割れないよう安全に出す", "蛍光管は有害ごみ", "DIRECT_ITEM", "04", "50音一覧『電球』", "電球を埋立ごみとして採点。", scoring=True)
    add("M110", "I033", "使い捨てライター", "C-M110-01", "可燃ごみ", "中身を使い切った使い捨てライター", "中身を使い切って出す", "中身が残る状態では出さない", "DIRECT_ITEM", "04", "50音一覧『使い捨てライター』", "使い切った通常枝を採点。", scoring=True)
    add("M110", "I033", "中身が残る使い捨てライター", "C-M110-01", "可燃ごみ", "燃料又はガスが残っている使い捨てライター", "使い切るまでは排出しない", "使い切ったものを可燃ごみへ出す", "DIRECT_ITEM", "04", "50音一覧『使い捨てライター』の条件", "残ガス条件を保持。")

    # M111 坂町。I029のみ町収集外、その他は公式区分へ投影。
    add("M111", "I001", "ペットボトル", "C-M111-13", "ペットボトル", "飲料用PETボトル", "ふたを外して洗う", "対象外・汚れたものはもやせるごみ", "DIRECT_ITEM", "01", "資源ごみ『ペットボトル』欄", "通常PETを採点。", scoring=True)
    add("M111", "I001", "資源化できないペットボトル", "C-M111-01", "もやせるごみ", "資源ごみの条件を満たさないもの", "中身を除きもやせるごみへ出す", "対象PETはペットボトル区分", "OFFICIAL_RULE_DERIVED", "02", "50音分別表『ペットボトル』", "条件外枝を保持。")
    add("M111", "I004", "アルミ缶", "C-M111-07", "缶類", "飲料・食品用アルミ缶", "中を洗って出す", "スプレー缶は使い切り個別条件に従う", "DIRECT_ITEM", "01", "資源ごみ『缶類』欄", "通常缶を採点。", scoring=True)
    add("M111", "I004", "スプレー缶", "C-M111-07", "缶類", "中身を使い切ったスプレー缶", "中身を使い切り町の指定方法で出す", "飲食用缶は洗って出す", "DIRECT_ITEM", "01", "資源ごみ『缶類』スプレー缶条件", "類似缶条件を保持。")
    add("M111", "I006", "ガラスびん", "C-M111-08", "びん類", "割れていない飲食用びん", "ふたを外し中を洗う", "割れたガラスは埋立ごみ", "DIRECT_ITEM", "01", "資源ごみ『びん類』欄", "通常びんを採点。", scoring=True)
    add("M111", "I006", "割れたガラスびん", "C-M111-04", "埋立ごみ", "破損したガラスびん", "危険がないよう包む", "割れていない飲食用びんはびん類", "DIRECT_ITEM", "02", "50音分別表『ガラス・びん』", "破損枝を保持。")
    add("M111", "I007", "白色トレイ", "C-M111-14", "白色トレイ", "白色の食品トレイ", "洗って乾かす", "白色以外・資源化できないものはもやせるごみ", "DIRECT_ITEM", "01", "資源ごみ『白色トレイ』欄", "固定画像の白色トレーを採点。", scoring=True)
    add("M111", "I007", "資源化できない食品トレイ", "C-M111-01", "もやせるごみ", "白色トレイ区分の対象外となるもの", "中身を除きもやせるごみへ出す", "対象の白色トレイは資源ごみ", "OFFICIAL_RULE_DERIVED", "02", "50音分別表『トレイ』", "条件外枝を保持。")
    add("M111", "I013", "新聞", "C-M111-09", "紙類", "家庭から出る汚れのない新聞", "新聞としてまとめてひもでしばる", "汚れた紙はもやせるごみ", "DIRECT_ITEM", "01", "資源ごみ『紙類』欄", "通常新聞を採点。", scoring=True)
    add("M111", "I013", "汚れた新聞", "C-M111-01", "もやせるごみ", "資源化できない汚れた新聞", "もやせるごみへ出す", "資源化できる新聞は紙類", "OFFICIAL_RULE_DERIVED", "02", "50音分別表『新聞』", "資源化不可枝を保持。")
    add("M111", "I014", "ダンボール", "C-M111-11", "ダンボール", "家庭から出る汚れのないダンボール", "たたんでひもでしばる", "汚れたものはもやせるごみ", "DIRECT_ITEM", "01", "資源ごみ『ダンボール』欄", "通常段ボールを採点。", scoring=True)
    add("M111", "I014", "汚れたダンボール", "C-M111-01", "もやせるごみ", "資源化できない汚れたダンボール", "もやせるごみへ出す", "資源化できるものはダンボール区分", "OFFICIAL_RULE_DERIVED", "02", "50音分別表『ダンボール』", "資源化不可枝を保持。")
    add("M111", "I017", "牛乳パック", "C-M111-10", "牛乳パック", "資源化できる牛乳等の紙パック", "洗い、開いて乾かす", "資源化できない紙パックはもやせるごみ", "DIRECT_ITEM", "01", "資源ごみ『牛乳パック』欄", "通常紙パックを採点。", scoring=True)
    add("M111", "I017", "資源化できない紙パック", "C-M111-01", "もやせるごみ", "汚れや加工で資源化条件を満たさないもの", "中身を除きもやせるごみへ出す", "資源化できる牛乳パックは専用区分", "OFFICIAL_RULE_DERIVED", "02", "50音分別表『紙パック』", "条件外枝を保持。")
    add("M111", "I029", "リチウム電池・モバイルバッテリー", "C-M111-15", "町で収集しないごみ（リチウム電池等）", "家庭から出るモバイルバッテリー", "販売店等の回収先を確認する", "町の通常収集には出さない", "DIRECT_ITEM", "02", "50音分別表『リチウム電池』", "非通常経路は正本に保持し教材では回収・確認。", scoring=True)
    add("M111", "I031", "電球", "C-M111-05", "有害ごみ", "家庭用の電球", "破損を防いで出す", "割れたガラス等は埋立ごみの条件を確認", "DIRECT_ITEM", "02", "50音分別表『電球』", "電球を有害ごみとして採点。", scoring=True)
    add("M111", "I033", "使い捨てライター", "C-M111-01", "もやせるごみ", "中身を使い切った使い捨てライター", "ガスを使い切って出す", "中身が残る状態では出さない", "DIRECT_ITEM", "01", "もやせるごみ『使い捨てライター』", "使い切った通常枝を採点。", scoring=True)
    add("M111", "I033", "中身が残る使い捨てライター", "C-M111-01", "もやせるごみ", "燃料又はガスが残っている使い捨てライター", "使い切るまでは排出しない", "使い切ったものをもやせるごみへ出す", "DIRECT_ITEM", "02", "50音分別表『使い捨てライター』の条件", "残ガス条件を保持。")

    # M112 安芸太田町。固定10はすべて通常の公式収集区分へ投影できる。
    add("M112", "I001", "ペットボトル", "C-M112-13", "ペットボトル", "PETマークのペットボトル", "内容物・付着物を除き洗う", "キャップ・ラベルはその他プラスチック", "DIRECT_ITEM", "02", "令和8年版『ペットボトル』欄", "通常PETを採点。", scoring=True)
    add("M112", "I001", "ペットボトルのキャップ・ラベル", "C-M112-14", "その他プラスチック", "ペットボトルから外したキャップ・ラベル", "本体から外してその他プラスチックへ出す", "PET本体はペットボトル区分", "DIRECT_ITEM", "02", "令和8年版プラスチックごみ欄", "関連部材の分別条件を保持。")
    add("M112", "I004", "アルミ缶", "C-M112-03", "缶", "飲料・食品用アルミ缶", "中身を除き、つぶさずに出す", "スプレー缶は使い切り穴あけ不要", "DIRECT_ITEM", "02", "令和8年版『缶』欄", "通常缶を採点。", scoring=True)
    add("M112", "I004", "スプレー缶", "C-M112-03", "缶", "中身を使い切ったスプレー缶", "中身を使い切り、穴を開けずに出す", "飲食用缶は中身を除いて同区分", "DIRECT_ITEM", "02", "令和8年版『缶』欄のスプレー缶条件", "類似缶条件を保持。")
    add("M112", "I006", "ガラスびん", "C-M112-04", "ビン", "割れていない飲食用びん", "内容物・付着物を除き洗う", "割れたガラスは陶器・ガラス類", "DIRECT_ITEM", "02", "令和8年版『ビン』欄", "通常びんを採点。", scoring=True)
    add("M112", "I006", "割れたガラスびん", "C-M112-10", "陶器・ガラス類", "破損したガラスびん", "危険がないよう紙等で包み内容を表示する", "割れていない飲食用びんはビン区分", "DIRECT_ITEM", "02", "令和8年版『陶器・ガラス類』欄", "破損枝を保持。")
    add("M112", "I007", "食品トレイ", "C-M112-14", "その他プラスチック", "家庭から出る対象プラスチック製食品トレイ", "内容物・付着物を除いて出す", "素材・状態により対象外なら燃えるごみ等を確認", "DIRECT_ITEM", "02", "令和8年版『その他プラスチック』欄／食品トレイ", "固定画像の白色食品トレーを採点。", scoring=True)
    add("M112", "I007", "その他の対象食品トレイ", "C-M112-14", "その他プラスチック", "その他プラスチックの対象となる食品トレイ", "内容物・付着物を除いて出す", "対象外素材は該当区分へ出す", "OFFICIAL_RULE_DERIVED", "02", "令和8年版『その他プラスチック』欄", "色だけで別categoryにしない。")
    add("M112", "I013", "新聞", "C-M112-05", "古紙類", "家庭から出る資源化可能な新聞", "ひもでくくり指定方法で出す", "資源化できない紙は燃えるごみ", "DIRECT_ITEM", "02", "令和8年版『古紙類』新聞欄", "通常新聞を採点。", scoring=True)
    add("M112", "I013", "資源化できない新聞", "C-M112-01", "燃えるごみ", "汚れ等で資源化できない新聞", "燃えるごみへ出す", "資源化できる新聞は古紙類", "OFFICIAL_RULE_DERIVED", "02", "令和8年版『新聞』行／燃えるごみ紙類", "条件外枝を保持。")
    add("M112", "I014", "ダンボール", "C-M112-05", "古紙類", "家庭から出る資源化可能なダンボール", "ひもでくくり指定方法で出す", "資源化できないものは燃えるごみ", "DIRECT_ITEM", "02", "令和8年版『古紙類』ダンボール欄", "通常段ボールを採点。", scoring=True)
    add("M112", "I014", "資源化できないダンボール", "C-M112-01", "燃えるごみ", "汚れ等で資源化できないダンボール", "燃えるごみへ出す", "資源化できるものは古紙類", "OFFICIAL_RULE_DERIVED", "02", "令和8年版『ダンボール』行／燃えるごみ紙類", "条件外枝を保持。")
    add("M112", "I017", "紙パック", "C-M112-05", "古紙類", "内側が白く資源化できる紙パック", "洗い、開いて乾かす", "内側が銀色等の対象外品は燃えるごみ", "DIRECT_ITEM", "02", "令和8年版『紙パック』行", "通常牛乳パックを採点。", scoring=True)
    add("M112", "I017", "内側が銀色等の紙パック", "C-M112-01", "燃えるごみ", "古紙類の対象外となる加工紙パック", "中身を除いて燃えるごみへ出す", "資源化できる紙パックは古紙類", "DIRECT_ITEM", "02", "令和8年版『紙パック』行の条件", "加工差を保持。")
    add("M112", "I029", "モバイルバッテリー", "C-M112-09", "小型電化製品及び有害物", "家庭用モバイルバッテリー・小型充電式電池", "端子をテープ等で絶縁して出す", "破損・膨張品も町の案内に従う", "DIRECT_ITEM", "03", "モバイルバッテリー等の出し方欄", "通常の公式収集区分へ投影。", scoring=True)
    add("M112", "I031", "電球・LED電球", "C-M112-09", "小型電化製品及び有害物", "家庭用の電球・LED電球", "破損を防いで出す", "割れたガラス片は安全に包む", "DIRECT_ITEM", "03", "電球・LED・蛍光灯の出し方欄", "電球を公式有害物系子区分として採点。", scoring=True)
    add("M112", "I033", "使い捨てライター", "C-M112-09", "小型電化製品及び有害物", "中身を使い切った使い捨てライター", "中身を使い切り、電池とは別の見える小袋で出す", "中身が残る場合は使い切ってから出す", "DIRECT_ITEM", "02", "令和8年版『小型電化製品及び有害物』ライター欄", "使い切った通常枝を採点。", scoring=True)
    add("M112", "I033", "中身が残る使い捨てライター", "C-M112-09", "小型電化製品及び有害物", "燃料又はガスが残っている使い捨てライター", "使い切るまでは排出しない", "使い切ったものを小型電化製品及び有害物として出す", "DIRECT_ITEM", "02", "令和8年版ライターの排出条件", "残ガス条件を保持。")

    return rows


def build_boxes() -> list[dict[str, str]]:
    spec = {
        "M110": {
            "online": [
                ("C-M110-02", "資源物（1）", "FIXED_10_SCORING"),
                ("C-M110-03", "資源物（2）", "FIXED_10_SCORING"),
                ("C-M110-04", "埋立ごみ", "FIXED_10_SCORING"),
                ("C-M110-01", "可燃ごみ", "FIXED_10_SCORING"),
                ("C-M110-07", "回収・確認", "SIMPLIFIED_ACTION"),
            ],
            "in_person": [(f"C-M110-{i:02d}", n) for i, n in enumerate(["可燃ごみ", "資源物（1）", "資源物（2）", "埋立ごみ", "有害ごみ", "大型ごみ"], 1)],
        },
        "M111": {
            "online": [
                ("C-M111-13", "ペットボトル", "FIXED_10_SCORING"),
                ("C-M111-07", "缶類", "FIXED_10_SCORING"),
                ("C-M111-08", "びん類", "FIXED_10_SCORING"),
                ("C-M111-14", "白色トレイ", "FIXED_10_SCORING"),
                ("C-M111-09", "紙類", "FIXED_10_SCORING"),
                ("C-M111-11", "ダンボール", "FIXED_10_SCORING"),
                ("C-M111-10", "牛乳パック", "FIXED_10_SCORING"),
                ("C-M111-05", "有害ごみ", "FIXED_10_SCORING"),
                ("C-M111-01", "もやせるごみ", "FIXED_10_SCORING"),
                ("C-M111-15", "回収・確認", "SIMPLIFIED_ACTION"),
            ],
            "in_person": [(f"C-M111-{i:02d}", n) for i, n in enumerate(["もやせるごみ", "もえる粗大ごみ", "もえない粗大ごみ", "埋立ごみ", "有害ごみ", "資源ごみ"], 1)],
        },
        "M112": {
            "online": [
                ("C-M112-13", "ペットボトル", "FIXED_10_SCORING"),
                ("C-M112-03", "缶", "FIXED_10_SCORING"),
                ("C-M112-04", "ビン", "FIXED_10_SCORING"),
                ("C-M112-14", "その他プラスチック", "FIXED_10_SCORING"),
                ("C-M112-05", "古紙類", "FIXED_10_SCORING"),
                ("C-M112-09", "小型電化製品及び有害物", "FIXED_10_SCORING"),
            ],
            "in_person": [
                ("C-M112-01", "燃えるごみ"), ("C-M112-02", "資源ごみ"),
                ("C-M112-07", "燃えないごみ"), ("C-M112-12", "プラスチックごみ"),
                ("C-M112-15", "粗大ごみ"),
            ],
        },
    }
    rows: list[dict[str, str]] = []
    for mid in TARGETS:
        for order, (cid, label, kind) in enumerate(spec[mid]["online"], 1):
            rows.append({
                "municipality_id": mid, "teaching_box_id": f"TB-{mid}-ON-{order:02d}",
                "class_mode": "ONLINE_CLASS", "box_kind": kind, "category_id": cid,
                "display_name": label, "display_order": str(order),
                "note": "教材用簡略行動。自治体正式区分ではない。" if kind == "SIMPLIFIED_ACTION" else "固定10品目採点用。",
            })
        for order, (cid, label) in enumerate(spec[mid]["in_person"], 1):
            rows.append({
                "municipality_id": mid, "teaching_box_id": f"TB-{mid}-IP-{order:02d}",
                "class_mode": "IN_PERSON_CLASS", "box_kind": "MAJOR_CATEGORY", "category_id": cid,
                "display_name": label, "display_order": str(order), "note": "対面授業用の主要分別箱。",
            })
    return rows


def build_projection(reviews: list[dict[str, str]], boxes: list[dict[str, str]]) -> list[dict[str, str]]:
    scoring = [row for row in reviews if row["scoring_branch"] == "TRUE"]
    box_by_category = {
        (row["municipality_id"], row["category_id"]): row
        for row in boxes if row["class_mode"] == "ONLINE_CLASS"
    }
    rows = []
    for review in scoring:
        mid, iid, cid = review["municipality_id"], review["internal_item_id"], review["category_id"]
        box = box_by_category[(mid, cid)]
        rows.append({
            "municipality_id": mid, "internal_item_id": iid, "teaching_box_id": box["teaching_box_id"],
            "projection_kind": "SIMPLIFIED_ACTION" if box["box_kind"] == "SIMPLIFIED_ACTION" else "OFFICIAL_CATEGORY",
            "category_id": cid, "review_status": "COMPLETE",
            "note": "非通常収集経路を通常SORT_BUCKETへ誤投影しない。" if box["box_kind"] == "SIMPLIFIED_ACTION" else "公式分別区分へ投影。",
        })
    return rows


def replace_targets(path: Path, fields: list[str], new_rows: list[dict[str, str]]) -> None:
    existing = read_csv(path)[1]
    kept = [row for row in existing if row.get("municipality_id") not in TARGETS]
    write_csv(path, fields, kept + new_rows)


def main() -> None:
    reviews = review_rows()
    by_mid = {mid: [row for row in reviews if row["municipality_id"] == mid] for mid in TARGETS}
    if any(len(rows) != 18 for rows in by_mid.values()):
        raise ValueError({mid: len(rows) for mid, rows in by_mid.items()})
    for mid, rows in by_mid.items():
        write_csv(REVIEW_DIR / f"{mid.lower()}_item_review.csv", REVIEW_FIELDS, rows)
    scope_rows = [
        {
            "municipality_id": mid, "municipality_name": name, "lesson_mode": "ONLINE_CLASS",
            "scoring_status": "LESSON_READY_10", "required_item_count": "10", "required_branch_count": "18",
            "review_source": f"data/research/lesson_readiness/{mid.lower()}_item_review.csv",
            "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
            "note": (
                "画像10品目の全条件枝COMPLETE。I029のみ非通常収集categoryをSIMPLIFIED_ACTIONへ投影。40品目APP_READYではない"
                if mid in {"M110", "M111"}
                else "画像10品目の全条件枝COMPLETE。通常収集categoryへ安全に投影。40品目APP_READYではない"
            ),
        }
        for mid, name in TARGETS.items()
    ]
    boxes = build_boxes()
    projections = build_projection(reviews, boxes)
    replace_targets(SCOPE, SCOPE_FIELDS, scope_rows)
    replace_targets(BOXES, BOX_FIELDS, boxes)
    replace_targets(PROJECTION, PROJECTION_FIELDS, projections)
    print("BATCH11_LESSON_READY_BUILT targets=M110,M111,M112 items=30 branches=54")


if __name__ == "__main__":
    main()
