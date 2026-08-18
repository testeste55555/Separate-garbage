# Separate-garbage

自治体ごとの家庭ごみ分別ルールを、授業用アプリで利用できる形へ正規化するプロジェクトです。

中心Can-do：

> 名前が分からないごみでも、自分が住む自治体のルールを調べて、仲間と相談しながら、正しく分別ができる。

収集曜日・収集時間・地区別カレンダーは構造化対象外です。

## 現在地（2026-08-18）

- MASTER：143自治体、固定ID済み
- Pilot：5自治体完了
- Batch 01：10自治体完了
- Batch 02：10自治体完了
- 調査・再validation済み：計25自治体、356 category行（公式葉325区分）、86公式出典
- Schema：v1.2.3へ移行済み
- 構造validation：Pilot / Batch 01 / Batch 02 / canonicalすべてPASS
- QA：25 `QA_PASSED` / 0 `QA_REQUIRED`
- 共通品目：40品目、安全区分付き
- item mapping：399条件枝（現状は全枝 `INITIAL_REVIEW_REQUIRED`）
- 40品目coverage：1,000自治体品目pair（383 `MAPPED_INITIAL` / 617 `NOT_RESEARCHED`）
- category review evidence：50行
- Schema v1.2.3 RED TEAM：25/25 PASS

Batch 02はMASTER順のM012・M014〜M022を対象に、公式ガイドの目次・分別見出しと151 category行の詳細を再照合しました。公式に詳細記載がない欄は補作せず`NOT_STATED_IN_CITED_SOURCE`で明示し、validatorは空欄回避用プレースホルダを拒否します。全10自治体を`MANUAL_INDEX_REVIEW`で記録し、公式粒度と教材UI投影を分離しています。`NEXT_BATCH_GATE` は `PASS`、`APP_READINESS_GATE` は25自治体×40品目の品目別公式確認が未完了のため `HOLD` です。

## ディレクトリ

- `data/master/01_municipalities_master.csv`：143自治体MASTER
- `data/master/02_official_domain_registry.csv`：公式・一部事務組合・公式案内外部サービスの根拠
- `data/master/04_common_items_master.csv`：共通40品目と教材安全区分
- `data/research/pilot/`：Pilot 5自治体の独立成果物・QA
- `data/research/batches/batch_01/`：Batch 01 10自治体
- `data/research/batches/batch_02/`：Batch 02 10自治体
- `data/research/02_categories_master.csv`：統合分別区分
- `data/research/03_sources_master.csv`：統合出典
- `data/research/04_municipalities_research.csv`：統合自治体調査
- `data/research/05_item_mapping_master.csv`：初期品目対応・条件枝
- `data/research/06_qa_log.csv`：機械再計算済みQA
- `data/research/07_item_mapping_coverage.csv`：全自治体×40品目の調査・実装準備状態
- `data/research/08_category_review_evidence.csv`：区分網羅性レビューの複数公式source証拠
- `docs/schema/`：Schema、Data Dictionary、移行・RED TEAM報告
- `docs/workflow/`：作業フロー（旧版を保持し、現行v1.10を追加）

## 再現コマンド

リポジトリ直下で実行します。

```bash
python3 scripts/validate_pilot.py
python3 scripts/validate_research.py --batch batch_01
python3 scripts/validate_research.py --batch batch_02
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/check_next_batch_gate.py  # 現状はPASS（終了コード0）
python3 scripts/validate_research.py --app-readiness-gate  # 現状はHOLDを示す終了コード2
python3 scripts/red_team_schema_v12.py
```

Batch 01の生成元から再構築する場合：

```bash
python3 scripts/build_batch_01.py
python3 scripts/validate_research.py --batch batch_01
python3 scripts/merge_research.py
python3 scripts/validate_research.py
```

Batch 02の生成元から再構築する場合：

```bash
python3 scripts/build_batch_02.py
python3 scripts/validate_research.py --batch batch_02 --next-batch-gate
python3 scripts/merge_research.py
python3 scripts/validate_research.py
```

migrationとmergeの冪等性は、2回連続実行後に完成bundleおよびcanonical 7 CSVのSHA-256が不変であることを確認済みです。

## 運用上の重要事項

- `rule_status=CURRENT` かつ `ui_role=SORT_BUCKET` の行だけを、学習者用の現在の仕分け箱として投影します。
- `PLANNED` / `RETIRED` は `HIDDEN` とし、現行ルールへ混入させません。
- `official_verified=TRUE` は公式ドメイン台帳との一致を意味します。外部サービスは自治体公式ページからの導線も保持します。
- `ui_role` は独立した教材UI指定です。`collection_channel` や `classification_level` から再推論しません。
- 袋・容器、収集経路、粗大・予約・料金はREFERENCEです。分類結果に影響する条件だけCORE側へ記録します。
- 空URLは「確認済み・不存在」ではありません。任意機能は `CHECKED_PRESENT / CHECKED_ABSENT / NOT_CHECKED` と証跡を保持します。
- municipalitiesの `確認ステータス` はQAログから自動同期する読取専用ミラーです。手入力の別ステータスとして使用しません。
- `OFFICIAL_COUNT_MATCHED` は公式総数を必須とし、`MANUAL_INDEX_REVIEW` は公式総数を要求せず `reviewed_category_count` と公式目次の照合証跡を必須とします。
- 区分網羅性の複数sourceは `category_review_evidence` へ正規化し、公式件数はCURRENTの公式葉区分を数えます。教材投影親は重複計上しません。
- item mappingは不変な `mapping_id` を条件枝の主キーにし、同じ品目・同じ分別先でも異なる条件枝を複数行で保持します。`branch_order` は表示順でありidentityではありません。
- mappingの `category_source_*` は区分体系の根拠、`item_evidence_*` は品目別判断の根拠です。両者は別の同一自治体公式sourceを使用できます。
- 初期mapping候補は `自治体正式名称` と `代表品目` だけをPositive evidenceとして生成します。`入れてはいけない物`、`条件外の扱い`、`出す前の処理`、`注意事項` の語だけで候補を生成しません。
- `衣類乾燥機`、`白色以外のトレイ`、`LED蛍光灯` など、別品目を内包する複合語はcollision guardで偽陽性を防ぎます。
- category詳細に公式記載がない場合は`NOT_STATED_IN_CITED_SOURCE`を使います。`該当する公式区分`、`公式ガイドの指定方法`等の空欄回避用プレースホルダはvalidatorが拒否します。
- `APP_READY` は40品目coverage、品目別公式証跡、全条件枝レビューが揃わない限りvalidatorが拒否します。
