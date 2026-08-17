# Schema v1.1

確定日：2026-08-17  
対象：家庭ごみ分別（収集曜日・時刻・地区別日程を除く）

## 1. 設計原則

1. 自治体の正式名称と条件を保持し、全国共通名へ置換しない。
2. 分別判断に必要なCOREと、運用補助のREFERENCEを分離する。
3. 将来・終了ルールを現行ルールから分離する。
4. 学習者用の箱は `ui_role` で決定し、推測しない。
5. QAは保存値を信用せず、元データから機械再計算する。
6. 公式性はURL文字列だけでなく公式ドメイン台帳で確認する。
7. 共通品目と自治体区分の対応は条件枝を失わない。

## 2. テーブル

| テーブル | 主キー | 役割 |
|---|---|---|
| municipalities | `municipality_id` | 自治体の公式導線、現行性、区分数根拠 |
| categories | `(municipality_id, category_id)` | 自治体の正式な分別区分と条件 |
| sources | `(municipality_id, source_id)` | 公式根拠資料と公式性の判定根拠 |
| official_domain_registry | `(municipality_id, host)` | 公式・一部事務組合・公式案内外部サービスの台帳 |
| common_items | `internal_item_id` | 自治体横断の代表品目と教材安全区分 |
| item_mapping | `mapping_id` | 共通品目から自治体区分への条件付き対応 |
| qa | `municipality_id` | 必須・任意チェックの機械判定結果 |

## 3. CORE / REFERENCE

### CORE必須

分別判断と根拠追跡に常に必要な値です。

- 識別：`municipality_id`, `category_id`
- 表示・階層：`自治体正式名称`, `category_group`, `classification_level`, `表示順`, `ui_role`
- 判断：`代表品目`, `入れてはいけない物`, `条件外の扱い`, `出す前の処理`, `袋・容器のルール`, `自治体収集外か`
- 根拠：`source_id`, `出典URL`, `出典ページ・該当箇所`, `確認日`
- 時点：`rule_status`

### CORE条件付き／任意

条件が存在する場合、または状態により必要になる値です。

- `parent_category_id`：親区分がある場合
- `適用条件`, `サイズ・条件`, `注意事項`：該当条件がある場合
- `effective_from`：`PLANNED` の場合は必須
- `effective_to`：`RETIRED` の場合は必須

### REFERENCE

既存15自治体で収集済みの値は保持しますが、今後の全自治体調査で一律必須にはしません。

- `collection_channel`
- `粗大ごみ扱いか`
- `予約が必要か`
- `有料か`
- `料金ルール`
- 直接搬入、代替処分経路、回収拠点、メーカー・販売店回収に関する情報

REFERENCEが分別結果や安全説明に必要な場合は記録します。

## 4. 時点管理

`rule_status` は次の3値です。

| 値 | 意味 | 日付条件 | 学習者用投影 |
|---|---|---|---|
| `CURRENT` | 現在適用 | 日付は任意 | `ui_role`に従う |
| `PLANNED` | 将来施行 | `effective_from`必須 | `HIDDEN` |
| `RETIRED` | 適用終了 | `effective_to`必須 | `HIDDEN` |

状態は自治体IDで分岐せず、sourceの現行性、適用条件、施行日から決定します。

## 5. 学習者用投影

`ui_role` は次の4値です。

| 値 | 用途 |
|---|---|
| `SORT_BUCKET` | 現行の学習者用仕分け箱 |
| `REFERENCE_ONLY` | 搬入・拠点回収・代替経路等の参照情報 |
| `HIDDEN` | 将来・終了ルール等、現在の箱に出さない情報 |
| `EXCLUDED_NOTICE` | 自治体収集外・処理不可の注意 |

現在の箱は `rule_status=CURRENT AND ui_role=SORT_BUCKET` のみです。`classification_level` からUI側で再推測しません。

## 6. 公式性

QA_PASSEDに使用するsourceは `official_verified=TRUE` が必須です。

- `MUNICIPAL_DOMAIN`：自治体公式ドメイン
- `INTERMUNICIPAL_AUTHORITY_DOMAIN`：一部事務組合等の公式ドメイン
- `MUNICIPAL_LINKED_SERVICE`：自治体公式ページから案内された外部サービス

外部サービスは `official_linking_url` に自治体公式導線を保持します。台帳にないhostは公式扱いしません。

## 7. 共通品目・mapping・教材安全

共通品目は40件です。`handling_safety` は以下の4値です。

- `SAFE_REAL`
- `EMPTY_CLEAN_ONLY`
- `TEACHER_ONLY`
- `MOCK_ONLY`

`safety_note` を必須とします。

item mappingは `(municipality_id, internal_item_id)` に複数の `branch_order` を許し、材質・汚れ・大きさ・電池着脱等の条件分岐を保持します。初期機械抽出は `INITIAL_REVIEW_REQUIRED` とし、品目別公式確認前に `APP_READY` へ昇格しません。

## 8. QA_PASSED

次の必須チェックがすべてTRUE、必須欄にUNKNOWNなし、参照整合性とSchema検証が成功した場合のみ `QA_PASSED` です。

`ごみトップ`, `現行ルール`, `全分別区分`, `正式名称`, `代表品目`, `前処理`, `袋容器`, `危険有害`, `収集しない物`, `公式出典`, `参照整合性`, `Schema検証`, `category_count_verified`, `rule_status検証`, `ui_role検証`

検索サービス・やさしい日本語・多言語は「確認済み」と「存在」を別列にします。存在FALSEはQA不合格理由ではありません。

分別区分数に固定下限は設けません。公式件数が明示される場合だけ `official_category_count` と構造化件数を照合し、その他は `category_count_basis` をレビューします。

## 9. 参照整合性

- すべての自治体IDは143自治体MASTERに存在する。
- categoriesのsourceは同じ自治体のsourcesに存在する。
- `parent_category_id` は同じ自治体のcategory、または空欄である。
- sourcesとcategory出典URLのhostは公式ドメイン台帳に存在する。
- item mappingはcommon item、category、sourceを参照し、categoryの状態・出典と一致する。
- 主キーと条件枝キーは一意である。
