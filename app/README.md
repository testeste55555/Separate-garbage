# app

自治体別ごみ分別学習Webアプリ本体です。

## 現在の実装: 学習者投影画面 v0.1

`index.html` を開くと、正本データから次の条件で分別ボックスを実行時抽出します。

- `04_municipalities_research.csv` の `確認ステータス = QA_PASSED`
- `02_categories_master.csv` の `ui_role = SORT_BUCKET`
- `02_categories_master.csv` の `rule_status = CURRENT`
- 選択した `municipality_id`

画面上の箱名は `自治体正式名称` をそのまま使用します。

教材管理用の `可燃ごみ系`、`紙類`、`電池類` 等は投影画面の箱として使用しません。

「投影表示」を押すと操作部分を隠し、選択自治体の分別ボックスだけを全画面表示します。

## データ参照

- `../data/master/01_municipalities_master.csv`
- `../data/research/04_municipalities_research.csv`
- `../data/research/02_categories_master.csv`

表示用の分別区分を別マスターへ複製しないため、category正本と画面表示が乖離しない構造です。また、調査途中の自治体は選択肢に出しません。
