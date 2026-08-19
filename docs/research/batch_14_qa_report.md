# Batch 14 QA Report

実施日: 2026-08-19
Schema: v1.2.4
対象MASTER: M136〜M143（MASTER最終8自治体）

## 判定

**PASS**

- active Batch 14: 6自治体
- QA_PASSED: 6/6
- DEFERRED: M136 吉野川市、M139 丸亀市
- Batch structural validation: PASS
- Batch 14 RED TEAM: PASS
- canonical merge: PASS
- canonical structural validation: PASS
- Schema v1.2.4 RED TEAM: PASS
- operational category semantics RED TEAM: PASS
- NEXT_BATCH_GATE: PASS
- APP_READINESS_GATE: HOLD

CI記録: `docs/research/batch_14_ci_status.txt`

## active自治体と公式葉

- M137 綾川町: 11
- M138 多度津町: 18
- M140 三豊市: 16
- M141 小竹町: 7
- M142 北九州市: 13
- M143 佐伯市: 12

合計公式葉: 77。

## DEFERRED

### M136 吉野川市

鴨島地区と川島・山川・美郷地区で、乾電池・蛍光管等についてCURRENTな住民向け排出単位・回収容器・経路が異なる。単なる収集曜日差ではなく、住民が実際に選択する排出方法に地域差がある。

現行municipality単位Schema/UIでは居住地域scopeを安全に解決できないため、`SCHEMA_SCOPE_LIMITATION`としてDEFERREDとした。固定IDは保持する。

### M139 丸亀市

令和8年度も旧丸亀地区・綾歌飯山地区・本島町等の島しょ部でCURRENTな住民向け収集体系が併存する。本島・牛島の複合的な資源不燃系排出単位や、小手島・手島町の可燃・不燃・資源・ペットボトル体系など、単なる日程差を超える分類・排出単位差がある。

現行municipality単位Schema/UIでは地域scopeを安全に解決できないため、`SCHEMA_SCOPE_LIMITATION`としてDEFERREDとした。固定IDは保持する。

## 真正性確認

- 綾川町: 町内共通の通常8区分を保持。2026年3月開始の小型充電式電池・小型家電回収は通常収集へ混ぜず`DROP_OFF`のREFERENCE_ONLY葉として保持。充電式電池は端子絶縁を記録。
- 多度津町: 上位`資源ごみ`を一葉へ潰さず、住民が品目別に分けて持ち込む15区分を公式子葉として保持。上位親は葉数へ二重計上しない。令和8年度資源ごみ資料を前処理の行単位根拠へ使用。
- 三豊市: 公式の12見出しをそのままofficial leaf総数とせず、`紙類・布類`の新聞／雑誌／ダンボール／紙パック／衣類を別束・別袋の5葉として保持し、16公式葉として`MANUAL_INDEX_REVIEW`。廃食用油はDROP_OFF。充電式電池はごみステーションへ出さない現行経路を保持。
- 小竹町: 現行カレンダーの5分類を保持し、`びん・缶`を人工的に分割しない。2026年4月開始の食品用トレイ類／発泡スチロールは別々の透明袋を用いるため、2つの独立DROP_OFF葉として追加。
- 北九州市: 索引上の`かん・びん・ペットボトル`を、実際の別指定袋・別収集車に対応する`かん・びん`／`ペットボトル`の2子葉へ展開。拠点回収群はREFERENCE_ONLY、市が収集しないものはEXCLUDED_NOTICE。スプレー缶をかん・びんへ誤投入させないよう除外情報を保持。
- 佐伯市: `資源物`を飲食用ビン・カン／PET／古紙3種／布類／小型家電の7実排出葉へ展開。粗大ごみはBOOKED_PICKUP、ガレキ類も独立CURRENT葉として保持。カセットボンベ・スプレー缶は燃えないごみで、中身を使い切り屋外でガス抜きし、穴を2か所あける現行ルールを行単位出典へ結び付けた。

Batch 14は全active自治体を`MANUAL_INDEX_REVIEW`としている。上位見出し数、地区別カレンダー、施設側処理区分をresident-facing official leaf総数へ自動転用していない。

また、category行の具体的な前処理・経路は、その内容を実際に記載する公式資料へsource_idを寄せ、補足資料の存在だけを根拠に詳細を補作しない運用を再確認した。

## canonical更新

Batch 14統合後:

- MASTER fixed IDs: 143
- DEFERRED: 11
- active implementation targets: 132
- canonical municipalities: 132
- QA: 132/132 `QA_PASSED`
- category: 1,594行
- structured official leaves: 1,464
- sources: 368
- initial mapping branches: 1,322
- coverage: 5,280 pair
- category review evidence: 331

DEFERRED 11自治体:
M065 知夫村、M076 備前市、M086 新庄村、M098 尾道市、M099 福山市、M100 府中市、M120 萩市、M123 岩国市、M127 美祢市、M136 吉野川市、M139 丸亀市。

## MASTER全体の到達点

Batch 14をもって、固定143自治体のうち現行Schemaで安全に一意化できる**132 active自治体すべてのresident-facing category研究が一巡完了**した。

`NEXT_BATCH_GATE=PASS`は研究データの構造・次工程進行条件を満たすことを示すが、固定IDに未処理のactive自治体が残っていることを意味しない。今後はcategory Batchを増やすのではなく、主に次へ移行する。

1. 40共通品目の`ITEM_SPECIFIC`公式証拠・条件枝レビューを進め、`APP_READINESS_GATE`を満たす。
2. `district_scope`等のSchema拡張を検討し、地域variantでDEFERREDとなった自治体を安全に再開する。
3. 一次資料本文の安定取得が理由のDEFERRED自治体は、公式資料が安定して確認できる時点で再調査する。

`APP_READINESS_GATE=HOLD`は異常ではなく、category研究完了とアプリ実装準備完了を分離しているための意図した状態である。
