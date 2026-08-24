#!/usr/bin/env python3
"""One-time patch: manual APP_READY/VERIFIED mappings supersede an entire pair's initial candidates."""

from pathlib import Path

path = Path(__file__).with_name("red_team_schema_v12.py")
text = path.read_text(encoding="utf-8")
old = "    initial_mapping_sync = stored_initial_keys == generated_mapping_keys - manual_mapping_keys\n"
new = '''    manual_mapping_pairs = {
        (row["municipality_id"], row["internal_item_id"])
        for row in canonical_mappings
        if row["mapping_status"] in MANUAL_MAPPING_STATUS
    }
    expected_stored_initial_keys = {
        key for key in generated_mapping_keys if key[:2] not in manual_mapping_pairs
    }
    initial_mapping_sync = stored_initial_keys == expected_stored_initial_keys
'''
if old not in text:
    if new in text:
        print("schema red team already patched")
        raise SystemExit(0)
    raise SystemExit("expected initial_mapping_sync line not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("patched red_team_schema_v12.py for pair-level manual supersession")
