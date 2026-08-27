#!/usr/bin/env python3
"""Build Batch 11 M107-M109 LESSON_READY_10 audit and teaching projections."""

from __future__ import annotations

from pathlib import Path

from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "data/research/lesson_readiness"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"
CHECKED = "2026-08-27"
REVIEWER = "OPENAI_CODEX_BATCH11_M107_M109_LESSON_READY_10_V1"
TARGETS = {"M107": "江田島市", "M108": "府中町", "M109": "海田町"}

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
    "M107-01": "https://www.city.etajima.hiroshima.jp/cms/articles/download/11923/1/R8_nihonngo.pdf",
    "M107-04": "https://www.city.etajima.hiroshima.jp/cms/files/uploads/29gomishiwake.pdf",
    "M108-01": "https://www.town.fuchu.hiroshima.jp/uploaded/attachment/31359.pdf",
    "M109-01": "https://www.town.kaita.lg.jp/uploaded/life/44980_122640_misc.pdf",
    "M109-03": "https://www.town.kaita.lg.jp/img/koenokouhou/202404/22.html",
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
        source_id = "IS-M109-03" if mid == "M109" and source_number == "03" else f"S-{mid}-{source_number}"
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

    # M107 江田島市。現行ポスターを主根拠とし、電球・ライターのみ公式掲載中の品目別ガイドで補完。
    add("M107", "I001", "ペットボトル", "C-M107-07", "資源ごみ（ペットボトル）", "PETマークのある飲料等のボトル", "キャップとラベルを外し中を洗う", "汚れが落ちないものは燃えるごみ", "DIRECT_ITEM", "01", "資源ごみ（ペットボトル）欄", "画像は通常の洗浄可能なPETボトル。", scoring=True, exception_locator="燃えるごみ欄")
    add("M107", "I001", "汚れが落ちないペットボトル", "C-M107-01", "燃えるごみ", "洗っても汚れが落ちず資源化条件を満たさないもの", "中身を除いて燃えるごみへ出す", "洗浄可能なPETマーク品はペットボトル", "OFFICIAL_RULE_DERIVED", "01", "ペットボトル欄の汚れ条件", "汚れ条件を保持。", exception_locator="資源ごみ（ペットボトル）欄")
    add("M107", "I004", "飲料・食品用アルミ缶", "C-M107-05", "資源ごみ（びん・缶）", "中身を空にした飲料・食品用アルミ缶", "中を洗って出す", "スプレー缶は有害・危険ごみの個別条件", "DIRECT_ITEM", "01", "資源ごみ（びん・缶）欄", "画像は通常の飲料用アルミ缶。", scoring=True, exception_locator="有害・危険ごみ欄")
    add("M107", "I004", "スプレー缶", "C-M107-08", "有害・危険ごみ", "中身を使い切ったスプレー缶", "中身を使い切り市の表示条件に従う", "飲料・食品缶は資源ごみ（びん・缶）", "OFFICIAL_RULE_DERIVED", "01", "有害・危険ごみ欄", "類似缶の危険物枝を保持。", exception_locator="資源ごみ（びん・缶）欄")
    add("M107", "I006", "飲料・食品用ガラスびん", "C-M107-05", "資源ごみ（びん・缶）", "割れていない飲料・食品用びん", "ふたを外し中を洗う", "割れたびんは燃えないごみ", "DIRECT_ITEM", "01", "資源ごみ（びん・缶）欄", "画像は割れていないびん。", scoring=True, exception_locator="燃えないごみ欄")
    add("M107", "I006", "割れたガラスびん", "C-M107-02", "燃えないごみ（埋立てるごみ）", "破損したガラスびん", "危険がないよう安全に扱う", "割れていない飲食用びんは資源ごみ", "OFFICIAL_RULE_DERIVED", "01", "燃えないごみ欄（ガラス類）", "破損枝を保持。", exception_locator="資源ごみ（びん・缶）欄")
    add("M107", "I007", "食品トレー（発泡スチロール）", "C-M107-09", "スーパーなどの回収容器へ（食品トレー（発泡スチロール））", "白色の発泡スチロール製食品トレー", "汚れを落として回収へ回す", "弁当等の非発泡食品トレーは燃えるごみ", "DIRECT_ITEM", "01", "注記『食品トレー（発泡スチロール）はスーパーなどの回収容器へ』", "非通常経路は詳細層に保持し教材では回収・確認へ投影。", scoring=True, exception_locator="燃えるごみ欄『食品トレー（弁当等）』")
    add("M107", "I007", "食品トレー（弁当等）", "C-M107-01", "燃えるごみ", "発泡スチロール製ではない弁当等の食品トレー", "中身を除いて燃えるごみへ出す", "発泡スチロール製食品トレーは店頭回収", "DIRECT_ITEM", "01", "燃えるごみ欄『食品トレー（弁当等）』", "素材差を正本側で保持。", exception_locator="発泡スチロール製食品トレーの注記")
    add("M107", "I013", "新聞", "C-M107-06", "資源ごみ（古紙・布類）", "汚れのない新聞・折込広告", "種類別にまとめる", "汚れた紙は燃えるごみ", "DIRECT_ITEM", "01", "資源ごみ（古紙・布類）欄", "画像は乾いた新聞。", scoring=True, exception_locator="燃えるごみ欄（再生できない紙類）")
    add("M107", "I013", "汚れた新聞", "C-M107-01", "燃えるごみ", "汚れ等で再生できない新聞", "燃えるごみへ出す", "再生可能な新聞は古紙・布類", "OFFICIAL_RULE_DERIVED", "01", "燃えるごみ欄（再生できない紙類）", "禁忌紙枝を保持。", exception_locator="資源ごみ（古紙・布類）欄")
    add("M107", "I014", "ダンボール", "C-M107-06", "資源ごみ（古紙・布類）", "汚れのない家庭のダンボール", "折りたたみ種類別にまとめる", "汚れたものは燃えるごみ", "DIRECT_ITEM", "01", "資源ごみ（古紙・布類）欄", "画像は乾いたダンボール。", scoring=True, exception_locator="燃えるごみ欄（再生できない紙類）")
    add("M107", "I014", "汚れたダンボール", "C-M107-01", "燃えるごみ", "汚れ等で再生できないダンボール", "燃えるごみへ出す", "再生可能品は古紙・布類", "OFFICIAL_RULE_DERIVED", "01", "燃えるごみ欄（再生できない紙類）", "汚れ枝を保持。", exception_locator="資源ごみ（古紙・布類）欄")
    add("M107", "I017", "紙パック", "C-M107-06", "資源ごみ（古紙・布類）", "内側が白く資源化できる紙パック", "洗い開いて乾かす", "アルミ加工・汚れたものは燃えるごみ", "DIRECT_ITEM", "01", "資源ごみ（古紙・布類）欄", "画像は通常紙パック。", scoring=True, exception_locator="燃えるごみ欄（再生できない紙類）")
    add("M107", "I017", "アルミ加工・汚れた紙パック", "C-M107-01", "燃えるごみ", "再生できない加工又は汚れのある紙パック", "中身を除いて燃えるごみへ出す", "資源化できる紙パックは古紙・布類", "OFFICIAL_RULE_DERIVED", "01", "燃えるごみ欄（再生できない紙類）", "加工差を保持。", exception_locator="資源ごみ（古紙・布類）欄")
    add("M107", "I029", "モバイルバッテリー", "C-M107-08", "有害・危険ごみ", "家庭用モバイルバッテリー", "端子を絶縁して出す", "膨張・破損品は市へ確認", "DIRECT_ITEM", "01", "有害・危険ごみ欄（モバイルバッテリー）", "通常の有害・危険ごみとして安全に採点。", scoring=True)
    add("M107", "I031", "電球・LED電球", "C-M107-08", "有害・危険ごみ", "家庭用の電球又はLED電球", "破損を防いで出す", "蛍光管も有害・危険ごみ", "DIRECT_ITEM", "04", "分別一覧『電球』『LED電球』の行", "公式掲載中の品目別ガイドで補完。", scoring=True)
    add("M107", "I033", "使い捨てライター", "C-M107-08", "有害・危険ごみ", "中身を使い切った使い捨てライター", "中身を使い切って出す", "金属製ライターは燃えない粗大ごみ", "DIRECT_ITEM", "04", "分別一覧『使い捨てライター』の行", "画像は使い切った通常枝。", scoring=True, exception_locator="分別一覧『ライター（金属製）』の行")
    add("M107", "I033", "中身が残る使い捨てライター", "C-M107-08", "有害・危険ごみ", "燃料又はガスが残っている使い捨てライター", "中身を使い切るまでは排出しない", "使い切ったものを有害・危険ごみへ出す", "DIRECT_ITEM", "04", "分別一覧『ライター（使い捨て）』の行", "残ガス条件を保持。", exception_locator="分別一覧『使い捨てライター』の行")

    # M108 府中町。
    add("M108", "I001", "ペットボトル", "C-M108-09", "ペットボトル", "PETマークがあり汚れを落とせるもの", "キャップとラベルを外し汚れを落とす", "汚れが落ちないものは普通ごみ", "DIRECT_ITEM", "01", "7頁 ペットボトル欄", "画像は通常PET。", scoring=True, exception_locator="7頁 汚れが落ちないものの注記")
    add("M108", "I001", "汚れが落ちないペットボトル", "C-M108-01", "普通ごみ", "洗っても汚れが落ちないもの", "中身を除き普通ごみへ出す", "洗浄可能品はペットボトル", "DIRECT_ITEM", "01", "7頁 ペットボトル欄の注記", "汚れ枝を保持。", exception_locator="7頁 ペットボトル欄")
    add("M108", "I004", "アルミ缶", "C-M108-06", "ビン・缶", "中身を空にした飲料・食品用アルミ缶", "中身を空にして出す", "スプレー缶は中身を使い切る", "DIRECT_ITEM", "01", "5頁 有価物『ビン・缶』欄", "画像は通常缶。", scoring=True)
    add("M108", "I004", "スプレー缶・カセットボンベ", "C-M108-06", "ビン・缶", "中身を使い切ったスプレー缶等", "中身を使い切って出す", "飲料缶は中身を空にして同区分", "OFFICIAL_RULE_DERIVED", "01", "5頁 有価物『ビン・缶』欄の条件", "類似缶条件を保持。")
    add("M108", "I006", "ガラスびん", "C-M108-06", "ビン・缶", "割れていない飲食用びん", "ふたを外し中身を空にする", "割れたびんは埋立ごみ", "DIRECT_ITEM", "01", "5頁 有価物『ビン・缶』欄", "画像は通常びん。", scoring=True, exception_locator="6頁 埋立ごみ欄")
    add("M108", "I006", "割れたガラスびん", "C-M108-07", "埋立ごみ", "破損したガラスびん", "安全に包み内容を表示する", "割れていない飲食用びんはビン・缶", "OFFICIAL_RULE_DERIVED", "01", "6頁 埋立ごみ欄", "破損枝を保持。", exception_locator="5頁 有価物『ビン・缶』欄")
    add("M108", "I007", "白色トレイ", "C-M108-11", "白色トレイ", "白色の発泡スチロール製食品トレイで汚れを落としたもの", "汚れを落として出す", "色柄・汚れたものは普通ごみ又は店頭回収条件", "DIRECT_ITEM", "01", "7頁 白色トレイ欄", "画像は白色の通常枝。", scoring=True, exception_locator="7頁 白色トレイの対象外注記")
    add("M108", "I007", "色柄又は汚れたトレイ", "C-M108-01", "普通ごみ", "白色トレイ区分の対象外となる色柄又は汚れたもの", "普通ごみへ出す", "店頭回収を使う場合は回収先条件に従う", "DIRECT_ITEM", "01", "7頁 白色トレイの対象外注記", "対象外・店頭回収情報を詳細層だけに保持。")
    add("M108", "I013", "新聞", "C-M108-03", "新聞・雑誌・雑がみ", "家庭から出る汚れのない新聞", "ひもでしばって出す", "汚れた紙は普通ごみ", "DIRECT_ITEM", "01", "5頁 有価物『新聞・雑誌・雑がみ』欄", "画像は通常新聞。", scoring=True, exception_locator="4頁 普通ごみ欄")
    add("M108", "I013", "汚れた新聞", "C-M108-01", "普通ごみ", "資源化できない汚れのある新聞", "普通ごみへ出す", "資源化できる新聞は有価物", "OFFICIAL_RULE_DERIVED", "01", "4頁 普通ごみ欄（紙くず）", "汚れ枝を保持。", exception_locator="5頁 新聞欄")
    add("M108", "I014", "ダンボール", "C-M108-04", "ダンボール", "家庭から出る汚れのないダンボール", "たたんでひもでしばる", "汚れたものは普通ごみ", "DIRECT_ITEM", "01", "5頁 有価物『ダンボール』欄", "画像は通常段ボール。", scoring=True, exception_locator="4頁 普通ごみ欄")
    add("M108", "I014", "汚れたダンボール", "C-M108-01", "普通ごみ", "資源化できない汚れのあるダンボール", "普通ごみへ出す", "資源化できるものはダンボール", "OFFICIAL_RULE_DERIVED", "01", "4頁 普通ごみ欄（紙くず）", "汚れ枝を保持。", exception_locator="5頁 ダンボール欄")
    add("M108", "I017", "紙パック", "C-M108-10", "紙パック", "内側にアルミ箔がなく汚れを落とした紙パック", "ストロー等を外し洗って出す", "内側アルミ箔付きは普通ごみ", "DIRECT_ITEM", "01", "7頁 紙パック欄", "画像は通常紙パック。", scoring=True, exception_locator="7頁 アルミ箔付き注記")
    add("M108", "I017", "内側アルミ箔付き紙パック", "C-M108-01", "普通ごみ", "内側にアルミ箔が付いた紙パック", "中身を除いて普通ごみへ出す", "アルミ箔なしは紙パック", "DIRECT_ITEM", "01", "7頁 紙パック欄の注記", "加工差を保持。", exception_locator="7頁 紙パック欄")
    add("M108", "I029", "モバイルバッテリー", "C-M108-08", "有害ごみ", "家庭用モバイルバッテリー", "電極をテープで絶縁して出す", "販売店等への返却も案内される", "DIRECT_ITEM", "01", "6頁 有害ごみ欄『モバイルバッテリー』", "通常有害ごみが公式に明記されるためOFFICIAL_CATEGORY。", scoring=True)
    add("M108", "I031", "白熱球（LED含む）", "C-M108-07", "埋立ごみ", "白熱電球又はLED電球", "割れないよう安全に出す", "蛍光管は有害ごみ", "DIRECT_ITEM", "01", "6頁 埋立ごみ欄『白熱球（LED含む）』", "電球種別を明示。", scoring=True, exception_locator="6頁 有害ごみ欄（蛍光管）")
    add("M108", "I033", "ライター", "C-M108-01", "普通ごみ", "中身を使い切った使い捨てライター", "中身を使い切るかガスを抜く", "中身が残る状態では出さない", "DIRECT_ITEM", "01", "4頁 普通ごみ欄『ライター』", "画像は使い切った通常枝。", scoring=True)
    add("M108", "I033", "中身が残るライター", "C-M108-01", "普通ごみ", "燃料又はガスが残っているライター", "使い切るかガスを抜くまでは排出しない", "処理後は普通ごみ", "DIRECT_ITEM", "01", "4頁 普通ごみ欄『ライター』の条件", "残ガス条件を保持。余分な方法詳細は教材へ出さない。")

    # M109 海田町。
    add("M109", "I001", "ペットボトル", "C-M109-07", "ペットボトル", "PETマークがあり汚れを落とせるもの", "中を洗いキャップとラベルを外す", "汚れたものは可燃ごみ", "DIRECT_ITEM", "01", "1頁 資源物『ペットボトル』欄", "画像は通常PET。", scoring=True, exception_locator="1頁 可燃ごみ欄")
    add("M109", "I001", "汚れたペットボトル", "C-M109-01", "可燃ごみ", "汚れが落ちず資源化条件を満たさないもの", "中身を除き可燃ごみへ出す", "洗浄可能品はペットボトル", "OFFICIAL_RULE_DERIVED", "01", "1頁 可燃ごみ欄（プラスチック類）", "汚れ枝を保持。", exception_locator="1頁 ペットボトル欄")
    add("M109", "I004", "アルミ缶", "C-M109-04", "缶・金属類", "中身を空にした飲料・食品用アルミ缶", "中を洗う", "スプレー缶は使い切り穴を開けない", "DIRECT_ITEM", "01", "1頁 資源物『缶・金属類』欄", "画像は通常缶。", scoring=True)
    add("M109", "I004", "スプレー缶", "C-M109-04", "缶・金属類", "中身を使い切ったスプレー缶", "中身を使い切り穴を開けずに出す", "飲料缶は中を洗って同区分", "OFFICIAL_RULE_DERIVED", "01", "1頁 資源物『缶・金属類』欄の条件", "類似缶条件を保持。")
    add("M109", "I006", "ガラスびん", "C-M109-05", "ビン類", "割れていない飲食用ガラスびん", "ふたを外し中を洗う", "割れたびんは埋立ごみ", "DIRECT_ITEM", "01", "1頁 資源物『ビン類』欄", "画像は通常びん。", scoring=True, exception_locator="1頁 埋立ごみ欄")
    add("M109", "I006", "割れたガラスびん", "C-M109-02", "埋立ごみ", "破損したガラスびん", "危険がないよう安全に扱う", "割れていない飲食用びんはビン類", "OFFICIAL_RULE_DERIVED", "01", "1頁 埋立ごみ欄（ガラス）", "破損枝を保持。", exception_locator="1頁 ビン類欄")
    add("M109", "I007", "白色トレイ", "C-M109-08", "その他", "白色で汚れを落とした食品トレイ", "洗って出す", "白色以外又は汚れたものは可燃ごみ", "DIRECT_ITEM", "01", "1頁 資源物『その他』白色トレイ欄", "公式子分類名『その他』を正本に保持。", scoring=True, exception_locator="1頁 可燃ごみ欄")
    add("M109", "I007", "白色以外又は汚れたトレイ", "C-M109-01", "可燃ごみ", "白色トレイ区分の対象外となるもの", "可燃ごみへ出す", "白色で洗浄済みは資源物のその他", "OFFICIAL_RULE_DERIVED", "01", "1頁 可燃ごみ欄（プラスチック類）", "対象外枝を保持。", exception_locator="1頁 その他欄")
    add("M109", "I013", "新聞", "C-M109-06", "紙・布類", "汚れのない新聞・折込広告", "種類別にまとめる", "汚れた紙は可燃ごみ", "DIRECT_ITEM", "01", "1頁 資源物『紙・布類』欄", "画像は通常新聞。", scoring=True, exception_locator="1頁 可燃ごみ欄")
    add("M109", "I013", "汚れた新聞", "C-M109-01", "可燃ごみ", "資源化できない汚れのある新聞", "可燃ごみへ出す", "資源化できる新聞は紙・布類", "OFFICIAL_RULE_DERIVED", "01", "1頁 可燃ごみ欄（紙くず）", "汚れ枝を保持。", exception_locator="1頁 紙・布類欄")
    add("M109", "I014", "ダンボール", "C-M109-06", "紙・布類", "汚れのない家庭のダンボール", "折りたたみ種類別にまとめる", "汚れたものは可燃ごみ", "DIRECT_ITEM", "01", "1頁 資源物『紙・布類』欄", "画像は通常段ボール。", scoring=True, exception_locator="1頁 可燃ごみ欄")
    add("M109", "I014", "汚れたダンボール", "C-M109-01", "可燃ごみ", "資源化できない汚れのあるダンボール", "可燃ごみへ出す", "資源化できるものは紙・布類", "OFFICIAL_RULE_DERIVED", "01", "1頁 可燃ごみ欄（紙くず）", "汚れ枝を保持。", exception_locator="1頁 紙・布類欄")
    add("M109", "I017", "紙パック", "C-M109-06", "紙・布類", "内側が白く汚れを落とした紙パック", "洗い開いて乾かす", "アルミ加工・汚れたものは可燃ごみ", "DIRECT_ITEM", "01", "1頁 資源物『紙・布類』紙パック欄", "画像は通常紙パック。", scoring=True, exception_locator="1頁 可燃ごみ欄")
    add("M109", "I017", "アルミ加工・汚れた紙パック", "C-M109-01", "可燃ごみ", "資源化条件を満たさない紙パック", "中身を除き可燃ごみへ出す", "資源化できるものは紙・布類", "OFFICIAL_RULE_DERIVED", "01", "1頁 可燃ごみ欄", "加工差を保持。", exception_locator="1頁 紙・布類欄")
    add("M109", "I029", "モバイルバッテリー", "C-M109-09", "有害ごみ", "家庭用モバイルバッテリー", "電極をテープで絶縁する", "膨張・破損品は町へ確認", "DIRECT_ITEM", "03", "モバイルバッテリー・小型充電式電池欄", "通常有害ごみが公式に明記されるためOFFICIAL_CATEGORY。", scoring=True)
    add("M109", "I031", "電球（蛍光管を除く）", "C-M109-02", "埋立ごみ", "蛍光管を除く家庭用電球", "割れないよう安全に出す", "蛍光管は有害ごみ", "DIRECT_ITEM", "01", "2頁 50音一覧『電球（蛍光管を除く）』", "公式50音一覧の直接記載。", scoring=True, exception_locator="1頁 有害ごみ欄（蛍光管）")
    add("M109", "I033", "ライター（使い切る）", "C-M109-03", "資源物", "中身を使い切った使い捨てライター", "中身を使い切って出す", "中身が残る状態では出さない", "DIRECT_ITEM", "01", "2頁 50音一覧『ライター（使い切る）』", "画像は使い切った通常枝。", scoring=True)
    add("M109", "I033", "中身が残るライター", "C-M109-03", "資源物", "燃料又はガスが残っている使い捨てライター", "使い切るまでは排出しない", "使い切ったものを資源物へ出す", "DIRECT_ITEM", "01", "2頁 50音一覧『ライター（使い切る）』", "残ガス条件を保持。")
    return rows


