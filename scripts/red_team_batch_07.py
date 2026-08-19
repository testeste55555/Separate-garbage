#!/usr/bin/env python3
from __future__ import annotations
from collections import Counter
from schema_v12 import RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS={f'M{i:03d}' for i in range(64,74)}
PASS={'M064','M067','M068','M070','M073'}
HOLD=TARGETS-PASS
EXPECTED={'M064':7,'M067':6,'M068':5,'M070':9,'M073':4}

def paths():
 b=RESEARCH/'batches'/'batch_07'; p='batch_07_'
 return {'municipality_path':b/f'{p}municipalities.csv','category_path':b/f'{p}categories.csv','source_path':b/f'{p}sources.csv','qa_path':b/f'{p}qa.csv','mapping_path':b/f'{p}item_mapping.csv','coverage_path':b/f'{p}item_coverage.csv','review_evidence_path':b/f'{p}category_review_evidence.csv'}

def main():
 p=paths(); errors,_,_=validate_dataset(label='BATCH_07',**p)
 _,munis=read_csv(p['municipality_path']); _,cats=read_csv(p['category_path']); _,qa=read_csv(p['qa_path']); _,cov=read_csv(p['coverage_path']); _,ev=read_csv(p['review_evidence_path'])
 by={r['municipality_id']:r for r in munis}; q={r['municipality_id']:r for r in qa}; evc=Counter(r['municipality_id'] for r in ev)
 names={mid:{r['自治体正式名称'] for r in cats if r['municipality_id']==mid and r.get('rule_status')=='CURRENT'} for mid in TARGETS}
 checks=[]
 checks.append(('structural validation passes',not errors,f'errors={len(errors)}'))
 checks.append(('exact target set',set(by)==TARGETS,str(sorted(by))))
 checks.append(('five researched municipalities QA_PASSED',all(q[mid]['確認ステータス']=='QA_PASSED' for mid in PASS),''))
 checks.append(('five unresolved municipalities remain QA_REQUIRED',all(q[mid]['確認ステータス']=='QA_REQUIRED' for mid in HOLD),str({mid:q[mid]['確認ステータス'] for mid in sorted(HOLD)})))
 checks.append(('unresolved municipalities stay NOT_REVIEWED',all(by[mid]['category_count_check_status']=='NOT_REVIEWED' and by[mid]['category_count_verified']=='FALSE' for mid in HOLD),''))
 checks.append(('reviewed counts match evidence-backed design',all(counted_category_total(mid,cats)==EXPECTED[mid] and int(by[mid]['reviewed_category_count'])==EXPECTED[mid] and evc[mid]>=1 for mid in PASS),str({mid:counted_category_total(mid,cats) for mid in sorted(PASS)})))
 checks.append(('Nishinoshima keeps seven resident leaves',{'燃えるごみ','埋立ごみ','資源ごみ：缶類','資源ごみ：びん類','資源ごみ：ペットボトル類','資源ごみ：新聞紙・折込チラシ','使用済蛍光管、電池、ペットボトルのキャップ'}.issubset(names['M064']),''))
 checks.append(('Okayama includes post-2024 plastic resource',{'可燃ごみ','不燃ごみ','プラスチック資源','資源化物','廃乾電池・体温計','粗大ごみ'}.issubset(names['M067']),''))
 checks.append(('Kurashiki does not split 雑がみ into synthetic bucket','資源ごみ（雑がみ）' not in names['M068'] and {'燃やせるごみ','資源ごみ','埋立ごみ','使用済み乾電池','粗大ごみ'}.issubset(names['M068']),''))
 checks.append(('Tamano preserves A/B and six other current resident streams',{'燃やせるごみ','不燃物A','不燃物B','古紙類','その他プラスチック製容器包装','ペットボトル・びん類','缶類・危険性の物','古布・廃食用油','粗大ごみ'}.issubset(names['M070']),''))
 checks.append(('Soja stays at four resident categories',counted_category_total('M073',cats)==4 and {'燃やせるごみ','燃やせないごみ','資源ごみ','不燃性粗大ごみ'}==names['M073'],''))
 checks.append(('no speculative categories for unresolved municipalities',all(not names[mid] for mid in HOLD),str({mid:len(names[mid]) for mid in sorted(HOLD)})))
 checks.append(('coverage exactly ten x forty',len(cov)==400 and Counter(r['municipality_id'] for r in cov)==Counter({mid:40 for mid in TARGETS}),f'coverage={len(cov)}'))
 checks.append(('no filler text',not any(is_placeholder_category_value(r.get(f,'')) for r in cats for f in CATEGORY_DETAIL_FIELDS),f'categories={len(cats)}'))
 passed=sum(ok for _,ok,_ in checks)
 for name,ok,detail in checks: print(f"{'PASS' if ok else 'FAIL'} {name}"+(f': {detail}' if detail else ''))
 print(f'BATCH07_RED_TEAM_SUMMARY={passed}/{len(checks)}')
 return 0 if passed==len(checks) else 1
if __name__=='__main__': raise SystemExit(main())
