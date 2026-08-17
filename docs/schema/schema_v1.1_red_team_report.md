# Schema v1.1 RED TEAM Report

> 履歴注記：本報告のGate PASSは、Batch拡張性を追加検査したSchema v1.2 RED TEAMにより撤回。現行判定はAPP readiness Gate HOLD。

実施日：2026-08-17  
結果：12/12 PASS

| # | 観点 | 結果 | 根拠 |
|---:|---|---|---|
| 1 | 既存15自治体の情報欠落 | PASS | 15自治体・194区分・57出典・15 QA行とLegacy列を保持 |
| 2 | CURRENT / PLANNED混在 | PASS | CURRENT 193、PLANNED 1。非CURRENTはHIDDEN |
| 3 | REFERENCEがCORE必須 | PASS | REFERENCE 5項目をvalidatorのCORE必須集合から分離 |
| 4 | ui_roleによる箱生成 | PASS | 全194区分で決定規則と一致。箱はCURRENT + SORT_BUCKETのみ |
| 5 | item mappingの条件分岐 | PASS | 283枝・244自治体品目pair。複数枝、条件、前処理、例外先を保持 |
| 6 | 教材安全 | PASS | 40/40品目に4段階区分とsafety_note |
| 7 | 全参照整合性 | PASS | municipality/category/source/item/mapping/QAを共通validatorで検証 |
| 8 | Pilot/Batch再実行 | PASS | 入力集合が非重複で、Batch再構築後もv1.1 validation成功 |
| 9 | merge再実行 | PASS | 2回連続実行後のcanonical 5 CSVのSHA-256が一致 |
| 10 | validator個別ハードコード | PASS | validator 3ファイルに `Mnnn` 形式の自治体IDなし |
| 11 | 公式と外部サービスの区別 | PASS | 公式自治体54・一部事務組合2・公式案内外部1を別enumで保持 |
| 12 | README再現コマンド | PASS | 掲載した5コマンドを実行し全成功 |

## 自動RED TEAM

```bash
python3 scripts/red_team_schema_v11.py
```

```text
SCHEMA_V11_RED_TEAM_PASSED
checks=1:PASS,2:PASS,3:PASS,4:PASS,5:PASS,6:PASS,7:PASS,8:PASS,9:PASS,10:PASS,11:PASS,12:PASS
```

## 残余リスク

- 初期item mapping 283枝は区分レベル情報からの機械抽出で、全件 `INITIAL_REVIEW_REQUIRED`。品目別の公式再確認前は `APP_READY` にしない。
- `official_category_count` が公式に明示されない13自治体は、件数一致ではなく `category_count_basis` のレビューで網羅性を確認している。
- PLANNEDルールは施行日に自動昇格しない。公式施行確認後にsource、rule_status、確認日を更新する。
- REFERENCEは任意のため、アプリは欠損を許容し、CORE判断へ依存させない。

## Gate

Schema v1.1、再validation、QA、RED TEAMのGateはPASSです。本作業ではBatch 02自治体の公式情報収集を開始していません。
