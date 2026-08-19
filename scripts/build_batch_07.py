#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from urllib.parse import urlparse
from schema_v12 import (CATEGORY_FIELDS,CATEGORY_REVIEW_EVIDENCE_FIELDS,COVERAGE_FIELDS,MAPPING_FIELDS,MASTER,MUNICIPALITY_FIELDS,QA_FIELDS,SOURCE_FIELDS,migrate_batch_dir,read_csv,write_csv)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'research'/'batches'/'batch_07'
CHECKED='2026-08-19'; REVIEWER='OPENAI_CHATGPT_BATCH07_REVIEW'; NOT_STATED='NOT_STATED_IN_CITED_SOURCE'
TARGETS={f'M{i:03d}' for i in range(64,74)}
PASS_TARGETS={'M064','M067','M068','M070','M073'}
REGISTRY_FIELDS=['municipality_id','host','authority_type','authority_name','verification_url','verified_date','notes']

municipality_specs={
'M064':dict(pref='島根県',city='西ノ島町',processor='西ノ島町',top='https://www.town.nishinoshima.shimane.jp/bunya/b_sumai/b_gomi/833',guide='https://www.town.nishinoshima.shimane.jp/bunya/b_sumai/b_gomi/833',current='https://www.town.nishinoshima.shimane.jp/files/original/202601221430235172519a52c.pdf',note='現行住民向けWebと令和8年度収集運搬仕様で分別体系の現行性を確認。'),
'M065':dict(pref='島根県',city='知夫村',processor='知夫村',top='https://www.chibu.jp/',guide='',current='',note='公式サイト検索障害のため全分別区分の網羅性未確認。推測せずNOT_REVIEWED。'),
'M066':dict(pref='島根県',city='隠岐の島町',processor='隠岐の島町',top='https://www.town.okinoshima.shimane.jp/kurashi/gomi-kankyo/katei_gomi/2/5013.html',guide='https://www.town.okinoshima.shimane.jp/kurashi/gomi-kankyo/katei_gomi/2/5013.html',current='https://www.town.okinoshima.shimane.jp/soshiki/kankyo/gyomu/1/1/1/242.html',note='令和8年度カレンダーとガイドブック導線は確認済みだが、検索障害でガイドブック全区分の網羅性確認未完了。'),
'M067':dict(pref='岡山県',city='岡山市',processor='岡山市',top='https://www.city.okayama.jp/kurashi/category/1-12-7-10-0-0-0-0-0-0.html',guide='https://www.city.okayama.jp/kurashi/category/1-12-7-10-7-0-0-0-0-0.html',current='https://www.city.okayama.jp/kurashi/0000053082.html',note='令和6年3月開始のプラスチック資源を反映し、現行6住民区分を保持。'),
'M068':dict(pref='岡山県',city='倉敷市',processor='倉敷市',top='https://www.city.kurashiki.okayama.jp/kurashi/kankyo/1003645/1013690/index.html',guide='https://www.city.kurashiki.okayama.jp/kurashi/kankyo/1003645/1013690/1012155.html',current='https://www.city.kurashiki.okayama.jp/kurashi/kankyo/1003645/1013690/index.html',note='ごみステーション4区分と粗大ごみを住民向け体系として採用。雑がみは資源ごみの内部条件で独立箱化しない。'),
'M069':dict(pref='岡山県',city='津山市',processor='津山市',top='https://www.city.tsuyama.lg.jp/',guide='',current='',note='公式サイト検索障害のため全分別区分の網羅性未確認。推測せずNOT_REVIEWED。'),
'M070':dict(pref='岡山県',city='玉野市',processor='玉野市',top='https://www.city.tamano.lg.jp/site/recycle/1630.html',guide='https://www.city.tamano.lg.jp/site/recycle/1630.html',current='https://www.city.tamano.lg.jp/site/recycle/1630.html',note='令和8年度カレンダーと現行分別辞典の住民向け8収集系統を採用。'),
'M071':dict(pref='岡山県',city='笠岡市',processor='笠岡市',top='https://www.city.kasaoka.okayama.jp/',guide='',current='',note='公式サイト検索障害のため全分別区分の網羅性未確認。推測せずNOT_REVIEWED。'),
'M072':dict(pref='岡山県',city='井原市',processor='井原市／井笠広域里庄清掃工場',top='https://www.city.ibara.okayama.jp/life/1/6/35/',guide='https://www.city.ibara.okayama.jp/soshiki/13/13158.html',current='https://www.city.ibara.okayama.jp/soshiki/13/19195.html',note='令和8年度カレンダー・現行ガイド・製品プラ変更導線は確認済みだが、全区分の網羅性を検索障害下で確証できずNOT_REVIEWED。'),
'M073':dict(pref='岡山県',city='総社市',processor='総社市',top='https://www.city.soja.okayama.jp/soshiki/34/4198.html',guide='https://www.city.soja.okayama.jp/soshiki/34/4198.html',current='https://www.city.soja.okayama.jp/soshiki/34/4198.html',note='現行公式ページが示す燃やせる・燃やせない・資源・不燃性粗大の4住民区分を採用。'),
}
source_specs={
'M064':[('家庭ごみの分別と正しい出し方','自治体公式Webページ',municipality_specs['M064']['guide'],'現行','燃える・埋立・資源各区分、前処理、収集不可'),('令和8年度西ノ島町ごみ収集運搬業務委託仕様書','自治体公式PDF',municipality_specs['M064']['current'],'2026-01','令和8年度も同じ収集区分が稼働することの現行性証拠')],
'M065':[('知夫村公式サイト','自治体公式Webページ',municipality_specs['M065']['top'],'現行','公式主体確認のみ。分別区分網羅性は未確認')],
'M066':[('ごみの分け方・出し方について','自治体公式Webページ',municipality_specs['M066']['guide'],'2026-03-02','現行ガイドブックへの公式導線'),('令和8年度ごみ分別収集カレンダー','自治体公式Webページ',municipality_specs['M066']['current'],'2026-03-02','令和8年度現行運用確認')],
'M067':[('家庭ごみに関すること','自治体公式Webページ',municipality_specs['M067']['top'],'現行','家庭ごみ各区分への公式索引'),('ごみの出し方','自治体公式Webページ',municipality_specs['M067']['guide'],'現行','可燃・不燃・プラスチック資源・粗大ごみ等'),('可燃ごみの出し方（令和6年3月から）','自治体公式Webページ',municipality_specs['M067']['current'],'2024-11-18','プラスチック資源分別開始後の現行体系'),('ごみの収集など（自動翻訳・音声読み上げ向け抜粋版）','自治体公式Webページ','https://www.city.okayama.jp/kurashi/0000028002.html','2024-08-19','資源化物・廃乾電池体温計・粗大ごみの住民区分')],
'M068':[('家庭ごみの出し方','自治体公式Webページ',municipality_specs['M068']['top'],'現行','ステーションの燃やせる・資源・埋立・使用済乾電池'),('ごみ分別検索','自治体公式Webページ',municipality_specs['M068']['guide'],'2026-04-01','現行分別区分と品目条件')],
'M069':[('津山市公式サイト','自治体公式Webページ',municipality_specs['M069']['top'],'現行','公式主体確認のみ。分別区分網羅性は未確認')],
'M070':[('令和8年度ごみカレンダーと玉野市ごみ分別辞典','自治体公式Webページ',municipality_specs['M070']['guide'],'2026-06-04','令和8年度現行運用と分別辞典区分')],
'M071':[('笠岡市公式サイト','自治体公式Webページ',municipality_specs['M071']['top'],'現行','公式主体確認のみ。分別区分網羅性は未確認')],
'M072':[('ごみ・リサイクル','自治体公式Webページ',municipality_specs['M072']['top'],'現行','現行ごみ情報索引'),('ごみの正しい分け方・出し方ガイド','自治体公式Webページ',municipality_specs['M072']['guide'],'2026-01-22','現行ガイドへの公式導線'),('令和8年度上半期ごみ収集カレンダー','自治体公式Webページ',municipality_specs['M072']['current'],'2026-03-02','令和8年度現行運用確認')],
'M073':[('ごみの収集日・正しい出し方','自治体公式Webページ',municipality_specs['M073']['guide'],'2025-11-25','燃やせる・燃やせない・資源・不燃性粗大の4区分')],
}

