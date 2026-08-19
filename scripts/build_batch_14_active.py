#!/usr/bin/env python3
"""Production entrypoint for Batch 14.

Tightens row-level evidence linkage before CI without changing the reviewed
resident-facing taxonomy:
- M138 preparation details point to the current FY2026 resource guide;
- M140 metal/hazard rows point to the detailed sorting page rather than the
  schedule-only supplement;
- M143 nonburnable row points to the household guide carrying the two-hole
  spray-can rule; unsupported method prose on the plan-only hazardous row is
  removed rather than inferred.
"""
from __future__ import annotations

import build_batch_14 as batch

NS = batch.NS

m138_detail = {
    "空かん(アルミ・スチール)", "布", "牛乳パック", "新聞紙", "段ボール", "雑誌",
    "駄ビン", "ペットボトル", "白色トレイ", "蛍光管",
}

for row in batch.categories:
    key = (row.get("municipality_id"), row.get("自治体正式名称"))
    if row.get("municipality_id") == "M138" and row.get("自治体正式名称") in m138_detail:
        row["source_index"] = "2"
    if key in {("M140", "金属ごみ"), ("M140", "有害ごみ")}:
        row["source_index"] = "1"
    if key == ("M143", "燃えないごみ"):
        row["source_index"] = "2"
    if key == ("M143", "有害物（乾電池・蛍光灯）"):
        row["出す前の処理"] = NS


def main() -> None:
    batch.main()


if __name__ == "__main__":
    main()