BOX_CONFIG = {
    "M107": {
        "online": [("C-M107-07", "資源ごみ（ペットボトル）", "FIXED_10_SCORING"), ("C-M107-09", "回収・確認", "SIMPLIFIED_ACTION"), ("C-M107-06", "資源ごみ（古紙・布類）", "FIXED_10_SCORING"), ("C-M107-05", "資源ごみ（びん・缶）", "FIXED_10_SCORING"), ("C-M107-08", "有害・危険ごみ", "FIXED_10_SCORING")],
        "in_person": [("C-M107-01", "燃えるごみ"), ("C-M107-02", "燃えないごみ"), ("C-M107-03", "燃える粗大ごみ"), ("C-M107-04", "燃えない粗大ごみ"), ("C-M107-05", "資源ごみ（びん・缶）"), ("C-M107-06", "資源ごみ（古紙・布類）"), ("C-M107-07", "資源ごみ（ペットボトル）"), ("C-M107-08", "有害・危険ごみ")],
    },
    "M108": {
        "online": [("C-M108-09", "ペットボトル", "FIXED_10_SCORING"), ("C-M108-11", "白色トレイ", "FIXED_10_SCORING"), ("C-M108-03", "新聞・雑誌・雑がみ", "FIXED_10_SCORING"), ("C-M108-06", "ビン・缶", "FIXED_10_SCORING"), ("C-M108-07", "埋立ごみ", "FIXED_10_SCORING"), ("C-M108-08", "有害ごみ", "FIXED_10_SCORING"), ("C-M108-04", "ダンボール", "FIXED_10_SCORING"), ("C-M108-01", "普通ごみ", "FIXED_10_SCORING"), ("C-M108-10", "紙パック", "FIXED_10_SCORING")],
        "in_person": [("C-M108-01", "普通ごみ"), ("C-M108-02", "有価物"), ("C-M108-07", "埋立ごみ"), ("C-M108-08", "有害ごみ"), ("C-M108-09", "ペットボトル"), ("C-M108-10", "紙パック"), ("C-M108-11", "白色トレイ"), ("C-M108-12", "大型ごみ")],
    },
    "M109": {
        "online": [("C-M109-07", "ペットボトル", "FIXED_10_SCORING"), ("C-M109-08", "白色トレイ", "FIXED_10_SCORING"), ("C-M109-06", "紙・布類", "FIXED_10_SCORING"), ("C-M109-04", "缶・金属類", "FIXED_10_SCORING"), ("C-M109-05", "ビン類", "FIXED_10_SCORING"), ("C-M109-09", "有害ごみ", "FIXED_10_SCORING"), ("C-M109-02", "埋立ごみ", "FIXED_10_SCORING"), ("C-M109-03", "資源物", "FIXED_10_SCORING")],
        "in_person": [("C-M109-01", "可燃ごみ"), ("C-M109-02", "埋立ごみ"), ("C-M109-03", "資源物"), ("C-M109-09", "有害ごみ"), ("C-M109-10", "大型ごみ")],
    },
}