categories=[]
def add(mid,name,rep,*,source=1,locator='分別区分',ui='SORT_BUCKET',level='PRIMARY',channel='CURBSIDE',forbidden=NOT_STATED,fallback=NOT_STATED,prep=NOT_STATED,bag='',size='',bulky='FALSE',excluded='FALSE',note=''):
 categories.append({'municipality_id':mid,'自治体正式名称':name,'category_group':name,'parent_name':'','classification_level':level,'collection_channel':channel,'代表品目':rep,'入れてはいけない物':forbidden,'適用条件':'','条件外の扱い':fallback,'出す前の処理':prep,'袋・容器のルール':bag,'サイズ・条件':size,'粗大ごみ扱いか':bulky,'予約が必要か':'FALSE','有料か':'FALSE','料金ルール':'','自治体収集外か':excluded,'注意事項':note,'source_index':str(source),'出典ページ・該当箇所':locator,'ui_role':ui})
def excluded(mid,name,rep,*,source=1,locator='収集できないもの'):
 add(mid,name,rep,source=source,locator=locator,ui='EXCLUDED_NOTICE',level='EXCLUDED',channel='NOT_COLLECTED',excluded='TRUE',fallback='販売店・メーカー・専門業者等の公式案内に従う',prep='受入先の指示に従う')

