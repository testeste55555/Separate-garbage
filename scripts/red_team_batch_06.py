#!/usr/bin/env python3
"""Batch 06 adversarial checks for current resident-facing category semantics."""
from __future__ import annotations

from collections import Counter

from schema_v12 import RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS={f"M{i:03d}" for i in range(54,64)}
EXPECTED_COUNTS={
    "M054":12,"M055":11,"M056":10,"M057":11,"M058":13,
    "M059":13,"M060":13,"M061":8,"M062":8,"M063":7,
}

def paths():
    b=RESEARCH/"batches"/"batch_06"; p="batch_06_"
    return {
        "municipality_path":b/f"{p}municipalities.csv", "category_path":b/f"{p}categories.csv",
        "source_path":b/f"{p}sources.csv", "qa_path":b/f"{p}qa.csv",
        "mapping_path":b/f"{p}item_mapping.csv", "coverage_path":b/f"{p}item_coverage.csv",
        "review_evidence_path":b/f"{p}category_review_evidence.csv",
    }

def main():
    p=paths(); errors,_,_=validate_dataset(label="BATCH_06",**p)
    _,munis=read_csv(p["municipality_path"]); _,cats=read_csv(p["category_path"])
    _,qa=read_csv(p["qa_path"]); _,cov=read_csv(p["coverage_path"]); _,evidence=read_csv(p["review_evidence_path"])
    by_mid={r["municipality_id"]:r for r in munis}; qa_by={r["municipality_id"]:r for r in qa}
    evidence_count=Counter(r["municipality_id"] for r in evidence)
    by_key={(r["municipality_id"],r["自治体正式名称"]):r for r in cats}
    names={mid:{r["自治体正式名称"] for r in cats if r["municipality_id"]==mid and r.get("rule_status")=="CURRENT"} for mid in TARGETS}
    children=Counter(r.get("parent_category_id","") for r in cats if r.get("parent_category_id"))
    checks=[]
    checks.append(("structural validation passes",not errors,f"errors={len(errors)}"))
    checks.append(("exact MASTER target set",set(by_mid)==TARGETS,f"targets={sorted(by_mid)}"))
    checks.append(("all ten municipalities pass QA",all(qa_by[mid]["確認ステータス"]=="QA_PASSED" for mid in TARGETS),""))
    checks.append(("all ten are manual resident-facing reviews",all(by_mid[mid]["category_count_check_status"]=="MANUAL_INDEX_REVIEW" and by_mid[mid]["category_count_verified"]=="TRUE" and evidence_count[mid]>=1 for mid in TARGETS),""))
    checks.append(("reviewed leaf counts match Batch 06 design",all(counted_category_total(mid,cats)==EXPECTED_COUNTS[mid] and int(by_mid[mid]["reviewed_category_count"])==EXPECTED_COUNTS[mid] for mid in TARGETS),str({mid:counted_category_total(mid,cats) for mid in sorted(TARGETS)})))
    checks.append(("Gotsu preserves five non-resource labels and seven resource leaves",{"金物類（粗大ごみを含む）","有害ごみ（粗大ごみを含む）","ガラス・陶器類（粗大ごみを含む）","燃やせるごみ","燃やせる粗大ごみ","ビン類","缶類","容器包装プラスチック類","ペットボトル","発泡スチロール","白色トレイ","紙類"}.issubset(names["M054"]),""))
    checks.append(("Unnan stores both official regional-system evidence",evidence_count["M055"]>=4 and {"有害ごみ1","有害ごみ2","灰類","資源ごみ（ビン・カン）","資源ごみ（古紙）"}.issubset(names["M055"]),""))
    checks.append(("Okuizumo preserves pierce-before-empty-can rule","穴を開け" in by_key[("M056","空き缶")]["出す前の処理"] and "中身を使い切" in by_key[("M056","空き缶")]["出す前の処理"],""))
    checks.append(("Iinan uses official linked joint-authority resident system",{"有害ごみ1","有害ごみ2","灰類","粗大ごみ（直接持込み）"}.issubset(names["M057"]) and evidence_count["M057"]>=3,""))
    checks.append(("Ochi three towns preserve official 13-leaf paper hierarchy",all(counted_category_total(mid,cats)==13 and "古紙類・紙パック" in names[mid] and all(n in names[mid] for n in ["新聞紙・折込広告","広告・雑誌・書籍","段ボール","紙パック"]) for mid in ["M058","M059","M060"]),""))
    checks.append(("Kawamoto, Misato and Ohnan retain municipality-specific aerosol piercing",all("穴を開け" in by_key[(mid,"不燃ごみ")]["出す前の処理"] for mid in ["M058","M059","M060"]),""))
    checks.append(("Tsuwano keeps eight resident calendar labels",{"もやせるごみ","容器包装プラスチック","商品プラスチック","びん・ガラス・陶器類","缶類","有害ごみ","粗大ごみ","資源ごみ"}.issubset(names["M061"]) and counted_category_total("M061",cats)==8,""))
    checks.append(("Yoshika current change sends lighters to hazardous", "ライター" in by_key[("M062","有害ごみ")]["代表品目"] and "ライター" in by_key[("M062","有害ごみ")]["出す前の処理"],""))
    checks.append(("Yoshika explicitly keeps spray cans no-hole", "穴はあけなくてよい" in by_key[("M062","カン類")]["出す前の処理"],""))
    checks.append(("Ama preserves exactly seven combined current labels",counted_category_total("M063",cats)==7 and {"可燃物","ペットボトル","びん・ガラス/陶器","蛍光灯/水銀","廃食用油","缶・金物","粗大・乾電池"}.issubset(names["M063"]),""))
    checks.append(("Ochi paper parents have four child leaves",all(children[by_key[(mid,"古紙類・紙パック")]["category_id"]]==4 for mid in ["M058","M059","M060"]),""))
    checks.append(("coverage is exactly ten municipalities x forty items",len(cov)==400 and Counter(r["municipality_id"] for r in cov)==Counter({mid:40 for mid in TARGETS}),f"coverage={len(cov)}"))
    checks.append(("no filler text in Batch 06 category details",not any(is_placeholder_category_value(r.get(f,"")) for r in cats for f in CATEGORY_DETAIL_FIELDS),f"categories={len(cats)}"))
    checks.append(("all stored category evidence checked 2026-08-19",all(r.get("確認日")=="2026-08-19" for r in cats),""))
    checks.append(("Tsuwano optional multilingual state is not falsely asserted",by_mid["M061"]["multilingual_check_status"]=="NOT_CHECKED" and not by_mid["M061"]["多言語資料URL"],""))
    checks.append(("Yoshika official multilingual material is recorded",by_mid["M062"]["multilingual_check_status"]=="CHECKED_PRESENT" and bool(by_mid["M062"]["多言語資料URL"]),""))
    passed=sum(ok for _,ok,_ in checks)
    for name,ok,detail in checks: print(f"{'PASS' if ok else 'FAIL'} {name}"+(f": {detail}" if detail else ""))
    print(f"BATCH06_RED_TEAM_SUMMARY={passed}/{len(checks)}")
    return 0 if passed==len(checks) else 1

if __name__=="__main__": raise SystemExit(main())

# Temporary no-op trigger for Batch 07 pipeline diagnostics; remove after probe.
