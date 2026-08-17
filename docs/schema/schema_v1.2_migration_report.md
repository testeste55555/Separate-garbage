# Schema v1.2 Migration Report

実施日：2026-08-17  
結果：構造validation PASS / APP readiness Gate HOLD

## 非破壊移行結果

| 対象 | 自治体 | 区分 | 出典 | mapping枝 | coverage |
|---|---:|---:|---:|---:|---:|
| Pilot | 5 | 60 | 25 | 93 | 200 |
| Batch 01 | 10 | 134 | 32 | 190 | 400 |
| canonical | 15 | 194 | 57 | 283 | 600 |

既存15自治体、194区分、57出典、283 mapping枝を保持した。Batch 02の自治体調査は行っていない。

## 状態の再判定

- 区分網羅性：2自治体 `OFFICIAL_COUNT_MATCHED`、13自治体 `NOT_REVIEWED`
- QA：2 `QA_PASSED`、13 `QA_REQUIRED`
- 40品目coverage：244 `MAPPED_INITIAL`、356 `NOT_RESEARCHED`
- APP_READY自治体：0/15

v1.1の一般文による `category_count_verified=TRUE` は証跡として扱わず、FALSEへ修正した。空の任意機能URLは `NOT_CHECKED` とし、不存在とは判定していない。

## 冪等性

- `build_batch_01.py` を2回実行し、Batch 01の6 CSVのSHA-256一致を確認。
- `merge_research.py` を2回実行し、canonical 6 CSVのSHA-256一致を確認。
- migrationとmergeは同一mappingキーの手動 `VERIFIED` / `APP_READY` を優先保持する。

## validation

```text
PILOT_STRUCTURAL_VALIDATION_PASSED
BATCH_01_STRUCTURAL_VALIDATION_PASSED
CANONICAL_STRUCTURAL_VALIDATION_PASSED
CANONICAL_APP_READINESS_GATE_HOLD
```

HOLDは構造エラーではない。未完了を明示した正常な状態である。

