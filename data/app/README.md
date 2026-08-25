# app data

Webアプリが直接読み込む加工済みデータを置くディレクトリです。

調査中の生データを直接アプリへ渡さず、QA済みデータから生成します。

想定成果物：

- `app_export.json`
- 自治体別の必要最小限の分別データ
- `item_image_assets.csv`：教材画像と共通品目の対応表
- `item_image_mapping_pilot_top8.csv`：画像10品目とStyle Research active 8自治体の公式分別先Pilot台帳（76 VERIFIED / 4 UNRESOLVED）
- `lesson_mode_app_ready_scope.csv`：オンライン授業モードで自動正誤判定を有効にする`APP_READY`／`LESSON_READY_10`自治体の明示的スコープ（歴史的ファイル名を維持）

品目情報の正本は `data/master/04_common_items_master.csv` です。

Pilotの`VERIFIED`だけでは学習者画面の自動正誤判定を有効にしません。`branch_completeness_confirmed=TRUE`、明示的lesson scope、画像固有mappingの`VERIFIED`をすべて要求します。

オンライン授業モードで画像問題を有効にする経路は2つです。

- `APP_READY`：40共通品目の全条件枝が`COMPLETE`
- `LESSON_READY_10`：固定画像10品目の全条件枝が`COMPLETE`で、各品目に画像と一致するscoring branchがちょうど1つ

後者は40品目`APP_READY`への昇格ではなく、残り30品目を未完了のまま明示します。対面授業モードでは画像問題を使用せず、自治体の正式な分別箱を投影します。

この領域のデータは、教師画面・学習者投映画面での利用を前提にします。
