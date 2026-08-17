# Data Dictionary v1.2.1

> 履歴版。列名称・必須条件の現行定義は `14_data_dictionary_v1.2.2.md` を参照する。

確定日：2026-08-17  
本書はv1.2の定義を継承し、運用上の意味を明確化する。

## municipalities

| 列 | v1.2.1の定義 |
|---|---|
| `確認ステータス` | enum: `QA_PASSED / QA_REQUIRED`。同一bundleのQA再計算結果を自動同期する読取専用ミラー |

この列を調査進行中・調査完了等のワークフロー状態に使用しない。QAテーブルとの不一致はvalidatorエラーである。

## item_mapping

| 列 | 型・制約 | v1.2.1の定義 |
|---|---|---|
| `mapping_id` | string、主キー、必須、一意 | 条件枝の安定identity。merge/reconciliation key |
| `municipality_id` | reference | 自治体 |
| `internal_item_id` | reference | 共通品目 |
| `category_id` | reference | 分別先。identityの全部ではない |
| `branch_order` | positive integer | 同一自治体・品目内で1から連続する表示順。merge keyではない |
| `条件` | non-empty | 枝を選ぶ条件。同一品目・同一categoryでも異なる条件を許可 |

`(municipality_id, internal_item_id, category_id)` は索引・migration fallbackには使えるが、主キーではない。人手で条件枝を追加・分割する場合、既存行を上書きせず一意の `mapping_id` を割り当てる。

## qa

| 列 | v1.2.1の定義 |
|---|---|
| `確認ステータス` | 元テーブルから機械再計算する品質判定の正本 |

## Batch completion

Batch completionはCSV列ではなく、次の6ファイルの存在を意味する。

- `<batch>_municipalities.csv`
- `<batch>_categories.csv`
- `<batch>_sources.csv`
- `<batch>_qa.csv`
- `<batch>_item_mapping.csv`
- `<batch>_item_coverage.csv`

4調査入力だけのbundleはmigration対象候補であって、completedではない。

## Gate vocabulary

| Gate | PASS条件 | 非PASS |
|---|---|---|
| `NEXT_BATCH_GATE` | 構造、公式性、区分網羅性QA、union、merge冪等性、RED TEAM | `HOLD`=QA未完、`FAILED`=構造破損 |
| `APP_READINESS_GATE` | QAと40品目のアプリ投入要件 | `HOLD`=レビュー未完、`FAILED`=構造破損 |

`NEXT_BATCH_GATE` は40品目APP_READYを要求しない。`APP_READINESS_GATE` は次Batch開始判定に代用しない。
