#!/usr/bin/env python3
"""Production entrypoint for Batch 13.

Applies pre-CI authenticity/Schema fixes to the research builder:
- M130 uses the Schema-valid CHECKED_PRESENT search-service status with dated URL evidence;
- generic or modelling-only preparation prose is removed rather than preserved as resident guidance;
- M132 records only the spray-can preparation explicitly supported by the cited page.
"""
from __future__ import annotations

import build_batch_13 as batch

NS = batch.NS

PREP_PATCHES = {
    ("M129", "燃やせるごみ"): NS,
    ("M132", "金属類"): "スプレー缶・カセットボンベは中身を使い切る",
    ("M135", "資源ごみ"): "資源ごみ指定袋へ",
    ("M135", "古紙等"): NS,
}

for row in batch.categories:
    key = (row.get("municipality_id"), row.get("自治体正式名称"))
    if key in PREP_PATCHES:
        row["出す前の処理"] = PREP_PATCHES[key]
    if key == ("M132", "金属類"):
        row["注意事項"] = "穴あけ有無は引用した現行公式ページに明示なし"

batch._original_build_municipalities = batch.build_municipalities


def build_municipalities():
    rows = batch._original_build_municipalities()
    for row in rows:
        if row.get("municipality_id") == "M130":
            url = row.get("品目検索URL", "")
            row["search_service_check_status"] = "CHECKED_PRESENT"
            row["search_service_check_evidence"] = f"URL:{url}; checked:{batch.CHECKED}"
    return rows


batch.build_municipalities = build_municipalities


def main() -> None:
    batch.main()


if __name__ == "__main__":
    main()
