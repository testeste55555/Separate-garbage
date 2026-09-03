#!/usr/bin/env python3
"""Validate the pilot item-image registry against the common-item master."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MASTER_PATH = ROOT / "data/master/04_common_items_master.csv"
ASSET_TABLE_PATH = ROOT / "data/app/item_image_assets.csv"
ASSET_DIR = ROOT / "app/assets/items"

COLUMNS = [
    "pilot_order",
    "internal_item_id",
    "canonical_name",
    "display_name",
    "image_file",
    "asset_status",
]

PILOT_ITEMS = [
    (1, "I001", "I001_pet_bottle.png"),
    (2, "I007", "I007_white_food_tray.png"),
    (3, "I013", "I013_newspaper.png"),
    (4, "I004", "I004_aluminum_can.png"),
    (5, "I006", "I006_glass_bottle.png"),
    (6, "I031", "I031_light_bulb.png"),
    (7, "I029", "I029_mobile_battery.png"),
    (8, "I014", "I014_cardboard.png"),
    (9, "I033", "I033_disposable_lighter.png"),
    (10, "I017", "I017_milk_carton.png"),
    (11, "I002", "I002_pet_cap.webp"),
    (12, "I003", "I003_pet_label.webp"),
    (13, "I027", "I027_dry_battery.webp"),
    (14, "I018", "I018_food_waste.webp"),
    (15, "I010", "I010_snack_bag.webp"),
]

IMAGE_FILE_RE = re.compile(r"^(I\d{3})_[a-z0-9]+(?:_[a-z0-9]+)*\.(?:png|webp)$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
WEBP_RIFF = b"RIFF"
WEBP_TAG = b"WEBP"


def fail(message: str) -> None:
    raise ValueError(message)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        fail(f"missing CSV: {path.relative_to(ROOT)}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def require_unique(rows: list[dict[str, str]], column: str) -> None:
    values = [row[column].strip() for row in rows]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        fail(f"duplicate {column}: {duplicates}")


def validate() -> None:
    master_columns, master_rows = read_csv(MASTER_PATH)
    required_master_columns = {"internal_item_id", "一般管理用名称", "教材表示名"}
    if not required_master_columns.issubset(master_columns):
        fail("common-item master is missing required columns")

    columns, rows = read_csv(ASSET_TABLE_PATH)
    if columns != COLUMNS:
        fail(f"item image CSV columns must be exactly {COLUMNS}")
    if len(rows) != len(PILOT_ITEMS):
        fail(f"pilot registry must contain exactly {len(PILOT_ITEMS)} rows")

    require_unique(rows, "pilot_order")
    require_unique(rows, "internal_item_id")
    require_unique(rows, "image_file")

    master = {row["internal_item_id"].strip(): row for row in master_rows}
    expected = {
        item_id: {"pilot_order": str(order), "image_file": image_file}
        for order, item_id, image_file in PILOT_ITEMS
    }

    for row in rows:
        item_id = row["internal_item_id"].strip()
        canonical = master.get(item_id)
        if canonical is None:
            fail(f"unknown internal_item_id: {item_id}")
        if item_id not in expected:
            fail(f"unexpected pilot internal_item_id: {item_id}")
        if row["canonical_name"].strip() != canonical["一般管理用名称"].strip():
            fail(f"canonical_name mismatch for {item_id}")
        if row["display_name"].strip() != canonical["教材表示名"].strip():
            fail(f"display_name mismatch for {item_id}")
        if row["pilot_order"].strip() != expected[item_id]["pilot_order"]:
            fail(f"pilot_order mismatch for {item_id}")
        if row["asset_status"].strip() != "CONFIRMED":
            fail(f"pilot asset_status must be CONFIRMED for {item_id}")

        image_file = row["image_file"].strip()
        if image_file != expected[item_id]["image_file"]:
            fail(f"image_file mismatch for {item_id}")
        match = IMAGE_FILE_RE.fullmatch(image_file)
        if match is None:
            fail(f"invalid image_file format: {image_file}")
        if match.group(1) != item_id:
            fail(f"image_file ID prefix mismatch for {item_id}: {image_file}")
        if Path(image_file).name != image_file:
            fail(f"image_file must be a basename: {image_file}")

        image_path = ASSET_DIR / image_file
        if not image_path.is_file():
            fail(f"missing image asset: {image_path.relative_to(ROOT)}")
        data = image_path.read_bytes()[:12]
        if image_file.endswith(".png"):
            if not data.startswith(PNG_SIGNATURE):
                fail(f"image asset is not a PNG: {image_file}")
        elif image_file.endswith(".webp"):
            if len(data) < 12 or data[:4] != WEBP_RIFF or data[8:12] != WEBP_TAG:
                fail(f"image asset is not a WEBP: {image_file}")
        else:
            fail(f"unsupported image asset format: {image_file}")

    actual_order = [row["internal_item_id"].strip() for row in rows]
    expected_order = [item_id for _, item_id, _ in PILOT_ITEMS]
    if actual_order != expected_order:
        fail(f"pilot row order mismatch: {actual_order}")

    print("PASS item image asset validation")
    print(f"registered_items={len(rows)}")
    print(f"confirmed_assets={sum(row['asset_status'].strip() == 'CONFIRMED' for row in rows)}")


if __name__ == "__main__":
    try:
        validate()
    except ValueError as exc:
        print(f"FAIL item image asset validation: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
