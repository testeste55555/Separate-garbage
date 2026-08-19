# Batch 07 QA Report

実施日: 2026-08-19
Schema: v1.2.4
対象: M064〜M073

## 判定

Batch 07は研究bundleを作成済みだが、**完了扱いにはしない**。

- QA_PASSED: 9自治体
- QA_REQUIRED: 1自治体（M065 知夫村）
- NEXT_BATCH_GATE: HOLD
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

これらは住民向け公式ページ・現年度資料・現行条例・公式ガイド等を用いてcategory completenessを確認した。

### 重要な真正性確認

- 岡山市: 令和6年3月開始の「プラスチック資源」をCURRENTとして保持。
- 倉敷市: 「雑がみ」を詳細品目条件から人工的な独立SORT_BUCKETへ昇格させない。
- 津山市: 公式生活ガイドが示す6種類を採用。自治体正式名称の表記も公式資料に合わせる。
- 笠岡市: 令和8年度の現行名称「もやすしかないごみ」を採用。ガス・スプレー缶は中身を使い切り、公式案内どおり穴あけルールを保持。
- 井原市: 現行ガイドの8葉を採用し、製品プラスチック対象拡大を「資源ごみ（プラ）」へ反映。

## M065 知夫村 — QA_REQUIRED

現在の村公式行政サイトと「ゴミ・リサイクル」ページの所在、2026年の村公式案内から同ページへ住民を誘導していることまでは確認できた。

しかし、今回の取得環境では当該ページおよび旧公式分別PDFの本文取得が安定せず、**住民が排出時に選択する全分別区分を全件照合できていない**。

したがって:

- `category_count_check_status=NOT_REVIEWED`
- `category_count_verified=FALSE`
- category行を推測で作成しない
- `QA_REQUIRED`を維持

とする。

「公式URLが存在する」「現行の案内先である」だけではcategory completenessの証明にならない。全区分本文を確認できるまでQA_PASSEDへ昇格させない。

## Batch Gate

Batch 07は7成果物を研究bundleとして保持するが、M065が未解決のためBatch 08へ進まない。

canonicalの完了自治体はBatch 06までの65自治体を現時点の正式完了値として扱う。Batch 07の9 QA_PASSED自治体はbundle内で証拠を保持し、M065解消後にBatch 07全体を再validation・RED TEAM・mergeする。

## 再開条件

M065について、知夫村が現在住民向けに使用している分別表・収集カレンダー・分別冊子等から全区分を読める状態で取得し、次を満たすこと。

1. 住民向け全区分の一覧を確定
2. `MANUAL_INDEX_REVIEW`または`OFFICIAL_COUNT_MATCHED`
3. `category_review_evidence`にPRIMARY_INDEXを保存
4. Batch 07 structural validation
5. Batch 07専用RED TEAM
6. canonical merge後のSchema RED TEAM
7. NEXT_BATCH_GATE再判定

ここを満たすまでBatch 08はHOLDとする。
