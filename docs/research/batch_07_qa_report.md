# Batch 07 QA Report

実施日: 2026-08-19
Schema: v1.2.4
対象（active）: M064, M066〜M073
保留: M065 知夫村

## 最終判定

Batch 07は**9自治体で完了**とする。

M065 知夫村はユーザー判断により2026-08-19付で一旦実装対象外へ移し、固定IDを保持したまま`data/master/05_deferred_municipalities.csv`へ記録した。Batch 07のmunicipality/category/source/QA/mapping/coverage/review evidenceには含めない。

CI結果:

- Batch 07 active municipalities: 9
- Batch 07 structural validation: PASS
- Batch 07 RED TEAM: PASS
- canonical merge: PASS
- canonical structural validation: PASS
- Schema v1.2.4 RED TEAM: PASS
- NEXT_BATCH_GATE: PASS
- APP_READINESS_GATE: HOLD

## QA_PASSED

- M064 西ノ島町: 7住民区分
- M066 隠岐の島町: 7住民区分
- M067 岡山市: 6住民区分
- M068 倉敷市: 5住民区分
- M069 津山市: 6住民区分
- M070 玉野市: 9住民区分
- M071 笠岡市: 12住民区分
- M072 井原市: 8住民区分
- M073 総社市: 4住民区分

9自治体すべて、住民向け公式ページ・現年度資料・現行条例・公式ガイド等を用いてcategory completenessを確認し、`QA_PASSED`となっている。

## 重要な真正性確認

- 西ノ島町: 現行住民向けWebと令和8年度資料を照合し、7住民区分を保持。
- 隠岐の島町: 現行ガイド・令和8年度カレンダー・現行条例を照合し7区分を保持。
- 岡山市: 令和6年3月開始の「プラスチック資源」をCURRENTとして保持。
- 倉敷市: 「雑がみ」を詳細品目条件から人工的な独立SORT_BUCKETへ昇格させない。
- 津山市: 公式生活ガイドが示す6種類を採用し、自治体正式名称の表記も公式資料に合わせる。
- 玉野市: 不燃物A/Bを含む現行9住民区分を保持。
- 笠岡市: 令和8年度の現行名称「もやすしかないごみ」を採用。ガス・スプレー缶は公式案内どおり穴あけルールを保持。
- 井原市: 現行ガイドの8葉を採用し、製品プラスチック対象拡大を「資源ごみ（プラ）」へ反映。
- 総社市: 現行公式ページの4住民区分を保持。

## M065 知夫村の扱い

知夫村は削除ではなく**DEFERRED**とする。

- 固定ID `M065` は維持
- MASTERの元行は維持
- `data/master/05_deferred_municipalities.csv`で保留状態を明示
- Batch 07のactive target setから除外
- canonicalへはmergeしない
- 後日、公式一次資料の全区分を取得できた場合はM065のまま再開可能

これにより、今回のBatch進行を知夫村1自治体でブロックしない一方、後日の復帰時にID再採番や履歴破壊を起こさない。

## canonical反映

Batch 07完了後のcanonicalは74自治体となった。M065は含まない。

Batch 07の9自治体×40品目=360 coverage pairを追加し、category/source/mapping/review evidenceもno-loss mergeした。

## Gate

`NEXT_BATCH_GATE=PASS`のため、次Batchへ進行可能。

`APP_READINESS_GATE=HOLD`は従来どおり正常状態である。40共通品目についてITEM_SPECIFICな公式証拠、coverage、全条件枝レビューが揃うまではAPP_READYへ昇格させない。
