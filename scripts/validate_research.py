#!/usr/bin/env python3
"""Validate canonical research CSVs or a PHASE 3 batch directory."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
BOOL = {"TRUE", "FALSE", "CONDITIONAL", "UNKNOWN"}
CHANNEL = {"CURBSIDE", "BOOKED_PICKUP", "DROP_OFF", "DIRECT_HAUL", "RETAILER_OR_MAKER", "NOT_COLLECTED"}
LEVEL = {"PRIMARY", "SUBCATEGORY", "ALTERNATIVE", "EXCLUDED"}
FORBIDDEN_DOMAINS = {"wikipedia.org", "ameblo.jp", "note.com"}


def read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def fail(errors: list[str], msg: str):
    errors.append(msg)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", help="batch directory under data/research/batches")
    args = parser.parse_args()
    errors: list[str] = []

    if args.batch:
        base = ROOT / "data" / "research" / "batches" / args.batch
        prefix = f"{args.batch}_"
        municipalities = read(base / f"{prefix}municipalities.csv")
        categories = read(base / f"{prefix}categories.csv")
        sources = read(base / f"{prefix}sources.csv")
        qa = read(base / f"{prefix}qa.csv")
    else:
        municipalities = read(ROOT / "data" / "research" / "04_municipalities_research.csv")
        categories = read(ROOT / "data" / "research" / "02_categories_master.csv")
        sources = read(ROOT / "data" / "research" / "03_sources_master.csv")
        qa = read(ROOT / "data" / "research" / "06_qa_log.csv")

    mids = [r["municipality_id"] for r in municipalities]
    if len(mids) != len(set(mids)):
        fail(errors, "duplicate municipality_id")
    source_keys = {(r["municipality_id"], r["source_id"]) for r in sources}
    if len(source_keys) != len(sources):
        fail(errors, "duplicate source key")
    category_keys = {(r["municipality_id"], r["category_id"]) for r in categories}
    if len(category_keys) != len(categories):
        fail(errors, "duplicate category key")

    master_mids = {r["municipality_id"] for r in read(ROOT / "data" / "01_municipalities_master.csv")}
    for mid in mids:
        if mid not in master_mids:
            fail(errors, f"unknown MASTER municipality_id: {mid}")

    counts = Counter()
    names_by_mid: dict[str, set[str]] = {}
    for row in categories:
        mid = row["municipality_id"]
        counts[mid] += 1
        names_by_mid.setdefault(mid, set())
        if row["自治体正式名称"] in names_by_mid[mid]:
            fail(errors, f"duplicate official category name: {mid} {row['自治体正式名称']}")
        names_by_mid[mid].add(row["自治体正式名称"])
        if (mid, row["source_id"]) not in source_keys:
            fail(errors, f"missing source reference: {mid} {row['category_id']} {row['source_id']}")
        if row["collection_channel"] not in CHANNEL:
            fail(errors, f"bad collection_channel: {mid} {row['category_id']}")
        if row["classification_level"] not in LEVEL:
            fail(errors, f"bad classification_level: {mid} {row['category_id']}")
        for field in ["粗大ごみ扱いか", "予約が必要か", "有料か", "自治体収集外か"]:
            if row[field] not in BOOL:
                fail(errors, f"bad boolean enum: {mid} {row['category_id']} {field}={row[field]}")
        if not row["出典URL"].startswith("https://"):
            fail(errors, f"non-https category source: {mid} {row['category_id']}")

    for row in sources:
        host = urlparse(row["公式URL"]).hostname or ""
        if not row["公式URL"].startswith("https://"):
            fail(errors, f"non-https source: {row['source_id']}")
        if any(host == d or host.endswith("." + d) for d in FORBIDDEN_DOMAINS):
            fail(errors, f"non-official source domain: {row['source_id']} {host}")
        if row["現行性"] not in {"現行", "現行案内中", "施行予定"}:
            fail(errors, f"bad currency value: {row['source_id']} {row['現行性']}")

    qa_map = {r["municipality_id"]: r for r in qa}
    for mid in mids:
        if counts[mid] < 6:
            fail(errors, f"too few categories: {mid}={counts[mid]}")
        if mid not in qa_map:
            fail(errors, f"missing QA row: {mid}")
        elif qa_map[mid]["確認ステータス"] != "QA_PASSED":
            fail(errors, f"QA not passed: {mid}")
    if set(qa_map) != set(mids):
        fail(errors, "municipality and QA id sets differ")

    future_rows = [r for r in categories if r["注意事項"].startswith("2026年10月1日施行予定")]
    if "M005" in mids and len(future_rows) != 1:
        fail(errors, "Ishinomaki future plastic transition must be exactly one annotated row")

    if errors:
        print("VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALIDATION_PASSED")
    print(f"municipalities={len(mids)} categories={len(categories)} sources={len(sources)} qa={len(qa)}")
    print("category_counts=" + ",".join(f"{mid}:{counts[mid]}" for mid in sorted(counts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
