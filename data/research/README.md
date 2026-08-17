# Research data

Schema v1.1の調査成果物です。

- `pilot/`：Pilot 5自治体。`pilot_qa.csv` を含み、canonical QAから独立して検証します。
- `batches/batch_01/`：Batch 01 10自治体。再構築時もv1.1へ正規化されます。
- `02_categories_master.csv`：15自治体・194区分
- `03_sources_master.csv`：15自治体・57出典
- `04_municipalities_research.csv`：15自治体
- `05_item_mapping_master.csv`：40共通品目に対する初期283条件枝
- `06_qa_log.csv`：15自治体の機械再計算QA

`data/` 直下の同名CSVと `data/pilot/` はSchema v1.0時点の履歴です。現行処理は `data/master/` と `data/research/` を参照します。

item mappingの `INITIAL_REVIEW_REQUIRED` は、品目別公式確認が未完了であることを示します。アプリは `APP_READY` 以外を本番データとして使用しないでください。
