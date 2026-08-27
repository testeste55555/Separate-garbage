# Separate-garbage

自治体ごとの家庭ごみ分別ルールを、授業用アプリで利用できる形へ正規化するプロジェクトです。

中心Can-do：

> 名前が分からないごみでも、自分が住む自治体のルールを調べて、仲間と相談しながら、正しく分別ができる。

収集曜日・収集時間・地区別カレンダーは構造化対象外です。カレンダーは必要に応じて、現行taxonomyの運用確認や地域variantの証拠として使用します。

## 現在地（2026-08-27）

- MASTER固定ID台帳：**143自治体**
- active実装対象：**132自治体**
- DEFERRED：**11自治体**
  - M065 知夫村：公式一次資料本文の全区分確認が安定しない
  - M076 備前市：地区別CURRENT分別体系が併存
  - M086 新庄村：公式一次資料本文を安定取得できず全区分を全件照合できない
  - M098 尾道市：尾道・向島・御調・因島・瀬戸田でCURRENT体系が併存
  - M099 福山市：市内一般・内海町・沼隈町・走島町で住民向け分別単位に差
  - M100 府中市：府中地区と上下地区で住民向け表示単位・正式名称に差
  - M120 萩市：大島・見島・相島地区で一部分別区分が異なる
  - M123 岩国市：地域群により食品トレー等の分別先・排出方法が異なる
  - M127 美祢市：美祢・美東・秋芳で正式区分・同一品目の分別先が異なる
  - M136 吉野川市：鴨島と川島・山川・美郷で乾電池・蛍光管等の排出容器・経路が異なる
  - M139 丸亀市：旧丸亀地区と島しょ部等で住民向け分類・排出単位が異なる
- Pilot：5自治体完了
- Batch 01〜06：各10自治体完了
- Batch 07：9自治体完了（M065 DEFERRED）
- Batch 08：9自治体完了（M076 DEFERRED）
- Batch 09：9自治体完了（M086 DEFERRED）
- Batch 10：7自治体完了（M098・M099・M100 DEFERRED）
- Batch 11：10自治体完了
- Batch 12：8自治体完了（M120・M123 DEFERRED）
- Batch 13：9自治体完了（M127 DEFERRED）
- Batch 14：**6自治体完了**（M136・M139 DEFERRED）
- canonical：**132自治体**
- canonical QA：**132 `QA_PASSED` / 0 `QA_REQUIRED`**
- category：**1,597行**（通常区分に加えAPP_READYレビューで追加した参照経路を含む）
- structured official leaves：**1,464区分**
- official sources：**413**
- item mapping：**1,515条件枝**（APP_READY 120品目pair＋M097・M105のLESSON_READY_10全41条件枝を含む）
- 40品目coverage：**5,280自治体品目pair**
- category review evidence：**332行**
- Schema：**v1.2.4**
- Workflow：**v1.29**
- Batch 14専用RED TEAM：**PASS**
- canonical structural validation：**PASS**
- Schema v1.2.4 RED TEAM：**PASS**
- operational category semantics RED TEAM：**PASS**
- `NEXT_BATCH_GATE`：**PASS**
- `APP_READINESS_GATE`：**HOLD**（M094・M095・M104は各40/40 APP_READY、残る129 active自治体は未完了）

### 地域variant LESSON_READY_10 M098/M099（2026-08-27）

完全な地域別category taxonomyと固定画像10品目に必要な教材差を分離し、`district_scope → lesson_variant_group → teaching box / scoring`を追加した。M098/M099の40品目・完全taxonomy側`DEFERRED`は維持する。

- M098 尾道市：6内部scopeを1教材groupへ集約。地域選択を表示しない
- M098固定10品目：6 scopeすべてを同一正答セットとして確認し、I031電球は教材上「有害ごみ系」に統一
- M099 福山市：4内部scopeを一般地域／内海町・沼隈町／走島町の3教材groupへ集約
- M099一般：紙パックは「資源回収・確認」
- M099内海町・沼隈町：新聞・段ボール・紙パックは「紙類」
- M099走島町：新聞・段ボール・紙パックは「資源回収・確認」
- 固定10品目：4 group×10＝40採点pair
- 対面授業：固定10品目専用BOXではなく、各groupの主要分別箱を表示
- 「資源回収・確認」：自治体正式区分ではなく、紙類差を示す教材用簡略行動箱
- variant mutation RED TEAM：18/18 PASS
- learner UI：内部district名・条件・前処理・例外・出典を表示しない

