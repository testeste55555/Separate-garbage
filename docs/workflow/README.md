# Workflow

- `WORK_ゴミ出し情報収集フロー_143自治体_v1.1.txt`〜`v1.16.txt`：Schema・QA・証拠分離・Batch運用の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.17.txt`：固定IDとactive targetを分離し、M065知夫村をDEFERREDとしてBatch 07を9自治体で完了した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.18.txt`：同一自治体内の複数CURRENT体系を`SCHEMA_SCOPE_LIMITATION`として扱い、M076備前市をDEFERREDとした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.19.txt`：**現行版**。公式URLの存在と一次資料本文によるcategory completenessを分離し、M086新庄村をDEFERREDとしてBatch 09を9自治体で完了。複合収集ラベル・公式総数・委託先taxonomyの扱いを明文化

## 現在地

- Schema：v1.2.4
- Workflow：v1.19
- 固定ID：143自治体
- active実装対象：140自治体
- DEFERRED：M065 知夫村、M076 備前市、M086 新庄村
- canonical：92自治体
- QA：92/92 `QA_PASSED`
- category：1,094行（構造化公式葉1,008区分）
- source：253
- item mapping：932条件枝
- coverage：3,680 pair
- category review evidence：216
- Batch 09 RED TEAM：PASS
- canonical structural validation：PASS
- Schema v1.2.4 RED TEAM：PASS
- NEXT_BATCH_GATE：PASS
- APP_READINESS_GATE：HOLD

## Batch 09

active target：M084・M085・M087〜M093の9自治体。

M086新庄村は、県の現行公式案内から村のごみ収集公式ページへの導線は確認できるものの、村側一次資料本文を安定取得できず、住民向け全分別区分を全件照合できないため`OFFICIAL_SOURCE_BODY_UNAVAILABLE`としてDEFERREDにします。地域計画等からcategoryを補作しません。

Batch 09では、勝央町の公式「7種分別収集」、奈義町の複合ラベル、西粟倉村の村版令和8年度カレンダー、久米南町のスプレー缶「穴を開けない」等を自治体固有のルールとして保持しています。

GitHub ActionsによるBatch 09検証は、Batch structural validation・専用RED TEAM・canonical merge・canonical validation・Schema RED TEAM・NEXT_BATCH_GATEまでPASSしています。CI記録は`docs/research/batch_09_ci_status.txt`です。
