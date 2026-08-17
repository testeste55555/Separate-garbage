# Schema v1.2.1 RED TEAM Report

実施日：2026-08-17  
自動判定：15/15 PASS  
NEXT_BATCH_GATE：HOLD  
APP_READINESS_GATE：HOLD

| # | 攻撃観点 | 結果 |
|---:|---|---|
| 1 | Pilot・全完成Batch・canonicalの構造validation | PASS |
| 2 | canonicalがPilot＋完成Batchのno-loss union | PASS |
| 3 | completed定義が共有され、6成果物を要求 | PASS |
| 4 | municipalitiesのQA状態がQAログの同期ミラー | PASS |
| 5 | coverageが動的な自治体×40品目直積 | PASS |
| 6 | 任意機能の確認済み／未確認と証跡 | PASS |
| 7 | ui_roleの独立性と意味上の不変条件 | PASS |
| 8 | active validatorに15自治体固定値なし | PASS |
| 9 | Batchが自身のmapping/coverageを検証 | PASS |
| 10 | mergeがmappingを再生成しない | PASS |
| 11 | `mapping_id` が同一categoryの複数review済み条件枝を保持 | PASS |
| 12 | 根拠なしAPP_READY直接編集を拒否 | PASS |
| 13 | NEXT_BATCH_GATEがQAから導出されAPP_READYに依存しない | PASS |
| 14 | APP_READINESS_GATEがデータからPASS/HOLDを判定 | PASS |
| 15 | APP readinessが全40 pairから導出 | PASS |

実行結果：

```text
RED_TEAM_SUMMARY=15/15
SCHEMA_V12_RED_TEAM_PASSED
```

RED TEAM PASSは検出器と拡張基盤が意図どおりであることを示す。現在データのGate PASSを意味しない。

## 現在のHOLD

- NEXT_BATCH_GATE：13自治体がQA_REQUIRED。
- APP_READINESS_GATE：上記に加え、600 pair中244 `MAPPED_INITIAL`、356 `NOT_RESEARCHED`、APP_READY自治体0/15。
- Batch 02は開始していない。
