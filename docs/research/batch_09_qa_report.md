# Batch 09 QA Report

実施日: 2026-08-19
Schema: v1.2.4
対象MASTER: M084〜M093

## 判定

**PASS**

- active Batch 09: 9自治体
- QA_PASSED: 9/9
- DEFERRED: M086 新庄村
- Batch structural validation: PASS
- Batch 09 RED TEAM: PASS
- canonical merge: PASS
- canonical structural validation: PASS
- Schema v1.2.4 RED TEAM: PASS
- NEXT_BATCH_GATE: PASS
- APP_READINESS_GATE: HOLD

CI記録: `docs/research/batch_09_ci_status.txt`

## active自治体と公式葉

- M084 里庄町: 10
- M085 矢掛町: 11
- M087 鏡野町: 8
- M088 勝央町: 7（`OFFICIAL_COUNT_MATCHED`）
- M089 奈義町: 2
- M090 西粟倉村: 5
- M091 久米南町: 14
- M092 美咲町: 5
- M093 吉備中央町: 11

合計公式葉: 73。親投影行を含むcategory行は76。

## M086 新庄村

岡山県の現行公式案内から新庄村のごみ収集公式ページへの導線は確認できるが、村公式ページ本文の取得が安定せず、住民が排出時に選択する全分別区分を一次資料で全件照合できなかった。

そのため、地域処理計画や第三者情報からcategoryを補作せず、固定ID `M086` を保持したまま `DEFERRED / OFFICIAL_SOURCE_BODY_UNAVAILABLE` とした。

## 真正性確認

- 里庄町: 2025年12月の現行案内を採用。燃える/燃えない、資源7系統、粗大を保持。
- 矢掛町: 公式ページのトップレベル区分を保持し、内部の色・素材分別や「家庭大型ごみ（不燃物）収集」サービスを別categoryとして二重計上しない。
- 鏡野町: 資源ごみ親の下に缶・びん・乾電池等・PETの4公式子葉を保持。スプレー缶について穴あけを推測追加しない。
- 勝央町: 町公式が明示する「7種分別収集」を7のまま保持し、粗大ごみを人工的な8番目へ追加しない。
- 奈義町: `資源ごみ・小型不燃ごみ・有害なごみ`という現行複合収集ラベルを3箱へ人工分割しない。
- 西粟倉村: 村版令和8年度カレンダーの5収集グループを保持し、委託先美作市の詳細taxonomyへ過剰展開しない。
- 久米南町: 資源9細分を公式子葉として保持。スプレー缶は「使い切る・穴を開けない」を保持。
- 美咲町: 2026年の全町統一運用を5住民区分で保持。
- 吉備中央町: 令和8年度日程表の11公式葉を保持。資源6葉、可燃/不燃粗大、蛍光管を混同しない。

## canonical更新

Batch 09統合後:

- canonical municipalities: 92
- QA: 92/92 `QA_PASSED`
- category: 1,094行
- structured official leaves: 1,008
- sources: 253
- initial mapping branches: 932
- coverage: 3,680 pair
- category review evidence: 216
- DEFERRED: 3（M065・M076・M086）
- active implementation targets: 140

Batch 10へ進行可能。
