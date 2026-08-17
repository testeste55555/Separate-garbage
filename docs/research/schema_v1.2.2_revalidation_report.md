# Schema v1.2.2 Revalidation / QA Report

実施日：2026-08-17  
13自治体の実資料レビュー：未実施  
Batch 02調査：未実施

| dataset | 構造validation | QA_PASSED | QA_REQUIRED | mapping枝 | coverage |
|---|---|---:|---:|---:|---:|
| Pilot | PASS | 1 | 4 | 93 | 200 |
| Batch 01 | PASS | 1 | 9 | 190 | 400 |
| canonical | PASS | 2 | 13 | 283 | 600 |

canonical coverageは244 MAPPED_INITIAL、356 NOT_RESEARCHED、APP_READY自治体0/15。全283 mapping枝のcategory根拠は移行済みで、item根拠は未レビュー状態に合わせて空欄である。

```text
RED_TEAM_SUMMARY=17/17
NEXT_BATCH_GATE_HOLD
CANONICAL_APP_READINESS_GATE_HOLD
```

Schema修正により、今後の13自治体レビューでは公式総数がなくてもMANUAL_INDEX_REVIEWを使用できる。ただし、本修正では実資料の全件照合自体は行っていない。
