# Schema管理

Schema v1.0はPilot時点の履歴として `docs/07_schema_v1.0.md` と `docs/08_data_dictionary_v1.0.md` に保持しています。

2026-08-17にv1.1を作成後、拡張性RED TEAMの指摘を反映してv1.2へ改訂し、追加RED TEAMの3件をv1.2.1で修正しました。v1.0〜v1.2成果物は履歴として保持します。

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

今後の調査はv1.2.1を使用します。`NEXT_BATCH_GATE` と `APP_READINESS_GATE` は別判定です。2026-08-17時点では前者もHOLDのため、Batch 02は開始していません。
