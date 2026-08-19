# Separate-garbage

自治体ごとの家庭ごみ分別ルールを、授業用アプリで利用できる形へ正規化するプロジェクトです。

中心Can-do：

> 名前が分からないごみでも、自分が住む自治体のルールを調べて、仲間と相談しながら、正しく分別ができる。

収集曜日・収集時間・地区別カレンダーは構造化対象外です。カレンダーは必要に応じて「その分別体系が現在も運用されていること」の現行性証拠として使用します。

## 現在地（2026-08-19）

- MASTER固定ID台帳：**143自治体**
- active実装対象：**140自治体**
- DEFERRED：**3自治体**
  - M065 知夫村：公式一次資料本文の全区分確認が安定しないため一旦対象外
  - M076 備前市：令和8年度に地区別CURRENT分別体系が併存し、現Schema/UIでは安全にvariant解決できないため対象外
  - M086 新庄村：現行公式ページへの導線は確認できるが、一次資料本文を安定取得できず全区分を全件照合できないため対象外
- Pilot：5自治体完了
- Batch 01〜06：各10自治体完了
- Batch 07：**9自治体完了**（M065をDEFERRED）
- Batch 08：**9自治体完了**（M076をDEFERRED）
- Batch 09：**9自治体完了**（M086をDEFERRED）
- canonical：**92自治体、1,094 category行、構造化公式葉1,008区分、253公式出典**
- Schema：**v1.2.4**
- Workflow：**v1.19**
- canonical QA：**92 `QA_PASSED` / 0 `QA_REQUIRED`**
- 共通品目：40品目、安全区分付き
- canonical item mapping：**932条件枝**（初期候補段階）
- canonical 40品目coverage：**3,680自治体品目pair**
- canonical category review evidence：**216行**
- Batch 09専用RED TEAM：**PASS**
- canonical structural validation：**PASS**
- Schema v1.2.4 RED TEAM：**PASS**
- `NEXT_BATCH_GATE`：**PASS**
- `APP_READINESS_GATE`：**HOLD**（40品目の品目別公式確認未完了）

CI記録：`docs/research/batch_09_ci_status.txt`

## Batch 09

MASTER範囲はM084〜M093です。M086新庄村をDEFERREDとし、次の9自治体をcanonicalへ統合しました。

- M084 里庄町：10公式葉
- M085 矢掛町：11公式葉
- M087 鏡野町：8公式葉
- M088 勝央町：7公式葉（`OFFICIAL_COUNT_MATCHED`）
- M089 奈義町：2公式葉
- M090 西粟倉村：5公式葉
- M091 久米南町：14公式葉
- M092 美咲町：5公式葉
- M093 吉備中央町：11公式葉

### Batch 09真正性事項

- 里庄町：2025年12月の現行住民向け案内を採用。燃える/燃えない、資源7系統、粗大を保持。
- 矢掛町：公式ページのトップレベル区分を保持し、内部の色・素材分別や「家庭大型ごみ（不燃物）収集」サービスを別categoryとして二重計上しない。
- 鏡野町：資源ごみ親の下に缶・びん・乾電池等・PETの4公式子葉を保持。スプレー缶へ他自治体の穴あけルールを推測追加しない。
- 勝央町：町公式が明示する**7種分別収集**を7のまま保持し、粗大ごみを人工的な8番目へ追加しない。
- 奈義町：`資源ごみ・小型不燃ごみ・有害なごみ`という現行複合収集ラベルを人工的に3箱へ分割しない。
- 西粟倉村：村版令和8年度カレンダーの5収集グループを保持し、委託先美作市の詳細taxonomyへ過剰展開しない。
- 久米南町：資源9細分を公式子葉として保持。スプレー缶は**使い切り、穴を開けない**。
- 美咲町：2026年の全町統一運用を5住民区分として保持。
- 吉備中央町：令和8年度日程表の11公式葉を保持。資源6葉、可燃/不燃粗大、蛍光管を混同しない。

M086新庄村については、地域処理計画や第三者資料から分別区分を補作しません。公式住民向け一次資料本文が取得できるようになれば、固定IDのまま再開できます。

## データ設計の原則

- `rule_status=CURRENT` かつ `ui_role=SORT_BUCKET` の行だけを学習者用の現在の仕分け箱として投影する。
- category completenessは、処理施設側の工程ではなく**住民が排出時に選択する公式分別区分**を基準とする。
- 自治体正式名称は括弧・記号を含め公式表記を保持する。
- `PLANNED` / `RETIRED` をCURRENTへ混入させない。
- 公式URLの存在と、一次資料本文で住民向け全区分を網羅確認できたことを混同しない。
- 複合収集ラベルを、処理上の内部区分だけを理由に人工分割しない。
- 公式区分が教材UIより細かい場合は、投影親＋公式子葉の親子構造で両方を保持し、親を公式葉件数へ二重計上しない。
- 定期収集ラベルではない拠点回収・予約・特殊経路を、公式総数を壊して人工的な独立categoryへ増やさない。
- 危険物の前処理を全国共通化しない。穴あけ必須／不要など逆ルールを自治体ごとに保持する。
- 公式記載がないcategory詳細は`NOT_STATED_IN_CITED_SOURCE`を使い、空欄回避用の汎用文を補作しない。
- 同一自治体内で複数CURRENT体系があり現Schemaで安全に解決できない場合はDEFERREDとする。
- 固定IDはDEFERREDでも削除・再採番しない。
- `APP_READY`はcategory調査完了とは独立し、40品目すべてについてITEM_SPECIFIC公式証拠・coverage・条件枝レビューが揃うまで付与しない。

## 主なディレクトリ

- `data/master/01_municipalities_master.csv`：143自治体固定ID MASTER
- `data/master/02_official_domain_registry.csv`：公式ドメイン・公式導線台帳
- `data/master/04_common_items_master.csv`：共通40品目と教材安全区分
- `data/master/05_deferred_municipalities.csv`：一時実装対象外の固定ID自治体
- `data/research/pilot/`：Pilot 5自治体
- `data/research/batches/batch_01/`〜`batch_09/`：Batch研究bundle
- `data/research/02_categories_master.csv`：canonical分別区分
- `data/research/03_sources_master.csv`：canonical出典
- `data/research/04_municipalities_research.csv`：canonical自治体調査
- `data/research/05_item_mapping_master.csv`：初期品目対応・条件枝
- `data/research/06_qa_log.csv`：機械再計算済みQA
- `data/research/07_item_mapping_coverage.csv`：全完了自治体×40品目の調査状態
- `data/research/08_category_review_evidence.csv`：category completeness公式証拠
- `docs/research/`：Batch QA・CI記録
- `docs/workflow/`：作業フロー履歴（現行 v1.19）
- `scripts/build_batch_*.py`：Batch再生成
- `scripts/red_team_batch_*.py`：Batch専用RED TEAM

## 再現・Gate

```bash
python3 scripts/validate_research.py --batch batch_09 --next-batch-gate
python3 scripts/red_team_batch_09.py
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v12.py
python3 scripts/red_team_operational_category_semantics.py
python3 scripts/check_next_batch_gate.py
```

`NEXT_BATCH_GATE`はcategory研究を次Batchへ進めるためのGateです。`APP_READINESS_GATE`とは分離されており、現時点の`APP_READINESS_GATE=HOLD`は40品目のITEM_SPECIFICレビュー未完了による正常な状態です。
