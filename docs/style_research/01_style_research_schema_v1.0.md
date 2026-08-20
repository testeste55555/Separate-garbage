# Style Research Schema v1.0

制定日: 2026-08-20

## 目的と境界

自治体が住民向け資料で分別区分を識別するために使用する色を、学習者UIへ安全に接続できる追加レイヤーとして保持する。

次の正本は変更しない。

- `02_categories_master.csv`
- `05_item_mapping_master.csv`
- `06_teaching_item_group_mapping.csv`
- MASTERのmunicipality_id / category_id / 自治体正式名称

通常のstyle投影対象は `rule_status=CURRENT AND ui_role=SORT_BUCKET` だけである。`REFERENCE_ONLY`、`HIDDEN`、`EXCLUDED_NOTICE` は通常箱へ混入させない。

## Stage A後に確定した構造

平坦な「1 category＝1色」表では、指定袋とガイド見出しの併存、共有袋色、地域variantを失う。このため、観測とUI判断を分離する。

### 1. `08_style_color_observations.csv`

公式資料で確認した色を一対多で保持する。主キーは `style_id`。

同じcategory_idに、指定袋、ステーション表示、カレンダー、ポスターの複数観測を持てる。色の用途が異なる観測を上書きしない。

### 2. `08_style_ui_projection.csv`

アプリへ渡す一意の判断を `(municipality_id, district_scope, category_id)` ごとに1行保持する。

選べるのは `semantic_fit=CATEGORY_DISCRIMINATOR` かつ公式statusの観測だけである。共有袋色、装飾色、競合色はPRIMARYにできない。

### 3. `09_style_sources.csv`

既存分別source正本とは独立したstyle調査用出典。地域scope、色の用途、locatorを保持する。

### 4. `03_top10_targets.csv`

固定順位、Stage、canonical状態、調査状態を管理する。順位は再計算しない。

## 地域scope

`district_scope` は必須。

- active正本が市全域一意: `MUNICIPALITY_WIDE`
- 福山市: `CITY_GENERAL` / `UCHIUMI` / `NUMAKUMA`
- 尾道市: `ONOMICHI` / `MUKAISHIMA` / `MITSUGI` / `INNOSHIMA` / `SETODA`
- 複数地域への公式索引: `MUNICIPALITY_MULTISCOPE`

福山市M099と尾道市M098はcategory正本が地域variant対応待ちでDEFERREDである。style層だけで架空category_idを発行せず、地域別sourceを調査済みとして保持する。

## color_status

- `OFFICIAL_CONFIRMED`: 自治体資料が色名またはRGB/HEXを明示。色名のみなら `display_color` は空欄可。
- `OFFICIAL_DERIVED`: 公式PDF・画像等の視覚表現から近似HEXを作成。noteへ近似であることを必須記録。
- `FALLBACK`: アプリ標準色。公式sourceを持たず、公式色と混同しない。
- `NOT_CONFIRMED`: category識別色を確認できない、または複数の意味色を安全に一意化できない。HEXは空欄。

## 色根拠の優先と意味適合

資料優先順位は次のとおり。

1. 指定袋・回収容器・ステーション表示
2. 公式カレンダー・分別ポスター
3. 公式ハンドブック・分別ガイド
4. 公式Webページ

ただし上位根拠でも、同じ袋色が複数categoryで共有される場合は `SHARED_COLLECTION_GROUP` として保持し、category識別用PRIMARYにはしない。曜日色、見出し装飾、紙面地色もPRIMARYにしない。

`semantic_fit`:

- `CATEGORY_DISCRIMINATOR`
- `SHARED_COLLECTION_GROUP`
- `MULTI_METHOD_CATEGORY`
- `NO_SEMANTIC_COLOR`
- `CONFLICTING_EVIDENCE`
- `DECORATIVE_ONLY`

## 複数色・不一致

- 用途が異なる色は `evidence_role` を分けて併存させる。
- 同一用途で現行公式資料が不一致なら全観測を残し、projectionは `NOT_CONFIRMED` とする。
- 投影親の子区分に複数の袋色・方法がある場合、親へ一色を推測しない。

## display / border / text

`display_color` は公式がRGB/HEXを明示した場合だけ `OFFICIAL_CONFIRMED` の数値とする。PDF・画像から得た値は必ず `OFFICIAL_DERIVED`。

`border_color` と `text_color` はアクセシビリティ用のアプリ計算値であり、自治体公式色ではない。validatorは文字コントラスト4.5:1以上を要求する。正式区分名を常に併記し、色を唯一の情報手段にしない。

## 不変条件

1. 色を推測しない。
2. 全国共通色を公式色として流用しない。
3. 空欄回避色を作らない。
4. 近似HEXを自治体公式HEXと呼ばない。
5. category正本をstyle都合で変更しない。
6. 独自アイコンを公式情報として記録しない。
