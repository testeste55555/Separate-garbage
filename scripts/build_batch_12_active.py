#!/usr/bin/env python3
"""Production entrypoint for Batch 12.

Keeps the base evidence bundle while resolving one official-heading collision in
M116: the heading `容器や包装のプラスチック` is also the exact name of one of
three separately bagged resident streams. We therefore use category_group for
that heading and keep the three official leaf names without inventing a suffix.
"""
from __future__ import annotations

import build_batch_12 as batch

GROUP = "容器や包装のプラスチック"

# Remove the projection-parent row whose name collides with an official child
# stream. The three actual resident streams remain current official leaves.
batch.categories[:] = [
    row for row in batch.categories
    if not (
        row.get("municipality_id") == "M116"
        and row.get("自治体正式名称") == GROUP
        and not row.get("parent_name")
    )
]

for row in batch.categories:
    if row.get("municipality_id") != "M116":
        continue
    if row.get("自治体正式名称") in {"ペットボトル", "白色トレー"}:
        row["parent_name"] = ""
        row["category_group"] = GROUP
        row["classification_level"] = "PRIMARY"
        row["ui_role"] = "SORT_BUCKET"
    elif row.get("自治体正式名称") == "容器や包装のプラスチック（プラマーク）":
        row["自治体正式名称"] = GROUP
        row["parent_name"] = ""
        row["category_group"] = GROUP
        row["classification_level"] = "PRIMARY"
        row["ui_role"] = "SORT_BUCKET"


def main() -> None:
    batch.main()


if __name__ == "__main__":
    main()
