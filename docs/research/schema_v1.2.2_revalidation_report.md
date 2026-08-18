# Schema v1.2.2 Revalidation / QA Report

初回実施日：2026-08-17  
候補再生成・再validation：2026-08-18  
13自治体の実資料レビュー：未実施  
Batch 02調査：未実施

| dataset | 構造validation | QA_PASSED | QA_REQUIRED | mapping枝 | coverage |
|---|---|---:|---:|---:|---:|
| Pilot | PASS | 1 | 4 | 76 | 200 |
| Batch 01 | PASS | 1 | 9 | 161 | 400 |
| canonical | PASS | 2 | 13 | 237 | 600 |

canonical coverageは225 MAPPED_INITIAL、375 NOT_RESEARCHED、APP_READY自治体0/15。全237 mapping枝のcategory根拠は移行済みで、item根拠は未レビュー状態に合わせて空欄である。旧候補283枝から、Negative/context evidenceまたは複合語衝突だけで生成された46枝を除去した。

```text
RED_TEAM_SUMMARY=19/19
NEXT_BATCH_GATE_HOLD
CANONICAL_APP_READINESS_GATE_HOLD
```

Schema v1.2.2と候補生成器の修正により、13自治体の区分網羅性レビューを開始できる。ただし、本修正では実資料の全件照合自体は行っていない。Batch 02も未開始である。
