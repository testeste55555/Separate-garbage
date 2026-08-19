#!/usr/bin/env python3
"""Production entrypoint for Batch 10.

Active municipalities: M095, M096, M097, M101, M103, M104, M105.
M098 Onomichi, M099 Fukuyama, and M100 Fuchu are deferred because multiple
resident-facing CURRENT category variants coexist by region and the current
municipality-level schema cannot safely resolve the resident's regional scope.

The wrapper also:
- removes generic non-empty preparation filler;
- uses OFFICIAL_COUNT_MATCHED only where a current official source explicitly
  states the numeric total (M097: 10分別);
- keeps all other category-completeness reviews as MANUAL_INDEX_REVIEW.
"""
from __future__ import annotations

import build_batch_10 as batch

NS = batch.NS
EXTRA_DEFERRED = "M100"

# Remove Fuchu from the active Batch before any CSV construction.
batch.TARGETS.discard(EXTRA_DEFERRED)
batch.municipality_specs.pop(EXTRA_DEFERRED, None)
batch.source_specs.pop(EXTRA_DEFERRED, None)
batch.categories[:] = [r for r in batch.categories if r.get("municipality_id") != EXTRA_DEFERRED]

# Replace generic prose with concrete cited facts or the explicit not-stated sentinel.
PREP_PATCHES = {
    ("M095", "燃えるごみ"): "生ごみは水切りする",
    ("M095", "粗大ごみ"): "粗大ごみシールを貼る",
    ("M095", "プラスチック資源"): "汚れを落とす",
    ("M095", "資源物（びん類・缶類・ペットボトル）"): "中身を空にする",
    ("M095", "資源物（紙類）"): NS,
    ("M101", "燃やせるごみ"): NS,
    ("M101", "プラスチック資源"): NS,
    ("M101", "紙資源"): NS,
    ("M101", "資源物"): NS,
    ("M101", "布資源"): NS,
    ("M101", "燃やせないごみ"): NS,
    ("M101", "粗大ごみ"): NS,
    ("M101", "埋立ごみ"): NS,
    ("M101", "有害ごみ"): NS,
    ("M103", "もやすごみ"): "30cm未満にする",
    ("M103", "プラスチックごみ"): "汚れを落とす",
    ("M103", "衣類・毛布類"): NS,
    ("M104", "燃やせる粗大ごみ"): "指定袋は不要",
    ("M104", "ビン・缶"): "中身を除き紫色指定袋へ入れる",
    ("M104", "ペットボトル"): "キャップ・ラベルを外し、紫色指定袋へ入れる",
    ("M105", "資源ごみ(4) 布類"): "金具等を外す",
}

for row in batch.categories:
    key = (row["municipality_id"], row["自治体正式名称"])
    if key in PREP_PATCHES:
        row["出す前の処理"] = PREP_PATCHES[key]


# Preserve the base implementations before replacing them.
batch._original_build_municipalities = batch.build_municipalities
batch._original_build_review_evidence = batch.build_review_evidence
batch._original_ensure_deferred = batch.ensure_deferred


def ensure_deferred() -> None:
    batch._original_ensure_deferred()
    path = batch.MASTER / "05_deferred_municipalities.csv"
    fields, rows = batch.read_csv(path)
    if not any(r.get("municipality_id") == EXTRA_DEFERRED for r in rows):
        rows.append({
            "municipality_id": "M100", "都道府県": "広島県", "市町村": "府中市", "status": "DEFERRED",
            "reason": "府中地区は『資源ごみ及び電池』、上下地区は資源ごみの下で『缶・びん・電池・金属・小型家電』『新聞・古着・紙パック』『雑誌・段ボール』を別収集単位としており、住民向け表示単位・正式名称が地域で異なる。現行municipality単位Schema/UIでは地域variantを安全に解決できないため一旦対象外。",
            "deferred_date": batch.CHECKED, "decision_source": "SCHEMA_SCOPE_LIMITATION",
        })
        rows.sort(key=lambda r: r.get("municipality_id", ""))
        batch.write_csv(path, fields, rows)


def build_municipalities():
    rows = batch._original_build_municipalities()
    for row in rows:
        mid = row["municipality_id"]
        if mid == "M097":
            row["official_category_count"] = "10"
            row["reviewed_category_count"] = ""
            row["category_count_check_status"] = "OFFICIAL_COUNT_MATCHED"
            row["category_count_basis"] = "三原市公式家庭ごみ分別ガイドが『家庭ごみの分別方法は10分別』と明記し、現行10区分を全件照合。"
        else:
            row["official_category_count"] = ""
            row["reviewed_category_count"] = str(batch.leaf_count(mid))
            row["category_count_check_status"] = "MANUAL_INDEX_REVIEW"
            row["category_count_basis"] = "住民が排出時に選択する現行公式分別区分を公式索引・現年度資料で全件照合。"
    return rows


def build_review_evidence():
    rows = batch._original_build_review_evidence()
    for row in rows:
        mid = row["municipality_id"]
        source_id = row["source_id"]
        if mid == "M097" and source_id == "S-M097-01":
            row["evidence_role"] = "OFFICIAL_TOTAL"
            row["locator"] = "家庭ごみの分別方法は10分別と明記し、10区分の現行分別を確認"
        else:
            index = int(source_id.rsplit("-", 1)[1])
            row["evidence_role"] = "PRIMARY_INDEX" if index == 1 else "SUPPLEMENTAL_INDEX"
    return rows


batch.ensure_deferred = ensure_deferred
batch.build_municipalities = build_municipalities
batch.build_review_evidence = build_review_evidence


def main() -> None:
    batch.main()


if __name__ == "__main__":
    main()
