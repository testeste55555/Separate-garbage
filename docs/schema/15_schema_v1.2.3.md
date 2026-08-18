# Schema v1.2.3

確定日：2026-08-18  
対象：Schema v1.2.2のQA日付、区分網羅性証拠、公式粒度とUI粒度の分離

## 1. 変更目的

1. QAの `確認日` を固定日ではなく、自治体ごとの最新根拠日から決定する。
2. 区分網羅性レビューで複数の公式sourceを正規化して保持する。
3. 公式の分別粒度と教材UIの箱粒度を階層で分離する。

## 2. QA確認日

QAの `確認日` は、同一自治体の次の有効なISO日付の最大値とする。

- municipalities.`最終確認日`
- municipalities.`category_count_reviewed_date`
- categories.`確認日`
- sources.`取得確認日`

validatorは保存済みQA日と再計算値の一致を要求する。実行日や固定定数を使用しないため、再実行しても根拠が変わらない限り値は変化しない。

## 3. category review evidence

municipalitiesの単一 `category_count_evidence_source_id` を廃止し、`category_count_review_id` と `category_review_evidence` テーブルへ置換する。

- `OFFICIAL_COUNT_MATCHED` は1件以上の `OFFICIAL_TOTAL` 証拠を要求する。
- `MANUAL_INDEX_REVIEW` は1件以上の `PRIMARY_INDEX` 証拠を要求する。
- 補足ページは `SUPPLEMENTAL_INDEX` として複数保持できる。
- 全証拠は同じmunicipalityの公式sourcesを参照し、locatorを必須とする。
- 存在しないsource、別自治体source、非公式source、孤立reviewはvalidatorが拒否する。

完成Batchは従来6成果物に `category_review_evidence.csv` を加えた7成果物を必須とする。

## 4. 公式葉区分とUI投影

区分網羅性の件数は、CURRENTかつ非EXCLUDED_NOTICEのうち、CURRENT子区分を持たない公式葉区分を数える。教材UIの投影親は重複計上しない。

石巻市は次の構造とする。

- `びん類`：PRIMARY、`SORT_BUCKET`、教材UIの親箱
  - `一升びん・ビールびん・リターナブルびん`
  - `無色透明びん`
  - `茶色びん`
  - `その他色びん`

4子区分はSUBCATEGORYかつ `REFERENCE_ONLY` とし、公式19分別には4件として数える。初期mappingは投影親を候補にせず公式葉区分へ生成する。UIは子からCURRENT `SORT_BUCKET` 親へ投影できる。

## 5. Gate

- NEXT_BATCH_GATE：構造、QA、公式葉区分、複数source証拠、canonical union、merge冪等性、RED TEAMを要求する。
- APP_READINESS_GATE：上記に加えて全40品目のAPP_READYまたはVERIFIED_NOT_APPLICABLEを要求する。

2026-08-18時点でNEXT_BATCH_GATEはPASS、APP_READINESS_GATEはHOLD。Batch 02は未開始である。
