#!/usr/bin/env python3
"""Batch 05 adversarial checks for resident-facing category semantics."""
from __future__ import annotations

from collections import Counter

from schema_v12 import RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS={f"M{i:03d}" for i in range(44,54)}
EXPECTED_COUNTS={
    "M044":11, "M045":26, "M046":13, "M047":19, "M048":7,
    "M049":8, "M050":13, "M051":13, "M052":7, "M053":16,
}

def paths():
    b=RESEARCH/"batches"/"batch_05"; p="batch_05_"
    return {
        "municipality_path":b/f"{p}municipalities.csv", "category_path":b/f"{p}categories.csv",
        "source_path":b/f"{p}sources.csv", "qa_path":b/f"{p}qa.csv",
        "mapping_path":b/f"{p}item_mapping.csv", "coverage_path":b/f"{p}item_coverage.csv",
        "review_evidence_path":b/f"{p}category_review_evidence.csv",
    }

def main():
    p=paths(); errors,_,_=validate_dataset(label="BATCH_05",**p)
    _,munis=read_csv(p["municipality_path"]); _,cats=read_csv(p["category_path"])
    _,qa=read_csv(p["qa_path"]); _,cov=read_csv(p["coverage_path"]); _,evidence=read_csv(p["review_evidence_path"])
    by_mid={r["municipality_id"]:r for r in munis}; qa_by={r["municipality_id"]:r for r in qa}
    evidence_count=Counter(r["municipality_id"] for r in evidence)
    names={mid:{r["自治体正式名称"] for r in cats if r["municipality_id"]==mid and r.get("rule_status")=="CURRENT"} for mid in TARGETS}
    checks=[]
    checks.append(("structural validation passes",not errors,f"errors={len(errors)}"))
    checks.append(("exact MASTER target set",set(by_mid)==TARGETS,f"targets={sorted(by_mid)}"))
    checks.append(("all ten municipalities pass QA",all(qa_by[mid]["確認ステータス"]=="QA_PASSED" for mid in TARGETS),""))
    checks.append(("all ten are manual resident-facing reviews",all(by_mid[mid]["category_count_check_status"]=="MANUAL_INDEX_REVIEW" and by_mid[mid]["category_count_verified"]=="TRUE" and evidence_count[mid]>=1 for mid in TARGETS),""))
    checks.append(("reviewed leaf counts match Batch 05 design",all(counted_category_total(mid,cats)==EXPECTED_COUNTS[mid] and int(by_mid[mid]["reviewed_category_count"])==EXPECTED_COUNTS[mid] for mid in TARGETS),str({mid:counted_category_total(mid,cats) for mid in sorted(TARGETS)})))
    checks.append(("Nichinan preserves all 26 official categories",counted_category_total("M045",cats)==26 and {"可燃","不燃","不燃性粗大","缶類（資源）","ビン類（資源）","生きビン（資源）","ペットボトル（資源）","発泡スチロール（資源）","軟質プラスチック（資源）","布類（資源）","小型家電（資源）","家電4品目"}.issubset(names["M045"]),""))
    checks.append(("Hino keeps FY2026 calendar labels and separate battery route",{"可燃","不燃","資源","古紙","軟プラ","ペットボトル","布畳","廃油","蛍光管","電池","可燃粗大","不燃粗大"}.issubset(names["M046"]),""))
    checks.append(("Matsue uses seven resident leaf categories without a synthetic 資源 bucket",counted_category_total("M048",cats)==7 and "資源" not in names["M048"] and {"古紙・古着","紙製容器包装","プラスチック製容器包装","缶・びん・ペットボトル"}.issubset(names["M048"]),""))
    checks.append(("Hamada does not revive ended 古着・古布 collection","古着・古布" not in names["M049"] and counted_category_total("M049",cats)==8,""))
    checks.append(("Oda preserves resident A/B/C resource groups",{"資源物Aグループ","資源物Bグループ","資源物Cグループ"}.issubset(names["M052"]) and counted_category_total("M052",cats)==7,""))
    checks.append(("Yasugi keeps detailed paper and material leaves",{"雑紙（その他の紙類）","本（書籍）・雑誌・冊子","ダンボール","牛乳パック","新聞・新聞チラシ","板ガラス","埋立ごみ"}.issubset(names["M053"]),""))
    checks.append(("coverage is exactly ten municipalities x forty items",len(cov)==400 and Counter(r["municipality_id"] for r in cov)==Counter({mid:40 for mid in TARGETS}),f"coverage={len(cov)}"))
    checks.append(("no filler text in Batch 05 category details",not any(is_placeholder_category_value(r.get(f,"")) for r in cats for f in CATEGORY_DETAIL_FIELDS),f"categories={len(cats)}"))
    checks.append(("all stored category evidence checked 2026-08-19",all(r.get("確認日")=="2026-08-19" for r in cats),""))
    passed=sum(ok for _,ok,_ in checks)
    for name,ok,detail in checks: print(f"{'PASS' if ok else 'FAIL'} {name}"+(f": {detail}" if detail else ""))
    print(f"BATCH05_RED_TEAM_SUMMARY={passed}/{len(checks)}")
    return 0 if passed==len(checks) else 1

if __name__=="__main__": raise SystemExit(main())
