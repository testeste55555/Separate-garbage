#!/usr/bin/env python3
"""Adversarial authenticity checks for final Batch 14."""
from __future__ import annotations

from collections import Counter

from schema_v12 import MASTER, RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS = {"M137","M138","M140","M141","M142","M143"}
EXPECTED = {"M137":11,"M138":18,"M140":16,"M141":7,"M142":13,"M143":12}


def main() -> int:
    b = RESEARCH / "batches" / "batch_14"
    p = "batch_14_"
    paths = {
        "municipality_path": b/f"{p}municipalities.csv", "category_path": b/f"{p}categories.csv",
        "source_path": b/f"{p}sources.csv", "qa_path": b/f"{p}qa.csv",
        "mapping_path": b/f"{p}item_mapping.csv", "coverage_path": b/f"{p}item_coverage.csv",
        "review_evidence_path": b/f"{p}category_review_evidence.csv",
    }
    errors, _, _ = validate_dataset(label="BATCH_14", **paths)
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
    checks.append(("exact active Batch 14 target set", set(by) == TARGETS, str(sorted(by))))
    checks.append(("all six active municipalities QA_PASSED", all(q[mid]["確認ステータス"] == "QA_PASSED" for mid in TARGETS), ""))
    checks.append(("official leaf counts match reviewed design", all(counted_category_total(mid, cats) == EXPECTED[mid] for mid in TARGETS), str({mid: counted_category_total(mid, cats) for mid in sorted(TARGETS)})))
    checks.append(("all counts use MANUAL_INDEX_REVIEW", all(by[mid]["category_count_check_status"] == "MANUAL_INDEX_REVIEW" and not by[mid]["official_category_count"] for mid in TARGETS), ""))
    checks.append(("all municipalities have formal review evidence", all(evc[mid] >= 1 for mid in TARGETS), str(evc)))

    y = deferred_by.get("M136", {})
    checks.append(("M136 Yoshinogawa is regional-route DEFERRED", y.get("status") == "DEFERRED" and y.get("decision_source") == "SCHEMA_SCOPE_LIMITATION" and all(t in y.get("reason", "") for t in ["鴨島","川島","山川","美郷","回収容器"]), y.get("reason", "")))
    m = deferred_by.get("M139", {})
    checks.append(("M139 Marugame is island-variant DEFERRED", m.get("status") == "DEFERRED" and m.get("decision_source") == "SCHEMA_SCOPE_LIMITATION" and all(t in m.get("reason", "") for t in ["旧丸亀","本島","牛島","小手島","手島"]), m.get("reason", "")))

    # M137 綾川町
    checks.append(("M137 keeps eight townwide routine classes", {"燃やせるごみ","プラスチック容器包装","破砕ごみ","ペットボトル","ビン類","缶類","古紙類","有害ごみ"}.issubset(names["M137"]), str(names["M137"])))
    checks.append(("M137 rechargeable batteries are insulated DROP_OFF references", rows[("M137","小型充電式電池")].get("collection_channel") == "DROP_OFF" and rows[("M137","小型充電式電池")].get("ui_role") == "REFERENCE_ONLY" and "絶縁" in rows[("M137","小型充電式電池")].get("出す前の処理", ""), rows[("M137","小型充電式電池")].get("出す前の処理", "")))
    checks.append(("M137 battery-containing small appliances preserve removal branch", rows[("M137","小型家電")].get("collection_channel") == "DROP_OFF" and "取り外せる" in rows[("M137","小型家電")].get("出す前の処理", ""), ""))

    # M138 多度津町
    res138 = rows[("M138", "資源ごみ")]
    expected138 = {"空かん(アルミ・スチール)","金属","布","牛乳パック","新聞紙","段ボール","雑誌","生きびん","駄ビン","ペットボトル","白色トレイ","廃食油","乾電池","蛍光管","小型家電"}
    checks.append(("M138 resource parent resolves to fifteen resident leaves", children[res138["category_id"]] == 15 and expected138.issubset(names["M138"]), str(names["M138"])))
    checks.append(("M138 resource children are references not duplicate learner buckets", all(rows[("M138", n)].get("ui_role") == "REFERENCE_ONLY" for n in expected138), ""))
    checks.append(("M138 white tray and PET remain separate outputs", rows[("M138","白色トレイ")]["category_id"] != rows[("M138","ペットボトル")]["category_id"] and "混ぜ" not in rows[("M138","白色トレイ")].get("自治体正式名称", ""), ""))
    checks.append(("M138 rough waste stays independent reference leaf", rows[("M138","粗大ごみ")].get("ui_role") == "REFERENCE_ONLY" and rows[("M138","粗大ごみ")].get("粗大ごみ扱いか") == "TRUE", ""))

    # M140 三豊市
    paper140 = rows[("M140", "紙類・布類")]
    checks.append(("M140 official twelve headings retained without treating 12 as leaf total", {"燃やせるごみ（可燃ごみ）","燃やせないごみ（不燃ごみ）","缶類","びん類","ペットボトル","紙製容器包装","プラスチック製容器包装","金属ごみ","有害ごみ","廃食用油（天ぷら油）","紙類・布類","粗大ごみ"}.issubset(names["M140"]) and counted_category_total("M140", cats) == 16, str(names["M140"])))
    checks.append(("M140 paper/clothing parent resolves to five separate output leaves", children[paper140["category_id"]] == 5 and {"新聞","雑誌","ダンボール","紙パック","衣類"}.issubset(names["M140"]), ""))
    checks.append(("M140 used cooking oil is DROP_OFF reference", rows[("M140","廃食用油（天ぷら油）")].get("collection_channel") == "DROP_OFF" and rows[("M140","廃食用油（天ぷら油）")].get("ui_role") == "REFERENCE_ONLY", ""))
    checks.append(("M140 rechargeable batteries do not get sent to station", "ごみステーションに出さず" in rows[("M140","有害ごみ")].get("出す前の処理", ""), rows[("M140","有害ごみ")].get("出す前の処理", "")))

    # M141 小竹町
    checks.append(("M141 exact five calendar classes retained", {"固形燃料用ごみ（燃えるごみ）","びん・缶","ペットボトル","燃えないゴミ","粗大ごみ"}.issubset(names["M141"]), str(names["M141"])))
    checks.append(("M141 does not split official combined bottle/can calendar class", not ({"びん","缶"} & names["M141"]), str(names["M141"])))
    checks.append(("M141 April 2026 tray and styrofoam streams are separate DROP_OFF leaves", all(rows[("M141", n)].get("collection_channel") == "DROP_OFF" and rows[("M141", n)].get("ui_role") == "REFERENCE_ONLY" for n in ["食品用トレイ類","発泡スチロール"]) and "発泡スチロールと分け" in rows[("M141","食品用トレイ類")].get("出す前の処理", ""), ""))

    # M142 北九州市
    kb = rows[("M142", "かん・びん・ペットボトル")]
    checks.append(("M142 combined index heading resolves to two actual bag outputs", children[kb["category_id"]] == 2 and {"かん・びん","ペットボトル"}.issubset(names["M142"]), ""))
    checks.append(("M142 can/bottle and PET children remain curbside references", all(rows[("M142", n)].get("collection_channel") == "CURBSIDE" and rows[("M142", n)].get("ui_role") == "REFERENCE_ONLY" for n in ["かん・びん","ペットボトル"]), ""))
    checks.append(("M142 spray cans are explicitly excluded from can/bottle leaf", "スプレー缶" in rows[("M142","かん・びん")].get("入れてはいけない物", ""), rows[("M142","かん・びん")].get("入れてはいけない物", "")))
    checks.append(("M142 drop-off categories remain references", all(rows[("M142", n)].get("collection_channel") == "DROP_OFF" and rows[("M142", n)].get("ui_role") == "REFERENCE_ONLY" for n in ["紙パック・トレイ","蛍光管","小物金属","小型電子機器","使用済食用油","電池","古紙","古着"]), ""))
    checks.append(("M142 non-collected notice excluded from official leaf total", rows[("M142","市が収集しないもの")].get("ui_role") == "EXCLUDED_NOTICE" and rows[("M142","市が収集しないもの")].get("collection_channel") == "NOT_COLLECTED", ""))

    # M143 佐伯市
    res143 = rows[("M143", "資源物")]
    expected143 = {"飲食用ビン・カン","ペットボトル","古紙（新聞）","古紙（ダンボール）","古紙（その他の紙類）","布類（リサイクル可能なもの）","小型家電（使用済小型電子機器）"}
    checks.append(("M143 resource parent resolves to seven actual output leaves", children[res143["category_id"]] == 7 and expected143.issubset(names["M143"]), str(names["M143"])))
    checks.append(("M143 beverage container streams preserve separate bags", {"飲食用ビン・カン","ペットボトル"}.issubset(names["M143"]), ""))
    checks.append(("M143 old paper preserves three separate bundle leaves", {"古紙（新聞）","古紙（ダンボール）","古紙（その他の紙類）"}.issubset(names["M143"]), ""))
    checks.append(("M143 spray cans retain two-hole rule in nonburnable waste", "穴を2か所" in rows[("M143","燃えないごみ")].get("出す前の処理", ""), rows[("M143","燃えないごみ")].get("出す前の処理", "")))
    checks.append(("M143 bulky waste is booked-pickup reference", rows[("M143","粗大ごみ")].get("collection_channel") == "BOOKED_PICKUP" and rows[("M143","粗大ごみ")].get("ui_role") == "REFERENCE_ONLY", ""))
    checks.append(("M143 rubble remains independent current leaf", "ガレキ類" in names["M143"] and rows[("M143","ガレキ類")].get("rule_status") == "CURRENT", ""))

    checks.append(("coverage exactly six x forty", len(cov) == 240 and Counter(r["municipality_id"] for r in cov) == Counter({mid:40 for mid in TARGETS}), f"coverage={len(cov)}"))
    checks.append(("no generic/filler category detail survives", not any(is_placeholder_category_value(r.get(f, "")) for r in cats for f in CATEGORY_DETAIL_FIELDS), f"categories={len(cats)}"))
    checks.append(("all category evidence uses research date", all(r.get("確認日") == "2026-08-19" for r in cats), ""))

    passed = sum(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    print(f"BATCH14_RED_TEAM_SUMMARY={passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
