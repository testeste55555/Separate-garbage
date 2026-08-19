# Separate-garbage

自治体ごとの家庭ごみ分別ルールを、授業用アプリで利用できる形へ正規化するプロジェクトです。

中心Can-do：

> 名前が分からないごみでも、自分が住む自治体のルールを調べて、仲間と相談しながら、正しく分別ができる。

収集曜日・収集時間・地区別カレンダーは構造化対象外です。カレンダーは、必要に応じて「その分別体系が現在も運用されていること」の現行性証拠として使用します。

## 現在地（2026-08-19）

- MASTER：143自治体、固定ID済み
- Pilot：5自治体完了
- Batch 01：10自治体完了
- Batch 02：10自治体完了
- Batch 03：10自治体完了
- Batch 04：10自治体完了
- Batch 05：10自治体完了
- Batch 06：10自治体完了
- Batch 07：研究bundle作成済み。**9 `QA_PASSED` / 1 `QA_REQUIRED`（M065 知夫村）**のため未完了
- 正式なcanonical完了値：**65自治体、842 category行（構造化公式葉776区分）、192公式出典**
- Schema：**v1.2.4**
- Workflow：**v1.16**
- canonical QA：**65 `QA_PASSED` / 0 `QA_REQUIRED`**（Batch 06まで）
- Batch 07 bundle QA：**9 `QA_PASSED` / 1 `QA_REQUIRED`**
- 共通品目：40品目、安全区分付き
- canonical item mapping：**755条件枝**（現状は初期候補段階）
- canonical 40品目coverage：**2,600自治体品目pair**
- canonical category review evidence：**156行**
- Schema v1.2.4 RED TEAM：26/26 PASS（Batch 06までの確定状態）
- Batch 03 / 04 / 05 / 06専用RED TEAM：PASS
- `NEXT_BATCH_GATE`：**HOLD**（Batch 07のM065未解決）
- `APP_READINESS_GATE`：**HOLD**（40品目の品目別公式確認未完了）

### Batch 07

対象はMASTER順の `M064〜M073`、西ノ島町・知夫村・隠岐の島町・岡山市・倉敷市・津山市・玉野市・笠岡市・井原市・総社市です。

公式根拠からcategory completenessを確認できた9自治体はbundle内で`QA_PASSED`です。

- M064 西ノ島町：7区分
- M066 隠岐の島町：7区分
- M067 岡山市：6区分
- M068 倉敷市：5区分
- M069 津山市：6区分
- M070 玉野市：9区分
- M071 笠岡市：12区分
- M072 井原市：8区分
- M073 総社市：4区分

M065知夫村は、2026年の村公式案内から現行の「ゴミ・リサイクル」公式ページへ到達することまでは確認しています。しかし今回の取得環境では当該ページ・旧公式分別資料の本文取得が安定せず、住民が排出時に選択する**全分別区分を全件照合できていません**。

そのため、知夫村についてはcategoryを推測で作らず、`category_count_check_status=NOT_REVIEWED / category_count_verified=FALSE / QA_REQUIRED`を維持します。公式URLが存在することだけではcategory completenessの証明にはしません。

Batch 07はこの1自治体が解消するまで完了扱いにせず、Batch 08へ進みません。

### 現行category semantics

Schema v1.2.4では、category completenessを「住民が家庭ごみを排出するときに実際に選択する自治体公式の分別体系」と定義します。処理計画上の資源フローや施設側の分類を、そのまま学習者用の独立仕分け箱へ昇格させません。

公開日が古い公式ページでも、現在も公式公開され、現年度カレンダー・現行公式案内で同じ体系の稼働が確認できればCURRENTとして使用できます。一方、公式ページの所在だけ確認できても全区分本文を読めない場合は`NOT_REVIEWED`のまま止めます。

自治体正式名称は改変せず、括弧・記号等を含め公式表記を保持します。詳細品目表の細分類を無条件で独立箱化せず、定期収集ラベルでない拠点回収等は必要に応じ`REFERENCE_ONLY`とします。

## ディレクトリ

- `data/master/01_municipalities_master.csv`：143自治体MASTER
- `data/master/02_official_domain_registry.csv`：公式・一部事務組合・公式案内外部サービスの根拠
- `data/master/04_common_items_master.csv`：共通40品目と教材安全区分
- `data/research/pilot/`：Pilot 5自治体
- `data/research/batches/batch_01/`〜`batch_06/`：完了Batch
- `data/research/batches/batch_07/`：9 PASSED / 1 REQUIREDの研究bundle
- `data/research/02_categories_master.csv`：統合分別区分（正式完了値はBatch 06まで）
- `data/research/03_sources_master.csv`：統合出典
- `data/research/04_municipalities_research.csv`：統合自治体調査
- `data/research/05_item_mapping_master.csv`：初期品目対応・条件枝
- `data/research/06_qa_log.csv`：機械再計算済みQA
- `data/research/07_item_mapping_coverage.csv`：全自治体×40品目の調査・実装準備状態
- `data/research/08_category_review_evidence.csv`：区分網羅性レビューの複数公式source証拠
- `docs/research/batch_03_qa_report.md`〜`batch_07_qa_report.md`：Batch QA記録
- `docs/schema/`：Schema、Data Dictionary、移行・RED TEAM報告
- `docs/workflow/`：作業フロー履歴（現行 v1.16）
- `scripts/build_batch_03.py`〜`scripts/build_batch_07.py`：再生成用
- `scripts/red_team_batch_03.py`〜`scripts/red_team_batch_07.py`：Batch専用RED TEAM

