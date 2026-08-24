# app data

Webアプリが直接読み込む加工済みデータを置くディレクトリです。

調査中の生データを直接アプリへ渡さず、QA済みデータから生成します。

想定成果物：

- `app_export.json`
- 自治体別の必要最小限の分別データ
- `item_image_assets.csv`：教材画像と共通品目の対応表
- `item_image_mapping_pilot_top8.csv`：画像10品目とStyle Research active 8自治体の公式分別先Pilot台帳（76 VERIFIED / 4 UNRESOLVED）
- `lesson_mode_app_ready_scope.csv`：オンライン授業モードで自動正誤判定を有効にするAPP_READY自治体の明示的スコープ

品目情報の正本は `data/master/04_common_items_master.csv` です。

Pilotの`VERIFIED`は品目別公式根拠の確認済みを示しますが、条件枝完全性または`APP_READY`を意味しません。したがって、`VERIFIED`だけでは学習者画面の自動正誤判定を有効にしません。

オンライン授業モードで画像問題を有効にするには、自治体の40共通品目レビューが全条件枝 `COMPLETE` であることと、画像固有mappingが `VERIFIED` であることの両方を要求します。対面授業モードでは画像問題を使用せず、自治体の正式な分別箱を投影します。

この領域のデータは、教師画面・学習者投映画面での利用を前提にします。
