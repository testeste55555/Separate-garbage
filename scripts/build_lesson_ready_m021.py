#!/usr/bin/env python3
"""Build M021 津市 LESSON_READY_10 learner projections.

The audited review is authoritative. This builder only projects the fixed ten
lesson items to learner-facing teaching boxes and never creates an APP_READY
claim. Existing municipalities are preserved unchanged.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M021"
NAME = "津市"
REVIEW = ROOT / "data/research/lesson_readiness/m021_item_review.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"

FIXED_10 = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}

SCOPE_FIELDS = [
    "municipality_id", "municipality_name", "lesson_mode", "scoring_status",
    "required_item_count", "required_branch_count", "review_source", "image_mapping_source", "note",
]
BOX_FIELDS = [
    "municipality_id", "teaching_box_id", "class_mode", "box_kind", "category_id",
    "display_name", "display_order", "note", "style_source_category_ids", "style_district_scope",
]
PROJECTION_FIELDS = [
    "municipality_id", "internal_item_id", "teaching_box_id", "projection_kind",
    "category_id", "review_status", "note",
]

ONLINE_SPEC = [
    ("C-M021-01", "金属・燃やせないごみ（不燃）"),
    ("C-M021-02", "危険ごみ"),
    ("C-M021-03", "新聞"),
    ("C-M021-05", "ダンボール"),
    ("C-M021-06", "飲料用紙パック"),
    ("C-M021-08", "ペットボトル（ペット）"),
    ("C-M021-09", "びん"),
    ("C-M021-10", "容器包装プラスチック（容プラ）"),
]
IN_PERSON_SPEC = ONLINE_SPEC + [("C-M021-12", "燃やせるごみ（可燃）")]


def replace_mid(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
    *,
    sort_by_municipality: bool = False,
) -> None:
    current_fields, existing = read_csv(path)
    if current_fields != fields:
        raise ValueError(f"unexpected schema for {path}: {current_fields}")
    kept = [row for row in existing if row.get("municipality_id") != MID]
    output = kept + rows
    if sort_by_municipality:
        output.sort(key=lambda row: row.get("municipality_id", ""))
    write_csv(path, fields, output)


def build() -> None:
    _, review_rows = read_csv(REVIEW)
    if not review_rows:
        raise ValueError("M021 review is empty")
    if any(row.get("municipality_id") != MID for row in review_rows):
        raise ValueError("review contains another municipality")
    if any(row.get("branch_review_status") != "COMPLETE" for row in review_rows):
        raise ValueError("review contains an incomplete branch")

    by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in review_rows:
        by_item[row["internal_item_id"]].append(row)
    if set(by_item) != FIXED_10:
        raise ValueError(f"M021 review must contain fixed ten items: {sorted(by_item)}")

    scoring: dict[str, dict[str, str]] = {}
    for iid, rows in by_item.items():
        hits = [row for row in rows if row.get("scoring_branch") == "TRUE"]
        if len(hits) != 1:
            raise ValueError(f"{MID}/{iid} must have exactly one scoring branch")
        scoring[iid] = hits[0]

    scope_rows = [{
        "municipality_id": MID,
        "municipality_name": NAME,
        "lesson_mode": "ONLINE_CLASS",
        "scoring_status": "LESSON_READY_10",
        "required_item_count": "10",
        "required_branch_count": str(len(review_rows)),
        "review_source": "data/research/lesson_readiness/m021_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "画像10品目の通常画像枝と必要条件枝をCOMPLETE。補助5品目は別Gateで完成時のみ追加し、40品目APP_READYには昇格しない。",
    }]

    boxes: list[dict[str, str]] = []
    for order, (cid, label) in enumerate(ONLINE_SPEC, 1):
        boxes.append({
            "municipality_id": MID,
            "teaching_box_id": f"TB-{MID}-ON-{order:02d}",
            "class_mode": "ONLINE_CLASS",
            "box_kind": "FIXED_10_SCORING",
            "category_id": cid,
            "display_name": label,
            "display_order": str(order),
            "note": "固定10品目採点用。",
            "style_source_category_ids": cid,
            "style_district_scope": "MUNICIPALITY_WIDE",
        })
    for order, (cid, label) in enumerate(IN_PERSON_SPEC, 1):
        boxes.append({
            "municipality_id": MID,
            "teaching_box_id": f"TB-{MID}-IP-{order:02d}",
            "class_mode": "IN_PERSON_CLASS",
            "box_kind": "MAJOR_CATEGORY",
            "category_id": cid,
            "display_name": label,
            "display_order": str(order),
            "note": "対面授業用の主要分別箱。",
            "style_source_category_ids": cid,
            "style_district_scope": "MUNICIPALITY_WIDE",
        })

    online_box_by_category = {
        row["category_id"]: row for row in boxes if row["class_mode"] == "ONLINE_CLASS"
    }
    projection: list[dict[str, str]] = []
    for iid in sorted(scoring):
        row = scoring[iid]
        cid = row["category_id"]
        box = online_box_by_category.get(cid)
        if not box:
            raise ValueError(f"no M021 online teaching box for {iid}/{cid}")
        projection.append({
            "municipality_id": MID,
            "internal_item_id": iid,
            "teaching_box_id": box["teaching_box_id"],
            "projection_kind": "OFFICIAL_CATEGORY",
            "category_id": cid,
            "review_status": "COMPLETE",
            "note": "公式分別区分へ投影。詳細条件・例外は教師用reviewに保持。",
        })

    # Scope is the ordering source used by sync_lesson_ready_reviews.py for the
    # shared image mapping.  Existing APP_READY builders also keep it in
    # municipality-id order, so preserve that canonical order here instead of
    # appending M021 at the end and creating cross-builder idempotence drift.
    replace_mid(SCOPE, SCOPE_FIELDS, scope_rows, sort_by_municipality=True)
    replace_mid(BOXES, BOX_FIELDS, boxes)
    replace_mid(PROJECTION, PROJECTION_FIELDS, projection)
    print(f"M021_LESSON_READY_BUILT items={len(scoring)} branches={len(review_rows)} online_boxes={len(ONLINE_SPEC)} in_person_boxes={len(IN_PERSON_SPEC)}")


if __name__ == "__main__":
    build()