add('M064','燃えるごみ','生ごみ・紙くず・衣類布類・木くず等',locator='家庭ごみの分別／燃えるごみ',prep='生ごみは水切り。木くず等の金属は外す',bag='黄色指定ごみ袋')
add('M064','埋立ごみ','金属類・ガラス類・陶磁器類・強化プラスチック等',locator='家庭ごみの分別／埋立ごみ',prep='鋭利物は新聞紙等で包む',bag='青色指定ごみ袋')
add('M064','資源ごみ：缶類','飲食用スチール缶・アルミ缶',locator='家庭ごみの分別／資源ごみ：缶類',prep='中身を空にして水洗い')
add('M064','資源ごみ：びん類','飲食用びん',locator='家庭ごみの分別／資源ごみ：びん類',prep='水洗いしキャップを外し、無色・茶色・その他に分ける')
add('M064','資源ごみ：ペットボトル類','PETマークのボトル',locator='家庭ごみの分別／資源ごみ：ペットボトル類',prep='水洗いしラベルとキャップを外す')
add('M064','資源ごみ：新聞紙・折込チラシ','新聞紙・折込チラシ',locator='家庭ごみの分別／新聞紙・折込チラシ',prep='2つ折り又は4つ折りでひも結束。濡らさない')
add('M064','使用済蛍光管、電池、ペットボトルのキャップ','蛍光管・電球・乾電池・PETキャップ',locator='家庭ごみの分別／使用済蛍光管、電池、ペットボトルのキャップ',prep='電池は必要に応じ絶縁。専用容器へ')
excluded('M064','町が収集及び直接搬入の受付をしないごみ','家電リサイクル対象・処理困難物等',locator='町が収集及び直接搬入の受付をしないごみ')

add('M067','可燃ごみ','生ごみ・ゴム革製品・紙おむつ等',source=3,locator='可燃ごみの出し方',prep='生ごみは十分水切り',bag='岡山市有料指定袋')
add('M067','不燃ごみ','ガラスくず・陶磁器類等',source=4,locator='家庭ごみの出し方／不燃ごみ')
add('M067','プラスチック資源','プラスチック製品・容器包装',source=3,locator='令和6年3月からプラスチック資源分別開始',prep='市のプラスチック資源ルールに従う')
add('M067','資源化物','空き缶・びん・古紙・古布・PET・天ぷら油等',source=4,locator='家庭ごみの出し方／資源化物',prep='品目ごとの市指定方法で分別')
add('M067','廃乾電池・体温計','乾電池・ボタン電池・充電式電池・水銀体温計等',source=4,locator='家庭ごみの出し方／廃乾電池・体温計',prep='市の専用コンテナ等へ')
add('M067','粗大ごみ','20L有料指定袋に入りきらない家具・自転車・家電等',source=4,locator='家庭ごみの出し方／粗大ごみ',ui='REFERENCE_ONLY',channel='BOOKED_PICKUP',bulky='TRUE',size='1個の大きさが20L有料指定袋に入りきらないもの')
excluded('M067','市で収集できないもの','タイヤ・ドラム缶・ピアノ・バッテリー等',source=4,locator='粗大ごみ／収集又は持込みできないもの')

add('M068','燃やせるごみ','生ごみ・可燃性家庭ごみ',locator='家庭ごみの出し方／燃やせるごみ',prep='大きさ基準に従う')
add('M068','資源ごみ','缶・びん・古紙・古布・金属類等',source=2,locator='ごみ分別検索／資源ごみ',prep='品目ごとの条件に従う')
add('M068','埋立ごみ','陶磁器・耐熱ガラス等',source=2,locator='ごみ分別検索／埋立ごみ',size='18L缶より小さいものを基本')
add('M068','使用済み乾電池','使用済み乾電池',locator='家庭ごみの出し方／使用済み乾電池',prep='市指定方法で排出')
add('M068','粗大ごみ','大型家具・複合製品等',source=2,locator='ごみ分別検索／粗大ごみ',ui='REFERENCE_ONLY',channel='BOOKED_PICKUP',bulky='TRUE')
excluded('M068','出せない','タイヤ・注射針・処理困難物等',source=2,locator='ごみ分別検索／出せない')

