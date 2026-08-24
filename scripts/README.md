# Scripts

| スクリプト | 役割 |
|---|---|
| `migrate_schema_v12.py` | 全既存bundleをSchema v1.2.3へ冪等移行し、QA・網羅性・複数source証拠を更新 |
| `apply_category_completeness_review.py` | 15自治体レビュー、11区分補正、石巻市19分別、複数source証拠をPilot/Batch 01/canonicalへ冪等反映 |
| `schema_v12.py` | v1.2.3列定義、QA日付再計算、公式葉区分、複数source証拠、mapping候補生成・reconciliation |
| `build_batch_01.py` | Batch 01を再構築し、手動レビュー証跡を保持してv1.2へ正規化 |
| `build_batch_02.py` | Batch 02の公式調査ノートから7成果物を再構築し、Schema v1.2.3へ正規化 |
| `validate_pilot.py` | `data/research/pilot/pilot_qa.csv` を使う独立Pilot検証 |
| `validate_research.py` | batchまたはcanonical検証 |
| `validation_v12.py` | 構造検証、NEXT_BATCH_GATE、APP_READINESS_GATEを分離した共通validator |
| `merge_research.py` | Pilotと完成batchの7成果物をmergeし、`mapping_id` 単位で手動VERIFIED/APP_READY枝を保持 |
| `check_next_batch_gate.py` | 全bundle、canonical union、二重merge冪等性、RED TEAMを統合した次Batch判定 |
| `red_team_schema_v12.py` | バッチ数・件数に依存しない24観点RED TEAM（Batch 02対象・QA・複数source証拠を含む） |
| `apply_item_image_mapping_pilot_top8.py` | 画像10品目×Style Research active 8自治体の公式mapping 80組を冪等生成（76 VERIFIED / 4 UNRESOLVED） |
| `validate_item_image_mapping_pilot.py` | Pilot台帳・画像・品目master・category・公式source・canonical mapping/coverageの参照整合性を検証 |
| `red_team_item_image_mapping_pilot.py` | 地域variant混入、推測昇格、非公式URL、汎用文、レイヤー間QA日結合等をmutation検査 |
| `validate_learner_item_sorting_pilot.py` | VERIFIED 76組の画像・category階層・Style projectionに加え、授業モード分離と学習者画面への答え・教師用説明の非表示を検証 |
| `red_team_learner_item_sorting_pilot.py` | UNRESOLVED混入、親子投影破壊、推測色、地域variant、画像path、答え漏洩、通信状態との混同等をmutation検査 |
| `*_v11.py` | 破壊的な旧処理を再実行しないv1.2互換entrypoint |

標準検証：

```bash
python3 scripts/validate_pilot.py
python3 scripts/validate_research.py --batch batch_01
python3 scripts/validate_research.py --batch batch_02
python3 scripts/merge_research.py
python3 scripts/validate_research.py
python3 scripts/check_next_batch_gate.py
python3 scripts/validate_research.py --app-readiness-gate
python3 scripts/red_team_schema_v12.py
python3 scripts/apply_item_image_mapping_pilot_top8.py
python3 scripts/validate_item_image_mapping_pilot.py
python3 scripts/red_team_item_image_mapping_pilot.py
python3 scripts/validate_learner_item_sorting_pilot.py
python3 scripts/red_team_learner_item_sorting_pilot.py
```

次Batchへ進むGateは `python3 scripts/check_next_batch_gate.py` です。構造、公式出典、区分網羅性QA、canonical union、merge冪等性、RED TEAMを要求しますが、40品目のAPP_READYは要求しません。

教材アプリ投入Gateは `python3 scripts/validate_research.py --app-readiness-gate` です。QAまたは40品目が未完了なら終了コード2で `HOLD` を返します。旧 `--gate` は互換aliasとして同じ判定を行います。

validatorは143自治体MASTERと、対象bundle自身のmapping/coverageを参照します。canonical自治体数、区分数、出典数、バッチ名の固定正常値は持ちません。
