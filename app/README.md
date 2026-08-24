# app

自治体別ごみ分別学習Webアプリ本体です。

## 現在の実装: 学習者画像仕分けPilot v0.2

`index.html` を開くと、正本データから次の条件で分別ボックスを実行時抽出します。

- `04_municipalities_research.csv` の `確認ステータス = QA_PASSED`
- `02_categories_master.csv` の `ui_role = SORT_BUCKET`
- `02_categories_master.csv` の `rule_status = CURRENT`
- 選択した `municipality_id`

画面上の箱名は `自治体正式名称` をそのまま使用します。

教材管理用の `可燃ごみ系`、`紙類`、`電池類` 等は投影画面の箱として使用しません。

「投影表示」を押すと操作部分を隠し、選択自治体の分別ボックスだけを全画面表示します。

Style Research active 8自治体では、`item_image_mapping_pilot_top8.csv` の
`VERIFIED` 76組だけを画像問題として表示します。品目画像と今回の条件を確認し、
正式区分名付きの箱を選ぶと正誤と公式ルールの補足を表示します。

- `UNRESOLVED` 4組は出題・正誤判定から除外する。
- M098尾道市・M099福山市は地域variant対応前のため画像問題へ含めない。
- `REFERENCE_ONLY` の公式下位区分はcategory正本の親子関係をたどり、最初の
  CURRENT `SORT_BUCKET`へ投影する。下位区分名は正解後の補足に保持する。
- Style Researchが`OFFICIAL_CONFIRMED` / `OFFICIAL_DERIVED`の箱だけ公式色を使う。
  `NOT_CONFIRMED`は白い標準表示とし、公式色とは表示上も区別する。
- 色だけを唯一の手掛かりにせず、正式名称・枠線・フォーカス表示を併用する。

この画面は条件枝完全性レビュー前のPilotです。`VERIFIED`を`APP_READY`として扱いません。

## データ参照

- `../data/master/01_municipalities_master.csv`
- `../data/research/04_municipalities_research.csv`
- `../data/research/02_categories_master.csv`
- `../data/style_research/08_style_ui_projection.csv`
- `../data/app/item_image_assets.csv`
- `../data/app/item_image_mapping_pilot_top8.csv`

表示用の分別区分を別マスターへ複製しないため、category正本と画面表示が乖離しない構造です。また、調査途中の自治体は選択肢に出しません。
