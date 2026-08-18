# Schema v1.2.2 Initial Mapping Candidate Fix Report

実施日：2026-08-18  
対象：初期mapping候補生成器  
Schema列・enum・主キー変更：なし

## 発見した問題

旧生成器は `自治体正式名称`、`代表品目` に加えて、`入れてはいけない物`、`出す前の処理`、`注意事項` を連結して品目パターンを検索していた。このため、次のような偽陽性が発生した。

- M001・I021「衣類」から、代表品目に「衣類乾燥機」を含む「家電リサイクル対象製品」枝を生成
- 「乾電池は入れない」「スプレー缶は対象外」等の除外説明だけで、そのcategoryを当該品目の候補として生成
- 家電4品目、パソコン、割れガラス等の条件外・注意文だけで候補を生成

## 修正

Positive evidenceを次の2列に限定した。

- `自治体正式名称`
- `代表品目`

次のNegative/context evidenceは候補生成に使用しない。

- `入れてはいけない物`
- `条件外の扱い`
- `出す前の処理`
- `注意事項`

さらに、パターン一致箇所が次の複合語内にある場合は、その一致だけを無視するcollision guardを追加した。

- 白色以外のトレイ → 白色トレイではない
- 衣類乾燥機 → 衣類ではない
- LED蛍光灯・電球型蛍光灯 → 蛍光管候補ではない
- 充電池を外せない小型家電 → 通常の小型家電候補ではない
- パソコン周辺機器 → 家庭用パソコン本体ではない
- 食用油ボトル → 使用済み食用油ではない

collision spanと重ならない別のPositive mentionが同じcategoryにある場合、その独立した一致は有効とする。

## データ再生成結果

| dataset | 修正前mapping枝 | 修正後mapping枝 | 除去 |
|---|---:|---:|---:|
| Pilot | 93 | 76 | 17 |
| Batch 01 | 190 | 161 | 29 |
| canonical | 283 | 237 | 46 |

canonical coverageは244 `MAPPED_INITIAL` / 356 `NOT_RESEARCHED` から、225 `MAPPED_INITIAL` / 375 `NOT_RESEARCHED` へ更新した。coverage直積600 pairは維持している。

除去対象はすべて `INITIAL_REVIEW_REQUIRED` の機械候補であり、手動 `VERIFIED` / `APP_READY` 枝は存在せず、品目別公式証拠も失っていない。reconciliationは今後も参照が有効な手動review枝を候補外でも保持する。

## RED TEAM

次の2観点を追加し、19/19 PASSとした。

1. 共通40品目すべてについて、Positive fixtureは候補化し、同じ語をNegative/context 4列だけに置いたfixtureは候補化しない。
2. 既知複合語collisionと実データM001・I021を検査し、保存済み初期mappingが現生成器と同期していることを確認する。

```text
RED_TEAM_SUMMARY=19/19
SCHEMA_V12_RED_TEAM_PASSED
```

13自治体の実資料レビューとBatch 02調査は本修正では実施していない。
