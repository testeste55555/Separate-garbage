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
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.10.txt`：Batch 02 category詳細真正性Gate追加の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.11.txt`：**現行版**。Batch 03と証拠不足時の`NOT_REVIEWED / QA_REQUIRED`保持を追加

v1.11では、公式全区分体系の証拠を取得できない自治体を推測で`QA_PASSED`へ昇格させません。Batch 03は10自治体を研究bundleとして統合し、M023・M024・M025・M026・M027・M029・M031・M032・M033の9自治体は`QA_PASSED`、M028由良町は全区分索引の現行一次資料が未取得のため`NOT_REVIEWED / QA_REQUIRED`です。

現状は構造validation・Schema RED TEAM・Batch 03 RED TEAMがPASS、`NEXT_BATCH_GATE=HOLD`、`APP_READINESS_GATE=HOLD`です。由良町の網羅性証拠を解消するまでBatch 04へ進みません。
