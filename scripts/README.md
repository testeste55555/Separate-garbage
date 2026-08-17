# Scripts

| スクリプト | 役割 |
|---|---|
| `migrate_schema_v11.py` | Pilot、Batch 01、canonicalを冪等にSchema v1.1へ移行し、初期mappingを生成 |
| `build_batch_01.py` | 確認済みBatch 01生成元からCSVを再構築し、直後にv1.1へ正規化 |
| `validate_pilot.py` | `data/research/pilot/pilot_qa.csv` を使う独立Pilot検証 |
| `validate_research.py` | batchまたはcanonical検証 |
| `validation_v11.py` | 共通Schema・参照・公式性・QA再計算ロジック |
| `merge_research.py` | Pilotと完成batchだけからcanonicalとmappingを冪等再構築 |
| `red_team_schema_v11.py` | Schema v1.1の12観点RED TEAM |

標準検証：

```bash
python3 scripts/validate_pilot.py
python3 scripts/validate_research.py --batch batch_01
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/red_team_schema_v11.py
```

validatorは `data/master/01_municipalities_master.csv` を参照します。自治体ID固有の分岐、固定の最小区分数、canonical QAをPilot QAとして再利用する処理はありません。
