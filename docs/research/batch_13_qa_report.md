# Batch 13 QA Report

実施日: 2026-08-19
Schema: v1.2.4
対象MASTER: M126〜M135（山口県残り10自治体）

## 判定

**PASS**

- active Batch 13: 9自治体
- QA_PASSED: 9/9
- DEFERRED: M127 美祢市
- Batch structural validation: PASS
- Batch 13 RED TEAM: PASS
- canonical merge: PASS
- canonical structural validation: PASS
- Schema v1.2.4 RED TEAM: PASS
- operational category semantics RED TEAM: PASS
- NEXT_BATCH_GATE: PASS
- APP_READINESS_GATE: HOLD

CI記録: `docs/research/batch_13_ci_status.txt`

## active自治体と公式葉

- M126 柳井市: 10
- M128 周南市: 11
- M129 山陽小野田市: 12
- M130 周防大島町: 12
- M131 和木町: 11
- M132 上関町: 12
- M133 田布施町: 12
- M134 平生町: 12
- M135 阿武町: 5

合計公式葉: 97。

## DEFERRED

### M127 美祢市

美祢地域・美東地域・秋芳地域で同時にCURRENTな住民向け分別体系が併存し、単なる収集日程差ではなく、正式区分と同一品目の分別先が実際に異なる。

現行municipality単位Schema/UIでは居住地域scopeを安全に解決できないため、`SCHEMA_SCOPE_LIMITATION`としてDEFERREDとした。固定IDは保持し、将来`district_scope`等の地域variant対応後に再開可能とする。

## 真正性確認

- 柳井市: `ビン・乾電池`を一つの葉へ潰さず、ガラスビン／乾電池を別葉として保持。`ペットボトル・古紙`もPETと古紙3種へ分け、住民が実際に別袋・別束・専用回収ボックスへ出す単位を保持。スプレー缶は使い切り後、屋外で穴を開ける。
- 周南市: 地域別ページは収集日程差であり、市全域向け分別体系をcanonicalとした。古紙・衣類、びん缶/PET、プラスチック2系統を住民子葉へ展開。使用済小型家電はDROP_OFF、粗大ごみはBOOKED_PICKUP。スプレー缶は穴あけあり。
- 山陽小野田市: 市全域向け現行体系を採用。古紙類は新聞／雑誌類／ダンボール／紙パックの4葉。根拠のない可燃ごみ前処理汎用文は`NOT_STATED_IN_CITED_SOURCE`へ戻した。
- 周防大島町: 現行公式検索サービスの`種類でさがす`から12公式葉を採用し、`収集できないごみ`／`収集も処理もできないごみ`はEXCLUDED_NOTICEとして葉数外。検索サービス確認は`CHECKED_PRESENT`＋URL/date evidenceで正式化。スプレー缶は使い切れば穴あけ不要。
- 和木町: 現行11住民区分を保持。`電池・ライター・スプレー類`は使い切り、穴を開けずに出す。
- 上関町: 古紙・紙パックは新聞紙・チラシ／雑誌／段ボール／紙パックの4葉。PETは専用回収ボックスのDROP_OFF。スプレー缶は中身を使い切ることだけを記録し、穴あけ有無を推測追加しない。
- 田布施町・平生町: 公式の`7分別`は上位見出し数として扱い、resident-facing official leaf総数へ流用しない。缶／金属を別袋、資源5品目を種別ごとに分ける実排出単位を保持し、各12葉としてMANUAL_INDEX_REVIEW。
- 阿武町: 2026年4月改定後も可燃／不燃／資源の3指定袋は維持されるため、同日収集化をcategory統合と誤認しない。資源袋内部の缶・びん・PET・容器包装プラを人工的な独立categoryへ増やさない。

Batch 13は全自治体を`MANUAL_INDEX_REVIEW`としている。数値見出し・収集日程・内部説明を、resident-facing official leaf総数へ自動転用しない。

## canonical更新

Batch 13統合後:

- canonical municipalities: 126
- QA: 126/126 `QA_PASSED`
- category: 1,512行
- structured official leaves: 1,387
- sources: 343
- initial mapping branches: 1,259
- coverage: 5,040 pair
- category review evidence: 306
- DEFERRED: 9
- active implementation targets: 134

Batch 14へ進行可能。
