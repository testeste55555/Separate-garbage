# Schema v1.2.3 Migration Report

実施日：2026-08-18

## 結果

| dataset | 自治体 | category行 | 公式葉区分 | source | review evidence | mapping枝 | coverage | QA |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Pilot | 5 | 60 | 54 | 25 | 5 | 76 | 200 | 5/5 PASS |
| Batch 01 | 10 | 145 | 133 | 33 | 17 | 169 | 400 | 10/10 PASS |
| canonical | 15 | 205 | 187 | 58 | 22 | 245 | 600 | 15/15 PASS |

公式葉区分はCURRENT、非EXCLUDED_NOTICE、かつCURRENT子を持たない行の合計。category行数には投影親、PLANNED、EXCLUDED_NOTICEを含む。

## 修正確認

- QA確認日：固定値を撤去し、15自治体すべて最新根拠日 `2026-08-18` へ再計算。
- 複数source：M002とM004は各4件、石巻市は公式総数と現行案内の2件を構造化。
- 石巻市：最終版公式計画をS-M005-04として追加し、`OFFICIAL_COUNT_MATCHED=19` へ修正。
- あきびん：親1行＋公式4子区分を保持。公式件数は4、教材箱は1。
- canonical：Pilot＋完成Batchのno-loss union。
- migration後の二重merge：SHA-256不変。

既存品目レビュー済み枝を破壊していない。全mappingは引き続きINITIAL_REVIEW_REQUIREDで、APP_READY 0/15である。Batch 02は作成していない。
