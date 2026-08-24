#!/usr/bin/env python3
"""Validate lesson-mode UI safety and APP_READY-only correctness scoring."""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ROOT / "data/research/02_categories_master.csv"
ASSETS = ROOT / "data/app/item_image_assets.csv"
IMAGE_MAPPING = ROOT / "data/app/item_image_mapping_pilot_top8.csv"
REVIEWS = {
    "M094": ROOT / "data/research/app_readiness/m094_item_review.csv",
    "M104": ROOT / "data/research/app_readiness/m104_item_review.csv",
}
HTML = ROOT / "app/index.html"
JS = ROOT / "app/app.js"
CSS = ROOT / "app/styles.css"
EXPECTED_APP_READY_ITEMS = 40
EXPECTED_IMAGE_ITEMS = 10
IMAGE_RE = re.compile(r"I\d{3}_[A-Za-z0-9_]+\.png")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_sort_bucket(mid: str, category_id: str, by_key: dict[tuple[str, str], dict[str, str]]) -> str | None:
    current = category_id
    visited: set[str] = set()
    while current:
        if current in visited:
            return None
        visited.add(current)
        row = by_key.get((mid, current))
        if not row or row.get("rule_status") != "CURRENT":
            return None
        role = row.get("ui_role", "")
        if role == "SORT_BUCKET":
            return current
        if role in {"HIDDEN", "EXCLUDED_NOTICE"}:
            return None
        current = row.get("parent_category_id", "").strip()
    return None


def validate() -> list[str]:
    errors: list[str] = []
    categories = read_rows(CATEGORIES)
    assets = read_rows(ASSETS)
    mapping = read_rows(IMAGE_MAPPING)
    category_by_key = {(r["municipality_id"], r["category_id"]): r for r in categories}
    asset_by_item = {r["internal_item_id"]: r for r in assets if r.get("asset_status") == "CONFIRMED"}

    ready_pairs: set[tuple[str, str]] = set()
    for mid, path in REVIEWS.items():
        rows = read_rows(path)
        mids = {r.get("municipality_id", "") for r in rows}
        item_ids = {r.get("internal_item_id", "") for r in rows if r.get("internal_item_id")}
        incomplete = [r for r in rows if r.get("branch_review_status") != "COMPLETE"]
        if mids != {mid}:
            errors.append(f"{mid}: review file municipality mismatch: {sorted(mids)}")
        if len(item_ids) != EXPECTED_APP_READY_ITEMS:
            errors.append(f"{mid}: APP_READY review must cover 40 unique items, got {len(item_ids)}")
        if incomplete:
            errors.append(f"{mid}: review contains {len(incomplete)} non-COMPLETE branches")
        if mids == {mid} and len(item_ids) == EXPECTED_APP_READY_ITEMS and not incomplete:
            ready_pairs.update((mid, iid) for iid in item_ids)

    interactive: list[tuple[str, str]] = []
    for row in mapping:
        mid = row.get("municipality_id", "")
        iid = row.get("internal_item_id", "")
        if mid not in REVIEWS:
            continue
        if row.get("review_status") != "VERIFIED":
            errors.append(f"{mid}/{iid}: APP_READY municipality image row is not VERIFIED")
            continue
        if (mid, iid) not in ready_pairs:
            errors.append(f"{mid}/{iid}: image row lacks COMPLETE APP_READY pair")
            continue
        asset = asset_by_item.get(iid)
        image_file = asset.get("image_file", "") if asset else ""
        if not asset or not IMAGE_RE.fullmatch(image_file) or not image_file.startswith(f"{iid}_"):
            errors.append(f"{mid}/{iid}: missing or unsafe confirmed image asset")
            continue
        if not (ROOT / "app/assets/items" / image_file).is_file():
            errors.append(f"{mid}/{iid}: image file missing from app/assets/items")
            continue
        if not resolve_sort_bucket(mid, row.get("category_id", ""), category_by_key):
            errors.append(f"{mid}/{iid}: answer category cannot project to CURRENT SORT_BUCKET")
            continue
        interactive.append((mid, iid))

    counts = Counter(mid for mid, _ in interactive)
    for mid in REVIEWS:
        if counts[mid] != EXPECTED_IMAGE_ITEMS:
            errors.append(f"{mid}: expected 10 APP_READY image questions, got {counts[mid]}")
    if len(interactive) != EXPECTED_IMAGE_ITEMS * len(REVIEWS):
        errors.append(f"interactive APP_READY image pairs must be 20, got {len(interactive)}")

    html = HTML.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    required_html = {
        'id="lessonModeSelect"', 'id="municipalitySelect"', 'id="practicePanel"',
        'id="itemImage"', 'id="answerFeedback"', 'id="nextItemButton"', 'id="bucketGrid"',
    }
    for token in required_html:
        if token not in html:
            errors.append(f"HTML missing {token}")

    forbidden_html = {
        "itemDisplayName", "itemCondition", "answerDestination", "answerPreparation",
        "answerException", "practiceInstruction", "画像仕分け Pilot",
    }
    for token in forbidden_html:
        if token in html:
            errors.append(f"learner HTML exposes forbidden item/explanation element: {token}")

    required_js = {
        'const ONLINE_CLASS_MODE = "ONLINE_CLASS"',
        'const IN_PERSON_CLASS_MODE = "IN_PERSON_CLASS"',
        "APP_READY_REVIEW_FILES",
        "m094_item_review.csv",
        "m104_item_review.csv",
        "EXPECTED_APP_READY_ITEM_COUNT = 40",
        'row.branch_review_status?.trim() === "COMPLETE"',
        "appReadyMunicipalities.has(municipalityId)",
        "appReadyPairs.has(pairKey(municipalityId, itemId))",
        'row.review_status?.trim() !== "VERIFIED"',
        'answerFeedback.textContent = "○"',
        'answerFeedback.textContent = "×"',
    }
    for token in required_js:
        if token not in js:
            errors.append(f"JavaScript missing safety token: {token}")

    forbidden_js = {
        "navigator.onLine", "item.display_name", "item.condition", "item.preparation",
        "item.exception_destination", "answerDestination", "answerPreparation", "answerException",
    }
    for token in forbidden_js:
        if token in js:
            errors.append(f"learner JavaScript leaks explanation or confuses class/network mode: {token}")

    for token in [":focus-visible", 'data-answer-state="correct"', 'data-answer-state="incorrect"']:
        if token not in css:
            errors.append(f"CSS missing feedback/accessibility token: {token}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("APP_READY_LESSON_MODE_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("APP_READY_LESSON_MODE_VALIDATION_PASSED")
    print("app_ready_municipalities=2 app_ready_image_pairs=20 modes=ONLINE_CLASS,IN_PERSON_CLASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
