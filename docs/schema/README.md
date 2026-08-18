# Schema管理

Schema v1.0はPilot時点の履歴として `docs/07_schema_v1.0.md` と `docs/08_data_dictionary_v1.0.md` に保持しています。

2026-08-17にv1.1を作成後、拡張性RED TEAMを反映してv1.2、v1.2.1へ改訂しました。追加RED TEAMで判明した網羅性レビューと品目証拠の矛盾をv1.2.2で修正し、2026-08-18に同Schemaの初期mapping候補生成精度を修正しました。旧版は履歴として保持します。

- `07_schema_v1.1.md`：テーブル構成、状態管理、参照・投影規則
- `08_data_dictionary_v1.1.md`：列単位の型、必須性、列挙値
- `schema_v1.1_migration_report.md`：既存15自治体の移行・再validation結果
- `schema_v1.1_red_team_report.md`：v1.1時点の結果（後続RED TEAMによりGate判定撤回）
- `09_schema_v1.2.md`：拡張可能な状態・Gate・mapping coverage設計
- `10_data_dictionary_v1.2.md`：v1.2追加列・enum・必須性
- `schema_v1.2_migration_report.md`：既存15自治体の非破壊移行結果
- `schema_v1.2_red_team_report.md`：バッチ数非依存RED TEAM結果
- `11_schema_v1.2.1.md`：QA状態一元化、6成果物判定、条件枝identity、Gate分離
- `12_data_dictionary_v1.2.1.md`：v1.2.1で明確化した列・キー・Gate
- `schema_v1.2.1_migration_report.md`：既存15自治体の同期・冪等移行結果
- `schema_v1.2.1_red_team_report.md`：15観点RED TEAM結果
- `13_schema_v1.2.2.md`：手動目次照合とcategory/item証拠分離
- `14_data_dictionary_v1.2.2.md`：追加・名称変更列とvalidation規則
- `schema_v1.2.2_migration_report.md`：既存15自治体の非破壊移行結果
- `schema_v1.2.2_mapping_candidate_fix_report.md`：Positive/Negative evidence分離と偽陽性除去結果
- `schema_v1.2.2_red_team_report.md`：19観点RED TEAM結果

今後の調査はv1.2.2を使用します。2026-08-18時点では13自治体の実資料レビューを開始できる基盤まで修正済みですが、レビュー自体は未実施で `NEXT_BATCH_GATE` はHOLDです。Batch 02も開始していません。
