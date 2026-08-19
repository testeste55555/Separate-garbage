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
- Batch 11：**10自治体完了**（新規DEFERREDなし）
- canonical：**109自治体、1,270 category行、構造化公式葉1,170区分、287公式出典**
- Schema：**v1.2.4**
- Workflow：**v1.21**
- canonical QA：**109 `QA_PASSED` / 0 `QA_REQUIRED`**
- 共通品目：40品目、安全区分付き
- canonical item mapping：**1,085条件枝**（初期候補段階）
- canonical 40品目coverage：**4,360自治体品目pair**
- canonical category review evidence：**250行**
- Batch 11専用RED TEAM：**PASS**
- canonical structural validation：**PASS**
- Schema v1.2.4 RED TEAM：**PASS**
- operational category semantics RED TEAM：**PASS**
- `NEXT_BATCH_GATE`：**PASS**
- `APP_READINESS_GATE`：**HOLD**（40品目の品目別公式確認未完了）

CI記録：`docs/research/batch_11_ci_status.txt`

## Batch 11

MASTER範囲はM106〜M115です。10自治体すべてをcanonicalへ統合しました。

- M106 安芸高田市：11公式葉
- M107 江田島市：8公式葉
- M108 府中町：11公式葉
- M109 海田町：9公式葉
- M110 熊野町：6公式葉
- M111 坂町：13公式葉
- M112 安芸太田町：12公式葉
- M113 北広島町：11公式葉
- M114 大崎上島町：8公式葉
- M115 世羅町：9公式葉

### Batch 11真正性事項

- 安芸高田市：`容器包装類`内部3区分、`燃えないごみ`内部4区分は住民が分類ごとに袋を分けるため公式子葉として保持。スプレー缶は**穴あけ不要**。
- 江田島市：令和8年度改定ポスターを正とし、旧資料の古紙／布類の分割を引き継がない。現行は`資源ごみ（古紙・布類）`を一つの区分として保持し8公式葉。スプレー缶は使い切り必須で、穴を開けずに出す公式経路もある。
- 府中町：`有価物`を投影親、その下の新聞・雑誌・雑がみ／ダンボール／衣類／ビン・缶を公式子葉として保持。
- 海田町：`資源物`の下に缶・金属類／ビン類／紙・布類／ペットボトル／その他の5子葉。スプレー缶は**穴を開けない**。
- 熊野町：現行6区分を保持し、資源物内部の「小分類」を人工的な独立categoryへ増やさない。
- 坂町：`資源ごみ`の下に8住民子葉。スプレー缶は**穴を開ける**。
- 安芸太田町：令和8年版五十音事典に基づき12公式葉。住民が区分ごとに別袋へ分ける子区分を保持。スプレー缶は**穴あけ不要**。
- 北広島町：芸北広域環境施設組合の住民向け体系を保持。地区差は収集日程でありtaxonomy差ではないためDEFERREDにしない。
- 大崎上島町：公式6上位分類を公式葉総数へ流用せず、不燃・資源内部の住民子区分を含め8公式葉。スプレー缶は**穴を開ける**。
- 世羅町：`不燃ごみ`内部の不燃物／発火性危険ごみ／充電式小型家電／電池類／蛍光灯類を別々の袋へ分けるため5子葉を保持。発火性危険ごみは使い切れば**穴あけ不要**。

Batch 11は全自治体を`MANUAL_INDEX_REVIEW`としています。公式上位分類数とresident-facing leaf数を混同しません。

## データ設計の原則

- `rule_status=CURRENT` かつ `ui_role=SORT_BUCKET` の行だけを学習者用の現在の仕分け箱として投影する。
- category completenessは、処理施設側の工程ではなく**住民が排出時に選択する公式分別区分**を基準とする。
- 自治体正式名称は括弧・記号を含め公式表記を保持する。
- `PLANNED` / `RETIRED` をCURRENTへ混入させない。
- 公式URLの存在と、一次資料本文で住民向け全区分を網羅確認できたことを混同しない。
- `OFFICIAL_COUNT_MATCHED`は公式資料が同じ粒度の数値総数を明示する場合だけ使用し、こちらで一覧を数えただけの場合は`MANUAL_INDEX_REVIEW`とする。
- 複合収集ラベルを、処理上の内部区分だけを理由に人工分割しない。
- 住民が別袋・別容器・別排出単位へ分ける公式子区分は、投影親＋公式子葉の親子構造で保持し、親を公式葉件数へ二重計上しない。
- 内部説明上の「小分類」を、自動的に独立categoryへ昇格させない。
- 現行年度の公式資料と旧年度資料が食い違う場合は現行年度を優先する。
- 定期収集ラベルではない拠点回収・予約・特殊経路を、公式総数を壊して人工的な独立SORT_BUCKETへ増やさない。
- 危険物の前処理を全国・県内共通化しない。穴あけ必須／不要など逆ルールを自治体ごとに保持する。
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
- `data/research/batches/batch_01/`〜`batch_11/`：Batch研究bundle
- `data/research/02_categories_master.csv`：canonical分別区分
- `data/research/03_sources_master.csv`：canonical出典
- `data/research/04_municipalities_research.csv`：canonical自治体調査
- `data/research/05_item_mapping_master.csv`：初期品目対応・条件枝
- `data/research/06_qa_log.csv`：機械再計算済みQA
- `data/research/07_item_mapping_coverage.csv`：全完了自治体×40品目の調査状態
- `data/research/08_category_review_evidence.csv`：category completeness公式証拠
- `docs/research/`：Batch QA・CI記録
- `docs/workflow/`：作業フロー履歴（現行 v1.21）
- `scripts/build_batch_*.py`：Batch再生成
- `scripts/red_team_batch_*.py`：Batch専用RED TEAM

## 再現・Gate

```bash
python3 scripts/build_batch_11.py
python3 scripts/validate_research.py --batch batch_11 --next-batch-gate
python3 scripts/red_team_batch_11.py
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v12.py
python3 scripts/red_team_operational_category_semantics.py
python3 scripts/check_next_batch_gate.py
```

`NEXT_BATCH_GATE`はcategory研究を次Batchへ進めるためのGateです。`APP_READINESS_GATE`とは分離されており、現時点の`APP_READINESS_GATE=HOLD`は40品目のITEM_SPECIFICレビュー未完了による正常な状態です。

## 次Batch

Batch 12は**M116 神石高原町〜M125 長門市**の10自治体を基本範囲とします。M116で広島県を完了し、M117から山口県へ入ります。
