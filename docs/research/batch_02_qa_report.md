# PHASE 3 Batch 02 QA Report

確認日：2026-08-18  
対象：M012、M014〜M022（MASTER順の次10自治体）  
適用Schema：v1.2.3

## 結果

- 自治体：10
- category行：151
- 公式葉区分：138
- 公式出典：28
- category review evidence：28
- 自治体別QA：10/10 `QA_PASSED`
- item mapping：152条件枝（全枝 `INITIAL_REVIEW_REQUIRED`）
- coverage：400 pair（151 `MAPPED_INITIAL` / 249 `NOT_RESEARCHED`）
- Batch単独構造validation：PASS
- Batch単独NEXT_BATCH_GATE：PASS

## 自治体別件数

| municipality_id | 自治体 | category行 | 公式葉区分 | QA | 主な確認事項 |
|---|---|---:|---:|---|---|
| M012 | 幸手市 | 17 | 16 | PASS | 令和8年度共通説明p23〜32、紙5区分、危険・有害、収集外 |
| M014 | 墨田区 | 11 | 10 | PASS | 2026年3月版分別フロー、プラスチック、拠点・イベント回収 |
| M015 | 中央区 | 16 | 14 | PASS | 資源の親1箱と公式9子区分を分離、拠点回収、収集外 |
| M016 | 三浦市 | 18 | 17 | PASS | 分割版ガイド全6冊、古紙5区分、枝木、蛍光管、粗大 |
| M017 | 新潟市 | 15 | 13 | PASS | 有料3区分、資源区分、古紙親＋4子、特定5品目 |
| M018 | 瑞穂市 | 12 | 11 | PASS | 区分別PDF索引、拠点・無料回収、剪定木、廃食用油 |
| M019 | 山県市 | 19 | 18 | PASS | 令和8年度実施計画、資源12区分、小型家電、有害、廃食用油 |
| M020 | 静岡市 | 17 | 15 | PASS | 葵・駿河区版と清水区版、古紙親＋4子、区別条件 |
| M021 | 津市 | 13 | 12 | PASS | 令和8年4月版p4の分別区分一覧12区分、収集外 |
| M022 | 四條畷市 | 13 | 12 | PASS | 2026年版定期収集、窓口・拠点回収、粗大不燃、収集外 |

`公式葉区分`はCURRENTかつ非`EXCLUDED_NOTICE`の葉だけを数え、教材投影用の親は重複計上していません。

## 横断QA / RED TEAM

| 観点 | 判定 | 対応 |
|---|---|---|
| MASTER対象 | PASS | M012・M014〜M022の次10自治体と一致 |
| 公式根拠 | PASS | 10自治体すべて自治体公式ドメインの現行ページ・PDFのみ使用 |
| 区分網羅性 | PASS | 全自治体を`MANUAL_INDEX_REVIEW`とし、主索引＋補足sourceを複数行で保持 |
| 公式粒度／UI粒度 | PASS | 中央区・新潟市・静岡市は公式子区分を葉、教材箱を親として分離 |
| 危険・有害 | PASS | 電池、蛍光管、スプレー缶、ライター等の区分または回収経路を保持 |
| 収集外 | PASS | 全自治体に法定リサイクル・処理困難物等の`EXCLUDED_NOTICE`を保持 |
| 初期mapping | PASS | Positive evidenceのみで152枝を生成。品目別証拠は未付与 |
| coverage | PASS | 10×40=400 pairの直積を保持 |
| QA日付 | PASS | 全自治体で最新根拠日`2026-08-18`と一致 |
| canonical merge | PASS | Pilot＋Batch 01＋Batch 02のno-loss union、二重mergeでSHA-256不変 |
| RED TEAM | PASS | 24/24。Batch 02の対象・QA・葉件数・複数source証拠を追加攻撃 |

## 統合後

- 25自治体
- 356 category行（公式葉325区分）
- 86 source
- 50 category review evidence
- 397 initial mapping branches
- 1,000 coverage pair（381 `MAPPED_INITIAL` / 619 `NOT_RESEARCHED`）
- 25 `QA_PASSED` / 0 `QA_REQUIRED`
- `NEXT_BATCH_GATE: PASS`
- `APP_READINESS_GATE: HOLD`（0/25自治体、正常）

## 再現コマンド

```bash
python3 scripts/build_batch_02.py
python3 scripts/validate_research.py --batch batch_02
python3 scripts/validate_research.py --batch batch_02 --next-batch-gate
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/check_next_batch_gate.py
python3 scripts/validate_research.py --app-readiness-gate
python3 scripts/red_team_schema_v12.py
```

## 判定

Batch 02は構造・公式根拠・区分網羅性・QA・merge・RED TEAMを通過した。次Batchは`NEXT_BATCH_GATE`上開始可能。40品目の品目別公式レビューは未実施のため、教材アプリ公開は引き続き`APP_READINESS_GATE: HOLD`とする。
