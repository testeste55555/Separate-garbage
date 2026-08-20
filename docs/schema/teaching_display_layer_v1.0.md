# Teaching / Display Layer v1.0

制定日: 2026-08-20

## 目的

調査正本を保持したまま、授業運用上の品目グループと、学習者投影用の分別ボックスを分離する。

## 3層

### 1. 正本データ層

既存の以下を正本とし、教材都合で統合・改名・削除しない。

- `data/master/04_common_items_master.csv` — 40品目
- `data/research/02_categories_master.csv` — 自治体公式分別区分
- `data/research/04_municipalities_research.csv` — 自治体QA状態
- `data/research/05_item_mapping_master.csv` — 自治体×品目の条件付きmapping

### 2. 教材グループ層

`data/master/06_teaching_item_group_mapping.csv` を追加する。

- 40品目の `internal_item_id` は保持する。
- グループは授業準備・出題管理のためだけに使用する。
- グループ名を自治体公式分別名称の代替として使用しない。
- 例: I018生ごみ・I019ティッシュ・I020おむつは `可燃ごみ系` にまとめるが、品目IDと自治体別mappingは統合しない。

### 3. 学習者投影層

画面の分別ボックスは正本から実行時に抽出する。

抽出条件:

```text
municipality_id = 選択自治体
AND 04_municipalities_research.確認ステータス = QA_PASSED
AND 02_categories_master.ui_role = SORT_BUCKET
AND 02_categories_master.rule_status = CURRENT
```

表示名は必ず `自治体正式名称` とし、`表示順` で並べる。

## 重要な不変条件

1. 全国共通の「燃えるごみ」「燃えないごみ」「資源ごみ」等へ正規化して画面表示しない。
2. `可燃ごみ系` 等の教材グループ名は学習者投影画面の箱にしない。
3. `REFERENCE_ONLY`、`HIDDEN`、`EXCLUDED_NOTICE` は通常の仕分け箱として表示しない。
4. 粗大ごみ、法定リサイクル、メーカー・販売店回収等は、自治体データが `SORT_BUCKET` として定義していない限り通常画面へ人工的に追加しない。
5. 条件分岐・前処理・例外は `05_item_mapping_master.csv` を正とする。
6. 画面表示用区分を手入力の別マスターとして二重管理しない。
7. 調査途中の自治体を学習者選択肢へ出さない。`QA_PASSED` の自治体だけを表示可能とする。

## 学習者画面 v0.1

`app/` に最小実装を置く。

- QA_PASSED自治体だけを自治体選択肢に出す
- 選択自治体の CURRENT / SORT_BUCKET のみ表示
- 自治体正式名称を大きなボックスとして表示
- 投影表示では操作部を隠し、分別ボックスだけを表示

品目カード、教師用正誤判定、外部回収ルート問題は後続実装とする。

## 検証

`scripts/validate_teaching_display_layer.py` で以下を確認する。

- 40品目すべてが教材グループへ1回だけ所属する
- 未知の品目IDを追加していない
- QA_PASSED自治体がMASTER内に存在する
- CURRENT / SORT_BUCKET候補がMASTER内の自治体に属する
- SORT_BUCKETの `自治体正式名称` が空ではない
- 同一自治体内で同一category_idを二重表示しない
- QA_PASSED自治体にCURRENT / SORT_BUCKETが少なくとも1件ある
