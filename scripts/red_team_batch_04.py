#!/usr/bin/env python3
"""Batch 04 adversarial checks for resident-facing category semantics."""
from __future__ import annotations

from collections import Counter

from schema_v12 import RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS = {f"M{i:03d}" for i in range(34, 44)}

def paths():
    base = RESEARCH / "batches" / "batch_04"; p = "batch_04_"
    return {"municipality_path":base/f"{p}municipalities.csv","category_path":base/f"{p}categories.csv","source_path":base/f"{p}sources.csv","qa_path":base/f"{p}qa.csv","mapping_path":base/f"{p}item_mapping.csv","coverage_path":base/f"{p}item_coverage.csv","review_evidence_path":base/f"{p}category_review_evidence.csv"}

def main():
    p=paths(); errors,_,_=validate_dataset(label="BATCH_04",**p)
    _,munis=read_csv(p["municipality_path"]); _,cats=read_csv(p["category_path"]); _,qa=read_csv(p["qa_path"]); _,ev=read_csv(p["review_evidence_path"])
    by_mid={r["municipality_id"]:r for r in munis}; q={r["municipality_id"]:r for r in qa}; ec=Counter(r["municipality_id"] for r in ev)
    names={mid:{r["自治体正式名称"] for r in cats if r["municipality_id"]==mid} for mid in TARGETS}
    checks=[]
    checks.append(("structural validation passes",not errors,f"errors={len(errors)}"))
    checks.append(("exact M034-M043 target set",set(by_mid)==TARGETS,str(sorted(by_mid))))
    checks.append(("all ten category reviews are evidence-backed QA_PASSED",all(by_mid[mid]["category_count_check_status"]=="MANUAL_INDEX_REVIEW" and by_mid[mid]["category_count_verified"]=="TRUE" and q[mid]["確認ステータス"]=="QA_PASSED" and ec[mid]>=1 and int(by_mid[mid]["reviewed_category_count"])==counted_category_total(mid,cats) for mid in TARGETS),""))
    checks.append(("no filler category text",not any(is_placeholder_category_value(r.get(f,"")) for r in cats for f in CATEGORY_DETAIL_FIELDS),f"categories={len(cats)}"))
    checks.append(("all category evidence dated current research pass",all(r.get("確認日")=="2026-08-19" for r in cats),""))
    checks.append(("East Tottori towns keep hazardous and battery resident buckets",all({"乾電池類","有害ごみ"} <= names[mid] for mid in {"M034","M035","M036"}),""))
    checks.append(("Misasa keeps 2026 resident schedule labels",{"可燃ごみ","不燃ごみ","小型家電","有害ごみ","可燃性粗大ごみ","不燃性粗大ごみ","ペットボトル","びん類","アルミ缶","スチール缶・スプレー缶","資源ごみ"} <= names["M037"],""))
    checks.append(("Yurihama has exact twelve resident leaf categories",counted_category_total("M038",cats)==12,""))
    checks.append(("Kotoura has exact thirteen resident leaf categories",counted_category_total("M039",cats)==13,""))
    checks.append(("Hokuei has twelve current categories including hazardous",counted_category_total("M040",cats)==12 and "有害ごみ" in names["M040"],""))
    checks.append(("Hiezu uses current seven collection labels",{"もえるゴミ","もえないゴミ","布・プラスチック類（資源ゴミ）","発泡スチロール（資源ゴミ）","その他資源ゴミ","蛍光灯","乾電池"} <= names["M041"] and counted_category_total("M041",cats)==7,""))
    checks.append(("Daisen removed April 2026 abolished categories","紙製容器包装" not in names["M042"] and "指定びん（生きびん）" not in names["M042"] and {"古紙類","缶・びん","発泡スチロール"} <= names["M042"],""))
    checks.append(("Daisen preserves current white-only foam fallback",any(r["municipality_id"]=="M042" and r["自治体正式名称"]=="発泡スチロール" and "白色以外" in r["条件外の扱い"] for r in cats),""))
    checks.append(("Nanbu keeps resident-facing resource leaves",{"古紙類","小雑紙","ビン・缶類","再利用ビン","軟質プラスチック類","ペットボトル","電池","蛍光管","木質類","布類"} <= names["M043"],""))
    passed=sum(ok for _,ok,_ in checks)
    for name,ok,detail in checks: print(f"{'PASS' if ok else 'FAIL'} {name}"+(f": {detail}" if detail else ""))
    print(f"BATCH04_RED_TEAM_SUMMARY={passed}/{len(checks)}")
    return 0 if passed==len(checks) else 1

if __name__=="__main__": raise SystemExit(main())
