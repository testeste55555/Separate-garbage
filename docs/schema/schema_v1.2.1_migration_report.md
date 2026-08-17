# Schema v1.2.1 Migration Report

> 履歴版。証跡列移行後の結果は `schema_v1.2.2_migration_report.md` を参照する。

実施日：2026-08-17  
結果：構造validation PASS / 両運用Gate HOLD

## 移行結果

| 対象 | 自治体 | 区分 | 出典 | mapping枝 | coverage |
|---|---:|---:|---:|---:|---:|
| Pilot | 5 | 60 | 25 | 93 | 200 |
| Batch 01 | 10 | 134 | 32 | 190 | 400 |
| canonical | 15 | 194 | 57 | 283 | 600 |

既存データ件数と全 `mapping_id` を保持した。Batch 02の自治体調査は行っていない。

## QA同期

municipalitiesの `確認ステータス` をQAログへ同期した。

| dataset | QA_PASSED | QA_REQUIRED | municipalitiesとの不一致 |
|---|---:|---:|---:|
| Pilot | 1 | 4 | 0 |
| Batch 01 | 1 | 9 | 0 |
| canonical | 2 | 13 | 0 |

## 完成Batchと条件枝

- 完成Batch判定を共有関数へ統一し、6成果物すべてを必須化した。
- 4調査入力だけのbundleはmigration候補としてのみ発見する。
- merge keyを `mapping_id` へ統一した。
- 同じ自治体・品目・categoryに異なる2条件枝を置く攻撃fixtureで、両枝の保持を確認した。
- `branch_order` の変更では条件枝identityが変わらない。

## 冪等性

`build_batch_01.py` を2回、`merge_research.py` を2回実行した。Pilot、Batch 01、canonicalの全v1.2 CSVについて、実行前・初回・2回目のSHA-256は一致した。

## Gate

```text
CANONICAL_STRUCTURAL_VALIDATION_PASSED
CANONICAL_NEXT_BATCH_GATE_HOLD
CANONICAL_APP_READINESS_GATE_HOLD
```

NEXT_BATCH_GATEのHOLD理由は13自治体のQA_REQUIREDだけであり、40品目APP_READYはこのGateの条件ではない。APP_READINESS_GATEはQA未完に加えて全15自治体の40品目レビュー未完を報告する。
