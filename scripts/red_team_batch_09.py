#!/usr/bin/env python3
"""Batch 09 adversarial checks for resident-facing category authenticity."""
from __future__ import annotations

from collections import Counter

from schema_v12 import MASTER, RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS = {"M084", "M085", "M087", "M088", "M089", "M090", "M091", "M092", "M093"}
EXPECTED = {"M084":10, "M085":11, "M087":8, "M088":7, "M089":2, "M090":5, "M091":14, "M092":5, "M093":11}


def paths():
    b = RESEARCH / "batches" / "batch_09"
    p = "batch_09_"
    return {
        "municipality_path": b / f"{p}municipalities.csv", "category_path": b / f"{p}categories.csv",
        "source_path": b / f"{p}sources.csv", "qa_path": b / f"{p}qa.csv",
        "mapping_path": b / f"{p}item_mapping.csv", "coverage_path": b / f"{p}item_coverage.csv",
        "review_evidence_path": b / f"{p}category_review_evidence.csv",
    }


def main() -> int:
    p = paths()
    errors, _, _ = validate_dataset(label="BATCH_09", **p)
    _, munis = read_csv(p["municipality_path"])
    _, cats = read_csv(p["category_path"])
    _, qa = read_csv(p["qa_path"])
    _, cov = read_csv(p["coverage_path"])
    _, evidence = read_csv(p["review_evidence_path"])
    _, deferred = read_csv(MASTER / "05_deferred_municipalities.csv")

    by = {r["municipality_id"]: r for r in munis}
    q = {r["municipality_id"]: r for r in qa}
    evc = Counter(r["municipality_id"] for r in evidence)
    names = {mid:{r["自治体正式名称"] for r in cats if r["municipality_id"]==mid and r.get("rule_status")=="CURRENT"} for mid in TARGETS}
    rows = {(r["municipality_id"], r["自治体正式名称"]):r for r in cats if r.get("rule_status")=="CURRENT"}
    children = Counter(r.get("parent_category_id", "") for r in cats if r.get("parent_category_id"))
    deferred_by = {r["municipality_id"]: r for r in deferred}

    checks = []
    checks.append(("structural validation passes", not errors, f"errors={len(errors)}"))
    checks.append(("exact active target set excludes Shinjo", set(by)==TARGETS and "M086" not in by, str(sorted(by))))
    checks.append(("all nine active municipalities QA_PASSED", all(q[mid]["確認ステータス"]=="QA_PASSED" for mid in TARGETS), ""))
    checks.append(("all official leaf counts match design", all(
        counted_category_total(mid,cats)==EXPECTED[mid]
        and (
            (mid=="M088" and by[mid]["official_category_count"]==str(EXPECTED[mid]) and by[mid]["category_count_check_status"]=="OFFICIAL_COUNT_MATCHED")
            or (mid!="M088" and by[mid]["reviewed_category_count"]==str(EXPECTED[mid]))
        )
        for mid in TARGETS
    ), str({mid:counted_category_total(mid,cats) for mid in sorted(TARGETS)})))
    checks.append(("every active municipality has review evidence", all(evc[mid]>=1 for mid in TARGETS), str(evc)))
    checks.append(("Shinjo fixed ID is deferred not fabricated", "M086" in deferred_by and deferred_by["M086"]["status"]=="DEFERRED" and "全分別区分" in deferred_by["M086"]["reason"], deferred_by.get("M086",{}).get("reason","")))

    checks.append(("Satosho retains seven resource streams plus burnable/unburnable/bulky", names["M084"]=={"燃えるごみ","燃えないごみ","缶","びん類","ペットボトル","その他プラスチック","製品プラスチック","紙類","古布","粗大ごみ"}, str(names["M084"])))
    checks.append(("Yakage does not double count large nonburnable pickup service", counted_category_total("M085",cats)==11 and "家庭大型ごみ（不燃物）収集" not in names["M085"], str(names["M085"])))
    checks.append(("Yakage preserves exact size-qualified category headings", {"可燃ごみ［30cm以下の焼却処理のできるごみ］","可燃ごみ［大型］","不燃ごみ［30cm以下の焼却処理のできないごみ］","不燃ごみ［大型］"}.issubset(names["M085"]), ""))

    kag_parent = rows.get(("M087","資源ごみ"),{})
    checks.append(("Kagamino resource parent has four official leaves", bool(kag_parent) and children[kag_parent.get("category_id","")]==4 and counted_category_total("M087",cats)==8, f"children={children[kag_parent.get('category_id','')]}"))
    kag_can = rows.get(("M087","缶"),{})
    checks.append(("Kagamino aerosol rule does not invent hole requirement", "穴" not in kag_can.get("出す前の処理","") and "使い切" in kag_can.get("出す前の処理",""), kag_can.get("出す前の処理","")))

    checks.append(("Shoo official total stays exactly seven", by["M088"]["category_count_check_status"]=="OFFICIAL_COUNT_MATCHED" and by["M088"]["official_category_count"]=="7" and names["M088"]=={"可燃ごみ","資源ごみA","資源ごみB","資源ごみC","資源ごみD","資源ごみE","不燃ごみ"}, str(names["M088"])))
    checks.append(("Shoo bulky route is not synthetic eighth leaf", "粗大ごみ" not in names["M088"], ""))

    checks.append(("Nagi composite collection label is not split", names["M089"]=={"可燃ごみ","資源ごみ・小型不燃ごみ・有害なごみ"} and not ({"資源ごみ","小型不燃ごみ","有害なごみ"} & names["M089"]), str(names["M089"])))
    checks.append(("Nishiawakura keeps five village calendar groups", counted_category_total("M090",cats)==5 and {"可燃ごみ","資源ごみ","かん類・乾電池類・ライター・スプレー缶","古紙類"}.issubset(names["M090"]), str(names["M090"])))

    kum_parent = rows.get(("M091","資源ごみ"),{})
    checks.append(("Kumenan resource parent has nine official children", bool(kum_parent) and children[kum_parent.get("category_id","")]==9 and counted_category_total("M091",cats)==14, f"children={children[kum_parent.get('category_id','')]}"))
    kum_hazard = rows.get(("M091","適正処理ごみ"),{})
    checks.append(("Kumenan aerosol keeps explicit no-hole rule", "穴を開けない" in kum_hazard.get("出す前の処理","") and "使い切" in kum_hazard.get("出す前の処理",""), kum_hazard.get("出す前の処理","")))

    checks.append(("Misaki stays at five townwide resident labels", counted_category_total("M092",cats)==5 and names["M092"]=={"可燃ごみ","不燃ごみ","プラスチック製容器包装ごみ","資源ごみ","粗大ごみ"}, str(names["M092"])))
    kibi_parent = rows.get(("M093","資源ごみ"),{})
    checks.append(("Kibichuo resource parent has six official children and 11 leaves", bool(kibi_parent) and children[kibi_parent.get("category_id","")]==6 and counted_category_total("M093",cats)==11, f"children={children[kibi_parent.get('category_id','')]}"))
    checks.append(("Kibichuo keeps separate combustible/noncombustible bulky and fluorescent", {"可燃粗大","不燃粗大","蛍光管"}.issubset(names["M093"]), ""))

    checks.append(("coverage exactly nine x forty", len(cov)==360 and Counter(r["municipality_id"] for r in cov)==Counter({mid:40 for mid in TARGETS}), f"coverage={len(cov)}"))
    checks.append(("no filler placeholders", not any(is_placeholder_category_value(r.get(f,"")) for r in cats for f in CATEGORY_DETAIL_FIELDS), f"categories={len(cats)}"))
    checks.append(("all category evidence checked on research date", all(r.get("確認日")=="2026-08-19" for r in cats), ""))

    passed = sum(ok for _,ok,_ in checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    print(f"BATCH09_RED_TEAM_SUMMARY={passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
