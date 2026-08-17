# Schema v1.2.1

確定日：2026-08-17  
対象：Schema v1.2の拡張運用修正

## 1. 互換性

v1.2.1はv1.2の列構成とenumを維持する。既存15自治体、194区分、57出典、283 mapping枝、600 coverage pairは削除しない。変更対象は状態の一元化、完成Batchの定義、条件枝identity、Gateの責務である。

## 2. QA状態の一元化

品質判定の正本は各bundleのQAテーブルとする。municipalitiesの `確認ステータス` はQA再計算後に自動同期する読取専用ミラーであり、独立した手入力状態ではない。

- QAテーブルを元データから再計算する。
- `QA_PASSED` / `QA_REQUIRED` をmunicipalitiesへ同期する。
- validatorは両テーブルの不一致を構造エラーにする。

調査進捗が別途必要になった場合は `research_status` 等の別列を将来Schemaで追加し、QAの語彙を流用しない。

## 3. 完成Batch

完成Batchは次の6成果物がすべて存在するディレクトリだけである。

1. municipalities
2. categories
3. sources
4. qa
5. item_mapping
6. item_coverage

定義は `schema_v12.completed_batch_dirs()` に一元化し、validator、merge、RED TEAMが共有する。4つの調査入力だけがあるディレクトリはmigration候補にはできるが、完成Batchとしてmergeしてはならない。

## 4. mapping条件枝identity

`item_mapping` の主キーは不変な `mapping_id` である。

- 同一 `(municipality_id, internal_item_id, category_id)` に、異なる条件を持つ複数枝を許可する。
- mergeとreconciliationは `mapping_id` で同一枝を識別する。
- `branch_order` は同一自治体・品目内の表示順であり、identityではない。
- 人が追加する条件枝は一意で安定した `mapping_id` を付ける。
- 旧mappingはsemantic keyを一度だけmigration fallbackとして使用し、既存 `mapping_id` を保持する。
- 手動 `VERIFIED` / `APP_READY` 枝は機械候補から外れても、参照整合性がある限り保持する。

## 5. Gate分離

### NEXT_BATCH_GATE

次の自治体調査へ進むための運用Gateである。

- Pilotと全完成Batchの構造validation
- canonical no-loss unionと構造validation
- 公式出典と参照整合性
- 区分網羅性証跡を含む全自治体QA_PASSED
- 自治体×40品目coverage行の完全な存在
- 二重mergeのno-change冪等性
- RED TEAM PASS

40品目の `APP_READY` は要求しない。

### APP_READINESS_GATE

自治体を教材アプリへ公開するためのGateである。

- QA_PASSED
- 40品目すべてが `APP_READY` または `VERIFIED_NOT_APPLICABLE`
- 品目別公式証拠、reviewer、日付、全条件枝の完全性

未完了はそれぞれ終了コード2の `HOLD`、構造破損は終了コード1の `FAILED` とする。

## 6. 2026-08-17時点

- 構造validation：PASS
- RED TEAM：15/15 PASS
- NEXT_BATCH_GATE：HOLD（13自治体がQA_REQUIRED）
- APP_READINESS_GATE：HOLD（13自治体がQA_REQUIRED、APP_READY 0/15）
- Batch 02：未開始
