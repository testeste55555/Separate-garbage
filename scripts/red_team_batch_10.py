#!/usr/bin/env python3
"""Batch 10 adversarial checks for resident-facing category authenticity."""
from __future__ import annotations

from collections import Counter

from schema_v12 import MASTER, RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS = {"M095","M096","M097","M101","M103","M104","M105"}
EXPECTED = {"M095":7,"M096":5,"M097":10,"M101":9,"M103":12,"M104":11,"M105":10}


def paths():
    b = RESEARCH / "batches" / "batch_10"
    p = "batch_10_"
    return {
        "municipality_path": b/f"{p}municipalities.csv", "category_path": b/f"{p}categories.csv",
        "source_path": b/f"{p}sources.csv", "qa_path": b/f"{p}qa.csv",
        "mapping_path": b/f"{p}item_mapping.csv", "coverage_path": b/f"{p}item_coverage.csv",
        "review_evidence_path": b/f"{p}category_review_evidence.csv",
    }


def main() -> int:
    p = paths()
    errors, _, _ = validate_dataset(label="BATCH_10", **p)
    _, munis = read_csv(p["municipality_path"])
    _, cats = read_csv(p["category_path"])
    _, qa = read_csv(p["qa_path"])
    _, cov = read_csv(p["coverage_path"])
    _, evidence = read_csv(p["review_evidence_path"])
    _, deferred = read_csv(MASTER / "05_deferred_municipalities.csv")

    by = {r["municipality_id"]:r for r in munis}
    q = {r["municipality_id"]:r for r in qa}
    evc = Counter(r["municipality_id"] for r in evidence)
    names = {mid:{r["自治体正式名称"] for r in cats if r["municipality_id"]==mid and r.get("rule_status")=="CURRENT"} for mid in TARGETS}
    rows = {(r["municipality_id"],r["自治体正式名称"]):r for r in cats if r.get("rule_status")=="CURRENT"}
    children = Counter(r.get("parent_category_id","") for r in cats if r.get("parent_category_id"))
    deferred_by = {r["municipality_id"]:r for r in deferred}

    checks = []
    checks.append(("structural validation passes", not errors, f"errors={len(errors)}"))
    checks.append(("exact active target set excludes regional variants", set(by)==TARGETS and not ({"M098","M099","M100"}&set(by)), str(sorted(by))))
    checks.append(("all seven active municipalities QA_PASSED", all(q[mid]["確認ステータス"]=="QA_PASSED" for mid in TARGETS), ""))
    checks.append(("all official leaf counts match design", all(counted_category_total(mid,cats)==EXPECTED[mid] for mid in TARGETS), str({mid:counted_category_total(mid,cats) for mid in sorted(TARGETS)})))
    checks.append(("all active municipalities have category review evidence", all(evc[mid]>=1 for mid in TARGETS), str(evc)))
    checks.append(("only Mihara uses explicit numeric official count", by["M097"]["category_count_check_status"]=="OFFICIAL_COUNT_MATCHED" and by["M097"]["official_category_count"]=="10" and all(by[mid]["category_count_check_status"]=="MANUAL_INDEX_REVIEW" and not by[mid]["official_category_count"] for mid in TARGETS-{"M097"}), ""))

    for mid, token in [("M098","地域"),("M099","内海町"),("M100","上下地区")]:
        checks.append((f"{mid} deferred for regional CORE variants", deferred_by.get(mid,{}).get("status")=="DEFERRED" and deferred_by[mid].get("decision_source")=="SCHEMA_SCOPE_LIMITATION" and token in deferred_by[mid].get("reason",""), deferred_by.get(mid,{}).get("reason","")))

    checks.append(("Kure keeps seven FY2026 collection labels and new plastic resource", names["M095"]=={"燃えるごみ","燃えないごみ","粗大ごみ","プラスチック資源","資源物（びん類・缶類・ペットボトル）","資源物（紙類）","有害・危険ごみ"}, str(names["M095"])))
    checks.append(("Kure does not misclaim explicit official total", by["M095"]["category_count_check_status"]=="MANUAL_INDEX_REVIEW" and by["M095"]["reviewed_category_count"]=="7", ""))

    takehara = rows[("M096","リサイクルする物")]
    checks.append(("Takehara remains exactly five resident categories", names["M096"]=={"もやせる物","リサイクルする物","資源物","粗大ごみ","有害ごみ"}, str(names["M096"])))
    checks.append(("Takehara spray cans retain no-hole rule", "穴を開ける必要はない" in takehara.get("出す前の処理",""), takehara.get("出す前の処理","")))
    checks.append(("Takehara hazardous captures rechargeable nonremovable devices", "充電池を外せない小型家電" in rows[("M096","有害ごみ")].get("代表品目",""), rows[("M096","有害ごみ")].get("代表品目","")))

    mihara_hazard = {"発火性危険ごみ","電池","電池の外せない小型家電・充電式小型家電","蛍光灯（有害ごみ）"}
    checks.append(("Mihara explicit ten divisions preserved", counted_category_total("M097",cats)==10 and mihara_hazard.issubset(names["M097"]), str(names["M097"])))
    checks.append(("Mihara aerosol current rule explicitly no-hole", "穴を開ける必要はない" in rows[("M097","発火性危険ごみ")].get("出す前の処理",""), rows[("M097","発火性危険ごみ")].get("出す前の処理","")))

    checks.append(("Miyoshi keeps exactly nine regular collection categories", names["M101"]=={"燃やせるごみ","プラスチック資源","紙資源","資源物","布資源","燃やせないごみ","粗大ごみ","埋立ごみ","有害ごみ"}, str(names["M101"])))
    checks.append(("Miyoshi does not promote dropoff/reuse routes to batch leaves", not ({"リユース本","小型家電","収集も処理もできないごみ"}&names["M101"]), ""))

    otake_station = {"もやすごみ","プラスチックごみ","紙資源","カン","ビン","ペットボトル","衣類・毛布類","もやさないごみ"}
    otake_special = {"粗大ごみ","有害ごみ","電池類","せん定枝"}
    checks.append(("Otake preserves eight station plus four special official routes", names["M103"]==otake_station|otake_special and counted_category_total("M103",cats)==12, str(names["M103"])))
    checks.append(("Otake spray cans use-up rule does not invent hole requirement", "使い切" in rows[("M103","カン")].get("出す前の処理","") and "穴" not in rows[("M103","カン")].get("出す前の処理",""), rows[("M103","カン")].get("出す前の処理","")))

    checks.append(("Higashihiroshima preserves eleven resident categories", counted_category_total("M104",cats)==11 and {"リサイクルプラ","その他プラ","危険ごみ","有害ごみ","新聞","雑誌・雑がみ・ダンボール","燃やせる粗大ごみ","燃やせない粗大ごみ"}.issubset(names["M104"]), str(names["M104"])))
    checks.append(("Higashihiroshima plastic streams stay semantically distinct", "プラマーク" in rows[("M104","リサイクルプラ")].get("代表品目","") and "プラマークのない" in rows[("M104","その他プラ")].get("代表品目",""), ""))

    hatsu_parent = rows[("M105","資源ごみ")]
    checks.append(("Hatsukaichi resource parent has five official child leaves", children[hatsu_parent.get("category_id","")]==5 and counted_category_total("M105",cats)==10, f"children={children[hatsu_parent.get('category_id','')]}"))
    checks.append(("Hatsukaichi spray cans retain explicit no-hole rule", "穴を開ける必要はない" in rows[("M105","資源ごみ(1) びん・かん類")].get("出す前の処理",""), rows[("M105","資源ごみ(1) びん・かん類")].get("出す前の処理","")))
    checks.append(("Hatsukaichi PET caps and labels go to burnable", "ふた・ラベルは燃やせるごみ" in rows[("M105","資源ごみ(2) ペットボトルなどプラスチック製の容器（限定7品目）")].get("出す前の処理",""), ""))

    checks.append(("coverage exactly seven x forty", len(cov)==280 and Counter(r["municipality_id"] for r in cov)==Counter({mid:40 for mid in TARGETS}), f"coverage={len(cov)}"))
    checks.append(("no generic/filler category detail survives", not any(is_placeholder_category_value(r.get(f,"")) for r in cats for f in CATEGORY_DETAIL_FIELDS), f"categories={len(cats)}"))
    checks.append(("all category evidence uses research date", all(r.get("確認日")=="2026-08-19" for r in cats), ""))

    passed=sum(ok for _,ok,_ in checks)
    for name,ok,detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}"+(f": {detail}" if detail else ""))
    print(f"BATCH10_RED_TEAM_SUMMARY={passed}/{len(checks)}")
    return 0 if passed==len(checks) else 1

if __name__=="__main__":
    raise SystemExit(main())
