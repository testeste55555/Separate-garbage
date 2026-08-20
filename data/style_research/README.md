# Style Research Pilot

自治体公式の分別色を、既存category正本・item mapping・教材グループから独立して保持する追加レイヤーです。

- `03_top10_targets.csv`: 事前確定順位・Stage・正本状態
- `04_stage_a_style_observations.csv`: TOP1〜5の色観測
- `07_stage_b_style_observations.csv`: TOP6〜10の色観測
- `08_style_color_observations.csv`: TOP10統合の一対多公式色観測
- `08_style_ui_projection.csv`: CURRENT / SORT_BUCKETごとのUI採否
- `09_style_sources.csv`: style専用公式出典台帳

`OFFICIAL_DERIVED` のHEXは公式PDF・画像からの近似値であり、自治体が公表したHEXではありません。`NOT_CONFIRMED` は空欄のまま保持します。アプリ標準色を使う場合は、この正本を上書きせず実行時に `FALLBACK` として明示してください。

再生成・検証:

```bash
python3 scripts/build_style_research_pilot.py
python3 scripts/validate_style_research.py --gate
python3 scripts/red_team_style_research.py
```
