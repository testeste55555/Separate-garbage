# Data Dictionary v1.2.3

確定日：2026-08-18  
本書はv1.2.2を継承し、変更列と追加テーブルを定義する。

## municipalities

| 列 | 型・制約 | 必須条件 | 説明 |
|---|---|---|---|
| `category_count_review_id` | reference | verified状態 | `category_review_evidence.review_id`を参照する安定ID |
| `category_count_reviewed_date` | date | verified状態 | 網羅性レビュー日、YYYY-MM-DD |
| `category_count_reviewed_by` | string | verified状態 | reviewer識別子 |

`category_count_evidence_source_id` は廃止した。複数sourceは追加テーブルで保持する。

## category_review_evidence

| 列 | 型・制約 | 必須 | 説明 |
|---|---|---|---|
| `review_evidence_id` | string、主キー | 必須 | 証拠行の安定ID |
| `review_id` | reference | 必須 | municipalities.`category_count_review_id` と一致 |
| `municipality_id` | reference | 必須 | reviewとsourceの自治体に一致 |
| `source_id` | reference | 必須 | 同一自治体のofficial_verified source |
| `locator` | string | 必須 | ページ、章、見出し範囲、表等 |
| `evidence_role` | enum | 必須 | OFFICIAL_TOTAL / PRIMARY_INDEX / SUPPLEMENTAL_INDEX |
| `notes` | string | 任意 | 補足 |

`OFFICIAL_COUNT_MATCHED` はOFFICIAL_TOTALを、`MANUAL_INDEX_REVIEW` はPRIMARY_INDEXを最低1件要求する。

## QA

| 列 | 型・制約 | 説明 |
|---|---|---|
| `確認日` | date | 自治体の最終確認日、category確認日、source取得確認日、category count review日の最大値 |

保存値は根拠データからの再計算値と一致しなければならない。

## categoriesの階層投影

- CURRENT子を持つ親は公式件数へ重複計上しない。
- 公式子区分は `classification_level=SUBCATEGORY` とし、`parent_category_id` を必須とする。
- `ui_role=REFERENCE_ONLY` のCURRENT子をUIで束ねる場合、親はCURRENTかつ `ui_role=SORT_BUCKET` でなければならない。
- 初期mapping候補はCURRENT子を持つ投影親から生成しない。

## Batch成果物

完成Batchの必須7成果物：municipalities、categories、sources、qa、item_mapping、item_coverage、category_review_evidence。

## category詳細の未記載値と禁止プレースホルダ

- 公式sourceの当該locatorに個別記載がないCORE詳細は、推測文で埋めず`NOT_STATED_IN_CITED_SOURCE`を保存する。
- REFERENCE詳細に記載がなければ空欄を許す。
- `他の分別区分に該当する物`、`該当する公式区分`、`公式ガイドの指定方法`、`公式ガイドの品目・寸法条件`、複数品目を一括した「品目別前処理」等は空欄回避用プレースホルダとして禁止する。
- validatorはcategory詳細全フィールドを検査し、禁止値・禁止パターンを構造エラーとして拒否する。
