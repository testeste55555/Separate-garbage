# Schema v1.2

確定日：2026-08-17  
対象：143自治体へ拡張可能な家庭ごみ分別データ基盤

## 1. v1.1からの修正目的

v1.1の自治体・区分・出典データは保持し、次の構造問題を修正する。

1. canonical件数やBatch名をvalidatorの正常値にしない。
2. batchはmerge前に、自身のmappingとcoverageで検証できる。
3. merge・再migrationで手動 `VERIFIED` / `APP_READY` を初期状態へ戻さない。
4. 確認済み、不存在、未確認を証跡付きで区別する。
5. 全自治体×共通40品目の調査状態を欠損なく管理する。
6. 区分網羅性は自己申告でなく、公式件数一致または手動索引レビューで証明する。
7. `ui_role` を独立した教材UI指定として扱う。
8. 構造validationとアプリ投入準備Gateを分離する。

## 2. テーブル

| テーブル | 主キー | 役割 |
|---|---|---|
| municipalities | `municipality_id` | 公式導線、任意機能の確認状態、区分網羅性証跡 |
| categories | `(municipality_id, category_id)` | 正式区分、分類条件、教材UI指定 |
| sources | `(municipality_id, source_id)` | 公式資料と公式性根拠 |
| common_items | `internal_item_id` | 共通40品目と教材安全区分 |
| item_mapping | `mapping_id` | 品目から区分への条件枝とレビュー証跡 |
| item_mapping_coverage | `(municipality_id, internal_item_id)` | 40品目すべての調査・実装準備状態 |
| qa | `municipality_id` | 元データから再計算した品質状態 |

Pilotと各batchは上記の自治体・区分・出典・QA・mapping・coverageの6成果物を自身のディレクトリに持つ。canonicalはPilotと完成batchの動的unionである。

## 3. CORE / REFERENCE

CORE必須は、正式区分、分類結果を変える条件、前処理、安全、収集外、出典、時点、`ui_role` である。

次はREFERENCEであり、一律QA Gateにはしない。

- `collection_channel`
- `袋・容器のルール`
- 粗大ごみ、予約、料金、直接搬入、回収拠点、代替経路

汚れ除去、キャップ分離、サイズ条件など、値によって分類結果が変わる情報は `適用条件`、`条件外の扱い`、`出す前の処理` へCOREとして記録する。袋そのものの指定や結束だけはREFERENCEでよい。

## 4. ui_role

`ui_role` は収集経路や階層から再推論しない独立値である。

- `SORT_BUCKET`：現行の教材用仕分け箱
- `REFERENCE_ONLY`：教材内の参照案内
- `HIDDEN`：将来・終了ルール
- `EXCLUDED_NOTICE`：自治体収集外の注意

validatorは意味上の矛盾だけを拒否する。

- 非CURRENTは `HIDDEN`
- `SORT_BUCKET` は自治体収集外にできない
- `EXCLUDED_NOTICE` は自治体収集外である

## 5. 任意機能の確認証跡

品目検索、やさしい日本語、多言語は各々に `check_status` と `check_evidence` を持つ。

| status | 意味 |
|---|---|
| `CHECKED_PRESENT` | URLの存在を確認し、URLと確認日を証跡化 |
| `CHECKED_ABSENT` | 公式ページを調査し、不存在の検索範囲と確認日を証跡化 |
| `NOT_CHECKED` | 未確認。空URLを不存在と解釈しない |

存在の有無はQA合否にしない。確認済み状態も分別COREのGateにはしない。

## 6. 区分網羅性

`category_count_check_status` は次の3値である。

- `OFFICIAL_COUNT_MATCHED`：公式総数が明示され、構造化件数と一致
- `MANUAL_INDEX_REVIEW`：公式目次・見出しを人が全件照合
- `NOT_REVIEWED`：網羅性未確認

前2状態は公式 `source_id`、根拠、レビュー日、reviewerが必要である。`NOT_REVIEWED` は `category_count_verified=FALSE` とし、一般文だけでTRUEにしない。

## 7. mappingと40品目coverage

各自治体は共通40品目すべてについてcoverageを1行持つ。

| coverage_status | 意味 |
|---|---|
| `NOT_RESEARCHED` | 未調査。不存在ではない |
| `MAPPED_INITIAL` | 区分レベルからの機械抽出 |
| `VERIFIED` | 品目別レビュー済みだがアプリ投入条件未達 |
| `VERIFIED_NOT_APPLICABLE` | 公式証跡により該当なしを確認 |
| `APP_READY` | 全条件枝がアプリ投入可能 |

mapping枝は `evidence_scope`, `branch_review_status`, `reviewed_date`, `reviewed_by` を持つ。`APP_READY` には次を必須とする。

1. `evidence_scope=ITEM_SPECIFIC`
2. `branch_review_status=COMPLETE`
3. 品目単位の公式source・該当箇所
4. reviewerとreviewed_date
5. coverageの枝数とmapping枝数が一致
6. その自治体の40 coverage行がすべて `APP_READY` または `VERIFIED_NOT_APPLICABLE`

CSVのenumだけを直接変更してもvalidatorは通らない。

## 8. validationとGate

通常validationはSchema、主キー、参照、公式性、証跡の意味、QA再計算、40品目coverageを検証する。未調査を正しく `NOT_RESEARCHED` / `QA_REQUIRED` と表現していれば構造PASSである。

`--gate` は追加で全自治体の `QA_PASSED` と40品目の実装準備完了を要求する。未完了は終了コード2の `APP_READINESS_GATE_HOLD` とする。

## 9. mergeと拡張性

- 完成batchの判定は必要6成果物の存在で行い、Batch名を固定しない。
- canonical自治体数はPilot＋完成batchのunionから決まり、15を期待値にしない。
- mappingはbatch自身のファイルで先にvalidationできる。
- mergeはmappingを再生成せず、bundleをmergeする。
- 既存canonicalの手動 `VERIFIED` / `APP_READY` は同一キーで優先保持する。
- migrationの機械抽出は手動レビュー行を上書きしない。

