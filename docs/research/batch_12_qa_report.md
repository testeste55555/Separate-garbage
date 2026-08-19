# Batch 12 QA Report

実施日: 2026-08-19
Schema: v1.2.4
MASTER範囲: M116〜M125

## 判定

**PASS**

- active: 8自治体
- QA_PASSED: 8/8
- 新規DEFERRED: 2自治体（M120 萩市、M123 岩国市）
- Batch structural validation: PASS
- Batch 12専用RED TEAM: PASS
- canonical merge: PASS
- canonical structural validation: PASS
- Schema v1.2.4 RED TEAM: PASS
- operational category semantics RED TEAM: PASS
- NEXT_BATCH_GATE: PASS
- APP_READINESS_GATE: HOLD

CI記録: `docs/research/batch_12_ci_status.txt`

## active自治体と公式葉

- M116 神石高原町: 18
- M117 下関市: 10
- M118 宇部市: 13
- M119 山口市: 15
- M121 防府市: 18
- M122 下松市: 15
- M124 光市: 14
- M125 長門市: 17

合計公式葉: **120**。
投影親・category_group等を含むcategory行は **132**。

全8自治体で、現行公式資料のresident-facing leafを手作業で全件照合し、`MANUAL_INDEX_REVIEW`を使用した。

## DEFERRED

### M120 萩市

令和8年度も、市公式50音表が**大島・見島・相島地区では一部分別区分が異なる**ことを明示している。単なる収集曜日差ではなく、同一自治体内に複数のCURRENT resident-facing taxonomyが併存するため、現行municipality単位Schema/UIでは安全に単一化できない。

判定: `SCHEMA_SCOPE_LIMITATION`

### M123 岩国市

令和8年度に岩国・由宇・周東・玖珂と錦・美川・美和・本郷等でCURRENTルールが併存し、食品トレー等について実際の分別先・排出方法が異なる。単なるカレンダー差ではないため、一つの岩国市ルールへ統合しない。

判定: `SCHEMA_SCOPE_LIMITATION`

固定IDは保持し、地域scope対応後に再開可能とする。

## 真正性確認

- 神石高原町: `空きカン`はスチール缶／アルミ缶／その他の缶、`空きビン`は無色／茶色／その他、`不燃物・容器包装以外のプラスチック`は4住民区分を別袋で排出するため公式葉として保持。`容器や包装のプラスチック`は上位見出しと実排出区分が同名のため、人工的な名称変更をせずcategory_groupで3実排出区分を束ねた。スプレー缶は公式本文に穴あけ指示がないため穴あけ有無を補作しない。
- 下関市: 令和8年度ガイドを正とし、古紙は新聞紙／雑誌類／ダンボールの3葉。粗大ごみは通常ステーション箱へ混ぜず、予約戸別収集のREFERENCE_ONLY公式葉として保持。
- 宇部市: 古紙3葉に加え、通常ステーションへ出せない`充電式電池`をDROP_OFFのREFERENCE_ONLY公式葉として保持。スプレー缶は`びん・缶`で**屋外で必ず穴を開ける**現行ルールを保持。
- 山口市: 2026年7月15日更新の現行情報を優先し、旧来の一括`有害ごみ`へ戻さず、`有害ごみ(1)`と`有害ごみ(2)`を別のDROP_OFF公式葉として保持。古紙は紙製容器包装／新聞／ダンボール／紙パック／雑がみの5葉。
- 防府市: カレンダー上の上位名称だけへ潰さず、資源ごみ7子葉、危険ごみ6子葉を保持。`粗大ごみ／埋立ごみ／一時多量ごみ`は学習者用の人工的な親SORT_BUCKETを作らず、同一category_groupの独立REFERENCE_ONLY葉とした。
- 下松市: `可燃系資源`は新聞紙／雑誌類・雑がみ／ダンボール／衣類の4葉を種類別に排出するため保持。スプレー缶は金属類で**必ず穴を開ける**現行ルール。
- 光市: 現行ページと現行基本計画期間内の実施計画を照合し、**14分別**を保持。古紙は新聞類／雑誌類・雑がみ／段ボールの3葉で、雑がみを人工的に独立させない。スプレー缶は金属類で**必ず穴を開ける**。
- 長門市: 令和8年度ガイドと現行計画を照合し、**17分別**を保持。古紙・衣類5葉、びん3色葉を保持し、缶はアルミ／スチールへ人工分割しない。

## 構造上の修正履歴

初回診断では、防府市の`粗大ごみ・埋立ごみ・一時多量ごみ（有料収集）`をREFERENCE_ONLY投影親とし、その下にREFERENCE_ONLY子葉を置いたため、Schemaの「REFERENCE_ONLY子葉の親はCURRENT SORT_BUCKET」という制約に抵触した。

親をSORT_BUCKETへ昇格させて学習者画面へ出す修正は採用せず、親行を削除し、3公式葉を同一category_groupの独立REFERENCE_ONLYとして保持した。再実行後、structural validationと専用RED TEAMはPASSした。

## category詳細真正性

Batch 02で問題となった空欄回避用の汎用文は使用していない。公式資料から具体的に言えないCORE詳細は`NOT_STATED_IN_CITED_SOURCE`とし、「自治体指定方法で出す」「公式ルールに従う」等の補作文を禁止した。

また、危険物の穴あけルールは自治体ごとに逆転するため、隣接自治体から横展開していない。

## Batch 12増分

- active municipalities: +8
- category rows: +132
- structured official leaves: +120
- official sources: +29
- initial mapping branches: +95
- coverage: +320
- category review evidence: +29
- DEFERRED: +2

## canonical更新

Batch 12統合後:

- fixed IDs: **143**
- active implementation targets: **135**
- canonical municipalities: **117**
- QA: **117/117 `QA_PASSED`**
- category: **1,402行**
- structured official leaves: **1,290**
- sources: **316**
- initial mapping branches: **1,180**
- coverage: **4,680 pair**
- category review evidence: **279**
- DEFERRED: **8**（M065・M076・M086・M098・M099・M100・M120・M123）

## 次Batch

`NEXT_BATCH_GATE=PASS`。

Batch 13は固定ID順に、山口県の残り10自治体:

**M126 柳井市 → M127 美祢市 → M128 周南市 → M129 山陽小野田市 → M130 周防大島町 → M131 和木町 → M132 上関町 → M133 田布施町 → M134 平生町 → M135 阿武町**

を基本範囲とする。
