#!/usr/bin/env python3
from __future__ import annotations

import difflib
from pathlib import Path

from check_next_batch_gate import CANONICAL_FILES
from merge_research import main as merge_main
from sync_lesson_ready_reviews import synchronize as sync_lesson_ready

snapshots = {path: path.read_bytes() for path in CANONICAL_FILES}
try:
    merge_main()
    sync_lesson_ready()
    changed = [path for path in CANONICAL_FILES if path.read_bytes() != snapshots[path]]
    print(f"M068_MERGE_DIAGNOSTIC changed={len(changed)}")
    for path in changed:
        print(f"--- {path.as_posix()} ---")
        before = snapshots[path].decode("utf-8-sig").splitlines()
        after = path.read_text(encoding="utf-8-sig").splitlines()
        diff = list(difflib.unified_diff(before, after, fromfile="before", tofile="after", lineterm=""))
        for line in diff[:240]:
            print(line)
        if len(diff) > 240:
            print(f"... diff truncated: {len(diff)} lines")
finally:
    for path, data in snapshots.items():
        path.write_bytes(data)