## 再現コマンド

Batch 06までの確定canonical：

```bash
python3 scripts/validate_pilot.py
python3 scripts/validate_research.py --batch batch_01
python3 scripts/validate_research.py --batch batch_02
python3 scripts/validate_research.py --batch batch_03
python3 scripts/validate_research.py --batch batch_04
python3 scripts/validate_research.py --batch batch_05
python3 scripts/validate_research.py --batch batch_06
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v12.py
python3 scripts/red_team_operational_category_semantics.py
python3 scripts/red_team_batch_03.py
python3 scripts/red_team_batch_04.py
python3 scripts/red_team_batch_05.py
python3 scripts/red_team_batch_06.py
```

Batch 07の研究bundle確認：

```bash
python3 scripts/build_batch_07.py
python3 scripts/validate_research.py --batch batch_07
python3 scripts/red_team_batch_07.py
```

M065が解消するまではBatch 07を完了canonicalへ昇格させず、Batch 08を開始しません。M065解消後にBatch 07を再生成・再validation・RED TEAMし、canonicalへmergeして`NEXT_BATCH_GATE`を再判定します。

## 運用上の重要事項

- `rule_status=CURRENT` かつ `ui_role=SORT_BUCKET` の行だけを、学習者用の現在の仕分け箱として投影します。
- `PLANNED` / `RETIRED` は `HIDDEN` とし、現行ルールへ混入させません。
- `official_verified=TRUE` は公式ドメイン台帳との一致を意味します。外部サービス・一部事務組合は自治体公式ページからの導線も保持します。
- 自治体正式名称は改変しません。
- `ui_role` は独立した教材UI指定です。`collection_channel` や `classification_level` から再推論しません。
- category completenessは、処理工程ではなく**住民が排出時に選択する公式分別区分**を基準にします。
- 公式URLの存在と、全分別区分の網羅性証拠を混同しません。
- 定期収集ラベルでない公式拠点回収等は必要に応じて`REFERENCE_ONLY`で保持します。
- 公式区分が教材UIより細かい場合は、投影親＋公式子葉の親子構造で両方を保持し、親を公式葉件数へ二重計上しません。
- 複数処理区域を持つ自治体では各区域の公式資料を照合し、地域差を推測で統一しません。
- 危険物の前処理は自治体ごとの公式ルールを保持し、穴あけ必須／不要など逆のルールを全国共通化しません。
- 複合収集ラベルは、処理上の都合だけで人工的に分割しません。
- `危険有害`・`収集しない物`はQA情報列として保持しますが、独立categoryを持たない自治体へ人工的な区分追加を強制しません。
- 危険物・収集不可品の最終判断は、40品目のitem-level `APP_READY`でITEM_SPECIFICな公式証拠を必須にします。
- 袋・容器、収集経路、粗大・予約・料金はREFERENCEです。分類結果に影響する条件だけCORE側へ記録します。
- 空URLは「確認済み・不存在」ではありません。任意機能は `CHECKED_PRESENT / CHECKED_ABSENT / NOT_CHECKED` と証跡を保持します。
- municipalitiesの `確認ステータス` はQAログから自動同期する読取専用ミラーです。
- `OFFICIAL_COUNT_MATCHED` は公式総数を必須とし、`MANUAL_INDEX_REVIEW` は `reviewed_category_count` と公式目次・住民向け区分の照合証跡を必須とします。
- 区分網羅性を証明できない場合は `NOT_REVIEWED / QA_REQUIRED` のまま止め、推測でQA_PASSEDへ昇格させません。
- 区分網羅性の複数sourceは `category_review_evidence` へ正規化します。
- item mappingは不変な `mapping_id` を条件枝の主キーにし、同じ品目・同じ分別先でも異なる条件枝を複数行で保持します。
- mappingの `category_source_*` は区分体系の根拠、`item_evidence_*` は品目別判断の根拠です。
- 初期mapping候補は `自治体正式名称` と `代表品目` だけをPositive evidenceとして生成します。
- category詳細に公式記載がない場合は `NOT_STATED_IN_CITED_SOURCE` を使います。空欄回避用プレースホルダはvalidatorが拒否します。
- `APP_READY` は40品目coverage、品目別公式証跡、全条件枝レビューが揃わない限りvalidatorが拒否します。
