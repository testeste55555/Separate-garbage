# Data Dictionary v1.0

## municipality

| 項目 | 型 | 必須 | 説明 |
|---|---|---:|---|
| municipality_id | string | ○ | MASTER固定ID（M001形式） |
| 都道府県 | string | ○ | MASTER表記 |
| 市町村 | string | ○ | MASTER表記 |
| 実装区分 | string | ○ | 個別指定／中国5県全市町村 |
| ごみ処理主体 | string | ○ | 自治体・一部事務組合等。複数可 |
| 自治体ごみトップURL | URL | ○ | 公式トップ |
| 分別ガイドURL | URL | ○ | 現行ルールの主要根拠 |
| 品目検索URL | URL |  | 公式または公式案内サービス |
| やさしい日本語URL | URL |  | 未確認・なしは空欄 |
| 多言語資料URL | URL |  | 未確認・なしは空欄 |
| 対象年度 | string | ○ | 資料上の年度／現行性説明 |
| 最終確認日 | date | ○ | YYYY-MM-DD |
| 確認ステータス | enum | ○ | NOT_STARTED〜APP_READY |
| 備考 | string |  | 更新差・主体分担等 |

## categories

| 項目 | 型 | 必須 | 説明 |
|---|---|---:|---|
| municipality_id | string | ○ | municipality参照 |
| category_id | string | ○ | 自治体内で一意 |
| 自治体正式名称 | string | ○ | 出典の正式表記 |
| category_group | string |  | 自治体内の親概念 |
| parent_category_id | string |  | 同一自治体の親category_id |
| classification_level | enum | ○ | PRIMARY / SUBCATEGORY / ALTERNATIVE / EXCLUDED |
| 表示順 | integer | ○ | 学習者投影順 |
| collection_channel | enum | ○ | 回収・持込経路 |
| 代表品目 | string | ○ | 全品目辞典ではなく代表例 |
| 入れてはいけない物 | string |  | 明示された除外 |
| 適用条件 | string |  | 材質・用途・汚れ等 |
| 条件外の扱い | string |  | 条件不成立時の分別先 |
| 出す前の処理 | string |  | 洗浄・分解・絶縁等 |
| 袋・容器のルール | string |  | 指定袋・透明袋・結束等 |
| サイズ・条件 | string |  | 寸法・重量・袋収容条件 |
| 粗大ごみ扱いか | enum | ○ | TRUE / FALSE / CONDITIONAL / UNKNOWN |
| 予約が必要か | enum | ○ | 同上 |
| 有料か | enum | ○ | 同上 |
| 料金ルール | string |  | 具体的な課金方法 |
| 自治体収集外か | enum | ○ | 同上 |
| 注意事項 | string |  | 安全・代替経路等 |
| source_id | string | ○ | sources参照 |
| 出典URL | URL | ○ | 公式URL |
| 出典ページ・該当箇所 | string | ○ | ページ／見出し |
| 確認日 | date | ○ | YYYY-MM-DD |

## sources

優先度は1（現行自治体公式ページ）から5（公式多言語資料）の順。`現行性` は `現行`、`現行案内中`、`要再確認` 等を明記し、発行年だけから推測しない。

