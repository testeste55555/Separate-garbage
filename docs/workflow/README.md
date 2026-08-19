# Workflow

- `WORK_ゴミ出し情報収集フロー_143自治体_v1.1.txt`〜`v1.16.txt`：Schema・QA・証拠分離・Batch運用の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.17.txt`：固定IDとactive targetを分離し、M065知夫村をDEFERREDとしてBatch 07を完了した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.18.txt`：地域別CURRENT体系を`SCHEMA_SCOPE_LIMITATION`として扱い、M076備前市をDEFERREDとした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.19.txt`：公式URL存在と一次資料本文によるcategory completenessを分離し、M086新庄村をDEFERREDとした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.20.txt`：OFFICIAL_COUNT_MATCHEDを明示的数値総数へ限定し、地域variantのM098尾道市・M099福山市・M100府中市をDEFERREDにした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.21.txt`：現行年度資料優先、別袋によるresident-facing child leaf、内部小分類との区別、上位分類数と公式葉数の分離、自治体固有の危険物前処理をBatch 11で再固定した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.22.txt`：同名見出しと公式葉の衝突をcategory_groupで解消し、特殊経路の実collection_channelと最新危険物体系を保持した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.23.txt`：**現行版**。上位見出し数とresident-facing official leaf総数を分離し、検索サービスのformal check status、地域差の日程/taxonomy切り分け、2026年改定後の同日収集と分別単位の区別をBatch 13で固定

## 現在地

- Schema：v1.2.4
- Workflow：v1.23
- 固定ID：143自治体
- active実装対象：134自治体
- DEFERRED：M065 知夫村、M076 備前市、M086 新庄村、M098 尾道市、M099 福山市、M100 府中市、M120 萩市、M123 岩国市、M127 美祢市
- canonical：126自治体
- QA：126/126 `QA_PASSED`
- category：1,512行（構造化公式葉1,387区分）
- source：343
- item mapping：1,259条件枝
- coverage：5,040 pair
- category review evidence：306
- Batch 13 RED TEAM：PASS
- canonical structural validation：PASS
- Schema v1.2.4 RED TEAM：PASS
- operational category semantics RED TEAM：PASS
- NEXT_BATCH_GATE：PASS
- APP_READINESS_GATE：HOLD

## Batch 13

MASTER範囲：M126〜M135。

active：
- M126 柳井市 10
- M128 周南市 11
- M129 山陽小野田市 12
- M130 周防大島町 12
- M131 和木町 11
- M132 上関町 12
- M133 田布施町 12
- M134 平生町 12
- M135 阿武町 5

DEFERRED：
- M127 美祢市：美祢・美東・秋芳で正式区分・同一品目の分別先が異なるため`SCHEMA_SCOPE_LIMITATION`

Batch 13では、柳井市の複合見出しを実際の別袋・別束・回収ボックス単位へ分解し、田布施町・平生町の`7分別`をresident-facing official leaf総数へ誤転用しなかった。周防大島町の公式検索サービスは`CHECKED_PRESENT`＋URL/date evidenceで管理している。

阿武町は2026年4月改定後も可燃・不燃・資源の3指定袋を維持するため、同日収集化をcategory統合と解釈しない。危険物の穴あけルールは柳井・周南は穴あけ、周防大島は不要、和木は穴を開けず、上関は引用ページに穴あけ有無の明示なしとして個別保持する。

GitHub ActionsによるBatch 13検証は、Batch structural validation・専用RED TEAM・canonical merge・canonical validation・Schema RED TEAM・operational category semantics RED TEAM・NEXT_BATCH_GATEまでPASS。CI記録は`docs/research/batch_13_ci_status.txt`。

## 次Batch

Batch 14はMASTER残りM136〜M143の8自治体を基本範囲とする。

M136 吉野川市 → M137 綾川町 → M138 多度津町 → M139 丸亀市 → M140 三豊市 → M141 小竹町 → M142 北九州市 → M143 佐伯市

Batch 14完了時、DEFERREDを除く134自治体のcategory研究が一巡する見込み。
