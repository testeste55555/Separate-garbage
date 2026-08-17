# Schema v1.2.2

確定日：2026-08-17  
対象：Schema v1.2.1の証跡モデル修正

## 1. 目的

v1.2.1の自治体・区分・出典・mapping・coverageを保持し、次の実運用上の矛盾を解消する。

1. 公式総数が公表されていない自治体でも、公式目次・見出しの全件照合により区分網羅性を証明できるようにする。
2. category体系の根拠と、個々の品目判断の公式根拠を別のsourceとして保持できるようにする。

## 2. 区分網羅性

### OFFICIAL_COUNT_MATCHED

- `official_category_count`：必須、正の整数
- `reviewed_category_count`：空欄。手動照合件数と二重管理しない
- 構造化したCURRENTかつ非EXCLUDED_NOTICEの区分数と一致
- `category_count_evidence_source_id`：総数を記載した同一自治体公式source
- `category_count_basis`：総数の記載位置
- `category_count_reviewed_date` / `category_count_reviewed_by`：必須

### MANUAL_INDEX_REVIEW

- `official_category_count`：空欄可。公式に総数がなければ空欄にする
- `reviewed_category_count`：必須、手動照合した見出し件数
- `reviewed_category_count` は構造化したCURRENTかつ非EXCLUDED_NOTICEの区分数と一致
- `category_count_evidence_source_id`：照合対象の公式目次・見出しsource
- `category_count_basis`：照合したページ、章、見出し範囲、除外判断を再現できる根拠
- `category_count_reviewed_date` / `category_count_reviewed_by`：必須

公式総数がない場合、構造化件数を `official_category_count` として記入してはならない。構造化件数は `reviewed_category_count` に記録する。

### NOT_REVIEWED

`category_count_verified=FALSE` とし、`reviewed_category_count`、evidence source、reviewer、review日を空欄にする。

## 3. category根拠とitem根拠

item_mappingは2種類の根拠を持つ。

### category_source_*

- `category_source_id`
- `category_source_url`
- `category_source_locator`

mappingの分別先categoryそのものを証明する。3列は参照categoryの `source_id / 出典URL / 出典ページ・該当箇所` と一致する。

### item_evidence_*

- `item_evidence_source_id`
- `item_evidence_url`
- `item_evidence_locator`

対象品目がそのcategoryへ入ること、条件、例外を証明する。同一自治体の公式sourcesに存在し、URLはsourceの公式URLと一致し、locatorは品目行・見出し・ページ等を特定できなければならない。category sourceと異なる公式品目辞典・注意ページを使用できる。

## 4. review状態

| 状態 | category根拠 | item根拠 |
|---|---|---|
| INITIAL_REVIEW_REQUIRED | 必須 | 空欄 |
| VERIFIED | 必須 | 必須。ITEM_SPECIFIC、reviewer/date必須 |
| APP_READY | 必須 | 必須。ITEM_SPECIFIC、全条件枝COMPLETE、公式品目表記必須 |

coverageの `item_evidence_*` も品目別根拠専用である。

- NOT_RESEARCHED / MAPPED_INITIAL：空欄
- VERIFIED / VERIFIED_NOT_APPLICABLE / APP_READY：3列すべて必須、同一自治体の公式source参照、reviewer/date必須

## 5. migration

- 旧mappingの `source_id / 出典URL / 出典ページ・該当箇所` はcategory根拠へ移す。
- 未レビューの旧行からitem根拠を自動生成しない。
- 旧行がすでに `ITEM_SPECIFIC` かつ手動review状態の場合だけ、既存証跡をitem根拠へ引き継ぐ。
- 旧coverageも、既にITEM_SPECIFICな手動review状態だけ既存証跡を引き継ぐ。

## 6. 現在地

- 15自治体、194区分、57出典、283 mapping枝、600 coverage pairを保持
- 構造validation：PASS
- RED TEAM：17/17 PASS
- QA：2 QA_PASSED / 13 QA_REQUIRED
- NEXT_BATCH_GATE：HOLD
- APP_READINESS_GATE：HOLD、APP_READY 0/15
- 13自治体の実資料レビュー：未開始
- Batch 02：未開始
