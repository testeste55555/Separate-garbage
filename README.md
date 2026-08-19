# Separate-garbage

自治体ごとの家庭ごみ分別ルールを、授業用アプリで利用できる形へ正規化するプロジェクトです。

中心Can-do：

> 名前が分からないごみでも、自分が住む自治体のルールを調べて、仲間と相談しながら、正しく分別ができる。

収集曜日・収集時間・地区別カレンダーは構造化対象外です。

## 現在地（2026-08-19）

- MASTER：143自治体、固定ID済み
- Pilot：5自治体完了
- Batch 01：10自治体完了
- Batch 02：10自治体完了
- Batch 03：10自治体の研究bundle作成・merge済み
- 統合済み：計35自治体、471 category行（構造化公式葉430区分）、110公式出典
- Schema：v1.2.3
- 構造validation：Pilot / Batch 01 / Batch 02 / Batch 03 / canonical PASS
- QA：34 `QA_PASSED` / 1 `QA_REQUIRED`
- `M028 由良町`：現行公式広報で可燃・プラスチック・不燃・資源・粗大のラベルは確認済み。ただし全区分索引を確認できていないため `NOT_REVIEWED / QA_REQUIRED`
- 共通品目：40品目、安全区分付き
- item mapping：485条件枝（現状は初期候補段階）
- 40品目coverage：1,400自治体品目pair
- category review evidence：72行
- Schema v1.2.3 RED TEAM：25/25 PASS
- Batch 03専用RED TEAM：由良町の証拠不足を自動昇格させない検査を追加
- `NEXT_BATCH_GATE`：`HOLD`（M028の区分網羅性証拠待ち）
- `APP_READINESS_GATE`：`HOLD`（40品目の品目別公式確認未完了）

Batch 03の対象はMASTER順の `M023〜M029・M031〜M033` です（M030米子市はPilotで既調査）。大阪市、神戸市、豊岡市、姫路市、大和郡山市、由良町、鳥取市、倉吉市、境港市、岩美町を公式資料で調査しました。由良町については証拠不足を汎用文や推測で補わず、Gateを意図的にHOLDにしています。

## ディレクトリ

- `data/master/01_municipalities_master.csv`：143自治体MASTER
- `data/master/02_official_domain_registry.csv`：公式・一部事務組合・公式案内外部サービスの根拠
- `data/master/04_common_items_master.csv`：共通40品目と教材安全区分
- `data/research/pilot/`：Pilot 5自治体の独立成果物・QA
- `data/research/batches/batch_01/`：Batch 01 10自治体
- `data/research/batches/batch_02/`：Batch 02 10自治体
- `data/research/batches/batch_03/`：Batch 03 10自治体（M028のみQA_REQUIRED）
- `data/research/02_categories_master.csv`：統合分別区分
- `data/research/03_sources_master.csv`：統合出典
- `data/research/04_municipalities_research.csv`：統合自治体調査
- `data/research/05_item_mapping_master.csv`：初期品目対応・条件枝
- `data/research/06_qa_log.csv`：機械再計算済みQA
- `data/research/07_item_mapping_coverage.csv`：全自治体×40品目の調査・実装準備状態
- `data/research/08_category_review_evidence.csv`：区分網羅性レビューの複数公式source証拠
- `docs/schema/`：Schema、Data Dictionary、移行・RED TEAM報告
- `docs/workflow/`：作業フロー（旧版を保持）
- `scripts/build_batch_03.py`：Batch 03再生成用
- `scripts/red_team_batch_03.py`：Batch 03証拠ギャップ専用RED TEAM

## 再現コマンド

リポジトリ直下で実行します。

```bash
python3 scripts/validate_pilot.py
python3 scripts/validate_research.py --batch batch_01
python3 scripts/validate_research.py --batch batch_02
python3 scripts/validate_research.py --batch batch_03
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v12.py
python3 scripts/red_team_batch_03.py
python3 scripts/check_next_batch_gate.py  # M028未解消中はHOLD（終了コード2）
python3 scripts/validate_research.py --app-readiness-gate  # 現状HOLD（終了コード2）
```

Batch 03の生成元から再構築する場合：

```bash
python3 scripts/build_batch_03.py
python3 scripts/validate_research.py --batch batch_03
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_batch_03.py
```

GitHub Actionsの `.github/workflows/build-batch-03.yml` でも同じ生成・validation・merge・RED TEAMを実行します。証拠不足による `NEXT_BATCH_GATE=HOLD` は有効な研究状態として保存します。

## 運用上の重要事項

- `rule_status=CURRENT` かつ `ui_role=SORT_BUCKET` の行だけを、学習者用の現在の仕分け箱として投影します。
- `PLANNED` / `RETIRED` は `HIDDEN` とし、現行ルールへ混入させません。
- `official_verified=TRUE` は公式ドメイン台帳との一致を意味します。外部サービスは自治体公式ページからの導線も保持します。
- `ui_role` は独立した教材UI指定です。`collection_channel` や `classification_level` から再推論しません。
- 袋・容器、収集経路、粗大・予約・料金はREFERENCEです。分類結果に影響する条件だけCORE側へ記録します。
- 空URLは「確認済み・不存在」ではありません。任意機能は `CHECKED_PRESENT / CHECKED_ABSENT / NOT_CHECKED` と証跡を保持します。
- municipalitiesの `確認ステータス` はQAログから自動同期する読取専用ミラーです。
- `OFFICIAL_COUNT_MATCHED` は公式総数を必須とし、`MANUAL_INDEX_REVIEW` は `reviewed_category_count` と公式目次の照合証跡を必須とします。
- 区分網羅性を証明できない場合は `NOT_REVIEWED / QA_REQUIRED` のまま止め、推測でQA_PASSEDへ昇格させません。
- 区分網羅性の複数sourceは `category_review_evidence` へ正規化し、公式件数はCURRENTの公式葉区分を数えます。教材投影親は重複計上しません。
- item mappingは不変な `mapping_id` を条件枝の主キーにし、同じ品目・同じ分別先でも異なる条件枝を複数行で保持します。
- mappingの `category_source_*` は区分体系の根拠、`item_evidence_*` は品目別判断の根拠です。
- 初期mapping候補は `自治体正式名称` と `代表品目` だけをPositive evidenceとして生成します。
- category詳細に公式記載がない場合は `NOT_STATED_IN_CITED_SOURCE` を使います。空欄回避用プレースホルダはvalidatorが拒否します。
- `APP_READY` は40品目coverage、品目別公式証跡、全条件枝レビューが揃わない限りvalidatorが拒否します。