データ：`data/app/district_scopes.csv`、`data/app/lesson_variant_groups.csv`、`data/app/lesson_variant_teaching_boxes.csv`、`data/app/lesson_variant_item_scoring.csv`

### LESSON_READY_10 M105（2026-08-25）

廿日市市の固定画像10品目について、現行公式50音表と2026年度版ごみ分別ガイドを正本に全条件枝を確認した。APP_READYの意味・40品目atomic昇格・global Gateは変更しない。

- 対象：M105 廿日市市
- 画像品目：10/10
- 条件枝：22/22 `ITEM_SPECIFIC / COMPLETE`
- scoring branch：各品目ちょうど1枝
- 白色トレイの材質・色・汚れ、びん・缶の対象条件、白熱／蛍光／LED電球、リチウムイオン電池の異常品経路を別枝で保持
- canonical：10 pairは`VERIFIED + branch_completeness_confirmed=TRUE`。`APP_READY`ではない
- LESSON_READY_10全自治体mutation RED TEAM：18/18 PASS

監査表：`data/research/lesson_readiness/m105_item_review.csv`

### LESSON_READY_10 M097（2026-08-25）

オンライン画像問題の利用可能自治体を40品目APP_READYの完成順だけに依存させないため、固定画像10品目に限定した`LESSON_READY_10`を追加した。APP_READYの意味・40品目atomic昇格・global Gateは変更しない。

- 対象：M097 三原市
- 画像品目：10/10
- 条件枝：19/19 `ITEM_SPECIFIC / COMPLETE`
- scoring branch：各品目ちょうど1枝
- learner UI：品目名・条件・前処理・例外を表示しない
- canonical：10 pairは`VERIFIED + branch_completeness_confirmed=TRUE`。`APP_READY`ではない
- 自治体別mutation：9/9 PASS

監査表：`data/research/lesson_readiness/m097_item_review.csv`

### APP readiness Pilot M095（2026-08-24）

呉市の共通40品目を現行公式資料へ照合し、2026年4月開始の「プラスチック資源」、危険物、回収拠点、市収集外を含む56条件枝を保持した。

- 40/40品目pair：`APP_READY`
- 56/56条件枝：`ITEM_SPECIFIC / COMPLETE / APP_READY`
- M095自治体単位Gate：PASS
- mutation RED TEAM：16/16 PASS
- canonical全体Gate：HOLD（正常）

監査表：`data/research/app_readiness/m095_item_review.csv`

### APP readiness Pilot M104（2026-08-24）

東広島市の共通40品目を公式資料へ照合し、材質・プラマーク・汚れ・寸法・電池内蔵・枝径等の差を63条件枝で保持した。家電4品目とパソコンは通常箱へ誤投影せず、`EXCLUDED_NOTICE`で保持する。

- 40/40品目pair：`APP_READY`
- 63/63条件枝：`ITEM_SPECIFIC / COMPLETE / APP_READY`
- M104自治体単位Gate：PASS
- mutation RED TEAM：22/22 PASS
- canonical全体Gate：HOLD（正常）

監査表：`data/research/app_readiness/m104_item_review.csv`
報告：`docs/research/app_readiness_m104_pilot_report.md`

### APP readiness Pilot M094（2026-08-24）

広島市の共通40品目を現行公式資料へ品目別に照合し、材質・汚れ・寸法・破損・内容物残存等の差を59条件枝で保持した。

- 40/40品目pair：`APP_READY`
- 59/59条件枝：`ITEM_SPECIFIC / COMPLETE / APP_READY`
- M094自治体単位Gate：PASS
- mutation RED TEAM：16/16 PASS
- canonical全体Gate：HOLD（正常）

公式品目表記・条件・前処理・例外・source/locatorの監査表：`data/research/app_readiness/m094_item_review.csv`
報告：`docs/research/app_readiness_m094_pilot_report.md`

### 画像10品目 mapping Pilot（2026-08-24）

Style Research TOP10のうち地域variantでDEFERREDの尾道市・福山市を除くactive 8自治体について、画像10品目×8自治体＝80組を公式資料へ照合した。

- 履歴的な品目別照合決定 `VERIFIED`：76組
- `UNRESOLVED`：4組（江田島市・海田町の電球／使い捨てライター）
- canonicalで後続 `APP_READY`へ移行：広島市・呉市・東広島市の計30組
- canonicalで後続 `LESSON_READY_10`へ移行：三原市・廿日市市の計20組
- mutation RED TEAM：9/9 PASS

