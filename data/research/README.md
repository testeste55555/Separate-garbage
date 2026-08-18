# Research data

Schema v1.2.3の調査成果物です。

- `pilot/`：Pilot 5自治体。QA、item mapping、40品目coverageを独立検証します。
- `batches/batch_01/`：Batch 01 10自治体。QA、item mapping、40品目coverageを自身のbundleから検証します。
- `batches/batch_02/`：Batch 02 10自治体。公式目次を全件照合し、7成果物を独立検証します。
- `02_categories_master.csv`：25自治体・356 category行（公式葉区分325）
- `03_sources_master.csv`：25自治体・86出典
- `04_municipalities_research.csv`：25自治体
- `05_item_mapping_master.csv`：40共通品目に対する初期397条件枝
- `06_qa_log.csv`：25自治体の機械再計算QA（25 PASS / 0 REQUIRED）
- `07_item_mapping_coverage.csv`：25×40=1,000 pairの完全な調査状態台帳
- `08_category_review_evidence.csv`：25自治体・50件の区分網羅性公式証拠

`data/` 直下の同名CSVと `data/pilot/` はSchema v1.0時点の履歴です。現行処理は `data/master/` と `data/research/` を参照します。

`NOT_RESEARCHED` は不存在を意味しません。`MAPPED_INITIAL` は区分レベルの機械抽出で、品目別公式確認済みではありません。アプリはcoverageと全条件枝がともに `APP_READY` のpairだけを利用してください。

初期候補生成は `自治体正式名称` と `代表品目` だけをPositive evidenceとして使用します。除外品、条件外、前処理、注意事項への語の出現は候補生成根拠にしません。複合語collision guardを含む40品目テストを通過した候補だけを `MAPPED_INITIAL` とします。

municipalitiesの `確認ステータス` は同一bundleのQAログから毎回自動同期します。QAの確認日は自治体・category・source・網羅性レビューの最新根拠日から導出します。現在は25 `QA_PASSED` / 0 `QA_REQUIRED` です。

item mappingの主キーは `mapping_id` です。同一 `(municipality_id, internal_item_id, category_id)` に複数の条件枝を許可し、merge/reconciliationも `mapping_id` で識別します。`branch_order` は同一自治体・品目内の表示順です。

区分網羅性は、公式総数一致なら `official_category_count`、公式総数がない手動目次照合なら `reviewed_category_count` を使用します。複数sourceは `08_category_review_evidence.csv` に正規化します。公式件数はCURRENTの公式葉区分を数え、教材UI投影親を重複計上しません。

mappingの `category_source_id/url/locator` はcategory行と一致する区分根拠です。`item_evidence_source_id/url/locator` は品目別の公式根拠で、categoryとは異なる公式品目辞典・注意ページを参照できます。coverageの同名3列も品目別根拠専用で、未調査・機械抽出行は空欄です。
