# Separate-garbage

自治体ごとの家庭ごみ分別ルールを、授業用アプリで利用できる形へ正規化するプロジェクトです。

中心Can-do：

> 名前が分からないごみでも、自分が住む自治体のルールを調べて、仲間と相談しながら、正しく分別ができる。

収集曜日・収集時間・地区別カレンダーは構造化対象外です。

## 現在地（2026-08-17）

- MASTER：143自治体、固定ID済み
- Pilot：5自治体完了
- Batch 01：10自治体完了
- 調査・再validation済み：計15自治体、194分別区分、57公式出典
- Schema：v1.1へ移行済み
- QA：15/15 `QA_PASSED`（必須条件を機械再計算）
- 共通品目：40品目、安全区分付き
- 初期item mapping：283条件枝（`INITIAL_REVIEW_REQUIRED`）
- Schema/QA修正後のRED TEAM：12/12 PASS

Batch 02の自治体調査は、このSchema/QA修正作業では実施していません。次バッチ前Gateは技術的にはPASSですが、初期item mappingは品目別公式確認前のため `APP_READY` ではありません。

## ディレクトリ

- `data/master/01_municipalities_master.csv`：143自治体MASTER
- `data/master/02_official_domain_registry.csv`：公式・一部事務組合・公式案内外部サービスの根拠
- `data/master/04_common_items_master.csv`：共通40品目と教材安全区分
- `data/research/pilot/`：Pilot 5自治体の独立成果物・QA
- `data/research/batches/batch_01/`：Batch 01 10自治体
- `data/research/02_categories_master.csv`：統合分別区分
- `data/research/03_sources_master.csv`：統合出典
- `data/research/04_municipalities_research.csv`：統合自治体調査
- `data/research/05_item_mapping_master.csv`：初期品目対応・条件枝
- `data/research/06_qa_log.csv`：機械再計算済みQA
- `docs/schema/`：Schema、Data Dictionary、移行・RED TEAM報告
- `docs/workflow/`：作業フロー（v1.1を保持し、v1.2を追加）

## 再現コマンド

リポジトリ直下で実行します。

```bash
python3 scripts/validate_pilot.py
python3 scripts/validate_research.py --batch batch_01
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v11.py
```

Batch 01の生成元から再構築する場合：

```bash
python3 scripts/build_batch_01.py
python3 scripts/validate_research.py --batch batch_01
python3 scripts/merge_research.py
python3 scripts/validate_research.py
```

mergeの冪等性は、2回連続実行後にcanonical 5 CSVのSHA-256が不変であることを確認済みです。

## 運用上の重要事項

- `rule_status=CURRENT` かつ `ui_role=SORT_BUCKET` の行だけを、学習者用の現在の仕分け箱として投影します。
- `PLANNED` / `RETIRED` は `HIDDEN` とし、現行ルールへ混入させません。
- `official_verified=TRUE` は公式ドメイン台帳との一致を意味します。外部サービスは自治体公式ページからの導線も保持します。
- REFERENCE項目は既存値を保持しますが、今後の全自治体調査では一律必須にしません。
- item mappingは条件分岐を複数行で保持します。`INITIAL_REVIEW_REQUIRED` はアプリ投入可を意味しません。
