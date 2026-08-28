#!/usr/bin/env python3
"""Build the fixed-10 regional lesson batch and implementation-priority layer.

The regional lesson layer is intentionally separate from the canonical 40-item
municipality taxonomy.  Running this script is idempotent: only the seven
municipalities owned by this batch are replaced.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKED_DATE = "2026-08-28"
REVIEWER = "OPENAI_CODEX_REGIONAL_LESSON_BATCH_20260828"
TARGETS = {"M076", "M100", "M120", "M123", "M127", "M136", "M139"}
FIXED_ITEMS = ["I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"]
ITEM_NAMES = {
    "I001": "ペットボトル", "I004": "アルミ缶", "I006": "ガラスびん", "I007": "白色食品トレー",
    "I013": "新聞", "I014": "段ボール", "I017": "紙パック", "I029": "モバイルバッテリー",
    "I031": "電球", "I033": "使い捨てライター",
}


def read_rows(path: str) -> tuple[list[str], list[dict[str, str]]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with (ROOT / path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def replace_target_rows(path: str, new_rows: list[dict[str, str]], municipality_field: str = "municipality_id") -> None:
    fields, rows = read_rows(path)
    kept = [row for row in rows if row.get(municipality_field) not in TARGETS]
    write_rows(path, fields, kept + new_rows)


SOURCES = [
    # M076 備前市
    ("M076", "S-M076-01", "令和8年度ごみ収集カレンダー", "自治体公式Webページ", "https://www.city.bizen.okayama.jp/soshiki/12/5401.html", "備前市", "令和8年度", "2026-04-01", "資源回収ステーション設置地区は9種23分別、未設置地区は旧分別であること", "ページ本文「資源回収ステーションが設置されている地区／されていない地区」"),
    ("M076", "S-M076-02", "令和8年度ごみ収集カレンダー（9種23分別）", "自治体公式PDF", "https://www.city.bizen.okayama.jp/uploaded/attachment/28806.pdf", "備前市", "令和8年度", "2026-04-01", "9種23分別地域の固定10品目の分別区分", "分別区分一覧・各品目欄"),
    ("M076", "S-M076-03", "令和8年度ごみ収集カレンダー（旧分別）", "自治体公式PDF", "https://www.city.bizen.okayama.jp/uploaded/attachment/28814.pdf", "備前市", "令和8年度", "2026-04-01", "旧分別地域の固定10品目の分別区分", "2頁「もえるごみ／金属類／びん／紙類／取扱注意ごみ／拠点回収」"),
    ("M076", "S-M076-04", "備前市ごみ分別ガイドブック", "自治体公式PDF", "https://www.city.bizen.okayama.jp/uploaded/attachment/18508.pdf", "備前市", "現行案内", "2026-04-01", "電球・使い捨てライター・紙パック等の品目別条件", "品目別分別一覧「電球」「ライター（使い捨て）」「紙パック」"),
    ("M076", "S-M076-05", "小型充電式電池等の回収", "自治体公式Webページ", "https://www.city.bizen.okayama.jp/soshiki/12/20071.html", "備前市", "現行", "2025-07-01", "モバイルバッテリーの絶縁と回収ボックス利用", "ページ本文「小型充電式電池」"),
    # M100 広島県府中市
    ("M100", "S-M100-01", "令和6年度ごみ収集カレンダー", "自治体公式Webページ", "https://www.city.fuchu.hiroshima.jp/kurashi/gomi_kankyo/gomi/nittei2/8752.html", "府中市", "令和6年度から現行案内", "2024-03-21", "府中地区と上下地区のカレンダー体系", "ページ本文・地区別カレンダー導線"),
    ("M100", "S-M100-02", "ごみ収集カレンダー記号一覧", "自治体公式PDF", "https://www.city.fuchu.hiroshima.jp/material/files/group/29/1306031415.pdf", "府中市", "現行案内", "2024-03-21", "上下地区の資・新・雑・ペ等の記号と分別対象", "1頁「上下」記号凡例"),
    ("M100", "S-M100-03", "家庭ごみ分別ガイド（50音順）", "自治体公式PDF", "https://www.city.fuchu.hiroshima.jp/material/files/group/16/FuchuBunbetsuGaido_50on.pdf", "府中市", "現行案内", "2024-03-21", "固定10品目の分別区分と出し方", "50音順「電球」「モバイルバッテリー」「ライター」「食品トレー」"),
    # M120 萩市（本土側のみ）
    ("M120", "S-M120-01", "家庭ごみの分別と出し方（50音順）", "自治体公式Webページ", "https://www.city.hagi.lg.jp/soshiki/32/h62019.html", "萩市", "令和8年度", "2026-04-01", "本土側固定10品目の分別区分", "50音順一覧「ペットボトル」「電球」「使い捨てライター」等"),
    ("M120", "S-M120-02", "令和8年度ごみ収集カレンダー", "自治体公式Webページ", "https://www.city.hagi.lg.jp/soshiki/32/h69429.html", "萩市", "令和8年度", "2026-03-02", "本土側の資源・燃やせない・有害ごみ体系", "本土側カレンダー導線。島しょ部は教材対象外"),
    ("M120", "S-M120-03", "リチウムイオン電池など小型充電式電池の出し方", "自治体公式Webページ", "https://www.city.hagi.lg.jp/soshiki/32/h67254.html", "萩市", "現行", "2025-09-19", "モバイルバッテリーを有害ごみ回収ボックスへ出す方法", "ページ本文「モバイルバッテリー」"),
    # M123 岩国市
    ("M123", "S-M123-01", "岩国市ごみ収集カレンダー（令和8年度）", "自治体公式Webページ", "https://www.city.iwakuni.lg.jp/soshiki/23/113972.html", "岩国市", "令和8年度", "2026-04-27", "8行政地区と現行カレンダーの対応", "ページ本文「地域を選択してください」"),
    ("M123", "S-M123-02", "食品トレーの出し方", "自治体公式Webページ", "https://www.city.iwakuni.lg.jp/soshiki/23/1585.html", "岩国市", "現行", "2024-03-13", "食品トレーの2地域群別の処理方法", "「出し方」表（岩国・由宇・周東・玖珂／錦・美川・美和・本郷）"),
    ("M123", "S-M123-03", "ペットボトルの出し方", "自治体公式Webページ", "https://www.city.iwakuni.lg.jp/soshiki/23/1572.html", "岩国市", "現行", "2020-11-13", "PETマーク対象容器の回収ボックス利用", "「出し方」4"),
    ("M123", "S-M123-04", "資源品の処理について", "自治体公式Webページ", "https://www.city.iwakuni.lg.jp/soshiki/23/46208.html", "岩国市", "現行", "2024-03-13", "新聞・段ボール・紙パック・アルミ缶・充電池内蔵小型家電", "「対象品」1〜7"),
    ("M123", "S-M123-05", "プラスチック類の出し方", "自治体公式Webページ", "https://www.city.iwakuni.lg.jp/soshiki/23/1569.html", "岩国市", "現行", "2024-03-13", "ライター・モバイルバッテリーとプラマーク条件", "「プラマークがあっても出せない主なもの」"),
    ("M123", "S-M123-06", "金属類及び破砕ごみの出し方", "自治体公式Webページ", "https://www.city.iwakuni.lg.jp/soshiki/23/47985.html", "岩国市", "現行", "2024-03-13", "白熱球・LEDの分別区分", "品目例「白熱球・LED（照明器具等）」"),
    # M127 美祢市
    ("M127", "S-M127-01", "ごみの分け方・出し方", "自治体公式Webページ", "https://www2.city.mine.lg.jp/useful/gomidashi/4770.html", "美祢市", "現行", "2026-04-27", "美祢・美東・秋芳の現行分別ガイドへの導線", "ページ本文「家庭ごみの分別ガイド」"),
    ("M127", "S-M127-02", "家庭ごみの分別ガイド（美祢地域版）", "自治体公式PDF", "https://www2.city.mine.lg.jp/material/files/group/11/R6_guidemine.pdf", "美祢市", "令和6年度版・現行案内中", "2026-04-27", "美祢地域fixed10の現行分別", "分別一覧「電球」「ライター」「紙パック」「モバイルバッテリー」"),
    ("M127", "S-M127-03", "家庭ごみの分別ガイド（美東地域版）", "自治体公式PDF", "https://www2.city.mine.lg.jp/material/files/group/11/R6_guidemitou.pdf", "美祢市", "令和6年度版・現行案内中", "2026-04-27", "美東地域fixed10の現行分別", "分別一覧「電球」「ライター」「紙パック」「モバイルバッテリー」"),
    ("M127", "S-M127-04", "家庭ごみの分別ガイド（秋芳地域版）", "自治体公式PDF", "https://www2.city.mine.lg.jp/material/files/group/11/R6_guidesyuuhou.pdf", "美祢市", "令和6年度版・現行案内中", "2026-04-27", "秋芳地域fixed10の現行分別", "分別一覧「電球」「ライター」「紙パック」「モバイルバッテリー」"),
    ("M127", "S-M127-05", "家庭ごみの分け方・出し方（美祢地域）", "自治体公式Webページ", "https://www2.city.mine.lg.jp/kurashi_tetsuzuki/gomi_recycling/kateigomi/13250.html", "美祢市", "現行", "2026-04-01", "美祢地域の対象範囲", "ページ全体"),
    ("M127", "S-M127-06", "家庭ごみの分け方・出し方（美東地域）", "自治体公式Webページ", "https://www2.city.mine.lg.jp/kurashi_tetsuzuki/gomi_recycling/kateigomi/13252.html", "美祢市", "現行", "2026-04-01", "美東地域の対象範囲", "ページ全体"),
    ("M127", "S-M127-07", "家庭ごみの分け方・出し方（秋芳地域）", "自治体公式Webページ", "https://www2.city.mine.lg.jp/kurashi_tetsuzuki/gomi_recycling/kateigomi/13253.html", "美祢市", "現行", "2026-04-01", "秋芳地域の対象範囲", "ページ全体"),
    # M136 吉野川市
    ("M136", "S-M136-01", "ごみの出し方などについて", "自治体公式Webページ", "https://www.city.yoshinogawa.lg.jp/docs/2019092600010/", "吉野川市", "現行", "2026-06-10", "市共通fixed10の分別・条件と地区差の範囲", "「ごみの分別について」各区分・古紙類・小型充電式電池"),
    ("M136", "S-M136-02", "ごみ分別ガイドブック", "自治体公式Webページ", "https://www.city.yoshinogawa.lg.jp/docs/2022090200021/", "吉野川市", "令和8年度", "2026-06-10", "現行ガイドブックへの導線", "ページ本文・令和8年版PDF"),
    ("M136", "S-M136-03", "令和8年度ごみ収集カレンダー", "自治体公式Webページ", "https://www.city.yoshinogawa.lg.jp/docs/2026030600018/", "吉野川市", "令和8年度", "2026-03-11", "鴨島A/B・川島・山川・美郷のカレンダー地区", "地区別カレンダー一覧"),
    # M139 丸亀市
    ("M139", "S-M139-01", "ごみ収集カレンダー", "自治体公式Webページ", "https://www.city.marugame.lg.jp/site/gomi-calendar/", "丸亀市", "令和8年度", "2026-03-11", "旧丸亀・綾歌飯山・島部等のカレンダー導線", "地区別カレンダー一覧"),
    ("M139", "S-M139-02", "家庭ごみ分別早見表", "自治体公式Webページ", "https://www.city.marugame.lg.jp/page/41602.html", "丸亀市", "現行", "2026-03-11", "fixed10の品目別分別", "品目検索「食品トレー」「電球」「使い捨てライター」等"),
    ("M139", "S-M139-03", "家庭ごみの分け方・出し方", "自治体公式Webページ", "https://www.city.marugame.lg.jp/site/life-stage/2403.html", "丸亀市", "現行", "2023-04-01", "資源ごみ・可燃ごみ・不燃ごみの主要区分", "分別区分一覧"),
    ("M139", "S-M139-04", "使用済小型家電の回収", "自治体公式Webページ", "https://www.city.marugame.lg.jp/page/2401.html", "丸亀市", "現行", "2026-03-11", "モバイルバッテリーの回収ボックス等", "ページ本文「モバイルバッテリー」"),
]


GROUPS = [
    ("LV-M076-01", "M076", "資源回収ステーション9種23分別地域", "TRUE", 1, "9種23分別地域"),
    ("LV-M076-02", "M076", "旧分別地域", "TRUE", 2, "資源回収ステーション未設置地域"),
    ("LV-M100-01", "M100", "府中地区", "TRUE", 1, "府中地区"),
    ("LV-M100-02", "M100", "上下地区", "TRUE", 2, "上下地区"),
    ("LV-M120-01", "M120", "萩市（本土側）", "FALSE", 1, "島しょ部は教材対象外"),
    ("LV-M123-01", "M123", "岩国・由宇・周東・玖珂", "TRUE", 1, "食品トレーは店頭回収BOX"),
    ("LV-M123-02", "M123", "錦・美川・美和・本郷", "TRUE", 2, "食品トレーは自治体収集経路も選択可"),
    ("LV-M127-01", "M127", "美祢", "TRUE", 1, "美祢地域"),
    ("LV-M127-02", "M127", "美東", "TRUE", 2, "美東地域"),
    ("LV-M127-03", "M127", "秋芳", "TRUE", 3, "秋芳地域"),
    ("LV-M136-01", "M136", "吉野川市", "FALSE", 1, "カレンダー地区差はfixed10正答を変えない"),
    ("LV-M139-01", "M139", "丸亀市", "FALSE", 1, "カレンダー地区差はfixed10正答を変えない"),
]


SCOPES = [
    ("DS-M076-01", "M076", "資源回収ステーション設置地域", "LV-M076-01", 1, "S-M076-01", "M076-FIXED10-23", "びん類 その他", "S-M076-04", "品目別分別一覧「電球」"),
    ("DS-M076-02", "M076", "資源回収ステーション未設置地域", "LV-M076-02", 2, "S-M076-01", "M076-FIXED10-OLD", "取扱注意ごみ", "S-M076-03", "2頁「取扱注意ごみ」"),
    ("DS-M100-01", "M100", "府中地区", "LV-M100-01", 1, "S-M100-01", "M100-FIXED10-FUCHU", "埋立ごみ", "S-M100-03", "50音順「電球」"),
    ("DS-M100-02", "M100", "上下地区", "LV-M100-02", 2, "S-M100-01", "M100-FIXED10-JOGE", "埋立ごみ", "S-M100-03", "50音順「電球」"),
    ("DS-M120-01", "M120", "本土側（教材対象）", "LV-M120-01", 1, "S-M120-02", "M120-FIXED10-MAINLAND", "燃やせない", "S-M120-01", "50音順「電球」"),
    ("DS-M123-01", "M123", "岩国", "LV-M123-01", 1, "S-M123-01", "M123-FIXED10-A", "金属類及び破砕ごみ", "S-M123-06", "品目例「白熱球・LED」"),
    ("DS-M123-02", "M123", "由宇", "LV-M123-01", 2, "S-M123-01", "M123-FIXED10-A", "金属類及び破砕ごみ", "S-M123-06", "品目例「白熱球・LED」"),
    ("DS-M123-03", "M123", "周東", "LV-M123-01", 3, "S-M123-01", "M123-FIXED10-A", "金属類及び破砕ごみ", "S-M123-06", "品目例「白熱球・LED」"),
    ("DS-M123-04", "M123", "玖珂", "LV-M123-01", 4, "S-M123-01", "M123-FIXED10-A", "金属類及び破砕ごみ", "S-M123-06", "品目例「白熱球・LED」"),
    ("DS-M123-05", "M123", "錦", "LV-M123-02", 5, "S-M123-01", "M123-FIXED10-B", "金属類及び破砕ごみ", "S-M123-06", "品目例「白熱球・LED」"),
    ("DS-M123-06", "M123", "美川", "LV-M123-02", 6, "S-M123-01", "M123-FIXED10-B", "金属類及び破砕ごみ", "S-M123-06", "品目例「白熱球・LED」"),
    ("DS-M123-07", "M123", "美和", "LV-M123-02", 7, "S-M123-01", "M123-FIXED10-B", "金属類及び破砕ごみ", "S-M123-06", "品目例「白熱球・LED」"),
    ("DS-M123-08", "M123", "本郷", "LV-M123-02", 8, "S-M123-01", "M123-FIXED10-B", "金属類及び破砕ごみ", "S-M123-06", "品目例「白熱球・LED」"),
    ("DS-M127-01", "M127", "美祢", "LV-M127-01", 1, "S-M127-05", "M127-FIXED10-MINE", "リサイクルステーション", "S-M127-02", "分別一覧「電球」"),
    ("DS-M127-02", "M127", "美東", "LV-M127-02", 2, "S-M127-06", "M127-FIXED10-MITOU", "有害ごみ", "S-M127-03", "分別一覧「電球」"),
    ("DS-M127-03", "M127", "秋芳", "LV-M127-03", 3, "S-M127-07", "M127-FIXED10-SHUUHOU", "有害ごみ", "S-M127-04", "分別一覧「電球」"),
    ("DS-M136-01", "M136", "鴨島A", "LV-M136-01", 1, "S-M136-03", "M136-FIXED10-COMMON", "埋立・危険なごみ", "S-M136-01", "埋立・危険なごみ一例「電球」"),
    ("DS-M136-02", "M136", "鴨島B", "LV-M136-01", 2, "S-M136-03", "M136-FIXED10-COMMON", "埋立・危険なごみ", "S-M136-01", "埋立・危険なごみ一例「電球」"),
    ("DS-M136-03", "M136", "川島", "LV-M136-01", 3, "S-M136-03", "M136-FIXED10-COMMON", "埋立・危険なごみ", "S-M136-01", "埋立・危険なごみ一例「電球」"),
    ("DS-M136-04", "M136", "山川", "LV-M136-01", 4, "S-M136-03", "M136-FIXED10-COMMON", "埋立・危険なごみ", "S-M136-01", "埋立・危険なごみ一例「電球」"),
    ("DS-M136-05", "M136", "美郷", "LV-M136-01", 5, "S-M136-03", "M136-FIXED10-COMMON", "埋立・危険なごみ", "S-M136-01", "埋立・危険なごみ一例「電球」"),
    ("DS-M139-01", "M139", "旧丸亀地区", "LV-M139-01", 1, "S-M139-01", "M139-FIXED10-COMMON", "不燃ごみ", "S-M139-02", "品目検索「電球」"),
    ("DS-M139-02", "M139", "綾歌町・飯山町", "LV-M139-01", 2, "S-M139-01", "M139-FIXED10-COMMON", "不燃ごみ", "S-M139-02", "品目検索「電球」"),
    ("DS-M139-03", "M139", "島部等", "LV-M139-01", 3, "S-M139-01", "M139-FIXED10-COMMON", "不燃ごみ", "S-M139-02", "品目検索「電球」"),
]


GROUP_SPECS = {
    "LV-M076-01": (["ペットボトル", "アルミ缶", "無色びん", "白色トレイ・発泡スチロール", "新聞", "ダンボール", "紙パック", "回収BOX等", "びん類 その他", "燃えるごみ"], ["ペットボトル", "アルミ缶", "無色びん", "白色トレイ・発泡スチロール", "新聞", "ダンボール", "紙パック", "回収BOX等", "びん類 その他", "燃えるごみ"]),
    "LV-M076-02": (["拠点回収（ペットボトル）", "金属類", "びん", "もえるごみ", "紙類", "回収BOX等", "取扱注意ごみ"], ["拠点回収（ペットボトル）", "金属類", "びん", "もえるごみ", "紙類", "紙類", "回収BOX等", "回収BOX等", "取扱注意ごみ", "もえるごみ"]),
    "LV-M100-01": (["ペットボトル", "資源ごみ", "容器包装プラスチックごみ", "埋立ごみ"], ["ペットボトル", "資源ごみ", "資源ごみ", "容器包装プラスチックごみ", "資源ごみ", "資源ごみ", "資源ごみ", "資源ごみ", "埋立ごみ", "埋立ごみ"]),
    "LV-M100-02": (["ペットボトル", "カン・ビン・乾電池・金属・小型家電", "新聞・古着・紙パック", "雑誌・ダンボール", "容器包装プラスチックごみ", "埋立ごみ"], ["ペットボトル", "カン・ビン・乾電池・金属・小型家電", "カン・ビン・乾電池・金属・小型家電", "容器包装プラスチックごみ", "新聞・古着・紙パック", "雑誌・ダンボール", "新聞・古着・紙パック", "カン・ビン・乾電池・金属・小型家電", "埋立ごみ", "埋立ごみ"]),
    "LV-M120-01": (["資源", "プラスチック製容器包装", "有害ごみ", "燃やせない"], ["資源", "資源", "資源", "プラスチック製容器包装", "資源", "資源", "資源", "有害ごみ", "燃やせない", "有害ごみ"]),
    "LV-M123-01": (["回収BOX等", "資源品", "びん類", "金属類及び破砕ごみ", "処理困難ごみ"], ["回収BOX等", "資源品", "びん類", "回収BOX等", "資源品", "資源品", "資源品", "回収BOX等", "金属類及び破砕ごみ", "処理困難ごみ"]),
    "LV-M123-02": (["回収BOX等", "資源品", "びん類", "プラスチック類", "金属類及び破砕ごみ", "処理困難ごみ"], ["回収BOX等", "資源品", "びん類", "プラスチック類", "資源品", "資源品", "資源品", "回収BOX等", "金属類及び破砕ごみ", "処理困難ごみ"]),
    "LV-M127-01": (["リサイクルステーション", "缶類", "びん類", "回収BOX等", "紙リサイクルステーション", "固形燃料化できるごみ", "硬質プラスチック類"], ["リサイクルステーション", "缶類", "びん類", "回収BOX等", "紙リサイクルステーション", "紙リサイクルステーション", "固形燃料化できるごみ", "回収BOX等", "リサイクルステーション", "硬質プラスチック類"]),
    "LV-M127-02": (["ペットボトル", "缶類", "びん類", "回収BOX等", "新聞・広告", "段ボール", "固形燃料化できるごみ", "有害ごみ"], ["ペットボトル", "缶類", "びん類", "回収BOX等", "新聞・広告", "段ボール", "固形燃料化できるごみ", "回収BOX等", "有害ごみ", "有害ごみ"]),
    "LV-M127-03": (["リサイクルステーション", "缶類", "びん類", "回収BOX等", "固形燃料化できるごみ", "有害ごみ"], ["リサイクルステーション", "缶類", "びん類", "回収BOX等", "リサイクルステーション", "リサイクルステーション", "固形燃料化できるごみ", "回収BOX等", "有害ごみ", "有害ごみ"]),
    "LV-M136-01": (["ペットボトル", "カン・金属", "無色透明びん", "もやせるごみ", "新聞紙", "ダンボール", "回収BOX等", "埋立・危険なごみ"], ["ペットボトル", "カン・金属", "無色透明びん", "もやせるごみ", "新聞紙", "ダンボール", "回収BOX等", "回収BOX等", "埋立・危険なごみ", "埋立・危険なごみ"]),
    "LV-M139-01": (["資源ごみ", "可燃ごみ", "回収BOX等", "不燃ごみ"], ["資源ごみ", "資源ごみ", "資源ごみ", "可燃ごみ", "資源ごみ", "資源ごみ", "資源ごみ", "回収BOX等", "不燃ごみ", "資源ごみ"]),
}


ITEM_DEFAULTS = {
    "I001": ("PETマークのある飲料用ペットボトル本体", "キャップとラベルを外し、中をすすぐ", "汚れが落ちないもの・対象外容器は公式案内を確認"),
    "I004": ("中身を使い切った飲料・食品用アルミ缶", "中をすすぐ", "スチール缶・大きな缶は別区分を確認"),
    "I006": ("無色透明の飲料・食品用ガラスびん", "ふたを外し、中をすすぐ", "割れたびん・耐熱ガラス・他色びんは別区分"),
    "I007": ("汚れを落とせる白色食品トレー", "中身を除き、すすいで乾かす", "汚れが落ちないもの・回収BOX対象外は別区分"),
    "I013": ("乾いた新聞と折込チラシ", "紙ひも等でまとめる", "濡れたもの・汚れたものは別区分"),
    "I014": ("乾いた段ボール", "折りたたみ、紙ひも等でまとめる", "汚れたもの・特殊加工品は別区分"),
    "I017": ("洗って開ける飲料用紙パック", "洗浄し、切り開いて乾かす", "アルミ付き・小型等は自治体条件を確認"),
    "I029": ("家庭用モバイルバッテリー", "端子を絶縁する", "破損・膨張品は通常BOXへ入れず公式窓口へ相談"),
    "I031": ("割れていない一般的な電球", "割れないよう保護する", "割れたもの・蛍光管・LEDは自治体条件を確認"),
    "I033": ("中身を使い切った使い捨てライター", "火気のない場所でガスを使い切る", "ガスを抜けない場合は自治体窓口へ相談"),
}


EVIDENCE = {
    "M076": {
        "I001": ("S-M076-02", "分別区分「ペットボトル」"), "I004": ("S-M076-02", "分別区分「アルミ缶」"),
        "I006": ("S-M076-02", "分別区分「無色びん」"), "I007": ("S-M076-02", "分別区分「白色トレイ・発泡スチロール」"),
        "I013": ("S-M076-02", "分別区分「新聞」"), "I014": ("S-M076-02", "分別区分「ダンボール」"),
        "I017": ("S-M076-04", "品目別分別一覧「紙パック」"), "I029": ("S-M076-05", "ページ本文「小型充電式電池」"),
        "I031": ("S-M076-04", "品目別分別一覧「電球」"), "I033": ("S-M076-04", "品目別分別一覧「ライター（使い捨て）」"),
    },
    "M100": {iid: ("S-M100-03", f"50音順品目別一覧「{ITEM_NAMES[iid]}」") for iid in FIXED_ITEMS},
    "M120": {iid: ("S-M120-01", f"50音順品目別一覧「{ITEM_NAMES[iid]}」") for iid in FIXED_ITEMS},
    "M123": {
        "I001": ("S-M123-03", "「出し方」4 回収協力店等の回収ボックス"), "I004": ("S-M123-04", "対象品6「アルミ缶」"),
        "I006": ("S-M123-01", "カレンダー「びん類」"), "I007": ("S-M123-02", "「出し方」地域別表"),
        "I013": ("S-M123-04", "対象品1「新聞紙類」"), "I014": ("S-M123-04", "対象品4「段ボール」"),
        "I017": ("S-M123-04", "対象品3「紙パック」"), "I029": ("S-M123-05", "モバイルバッテリー等の出し方"),
        "I031": ("S-M123-06", "品目例「白熱球・LED」"), "I033": ("S-M123-05", "品目例「ライター」"),
    },
    "M127": {iid: ("", f"分別一覧「{ITEM_NAMES[iid]}」") for iid in FIXED_ITEMS},
    "M136": {iid: ("S-M136-01", f"ごみの分別について「{ITEM_NAMES[iid]}」相当欄") for iid in FIXED_ITEMS},
    "M139": {iid: ("S-M139-02", f"品目別分別「{ITEM_NAMES[iid]}」相当欄") for iid in FIXED_ITEMS},
}


SOURCE_BY_ID = {source[1]: source for source in SOURCES}


def source_url(source_id: str) -> str:
    return SOURCE_BY_ID[source_id][4]


def build_source_rows() -> list[dict[str, str]]:
    return [{
        "municipality_id": mid, "source_id": sid, "資料名": title, "資料種別": source_type,
        "公式URL": url, "発行主体": issuer, "対象年度": year, "ページ更新日": updated,
        "取得確認日": CHECKED_DATE, "使用した情報": used, "優先度": "1", "現行性": "現行案内中",
        "備考": locator, "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN",
        "official_linking_url": "",
    } for mid, sid, title, source_type, url, issuer, year, updated, used, locator in SOURCES]


def build_group_rows() -> list[dict[str, str]]:
    return [{
        "lesson_variant_group_id": gid, "municipality_id": mid, "display_name": name,
        "learner_selection_required": required, "display_order": str(order),
        "readiness_status": "LESSON_READY_10", "note": note,
    } for gid, mid, name, required, order, note in GROUPS]


def build_scope_rows() -> list[dict[str, str]]:
    rows = []
    for sid, mid, name, gid, order, source_id, answer_set, family, i031_source, i031_locator in SCOPES:
        rows.append({
            "district_scope_id": sid, "municipality_id": mid, "district_name": name,
            "lesson_variant_group_id": gid, "display_order": str(order), "learner_visible": "FALSE",
            "official_source_id": source_id, "official_url": source_url(source_id),
            "official_locator": SOURCE_BY_ID[source_id][9], "fixed_10_answer_set_id": answer_set,
            "fixed_10_confirmation_status": "CONFIRMED", "i031_answer_family": family,
            "i031_evidence_source_id": i031_source, "i031_evidence_url": source_url(i031_source),
            "i031_evidence_locator": i031_locator,
            "note": "fixed10の正答が同じ地区は1 learner groupへ統合",
        })
    return rows


def build_box_and_scoring_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    boxes: list[dict[str, str]] = []
    scoring: list[dict[str, str]] = []
    group_meta = {gid: (mid, name) for gid, mid, name, *_ in GROUPS}
    for gid, (labels, answers) in GROUP_SPECS.items():
        mid, _ = group_meta[gid]
        if len(answers) != len(FIXED_ITEMS):
            raise AssertionError(f"{gid}: answer vector must cover fixed 10")
        label_to_box: dict[str, str] = {}
        for order, label in enumerate(labels, 1):
            box_id = f"TB-{gid[3:]}-{order:02d}"
            label_to_box[label] = box_id
            kind = "SIMPLIFIED_ACTION" if label == "回収BOX等" else "FIXED_10_SCORING"
            boxes.append({
                "lesson_variant_group_id": gid, "teaching_box_id": box_id,
                "class_mode": "ONLINE_CLASS", "box_kind": kind, "display_name": label,
                "display_order": str(order),
                "note": "自治体正式区分ではない教材用行動箱" if kind == "SIMPLIFIED_ACTION" else "fixed10採点用",
            })
            boxes.append({
                "lesson_variant_group_id": gid, "teaching_box_id": f"{box_id}-IP",
                "class_mode": "IN_PERSON_CLASS", "box_kind": "SIMPLIFIED_ACTION" if kind == "SIMPLIFIED_ACTION" else "MAJOR_CATEGORY",
                "display_name": label, "display_order": str(order),
                "note": "対面授業用の主要BOX。練習問題には使用しない",
            })
        for iid, answer in zip(FIXED_ITEMS, answers):
            condition, preparation, exception = ITEM_DEFAULTS[iid]
            source_id, locator = EVIDENCE[mid][iid]
            if mid == "M127":
                source_id = {"LV-M127-01": "S-M127-02", "LV-M127-02": "S-M127-03", "LV-M127-03": "S-M127-04"}[gid]
            if mid == "M076" and gid == "LV-M076-02" and iid in {"I001", "I004", "I006", "I007", "I013", "I014", "I031", "I033"}:
                source_id, locator = "S-M076-03", f"2頁 旧分別の{answer}欄"
            if mid == "M100" and gid == "LV-M100-02":
                source_id, locator = "S-M100-02", f"1頁 上下地区記号凡例「{answer}」"
            if mid == "M120" and iid == "I029":
                source_id, locator = "S-M120-03", "ページ本文「モバイルバッテリー」"
            if mid == "M139" and iid == "I029":
                source_id, locator = "S-M139-04", "ページ本文「モバイルバッテリー」"
            if mid == "M076" and gid == "LV-M076-01" and iid == "I031":
                condition = "割れていないLED以外の一般電球"
                exception = "LED電球は「電球」、割れたものは公式案内を確認"
            if mid == "M127" and gid == "LV-M127-01" and iid == "I031":
                condition = "割れていない一般電球"
                exception = "割れた電球は「その他のごみ」"
            if mid == "M123" and gid == "LV-M123-02" and iid == "I007":
                condition = "プラマークのある、汚れを落とせる白色食品トレー"
                exception = "店頭回収BOXも可。プラマークなしは金属類及び破砕ごみ、汚れたものは焼却ごみ"
            scoring.append({
                "lesson_variant_group_id": gid, "municipality_id": mid, "internal_item_id": iid,
                "teaching_box_id": label_to_box[answer], "condition": condition,
                "preparation": preparation, "exception_destination": exception,
                "evidence_source_id": source_id, "evidence_url": source_url(source_id),
                "evidence_locator": locator, "review_status": "COMPLETE", "checked_date": CHECKED_DATE,
                "reviewer": REVIEWER, "note": "教材画像の通常状態を採点。正答を変える条件だけ保持",
            })
    return boxes, scoring


PRIORITY_A = {f"M{i:03d}" for i in range(1, 29)} | {f"M{i:03d}" for i in range(136, 144)}
PRIORITY_B = {
    "M029", "M030", "M032", "M042", "M048", "M050", "M052", "M055", "M067", "M068",
    "M070", "M071", "M072", "M078", "M096", "M101", "M117", "M120", "M121", "M123",
    "M128", "M131", "M133", "M135",
}


def write_priority_layer() -> None:
    _, municipalities = read_rows("data/master/01_municipalities_master.csv")
    _, standard_scope = read_rows("data/app/lesson_mode_app_ready_scope.csv")
    _, variant_groups = read_rows("data/app/lesson_variant_groups.csv")
    readiness = {row["municipality_id"]: row["scoring_status"] for row in standard_scope}
    for row in variant_groups:
        readiness[row["municipality_id"]] = row["readiness_status"]
    rows = []
    for municipality in municipalities:
        mid = municipality["municipality_id"]
        if mid in PRIORITY_A:
            basis = "USER_SPECIFIED_MASTER_36"
        elif mid in PRIORITY_B:
            basis = "USER_CONFIRMED_CHUGOKU_CANDIDATE"
        else:
            basis = "NOT_IN_CURRENT_PRIORITY_SET"
        current_readiness = readiness.get(mid, "NOT_LESSON_READY")
        rows.append({
            "municipality_id": mid, "prefecture": municipality["都道府県"], "municipality_name": municipality["市町村"],
            "implementation_status": "IMPLEMENTED" if current_readiness in {"APP_READY", "LESSON_READY_10"} else "NOT_IMPLEMENTED",
            "priority_status": "PRIORITY" if mid in PRIORITY_A | PRIORITY_B else "STANDARD",
            "priority_basis": basis, "company_link_status": "PENDING_COMPANY_LINK",
            "readiness_status_snapshot": current_readiness, "checked_date": CHECKED_DATE,
            "note": "企業紐付け一次ソースはreadinessに使用しない。repository内で未登録のため推測しない",
        })
    fields = [
        "municipality_id", "prefecture", "municipality_name", "implementation_status", "priority_status",
        "priority_basis", "company_link_status", "readiness_status_snapshot", "checked_date", "note",
    ]
    write_rows("data/master/07_implementation_priority.csv", fields, rows)


def ensure_style_source_columns() -> None:
    """Expose optional official-category inputs without storing fallback colors."""
    for path, variant in (
        ("data/app/lesson_teaching_boxes.csv", False),
        ("data/app/lesson_variant_teaching_boxes.csv", True),
    ):
        fields, rows = read_rows(path)
        for field in ("style_source_category_ids", "style_district_scope"):
            if field not in fields:
                fields.append(field)
        for row in rows:
            if variant or row.get("box_kind") == "SIMPLIFIED_ACTION":
                row.setdefault("style_source_category_ids", "")
                row.setdefault("style_district_scope", "")
                if row.get("box_kind") == "SIMPLIFIED_ACTION":
                    row["style_source_category_ids"] = ""
                    row["style_district_scope"] = ""
            else:
                row["style_source_category_ids"] = row.get("category_id", "")
                row["style_district_scope"] = "MUNICIPALITY_WIDE"
        write_rows(path, fields, rows)


def main() -> None:
    replace_target_rows("data/research/lesson_readiness/lesson_variant_sources.csv", build_source_rows())
    replace_target_rows("data/app/lesson_variant_groups.csv", build_group_rows())
    replace_target_rows("data/app/district_scopes.csv", build_scope_rows())
    boxes, scoring = build_box_and_scoring_rows()
    target_group_ids = {gid for gid, *_ in GROUPS}
    fields, old_boxes = read_rows("data/app/lesson_variant_teaching_boxes.csv")
    write_rows("data/app/lesson_variant_teaching_boxes.csv", fields, [r for r in old_boxes if r["lesson_variant_group_id"] not in target_group_ids] + boxes)
    replace_target_rows("data/app/lesson_variant_item_scoring.csv", scoring)
    write_priority_layer()
    ensure_style_source_columns()
    print(f"built regional lesson batch targets={len(TARGETS)} groups={len(GROUPS)} scoring={len(scoring)}")


if __name__ == "__main__":
    main()
