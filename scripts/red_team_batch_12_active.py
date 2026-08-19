#!/usr/bin/env python3
"""Production RED TEAM for Batch 12 after projection-only fixes."""
from __future__ import annotations

from collections import Counter

from schema_v12 import MASTER, RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS = {"M116","M117","M118","M119","M121","M122","M124","M125"}
EXPECTED = {"M116":18,"M117":10,"M118":13,"M119":15,"M121":18,"M122":15,"M124":14,"M125":17}


def main() -> int:
    b = RESEARCH / "batches" / "batch_12"
    p = "batch_12_"
    paths = {
        "municipality_path": b/f"{p}municipalities.csv", "category_path": b/f"{p}categories.csv",
        "source_path": b/f"{p}sources.csv", "qa_path": b/f"{p}qa.csv",
        "mapping_path": b/f"{p}item_mapping.csv", "coverage_path": b/f"{p}item_coverage.csv",
        "review_evidence_path": b/f"{p}category_review_evidence.csv",
    }
    errors, _, _ = validate_dataset(label="BATCH_12", **paths)
    _, munis = read_csv(paths["municipality_path"])
    _, cats = read_csv(paths["category_path"])
    _, qa = read_csv(paths["qa_path"])
    _, cov = read_csv(paths["coverage_path"])
    _, evidence = read_csv(paths["review_evidence_path"])
    _, deferred = read_csv(MASTER / "05_deferred_municipalities.csv")

    by = {r["municipality_id"]: r for r in munis}
    q = {r["municipality_id"]: r for r in qa}
    evc = Counter(r["municipality_id"] for r in evidence)
    current = [r for r in cats if r.get("rule_status") == "CURRENT"]
    names = {mid: {r["自治体正式名称"] for r in current if r["municipality_id"] == mid} for mid in TARGETS}
    rows = {(r["municipality_id"], r["自治体正式名称"]): r for r in current}
    children = Counter(r.get("parent_category_id", "") for r in current if r.get("parent_category_id"))
    deferred_by = {r["municipality_id"]: r for r in deferred}

    checks: list[tuple[str, bool, str]] = []
    checks.append(("structural validation passes", not errors, f"errors={len(errors)} {errors[:5]}"))
    checks.append(("exact active Batch 12 target set", set(by) == TARGETS, str(sorted(by))))
    checks.append(("all eight active municipalities QA_PASSED", all(q[mid]["確認ステータス"] == "QA_PASSED" for mid in TARGETS), ""))
    checks.append(("official leaf counts match reviewed design", all(counted_category_total(mid, cats) == EXPECTED[mid] for mid in TARGETS), str({mid: counted_category_total(mid, cats) for mid in sorted(TARGETS)})))
    checks.append(("all counts use MANUAL_INDEX_REVIEW", all(by[mid]["category_count_check_status"] == "MANUAL_INDEX_REVIEW" and not by[mid]["official_category_count"] for mid in TARGETS), ""))
    checks.append(("all municipalities have formal review evidence", all(evc[mid] >= 1 for mid in TARGETS), str(evc)))

    checks.append(("M120 Hagi remains regional-variant DEFERRED", deferred_by.get("M120", {}).get("decision_source") == "SCHEMA_SCOPE_LIMITATION" and "大島・見島・相島" in deferred_by.get("M120", {}).get("reason", ""), deferred_by.get("M120", {}).get("reason", "")))
    checks.append(("M123 Iwakuni remains regional-variant DEFERRED", deferred_by.get("M123", {}).get("decision_source") == "SCHEMA_SCOPE_LIMITATION" and "食品トレー" in deferred_by.get("M123", {}).get("reason", ""), deferred_by.get("M123", {}).get("reason", "")))

    # M116 神石高原町
    can = rows[("M116", "空きカン")]; bottle = rows[("M116", "空きビン")]; nb = rows[("M116", "不燃物・容器包装以外のプラスチック")]
    checks.append(("M116 can/bottle children preserved", children[can["category_id"]] == 3 and children[bottle["category_id"]] == 3, ""))
    checks.append(("M116 exact three plastic streams without invented suffix", {"ペットボトル","容器や包装のプラスチック","白色トレー"}.issubset(names["M116"]) and "容器や包装のプラスチック（プラマーク）" not in names["M116"], str(names["M116"])))
    checks.append(("M116 nonburnable group has four child leaves", children[nb["category_id"]] == 4, f"children={children[nb['category_id']]}"))
    checks.append(("M116 spray rule does not invent hole instruction", "穴" not in rows[("M116", "その他の缶")].get("出す前の処理", ""), rows[("M116", "その他の缶")].get("出す前の処理", "")))

    # M117 下関市
    paper117 = rows[("M117", "古紙")]
    checks.append(("M117 old paper has three child leaves", children[paper117["category_id"]] == 3, ""))
    checks.append(("M117 bulky remains BOOKED_PICKUP reference", rows[("M117", "粗大ごみ")].get("collection_channel") == "BOOKED_PICKUP" and rows[("M117", "粗大ごみ")].get("ui_role") == "REFERENCE_ONLY", ""))

    # M118 宇部市
    paper118 = rows[("M118", "古紙")]
    checks.append(("M118 old paper has three child leaves", children[paper118["category_id"]] == 3, ""))
    checks.append(("M118 rechargeable batteries remain DROP_OFF reference", rows[("M118", "充電式電池")].get("collection_channel") == "DROP_OFF" and rows[("M118", "充電式電池")].get("ui_role") == "REFERENCE_ONLY", ""))
    checks.append(("M118 spray cans retain mandatory puncture", "必ず穴を開ける" in rows[("M118", "びん・缶")].get("出す前の処理", ""), rows[("M118", "びん・缶")].get("出す前の処理", "")))

    # M119 山口市 — July 2026 split
    paper119 = rows[("M119", "古紙")]
    checks.append(("M119 old paper has five child leaves", children[paper119["category_id"]] == 5, ""))
    checks.append(("M119 keeps July 2026 hazardous split", {"有害ごみ(1)","有害ごみ(2)"}.issubset(names["M119"]) and "有害ごみ" not in names["M119"], str(names["M119"])))
    checks.append(("M119 hazardous streams remain DROP_OFF", all(rows[("M119", n)].get("collection_channel") == "DROP_OFF" for n in ["有害ごみ(1)","有害ごみ(2)"]), ""))
    checks.append(("M119 hazard1 retains spray puncture rule", "穴を開ける" in rows[("M119", "有害ごみ(1)")].get("出す前の処理", ""), ""))

    # M121 防府市 — special routes grouped without a fake projection bucket.
    res121 = rows[("M121", "資源ごみ")]; danger121 = rows[("M121", "危険ごみ")]
    checks.append(("M121 resource parent has seven child leaves", children[res121["category_id"]] == 7, ""))
    checks.append(("M121 dangerous parent has six child leaves", children[danger121["category_id"]] == 6, ""))
    special121 = [rows[("M121", n)] for n in ["粗大ごみ","埋立ごみ","一時多量ごみ"]]
    checks.append(("M121 three paid special leaves are independent references", all(r.get("ui_role") == "REFERENCE_ONLY" and not r.get("parent_category_id") and r.get("category_group") == "粗大ごみ・埋立ごみ・一時多量ごみ（有料収集）" for r in special121) and "粗大ごみ・埋立ごみ・一時多量ごみ（有料収集）" not in names["M121"], ""))
    checks.append(("M121 spray cans retain puncture rule", "穴を開ける" in rows[("M121", "スプレー缶類")].get("出す前の処理", ""), ""))

    # M122 下松市
    res122 = rows[("M122", "可燃系資源")]
    checks.append(("M122 combustible resources have four child leaves", children[res122["category_id"]] == 4, ""))
    checks.append(("M122 spray rule remains mandatory puncture", "必ず穴を開ける" in rows[("M122", "金属類")].get("出す前の処理", ""), ""))

    # M124 光市
    paper124 = rows[("M124", "古紙類")]
    checks.append(("M124 exact 14 leaves", counted_category_total("M124", cats) == 14, ""))
    checks.append(("M124 old paper is exactly three leaves", children[paper124["category_id"]] == 3 and {"新聞類","雑誌類・雑がみ","段ボール"}.issubset(names["M124"]) and "雑がみ" not in names["M124"], ""))
    checks.append(("M124 spray rule remains mandatory puncture", "必ず穴を開ける" in rows[("M124", "金属類")].get("出す前の処理", ""), ""))

    # M125 長門市
    paper125 = rows[("M125", "古紙・衣類")]; bin125 = rows[("M125", "ビン")]
    checks.append(("M125 exact 17 leaves", counted_category_total("M125", cats) == 17, ""))
    checks.append(("M125 paper/clothing has five child leaves", children[paper125["category_id"]] == 5, ""))
    checks.append(("M125 bottles have three colour leaves", children[bin125["category_id"]] == 3 and {"無色","茶色","その他色"}.issubset(names["M125"]), ""))
    checks.append(("M125 cans remain one leaf and fluorescent leaf retained", "缶" in names["M125"] and not ({"アルミ缶","スチール缶"} & names["M125"]) and "蛍光灯（管）" in names["M125"], ""))

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
