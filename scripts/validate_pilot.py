#!/usr/bin/env python3
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "master"
RESEARCH = ROOT / "data" / "research"
PILOT = RESEARCH / "pilot"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


master = read_csv(MASTER / "01_municipalities_master.csv")
municipalities = read_csv(PILOT / "pilot_municipalities.csv")
categories = read_csv(PILOT / "pilot_categories.csv")
sources = read_csv(PILOT / "pilot_sources.csv")
qa = read_csv(RESEARCH / "06_qa_log.csv")

master_ids = {row["municipality_id"] for row in master}
master_by_id = {row["municipality_id"]: row for row in master}
pilot_ids = {row["municipality_id"] for row in municipalities}
source_keys = {(row["municipality_id"], row["source_id"]) for row in sources}
category_keys = {(row["municipality_id"], row["category_id"]) for row in categories}

require(len(master) == 143, f"MASTER count: {len(master)} != 143")
require(len(master_ids) == 143, "Duplicate municipality_id in MASTER")
require(len({(r['都道府県'], r['市町村']) for r in master}) == 143, "Duplicate municipality in MASTER")
require(pilot_ids == {"M001", "M013", "M030", "M094", "M102"}, f"Unexpected Pilot IDs: {pilot_ids}")
require(pilot_ids <= master_ids, "Pilot municipality missing from MASTER")
for row in municipalities:
    base = master_by_id[row["municipality_id"]]
    for field in ("都道府県", "市町村", "実装区分"):
        require(row[field] == base[field], f"Pilot {field} differs from MASTER: {row['municipality_id']}")
require(len(category_keys) == len(categories), "Duplicate category key")
require(len(source_keys) == len(sources), "Duplicate source key")

required_category = [
    "municipality_id", "category_id", "自治体正式名称", "表示順", "collection_channel",
    "代表品目", "出す前の処理", "袋・容器のルール", "粗大ごみ扱いか", "予約が必要か",
    "有料か", "自治体収集外か", "source_id", "出典URL", "出典ページ・該当箇所", "確認日"
]
allowed_bool = {"TRUE", "FALSE", "CONDITIONAL", "UNKNOWN"}
allowed_channels = {"CURBSIDE", "BOOKED_PICKUP", "DROP_OFF", "DIRECT_HAUL", "RETAILER_OR_MAKER", "NOT_COLLECTED"}

for row in categories:
    for field in required_category:
        require(row.get(field, "") != "", f"Missing {field}: {row}")
    require(row["municipality_id"] in pilot_ids, "Category municipality not in Pilot")
    require((row["municipality_id"], row["source_id"]) in source_keys, f"Missing source reference: {row}")
    require(row["collection_channel"] in allowed_channels, f"Bad channel: {row}")
    for field in ("粗大ごみ扱いか", "予約が必要か", "有料か", "自治体収集外か"):
        require(row[field] in allowed_bool, f"Bad enum {field}: {row}")
    parent = row.get("parent_category_id", "")
    if parent:
        require((row["municipality_id"], parent) in category_keys, f"Missing parent category: {row}")

for row in sources:
    require(row["municipality_id"] in pilot_ids, "Source municipality not in Pilot")
    require(row["公式URL"].startswith("https://"), f"Non-HTTPS source: {row}")

require({r["municipality_id"] for r in qa} == pilot_ids, "QA coverage mismatch")
require(all(r["確認ステータス"] == "QA_PASSED" for r in qa), "Pilot contains non-passed QA")

counts = {mid: sum(r["municipality_id"] == mid for r in categories) for mid in sorted(pilot_ids)}
print(f"PASS master={len(master)} pilot={len(municipalities)} categories={len(categories)} sources={len(sources)}")
print("category_counts", counts)
