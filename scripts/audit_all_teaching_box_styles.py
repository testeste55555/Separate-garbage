#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
VARIANT_BOXES = ROOT / "data/app/lesson_variant_teaching_boxes.csv"
VARIANT_GROUPS = ROOT / "data/app/lesson_variant_groups.csv"
STYLES = ROOT / "data/style_research/08_style_ui_projection.csv"

OFFICIAL = {"OFFICIAL_CONFIRMED", "OFFICIAL_DERIVED"}


def rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def usable(style):
    if not style or style.get("color_status", "").strip() not in OFFICIAL:
        return False
    vals = [style.get("display_color", ""), style.get("border_color", ""), style.get("text_color", "")]
    return all(v.startswith("#") and len(v) == 7 for v in vals)


def main():
    target_mids = {r["municipality_id"].strip() for r in rows(SCOPE)}
    group_to_mid = {r["lesson_variant_group_id"].strip(): r["municipality_id"].strip() for r in rows(VARIANT_GROUPS)}

    style_by_key = {}
    for r in rows(STYLES):
        mid = r.get("municipality_id", "").strip()
        cid = r.get("category_id", "").strip()
        scope = r.get("district_scope", "").strip() or "MUNICIPALITY_WIDE"
        if mid and cid:
            style_by_key[(mid, scope, cid)] = r

    all_boxes = []
    for r in rows(BOXES):
        r = dict(r)
        r["_mid"] = r.get("municipality_id", "").strip()
        all_boxes.append(r)
    for r in rows(VARIANT_BOXES):
        r = dict(r)
        gid = r.get("lesson_variant_group_id", "").strip()
        r["_mid"] = group_to_mid.get(gid, "")
        all_boxes.append(r)

    missing = defaultdict(list)
    resolved = defaultdict(int)
    simplified = defaultdict(int)

    for r in all_boxes:
        mid = r.get("_mid", "")
        if not mid or mid not in target_mids:
            continue
        if r.get("box_kind", "").strip() == "SIMPLIFIED_ACTION":
            simplified[mid] += 1
            continue
        source_text = r.get("style_source_category_ids", "").strip() or r.get("category_id", "").strip()
        source_ids = [x.strip() for x in source_text.split(";") if x.strip()]
        district_scope = r.get("style_district_scope", "").strip() or "MUNICIPALITY_WIDE"
        if not source_ids:
            missing[mid].append((r.get("teaching_box_id", ""), r.get("display_name", ""), "NO_SOURCE"))
            continue
        bad = []
        signatures = set()
        for cid in source_ids:
            style = style_by_key.get((mid, district_scope, cid)) or style_by_key.get((mid, "MUNICIPALITY_WIDE", cid))
            if not usable(style):
                bad.append(cid)
            else:
                signatures.add((style["display_color"].upper(), style["border_color"].upper(), style["text_color"].upper()))
        if bad:
            missing[mid].append((r.get("teaching_box_id", ""), r.get("display_name", ""), "MISSING:" + ";".join(bad)))
        elif len(signatures) != 1:
            missing[mid].append((r.get("teaching_box_id", ""), r.get("display_name", ""), "CONFLICTING_STYLES"))
        else:
            resolved[mid] += 1

    print("ALL_TEACHING_BOX_STYLE_AUDIT")
    print(f"target_municipalities={len(target_mids)}")
    for mid in sorted(target_mids):
        print(f"{mid}: resolved={resolved[mid]} missing={len(missing[mid])} simplified={simplified[mid]}")
        for box_id, name, reason in missing[mid]:
            print(f"  - {box_id} | {name} | {reason}")

    missing_count = sum(len(v) for v in missing.values())
    print(f"missing_total={missing_count}")
    if missing_count:
        raise SystemExit(2)
    print("ALL_TEACHING_BOX_STYLE_AUDIT_PASSED")


if __name__ == "__main__":
    main()
