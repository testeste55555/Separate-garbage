# Style Research Data Dictionary v1.0

## `03_top10_targets.csv`

| 列 | 必須 | 定義 |
|---|---:|---|
| rank | Yes | 事前確定順位1〜10 |
| stage | Yes | AまたはB |
| municipality_id | Yes | MASTER固定ID |
| municipality_name | Yes | MASTER市町村名 |
| canonical_status | Yes | ACTIVE / DEFERRED |
| style_research_status | Yes | COMPLETED / RESEARCHED_CANONICAL_DEFERRED |
| district_scope_required | Yes | 地域variant必須か |
| current_sort_bucket_count | Yes | active自治体のCURRENT/SORT_BUCKET直積件数。DEFERREDは0 |
| source_ids | Yes | style source_idのセミコロン区切り |
| note | Yes | 調査・保留理由 |

## `08_style_color_observations.csv`

| 列 | 必須 | 定義 |
|---|---:|---|
| style_id | Yes | 観測主キー |
| rank / stage | Yes | 固定順位・A/B |
| municipality_id | Yes | MASTER参照 |
| district_scope | Yes | 色が適用される地域scope |
| category_id | Yes | category正本参照。DEFERRED自治体では発行禁止 |
| 自治体正式名称 | Yes | category正本のsnapshot |
| evidence_role | Yes | DESIGNATED_BAG / COLLECTION_CONTAINER / STATION_SIGN / OFFICIAL_CALENDAR / OFFICIAL_POSTER_GUIDE |
| official_color_label | 条件 | 公式記載色名または視覚色ラベル |
| display_color | 条件 | `#RRGGBB`。DERIVEDは近似値。NOT_CONFIRMEDは空欄 |
| color_status | Yes | OFFICIAL_CONFIRMED / OFFICIAL_DERIVED / FALLBACK / NOT_CONFIRMED |
| color_basis | Yes | 何が区分識別色であるかを具体記録 |
| semantic_fit | Yes | category識別性の判定 |
| ui_selection | Yes | PRIMARY / SUPPORTING / REJECTED / NOT_APPLICABLE |
| source_id / source_url / source_locator | 公式行Yes | 追跡可能な公式根拠 |
| checked_date | Yes | ISO日付 |
| reviewer | Yes | 確認主体 |
| note | Yes | 近似・共有・競合等の注意 |

`OFFICIAL_DERIVED` は有効HEXと「近似」のnoteが必須。`OFFICIAL_CONFIRMED` で数値HEXを入れる場合は公式RGB/HEX明示がbasisに必要。`FALLBACK` は公式sourceを持てない。

## `08_style_ui_projection.csv`

| 列 | 必須 | 定義 |
|---|---:|---|
| projection_id | Yes | UI判断主キー |
| municipality_id / district_scope / category_id | Yes | 論理一意キー |
| 自治体正式名称 | Yes | category正本と一致 |
| display_color | 条件 | UI背景/アクセント候補 |
| border_color | 条件 | アプリ計算の独立枠線色 |
| text_color | 条件 | アプリ計算色。displayとのコントラスト4.5:1以上 |
| color_status | Yes | 公式性・未確認状態 |
| color_basis | Yes | 採否の根拠 |
| selected_style_id | 公式採用時Yes | PRIMARY観測参照。NOT_CONFIRMEDは空欄 |
| accessibility_label_required | Yes | 常にTRUE |
| icon_status | Yes | PilotではNOT_RESEARCHED_AS_OFFICIAL |
| checked_date / reviewer / note | Yes | 監査証跡 |

## `09_style_sources.csv`

| 列 | 必須 | 定義 |
|---|---:|---|
| source_id | Yes | style出典主キー |
| municipality_id | Yes | 対象自治体 |
| district_scope | Yes | 資料適用地域 |
| source_title / source_type | Yes | 公式資料名・種別 |
| source_url / source_locator | Yes | 公式URLとページ内位置 |
| evidence_roles | Yes | 色用途。複数はセミコロン区切り |
| priority | Yes | 1〜4。指定の根拠優先順位 |
| currentness | Yes | PilotではCURRENT |
| official_verified / official_basis | Yes | TRUE / MUNICIPAL_DOMAIN |
| checked_date / note | Yes | 取得日・補足 |
