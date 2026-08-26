# 画像10品目 × Style Research active 8自治体 mapping Pilot

確認日：2026-08-24  
reviewer：`OPENAI_CODEX_IMAGE_MAPPING_PILOT_V1`

## 範囲

Style Research TOP10のうち、municipality-wide category正本が確定している次の8自治体を対象とした。

- M094 広島市
- M095 呉市
- M097 三原市
- M104 東広島市
- M105 廿日市市
- M106 安芸高田市
- M107 江田島市
- M109 海田町

M098尾道市とM099福山市は地域別CURRENT taxonomyが併存するため対象外とした。municipality単位へ推測統合しない。

品目は `data/app/item_image_assets.csv` のCONFIRMED 10品目。正本名称は `data/master/04_common_items_master.csv`、分別先は `data/research/02_categories_master.csv` を参照した。

## 結果

| 判定 | 組数 | 意味 |
|---|---:|---|
| VERIFIED | 76 | 同一自治体の公式source・URL・locatorとcategory参照を確認 |
| UNRESOLVED | 4 | 現行資料で品目単位の分別先を確証できず、推測しない |
| APP_READY | 0 | 条件枝完全性レビュー前のため昇格しない |

`DIRECT_ITEM`は68組、公式categoryの対象例・共通条件から品目へ適用した`OFFICIAL_CATEGORY_RULE`は8組。

### UNRESOLVED

- M107 江田島市：I031 電球、I033 使い捨てライター
- M109 海田町：I031 電球、I033 使い捨てライター

蛍光管・危険物一般の記載を、電球・ライターの個別分別先へ読み替えていない。公式50音辞典等で確認できた時点で別レビューする。

### M106 I029の現行資料優先訂正（2026-08-26）

安芸高田市の現行モバイルバッテリー直接案内は、一般ごみと小型家電回収ボックスへの投入を不可とし、販売店・リサイクル業者への引取を指定している。旧Pilotの一般的な「小型充電式電池」記載から`有害ごみ`へ投影した判断を撤回し、`C-M106-14 / EXCLUDED_NOTICE`へ訂正した。`VERIFIED`は公式経路の確認を意味するが、この行は通常の仕分けBOXにも`LESSON_READY_10`にも使用しない。

## データ境界

- `data/app/item_image_mapping_pilot_top8.csv` は画像10品目と自治体分別先のPilot判断台帳。
- category正本、item mapping正本、coverage正本のID・名称は変更しない。確定76組のreview metadataと品目別根拠のみ同期した。
- 品目別追加公式sourceは`IS-*`名前空間で保持する。
- `IS-*`の取得日はAPP品目レビューに使うが、自治体/category QA日を更新しない。両Gateを独立させる。
- `branch_review_status=INCOMPLETE`、`branch_completeness_confirmed=FALSE`を維持し、`APP_READY`へは昇格しない。
- 直接品目案内が通常categoryの一般記載と競合する場合は直接品目案内を優先し、非BOX経路を`EXCLUDED_NOTICE`として保持する。

## UI HANDOFF

1. 画像は `item_image_assets.csv` の `internal_item_id` で解決する。
2. 自治体選択後、Pilotの`VERIFIED`行だけをcategoryへ結び付ける。
3. category表示色はStyle Research projectionから取得し、画像や品目masterへ色を埋め込まない。
4. `UNRESOLVED`は正誤判定対象にせず、「現在確認中」等の非判定状態として扱う。
5. `VERIFIED`は公式根拠確認済みを意味するが、全条件枝の完全性は保証しない。公開判定には既存APP readiness Gateを使う。

## QA / RED TEAM

- Pilot validator：PASS（80組、76 VERIFIED、4 UNRESOLVED、0 APP_READY）
- mutation RED TEAM：9/9 PASS
- M106 LESSON_READY_10 preflight blocker validator／mutation：PASS
- canonical research validation：PASS
- item image assets validation：PASS
- Teaching Display Layer：PASS
- Style Research Gate / RED TEAM：PASS

## 主要な公式根拠

- 広島市：家庭ごみ分別50音事典、家庭ごみの正しい出し方、小型充電式電池案内
- 呉市：令和8年度からのごみの出し方
- 三原市：現行分別方法と50音順一覧
- 東広島市：ごみブック、小型充電式電池案内、紙資源案内
- 廿日市市：令和8年4月版ごみ分別一覧表
- 安芸高田市：家庭ごみの出し方
- 江田島市：令和8年度改定版 家庭ごみの種類と正しい出し方
- 海田町：令和8年度 家庭ごみの正しい出し方、モバイルバッテリー案内

各URLとlocatorは `data/research/03_sources_master.csv` およびPilot台帳に保存した。
