# Workflow

- `WORK_ゴミ出し情報収集フロー_143自治体_v1.1.txt`：従来版（履歴として保持）
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.2.txt`：Schema v1.1対応の旧版（Gate判定撤回）
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.3.txt`：Schema v1.2対応の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.4.txt`：Schema v1.2.1対応の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.5.txt`：Schema v1.2.2証拠分離対応の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.6.txt`：初期mapping候補精度修正の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.7.txt`：13自治体網羅性レビューの履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.8.txt`：Schema v1.2.3対応の現行版

v1.8ではQA確認日を最新根拠日から導出し、区分網羅性の複数sourceを7番目のBatch成果物へ正規化しました。石巻市の公式19分別はあきびん4子区分として保持し、教材UIは親1箱へ投影します。構造validationと23観点RED TEAM、NEXT_BATCH_GATEはPASS、APP_READINESS_GATEはHOLDです。Batch 02は未開始です。