品目別追加sourceは`IS-*`でcategory研究sourceと分離する。成果物・UI HANDOFF：`docs/research/item_image_mapping_pilot_top8_report.md`

**固定143自治体のうち、現行Schemaで安全に一意化できる132 active自治体について、resident-facing category研究の初回一巡は完了しました。**

### Style Research Pilot（2026-08-20）

広島県TOP10の公式分別色を、category正本から独立した追加レイヤーとして実装した。

- 固定TOP10: 10自治体（再ランキングなし）
- category参照可能: 8自治体・51 CURRENT/SORT_BUCKET
- 公式色観測: 61
- UI projection: OFFICIAL_DERIVED 47 / NOT_CONFIRMED 4
- style公式出典: 26
- 中間RED TEAM: PASS
- 最終RED TEAM: 24/24 PASS
- `NEXT_STYLE_BATCH_GATE`: PASS
- M098尾道市・M099福山市の完全category/style接続: HOLD。固定10品目の授業用variantは中立色の主要箱で接続済み

成果物索引: `docs/style_research/README.md`

CI記録：`docs/research/batch_14_ci_status.txt`
QA記録：`docs/research/batch_14_qa_report.md`
現行Workflow：`docs/workflow/WORK_ゴミ出し情報収集フロー_143自治体_v1.28.txt`

## Batch 14

MASTER範囲はM136〜M143です。

### canonicalへ統合した6自治体

- M137 綾川町：11公式葉
- M138 多度津町：18公式葉
- M140 三豊市：16公式葉
- M141 小竹町：7公式葉
- M142 北九州市：13公式葉
- M143 佐伯市：12公式葉

### DEFERRED

- M136 吉野川市：鴨島地区と川島・山川・美郷地区で乾電池・蛍光管等の住民向け排出単位・回収容器・経路が異なるため`SCHEMA_SCOPE_LIMITATION`
- M139 丸亀市：旧丸亀地区と本島・牛島・小手島・手島等で分類・排出単位が異なるため`SCHEMA_SCOPE_LIMITATION`

固定IDは削除・再採番しません。

### Batch 14真正性事項

- 綾川町：町内共通の通常8区分を保持。2026年3月開始の小型充電式電池・小型家電は`DROP_OFF + REFERENCE_ONLY`。充電式電池は端子絶縁を保持。
- 多度津町：上位`資源ごみ`を一葉に潰さず、公式持込一覧で住民が分ける15区分を子葉として保持。上位親は公式葉数へ二重計上しない。
- 三豊市：公式12見出しのうち`紙類・布類`を新聞／雑誌／ダンボール／紙パック／衣類の5実排出葉へ展開し、16公式葉として`MANUAL_INDEX_REVIEW`。廃食用油はDROP_OFF。
- 小竹町：現行5分類を保持し、`びん・缶`を人工分割しない。2026年4月開始の食品用トレイ類／発泡スチロールは別々の透明袋を用いる2つのDROP_OFF葉。
- 北九州市：索引上の`かん・びん・ペットボトル`を、実際の別指定袋・別収集車に対応する`かん・びん`／`ペットボトル`へ展開。拠点回収はREFERENCE_ONLY、市が収集しないものはEXCLUDED_NOTICE。
- 佐伯市：`資源物`を実際の7排出葉へ展開。粗大ごみはBOOKED_PICKUP、ガレキ類は独立CURRENT葉。スプレー缶は中身を使い切り、屋外でガス抜きし、穴を2か所あける現行ルールを具体記載のある公式資料へ結び付ける。

## データ設計の原則

