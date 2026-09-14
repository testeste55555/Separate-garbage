#!/usr/bin/env python3
from pathlib import Path

path = Path('scripts/build_lesson_ready_m068.py')
text = path.read_text()
bad = 'row.get("municipality_id", ""), row.get("category_id", row.get("source_id", row.get("internal_item_id", row.get("review_evidence_id", ""))))),'
good = 'row.get("municipality_id", ""), row.get("category_id", row.get("source_id", row.get("internal_item_id", row.get("review_evidence_id", "")))),'
if bad in text:
    text = text.replace(bad, good)
elif good not in text:
    raise SystemExit('M068 builder syntax anchor not found')
path.write_text(text)
