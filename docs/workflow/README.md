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
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.13.txt`：Batch 04で現行変更・地域差・詳細表の過剰細分化防止を実地適用した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.14.txt`：**現行版**。Batch 05で鳥取県残自治体と島根県主要市へ住民向け区分 semantics を展開

v1.14でもcategory completenessは「住民が排出時に選択する公式分別区分の網羅」です。定期収集箱ではない公式拠点回収等は`REFERENCE_ONLY`として保持し、学習者用SORT_BUCKETと区別します。

Batch 05ではM044〜M053の10自治体を追加し、全10自治体が`MANUAL_INDEX_REVIEW / QA_PASSED`です。日南町は公式26種類を縮約せず保持、松江市は親「資源」の二重計上を避け、浜田市は終了済み古着収集を復活させず、大田市は資源物A/B/Cの住民向けグループを保持しました。

現在は55自治体すべてQA_PASSED、Batch 05 structural validation・canonical validation・Schema v1.2.4 RED TEAM・Batch 05専用RED TEAM・`NEXT_BATCH_GATE`がPASSです。`APP_READINESS_GATE`は40品目の品目別公式確認未完了のためHOLDです。
