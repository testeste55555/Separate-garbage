# Schema v1.2 RED TEAM Report

> 履歴版。12/12判定は後続RED TEAMで置換済み。現行結果はv1.2.1の15/15 PASSである。

実施日：2026-08-17  
自動判定：12/12 PASS  
アプリ実装準備Gate：HOLD

| # | 攻撃観点 | 結果 |
|---:|---|---|
| 1 | Pilot・全完成batch・canonicalの構造validation | PASS |
| 2 | canonicalがPilot＋完成batchのno-loss union | PASS |
| 3 | coverageが動的な自治体×40品目直積 | PASS |
| 4 | 任意機能の確認済み／未確認と証跡 | PASS |
| 5 | ui_roleの独立性と意味上の不変条件 | PASS |
| 6 | active validatorに15自治体固定値なし | PASS |
| 7 | batchが自身のmapping/coverageを検証 | PASS |
| 8 | mergeがmappingを再生成しない | PASS |
| 9 | reconciliationが手動APP_READYを保持 | PASS |
| 10 | 根拠なしAPP_READY直接編集を拒否 | PASS |
| 11 | Gateが件数でなくデータからPASS/HOLD判定 | PASS |
| 12 | Gateが全40 pairから導出 | PASS |

実行コマンド：

```bash
python3 scripts/red_team_schema_v12.py
```

```text
RED_TEAM_SUMMARY=12/12
SCHEMA_V12_RED_TEAM_PASSED
```

RED TEAM PASSは現在データのAPP_READYを意味しない。検出器と拡張基盤が未完了状態を正しくHOLDできることを意味する。

## 現在のHOLD理由

- 13自治体は区分網羅性の公式件数一致または手動索引レビューが未完了。
- 600自治体品目pairのうち244は機械初期mapping、356は未調査。
- APP_READY coverageは0、APP_READY自治体は0/15。

したがってBatch 02は開始しない。
