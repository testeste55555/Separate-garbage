# Separate-garbage

自治体ごとの家庭ごみ分別ルールを、授業用アプリで利用できる形へ正規化するプロジェクトです。

中心Can-do：

> 名前が分からないごみでも、自分が住む自治体のルールを調べて、仲間と相談しながら、正しく分別ができる。

収集曜日・収集時間・地区別カレンダーは構造化対象外です。カレンダーは必要に応じて「その分別体系が現在も運用されていること」の現行性証拠として使用します。

## 現在地（2026-08-19）

- MASTER固定ID台帳：**143自治体**
- active実装対象：**141自治体**
- DEFERRED：**2自治体**
  - M065 知夫村：一次資料本文の全区分確認が安定しないため一旦対象外
  - M076 備前市：令和8年度に地区別のCURRENT分別体系が併存し、現Schema/UIでは安全にvariant解決できないため対象外
- Pilot：5自治体完了
- Batch 01〜06：各10自治体完了
- Batch 07：**9自治体完了**（M065をDEFERRED）
- Batch 08：**9自治体完了**（M076をDEFERRED）
- canonical：**83自治体、1,018 category行、構造化公式葉935区分、236公式出典**
- Schema：**v1.2.4**
- Workflow：**v1.18**
- canonical QA：**83 `QA_PASSED` / 0 `QA_REQUIRED`**
- 共通品目：40品目、安全区分付き
- canonical item mapping：**877条件枝**（初期候補段階）
- canonical 40品目coverage：**3,320自治体品目pair**
- canonical category review evidence：**199行**
- Schema v1.2.4 RED TEAM：**25/25 PASS**
- Batch 08専用RED TEAM：**24/24 PASS**
- canonical structural validation：**PASS**
- `NEXT_BATCH_GATE`：**PASS**
- `APP_READINESS_GATE`：**HOLD**（40品目の品目別公式確認未完了）

CI記録：`docs/research/batch_08_ci_status.txt`

## Batch 08

active targetは次の9自治体です。

- M074 高梁市：7公式葉
- M075 新見市：4公式葉
- M077 瀬戸内市：9公式葉
- M078 赤磐市：7公式葉
- M079 真庭市：16公式葉
- M080 美作市：20公式葉
- M081 浅口市：14公式葉
- M082 和気町：12公式葉
- M083 早島町：6公式葉

M076備前市は令和8年度時点で、資源回収ステーション設置済地区の**9種23分別**と未設置地区の旧分別体系が併存しています。これは収集曜日差ではなく分別区分そのもののCORE差なので、自治体全域に片方だけを適用しません。固定IDと調査履歴は保持し、地区variant対応後に再開します。

Batch 08で特に固定した真正性事項：

- 高梁市：かん類のスプレー缶・ガス缶は公式どおり穴あけルールを保持
- 瀬戸内市：令和8年4月開始のプラスチック資源を反映。スプレー缶等は現行火災防止案内を優先し、**中身を完全に出し切る**。旧資料の穴あけ記載を現在必須条件へ昇格させない
- 赤磐市：製品プラスチックを含む現行「プラスチック資源」を保持
- 真庭市：公式の家庭ごみ分別表(1)〜(16)を16公式葉として保持
- 美作市：カレンダー投影親と詳細公式子葉を親子構造で保持。スプレー缶は穴あけ必須
- 浅口市：地域ごとの収集日の組み方と共通の資源11品目taxonomyを混同しない
- 和気町：2026-10-01開始予定の製品プラスチック拡大を`PLANNED / HIDDEN`としてCURRENTから分離
- 早島町：収集シール対象の大型物を人工的な「粗大ごみ」独立categoryにしない

## データ設計の原則

- `rule_status=CURRENT` かつ `ui_role=SORT_BUCKET` の行だけを学習者用の現在の仕分け箱として投影する。
- category completenessは、処理施設側の工程ではなく**住民が排出時に選択する公式分別区分**を基準とする。
- 自治体正式名称は括弧・記号を含め公式表記を保持する。
- `PLANNED` / `RETIRED` をCURRENTへ混入させない。
- 定期収集ラベルではない拠点回収・粗大・予約等は必要に応じ`REFERENCE_ONLY`とする。
- 公式区分が教材UIより細かい場合は投影親＋公式子葉で保持し、親を公式葉件数へ二重計上しない。
- 危険物の前処理を全国共通化しない。穴あけ必須／不要など逆ルールを自治体ごとに保持する。
- 公式記載がないcategory詳細は`NOT_STATED_IN_CITED_SOURCE`を使い、空欄回避用の汎用文を補作しない。
- 公式URLの存在と「全分別区分を網羅確認できたこと」を混同しない。
- 同一自治体内で複数CURRENT体系がある場合、現Schemaで安全に解決できなければDEFERREDとする。
- `APP_READY`はcategory調査完了とは独立し、40品目すべてについてITEM_SPECIFIC公式証拠・coverage・条件枝レビューが揃うまで付与しない。

## 主なディレクトリ

- `data/master/01_municipalities_master.csv`：143固定ID
- `data/master/05_deferred_municipalities.csv`：一時対象外自治体と理由
- `data/research/pilot/`：Pilot
- `data/research/batches/batch_01/`〜`batch_08/`：Batch成果物
- `data/research/02_categories_master.csv`：canonical categories
- `data/research/03_sources_master.csv`：canonical sources
- `data/research/04_municipalities_research.csv`：canonical municipalities
- `data/research/05_item_mapping_master.csv`：初期mapping枝
- `data/research/06_qa_log.csv`：QA
- `data/research/07_item_mapping_coverage.csv`：自治体×40品目coverage
- `data/research/08_category_review_evidence.csv`：category completeness evidence
- `docs/schema/`：Schema / Data Dictionary / RED TEAM
- `docs/workflow/`：Workflow履歴（現行v1.18）

## Batch 08再現

```bash
python3 scripts/build_batch_08_active.py
python3 scripts/fix_batch08_authenticity.py
python3 scripts/validate_research.py --batch batch_08 --next-batch-gate
python3 scripts/red_team_batch_08.py
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v12.py
python3 scripts/red_team_operational_category_semantics.py
python3 scripts/check_next_batch_gate.py
python3 scripts/validate_research.py --app-readiness-gate  # 現状HOLD（rc=2）
```

GitHub Actionsの`.github/workflows/build-batch-08.yml`でも同じ検証を再現します。
