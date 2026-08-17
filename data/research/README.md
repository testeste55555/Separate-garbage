# Research data

Schema v1.2の調査成果物です。

- `pilot/`：Pilot 5自治体。QA、item mapping、40品目coverageを独立検証します。
- `batches/batch_01/`：Batch 01 10自治体。QA、item mapping、40品目coverageを自身のbundleから検証します。
- `02_categories_master.csv`：15自治体・194区分
- `03_sources_master.csv`：15自治体・57出典
- `04_municipalities_research.csv`：15自治体
- `05_item_mapping_master.csv`：40共通品目に対する初期283条件枝
- `06_qa_log.csv`：15自治体の機械再計算QA（2 PASS / 13 REQUIRED）
- `07_item_mapping_coverage.csv`：15×40=600 pairの完全な調査状態台帳

`data/` 直下の同名CSVと `data/pilot/` はSchema v1.0時点の履歴です。現行処理は `data/master/` と `data/research/` を参照します。

`NOT_RESEARCHED` は不存在を意味しません。`MAPPED_INITIAL` は区分レベルの機械抽出で、品目別公式確認済みではありません。アプリはcoverageと全条件枝がともに `APP_READY` のpairだけを利用してください。
