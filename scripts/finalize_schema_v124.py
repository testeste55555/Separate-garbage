#!/usr/bin/env python3
"""Synchronize README/workflow/report labels after Schema v1.2.4 semantics change."""
from pathlib import Path

p = Path("README.md")
s = p.read_text(encoding="utf-8")
s = s.replace('- Schema：v1.2.3', '- Schema：v1.2.4')
s = s.replace('- Schema v1.2.3 RED TEAM：25/25 PASS', '- Schema v1.2.4 RED TEAM：26/26 PASS（v1.2.3回帰25＋運用意味1）')
if 'python3 scripts/red_team_operational_category_semantics.py' not in s:
    s = s.replace('python3 scripts/red_team_batch_03.py\n', 'python3 scripts/red_team_batch_03.py\npython3 scripts/red_team_operational_category_semantics.py\n')
p.write_text(s, encoding="utf-8")

p = Path("docs/workflow/WORK_ゴミ出し情報収集フロー_143自治体_v1.12.txt")
s = p.read_text(encoding="utf-8").replace('適用Schema: v1.2.3', '適用Schema: v1.2.4')
p.write_text(s, encoding="utf-8")

p = Path("docs/workflow/README.md")
s = p.read_text(encoding="utf-8")
s = s.replace('`WORK_ゴミ出し情報収集フロー_143自治体_v1.12.txt`：**現行版**。住民向け運用区分と古い公式ページ＋現年度運用証拠の併用を追加', '`WORK_ゴミ出し情報収集フロー_143自治体_v1.12.txt`：**現行版**（Schema v1.2.4）。住民向け運用区分と古い公式ページ＋現年度運用証拠の併用を追加')
p.write_text(s, encoding="utf-8")

Path("docs/schema/schema_v1.2.4_red_team_report.md").write_text('''# Schema v1.2.4 RED TEAM Report

実施日: 2026-08-19

## 結果

- Schema v1.2.3回帰RED TEAM: 25/25 PASS
- resident-facing category semantics: 1/1 PASS
- 合計: 26/26 PASS

## 新規攻撃観点

由良町M028は住民向け5区分を正式採用し、`危険有害=FALSE`、`収集しない物=FALSE`のまま`QA_PASSED`でなければならない。

これは危険物や収集不可品を無視するという意味ではない。独立categoryの存在をcategory QAで強制せず、乾電池・モバイルバッテリー・スプレー缶・家電4品目・PC等はitem-level APP_READYで個別の公式証拠を必須にする。

## M028証拠

- PRIMARY_INDEX: 由良町公式 住民向けごみ分別案内
- SUPPLEMENTAL_INDEX: 広報ゆら2026年3月号
- reviewed_category_count: 5
- MANUAL_INDEX_REVIEW
- QA_PASSED

## Gate

- Batch 03 structural validation: PASS
- canonical structural validation: PASS
- Schema RED TEAM: PASS
- Batch 03 RED TEAM: PASS
- operational semantics RED TEAM: PASS
- NEXT_BATCH_GATE: PASS
- APP_READINESS_GATE: HOLD
''', encoding="utf-8")
print("Schema v1.2.4 labels synchronized")
