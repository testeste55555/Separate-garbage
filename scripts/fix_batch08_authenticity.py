#!/usr/bin/env python3
"""Authenticity corrections applied after rebuilding Batch 08.

瀬戸内市の旧分別マニュアルにはスプレー缶の穴あけ記載が残る一方、
現行の市公式火災防止ページは、安全機構を使って中身を完全に出し切り
金物類へ出すよう案内している。現在ルールとして穴あけを強制しない。
"""
from __future__ import annotations

from pathlib import Path
from schema_v12 import RESEARCH, SOURCE_FIELDS, read_csv, write_csv, migrate_batch_dir

BATCH = RESEARCH / "batches" / "batch_08"
P = "batch_08_"
MID = "M077"
SOURCE_ID = "S-M077-04"
CURRENT_URL = "https://www.city.setouchi.lg.jp/soshiki/14/139499.html"


def main() -> None:
    source_path = BATCH / f"{P}sources.csv"
    category_path = BATCH / f"{P}categories.csv"

    _, sources = read_csv(source_path)
    sources = [r for r in sources if not (r.get("municipality_id") == MID and r.get("source_id") == SOURCE_ID)]
    sources.append({
        "municipality_id": MID,
        "source_id": SOURCE_ID,
        "資料名": "パッカー車（ごみ収集車）で火が出る事故がありました！！",
        "資料種別": "自治体公式Webページ",
        "公式URL": CURRENT_URL,
        "発行主体": "瀬戸内市",
        "対象年度": "現行",
        "ページ更新日": "2023-12-21",
        "取得確認日": "2026-08-19",
        "使用した情報": "スプレー缶・カセット式ガスボンベは安全機構を利用し中身を完全に出し切ってから金物類へ出す現行安全案内",
        "優先度": "1",
        "現行性": "現行案内中",
        "備考": "旧マニュアルの穴あけ記載より、現在の市公式火災防止ページの安全なガス抜き案内を優先。穴あけを必須条件として補作しない。",
        "official_verified": "",
        "official_basis": "",
        "official_linking_url": "",
    })
    sources.sort(key=lambda r: (r.get("municipality_id", ""), r.get("source_id", "")))
    write_csv(source_path, SOURCE_FIELDS, sources)

    fields, categories = read_csv(category_path)
    found = False
    for row in categories:
        if row.get("municipality_id") == MID and row.get("自治体正式名称") == "金物類" and row.get("rule_status") == "CURRENT":
            row["出す前の処理"] = "スプレー缶・カセット式ガスボンベは安全機構を利用し、火気のない風通しのよい屋外で中身を完全に出し切ってから出す"
            row["source_id"] = SOURCE_ID
            row["出典URL"] = CURRENT_URL
            row["出典ページ・該当箇所"] = "スプレー缶・カセット式ガスボンベ／中身を出し切ったもの→金物類"
            row["注意事項"] = "現行公式安全案内では穴あけを必須としていないため、穴あけ条件を現在ルールとして断定しない"
            found = True
    if not found:
        raise RuntimeError("M077 金物類 CURRENT row not found")
    write_csv(category_path, fields, categories)

    # Recompute official verification, mappings, coverage and QA after the source change.
    migrate_batch_dir(BATCH)
    print("Batch 08 authenticity fix applied: M077 current aerosol rule uses complete gas release, not mandatory piercing")


if __name__ == "__main__":
    main()
