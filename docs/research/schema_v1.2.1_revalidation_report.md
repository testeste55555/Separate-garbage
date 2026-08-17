# Schema v1.2.1 Revalidation / QA Report

> 履歴版。証跡列分離後の結果は `schema_v1.2.2_revalidation_report.md` を参照する。

実施日：2026-08-17  
Batch 02調査：未実施

| dataset | 構造validation | QA_PASSED | QA_REQUIRED | mapping枝 | 40品目coverage |
|---|---|---:|---:|---:|---:|
| Pilot | PASS | 1 | 4 | 93 | 200 |
| Batch 01 | PASS | 1 | 9 | 190 | 400 |
| canonical | PASS | 2 | 13 | 283 | 600 |

municipalitiesとQAログの `確認ステータス` は全15自治体で一致する。canonical coverageは244 `MAPPED_INITIAL`、356 `NOT_RESEARCHED`、APP_READY自治体は0/15である。

## 判定

```text
PILOT_STRUCTURAL_VALIDATION_PASSED
BATCH_01_STRUCTURAL_VALIDATION_PASSED
CANONICAL_STRUCTURAL_VALIDATION_PASSED
RED_TEAM_SUMMARY=15/15
SCHEMA_V12_RED_TEAM_PASSED
NEXT_BATCH_GATE_HOLD
CANONICAL_APP_READINESS_GATE_HOLD
```

`NEXT_BATCH_GATE` は13自治体の区分網羅性QAが未完のためHOLDであり、40品目APP_READYを理由にはしていない。`APP_READINESS_GATE` は全40品目の品目別公式確認も要求する。構造エラーは0件である。
