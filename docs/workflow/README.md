# Workflow

- `WORK_ゴミ出し情報収集フロー_143自治体_v1.1.txt`：従来版（履歴として保持）
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.2.txt`：Schema v1.1対応の旧版（Gate判定撤回）
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.3.txt`：Schema v1.2対応の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.4.txt`：Schema v1.2.1対応の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.5.txt`：Schema v1.2.2証拠分離対応の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.6.txt`：初期mapping候補精度修正の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.7.txt`：13自治体網羅性レビューの履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.8.txt`：Schema v1.2.3対応の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.9.txt`：Batch 02初回完了時の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.10.txt`：category詳細真正性Gateを追加した現行版

v1.10ではBatch 02の151 category行を公式source・locatorへ再照合し、公式記載なしを`NOT_STATED_IN_CITED_SOURCE`で表現します。空欄回避用プレースホルダはvalidatorが拒否します。構造validation、25観点RED TEAM、NEXT_BATCH_GATEはPASS、APP_READINESS_GATEはHOLDです。
