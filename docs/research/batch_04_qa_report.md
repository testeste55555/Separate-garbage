# Batch 04 QA Report

実施日: 2026-08-19  
Schema: v1.2.4  
Workflow: v1.13

## 対象

MASTER順の M034〜M043。

- M034 若桜町
- M035 智頭町
- M036 八頭町
- M037 三朝町
- M038 湯梨浜町
- M039 琴浦町
- M040 北栄町
- M041 日吉津村
- M042 大山町
- M043 南部町

10自治体すべて `MANUAL_INDEX_REVIEW / QA_PASSED`。

## 成果

Batch 04追加量:
- municipalities: 10
- categories: 115
- official sources: 26
- initial item mapping branches: 101
- coverage: 400 municipality-item pairs
- category review evidence: 26

canonical累計:
- municipalities: 45
- categories: 586
- structured official leaves: 537
- official sources: 136
- initial item mapping branches: 586
- coverage: 1,800 pairs
- category review evidence: 100
- QA: 45 QA_PASSED / 0 QA_REQUIRED

## v1.2.4適用上の主要判断

### 東部3町 M034-M036

若桜町・智頭町・八頭町は、可燃、缶・びん/資源、プラスチック、PET、小型破砕、大型資源、乾電池類、有害ごみという住民向け体系を自治体ごとの正式名称のまま保持した。

令和6年4月からの有害ごみ新設、白色トレイのプラスチック統合、PETの出し方変更等を現行ルールへ反映した。

### 三朝町 M037

令和8年度前期収集日程表に実際に表示される11ラベルを住民向け体系として採用した。令和8年4月から充電式電池を有害ごみとして出せる変更を反映した。

### 湯梨浜町 M038 / 琴浦町 M039 / 北栄町 M040

鳥取中部地域でも自治体公式の住民向け区分数と名称をそのまま保持した。

- 湯梨浜町: 12
- 琴浦町: 13
- 北栄町: 12

広域処理主体が共通でも名称・分け方を自治体間で一律化しない。

### 日吉津村 M041

詳細50音表の細分類をすべて独立箱にせず、現在の村公式「ごみの収集日について」で住民が選択する7ラベルをPRIMARYな分別体系とした。

1. もえるゴミ
2. もえないゴミ
3. 布・プラスチック類（資源ゴミ）
4. 発泡スチロール（資源ゴミ）
5. その他資源ゴミ
6. 蛍光灯
7. 乾電池

詳細50音表は品目別条件と収集不可の補助証拠として使用する。

### 大山町 M042

令和8年1月改訂版手引きを主根拠にしつつ、令和8年4月1日の変更を優先した。

- 紙製容器包装の独立収集終了 → 古紙類へ
- 指定びん（生きびん）の独立収集終了 → 缶・びんへ
- 発泡スチロール → 白色のみ回収

したがって廃止済み2区分をCURRENT categoryとして残していない。

### 南部町 M043

町公式分別表の住民向け資源区分を保持し、令和8年度カレンダーで現行性を確認した。小型家電はDROP_OFF/REFERENCE_ONLY、収集不可はEXCLUDED_NOTICEとして住民の通常仕分け箱と分離する。

## RED TEAM

Batch 04専用RED TEAMでは以下を含む14観点を確認する。

- 構造validation
- M034〜M043の正確な対象集合
- 10/10 QA_PASSED
- 空欄回避プレースホルダ禁止
- 東部3町の乾電池類・有害ごみ保持
- 三朝町11ラベル保持
- 湯梨浜町12区分
- 琴浦町13区分
- 北栄町12区分＋有害ごみ
- 日吉津村7ラベル
- 大山町の廃止区分が復活していない
- 大山町の白色発泡スチロール条件
- 南部町の資源系区分保持

CI結果:
- Batch 04 structural validation: PASS
- canonical structural validation: PASS
- Schema v1.2.4 RED TEAM: PASS
- Batch 04 RED TEAM: PASS
- NEXT_BATCH_GATE: PASS

実行証跡: `docs/research/batch_04_ci_status.txt`

## Gate

- NEXT_BATCH_GATE: PASS
- APP_READINESS_GATE: HOLD

APP_READINESS_GATEは45自治体×40品目の品目別公式証拠・全条件枝レビューが未完了のため正常なHOLD。