add('M070','燃やせるごみ','生ごみ・可燃性家庭ごみ',locator='玉野市ごみ分別辞典／燃やせるごみ',bag='市指定袋')
add('M070','不燃物A','市が不燃物Aとして指定する家庭ごみ',locator='玉野市ごみ分別辞典／燃やせないごみ（不燃物A・B）')
add('M070','不燃物B','市が不燃物Bとして指定する家庭ごみ',locator='玉野市ごみ分別辞典／燃やせないごみ（不燃物A・B）')
add('M070','古紙類','新聞・雑誌・段ボール・紙パック等',locator='玉野市ごみ分別辞典／古紙類',prep='種類別に市指定方法でまとめる')
add('M070','その他プラスチック製容器包装','プラマークの容器包装',locator='玉野市ごみ分別辞典／その他プラスチック製容器包装',prep='中身・汚れを除く')
add('M070','ペットボトル・びん類','PETボトル・飲食用びん',locator='玉野市ごみ分別辞典／ペットボトル・びん類',prep='市の指定方法で分別')
add('M070','缶類・危険性の物','飲食用缶・スプレー缶等',locator='玉野市ごみ分別辞典／缶類・危険性の物',prep='中身を使い切り市指定方法で出す')
add('M070','古布・廃食用油','古布・家庭の廃食用油',locator='玉野市ごみ分別辞典／古布・廃食用油',prep='市の指定方法で出す')
add('M070','粗大ごみ','市指定の大型家庭ごみ',locator='玉野市ごみ分別辞典／粗大ごみ',ui='REFERENCE_ONLY',channel='BOOKED_PICKUP',bulky='TRUE')
excluded('M070','市が取り扱わないもの','処理困難物等',locator='玉野市ごみ分別辞典／市が取り扱わないもの')

add('M073','燃やせるごみ','生ごみ・紙おむつ・紙くず・ゴム革・プラスチック製品等',locator='ごみの収集日・正しい出し方／燃やせるごみ',prep='市指定方法に従う')
add('M073','燃やせないごみ','家庭の不燃ごみ',locator='ごみの収集日・正しい出し方／燃やせないごみ')
add('M073','資源ごみ','市指定の資源ごみ',locator='ごみの収集日・正しい出し方／資源ごみ',prep='資源品目ごとの市指定方法に従う')
add('M073','不燃性粗大ごみ','大型の不燃性家庭ごみ',locator='ごみの収集日・正しい出し方／不燃性粗大ごみ',ui='REFERENCE_ONLY',channel='CURBSIDE',bulky='TRUE')

def ensure_registry():
 path=MASTER/'02_official_domain_registry.csv'; fields,rows=read_csv(path); fields=fields or REGISTRY_FIELDS
 existing={(r.get('municipality_id'),r.get('host')) for r in rows}
 for mid,specs in source_specs.items():
  for _,_,url,_,_ in specs:
   host=(urlparse(url).hostname or '').lower(); key=(mid,host)
   if not host or key in existing: continue
   rows.append({'municipality_id':mid,'host':host,'authority_type':'MUNICIPAL_DOMAIN','authority_name':municipality_specs[mid]['city'],'verification_url':municipality_specs[mid]['top'],'verified_date':CHECKED,'notes':'Batch 07 official source host'}); existing.add(key)
 rows.sort(key=lambda r:(r.get('municipality_id',''),r.get('host',''))); write_csv(path,fields,rows)

def build_sources():
 rows=[]
 for mid,specs in source_specs.items():
  for i,(title,kind,url,updated,used) in enumerate(specs,1):
   rows.append({'municipality_id':mid,'source_id':f'S-{mid}-{i:02d}','資料名':title,'資料種別':kind,'公式URL':url,'発行主体':municipality_specs[mid]['city'],'対象年度':'令和8年度','ページ更新日':updated,'取得確認日':CHECKED,'使用した情報':used,'優先度':str(i),'現行性':'現行','備考':'','official_verified':'','official_basis':'','official_linking_url':''})
 return rows

