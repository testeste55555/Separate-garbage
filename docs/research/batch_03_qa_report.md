# Batch 03 QA Report

実施日: 2026-08-19  
適用Schema: v1.2.3  
適用Workflow: v1.11

## 1. 対象

MASTER順の未調査自治体から次の10自治体を対象とした。M030米子市はPilotで既調査のため除外した。

| ID | 自治体 | QA | 網羅性 |
|---|---|---|---|
| M023 | 大阪市 | QA_PASSED | MANUAL_INDEX_REVIEW |
| M024 | 神戸市 | QA_PASSED | MANUAL_INDEX_REVIEW |
| M025 | 豊岡市 | QA_PASSED | MANUAL_INDEX_REVIEW |
| M026 | 姫路市 | QA_PASSED | MANUAL_INDEX_REVIEW |
| M027 | 大和郡山市 | QA_PASSED | MANUAL_INDEX_REVIEW |
| M028 | 由良町 | QA_REQUIRED | NOT_REVIEWED |
| M029 | 鳥取市 | QA_PASSED | MANUAL_INDEX_REVIEW |
| M031 | 倉吉市 | QA_PASSED | MANUAL_INDEX_REVIEW |
| M032 | 境港市 | QA_PASSED | MANUAL_INDEX_REVIEW |
| M033 | 岩美町 | QA_PASSED | MANUAL_INDEX_REVIEW |

Batch 03: 9 QA_PASSED / 1 QA_REQUIRED。

## 2. 成果物

`data/research/batches/batch_03/` に7成果物を保存した。

1. `batch_03_municipalities.csv`
2. `batch_03_categories.csv`
3. `batch_03_sources.csv`
4. `batch_03_qa.csv`
5. `batch_03_item_mapping.csv`
6. `batch_03_item_coverage.csv`
7. `batch_03_category_review_evidence.csv`

Batch 03追加量:
- municipality: 10
- category: 115
- source: 24
- item mapping: 86初期条件枝
- coverage: 400 pair
- category review evidence: 22

canonical統合後:
- municipality: 35
- category: 471
- 構造化公式葉: 430（M028の5葉は区分網羅性未証明）
- source: 110
- item mapping: 485
- coverage: 1,400 pair
- category review evidence: 72
- QA: 34 QA_PASSED / 1 QA_REQUIRED

## 3. 真正性方針

- 公式自治体サイト・公式PDFを優先した。
- category詳細はsource_id / URL / locatorへ戻って確認した。
- sourceに個別記載のないCORE詳細は`NOT_STATED_IN_CITED_SOURCE`とした。
- 空欄回避の汎用文は使用しない。
- 地域限定区分は適用条件を残し、市内差を消さない。
- 全区分体系を証明できない自治体は`NOT_REVIEWED / QA_REQUIRED`で停止する。

## 4. 由良町 M028 Evidence Hold

取得できた現行一次資料:
- 由良町公式サイト
- 由良町公式「広報ゆら 2026年3月号」

同広報のごみカレンダーから、少なくとも次の収集ラベルを確認した。
- 可燃1 / 可燃2
- プラスチック
- 不燃
- 資源1 / 資源2
- 粗大ごみ

可燃1/2・資源1/2は地域グループ差として扱い、category上は「可燃ごみ」「資源ごみ」に統合した。

しかし当該広報は「全分別区分の索引・見出し一覧」ではなく、乾電池・ペットボトル等を含む由良町の現行分類体系全体を証明できない。そのため:

- `category_count_verified=FALSE`
- `category_count_check_status=NOT_REVIEWED`
- `確認ステータス=QA_REQUIRED`
- category review evidenceは作成しない

とした。

補助確認として、環境省「御坊周辺地域 循環型社会形成推進地域計画」には由良町の分別区分として燃やせるごみ、プラスチック系、燃やせる/燃やせない大型ごみ、ペットボトル、乾電池等が掲載されている。ただし、これは自治体・広域処理主体の現行一次資料ではないため、Schema v1.2.3の区分網羅性証拠には使用していない。

また、御坊市公式サイトは御坊広域清掃センターが由良町を含む6市町のごみを受け入れることを確認でき、御坊広域行政事務組合公式サイトへの導線も確認できる。しかし、由良町の現行家庭ごみ全区分表として利用できる資料は今回取得できなかった。

## 5. RED TEAM / CI

GitHub Actionsで以下を実行した。

- Batch 03 structural validation: PASS
- canonical structural validation: PASS
- Schema v1.2.3 RED TEAM: PASS
- Batch 03 dedicated RED TEAM: PASS
- NEXT_BATCH_GATE: HOLD

Batch 03 dedicated RED TEAMでは特に、M028を不十分な証拠のまま`QA_PASSED`へ自動昇格させないことを検査する。

実行証跡: `docs/research/batch_03_ci_status.txt`

## 6. Gate判定

### NEXT_BATCH_GATE: HOLD

理由: M028由良町が`QA_REQUIRED`。

Batch 04は開始しない。

### APP_READINESS_GATE: HOLD

全35自治体×40品目の品目別公式根拠・条件枝レビューが未完了のため正常なHOLD。

## 7. 次の作業

M028について次の順で公式網羅性証拠を再探索する。

1. 由良町公式サイト内のごみ・リサイクルページ／分別冊子
2. 由良町公式ページから御坊広域行政事務組合への公式導線
3. 御坊広域行政事務組合が公開する由良町適用の現行分別資料
4. 現行一般廃棄物処理実施計画等

いずれかで全区分体系を確認できた場合のみMANUAL_INDEX_REVIEWまたはOFFICIAL_COUNT_MATCHEDへ昇格し、Batch 03を再validationする。
