# Style Research Pilot QA

実施日: 2026-08-20

## 集計

- 固定TOP10: 10自治体（順位変更なし）
- category参照可能: 8自治体
- canonical地域variant待ち: M098尾道市・M099福山市
- style公式出典: 26
- 色観測: 61
- UI projection: 51 CURRENT / SORT_BUCKET
- `OFFICIAL_DERIVED`: 47 projection
- `NOT_CONFIRMED`: 4 projection
- `FALLBACK`: 0（Pilot正本へアプリ標準色を混入していない）

## 自治体別projection

| 自治体 | 件数 | DERIVED | NOT_CONFIRMED | 主根拠 |
|---|---:|---:|---:|---|
| 広島市 | 7 | 7 | 0 | 年度版分別表 |
| 東広島市 | 9 | 9 | 0 | ごみブック区分枠。共有指定袋色は別観測 |
| 呉市 | 6 | 6 | 0 | 年度カレンダー凡例 |
| 三原市 | 9 | 9 | 0 | ステーション看板 |
| 廿日市市 | 5 | 4 | 1 | 指定袋色。資源親は複数方法 |
| 安芸高田市 | 5 | 3 | 2 | 公式ポスター。白地・複数子色は未確認 |
| 海田町 | 4 | 3 | 1 | 公式分別表。資源親は3意味色競合 |
| 江田島市 | 6 | 6 | 0 | 令和8年度改定ポスター |

## 真正性QA

- 全sourceに公式URL、locator、scope、確認日がある。
- 全style category_idは同一自治体のCURRENT/SORT_BUCKETを参照する。
- 既存category・mapping・教材グループに差分なし。
- PDF/画像由来HEXは全件`OFFICIAL_DERIVED`かつ近似noteあり。
- `OFFICIAL_CONFIRMED`の東広島市指定袋色名7観測には、推測HEXを入れていない。
- M105資源親、M106燃える/容器包装親、M109資源親は無理に色を作らず`NOT_CONFIRMED`。
- 色だけに依存しないため全projectionで`accessibility_label_required=TRUE`。
- text/displayコントラストは全数4.5:1以上。

## 実行結果

```text
PASS Style Research validation
targets=10
active_municipalities=8
canonical_deferred_municipalities=2
sources=26
observations=61
projections=51
official_derived_projections=47
not_confirmed_projections=4
```
