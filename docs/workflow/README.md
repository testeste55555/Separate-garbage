# Workflow

- `WORK_ゴミ出し情報収集フロー_143自治体_v1.1.txt`：従来版（履歴として保持）
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.2.txt`：Schema v1.1対応の旧版（Gate判定撤回）
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.3.txt`：Schema v1.2対応の現行版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.4.txt`：Schema v1.2.1対応の現行版

v1.3までの単一Gate設計は撤回します。v1.4は `NEXT_BATCH_GATE` と `APP_READINESS_GATE` を分離します。現時点は構造validationとRED TEAMがPASS、両GateはHOLDです。次バッチ以降はv1.4を使用し、本修正作業ではBatch 02の自治体調査を開始していません。
