#!/usr/bin/env python3
"""Mutation-style RED TEAM checks for APP_READY learner scoring boundaries."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "app/app.js"
HTML = ROOT / "app/index.html"
LESSON_SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"


def main() -> int:
    js = JS.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    lesson_scope = LESSON_SCOPE.read_text(encoding="utf-8-sig")
    failures: list[str] = []

    tests = {
        "class mode is not network mode": "navigator.onLine" not in js,
        "online mode exists": 'const ONLINE_CLASS_MODE = "ONLINE_CLASS"' in js,
        "in-person mode exists": 'const IN_PERSON_CLASS_MODE = "IN_PERSON_CLASS"' in js,
        "APP_READY municipality gate exists": "appReadyMunicipalities.has(municipalityId)" in js,
        "APP_READY pair gate exists": "appReadyPairs.has(pairKey(municipalityId, itemId))" in js,
        "M095 review is loaded": "m095_item_review.csv" in js,
        "M095 is in explicit lesson scope": "M095,呉市,ONLINE_CLASS,APP_READY" in lesson_scope,
        "next municipality is not enabled early": "M097,三原市,ONLINE_CLASS,APP_READY" not in lesson_scope,
        "40-item completeness gate exists": "EXPECTED_APP_READY_ITEM_COUNT = 40" in js,
        "branch COMPLETE gate exists": 'row.branch_review_status?.trim() === "COMPLETE"' in js,
        "image-specific VERIFIED mapping remains required": 'row.review_status?.trim() !== "VERIFIED"' in js,
        "wrong feedback is symbol only": 'answerFeedback.textContent = "×"' in js,
        "correct feedback is symbol only": 'answerFeedback.textContent = "○"' in js,
        "item display name absent": "itemDisplayName" not in html and "item.display_name" not in js,
        "condition text absent": "itemCondition" not in html and "item.condition" not in js,
        "preparation text absent": "answerPreparation" not in html and "item.preparation" not in js,
        "exception text absent": "answerException" not in html and "item.exception_destination" not in js,
    }

    for name, passed in tests.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
        if not passed:
            failures.append(name)

    if failures:
        print(f"APP_READY_LESSON_MODE_RED_TEAM_FAILED {len(failures)}/{len(tests)}")
        return 1
    print(f"APP_READY_LESSON_MODE_RED_TEAM_PASSED {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
