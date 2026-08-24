# app

自治体別ごみ分別学習Webアプリ本体です。

## 学習者投影画面

`index.html` では、自治体の正本データから `QA_PASSED`・`CURRENT`・`SORT_BUCKET` の分別箱を実行時に抽出します。箱名は自治体の `自治体正式名称` をそのまま使用し、Style Researchで公式色を確認できた区分だけ公式色を適用します。

### 授業モード

- **対面授業**：自治体の分別箱のみを投影します。教師が実物のごみを提示して授業を進めます。
- **オンライン授業**：画像問題を表示し、学習者が分別箱を選択すると ○ / × を表示します。

ここでいうオンライン／対面は**授業形態**です。ネットワーク接続状態による切替ではありません。

### 自動正誤判定の安全境界

自動正誤判定は、40共通品目の全条件枝レビューが `COMPLETE` となった **APP_READY自治体**だけで有効にします。

現在の対象：

- M094 広島市
- M095 呉市
- M104 東広島市

画像ごとの出題先は `item_image_mapping_pilot_top8.csv` の画像固有mappingを利用しますが、`VERIFIED` だけでは正誤判定を有効化しません。対応する自治体・品目がAPP_READYレビューを通過していることを追加条件にします。

### 学習者画面に出さない情報

画像問題では、次を学習者画面に表示しません。

- 品目名
- 条件文
- 前処理
- 例外説明
- 正解区分の解説

表示する中心要素は **画像・自治体の分別箱・○/×判定**です。詳細情報は教師用データとして保持します。

## 主なデータ参照

- `../data/master/01_municipalities_master.csv`
- `../data/research/04_municipalities_research.csv`
- `../data/research/02_categories_master.csv`
- `../data/style_research/08_style_ui_projection.csv`
- `../data/app/item_image_assets.csv`
- `../data/app/item_image_mapping_pilot_top8.csv`
- `../data/app/lesson_mode_app_ready_scope.csv`
- `../data/research/app_readiness/m094_item_review.csv`
- `../data/research/app_readiness/m095_item_review.csv`
- `../data/research/app_readiness/m104_item_review.csv`

表示用データを別正本へ複製せず、category正本・APP readinessレビュー・画像mappingを読み取り専用で組み合わせる構造です。