def build_boxes() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for mid, config in BOX_CONFIG.items():
        for order, (category_id, label, kind) in enumerate(config["online"], 1):
            rows.append({"municipality_id": mid, "teaching_box_id": f"TB-{mid}-ON-{order:02d}", "class_mode": "ONLINE_CLASS", "box_kind": kind, "category_id": category_id, "display_name": label, "display_order": str(order), "note": "自治体正式区分ではない教材用簡略行動箱" if kind == "SIMPLIFIED_ACTION" else "固定画像10品目の採点用"})
        for order, (category_id, label) in enumerate(config["in_person"], 1):
            rows.append({"municipality_id": mid, "teaching_box_id": f"TB-{mid}-IP-{order:02d}", "class_mode": "IN_PERSON_CLASS", "box_kind": "MAJOR_CATEGORY", "category_id": category_id, "display_name": label, "display_order": str(order), "note": "対面授業で使う主要分別箱"})
    return rows


def build_projection(reviews: list[dict[str, str]], boxes: list[dict[str, str]]) -> list[dict[str, str]]:
    scoring = [row for row in reviews if row["scoring_branch"] == "TRUE"]
    box_by_category = {(row["municipality_id"], row["category_id"]): row for row in boxes if row["class_mode"] == "ONLINE_CLASS"}
    rows = []
    for row in scoring:
        box = box_by_category[(row["municipality_id"], row["category_id"])]
        kind = "SIMPLIFIED_ACTION" if box["box_kind"] == "SIMPLIFIED_ACTION" else "OFFICIAL_CATEGORY"
        rows.append({"municipality_id": row["municipality_id"], "internal_item_id": row["internal_item_id"], "teaching_box_id": box["teaching_box_id"], "projection_kind": kind, "category_id": row["category_id"], "review_status": "COMPLETE", "note": "非通常収集categoryを通常分別箱へ誤投影しない" if kind == "SIMPLIFIED_ACTION" else "通常収集categoryを固定10品目採点箱へ投影"})
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
    scope_rows = [{"municipality_id": mid, "municipality_name": name, "lesson_mode": "ONLINE_CLASS", "scoring_status": "LESSON_READY_10", "required_item_count": "10", "required_branch_count": "18", "review_source": f"data/research/lesson_readiness/{mid.lower()}_item_review.csv", "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv", "note": "画像10品目の全条件枝COMPLETE。M107のI007のみ非通常収集categoryをSIMPLIFIED_ACTIONへ投影。40品目APP_READYではない" if mid == "M107" else "画像10品目の全条件枝COMPLETE。通常収集categoryへ安全に投影。40品目APP_READYではない"} for mid, name in TARGETS.items()]
    boxes = build_boxes()
    projections = build_projection(reviews, boxes)
    replace_targets(SCOPE, SCOPE_FIELDS, scope_rows)
    replace_targets(BOXES, BOX_FIELDS, boxes)
    replace_targets(PROJECTION, PROJECTION_FIELDS, projections)
    print("M107-M109 LESSON_READY_10 inputs written: reviews=54 boxes=43 projections=30")


if __name__ == "__main__":
    main()
