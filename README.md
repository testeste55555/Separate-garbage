# Separate-garbage

自治体ごとの家庭ごみ分別ルールを、授業用アプリで利用できる形へ正規化するプロジェクトです。

中心Can-do：

> 名前が分からないごみでも、自分が住む自治体のルールを調べて、仲間と相談しながら、正しく分別ができる。

収集曜日・収集時間・地区別カレンダーは構造化対象外です。カレンダーは必要に応じて、現行taxonomyの運用確認や地域variantの証拠として使用します。

## 現在地（2026-08-19）

- MASTER固定ID台帳：**143自治体**
- active実装対象：**134自治体**
- DEFERRED：**9自治体**
  - M065 知夫村：公式一次資料本文の全区分確認が安定しない
  - M076 備前市：地区別CURRENT分別体系が併存
  - M086 新庄村：公式一次資料本文を安定取得できず全区分を全件照合できない
  - M098 尾道市：尾道・向島・御調・因島・瀬戸田でCURRENT体系が併存
  - M099 福山市：市内一般・内海町・沼隈町で住民向け分別単位に差
  - M100 府中市：府中地区と上下地区で住民向け表示単位・正式名称に差
  - M120 萩市：大島・見島・相島地区で一部分別区分が異なる
  - M123 岩国市：地域群により食品トレー等の分別先・排出方法が異なる
  - M127 美祢市：美祢・美東・秋芳で正式区分・同一品目の分別先が異なる
- Pilot：5自治体完了
- Batch 01〜06：各10自治体完了
- Batch 07：9自治体完了（M065 DEFERRED）
- Batch 08：9自治体完了（M076 DEFERRED）
- Batch 09：9自治体完了（M086 DEFERRED）
- Batch 10：7自治体完了（M098・M099・M100 DEFERRED）
- Batch 11：10自治体完了
- Batch 12：8自治体完了（M120・M123 DEFERRED）
- Batch 13：**9自治体完了**（M127 DEFERRED）
- canonical：**126自治体**
- canonical QA：**126 `QA_PASSED` / 0 `QA_REQUIRED`**
- category：**1,512行**
- structured official leaves：**1,387区分**
- official sources：**343**
- item mapping：**1,259条件枝**（初期候補段階）
- 40品目coverage：**5,040自治体品目pair**
- category review evidence：**306行**
- Schema：**v1.2.4**
- Workflow：**v1.23**
- Batch 13専用RED TEAM：**PASS**
- canonical structural validation：**PASS**
- Schema v1.2.4 RED TEAM：**PASS**
- operational category semantics RED TEAM：**PASS**
- `NEXT_BATCH_GATE`：**PASS**
- `APP_READINESS_GATE`：**HOLD**（40共通品目のITEM_SPECIFIC公式確認未完了）

CI記録：`docs/research/batch_13_ci_status.txt`
QA記録：`docs/research/batch_13_qa_report.md`

## Batch 13

MASTER範囲はM126〜M135です。

### canonicalへ統合した9自治体

- M126 柳井市：10公式葉
- M128 周南市：11公式葉
- M129 山陽小野田市：12公式葉
- M130 周防大島町：12公式葉
- M131 和木町：11公式葉
- M132 上関町：12公式葉
- M133 田布施町：12公式葉
- M134 平生町：12公式葉
- M135 阿武町：5公式葉

### DEFERRED

- M127 美祢市：美祢地域・美東地域・秋芳地域で同時にCURRENTな住民向け体系が併存し、正式区分および同一品目の分別先が実際に異なるため`SCHEMA_SCOPE_LIMITATION`

固定IDは削除・再採番しません。

### Batch 13真正性事項

