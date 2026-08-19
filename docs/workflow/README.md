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
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.11.txt`：Batch 03証拠不足HOLD時の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.12.txt`：**現行版**（Schema v1.2.4）。住民向け運用区分と古い公式ページ＋現年度運用証拠の併用を追加

v1.12ではcategory completenessを「住民が排出時に選択する公式分別区分の網羅」と定義します。由良町は町公式の住民向け分別案内をPRIMARY_INDEX、2026年広報カレンダーをcurrent-operation evidenceとして採用し、5区分を`MANUAL_INDEX_REVIEW / QA_PASSED`としました。処理計画上の資源フローだけを理由に独立SORT_BUCKETへ昇格させません。

現状はBatch 03全10自治体QA_PASSED、構造validation・Schema RED TEAM・Batch 03 RED TEAM・`NEXT_BATCH_GATE`がPASS、`APP_READINESS_GATE`はHOLDです。Batch 04開始可です。
