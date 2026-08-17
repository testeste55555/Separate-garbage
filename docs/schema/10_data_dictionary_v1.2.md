# Data Dictionary v1.2

確定日：2026-08-17  
本書はv1.1からの変更・追加を定義する。未記載列はv1.1を継承する。

## municipalities追加列

| 列 | 型・列挙 | 必須性 | 説明 |
|---|---|---|---|
| category_count_check_status | enum | 必須 | OFFICIAL_COUNT_MATCHED / MANUAL_INDEX_REVIEW / NOT_REVIEWED |
| category_count_evidence_source_id | string | 条件付き | verified時の同一自治体source |
| category_count_reviewed_date | date | 条件付き | verified時必須 |
| category_count_reviewed_by | string | 条件付き | 人または検証処理の識別子 |
| search_service_check_status | enum | 必須 | CHECKED_PRESENT / CHECKED_ABSENT / NOT_CHECKED |
| search_service_check_evidence | string | 条件付き | checked時のURL・範囲・確認日 |
| easy_japanese_check_status | enum | 必須 | 同上 |
| easy_japanese_check_evidence | string | 条件付き | 同上 |
| multilingual_check_status | enum | 必須 | 同上 |
| multilingual_check_evidence | string | 条件付き | 同上 |

`category_count_verified=TRUE` は `category_count_check_status` がverified状態で、公式source・根拠・日付・reviewerが揃う場合だけ許可する。`NOT_REVIEWED` はFALSE固定である。

`CHECKED_PRESENT` はHTTPS URLと証跡中の同一URL・確認日が必要である。`CHECKED_ABSENT` は空URL、調査した公式URL、確認日が必要である。`NOT_CHECKED` はURL・証跡を空にする。

## categories必須性変更

| 列 | v1.2必須性 | 説明 |
|---|---|---|
| 袋・容器のルール | REFERENCE | 指定袋・透明袋・結束等。分類を変える条件はCORE列へ記録 |
| collection_channel | REFERENCE | `ui_role` の算出に使わない |
| ui_role | 必須・独立値 | UI用途を明示し、他列から再推論しない |

## item_mapping追加列

| 列 | 型・列挙 | 必須性 | 説明 |
|---|---|---|---|
| evidence_scope | enum | 必須 | NONE / CATEGORY_LEVEL / ITEM_SPECIFIC |
| branch_review_status | enum | 必須 | UNREVIEWED / INCOMPLETE / COMPLETE |
| reviewed_date | date | VERIFIED/APP_READY | レビュー日 |
| reviewed_by | string | VERIFIED/APP_READY | reviewer識別子 |

`mapping_status` は `INITIAL_REVIEW_REQUIRED / VERIFIED / APP_READY`。APP_READYは `ITEM_SPECIFIC`, `COMPLETE`, 公式source、日付、reviewer、公式品目表記を必要とする。

## item_mapping_coverage

| 列 | 型・列挙 | 必須性 | 説明 |
|---|---|---|---|
| municipality_id | string | 必須 | municipality参照 |
| internal_item_id | string | 必須 | common item参照 |
| coverage_status | enum | 必須 | NOT_RESEARCHED / MAPPED_INITIAL / VERIFIED / VERIFIED_NOT_APPLICABLE / APP_READY |
| mapping_branch_count | integer | 必須 | 同pairのmapping実数と一致 |
| branch_completeness_confirmed | boolean | 必須 | 条件枝の網羅性確認 |
| evidence_scope | enum | 必須 | NONE / CATEGORY_LEVEL / ITEM_SPECIFIC |
| source_id | string | reviewed状態 | 同一自治体公式source |
| 出典URL | HTTPS URL | reviewed状態 | 品目別根拠 |
| 出典ページ・該当箇所 | string | reviewed状態 | 品目の行・見出し・ページ |
| reviewed_date | date | reviewed状態 | YYYY-MM-DD |
| reviewed_by | string | reviewed状態 | reviewer識別子 |
| notes | string | 任意 | 未調査・条件枝等の説明 |

主キーは `(municipality_id, internal_item_id)`。各datasetで自治体数×40行を必須とする。

## qa変更

- `袋容器` は情報品質の観測値として残すが、QA_PASSED必須集合から外す。
- 任意機能の `存在` は TRUE / FALSE / UNKNOWN。未確認はUNKNOWNである。
- 任意機能の `確認済み` は元のcheck_statusから算出するが、分別QA Gateにはしない。
- `全分別区分` と `category_count_verified` は網羅性証跡から再計算する。

