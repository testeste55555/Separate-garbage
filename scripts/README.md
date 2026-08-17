# Scripts

| スクリプト | 役割 |
|---|---|
| `migrate_schema_v12.py` | 全既存bundleをSchema v1.2へ冪等移行し、mappingを状態保持更新、40品目coverageを生成 |
| `schema_v12.py` | v1.2列定義、QA再計算、mapping reconciliation、coverage生成 |
| `build_batch_01.py` | Batch 01を再構築し、手動レビュー証跡を保持してv1.2へ正規化 |
| `validate_pilot.py` | `data/research/pilot/pilot_qa.csv` を使う独立Pilot検証 |
| `validate_research.py` | batchまたはcanonical検証 |
| `validation_v12.py` | 構造検証とAPP readiness Gateを分離した共通validator |
| `merge_research.py` | Pilotと完成batchの6成果物をmergeし、手動VERIFIED/APP_READYを保持 |
| `red_team_schema_v12.py` | バッチ数・件数に依存しない12観点RED TEAM |
| `*_v11.py` | 破壊的な旧処理を再実行しないv1.2互換entrypoint |

標準検証：

```bash
python3 scripts/validate_pilot.py
python3 scripts/validate_research.py --batch batch_01
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v12.py
```

厳格なアプリ投入Gateは `python3 scripts/validate_research.py --gate` です。構造が正しくてもQAまたは40品目が未完了なら終了コード2で `HOLD` を返します。

validatorは143自治体MASTERと、対象bundle自身のmapping/coverageを参照します。canonical自治体数、区分数、出典数、バッチ名の固定正常値は持ちません。
