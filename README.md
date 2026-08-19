# Separate-garbage

自治体ごとの家庭ごみ分別ルールを、授業用アプリで利用できる形へ正規化するプロジェクトです。

中心Can-do：

> 名前が分からないごみでも、自分が住む自治体のルールを調べて、仲間と相談しながら、正しく分別ができる。

収集曜日・収集時間・地区別カレンダーは構造化対象外です。カレンダーは必要に応じて「その分別体系が現在も運用されていること」や地域差を確認する証拠として使用します。

## 現在地（2026-08-19）

- MASTER固定ID台帳：**143自治体**
- active実装対象：**137自治体**
- DEFERRED：**6自治体**
  - M065 知夫村：公式一次資料本文の全区分確認が安定しないため一旦対象外
  - M076 備前市：地区別CURRENT分別体系が併存
  - M086 新庄村：公式一次資料本文を安定取得できず全区分を全件照合できない
  - M098 尾道市：尾道・向島・御調・因島・瀬戸田で住民向けCURRENT体系が併存
  - M099 福山市：市内一般・内海町・沼隈町で住民向け分別単位に差
  - M100 府中市：府中地区と上下地区で資源ごみの住民向け表示単位・正式名称に差
- Pilot：5自治体完了
- Batch 01〜06：各10自治体完了
- Batch 07：**9自治体完了**（M065をDEFERRED）
- Batch 08：**9自治体完了**（M076をDEFERRED）
- Batch 09：**9自治体完了**（M086をDEFERRED）
- Batch 10：**7自治体完了**（M098・M099・M100をDEFERRED）
- canonical：**99自治体、1,159 category行、構造化公式葉1,072区分、270公式出典**
- Schema：**v1.2.4**
- Workflow：**v1.20**
- canonical QA：**99 `QA_PASSED` / 0 `QA_REQUIRED`**
- 共通品目：40品目、安全区分付き
- canonical item mapping：**990条件枝**（初期候補段階）
- canonical 40品目coverage：**3,960自治体品目pair**
- canonical category review evidence：**233行**
- Batch 10専用RED TEAM：**PASS**
- canonical structural validation：**PASS**
- Schema v1.2.4 RED TEAM：**PASS**
- `NEXT_BATCH_GATE`：**PASS**
- `APP_READINESS_GATE`：**HOLD**（40品目の品目別公式確認未完了）

CI記録：`docs/research/batch_10_ci_status.txt`

## Batch 10

MASTER範囲はM095〜M105です。M102庄原市は既に完了済みです。

canonicalへ統合したactive自治体：

- M095 呉市：7公式葉
- M096 竹原市：5公式葉
- M097 三原市：10公式葉（`OFFICIAL_COUNT_MATCHED`）
- M101 三次市：9公式葉
- M103 大竹市：12公式葉
- M104 東広島市：11公式葉
- M105 廿日市市：10公式葉

### Batch 10真正性事項

- 呉市：令和8年4月開始の`プラスチック資源`を反映。7収集ラベルは一覧全件照合による`MANUAL_INDEX_REVIEW`とし、別粒度の「6つの大分類」を数値総数として流用しない。
- 竹原市：5区分。スプレー缶は中身を使い切り、**穴あけ不要**。
- 三原市：市公式が「家庭ごみの分別方法は10分別」と明記。発火性・有害ごみ内部4分別を独立葉として保持し、発火性危険ごみは**穴あけ不要**。
- 三次市：定期収集9区分を保持し、リユース本・小型家電等の別経路を人工的な追加categoryにしない。
- 大竹市：8ステーション区分＋粗大・有害・電池類・せん定枝の4特殊経路を保持。スプレー缶へ他自治体の穴あけルールを推測追加しない。
- 東広島市：`リサイクルプラ`と`その他プラ`、`危険ごみ`と`有害ごみ`、新聞と雑誌等を混同しない。
- 廿日市市：6種10分別の構造を保持。`資源ごみ`を投影親、その下の資源(1)〜(5)を公式子葉とし親を二重計上しない。スプレー缶は穴あけ不要、PETのふた・ラベルは燃やせるごみ。

