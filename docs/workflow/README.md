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
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.14.txt`：Batch 05で鳥取県残自治体と島根県主要市へ住民向け区分semanticsを展開した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.15.txt`：Batch 06で広域処理主体・公式親子区分・逆方向の危険物前処理・複合収集ラベルを実地適用した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.16.txt`：Batch 07証拠不足HOLD時の履歴版。「公式URLの所在確認」と「全分別区分の網羅性証明」を分離
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.17.txt`：**現行版**。固定IDとactive targetを分離し、M065知夫村をDEFERREDとしてBatch 07を9自治体で完了

Batch 07はM064・M066〜M073の9自治体で完了しました。9自治体すべて`QA_PASSED`です。M065知夫村は2026-08-19のユーザー判断で一旦実装対象外とし、`data/master/05_deferred_municipalities.csv`に記録しています。固定IDは保持するため、後日M065のまま再開できます。

Batch 07のCIはstructural validation・専用RED TEAM・canonical merge・canonical validation・Schema v1.2.4 RED TEAM・`NEXT_BATCH_GATE`までPASSしています。

現在のcanonicalは74自治体、910 category行（構造化公式葉840区分）、216公式出典、797 mapping条件枝、2,960 coverage pair、180 category review evidenceです。`NEXT_BATCH_GATE=PASS`のため次Batchへ進行可能です。`APP_READINESS_GATE`は40品目の品目別公式確認未完了のためHOLDです。
