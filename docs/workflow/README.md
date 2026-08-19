# Workflow

- `WORK_ゴミ出し情報収集フロー_143自治体_v1.1.txt`〜`v1.16.txt`：Schema・QA・証拠分離・Batch運用の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.17.txt`：固定IDとactive targetを分離し、M065知夫村をDEFERREDとしてBatch 07を9自治体で完了した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.18.txt`：**現行版**。同一自治体内に複数CURRENT分別体系がある場合の`SCHEMA_SCOPE_LIMITATION`を定義し、M076備前市をDEFERREDとしてBatch 08を9自治体で完了

## 現在地

- Schema：v1.2.4
- Workflow：v1.18
- 固定ID：143自治体
- DEFERRED：M065 知夫村、M076 備前市
- canonical：83自治体
- QA：83/83 `QA_PASSED`
- category：1,018行（構造化公式葉935区分）
- source：236
- item mapping：877条件枝
- coverage：3,320 pair
- category review evidence：199
- Schema RED TEAM：25/25 PASS
- Batch 08 RED TEAM：24/24 PASS
- NEXT_BATCH_GATE：PASS
- APP_READINESS_GATE：HOLD

## Batch 08

active target：M074・M075・M077〜M083の9自治体。

M076備前市は令和8年度に「資源回収ステーション設置済地区の9種23分別」と「未設置地区の旧分別」が併存します。これは収集曜日差ではなくcategory CORE自体の差なので、現Schema/UIで片方を市全域ルールとして採用せず`SCHEMA_SCOPE_LIMITATION`としてDEFERREDにします。

Batch 08では、瀬戸内市のスプレー缶について旧分別資料より現行の市公式火災防止案内を優先し、「安全機構を利用し中身を完全に出し切る」をCURRENT前処理として保持します。高梁市・美作市・和気町など穴あけを明示する自治体とは別ルールとして扱います。

GitHub ActionsによるBatch 08検証は、Batch structural validation・専用RED TEAM・canonical merge・canonical validation・Schema RED TEAM・NEXT_BATCH_GATEまでPASSしています。CI記録は`docs/research/batch_08_ci_status.txt`です。
