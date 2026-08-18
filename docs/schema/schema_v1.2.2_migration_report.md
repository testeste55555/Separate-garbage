# Schema v1.2.2 Migration Report

初回実施日：2026-08-17  
候補再生成：2026-08-18  
結果：構造validation PASS / 両Gate HOLD

| 対象 | 自治体 | 区分 | 出典 | mapping枝 | coverage |
|---|---:|---:|---:|---:|---:|
| Pilot | 5 | 60 | 25 | 76 | 200 |
| Batch 01 | 10 | 134 | 32 | 161 | 400 |
| canonical | 15 | 194 | 57 | 237 | 600 |

## 列移行

- municipalitiesへ `reviewed_category_count` を追加。
- mappingの旧category引用3列を `category_source_*` へ移行。
- mappingへ空の `item_evidence_*` 3列を追加。現在237枝はすべてINITIAL_REVIEW_REQUIREDのため、品目証拠を自動生成していない。
- 2026-08-18に候補生成をPositive evidence限定へ変更し、Negative/context evidenceまたは複合語衝突だけで生成されていた46枝を除去した。
- coverageの引用3列を `item_evidence_*` へ名称変更。現在のMAPPED_INITIAL / NOT_RESEARCHED行はすべて空欄とした。

既存category、source、残存mapping_id、coverage pair、QA状態は保持した。13自治体の実資料レビューとBatch 02調査は行っていない。

## 冪等性

Schema migrationを2回、Batch 01 buildを2回、canonical mergeを2回実行した。Pilot、Batch 01、canonicalの全CSVについて、実行前・初回・2回目のSHA-256が一致した。

## 判定

```text
PILOT_STRUCTURAL_VALIDATION_PASSED
BATCH_01_STRUCTURAL_VALIDATION_PASSED
CANONICAL_STRUCTURAL_VALIDATION_PASSED
NEXT_BATCH_GATE_HOLD
CANONICAL_APP_READINESS_GATE_HOLD
```

HOLDは既存13自治体の区分網羅性レビューと40品目レビューが未完であることを正しく示す。