def build_categories():
 by_mid={}
 for raw in categories: by_mid.setdefault(raw['municipality_id'],[]).append(raw)
 rows=[]
 for mid,raws in by_mid.items():
  name_to_id={r['自治体正式名称']:f'C-{mid}-{i:02d}' for i,r in enumerate(raws,1)}
  for i,raw in enumerate(raws,1):
   sidx=int(raw['source_index']); src=source_specs[mid][sidx-1]
   rows.append({'municipality_id':mid,'category_id':name_to_id[raw['自治体正式名称']],'自治体正式名称':raw['自治体正式名称'],'category_group':raw['category_group'],'parent_category_id':'','classification_level':raw['classification_level'],'表示順':str(i),'collection_channel':raw['collection_channel'],'代表品目':raw['代表品目'],'入れてはいけない物':raw['入れてはいけない物'],'適用条件':raw['適用条件'],'条件外の扱い':raw['条件外の扱い'],'出す前の処理':raw['出す前の処理'],'袋・容器のルール':raw['袋・容器のルール'],'サイズ・条件':raw['サイズ・条件'],'粗大ごみ扱いか':raw['粗大ごみ扱いか'],'予約が必要か':raw['予約が必要か'],'有料か':raw['有料か'],'料金ルール':raw['料金ルール'],'自治体収集外か':raw['自治体収集外か'],'注意事項':raw['注意事項'],'source_id':f'S-{mid}-{sidx:02d}','出典URL':src[2],'出典ページ・該当箇所':raw['出典ページ・該当箇所'],'確認日':CHECKED,'ui_role':raw['ui_role'],'rule_status':'CURRENT','effective_from':'','effective_to':''})
 return rows

def build_municipalities():
 rows=[]
 for mid,spec in municipality_specs.items():
  passed=mid in PASS_TARGETS
  rows.append({'municipality_id':mid,'都道府県':spec['pref'],'市町村':spec['city'],'実装区分':'中国5県全市町村','ごみ処理主体':spec['processor'],'自治体ごみトップURL':spec['top'],'分別ガイドURL':spec['guide'],'品目検索URL':'','やさしい日本語URL':'','多言語資料URL':'','対象年度':'令和8年度','最終確認日':CHECKED,'確認ステータス':'QA_REQUIRED','備考':spec['note'],'official_category_count':'','reviewed_category_count':'','category_count_basis':'住民が排出時に選択する公式区分を現行公式ページ・現年度資料で照合。' if passed else '全区分網羅性の証拠未取得。推測で補完しない。','category_count_verified':'TRUE' if passed else 'FALSE','category_count_check_status':'MANUAL_INDEX_REVIEW' if passed else 'NOT_REVIEWED','category_count_review_id':f'CR-{mid}-CATEGORY-COVERAGE' if passed else '','category_count_reviewed_date':CHECKED if passed else '','category_count_reviewed_by':REVIEWER if passed else '','search_service_check_status':'NOT_CHECKED','search_service_check_evidence':'','easy_japanese_check_status':'NOT_CHECKED','easy_japanese_check_evidence':'','multilingual_check_status':'NOT_CHECKED','multilingual_check_evidence':''})
 return rows

def build_review_evidence():
 rows=[]
 for mid in PASS_TARGETS:
  for i,src in enumerate(source_specs[mid],1):
   rows.append({'review_evidence_id':f'CRE-{mid}-{i:02d}','review_id':f'CR-{mid}-CATEGORY-COVERAGE','municipality_id':mid,'source_id':f'S-{mid}-{i:02d}','locator':src[4],'evidence_role':'PRIMARY_INDEX' if i==1 else 'SUPPLEMENTAL_INDEX','notes':f'{CHECKED} Batch 07 resident-facing category completeness review'})
 return rows

def main():
 if set(municipality_specs)!=TARGETS or set(source_specs)!=TARGETS: raise ValueError('Batch07 spec target mismatch')
 ensure_registry(); OUT.mkdir(parents=True,exist_ok=True); p='batch_07_'
 write_csv(OUT/f'{p}municipalities.csv',MUNICIPALITY_FIELDS,build_municipalities())
 write_csv(OUT/f'{p}categories.csv',CATEGORY_FIELDS,build_categories())
 write_csv(OUT/f'{p}sources.csv',SOURCE_FIELDS,build_sources())
 write_csv(OUT/f'{p}qa.csv',QA_FIELDS,[]); write_csv(OUT/f'{p}item_mapping.csv',MAPPING_FIELDS,[]); write_csv(OUT/f'{p}item_coverage.csv',COVERAGE_FIELDS,[])
 write_csv(OUT/f'{p}category_review_evidence.csv',CATEGORY_REVIEW_EVIDENCE_FIELDS,build_review_evidence())
 counts=migrate_batch_dir(OUT); print(' '.join(f'{k}={v}' for k,v in counts.items()))
import sys
from batch07_verified_supplement import apply as _apply_batch07_verified_supplement
_apply_batch07_verified_supplement(sys.modules[__name__])

if __name__=='__main__': main()
