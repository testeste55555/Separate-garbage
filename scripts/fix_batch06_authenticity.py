#!/usr/bin/env python3
"""Apply deterministic source-specific authenticity corrections after Batch 06 build.

This stays separate from the bulk builder so the rule-sensitive assertions remain
small and auditable. It is idempotent and re-runs migrate_batch_dir after edits.
"""
from schema_v12 import RESEARCH, read_csv, write_csv, migrate_batch_dir

B = RESEARCH / "batches" / "batch_06"

#川本町: current resident guide requires emptied aerosol cans to be pierced.
p = B / "batch_06_categories.csv"
fields, rows = read_csv(p)
for row in rows:
    if row.get("municipality_id") == "M058" and row.get("自治体正式名称") == "不燃ごみ":
        row["出す前の処理"] = "スプレー缶・カセットボンベは中身を使い切り、火気のない屋外で穴を開ける"
write_csv(p, fields, rows)

# 津和野町: machine translation links on the municipal site are not stored as a
# checked standalone multilingual garbage artifact. Keep optional-resource state honest.
p = B / "batch_06_municipalities.csv"
fields, rows = read_csv(p)
for row in rows:
    if row.get("municipality_id") == "M061":
        row["多言語資料URL"] = ""
        row["multilingual_check_status"] = "NOT_CHECKED"
        row["multilingual_check_evidence"] = ""
write_csv(p, fields, rows)

counts = migrate_batch_dir(B)
print(" ".join(f"{k}={v}" for k,v in counts.items()))
