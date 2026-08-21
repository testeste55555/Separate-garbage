# app data

Webアプリが直接読み込む加工済みデータを置くディレクトリです。

調査中の生データを直接アプリへ渡さず、QA済みデータから生成します。

想定成果物：

- `app_export.json`
- 自治体別の必要最小限の分別データ
- `item_image_assets.csv`：教材画像と共通品目の対応表

品目情報の正本は `data/master/04_common_items_master.csv` です。

この領域のデータは、教師画面・学習者投映画面での利用を前提にします。
