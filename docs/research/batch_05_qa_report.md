# Batch 05 QA Report

実施日: 2026-08-19  
Schema: v1.2.4  
対象: M044〜M053

## 1. 対象と結果

| ID | 自治体 | reviewed_category_count | QA |
|---|---|---:|---|
| M044 | 伯耆町 | 11 | QA_PASSED |
| M045 | 日南町 | 26 | QA_PASSED |
| M046 | 日野町 | 13 | QA_PASSED |
| M047 | 江府町 | 19 | QA_PASSED |
| M048 | 松江市 | 7 | QA_PASSED |
| M049 | 浜田市 | 8 | QA_PASSED |
| M050 | 出雲市 | 13 | QA_PASSED |
| M051 | 益田市 | 13 | QA_PASSED |
| M052 | 大田市 | 7 | QA_PASSED |
| M053 | 安来市 | 16 | QA_PASSED |

Batch 05: **10 QA_PASSED / 0 QA_REQUIRED**。

## 2. 追加量

- municipality: 10
- category: 139行
- 構造化公式葉: 133
- source: 26
- initial item mapping: 95条件枝
- coverage: 400 pair
- category review evidence: 26

canonical統合後:

- municipality: **55**
- category: **725行**
- 構造化公式葉: **670区分**
- source: **162**
- item mapping: **681条件枝**
- coverage: **2,200 pair**
- category review evidence: **126行**
- QA: **55 QA_PASSED / 0 QA_REQUIRED**

## 3. 住民向け区分の判断

Schema v1.2.4に従い、処理施設内部の分類ではなく、住民が排出時に実際に選択する自治体公式の分別体系を採用した。

### M045 日南町

町公式が「現在、ごみを26種類に分別して収集」と明示しているため、袋色などに縮約せず26種類を保持した。処理困難物はEXCLUDED_NOTICEとして別保持し、26には数えない。

### M046 日野町

令和8年度カレンダーに表示される12の定期収集ラベルを保持した。加えて、同じ公式資料で住民に明示される「充電式小型家電」の役場・黒坂支所への拠点回収経路を`REFERENCE_ONLY`で保持するため、`reviewed_category_count=13`となる。

この1行は学習者用の仕分け箱には投影されない。12収集ラベルと1補助経路を混同しない。

### M048 松江市

公式ページの「資源」は概念上の親であり、住民は古紙・古着／紙製容器包装／プラスチック製容器包装／缶・びん・ペットボトルへ分けるため、親「資源」を独立葉として二重計上しない。

### M049 浜田市

一般家庭向けページの公開日は古いが、令和8年度収集日程と現行公式索引で同体系の稼働を確認したためCURRENTとした。2016年3月で収集終了した古着・古布はCURRENT区分へ復活させていない。

### M052 大田市

住民向けカレンダーで使用される資源物A／B／Cグループをそのまま保持し、内部品目を人工的に独立SORT_BUCKETへ分解しない。

## 4. 真正性

- 自治体公式Web・公式PDFを使用した。
- 古い公式ページは現年度カレンダー・現行公式導線でCURRENT性を補強した。
- sourceに記載がない詳細は`NOT_STATED_IN_CITED_SOURCE`を使用した。
- 汎用プレースホルダは使用していない。
- 地域差・自治体独自名称を隣接自治体に合わせて正規化していない。

## 5. RED TEAM / CI

GitHub Actionsで以下を再実行した。

- Batch 05 structural validation: PASS
- canonical structural validation: PASS
- Schema v1.2.4 RED TEAM: PASS
- Batch 05 dedicated RED TEAM: PASS
- NEXT_BATCH_GATE: PASS

Batch 05専用RED TEAMでは、日南町26区分、日野町の12収集ラベル＋補助経路、松江市の親「資源」二重計上防止、浜田市の終了済み古着収集非復活、大田市A/B/Cグループ保持、安来市の詳細紙類区分等を検査する。

## 6. Gate

### NEXT_BATCH_GATE: PASS

Batch 06開始可。

### APP_READINESS_GATE: HOLD

55自治体×40品目の品目別公式根拠・条件枝レビューが未完了のため、正常なHOLD。
