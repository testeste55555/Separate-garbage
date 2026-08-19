#!/usr/bin/env python3
"""Batch 12 adversarial checks for official resident-facing taxonomy authenticity."""
from __future__ import annotations

from collections import Counter

from schema_v12 import MASTER, RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS = {"M116","M117","M118","M119","M121","M122","M124","M125"}
EXPECTED = {"M116":18,"M117":10,"M118":13,"M119":15,"M121":18,"M122":15,"M124":14,"M125":17}


def paths():
    b = RESEARCH / "batches" / "batch_12"
    p = "batch_12_"
    return {
        "municipality_path": b/f"{p}municipalities.csv", "category_path": b/f"{p}categories.csv",
        "source_path": b/f"{p}sources.csv", "qa_path": b/f"{p}qa.csv",
        "mapping_path": b/f"{p}item_mapping.csv", "coverage_path": b/f"{p}item_coverage.csv",
        "review_evidence_path": b/f"{p}category_review_evidence.csv",
    }


def main() -> int:
    p = paths()
    errors, _, _ = validate_dataset(label="BATCH_12", **p)
    _, munis = read_csv(p["municipality_path"])
    _, cats = read_csv(p["category_path"])
    _, qa = read_csv(p["qa_path"])
    _, cov = read_csv(p["coverage_path"])
    _, evidence = read_csv(p["review_evidence_path"])
    _, deferred = read_csv(MASTER / "05_deferred_municipalities.csv")

    by = {r["municipality_id"]: r for r in munis}
    q = {r["municipality_id"]: r for r in qa}
    evc = Counter(r["municipality_id"] for r in evidence)
    names = {mid: {r["自治体正式名称"] for r in cats if r["municipality_id"] == mid and r.get("rule_status") == "CURRENT"} for mid in TARGETS}
    rows = {(r["municipality_id"], r["自治体正式名称"]): r for r in cats if r.get("rule_status") == "CURRENT"}
    children = Counter(r.get("parent_category_id", "") for r in cats if r.get("parent_category_id"))
    deferred_by = {r["municipality_id"]: r for r in deferred}

    checks = []
    checks.append(("structural validation passes", not errors, f"errors={len(errors)}"))
    checks.append(("exact active Batch 12 target set", set(by) == TARGETS, str(sorted(by))))
    checks.append(("all eight active municipalities QA_PASSED", all(q[mid]["確認ステータス"] == "QA_PASSED" for mid in TARGETS), ""))
    checks.append(("all official leaf counts match reviewed design", all(counted_category_total(mid, cats) == EXPECTED[mid] for mid in TARGETS), str({mid: counted_category_total(mid, cats) for mid in sorted(TARGETS)})))
    checks.append(("all active municipalities have category review evidence", all(evc[mid] >= 1 for mid in TARGETS), str(evc)))
    checks.append(("all Batch 12 counts are manual index reviews", all(by[mid]["category_count_check_status"] == "MANUAL_INDEX_REVIEW" and not by[mid]["official_category_count"] for mid in TARGETS), ""))

    for mid, token in [("M120", "大島・見島・相島"), ("M123", "食品トレー")]:
        r = deferred_by.get(mid, {})
        checks.append((f"{mid} deferred for real regional taxonomy variance", r.get("status") == "DEFERRED" and r.get("decision_source") == "SCHEMA_SCOPE_LIMITATION" and token in r.get("reason", ""), r.get("reason", "")))

    # M116: exact official same-name heading collision is handled without an invented child suffix.
    m116_can = rows[("M116", "空きカン")]
    m116_bin = rows[("M116", "空きビン")]
    m116_nonburn = rows[("M116", "不燃物・容器包装以外のプラスチック")]
    checks.append(("Jinsekikogen preserves three can and three bottle child leaves", children[m116_can["category_id"]] == 3 and children[m116_bin["category_id"]] == 3, ""))
    checks.append(("Jinsekikogen plastic heading collision keeps three exact resident streams", {"ペットボトル","容器や包装のプラスチック","白色トレー"}.issubset(names["M116"]) and "容器や包装のプラスチック（プラマーク）" not in names["M116"], str(names["M116"])))
    checks.append(("Jinsekikogen nonburnable group has four separately bagged leaves", children[m116_nonburn["category_id"]] == 4 and counted_category_total("M116", cats) == 18, f"children={children[m116_nonburn['category_id']]}"))
    checks.append(("Jinsekikogen spray rule does not invent a hole requirement", "穴" not in rows[("M116", "その他の缶")].get("出す前の処理", ""), rows[("M116", "その他の缶")].get("出す前の処理", "")))

    # M117: three old-paper resident units; bulky remains special reference route.
    m117_paper = rows[("M117", "古紙")]
    checks.append(("Shimonoseki old paper parent has three child leaves", children[m117_paper["category_id"]] == 3 and counted_category_total("M117", cats) == 10, f"children={children[m117_paper['category_id']]}"))
    checks.append(("Shimonoseki bulky remains booked reference route", rows[("M117", "粗大ごみ")].get("ui_role") == "REFERENCE_ONLY" and rows[("M117", "粗大ごみ")].get("collection_channel") == "BOOKED_PICKUP", ""))

    # M118: rechargeable batteries are not forced into station collection.
    m118_paper = rows[("M118", "古紙")]
    checks.append(("Ube old paper parent has three child leaves", children[m118_paper["category_id"]] == 3 and counted_category_total("M118", cats) == 13, f"children={children[m118_paper['category_id']]}"))
    checks.append(("Ube rechargeable battery is DROP_OFF reference leaf", rows[("M118", "充電式電池")].get("collection_channel") == "DROP_OFF" and rows[("M118", "充電式電池")].get("ui_role") == "REFERENCE_ONLY", ""))
    checks.append(("Ube spray cans retain mandatory puncture rule", "必ず穴を開ける" in rows[("M118", "びん・缶")].get("出す前の処理", ""), rows[("M118", "びん・缶")].get("出す前の処理", "")))

    # M119: fresh July 2026 split must not regress to one broad hazardous category.
    m119_paper = rows[("M119", "古紙")]
    checks.append(("Yamaguchi old paper parent has five child leaves", children[m119_paper["category_id"]] == 5 and counted_category_total("M119", cats) == 15, f"children={children[m119_paper['category_id']]}"))
    checks.append(("Yamaguchi keeps July 2026 hazardous split", {"有害ごみ(1)","有害ごみ(2)"}.issubset(names["M119"]) and "有害ごみ" not in names["M119"], str(names["M119"])))
    checks.append(("Yamaguchi both hazardous streams are DROP_OFF", all(rows[("M119", n)].get("collection_channel") == "DROP_OFF" for n in ["有害ごみ(1)","有害ごみ(2)"]), ""))
    checks.append(("Yamaguchi hazard1 spray prep retains puncture rule", "穴を開ける" in rows[("M119", "有害ごみ(1)")].get("出す前の処理", ""), rows[("M119", "有害ごみ(1)")].get("出す前の処理", "")))

    # M121: booklet hierarchy is preserved, not flattened into only five calendar headings.
    m121_resource = rows[("M121", "資源ごみ")]
    m121_danger = rows[("M121", "危険ごみ")]
    m121_paid = rows[("M121", "粗大ごみ・埋立ごみ・一時多量ごみ（有料収集）")]
    checks.append(("Hofu resource parent has seven official child leaves", children[m121_resource["category_id"]] == 7, f"children={children[m121_resource['category_id']]}"))
    checks.append(("Hofu dangerous parent has six official child leaves", children[m121_danger["category_id"]] == 6, f"children={children[m121_danger['category_id']]}"))
    checks.append(("Hofu paid special parent has three official child leaves", children[m121_paid["category_id"]] == 3 and counted_category_total("M121", cats) == 18, f"children={children[m121_paid['category_id']]}"))
    checks.append(("Hofu spray cans retain puncture rule", "穴を開ける" in rows[("M121", "スプレー缶類")].get("出す前の処理", ""), rows[("M121", "スプレー缶類")].get("出す前の処理", "")))

    # M122: combustible resources are separate tied streams; spray cans go to metal after puncture.
    m122_resource = rows[("M122", "可燃系資源")]
    checks.append(("Kudamatsu combustible resources have four child leaves", children[m122_resource["category_id"]] == 4 and counted_category_total("M122", cats) == 15, f"children={children[m122_resource['category_id']]}"))
    checks.append(("Kudamatsu spray rule retains mandatory puncture", "必ず穴を開ける" in rows[("M122", "金属類")].get("出す前の処理", ""), rows[("M122", "金属類")].get("出す前の処理", "")))

    # M124: 14 divisions exactly; magazines and miscellaneous paper are one leaf.
    m124_paper = rows[("M124", "古紙類")]
    checks.append(("Hikari remains exactly fourteen official leaves", counted_category_total("M124", cats) == 14, str(names["M124"])))
    checks.append(("Hikari old paper parent has exactly three leaves", children[m124_paper["category_id"]] == 3 and {"新聞類","雑誌類・雑がみ","段ボール"}.issubset(names["M124"]) and "雑がみ" not in names["M124"], f"children={children[m124_paper['category_id']]}"))
    checks.append(("Hikari spray cans retain mandatory puncture", "必ず穴を開ける" in rows[("M124", "金属類")].get("出す前の処理", ""), rows[("M124", "金属類")].get("出す前の処理", "")))

    # M125: exact 17-leaf structure and three bottle colours.
    m125_paper = rows[("M125", "古紙・衣類")]
    m125_bottle = rows[("M125", "ビン")]
    checks.append(("Nagato remains seventeen official leaves", counted_category_total("M125", cats) == 17, str(names["M125"])))
    checks.append(("Nagato paper-clothing parent has five child leaves", children[m125_paper["category_id"]] == 5, f"children={children[m125_paper['category_id']]}"))
    checks.append(("Nagato bottle parent has three colour leaves", children[m125_bottle["category_id"]] == 3 and {"無色","茶色","その他色"}.issubset(names["M125"]), f"children={children[m125_bottle['category_id']]}"))
    checks.append(("Nagato cans remain one official leaf", "缶" in names["M125"] and not ({"アルミ缶","スチール缶"} & names["M125"]), ""))
    checks.append(("Nagato fluorescent tube leaf retained", "蛍光灯（管）" in names["M125"], ""))

    checks.append(("coverage exactly eight x forty", len(cov) == 320 and Counter(r["municipality_id"] for r in cov) == Counter({mid:40 for mid in TARGETS}), f"coverage={len(cov)}"))
    checks.append(("no generic/filler category detail survives", not any(is_placeholder_category_value(r.get(f, "")) for r in cats for f in CATEGORY_DETAIL_FIELDS), f"categories={len(cats)}"))
    checks.append(("all category evidence uses research date", all(r.get("確認日") == "2026-08-19" for r in cats), ""))

    passed = sum(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    print(f"BATCH12_RED_TEAM_SUMMARY={passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
