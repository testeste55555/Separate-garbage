# Workflow

- `WORK_ゴミ出し情報収集フロー_143自治体_v1.1.txt`〜`v1.16.txt`：Schema・QA・証拠分離・Batch運用の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.17.txt`：固定IDとactive targetを分離し、M065知夫村をDEFERREDとしてBatch 07を完了した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.18.txt`：地域別CURRENT体系を`SCHEMA_SCOPE_LIMITATION`として扱い、M076備前市をDEFERREDとした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.19.txt`：公式URL存在と一次資料本文によるcategory completenessを分離し、M086新庄村をDEFERREDとした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.20.txt`：OFFICIAL_COUNT_MATCHEDを明示的数値総数へ限定し、地域variantのM098尾道市・M099福山市・M100府中市をDEFERREDにした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.21.txt`：現行年度資料優先、別袋によるresident-facing child leaf、内部小分類との区別、上位分類数と公式葉数の分離、自治体固有の危険物前処理をBatch 11で再固定した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.22.txt`：**現行版**。同名見出しと公式葉の衝突はcategory_groupで解消し、特殊経路の非操作的親をSORT_BUCKETへ昇格させず、DROP_OFF/BOOKED_PICKUP等の実経路と最新危険物体系を保持する原則をBatch 12で固定

## 現在地

- Schema：v1.2.4
- Workflow：v1.22
- 固定ID：143自治体
- active実装対象：135自治体
- DEFERRED：M065 知夫村、M076 備前市、M086 新庄村、M098 尾道市、M099 福山市、M100 府中市、M120 萩市、M123 岩国市
- canonical：117自治体
- QA：117/117 `QA_PASSED`
- category：1,402行（構造化公式葉1,290区分）
- source：316
- item mapping：1,180条件枝
- coverage：4,680 pair
- category review evidence：279
- Batch 12 RED TEAM：PASS
- canonical structural validation：PASS
- Schema v1.2.4 RED TEAM：PASS
- operational category semantics RED TEAM：PASS
- NEXT_BATCH_GATE：PASS
- APP_READINESS_GATE：HOLD

## Batch 12

MASTER範囲：M116〜M125。

active：
- M116 神石高原町 18
- M117 下関市 10
- M118 宇部市 13
- M119 山口市 15
- M121 防府市 18
- M122 下松市 15
- M124 光市 14
- M125 長門市 17

DEFERRED：
- M120 萩市：大島・見島・相島地区で一部分別区分が異なるため`SCHEMA_SCOPE_LIMITATION`
- M123 岩国市：地域群により食品トレー等の分別先・排出方法が異なるため`SCHEMA_SCOPE_LIMITATION`

Batch 12では、神石高原町の同名見出し／公式葉の衝突を人工的な名称変更で解消せずcategory_groupを使用した。防府市の粗大・埋立・一時多量ごみは、説明上の親を学習者SORT_BUCKETへ昇格させず、同一category_groupの独立REFERENCE_ONLY葉とした。

また、宇部市の充電式電池、山口市の2026年7月改定`有害ごみ(1)(2)`等、ステーション外の公式経路は`DROP_OFF`等のcollection_channelを保持している。危険物の穴あけルールは自治体固有で、近隣自治体から横展開していない。

GitHub ActionsによるBatch 12検証は、Batch structural validation・専用RED TEAM・canonical merge・canonical validation・Schema RED TEAM・operational category semantics RED TEAM・NEXT_BATCH_GATEまでPASS。CI記録は`docs/research/batch_12_ci_status.txt`。

## 次Batch

Batch 13はM126〜M135の山口県残り10自治体を基本範囲とする。

M126 柳井市 → M127 美祢市 → M128 周南市 → M129 山陽小野田市 → M130 周防大島町 → M131 和木町 → M132 上関町 → M133 田布施町 → M134 平生町 → M135 阿武町
