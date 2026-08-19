# Workflow

- `WORK_ゴミ出し情報収集フロー_143自治体_v1.1.txt`〜`v1.16.txt`：Schema・QA・証拠分離・Batch運用の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.17.txt`：固定IDとactive targetを分離し、M065知夫村をDEFERREDとしてBatch 07を完了した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.18.txt`：地域別CURRENT体系を`SCHEMA_SCOPE_LIMITATION`として扱い、M076備前市をDEFERREDとした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.19.txt`：公式URL存在と一次資料本文によるcategory completenessを分離し、M086新庄村をDEFERREDとした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.20.txt`：OFFICIAL_COUNT_MATCHEDを明示的数値総数へ限定し、地域variantのM098尾道市・M099福山市・M100府中市をDEFERREDにした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.21.txt`：**現行版**。現行年度資料優先、別袋によるresident-facing child leaf、内部小分類との区別、上位分類数と公式葉数の分離、自治体固有の危険物前処理をBatch 11で再固定

## 現在地

- Schema：v1.2.4
- Workflow：v1.21
- 固定ID：143自治体
- active実装対象：137自治体
- DEFERRED：M065 知夫村、M076 備前市、M086 新庄村、M098 尾道市、M099 福山市、M100 府中市
- canonical：109自治体
- QA：109/109 `QA_PASSED`
- category：1,270行（構造化公式葉1,170区分）
- source：287
- item mapping：1,085条件枝
- coverage：4,360 pair
- category review evidence：250
- Batch 11 RED TEAM：PASS
- canonical structural validation：PASS
- Schema v1.2.4 RED TEAM：PASS
- operational category semantics RED TEAM：PASS
- NEXT_BATCH_GATE：PASS
- APP_READINESS_GATE：HOLD

## Batch 11

active target：M106〜M115の10自治体。新規DEFERREDはありません。

公式葉：
- M106 安芸高田市 11
- M107 江田島市 8
- M108 府中町 11
- M109 海田町 9
- M110 熊野町 6
- M111 坂町 13
- M112 安芸太田町 12
- M113 北広島町 11
- M114 大崎上島町 8
- M115 世羅町 9

Batch 11では全自治体を`MANUAL_INDEX_REVIEW`とした。江田島市は令和8年度改定ポスターの`資源ごみ（古紙・布類）`を現行区分として採用し、旧資料の分割を引き継がない。安芸高田市・安芸太田町・世羅町では、住民が上位区分の内部を別袋へ分けるため公式子葉を保持した。一方、熊野町の内部「小分類」は独立categoryへ人工展開しない。

スプレー缶等は、穴あけ不要・穴あけ可・穴あけ必須が近隣自治体でも混在するため、自治体固有の公式一次資料だけを根拠とする。

GitHub ActionsによるBatch 11検証は、Batch structural validation・専用RED TEAM・canonical merge・canonical validation・Schema RED TEAM・operational category semantics RED TEAM・NEXT_BATCH_GATEまでPASS。CI記録は`docs/research/batch_11_ci_status.txt`。

## 次Batch

Batch 12はM116神石高原町〜M125長門市の10自治体を基本範囲とする。M116で広島県を完了し、M117から山口県へ入る。
