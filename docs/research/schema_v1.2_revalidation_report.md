# Schema v1.2 Revalidation / QA Report

実施日：2026-08-17  
Batch 02調査：未実施

| dataset | 構造validation | QA_PASSED | QA_REQUIRED | mapping枝 | 40品目coverage |
|---|---|---:|---:|---:|---:|
| Pilot | PASS | 1 | 4 | 93 | 200 |
| Batch 01 | PASS | 1 | 9 | 190 | 400 |
| canonical | PASS | 2 | 13 | 283 | 600 |

canonical coverageは244 `MAPPED_INITIAL`、356 `NOT_RESEARCHED`。APP_READY自治体は0/15である。

QA_REQUIREDの主因は、v1.1 migrationが一般文だけでTRUEにしていた区分網羅性を `NOT_REVIEWED` へ是正したこと。既存区分・出典の削除や再調査失敗ではない。

```text
CANONICAL_STRUCTURAL_VALIDATION_PASSED
CANONICAL_APP_READINESS_GATE_HOLD
```

構造validationとAPP readinessを別判定にしたため、未完了状態を隠さずデータセット自体の整合性を検証できる。
