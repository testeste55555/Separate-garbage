# Stage A 中間RED TEAM

実施日: 2026-08-20
対象: 広島市・福山市・東広島市・尾道市・呉市

## 結果

**PASS（Schema修正後）**

| 攻撃観点 | 発見 | 対応 |
|---|---|---|
| municipality単位だけで保持 | 福山市と尾道市は地域taxonomy自体が異なる | district_scopeを必須化。正本category未確定の両市はsourceのみ地域別保持 |
| 1 categoryに複数色 | 東広島市は指定袋色とガイド区分色が併存 | 一対多observationと一意projectionを分離 |
| 指定袋色とカレンダー色 | 用途が違う色を一列で上書きすると根拠が失われる | evidence_roleを追加。上位資料でもcategory識別性を別判定 |
| 単なる装飾色 | タイトル・曜日・紙面地色が大量に存在 | CATEGORY_DISCRIMINATORだけPRIMARY可 |
| 公式資料間の不一致 | 用途差と真正な同一用途競合を区別する必要 | 用途差は併存。同一用途競合はprojectionをNOT_CONFIRMED |
| 色体系がない自治体 | 白地や単一共有色はcategory色を意味しない | NO_SEMANTIC_COLOR / NOT_CONFIRMEDを空欄で許容 |
| REFERENCE等の混入 | 色付きの粗大ごみ等を通常箱へ誤投影できる | validatorがCURRENT/SORT_BUCKET直積のみ許可 |

## Stage Aの具体判断

- 広島市: 年度版分別表の区分見出し帯が区分ごとに反復し識別用途。PDF近似として採用。
- 東広島市: オレンジ袋・紫袋は公式色名だが複数categoryの共通排出袋。SUPPORTINGで保持し、区分枠色をPRIMARYとした。
- 呉市: カレンダー凡例と月セルで同じ区分色が反復。曜日装飾ではなく分別ラベルとして採用。
- 福山市: 市内一般・内海町・沼隈町scopeが必要。category正本待ち。
- 尾道市: 5地域guideが現行併存。category正本待ち。

Stage B開始条件であった「中間RED TEAMで発見した問題のSchema反映」を確認した。
