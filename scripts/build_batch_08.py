#!/usr/bin/env python3
"""Build Batch 08 (M074-M083) from official resident-facing sources.

M076 Bizen is intentionally QA_REQUIRED: in FY2026 the municipality still
operates both 9-type/23-division districts and old-division districts.
The 23-division evidence is stored, but city-wide completeness is not claimed.
"""
from __future__ import annotations
from pathlib import Path
from urllib.parse import urlparse
from schema_v12 import (
    CATEGORY_FIELDS,CATEGORY_REVIEW_EVIDENCE_FIELDS,COVERAGE_FIELDS,MAPPING_FIELDS,
    MASTER,MUNICIPALITY_FIELDS,QA_FIELDS,SOURCE_FIELDS,migrate_batch_dir,read_csv,write_csv,
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'research'/'batches'/'batch_08'
CHECKED='2026-08-19'; REVIEWER='OPENAI_CHATGPT_BATCH08_REVIEW'; NS='NOT_STATED_IN_CITED_SOURCE'
TARGETS={f'M{i:03d}' for i in range(74,84)}
PASS_TARGETS=TARGETS-{'M076'}
REGISTRY_FIELDS=['municipality_id','host','authority_type','authority_name','verification_url','verified_date','notes']

municipality_specs={
'M074':dict(pref='岡山県',city='高梁市',processor='高梁市／高梁地域事務組合',top='https://www.city.takahashi.lg.jp/soshiki/14/gomibunbetsu.html',guide='https://www.city.takahashi.lg.jp/soshiki/14/gomibunbetsu.html',note='2026年2月更新の住民向け公式表を全件照合。'),
'M075':dict(pref='岡山県',city='新見市',processor='新見市',top='https://www.city.niimi.okayama.jp/kurashi/kurashi_detail/index/37602.html',guide='https://www.city.niimi.okayama.jp/kurashi/kurashi_detail/index/37602.html',note='現行公式ページの可燃・埋立・資源・粗大の4住民区分を採用。'),
'M076':dict(pref='岡山県',city='備前市',processor='備前市',top='https://www.city.bizen.okayama.jp/soshiki/12/5401.html',guide='https://www.city.bizen.okayama.jp/soshiki/12/5401.html',note='令和8年度も資源回収ステーション設置済地区の9種23分別と未設置地区の旧分別版が併存。23分別は構造化するが市全域のcategory completenessは未確認。'),
'M077':dict(pref='岡山県',city='瀬戸内市',processor='瀬戸内市',top='https://www.city.setouchi.lg.jp/soshiki/14/138748.html',guide='https://www.city.setouchi.lg.jp/soshiki/14/138748.html',note='令和8年度カレンダーと令和8年4月開始のプラスチック資源一括回収を反映。'),
'M078':dict(pref='岡山県',city='赤磐市',processor='赤磐市',top='https://www.city.akaiwa.lg.jp/kurashi/gomi/gomi/kankyo_center/gomibunbetu/index.html',guide='https://www.city.akaiwa.lg.jp/kurashi/gomi/gomi/kankyo_center/gomibunbetu/7755.html',note='2026年度カレンダーと2026年7月更新のプラスチック資源案内を照合。'),
'M079':dict(pref='岡山県',city='真庭市',processor='真庭市',top='https://www.city.maniwa.lg.jp/soshiki/171/98300.html',guide='https://www.city.maniwa.lg.jp/soshiki/171/98300.html',note='公式ページが家庭ごみ分別表(1)～(16)を明示。16区分を公式葉として保持。'),
'M080':dict(pref='岡山県',city='美作市',processor='美作市',top='https://www.city.mimasaka.lg.jp/soshiki/shimin/kankyo/Cleancenter/life_guide01.html',guide='https://www.city.mimasaka.lg.jp/soshiki/shimin/kankyo/Cleancenter/life_guide01.html',note='現行詳細ページと令和8年度カレンダーを照合。カレンダー群を投影親、実際の分別コンテナ等を公式子葉として保持。'),
'M081':dict(pref='岡山県',city='浅口市',processor='浅口市／井笠広域里庄清掃工場',top='https://www.city.asakuchi.lg.jp/page/1109.html',guide='https://www.city.asakuchi.lg.jp/page/1109.html',note='複数地域の2026年4月更新ページを照合。収集日・粗大日の組み方に地域差はあるが、資源11品目は共通。'),
'M082':dict(pref='岡山県',city='和気町',processor='和気町',top='https://www.town.wake.lg.jp/soshiki/seikatsukankyo/gyomu/1/1999.html',guide='https://www.town.wake.lg.jp/soshiki/seikatsukankyo/gyomu/1/1999.html',note='令和8年度分別表を使用。令和8年10月開始の製品プラスチック拡大はPLANNEDとしてCURRENTから分離。'),
'M083':dict(pref='岡山県',city='早島町',processor='早島町',top='https://www.town.hayashima.lg.jp/soshiki/jogesuido/gyomu/gomi/katei_gomi/bunbetsu/1638.html',guide='https://www.town.hayashima.lg.jp/soshiki/jogesuido/gyomu/gomi/katei_gomi/bunbetsu/1887.html',note='2026年4月更新家庭ごみページと現行資源ごみ4系統を照合。収集シール対象を人工的な粗大ごみ区分にしない。'),
}

source_specs={
'M074': [('ごみの分別や出し方','自治体公式Webページ',municipality_specs['M074']['guide'],'2026-02-16','燃やせる/燃やせない/びん/かん/PET/その他プラ/紙類の住民区分と前処理')],
'M075': [('ごみの分別・出し方','自治体公式Webページ',municipality_specs['M075']['guide'],'現行','可燃・埋立・資源ごみ（再資源化物）・粗大ごみの住民区分')],
'M076': [('ごみの収集及び分別','自治体公式Webページ',municipality_specs['M076']['guide'],'2026-04-01','令和8年度に9種23分別地区と旧分別地区が併存すること'),('簡易版ごみ分別ちらし（英語版）','自治体公式PDF','https://www.city.bizen.okayama.jp/uploaded/attachment/23007.pdf','現行配布','9種23分別の個別分別項目・品目・前処理')],
'M077': [('家庭ごみの出し方','自治体公式Webページ',municipality_specs['M077']['guide'],'2026-03-17','令和8年度カレンダー・分別マニュアルへの現行導線'),('令和8年度ごみ収集カレンダー（牛窓地区）','自治体公式PDF','https://www.city.setouchi.lg.jp/uploaded/attachment/126501.pdf','2026','現行9収集ラベル'),('プラスチック資源の一括回収について','自治体公式Webページ','https://www.city.setouchi.lg.jp/soshiki/14/154186.html','2025-10-17','令和8年4月から製品プラスチックを含めた一括回収')],
'M078': [('ごみの分別','自治体公式Webページ',municipality_specs['M078']['top'],'現行','2026年度カレンダーと分別資料への公式索引'),('2026年度ごみカレンダー','自治体公式Webページ',municipality_specs['M078']['guide'],'2026','A/B/C/D地域で共通する現行分別ラベル'),('プラスチック資源回収','自治体公式Webページ','https://www.city.akaiwa.lg.jp/annai/shiminseikatsu/kankyou/kurashi/kankyo_eisei/gomi/kankyo_center/gomibunnbetu/9352.html','2026-07-07','プラスチック製容器包装と製品プラスチックをプラスチック資源として回収')],
'M079': [('令和8年度のごみ収集日程及び家庭ごみ分別表について','自治体公式Webページ',municipality_specs['M079']['guide'],'2026-04-01','分別表に(1)～(16)があることを明示'),('家庭ごみ分別表（全地域）','自治体公式PDF','https://www.city.maniwa.lg.jp/uploaded/attachment/35804.pdf','現行配布','16区分の正式名称と代表品目・前処理')],
'M080': [('ごみの出し方','自治体公式Webページ',municipality_specs['M080']['guide'],'現行','実際の分別コンテナ・袋ごとの詳細区分と前処理'),('令和8年度ごみカレンダー','自治体公式PDF','https://www.city.mimasaka.lg.jp/material/files/group/14/REIWA8NENNDOGOMMIKARENNDA-1.pdf','令和8年度','現年度に同区分体系が稼働すること')],
'M081': [('家庭ごみの出し方','自治体公式Webページ',municipality_specs['M081']['top'],'2024-03-19','令和7年12月15日以降の変更と各地域ページへの公式索引'),('家庭ごみの出し方（寄島地域例）','自治体公式Webページ','https://www.city.asakuchi.lg.jp/page/1143.html','2026-04-01','もえる/もえない/不燃性粗大/資源物と資源11品目'),('家庭ごみの出し方（金光地域例）','自治体公式Webページ','https://www.city.asakuchi.lg.jp/page/14587.html','2026-04-01','もえないごみ・不燃性粗大ごみが同日に収集される地域でも資源11品目は共通')],
'M082': [('収集カレンダー・指定ごみ袋等取扱い店','自治体公式Webページ',municipality_specs['M082']['top'],'2026-05-01','令和8年度各地区カレンダーへの公式導線'),('令和8年度家庭ゴミと資源化物の分け方・出し方','自治体公式PDF','https://www.town.wake.lg.jp/material/files/group/21/syuusyuunittei4.pdf','令和8年度','CURRENT区分、危険物前処理、令和8年10月開始予定の製品プラスチック')],
'M083': [('家庭ごみの出し方','自治体公式Webページ',municipality_specs['M083']['top'],'2026-04-01','燃やせる・燃やせないごみと収集シール条件'),('資源ごみの出し方','自治体公式Webページ',municipality_specs['M083']['guide'],'現行案内中','紙類・金属類・びん等・布類/PETの4資源系統')],
}

cats=[]
def add(mid,name,rep,*,source=1,parent='',ui='SORT_BUCKET',level='PRIMARY',channel='CURBSIDE',forbidden=NS,cond='',fallback=NS,prep=NS,bag='',size='',bulky='FALSE',excluded='FALSE',note='',status='CURRENT',effective_from='',effective_to=''):
    cats.append(dict(municipality_id=mid,自治体正式名称=name,category_group=parent or name,parent_name=parent,classification_level=level,collection_channel=channel,代表品目=rep,入れてはいけない物=forbidden,適用条件=cond,条件外の扱い=fallback,出す前の処理=prep,袋・容器のルール=bag,サイズ・条件=size,粗大ごみ扱いか=bulky,予約が必要か='TRUE' if channel=='BOOKED_PICKUP' else 'FALSE',有料か='FALSE',料金ルール='',自治体収集外か=excluded,注意事項=note,source_index=str(source),出典ページ・該当箇所=name,ui_role=ui,rule_status=status,effective_from=effective_from,effective_to=effective_to))
def ex(mid,name,rep,*,source=1): add(mid,name,rep,source=source,ui='EXCLUDED_NOTICE',level='EXCLUDED',channel='NOT_COLLECTED',excluded='TRUE',fallback='販売店・専門業者等の公式案内に従う',prep='受入先の指示に従う')

# M074 Takahashi: seven resident categories.
add('M074','燃やせるごみ','生ごみ・可燃性家庭ごみ',prep='生ごみは十分に水切り',bag='45L以下の透明・半透明袋')
add('M074','燃やせないごみ','不燃性家庭ごみ',bag='45L以下の透明・半透明袋',prep='袋に入らないものは「不用品」と表示')
add('M074','びん類','飲食用びん',prep='キャップを外し水洗いし指定コンテナへ')
add('M074','かん類','飲食用缶・スプレー缶・ガス缶',prep='水洗い。スプレー缶・ガス缶は使い切り穴を空ける')
add('M074','ペットボトル','PETマークのボトル',prep='水洗い。キャップ・ラベルはその他プラスチックへ')
add('M074','その他プラスチック','その他プラマークのある容器包装',prep='水洗い等で汚れを落とす')
add('M074','雑紙・紙パック・段ボール・古新聞・古雑誌','雑紙・紙パック・段ボール・新聞・雑誌',prep='種類ごとにひもで十文字。雑紙は紙袋または結束')
ex('M074','収集できないもの','家電リサイクル品・処理困難物等')

# M075 Niimi.
add('M075','可燃ごみ','可燃性家庭ごみ',bag='新見市記名式指定ごみ袋（黄色）')
add('M075','埋立ごみ','埋立対象の家庭ごみ',bag='新見市記名式指定ごみ袋（黄色）')
add('M075','資源ごみ（再資源化物）','びん・缶・PET・古紙等',prep='資源は透明袋。古紙類はひもでしばる')
add('M075','粗大ごみ','大型家庭ごみ',ui='REFERENCE_ONLY',channel='BOOKED_PICKUP',bulky='TRUE',prep='事前申込し収集指定日に出す')

# M076 Bizen: 23-division districts only. City-wide completeness intentionally not claimed.
bizen_cond='資源回収ステーション設置済地区（令和8年度9種23分別）'
for name,rep,prep in [
('燃えるごみ','可燃性家庭ごみ',NS),('小型混合物','小型の不燃・複合ごみ',NS),
('無色びん','無色の飲食用びん','フタを外し洗浄'),('茶色びん','茶色の飲食用びん','フタを外し洗浄'),('その他色びん','無色・茶色以外の飲食用びん','フタを外し洗浄'),
('アルミ缶','アルミ缶','中を洗浄'),('スチール缶','スチール缶','中を洗浄'),('その他金属','鍋・やかん・フライパン等','透明・半透明袋'),('スプレー缶','スプレー缶','中身を使い切るか表示に従いガスを完全に抜く'),
('新聞','新聞紙','種類別にひもで十字'),('雑誌','雑誌','種類別にひもで十字'),('ダンボール','段ボール','種類別にひもで十字'),('紙パック','紙パック','洗浄・乾燥して種類別に結束'),('ざつ紙','雑紙','紙袋に入れて結束または口をテープ留め'),('布類','衣類・布類','45L程度の透明・半透明袋'),
('ペットボトル','PETマークの飲料等ボトル','洗浄・乾燥。フタ・ラベルは廃プラスチックへ'),('廃プラスチック','対象プラスチック容器等','洗浄・乾燥して回収袋へ'),('白色トレイ・発泡スチロール','白色食品トレイ・発泡スチロール','洗浄・乾燥して回収ネットへ'),
('蛍光灯','丸形・直管・電球型蛍光灯','種類別回収。割らない'),('びん類 その他','化粧品びん・陶磁器等',NS),('電球','白熱電球等',NS),('体温計等','アルコール・水銀体温計等',NS),('廃乾電池','アルカリ・マンガン等乾電池','指定回収。対象外電池は公式案内に従う')]:
    add('M076',name,rep,source=2,cond=bizen_cond,prep=prep)
ex('M076','市では処分できないごみ','危険物・適正処理困難物・家電4品目等',source=1)

# M077 Setouchi: FY2026 calendar labels.
add('M077','燃やすしかないごみ','生ごみ・資源化できない可燃物',source=2,prep='市指定袋。生ごみは水切り')
add('M077','飲料用カン・ペットボトル','飲料用缶・PETボトル',source=2,prep='中身を空にして洗浄。PETはキャップ・ラベルを外す')
add('M077','プラスチック資源','プラスチック製容器包装・対象プラスチック製品',source=3,prep='汚れや残留物を除く')
add('M077','金物類','1L超の缶・金属小物・スプレー缶等',source=2,prep='スプレー缶・カセットボンベは中身を使い切り穴をあける')
add('M077','飲食料用ビン','飲食料用びん',source=2,prep='中を洗い色別コンテナへ')
add('M077','古紙','新聞・段ボール・紙パック・雑誌/ざつ紙',source=2,prep='品目別に結束等')
add('M077','コンテナ（電池類・蛍光管・陶磁器・ガラス類・その他ビン）','乾電池・蛍光管・陶磁器・ガラス類・その他びん',source=2,prep='品目に応じ指定コンテナへ')
add('M077','粗大ごみ（可燃）・古布','可燃性粗大ごみ・古布',source=2,ui='REFERENCE_ONLY',bulky='TRUE')
add('M077','粗大ごみ（不燃）・小型家電','不燃性粗大ごみ・小型家電',source=2,ui='REFERENCE_ONLY',bulky='TRUE')

# M078 Akaiwa: six calendar streams + current plastic resource.
for name,rep in [('可燃ごみ','可燃性家庭ごみ'),('中型混合ごみ','中型の混合ごみ'),('粗大ごみ','大型家庭ごみ'),('新聞・雑誌・布等','新聞・雑誌・布類等'),('金属・びん','金属類・飲食用びん'),('ペットボトル・埋立ごみ等','PETボトル・埋立対象物等')]:
    add('M078',name,rep,source=2,ui='REFERENCE_ONLY' if name=='粗大ごみ' else 'SORT_BUCKET',bulky='TRUE' if name=='粗大ごみ' else 'FALSE')
add('M078','プラスチック資源','プラスチック製容器包装・100%プラスチック製品',source=3,prep='汚れを除く。一辺50cm・厚さ0.5cm以下等の条件を確認')

# M079 Maniwa: official 16 numbered divisions.
for name,rep,prep in [
('燃えるごみ類','紙くず・木くず・革・ゴム・塩ビ等',NS),('アルミ缶・スチール缶','飲食用アルミ缶・スチール缶','洗浄'),('無色透明のビン','無色透明びん','ふた・ラベルを外し軽くすすぐ'),('茶色のビン','茶色びん','ふた・ラベルを外し軽くすすぐ'),('その他の色のビン','その他色びん','ふた・ラベルを外し軽くすすぐ'),('ペットボトル','PETボトル','ふた・ラベルを外し軽くすすぐ'),('プラスチック容器包装類','プラマーク容器包装','汚れをすすぐ。落ちない物は燃えるごみ'),('プラスチック製品（プラマーク無し）','対象プラスチック製品','汚れをすすぐ。金属付きは金属類（小）'),('小型家電','携帯電話・デジカメ等','個人情報を削除'),('乾電池','乾電池','対象電池を指定方法で出す'),('布類','古着・下着・シーツ等','透明・半透明袋'),('古紙類','新聞・雑誌・段ボール・牛乳パック・雑がみ','紙ひも等で結束'),('ガラス・陶磁器類','割れたガラス・陶磁器','割れ物は紙等に包む'),('蛍光管類','蛍光管・水銀体温計','割れないようケース等で保護'),('金属類（小）','小型金属類','ガス等は抜く'),('粗大ごみ類','布団・家具・大型金属等','可能な範囲で異素材を外す')]:
    add('M079',name,rep,source=2,prep=prep,ui='REFERENCE_ONLY' if name=='粗大ごみ類' else 'SORT_BUCKET',bulky='TRUE' if name=='粗大ごみ類' else 'FALSE')
ex('M079','取り扱いできないごみ','家電4品目・産廃・処理困難物等',source=2)

# M080 Mimasaka: five learner-facing calendar groups with detailed official leaf children.
add('M080','燃えるごみ','生ごみ・紙おむつ・可燃性家庭ごみ',prep='水切り。金属を外す。指定可燃袋に記名')
parent2='3色びん・生びん・蛍光灯類・ガラス類・陶器類・廃天ぷら油'
add('M080',parent2,'びん・蛍光灯・ガラス・陶器・廃食油',source=2,ui='SORT_BUCKET')
for name,rep,prep in [('透明びん','透明の飲食用びん','キャップを外し洗浄し専用コンテナ'),('茶色びん','茶色の飲食用びん','キャップを外し洗浄し専用コンテナ'),('その他色びん','その他色の飲食用びん','キャップを外し洗浄し専用コンテナ'),('生ビン（いきびん）','ビールびん・一升びん','キャップを外し洗浄し生びんコンテナ'),('蛍光灯類','蛍光管・水銀体温計','割らず専用コンテナ'),('ガラス類','板ガラス・化粧びん・割れガラス','ガラス類コンテナ'),('陶器類','茶碗・皿・鏡・白熱電球','指定燃えないごみ袋'),('廃天ぷら油','家庭の植物性廃食油','PETボトル8分目程度に入れ密栓し専用コンテナ')]:
    add('M080',name,rep,parent=parent2,ui='REFERENCE_ONLY',level='SUBCATEGORY',prep=prep)
parent3='かん類・乾電池類・ライター・スプレー缶・刃物・突鋭物等・小型金属類'
add('M080',parent3,'缶・電池・ライター・スプレー缶・刃物・小型金属',source=2,ui='SORT_BUCKET')
for name,rep,prep in [('かん類','飲料缶・食物缶','洗浄し缶類コンテナ'),('乾電池類','乾電池・ライター','乾電池コンテナ。ライターはナイロン袋'),('小型金属類','小型金属製品','指定燃えない袋。鋭利物は保護'),('スプレー缶','スプレー缶・カセットボンベ','必ず穴をあけてスプレー缶コンテナ'),('刃物・突鋭物など','包丁・ナイフ・画鋲・釘等','専用コンテナ。細かい物は金属缶に入れ密閉')]:
    add('M080',name,rep,parent=parent3,ui='REFERENCE_ONLY',level='SUBCATEGORY',prep=prep)
parent4='プラ製容器包装類・発泡スチロール・紙製容器包装類・ペットボトル'
add('M080',parent4,'プラ容器・白色トレイ・紙容器・PET',source=2,ui='SORT_BUCKET')
for name,rep,prep in [('白色トレイ・発泡スチロール','白色食品トレイ・発泡スチロール','透明・半透明袋。色柄トレイはプラへ'),('プラスチック製容器包装類','プラマーク容器包装','洗浄し透明・半透明袋'),('紙製容器包装類','紙マーク容器包装','異物を外し透明・半透明袋'),('ペットボトル','PETマークのボトル','洗浄しキャップ・ラベルを外す')]:
    add('M080',name,rep,parent=parent4,ui='REFERENCE_ONLY',level='SUBCATEGORY',prep=prep)
add('M080','古紙類','新聞・段ボール・雑誌・牛乳パック等',prep='品目別にひも結束。紙パックは洗い開き乾燥')
add('M080','粗大ごみ（直接搬入のみ）','ベッド・ソファ・布団・大型家具・自転車等',ui='REFERENCE_ONLY',channel='DIRECT_HAUL',bulky='TRUE',prep='美作クリーンセンターへ直接搬入')
ex('M080','家電リサイクル法対象機器','テレビ・エアコン・洗濯機・冷蔵庫等')

# M081 Asakuchi: common item taxonomy; regional calendar may combine nonburnable/coarse days.
add('M081','もえるごみ','生ごみ・可燃性家庭ごみ',source=2,prep='生ごみは水切り',bag='浅口市指定袋')
add('M081','もえないごみ','不燃性家庭ごみ',source=2,bag='浅口市指定袋',cond='地域により不燃性粗大ごみと同日収集')
add('M081','不燃性粗大ごみ','大型不燃性家庭ごみ',source=2,ui='REFERENCE_ONLY',bulky='TRUE',cond='地域によりもえないごみと同日収集')
parent='資源物'; add('M081',parent,'市が資源物として収集する11品目',source=2,ui='SORT_BUCKET')
for name,rep in [('缶類','飲食用缶等'),('びん','飲食用びん等'),('ペットボトル','PETボトル'),('プラスチック製容器包装','プラマーク容器包装'),('プラスチック製品','対象製品プラスチック'),('新聞紙、折り込み広告','新聞・折込広告'),('雑誌、本、雑紙','雑誌・本・雑紙'),('ダンボール','段ボール'),('紙パック','飲料用紙パック'),('布類','衣類・布類'),('乾電池','乾電池')]:
    add('M081',name,rep,source=2,parent=parent,ui='REFERENCE_ONLY',level='SUBCATEGORY',prep='容器類は中をきれいに洗う' if name in {'缶類','びん','ペットボトル','プラスチック製容器包装','プラスチック製品'} else NS)
ex('M081','ステーションで収集しないごみ','家電4品目・処理困難物等',source=2)

# M082 Wake: current FY2026 taxonomy + October planned plastic expansion.
p='可燃ごみ・生ごみ'; add('M082',p,'可燃ごみ・生ごみ',source=2,ui='SORT_BUCKET')
add('M082','可燃ごみ','可燃性家庭ごみ',source=2,parent=p,ui='REFERENCE_ONLY',level='SUBCATEGORY',bag='和気町指定袋（氏名記入）')
add('M082','生ごみ','家庭の生ごみ',source=2,parent=p,ui='REFERENCE_ONLY',level='SUBCATEGORY',prep='十分水切りし専用タルへ。袋のまま入れない')
r='資源化物'; add('M082',r,'かん・PET・白色トレイ・びん・危険物・紙・布・プラ容器包装・廃食油',source=2,ui='SORT_BUCKET')
for name,rep,prep in [('かん類','飲料缶・食用油缶等','中を洗う。油・塗料は完全に抜く'),('ペットボトル','PETボトル','ふた・ラベルを外し水洗いし乾燥'),('白色トレイ','白色食品トレイ','水洗いし乾燥'),('びん類','飲食用びん等','キャップ・口巻きを外し水洗い。5種類に分別'),('危険物等','ガス缶・スプレー缶・刃物・乾電池・ライター等','ガス缶・スプレー缶は穴を開ける。電池は絶縁。刃物は包む'),('紙類','新聞・雑誌・段ボール・牛乳パック等','種類別に結束。紙パックは開き洗い乾燥'),('布類','衣類等','透明袋等で指定方法に従う'),('プラスチック製容器・包装','現行対象プラスチック容器包装','汚れを除く'),('廃食油（天ぷら油）','家庭の植物性廃食油','油かすを除き指定容器へ移す')]:
    add('M082',name,rep,source=2,parent=r,ui='REFERENCE_ONLY',level='SUBCATEGORY',prep=prep)
add('M082','粗大ごみ','家庭用電気製品・家具・自転車等',source=2,ui='REFERENCE_ONLY',bulky='TRUE',prep='器具内の油・乾電池等を抜く')
add('M082','プラスチック資源（製品プラスチックを含む）','容器包装・対象製品プラスチック',source=2,parent=r,ui='HIDDEN',level='SUBCATEGORY',status='PLANNED',effective_from='2026-10-01',prep='汚れを除く。一辺50cm以下・厚さ0.5cm以下等',note='令和8年10月から分別収集開始予定')
ex('M082','処理できないごみ','家電4品目・医療廃棄物・タイヤ・バッテリー等',source=2)

# M083 Hayashima: two household streams + four resource streams. Oversize sticker is not a new category.
add('M083','燃やせるごみ','可燃性家庭ごみ',source=1,bag='町指定ごみ袋',size='袋に入らない場合も長さ1m・20kg以内なら収集シール')
add('M083','燃やせないごみ','不燃性家庭ごみ',source=1,bag='町指定ごみ袋',size='袋に入らない場合も長さ1m・20kg以内なら収集シール')
add('M083','資源ごみ（紙類）','新聞・チラシ・雑誌・段ボール・牛乳パック・その他紙',source=2)
add('M083','資源ごみ（金属類）','アルミ缶・スチール缶・スプレー缶',source=2)
add('M083','資源ごみ（びん・廃乾電池・蛍光管等水銀入り廃製品）','生きびん・雑びん・乾電池・蛍光管等',source=2)
add('M083','資源ごみ（布類・ペットボトル）','衣類・毛布・PETボトル',source=2)
ex('M083','ごみステーションに出せない家電4品目','テレビ・冷蔵庫/冷凍庫・エアコン・洗濯機/衣類乾燥機',source=1)


def ensure_registry():
    path=MASTER/'02_official_domain_registry.csv'; fields,rows=read_csv(path); fields=fields or REGISTRY_FIELDS
    existing={(r.get('municipality_id'),r.get('host')) for r in rows}
    for mid,specs in source_specs.items():
        for _,_,url,_,_ in specs:
            host=(urlparse(url).hostname or '').lower(); key=(mid,host)
            if not host or key in existing: continue
            rows.append({'municipality_id':mid,'host':host,'authority_type':'MUNICIPAL_DOMAIN','authority_name':municipality_specs[mid]['city'],'verification_url':municipality_specs[mid]['top'],'verified_date':CHECKED,'notes':'Batch 08 official source host'}); existing.add(key)
    rows.sort(key=lambda r:(r.get('municipality_id',''),r.get('host',''))); write_csv(path,fields,rows)

def build_sources():
    out=[]
    for mid,specs in source_specs.items():
        for i,(title,kind,url,updated,used) in enumerate(specs,1):
            out.append({'municipality_id':mid,'source_id':f'S-{mid}-{i:02d}','資料名':title,'資料種別':kind,'公式URL':url,'発行主体':municipality_specs[mid]['city'],'対象年度':'令和8年度','ページ更新日':updated,'取得確認日':CHECKED,'使用した情報':used,'優先度':str(i),'現行性':'現行','備考':'','official_verified':'','official_basis':'','official_linking_url':''})
    return out

def build_categories():
    by={}
    for r in cats: by.setdefault(r['municipality_id'],[]).append(r)
    out=[]
    for mid,raws in by.items():
        name_to_id={r['自治体正式名称']:f'C-{mid}-{i:02d}' for i,r in enumerate(raws,1)}
        for i,r in enumerate(raws,1):
            si=int(r['source_index']); src=source_specs[mid][si-1]
            out.append({'municipality_id':mid,'category_id':name_to_id[r['自治体正式名称']],'自治体正式名称':r['自治体正式名称'],'category_group':r['category_group'],'parent_category_id':name_to_id.get(r['parent_name'],'') if r['parent_name'] else '','classification_level':r['classification_level'],'表示順':str(i),'collection_channel':r['collection_channel'],'代表品目':r['代表品目'],'入れてはいけない物':r['入れてはいけない物'],'適用条件':r['適用条件'],'条件外の扱い':r['条件外の扱い'],'出す前の処理':r['出す前の処理'],'袋・容器のルール':r['袋・容器のルール'],'サイズ・条件':r['サイズ・条件'],'粗大ごみ扱いか':r['粗大ごみ扱いか'],'予約が必要か':r['予約が必要か'],'有料か':r['有料か'],'料金ルール':r['料金ルール'],'自治体収集外か':r['自治体収集外か'],'注意事項':r['注意事項'],'source_id':f'S-{mid}-{si:02d}','出典URL':src[2],'出典ページ・該当箇所':r['出典ページ・該当箇所'],'確認日':CHECKED,'ui_role':r['ui_role'],'rule_status':r['rule_status'],'effective_from':r['effective_from'],'effective_to':r['effective_to']})
    return out

def leaf_count(mid):
    rows=[r for r in cats if r['municipality_id']==mid and r['rule_status']=='CURRENT' and r['ui_role']!='EXCLUDED_NOTICE']
    parents={r['parent_name'] for r in rows if r['parent_name']}
    return sum(1 for r in rows if r['自治体正式名称'] not in parents)

def build_municipalities():
    out=[]
    for mid,s in municipality_specs.items():
        passed=mid in PASS_TARGETS; official='16' if mid=='M079' else ''
        status='OFFICIAL_COUNT_MATCHED' if mid=='M079' else ('MANUAL_INDEX_REVIEW' if passed else 'NOT_REVIEWED')
        reviewed='' if status!='MANUAL_INDEX_REVIEW' else str(leaf_count(mid))
        basis=('公式ページが家庭ごみ分別表(1)～(16)を明示し16葉を照合。' if mid=='M079' else ('住民が排出時に選択する現行公式区分を複数の公式資料で照合。' if passed else '令和8年度も9種23分別と旧分別が地区別併存。市全域を一意な分別体系としては未確認。'))
        out.append({'municipality_id':mid,'都道府県':s['pref'],'市町村':s['city'],'実装区分':'中国5県全市町村','ごみ処理主体':s['processor'],'自治体ごみトップURL':s['top'],'分別ガイドURL':s['guide'],'品目検索URL':'','やさしい日本語URL':'','多言語資料URL':'','対象年度':'令和8年度','最終確認日':CHECKED,'確認ステータス':'QA_REQUIRED','備考':s['note'],'official_category_count':official,'reviewed_category_count':reviewed,'category_count_basis':basis,'category_count_verified':'TRUE' if passed else 'FALSE','category_count_check_status':status,'category_count_review_id':f'CR-{mid}-CATEGORY-COVERAGE' if passed else '','category_count_reviewed_date':CHECKED if passed else '','category_count_reviewed_by':REVIEWER if passed else '','search_service_check_status':'NOT_CHECKED','search_service_check_evidence':'','easy_japanese_check_status':'NOT_CHECKED','easy_japanese_check_evidence':'','multilingual_check_status':'NOT_CHECKED','multilingual_check_evidence':''})
    return out

def build_review_evidence():
    out=[]
    for mid in sorted(PASS_TARGETS):
        for i,src in enumerate(source_specs[mid],1):
            role='OFFICIAL_TOTAL' if mid=='M079' and i==1 else ('PRIMARY_INDEX' if i==1 else 'SUPPLEMENTAL_INDEX')
            out.append({'review_evidence_id':f'CRE-{mid}-{i:02d}','review_id':f'CR-{mid}-CATEGORY-COVERAGE','municipality_id':mid,'source_id':f'S-{mid}-{i:02d}','locator':src[4],'evidence_role':role,'notes':f'{CHECKED} Batch 08 resident-facing category completeness review'})
    return out

def main():
    if set(municipality_specs)!=TARGETS or set(source_specs)!=TARGETS: raise ValueError('Batch08 target mismatch')
    ensure_registry(); OUT.mkdir(parents=True,exist_ok=True); p='batch_08_'
    write_csv(OUT/f'{p}municipalities.csv',MUNICIPALITY_FIELDS,build_municipalities())
    write_csv(OUT/f'{p}categories.csv',CATEGORY_FIELDS,build_categories())
    write_csv(OUT/f'{p}sources.csv',SOURCE_FIELDS,build_sources())
    write_csv(OUT/f'{p}qa.csv',QA_FIELDS,[]); write_csv(OUT/f'{p}item_mapping.csv',MAPPING_FIELDS,[]); write_csv(OUT/f'{p}item_coverage.csv',COVERAGE_FIELDS,[])
    write_csv(OUT/f'{p}category_review_evidence.csv',CATEGORY_REVIEW_EVIDENCE_FIELDS,build_review_evidence())
    counts=migrate_batch_dir(OUT); print(' '.join(f'{k}={v}' for k,v in counts.items()))

if __name__=='__main__': main()
