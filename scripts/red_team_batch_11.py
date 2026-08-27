#!/usr/bin/env python3
"""Batch 11 adversarial checks for resident-facing category authenticity."""
from __future__ import annotations

from collections import Counter

from schema_v12 import RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS = {f"M{i:03d}" for i in range(106, 116)}
EXPECTED = {"M106":11,"M107":8,"M108":11,"M109":9,"M110":6,"M111":13,"M112":12,"M113":11,"M114":8,"M115":9}


def paths():
    b = RESEARCH / "batches" / "batch_11"
    p = "batch_11_"
    return {
        "municipality_path": b/f"{p}municipalities.csv", "category_path": b/f"{p}categories.csv",
        "source_path": b/f"{p}sources.csv", "qa_path": b/f"{p}qa.csv",
        "mapping_path": b/f"{p}item_mapping.csv", "coverage_path": b/f"{p}item_coverage.csv",
        "review_evidence_path": b/f"{p}category_review_evidence.csv",
    }


def main() -> int:
    p = paths()
    errors, _, _ = validate_dataset(label="BATCH_11", **p)
    _, munis = read_csv(p["municipality_path"])
    _, cats = read_csv(p["category_path"])
    _, sources = read_csv(p["source_path"])
    _, qa = read_csv(p["qa_path"])
    _, cov = read_csv(p["coverage_path"])
    _, evidence = read_csv(p["review_evidence_path"])

    by = {r["municipality_id"]: r for r in munis}
    q = {r["municipality_id"]: r for r in qa}
    evc = Counter(r["municipality_id"] for r in evidence)
    names = {mid: {r["自治体正式名称"] for r in cats if r["municipality_id"] == mid and r.get("rule_status") == "CURRENT"} for mid in TARGETS}
    rows = {(r["municipality_id"], r["自治体正式名称"]): r for r in cats if r.get("rule_status") == "CURRENT"}
    children = Counter(r.get("parent_category_id", "") for r in cats if r.get("parent_category_id"))
    source_by_key = {(r["municipality_id"], r["source_id"]): r for r in sources}

    checks = []
    checks.append(("structural validation passes", not errors, f"errors={len(errors)}"))
    checks.append(("exact Batch 11 target set", set(by) == TARGETS, str(sorted(by))))
    checks.append(("all ten municipalities QA_PASSED", all(q[mid]["確認ステータス"] == "QA_PASSED" for mid in TARGETS), ""))
    checks.append(("all official leaf counts match reviewed design", all(counted_category_total(mid, cats) == EXPECTED[mid] for mid in TARGETS), str({mid: counted_category_total(mid, cats) for mid in sorted(TARGETS)})))
    checks.append(("all targets have category review evidence", all(evc[mid] >= 1 for mid in TARGETS), str(evc)))
    checks.append(("all Batch 11 counts are manual index reviews", all(by[mid]["category_count_check_status"] == "MANUAL_INDEX_REVIEW" and not by[mid]["official_category_count"] for mid in TARGETS), ""))

    m106_container = rows[("M106", "容器包装類")]
    m106_nonburn = rows[("M106", "燃えないごみ")]
    checks.append(("Akitakata preserves 3 container and 4 nonburnable child leaves", children[m106_container["category_id"]] == 3 and children[m106_nonburn["category_id"]] == 4 and counted_category_total("M106", cats) == 11, ""))
    checks.append(("Akitakata aerosol rule is no-hole", "穴あけ不要" in rows[("M106", "かん類")].get("出す前の処理", ""), rows[("M106", "かん類")].get("出す前の処理", "")))

    checks.append(("Etajima uses current 2026 eight-category poster", counted_category_total("M107", cats) == 8 and "資源ごみ（古紙・布類）" in names["M107"] and "資源ごみ（古紙）" not in names["M107"] and "資源ごみ（布類）" not in names["M107"], str(names["M107"])))
    checks.append(("Etajima unpunctured aerosol path retained", "穴を開けず" in rows[("M107", "有害・危険ごみ")].get("出す前の処理", ""), rows[("M107", "有害・危険ごみ")].get("出す前の処理", "")))

    fuchu_parent = rows[("M108", "有価物")]
    checks.append(("Fuchucho valuable-material parent has four resident child leaves", children[fuchu_parent["category_id"]] == 4 and counted_category_total("M108", cats) == 11, f"children={children[fuchu_parent['category_id']]}"))

    kaita_parent = rows[("M109", "資源物")]
    checks.append(("Kaita resource parent has five child leaves", children[kaita_parent["category_id"]] == 5 and counted_category_total("M109", cats) == 9, f"children={children[kaita_parent['category_id']]}"))
    checks.append(("Kaita spray cans explicitly no-hole", "穴を開けない" in rows[("M109", "缶・金属類")].get("出す前の処理", ""), rows[("M109", "缶・金属類")].get("出す前の処理", "")))

    checks.append(("Kumano remains exactly six collection labels", names["M110"] == {"可燃ごみ","資源物（1）","資源物（2）","埋立ごみ","有害ごみ","大型ごみ"}, str(names["M110"])))
    checks.append(("Kumano does not promote internal paper/PET small classes", not ({"ペットボトル","紙類","びん類","缶類"} & names["M110"]), ""))

    saka_parent = rows[("M111", "資源ごみ")]
    checks.append(("Saka resource parent has eight child leaves", children[saka_parent["category_id"]] == 8 and counted_category_total("M111", cats) == 13, f"children={children[saka_parent['category_id']]}"))
    checks.append(("Saka retains puncture-required aerosol rule", "穴を開ける" in rows[("M111", "缶類")].get("出す前の処理", ""), rows[("M111", "缶類")].get("出す前の処理", "")))

    checks.append(("Akiota preserves twelve resident leaves", counted_category_total("M112", cats) == 12 and {"缶","ビン","古紙類","衣類・布類","金属類","小型電化製品及び有害物","陶器・ガラス類","その他不燃物","ペットボトル","その他プラスチック"}.issubset(names["M112"]), str(names["M112"])))
    checks.append(("Akiota aerosol rule explicitly no-hole", "穴あけ不要" in rows[("M112", "缶")].get("出す前の処理", ""), rows[("M112", "缶")].get("出す前の処理", "")))

    m113_container = rows[("M113", "容器包装類")]
    m113_nonburn = rows[("M113", "燃えないごみ")]
    checks.append(("Kitahiroshima preserves Geihoku 11-leaf taxonomy", children[m113_container["category_id"]] == 3 and children[m113_nonburn["category_id"]] == 4 and counted_category_total("M113", cats) == 11, ""))

    m114_nonburn = rows[("M114", "不燃ごみ")]
    m114_resource = rows[("M114", "資源ごみ")]
    checks.append(("Osakikamijima six top groups resolve to eight resident leaves", children[m114_nonburn["category_id"]] == 2 and children[m114_resource["category_id"]] == 2 and counted_category_total("M114", cats) == 8, ""))
    checks.append(("Osakikamijima aerosol rule retains puncture requirement", "穴を開ける" in rows[("M114", "缶類・刃物類")].get("出す前の処理", ""), rows[("M114", "缶類・刃物類")].get("出す前の処理", "")))

    m115_nonburn = rows[("M115", "不燃ごみ")]
    checks.append(("Sera nonburnable parent has five separately bagged child leaves", children[m115_nonburn["category_id"]] == 5 and counted_category_total("M115", cats) == 9, f"children={children[m115_nonburn['category_id']]}"))
    checks.append(("Sera aerosol rule explicitly no-hole after use-up", "穴を開ける必要はない" in rows[("M115", "発火性危険ごみ")].get("出す前の処理", ""), rows[("M115", "発火性危険ごみ")].get("出す前の処理", "")))

    checks.append(("coverage exactly ten x forty", len(cov) == 400 and Counter(r["municipality_id"] for r in cov) == Counter({mid: 40 for mid in TARGETS}), f"coverage={len(cov)}"))
    checks.append(("no generic/filler category detail survives", not any(is_placeholder_category_value(r.get(f, "")) for r in cats for f in CATEGORY_DETAIL_FIELDS), f"categories={len(cats)}"))
    checks.append((
        "all category evidence dates match their cited source review dates",
        all(
            r.get("確認日") == source_by_key.get((r["municipality_id"], r["source_id"]), {}).get("取得確認日")
            for r in cats
        ),
        "",
    ))

    passed = sum(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    print(f"BATCH11_RED_TEAM_SUMMARY={passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
