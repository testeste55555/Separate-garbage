# Schema v1.0

確定日：2026-08-17  
対象：家庭ごみ分別（収集曜日・時刻・地区別日程を除く）

## A. municipality

自治体単位の公式案内、処理主体、現行性、進捗を保持する。主キーは `municipality_id`。PilotではMASTER固定順の `M001`〜`M143` を使用し、並べ替え後も変更しない。

## B. categories

自治体が使用する正式名称をそのまま保持する。主キーは `(municipality_id, category_id)`。

追加した構造：

- `category_group`: 自治体内の親概念（例：資源）
- `parent_category_id`: 下位区分の親ID
- `classification_level`: PRIMARY / SUBCATEGORY / ALTERNATIVE / EXCLUDED
- `collection_channel`: CURBSIDE / BOOKED_PICKUP / DROP_OFF / DIRECT_HAUL / RETAILER_OR_MAKER / NOT_COLLECTED
- `適用条件`: 汚れ、色、材質、用途等
- `条件外の扱い`: 条件不成立時の正式な分別先
- `サイズ・条件`: 粗大ごみ閾値や袋に入る条件
- `料金ルール`: 指定袋・シール・処理券・搬入料金の具体内容

`粗大ごみ扱いか`、`予約が必要か`、`有料か`、`自治体収集外か` は `TRUE / FALSE / CONDITIONAL / UNKNOWN` の4値とする。不明値は推測しない。

## C. sources

資料単位で公式URL、発行主体、対象年度、更新日、取得確認日、使用範囲、優先度、現行性を保持する。主キーは `(municipality_id, source_id)`。

## 参照整合性

1. categoriesとsourcesの `municipality_id` はmunicipalityに存在する。
2. categoriesの `source_id` は同じ自治体のsourcesに存在する。
3. `parent_category_id` は同じ自治体のcategoryに存在するか空欄。
4. `自治体正式名称` は出典表記を一般名称へ置換しない。
5. QA_PASSEDは一次QA全項目がTRUEで、schema検証が成功した自治体のみ。

