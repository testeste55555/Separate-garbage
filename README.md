# Separate-garbage

自治体ごとの家庭ごみ分別ルールを、授業用アプリで利用できる形へ正規化するプロジェクトです。

中心Can-do：

> 名前が分からないごみでも、自分が住む自治体のルールを調べて、仲間と相談しながら、正しく分別ができる。

収集曜日・収集時間・地区別カレンダーは構造化対象外です。カレンダーは必要に応じて、現行taxonomyの運用確認や地域variantの証拠として使用します。

## 現在地（2026-08-19）

- MASTER固定ID台帳：**143自治体**
- active実装対象：**135自治体**
- DEFERRED：**8自治体**
  - M065 知夫村：公式一次資料本文の全区分確認が安定しない
  - M076 備前市：地区別CURRENT分別体系が併存
  - M086 新庄村：公式一次資料本文を安定取得できず全区分を全件照合できない
  - M098 尾道市：尾道・向島・御調・因島・瀬戸田でCURRENT体系が併存
  - M099 福山市：市内一般・内海町・沼隈町で住民向け分別単位に差
  - M100 府中市：府中地区と上下地区で住民向け表示単位・正式名称に差
  - M120 萩市：大島・見島・相島地区で一部分別区分が異なる
  - M123 岩国市：地域群により食品トレー等の分別先・排出方法が異なる
- Pilot：5自治体完了
- Batch 01〜06：各10自治体完了
- Batch 07：9自治体完了（M065 DEFERRED）
- Batch 08：9自治体完了（M076 DEFERRED）
- Batch 09：9自治体完了（M086 DEFERRED）
- Batch 10：7自治体完了（M098・M099・M100 DEFERRED）
- Batch 11：10自治体完了
- Batch 12：**8自治体完了**（M120・M123 DEFERRED）
- canonical：**117自治体**
- canonical QA：**117 `QA_PASSED` / 0 `QA_REQUIRED`**
- category：**1,402行**
- structured official leaves：**1,290区分**
- official sources：**316**
- item mapping：**1,180条件枝**（初期候補段階）
- 40品目coverage：**4,680自治体品目pair**
- category review evidence：**279行**
- Schema：**v1.2.4**
- Workflow：**v1.22**
- Batch 12専用RED TEAM：**PASS**
- canonical structural validation：**PASS**
- Schema v1.2.4 RED TEAM：**PASS**
- operational category semantics RED TEAM：**PASS**
- `NEXT_BATCH_GATE`：**PASS**
- `APP_READINESS_GATE`：**HOLD**（40共通品目のITEM_SPECIFIC公式確認未完了）

CI記録：`docs/research/batch_12_ci_status.txt`
QA記録：`docs/research/batch_12_qa_report.md`

## Batch 12

MASTER範囲はM116〜M125です。

### canonicalへ統合した8自治体

- M116 神石高原町：18公式葉
- M117 下関市：10公式葉
- M118 宇部市：13公式葉
- M119 山口市：15公式葉
- M121 防府市：18公式葉
- M122 下松市：15公式葉
- M124 光市：14公式葉
- M125 長門市：17公式葉

### DEFERRED

- M120 萩市：令和8年度も大島・見島・相島地区で一部分別区分が異なるため`SCHEMA_SCOPE_LIMITATION`
- M123 岩国市：地域群により食品トレー等の分別先・排出方法が実際に異なるため`SCHEMA_SCOPE_LIMITATION`

固定IDは削除・再採番しません。

### Batch 12真正性事項

- 神石高原町：`容器や包装のプラスチック`が上位見出しと実排出区分で同名のため、人工的なサフィックスを正式名称へ残さずcategory_groupで整理。
- 下関市：古紙3区分を保持し、粗大ごみは予約戸別収集のREFERENCE_ONLY公式葉。
- 宇部市：通常ステーションへ出せない充電式電池を`DROP_OFF`で保持。スプレー缶は**屋外で必ず穴を開ける**。
- 山口市：2026-07-15更新の`有害ごみ(1)`／`有害ごみ(2)`を別DROP_OFF葉として保持し、一括`有害ごみ`へ戻さない。
- 防府市：資源7子葉・危険6子葉を保持。粗大／埋立／一時多量は人工親SORT_BUCKETを作らず、同一category_groupの独立REFERENCE_ONLY葉。
- 下松市：可燃系資源4葉を保持。スプレー缶は**必ず穴を開ける**。
- 光市：現行体系を14公式葉として保持。古紙は新聞類／雑誌類・雑がみ／段ボールの3葉。スプレー缶は**必ず穴を開ける**。
- 長門市：令和8年度ガイドと計画を照合し17公式葉。古紙・衣類5葉、びん3色葉を保持し、缶を人工的にアルミ／スチールへ分割しない。

