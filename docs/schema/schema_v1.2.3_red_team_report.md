# Schema v1.2.3 RED TEAM Report

実施日：2026-08-18  
自動判定：23/23 PASS

## 新規攻撃観点

1. QA日付を古い固定日に改ざんするとstored QA再計算不一致で失敗する。
2. 複数source証拠へ別自治体sourceを混入すると失敗する。
3. 完成Batchは7成果物すべてがなければ検出されない。
4. 石巻市は公式葉19区分を保持し、びんの教材箱は1件だけである。
5. 投影親から初期mappingを生成せず、公式4子区分を条件枝として保持する。

## 回帰

- 全bundle構造validation PASS
- canonical no-loss union PASS
- MANUAL_INDEX_REVIEWの空official countとreviewed count検査 PASS
- 12自治体の手動索引レビューと11区分補正 PASS
- 40品目Positive/Negative context、複合語collision PASS
- mapping_id条件枝保持、item evidence分離、APP_READY改ざん拒否 PASS
- NEXT_BATCH_GATE整合 PASS
- APP_READINESS_GATE HOLD整合 PASS

`RED_TEAM_SUMMARY=23/23`。Batch 02は未開始。
