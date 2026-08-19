# Workflow

- `WORK_ゴミ出し情報収集フロー_143自治体_v1.1.txt`〜`v1.16.txt`：Schema・QA・証拠分離・Batch運用の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.17.txt`：固定IDとactive targetを分離し、M065知夫村をDEFERREDとしてBatch 07を完了した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.18.txt`：地域別CURRENT体系を`SCHEMA_SCOPE_LIMITATION`として扱い、M076備前市をDEFERREDとした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.19.txt`：公式URL存在と一次資料本文によるcategory completenessを分離し、M086新庄村をDEFERREDとした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.20.txt`：**現行版**。OFFICIAL_COUNT_MATCHEDを明示的数値総数へ限定し、地域ごとの住民向け表示単位・正式名称が異なるM098尾道市・M099福山市・M100府中市を`SCHEMA_SCOPE_LIMITATION`としてDEFERREDにした

## 現在地

- Schema：v1.2.4
- Workflow：v1.20
- 固定ID：143自治体
- active実装対象：137自治体
- DEFERRED：M065 知夫村、M076 備前市、M086 新庄村、M098 尾道市、M099 福山市、M100 府中市
- canonical：99自治体
- QA：99/99 `QA_PASSED`
- category：1,159行（構造化公式葉1,072区分）
- source：270
- item mapping：990条件枝
- coverage：3,960 pair
- category review evidence：233
- Batch 10 RED TEAM：PASS
- canonical structural validation：PASS
- Schema v1.2.4 RED TEAM：PASS
- NEXT_BATCH_GATE：PASS
- APP_READINESS_GATE：HOLD

## Batch 10

active target：M095・M096・M097・M101・M103・M104・M105の7自治体。

M098尾道市、M099福山市、M100府中市は、令和8年度に地域別の住民向けCURRENT分類単位が併存するためDEFERREDです。収集曜日だけの差ではなく、住民が見るcategory名称・細分単位の差を含むため、municipality単位の単一taxonomyを適用しません。

Batch 10では、三原市だけが公式に「家庭ごみの分別方法は10分別」と数値総数を明示するため`OFFICIAL_COUNT_MATCHED`を使用しました。その他は公式一覧を全件照合した`MANUAL_INDEX_REVIEW`です。

GitHub ActionsによるBatch 10検証は、Batch structural validation・専用RED TEAM・canonical merge・canonical validation・Schema RED TEAM・NEXT_BATCH_GATEまでPASSしています。CI記録は`docs/research/batch_10_ci_status.txt`です。
