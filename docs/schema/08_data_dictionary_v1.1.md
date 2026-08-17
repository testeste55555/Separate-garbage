# Data Dictionary v1.1

確定日：2026-08-17

表中の必須性は `必須`、`条件付き`、`任意`、`REFERENCE` で示します。

## municipalities

| 列 | 型・列挙 | 必須性 | 説明 |
|---|---|---|---|
| municipality_id | string | 必須 | MASTER固定ID |
| 都道府県 / 市町村 / 実装区分 | string | 必須 | MASTERと一致 |
| ごみ処理主体 | string | 必須 | 自治体・一部事務組合等 |
| 自治体ごみトップURL | HTTPS URL | 必須 | 公式ごみトップ |
| 分別ガイドURL | HTTPS URL | 必須 | 主要な現行根拠 |
| 品目検索URL | HTTPS URL | 任意 | 公式または公式案内サービス |
| やさしい日本語URL | HTTPS URL | 任意 | 未提供は空欄 |
| 多言語資料URL | HTTPS URL | 任意 | 未提供は空欄 |
| 対象年度 | string | 必須 | 資料の年度・現行性 |
| 最終確認日 | date | 必須 | YYYY-MM-DD |
| 確認ステータス | enum | 必須 | 調査進捗 |
| 備考 | string | 任意 | 主体分担・版差等 |
| official_category_count | integer | 条件付き | 公式が総数を明示した場合 |
| category_count_basis | string | 必須 | 全区分確認の根拠 |
| category_count_verified | boolean | 必須 | QA_PASSEDはTRUE |

## categories

| 列 | 型・列挙 | 必須性 | 説明 |
|---|---|---|---|
| municipality_id | string | 必須 | municipality参照 |
| category_id | string | 必須 | 自治体内で一意 |
| 自治体正式名称 | string | 必須 | 公式表記 |
| category_group | string | 必須 | 親概念。親概念がなければ正式名称と同値 |
| parent_category_id | string | 条件付き | 同一自治体の親category |
| classification_level | enum | 必須 | PRIMARY / SUBCATEGORY / ALTERNATIVE / EXCLUDED |
| 表示順 | integer | 必須 | 自治体内の順序 |
| collection_channel | enum | REFERENCE | CURBSIDE / BOOKED_PICKUP / DROP_OFF / DIRECT_HAUL / RETAILER_OR_MAKER / NOT_COLLECTED |
| 代表品目 | string | 必須 | 代表例。全品目辞典ではない |
| 入れてはいけない物 | string | 必須 | 除外品または該当なしの明示 |
| 適用条件 | string | 条件付き | 材質・用途・汚れ・地域等 |
| 条件外の扱い | string | 必須 | 条件不成立時の分別先または該当なし |
| 出す前の処理 | string | 必須 | 洗浄・分解・絶縁等 |
| 袋・容器のルール | string | 必須 | 指定袋・透明袋・結束等 |
| サイズ・条件 | string | 条件付き | 寸法・重量・袋収容条件 |
| 粗大ごみ扱いか | enum | REFERENCE | TRUE / FALSE / CONDITIONAL / UNKNOWN |
| 予約が必要か | enum | REFERENCE | 同上 |
| 有料か | enum | REFERENCE | 同上 |
| 料金ルール | string | REFERENCE | 課金方法 |
| 自治体収集外か | enum | 必須 | TRUE / FALSE / CONDITIONAL / UNKNOWN |
| 注意事項 | string | 任意 | 安全・代替経路等 |
| source_id | string | 必須 | sources参照 |
| 出典URL | HTTPS URL | 必須 | 公式根拠URL |
| 出典ページ・該当箇所 | string | 必須 | 見出し・ページ |
| 確認日 | date | 必須 | YYYY-MM-DD |
| ui_role | enum | 必須 | SORT_BUCKET / REFERENCE_ONLY / HIDDEN / EXCLUDED_NOTICE |
| rule_status | enum | 必須 | CURRENT / PLANNED / RETIRED |
| effective_from | date | 条件付き | PLANNEDでは必須 |
| effective_to | date | 条件付き | RETIREDでは必須 |

## sources

従来13列は保持します。追加列は以下です。

| 列 | 型・列挙 | 必須性 | 説明 |
|---|---|---|---|
| official_verified | boolean | 必須 | QA_PASSED根拠はTRUE |
| official_basis | enum | 必須 | MUNICIPAL_DOMAIN / INTERMUNICIPAL_AUTHORITY_DOMAIN / MUNICIPAL_LINKED_SERVICE |
| official_linking_url | HTTPS URL | 条件付き | 外部サービスの場合の自治体公式導線 |

`現行性` は `現行`, `現行案内中`, `施行予定`, `終了` を使用します。

## official_domain_registry

| 列 | 型 | 必須性 | 説明 |
|---|---|---|---|
| municipality_id | string | 必須 | MASTER参照 |
| host | hostname | 必須 | 完全一致で検証するhost |
| authority_type | enum | 必須 | sourceのofficial_basisと同じ3値 |
| authority_name | string | 必須 | 運営主体 |
| verification_url | HTTPS URL | 必須 | 公式性または公式導線の根拠 |
| verified_date | date | 必須 | YYYY-MM-DD |
| notes | string | 任意 | 主体関係等 |

## common_items

| 列 | 型・列挙 | 必須性 | 説明 |
|---|---|---|---|
| internal_item_id | string | 必須 | I001形式 |
| 一般管理用名称 | string | 必須 | 内部の標準名 |
| 教材表示名 | string | 必須 | 学習者向け表示 |
| 品目グループ | string | 必須 | 教材グループ |
| 確認ポイント | string | 必須 | 分別条件の観察点 |
| handling_safety | enum | 必須 | SAFE_REAL / EMPTY_CLEAN_ONLY / TEACHER_ONLY / MOCK_ONLY |
| safety_note | string | 必須 | 教材運用時の注意 |
| selection_status | enum | 必須 | 選定状態 |
| 表示順 | integer | 必須 | 教材内順序 |

## item_mapping

| 列 | 型・列挙 | 必須性 | 説明 |
|---|---|---|---|
| mapping_id | string | 必須 | 一意ID |
| municipality_id | string | 必須 | municipality参照 |
| internal_item_id | string | 必須 | common item参照 |
| branch_order | integer | 必須 | 同一自治体・品目内の条件枝順 |
| 自治体での品目表記 | string | 必須 | 公式確認後は公式表記 |
| category_id / 分別区分正式名称 | string | 必須 | category参照と照合用名称 |
| 条件 / 前処理 / 例外分別先 | string | 必須 | 条件分岐を復元する情報 |
| 自治体収集外 | enum | 必須 | categoryと一致 |
| rule_status / effective_from / effective_to | enum/date | 必須・条件付き | categoryと一致 |
| source_id / 出典URL / 出典ページ・該当箇所 / 確認日 | string/URL/date | 必須 | categoryの根拠と一致 |
| mapping_status | enum | 必須 | INITIAL_REVIEW_REQUIRED / VERIFIED / APP_READY |
| 備考 | string | 任意 | 自動抽出・確認状態等 |

## qa

必須QA項目はTRUE/FALSEです。任意機能は `確認済み` と `存在` を分離し、存在はTRUE/FALSEで明示します。`粗大ごみ` は TRUE / FALSE / NOT_APPLICABLE。`確認ステータス` は機械再計算した必須条件がすべてTRUEの場合のみ `QA_PASSED` です。
