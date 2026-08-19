#!/usr/bin/env python3
"""Production entrypoint for Batch 12.

Keeps the base evidence bundle while resolving two projection-only structures:
- M116: `容器や包装のプラスチック` is both an official heading and one exact
  resident stream, so category_group is used instead of inventing a suffix.
- M121: the booklet heading for paid special routes groups three independent
  REFERENCE_ONLY leaves. The heading itself is not promoted to a learner bucket.
"""
from __future__ import annotations

import build_batch_12 as batch

M116_GROUP = "容器や包装のプラスチック"
M121_SPECIAL_GROUP = "粗大ごみ・埋立ごみ・一時多量ごみ（有料収集）"

# M116: remove projection parent whose official name collides with one child.
batch.categories[:] = [
    row for row in batch.categories
    if not (
        row.get("municipality_id") == "M116"
        and row.get("自治体正式名称") == M116_GROUP
        and not row.get("parent_name")
    )
]
for row in batch.categories:
    if row.get("municipality_id") == "M116" and row.get("自治体正式名称") in {"ペットボトル", "白色トレー"}:
        row["parent_name"] = ""
        row["category_group"] = M116_GROUP
        row["classification_level"] = "PRIMARY"
        row["ui_role"] = "SORT_BUCKET"
    elif row.get("municipality_id") == "M116" and row.get("自治体正式名称") == "容器や包装のプラスチック（プラマーク）":
        row["自治体正式名称"] = M116_GROUP
        row["parent_name"] = ""
        row["category_group"] = M116_GROUP
        row["classification_level"] = "PRIMARY"
        row["ui_role"] = "SORT_BUCKET"

# M121: remove non-operational projection heading and keep three special-route
# official leaves as independent REFERENCE_ONLY categories in one group.
batch.categories[:] = [
    row for row in batch.categories
    if not (
        row.get("municipality_id") == "M121"
        and row.get("自治体正式名称") == M121_SPECIAL_GROUP
    )
]
for row in batch.categories:
    if row.get("municipality_id") == "M121" and row.get("自治体正式名称") in {"粗大ごみ", "埋立ごみ", "一時多量ごみ"}:
        row["parent_name"] = ""
        row["category_group"] = M121_SPECIAL_GROUP
        row["classification_level"] = "PRIMARY"
        row["ui_role"] = "REFERENCE_ONLY"


def main() -> None:
    batch.main()


if __name__ == "__main__":
    main()