### Batch 10 DEFERRED

M098尾道市・M099福山市・M100府中市は、令和8年度に同一自治体内で地域別の住民向けCURRENT分別体系・表示単位が併存します。

これは単なる収集曜日差ではなく、resident-facing category COREまたは正式名称に地域差があるため、現行のmunicipality単位Schema/UIで一つの市全域taxonomyへ潰しません。固定IDと根拠を保持し、将来`district_scope`等の地域variant対応後に再開します。

## データ設計の原則

- `rule_status=CURRENT` かつ `ui_role=SORT_BUCKET` の行だけを学習者用の現在の仕分け箱として投影する。
- category completenessは、処理施設側の工程ではなく**住民が排出時に選択する公式分別区分**を基準とする。
- 自治体正式名称は括弧・記号を含め公式表記を保持する。
- `PLANNED` / `RETIRED` をCURRENTへ混入させない。
- 公式URLの存在と、一次資料本文で住民向け全区分を網羅確認できたことを混同しない。
- `OFFICIAL_COUNT_MATCHED`は公式資料が数値総数を明示する場合だけ使用し、こちらで一覧を数えただけの場合は`MANUAL_INDEX_REVIEW`とする。
- 複合収集ラベルを、処理上の内部区分だけを理由に人工分割しない。
- 公式区分が教材UIより細かい場合は、投影親＋公式子葉の親子構造で両方を保持し、親を公式葉件数へ二重計上しない。
- 定期収集ラベルではない拠点回収・予約・特殊経路を、公式総数を壊して人工的な独立SORT_BUCKETへ増やさない。
- 危険物の前処理を全国共通化しない。穴あけ必須／不要など逆ルールを自治体ごとに保持する。
- 公式記載がないcategory詳細は`NOT_STATED_IN_CITED_SOURCE`を使い、空欄回避用の汎用文を補作しない。
- 同一自治体内で複数CURRENT体系があり、住民の地域を現Schemaで安全に解決できない場合はDEFERREDとする。
- 固定IDはDEFERREDでも削除・再採番しない。
- `APP_READY`はcategory調査完了とは独立し、40品目すべてについてITEM_SPECIFIC公式証拠・coverage・条件枝レビューが揃うまで付与しない。

## 主なディレクトリ

- `data/master/01_municipalities_master.csv`：143自治体固定ID MASTER
- `data/master/02_official_domain_registry.csv`：公式ドメイン・公式導線台帳
- `data/master/04_common_items_master.csv`：共通40品目と教材安全区分
- `data/master/05_deferred_municipalities.csv`：一時実装対象外の固定ID自治体
- `data/research/pilot/`：Pilot 5自治体
- `data/research/batches/batch_01/`〜`batch_10/`：Batch研究bundle
- `data/research/02_categories_master.csv`：canonical分別区分
- `data/research/03_sources_master.csv`：canonical出典
- `data/research/04_municipalities_research.csv`：canonical自治体調査
- `data/research/05_item_mapping_master.csv`：初期品目対応・条件枝
- `data/research/06_qa_log.csv`：機械再計算済みQA
- `data/research/07_item_mapping_coverage.csv`：全完了自治体×40品目の調査状態
- `data/research/08_category_review_evidence.csv`：category completeness公式証拠
- `docs/research/`：Batch QA・CI記録
- `docs/workflow/`：作業フロー履歴（現行 v1.20）
- `scripts/build_batch_*.py`：Batch再生成
- `scripts/red_team_batch_*.py`：Batch専用RED TEAM

## 再現・Gate

```bash
python3 scripts/build_batch_10_active.py
python3 scripts/validate_research.py --batch batch_10 --next-batch-gate
python3 scripts/red_team_batch_10.py
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v12.py
python3 scripts/red_team_operational_category_semantics.py
python3 scripts/check_next_batch_gate.py
```

`NEXT_BATCH_GATE`はcategory研究を次Batchへ進めるためのGateです。`APP_READINESS_GATE`とは分離されており、現時点の`APP_READINESS_GATE=HOLD`は40品目のITEM_SPECIFICレビュー未完了による正常な状態です。
