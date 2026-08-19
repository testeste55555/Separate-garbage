# Schema v1.2.4 RED TEAM Report

実施日: 2026-08-19

## 結果

- Schema v1.2.3回帰RED TEAM: 25/25 PASS
- resident-facing category semantics: 1/1 PASS
- 合計: 26/26 PASS

## 新規攻撃観点

由良町M028は住民向け5区分を正式採用し、`危険有害=FALSE`、`収集しない物=FALSE`のまま`QA_PASSED`でなければならない。

これは危険物や収集不可品を無視するという意味ではない。独立categoryの存在をcategory QAで強制せず、乾電池・モバイルバッテリー・スプレー缶・家電4品目・PC等はitem-level APP_READYで個別の公式証拠を必須にする。

## M028証拠

- PRIMARY_INDEX: 由良町公式 住民向けごみ分別案内
- SUPPLEMENTAL_INDEX: 広報ゆら2026年3月号
- reviewed_category_count: 5
- MANUAL_INDEX_REVIEW
- QA_PASSED

## Gate

- Batch 03 structural validation: PASS
- canonical structural validation: PASS
- Schema RED TEAM: PASS
- Batch 03 RED TEAM: PASS
- operational semantics RED TEAM: PASS
- NEXT_BATCH_GATE: PASS
- APP_READINESS_GATE: HOLD
