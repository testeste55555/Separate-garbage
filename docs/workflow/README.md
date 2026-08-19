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
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.12.txt`：Schema v1.2.4の住民向け運用区分定義を追加した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.13.txt`：**現行版**。Batch 04で現行変更・地域差・詳細表の過剰細分化防止を実地適用

v1.13でもcategory completenessは「住民が排出時に選択する公式分別区分の網羅」です。処理主体が共通でも自治体の住民向け名称を統一せず、現年度変更は旧冊子より優先します。

Batch 04ではM034〜M043の10自治体を追加し、全10自治体が`MANUAL_INDEX_REVIEW / QA_PASSED`です。特に、大山町の令和8年4月廃止区分をCURRENTから除外し、日吉津村では詳細50音表を独立仕分け箱へ過剰展開せず、現在の収集案内に出る7ラベルを主体系としました。

現在は45自治体すべてQA_PASSED、Batch 04 structural validation・canonical validation・Schema v1.2.4 RED TEAM・Batch 04専用RED TEAM・`NEXT_BATCH_GATE`がPASSです。`APP_READINESS_GATE`は40品目の品目別公式確認未完了のためHOLDです。