- 柳井市：`ビン・乾電池`をガラスビン／乾電池へ、`ペットボトル・古紙`をPET／新聞・チラシ／段ボール／雑誌・本・その他の紙へ分解し、別袋・別束・専用回収ボックスという実排出単位を保持。スプレー缶は**使い切り後、屋外で穴を開ける**。
- 周南市：地域別ページは日程差で、市全域向けtaxonomyを採用。古紙・衣類、びん缶/PET、プラスチック2系統を住民子葉へ展開。小型家電は`DROP_OFF`、粗大ごみは`BOOKED_PICKUP`。スプレー缶は**穴を開ける**。
- 山陽小野田市：古紙類は新聞／雑誌類／ダンボール／紙パックの4葉。根拠のない可燃ごみ前処理は`NOT_STATED_IN_CITED_SOURCE`へ戻した。
- 周防大島町：公式検索サービスの`種類でさがす`から12公式葉を採用し、`収集できないごみ`等2区分は`EXCLUDED_NOTICE`として葉数外。検索サービスは`CHECKED_PRESENT`＋URL/date evidenceで正式管理。スプレー缶は**穴あけ不要**。
- 和木町：現行11住民区分。スプレー缶は**使い切り、穴を開けずに出す**。
- 上関町：古紙・紙パックを4子葉へ分け、PETは専用回収ボックスの`DROP_OFF`。スプレー缶は中身を使い切ることだけを記録し、穴あけ有無を推測追加しない。
- 田布施町・平生町：公式の`7分別`をofficial leaf総数へ流用せず、缶／金属の別袋と資源5品目の種別分離を保持し、各12公式葉として`MANUAL_INDEX_REVIEW`。
- 阿武町：2026年4月改定後も可燃／不燃／資源の3指定袋は維持。**同日収集化をcategory統合と誤認しない**。資源袋内部の缶・びん・PET・容器包装プラを人工分割しない。

## データ設計の原則

- `rule_status=CURRENT` かつ `ui_role=SORT_BUCKET` の行だけを学習者用の現在の仕分け箱として投影する。
- category completenessは処理施設側工程ではなく、**住民が排出時に選択する公式分別区分**を基準とする。
- 自治体正式名称は括弧・記号を含め公式表記を保持する。
- `OFFICIAL_COUNT_MATCHED`は公式資料がcanonical leafと同じ粒度の数値総数を明示する場合だけ使用する。それ以外は`MANUAL_INDEX_REVIEW`。
- 上位見出しの数値とresident-facing official leaf総数を混同しない。
- 住民が別袋・別容器・別束へ分ける公式子区分は保持し、投影親を公式葉件数へ二重計上しない。
- 地域別資料があっても、差が収集日程だけかtaxonomy差かを必ず分ける。
- 公式検索サービスは`CHECKED_PRESENT`等のformal check statusとURL/date evidenceで管理する。
- `DROP_OFF`・`BOOKED_PICKUP`・`DIRECT_HAUL`・`RETAILER_OR_MAKER`等の実経路を通常収集へ寄せない。
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
- `data/research/batches/batch_01/`〜`batch_13/`：Batch研究bundle
- `data/research/02_categories_master.csv`：canonical分別区分
- `data/research/03_sources_master.csv`：canonical出典
- `data/research/04_municipalities_research.csv`：canonical自治体調査
- `data/research/05_item_mapping_master.csv`：初期品目対応・条件枝
- `data/research/06_qa_log.csv`：機械再計算済みQA
- `data/research/07_item_mapping_coverage.csv`：完了自治体×40品目の調査状態
- `data/research/08_category_review_evidence.csv`：category completeness公式証拠
- `docs/research/`：Batch QA・CI記録
- `docs/workflow/`：作業フロー履歴（現行 v1.23）
- `scripts/build_batch_*.py`：Batch再生成
- `scripts/red_team_batch_*.py`：Batch専用RED TEAM

## Batch 13再現・Gate

```bash
python3 scripts/build_batch_13_active.py
python3 scripts/validate_research.py --batch batch_13 --next-batch-gate
python3 scripts/red_team_batch_13.py
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v12.py
python3 scripts/red_team_operational_category_semantics.py
python3 scripts/check_next_batch_gate.py
```

`NEXT_BATCH_GATE`はcategory研究を次Batchへ進めるためのGateです。`APP_READINESS_GATE`とは分離されており、現在の`APP_READINESS_GATE=HOLD`は40品目のITEM_SPECIFICレビュー未完了による正常な状態です。

## 次Batch

Batch 14はMASTER残りの個別指定8自治体です。

**M136 吉野川市 → M137 綾川町 → M138 多度津町 → M139 丸亀市 → M140 三豊市 → M141 小竹町 → M142 北九州市 → M143 佐伯市**

Batch 14完了時、DEFERREDを除く134自治体のcategory研究が一巡する見込みです。