## データ設計の原則

- `rule_status=CURRENT` かつ `ui_role=SORT_BUCKET` の行だけを学習者用の現在の仕分け箱として投影する。
- category completenessは処理施設側工程ではなく、**住民が排出時に選択する公式分別区分**を基準とする。
- 自治体正式名称は括弧・記号を含め公式表記を保持する。
- `OFFICIAL_COUNT_MATCHED`は公式資料がcanonical leafと同じ粒度の数値総数を明示する場合だけ使用する。それ以外は`MANUAL_INDEX_REVIEW`。
- 住民が別袋・別容器・別束へ分ける公式子区分は保持し、投影親を公式葉件数へ二重計上しない。
- 公式見出しと実排出区分が同名の場合、人工名称を作らずcategory_groupで解決する。
- 特殊経路の説明見出しを、Schema制約回避のためだけに学習者SORT_BUCKETへ昇格させない。
- `DROP_OFF`・`BOOKED_PICKUP`・`DIRECT_HAUL`・`RETAILER_OR_MAKER`等の実経路を通常収集へ寄せない。
- 内部説明上の小分類だけを理由に独立categoryへ増やさない。
- 現行年度・最新更新の公式資料を優先する。
- 危険物の穴あけ必須／不要を全国・県内共通化しない。
- 公式記載がないCORE詳細は`NOT_STATED_IN_CITED_SOURCE`とし、空欄回避用汎用文を補作しない。
- 同一自治体内で複数CURRENT taxonomyがあり、住民の地域scopeを安全に解決できない場合はDEFERREDとする。
- 固定IDはDEFERREDでも削除・再採番しない。
- `APP_READY`はcategory研究完了とは独立し、40品目すべてのITEM_SPECIFIC公式証拠・coverage・条件枝レビューが揃うまで付与しない。

## 主なディレクトリ

- `data/master/01_municipalities_master.csv`：143自治体固定ID MASTER
- `data/master/02_official_domain_registry.csv`：公式ドメイン・公式導線台帳
- `data/master/04_common_items_master.csv`：共通40品目と教材安全区分
- `data/master/05_deferred_municipalities.csv`：一時実装対象外の固定ID自治体
- `data/research/pilot/`：Pilot 5自治体
- `data/research/batches/batch_01/`〜`batch_12/`：Batch研究bundle
- `data/research/02_categories_master.csv`：canonical分別区分
- `data/research/03_sources_master.csv`：canonical出典
- `data/research/04_municipalities_research.csv`：canonical自治体調査
- `data/research/05_item_mapping_master.csv`：初期品目対応・条件枝
- `data/research/06_qa_log.csv`：機械再計算済みQA
- `data/research/07_item_mapping_coverage.csv`：完了自治体×40品目の調査状態
- `data/research/08_category_review_evidence.csv`：category completeness公式証拠
- `docs/research/`：Batch QA・CI記録
- `docs/workflow/`：作業フロー履歴（現行 v1.22）
- `scripts/build_batch_*.py`：Batch再生成
- `scripts/red_team_batch_*.py`：Batch専用RED TEAM

## Batch 12再現・Gate

```bash
python3 scripts/build_batch_12_active.py
python3 scripts/validate_research.py --batch batch_12 --next-batch-gate
python3 scripts/red_team_batch_12_active.py
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v12.py
python3 scripts/red_team_operational_category_semantics.py
python3 scripts/check_next_batch_gate.py
```

`NEXT_BATCH_GATE`はcategory研究を次Batchへ進めるためのGateです。`APP_READINESS_GATE`とは分離されており、現在の`APP_READINESS_GATE=HOLD`は40品目のITEM_SPECIFICレビュー未完了による正常な状態です。

## 次Batch

Batch 13は山口県の残り10自治体です。

**M126 柳井市 → M127 美祢市 → M128 周南市 → M129 山陽小野田市 → M130 周防大島町 → M131 和木町 → M132 上関町 → M133 田布施町 → M134 平生町 → M135 阿武町**
