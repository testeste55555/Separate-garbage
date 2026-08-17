# Schema v1.1 Migration / Revalidation Report

実施日：2026-08-17  
対象：Pilot 5自治体 + Batch 01 10自治体（計15自治体）

## 結果

| 指標 | v1.0移行前 | v1.1移行後 | 判定 |
|---|---:|---:|---|
| 自治体 | 15 | 15 | 保持 |
| 分別区分 | 194 | 194 | 保持 |
| 出典 | 57 | 57 | 保持 |
| QA行 | 15 | 15 | 保持・再計算 |
| PLANNED区分 | 注意事項内 | 1 | 構造化 |
| 共通品目 | 0 | 40 | 新規 |
| item mapping条件枝 | 0 | 283 | 新規・初期確認待ち |

既存の主キー、正式名称、代表品目、前処理、袋・容器、条件、REFERENCE値、出典、確認日、備考を保持しました。Legacy列は削除していません。旧Pilotで親グループの記録がなかった28区分は、新しい自治体名称を作らず、当該区分の正式名称を単一要素の `category_group` として補完しました。

## v1.1への変換

- categories：`ui_role`, `rule_status`, `effective_from`, `effective_to` を追加
- sources：`official_verified`, `official_basis`, `official_linking_url` を追加
- municipalities：`official_category_count`, `category_count_basis`, `category_count_verified` を追加
- QA：必須判定、任意機能の確認済み/存在、Schema・参照・状態・UI検証を分離
- 公式ドメイン台帳を追加
- 共通40品目と4段階の教材安全区分を追加
- 既存categoryから初期item mappingを生成。品目別公式確認前は全件 `INITIAL_REVIEW_REQUIRED`

## 状態・UI投影

| 集計 | 件数 |
|---|---:|
| CURRENT | 193 |
| PLANNED | 1 |
| RETIRED | 0 |
| SORT_BUCKET | 152 |
| REFERENCE_ONLY | 25 |
| EXCLUDED_NOTICE | 16 |
| HIDDEN | 1 |

将来施行1区分は `PLANNED`、`effective_from=2026-10-01`、`ui_role=HIDDEN` へ移行し、現行の学習者用箱から除外しました。自治体ID固有のvalidator分岐は使用していません。

## 公式性

57/57 sourceが `official_verified=TRUE` です。

| official_basis | 件数 |
|---|---:|
| MUNICIPAL_DOMAIN | 54 |
| INTERMUNICIPAL_AUTHORITY_DOMAIN | 2 |
| MUNICIPAL_LINKED_SERVICE | 1 |

外部サービス1件は自治体公式ページからの導線URLを保持し、自治体公式ドメインと区別しました。

## 教材安全

| handling_safety | 品目数 |
|---|---:|
| SAFE_REAL | 6 |
| EMPTY_CLEAN_ONLY | 13 |
| TEACHER_ONLY | 6 |
| MOCK_ONLY | 15 |

全40品目に `safety_note` があります。

## 再validation

| 対象 | 自治体 | categories | sources | mappings | QA |
|---|---:|---:|---:|---:|---|
| Pilot | 5 | 60 | 25 | 93 | 5/5 PASS |
| Batch 01 | 10 | 134 | 32 | 190 | 10/10 PASS |
| canonical | 15 | 194 | 57 | 283 | 15/15 PASS |

実行結果：

```text
PILOT_VALIDATION_PASSED
BATCH_01_VALIDATION_PASSED
CANONICAL_VALIDATION_PASSED
```

QAは旧 `QA_PASSED` を引き継いだのではなく、v1.1データから再計算し、保存値と再計算値の一致まで検証しました。検索サービス・やさしい日本語・多言語が存在しない場合も、確認済みTRUE／存在FALSEとして区別しています。

## 再実行耐性

`build_batch_01.py` は生成直後にv1.1へ正規化します。`merge_research.py` はPilotの独立QAと完成batchのみを入力にし、canonical自身を入力へ戻しません。mergeを2回連続実行した後、canonical 5 CSVのSHA-256はすべて不変でした。

## 判定

Schema v1.1移行、既存15自治体の再validation、QAは完了です。Batch 02の調査は実施していません。
