# app data

Webアプリが直接読み込む加工済みデータを置くディレクトリです。

調査中の生データを直接アプリへ渡さず、QA済みデータから生成します。

想定成果物：

- `app_export.json`
- 自治体別の必要最小限の分別データ
- `item_image_assets.csv`：教材画像と共通品目の対応表
- `item_image_mapping_pilot_top8.csv`：画像10品目とStyle Research active 8自治体の公式分別先Pilot台帳（76 VERIFIED / 4 UNRESOLVED）

品目情報の正本は `data/master/04_common_items_master.csv` です。

Pilotの`VERIFIED`は品目別公式根拠の確認済みを示しますが、条件枝完全性または`APP_READY`を意味しません。

学習者画像仕分けPilotは`VERIFIED`行だけを読み込み、公式下位区分をcategory正本の
CURRENT `SORT_BUCKET`へ投影します。`UNRESOLVED`はUIの正誤判定へ渡しません。

この領域のデータは、教師画面・学習者投映画面での利用を前提にします。
