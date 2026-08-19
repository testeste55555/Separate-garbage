#!/usr/bin/env python3
"""Adversarial checks for active Batch 08 resident-facing semantics."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from schema_v12 import MASTER,RESEARCH,counted_category_total,read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS,is_placeholder_category_value,validate_dataset

TARGETS={'M074','M075','M077','M078','M079','M080','M081','M082','M083'}
EXPECTED={'M074':7,'M075':4,'M077':9,'M078':7,'M079':16,'M080':20,'M081':14,'M082':12,'M083':6}

def paths():
 b=RESEARCH/'batches'/'batch_08'; p='batch_08_'
 return {'municipality_path':b/f'{p}municipalities.csv','category_path':b/f'{p}categories.csv','source_path':b/f'{p}sources.csv','qa_path':b/f'{p}qa.csv','mapping_path':b/f'{p}item_mapping.csv','coverage_path':b/f'{p}item_coverage.csv','review_evidence_path':b/f'{p}category_review_evidence.csv'}

def main():
 p=paths(); errors,_,_=validate_dataset(label='BATCH_08',**p)
 _,munis=read_csv(p['municipality_path']); _,cats=read_csv(p['category_path']); _,qa=read_csv(p['qa_path']); _,cov=read_csv(p['coverage_path']); _,ev=read_csv(p['review_evidence_path'])
 _,deferred=read_csv(MASTER/'05_deferred_municipalities.csv')
 by={r['municipality_id']:r for r in munis}; q={r['municipality_id']:r for r in qa}; evc=Counter(r['municipality_id'] for r in ev)
 cur={(r['municipality_id'],r['自治体正式名称']):r for r in cats if r.get('rule_status')=='CURRENT'}
 names={mid:{r['自治体正式名称'] for r in cats if r['municipality_id']==mid and r.get('rule_status')=='CURRENT'} for mid in TARGETS}
 checks=[]
 checks.append(('structural validation passes',not errors,f'errors={len(errors)}'))
 checks.append(('exact active target set',set(by)==TARGETS,str(sorted(by))))
 checks.append(('deferred Bizen absent from active Batch 08',all(r.get('municipality_id')!='M076' for dataset in (munis,cats,qa,cov,ev) for r in dataset),''))
 checks.append(('Bizen is retained in deferred registry for district-variant support',any(r.get('municipality_id')=='M076' and r.get('status')=='DEFERRED' and 'variant' in r.get('reason','') for r in deferred),''))
 checks.append(('all nine active municipalities pass QA',all(q[mid]['確認ステータス']=='QA_PASSED' for mid in TARGETS),''))
 checks.append(('reviewed leaf counts match evidence',all(counted_category_total(mid,cats)==EXPECTED[mid] and (by[mid]['official_category_count']=='16' if mid=='M079' else int(by[mid]['reviewed_category_count'])==EXPECTED[mid]) and evc[mid]>=1 for mid in TARGETS),str({mid:counted_category_total(mid,cats) for mid in sorted(TARGETS)})))
 checks.append(('Takahashi exact seven and aerosol piercing preserved',{'燃やせるごみ','燃やせないごみ','びん類','かん類','ペットボトル','その他プラスチック','雑紙・紙パック・段ボール・古新聞・古雑誌'}.issubset(names['M074']) and '穴' in cur[('M074','かん類')]['出す前の処理'],''))
 checks.append(('Niimi stays four resident categories',counted_category_total('M075',cats)==4 and {'可燃ごみ','埋立ごみ','資源ごみ（再資源化物）','粗大ごみ'}==names['M075'],''))
 checks.append(('Setouchi uses post-April-2026 plastic resource','プラスチック資源' in names['M077'] and 'プラスチック製品' in cur[('M077','プラスチック資源')]['代表品目'],''))
 setouchi_prep=cur[('M077','金物類')]['出す前の処理']
 checks.append(('Setouchi current aerosol rule requires complete gas release without invented piercing','中身を完全に出し切' in setouchi_prep and '穴をあけ' not in setouchi_prep and '穴を開け' not in setouchi_prep,setouchi_prep))
 checks.append(('Setouchi current aerosol evidence uses official fire-safety page',cur[('M077','金物類')]['出典URL']=='https://www.city.setouchi.lg.jp/soshiki/14/139499.html',cur[('M077','金物類')]['出典URL']))
 checks.append(('Akaiwa current plastic resource is not omitted','プラスチック資源' in names['M078'] and '100%プラスチック製品' in cur[('M078','プラスチック資源')]['代表品目'],''))
 checks.append(('Maniwa is official-count-matched at 16',by['M079']['category_count_check_status']=='OFFICIAL_COUNT_MATCHED' and by['M079']['official_category_count']=='16' and counted_category_total('M079',cats)==16,''))
 checks.append(('Maniwa does not inflate 16 with special-route food/oil rows','生ごみ' not in names['M079'] and '廃食油' not in names['M079'],str(names['M079'])))
 checks.append(('Mimasaka keeps 20 official leaves under calendar projection parents',counted_category_total('M080',cats)==20 and all(x in names['M080'] for x in ['透明びん','茶色びん','その他色びん','生ビン（いきびん）','蛍光灯類','ガラス類','陶器類','廃天ぷら油','かん類','乾電池類','小型金属類','スプレー缶','刃物・突鋭物など','白色トレイ・発泡スチロール','プラスチック製容器包装類','紙製容器包装類','ペットボトル','古紙類']),''))
 checks.append(('Mimasaka spray cans explicitly require holes','穴' in cur[('M080','スプレー缶')]['出す前の処理'],cur[('M080','スプレー缶')]['出す前の処理']))
 checks.append(('Asakuchi preserves common 11 resource leaves and nonburnable/coarse distinction',counted_category_total('M081',cats)==14 and all(x in names['M081'] for x in ['もえるごみ','もえないごみ','不燃性粗大ごみ','缶類','びん','ペットボトル','プラスチック製容器包装','プラスチック製品','新聞紙、折り込み広告','雑誌、本、雑紙','ダンボール','紙パック','布類','乾電池']),''))
 checks.append(('Wake October product-plastic change is PLANNED not CURRENT',any(r['municipality_id']=='M082' and r['自治体正式名称']=='プラスチック資源（製品プラスチックを含む）' and r['rule_status']=='PLANNED' and r['ui_role']=='HIDDEN' and r['effective_from']=='2026-10-01' for r in cats) and 'プラスチック資源（製品プラスチックを含む）' not in names['M082'],''))
 checks.append(('Wake current leaf count excludes October plan',counted_category_total('M082',cats)==12 and 'プラスチック製容器・包装' in names['M082'],''))
 checks.append(('Wake current aerosol rule requires hole','穴' in cur[('M082','危険物等')]['出す前の処理'],cur[('M082','危険物等')]['出す前の処理']))
 checks.append(('Hayashima has six categories and no synthetic bulky bucket',counted_category_total('M083',cats)==6 and '粗大ごみ' not in names['M083'] and {'燃やせるごみ','燃やせないごみ','資源ごみ（紙類）','資源ごみ（金属類）','資源ごみ（びん・廃乾電池・蛍光管等水銀入り廃製品）','資源ごみ（布類・ペットボトル）'}==names['M083'],''))
 checks.append(('coverage exactly nine x forty',len(cov)==360 and Counter(r['municipality_id'] for r in cov)==Counter({mid:40 for mid in TARGETS}),f'coverage={len(cov)}'))
 checks.append(('no generic placeholder filler',not any(is_placeholder_category_value(r.get(f,'')) for r in cats for f in CATEGORY_DETAIL_FIELDS),f'categories={len(cats)}'))
 checks.append(('all category evidence checked 2026-08-19',all(r.get('確認日')=='2026-08-19' for r in cats),''))
 passed=sum(ok for _,ok,_ in checks)
 for name,ok,detail in checks: print(f"{'PASS' if ok else 'FAIL'} {name}"+(f': {detail}' if detail else ''))
 print(f'BATCH08_RED_TEAM_SUMMARY={passed}/{len(checks)}')
 return 0 if passed==len(checks) else 1
if __name__=='__main__': raise SystemExit(main())
