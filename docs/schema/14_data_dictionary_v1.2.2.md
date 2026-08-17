# Data Dictionary v1.2.2

確定日：2026-08-17  
本書はv1.2.1を継承し、追加・名称変更した列を定義する。

## municipalities

| 列 | 型・制約 | 必須条件 | 説明 |
|---|---|---|---|
| `official_category_count` | integer | OFFICIAL_COUNT_MATCHED | 公式資料に明記された総数。MANUAL_INDEX_REVIEWでは空欄可 |
| `reviewed_category_count` | integer | MANUAL_INDEX_REVIEW | 人が公式目次・見出しを全件照合した件数 |
| `category_count_basis` | string | verified状態 | 総数の記載位置、または手動照合したページ・章・見出し範囲 |
| `category_count_evidence_source_id` | reference | verified状態 | 同一自治体の公式source |
| `category_count_reviewed_date` | date | verified状態 | YYYY-MM-DD |
| `category_count_reviewed_by` | string | verified状態 | reviewer識別子 |

`OFFICIAL_COUNT_MATCHED` はofficial countと構造化件数の一致を要求し、reviewed countは空欄とする。`MANUAL_INDEX_REVIEW` はreviewed countと構造化件数の一致を要求し、official countを要求しない。optionalなofficial countを記入した場合は数値かつ構造化件数と一致しなければならない。

## item_mapping

v1.2.1の `source_id / 出典URL / 出典ページ・該当箇所` を次の6列へ置換する。

| 列 | 型・制約 | 必須条件 | 説明 |
|---|---|---|---|
| `category_source_id` | reference | 全行 | 参照categoryと同じsource |
| `category_source_url` | HTTPS URL | 全行 | 参照categoryと同じURL |
| `category_source_locator` | string | 全行 | 参照categoryと同じ該当箇所 |
| `item_evidence_source_id` | reference | VERIFIED / APP_READY | 品目判断を裏づける同一自治体公式source |
| `item_evidence_url` | HTTPS URL | VERIFIED / APP_READY | item evidence sourceの公式URLと一致 |
| `item_evidence_locator` | string | VERIFIED / APP_READY | 品目行、索引語、見出し、ページ等 |

categoryとitemは異なるsourceを参照できる。`INITIAL_REVIEW_REQUIRED` はitem evidence 3列を空欄とする。

`VERIFIED` は `evidence_scope=ITEM_SPECIFIC`、item evidence 3列、reviewed_date、reviewed_byを必須とする。`APP_READY` はこれらに加えて `branch_review_status=COMPLETE` と人が確認した公式品目表記を必須とする。

## item_mapping_coverage

旧 `source_id / 出典URL / 出典ページ・該当箇所` を次の3列へ名称変更する。

| 列 | 型・制約 | 必須条件 | 説明 |
|---|---|---|---|
| `item_evidence_source_id` | reference | reviewed状態 | 同一自治体公式source |
| `item_evidence_url` | HTTPS URL | reviewed状態 | sourceの公式URLと一致 |
| `item_evidence_locator` | string | reviewed状態 | 品目別確認位置 |

reviewed状態は `VERIFIED / VERIFIED_NOT_APPLICABLE / APP_READY`。この3状態はITEM_SPECIFIC、item evidence 3列、reviewed_date、reviewed_byを必須とする。NOT_RESEARCHEDとMAPPED_INITIALはitem evidence 3列を空欄にする。