- `rule_status=CURRENT` かつ `ui_role=SORT_BUCKET` の行だけを学習者用の現在の仕分け箱として投影する。
- category completenessは処理施設側工程ではなく、**住民が排出時に選択する公式分別区分**を基準とする。
- 自治体正式名称は括弧・記号を含め公式表記を保持する。
- `OFFICIAL_COUNT_MATCHED`は公式資料がcanonical leafと同じ粒度の数値総数を明示する場合だけ使用する。それ以外は`MANUAL_INDEX_REVIEW`。
- 上位見出しの数値とresident-facing official leaf総数を混同しない。
- 住民が別袋・別容器・別束・別回収ボックスへ分ける公式子区分は保持し、投影親を公式葉件数へ二重計上しない。
- 逆に、公式に一体の住民排出単位を人工的に分割しない。
- 地域別資料があっても、差が収集日程だけかtaxonomy・排出容器・経路差かを必ず分ける。
- `DROP_OFF`・`BOOKED_PICKUP`・`DIRECT_HAUL`・`RETAILER_OR_MAKER`等の実経路を通常収集へ寄せない。
- category行の具体的な前処理・条件・経路は、その内容を実際に支持するsource_idへ結び付ける。
- 内部説明上の小分類だけを理由に独立categoryへ増やさない。
- 現行年度・最新更新の公式資料を優先する。
- 危険物の穴あけ必須／不要／記載なしを全国・県内共通化しない。
- 公式記載がないCORE詳細は`NOT_STATED_IN_CITED_SOURCE`とし、空欄回避用汎用文やモデリング上の説明文をresident guidanceへ混入させない。
- 同一自治体内で複数CURRENT taxonomyがあり、住民の地域scopeを安全に解決できない場合はDEFERREDとする。
- 固定IDはDEFERREDでも削除・再採番しない。
- `APP_READY`はcategory研究完了とは独立し、40品目すべてのITEM_SPECIFIC公式証拠・coverage・条件枝レビューが揃うまで付与しない。

## 主なディレクトリ

- `data/master/01_municipalities_master.csv`：143自治体固定ID MASTER
- `data/master/02_official_domain_registry.csv`：公式ドメイン・公式導線台帳
- `data/master/04_common_items_master.csv`：共通40品目と教材安全区分
- `data/master/05_deferred_municipalities.csv`：一時実装対象外の固定ID自治体
- `data/research/pilot/`：Pilot 5自治体
- `data/research/batches/batch_01/`〜`batch_14/`：Batch研究bundle
- `data/research/02_categories_master.csv`：canonical分別区分
- `data/research/03_sources_master.csv`：canonical出典
- `data/research/04_municipalities_research.csv`：canonical自治体調査
- `data/research/05_item_mapping_master.csv`：初期品目対応・条件枝
- `data/research/06_qa_log.csv`：機械再計算済みQA
- `data/research/07_item_mapping_coverage.csv`：完了自治体×40品目の調査状態
- `data/research/08_category_review_evidence.csv`：category completeness公式証拠
- `docs/research/`：Batch QA・CI記録
- `docs/workflow/`：作業フロー履歴（現行 v1.28）
- `data/style_research/`：公式色の観測・UI projection・出典台帳
- `data/app/district_scopes.csv`：地域variantの内部地域索引
- `data/app/lesson_variant_groups.csv`：固定10品目に必要な学習者向け地域グループ
- `data/app/lesson_variant_teaching_boxes.csv`：地域variant用の授業用主要箱
- `data/app/lesson_variant_item_scoring.csv`：地域variant group別の固定10品目採点
- `docs/style_research/`：Style Schema、QA、RED TEAM、Gate、HANDOFF
- `scripts/build_batch_*.py`：Batch再生成
- `scripts/red_team_batch_*.py`：Batch専用RED TEAM

## Batch 14再現・Gate

```bash
python3 scripts/build_batch_14_active.py
python3 scripts/validate_research.py --batch batch_14 --next-batch-gate
python3 scripts/red_team_batch_14.py
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v12.py
python3 scripts/red_team_operational_category_semantics.py
python3 scripts/check_next_batch_gate.py
```

`NEXT_BATCH_GATE=PASS`はデータ構造上、次工程へ進める状態であることを示します。未処理active自治体が残っているという意味ではありません。

`APP_READINESS_GATE=HOLD`は正常です。category研究は132 active自治体で一巡完了していますが、アプリに40共通品目を安全に載せるための`ITEM_SPECIFIC`公式証拠・全条件枝レビューは別工程です。

## 次工程

新しいcategory Batchを始めるのではなく、優先順は次のとおりです。

1. 優先自治体ごとに固定10画像品目をルールfamily単位で確認し、`LESSON_READY_10`の授業利用自治体を増やす。
2. 同じ公式根拠を再利用しながら残り30品目も確認し、自治体単位の40/40 `APP_READY`を継続する。
3. 地域variantでDEFERREDとなった自治体向けに`district_scope`等のSchema/UI拡張を設計する。
4. M065知夫村・M086新庄村など一次資料本文の安定取得が課題の自治体を、公式資料が安定して確認できる時点で再調査する。
