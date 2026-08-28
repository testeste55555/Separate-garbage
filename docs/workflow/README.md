# Workflow

- `WORK_ゴミ出し情報収集フロー_143自治体_v1.1.txt`〜`v1.16.txt`：Schema・QA・証拠分離・Batch運用の履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.17.txt`：固定IDとactive targetを分離し、M065知夫村をDEFERREDとしてBatch 07を完了した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.18.txt`：地域別CURRENT体系を`SCHEMA_SCOPE_LIMITATION`として扱い、M076備前市をDEFERREDとした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.19.txt`：公式URL存在と一次資料本文によるcategory completenessを分離し、M086新庄村をDEFERREDとした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.20.txt`：OFFICIAL_COUNT_MATCHEDを明示的数値総数へ限定し、地域variantのM098尾道市・M099福山市・M100府中市をDEFERREDにした履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.21.txt`：現行年度資料優先、別袋によるresident-facing child leaf、内部小分類との区別、上位分類数と公式葉数の分離、自治体固有の危険物前処理をBatch 11で再固定した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.22.txt`：同名見出しと公式葉の衝突をcategory_groupで解消し、特殊経路の実collection_channelと最新危険物体系を保持した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.23.txt`：上位見出し数とresident-facing official leaf総数の分離、検索サービスformal status、2026年改定後の同日収集と分別単位の区別をBatch 13で固定した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.24.txt`：初回category研究一巡完了後の運用基準
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.25.txt`：M094広島市APP readiness Pilotの履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.26.txt`：M104東広島市APP_READY化までの履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.27.txt`：LESSON_READY_10をAPP_READYから分離し、M097三原市の画像10品目・19条件枝を有効化した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.28.txt`：M105廿日市市の画像10品目・22条件枝を追加し、mutation RED TEAMを全LESSON_READY_10自治体へ汎用化した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.29.txt`：M098尾道市・M099福山市で`district_scope`と`lesson_variant_group`を分離し、オンライン固定10品目BOXと対面主要分別箱を分離した履歴版
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.30.txt`：一般自治体にも`SIMPLIFIED_ACTION`を適用可能にし、M106の非通常収集I029を教材用「回収・確認」へ安全投影
- `WORK_ゴミ出し情報収集フロー_143自治体_v1.31.txt`：**現行版**。Batch 11のM107〜M109を追加し、M107白色発泡トレーの非通常収集を詳細層に保持して教材のみ簡略化

## 現在地

- Schema：v1.2.4
- Workflow：v1.31
- 固定ID：143自治体
- active実装対象：132自治体
- DEFERRED：11自治体
  - M065 知夫村
  - M076 備前市
  - M086 新庄村
  - M098 尾道市
  - M099 福山市
  - M100 府中市
  - M120 萩市
  - M123 岩国市
  - M127 美祢市
  - M136 吉野川市
  - M139 丸亀市
- canonical：132自治体
- QA：132/132 `QA_PASSED`
- category：1,599行
- source：416
- item mapping：1,557条件枝
- coverage：5,280 pair
- category review evidence：334
- Batch 14 RED TEAM：PASS
- canonical structural validation：PASS
- Schema v1.2.4 RED TEAM：PASS
- operational category semantics RED TEAM：PASS
- NEXT_BATCH_GATE：PASS
- APP_READINESS_GATE：HOLD（M094・M095・M104の3/132自治体完了）
- lesson scoring：自治体単位60画像pair＋M098/M099の4地域variant group 40画像pair、計100画像pair

**固定143自治体のうち、現行Schemaで安全に一意化できる132 active自治体について、resident-facing category研究の初回一巡は完了。**

`APP_READINESS_GATE=HOLD`は正常な状態であり、40共通品目のITEM_SPECIFIC公式証拠・条件枝レビュー未完了を示す。category研究完了とは別Gateである。

## LESSON_READY_10

固定画像10品目だけをオンライン練習へ早期投入する安全境界。APP_READYの40品目atomic昇格とglobal Gateは変更しない。

- M097三原市：10/10品目、19/19条件枝COMPLETE
- M105廿日市市：10/10品目、22/22条件枝COMPLETE
- M106安芸高田市：10/10品目、18/18条件枝COMPLETE。I029は非通常収集categoryを保持して教材用`SIMPLIFIED_ACTION`「回収・確認」へ投影
- M107江田島市：10/10品目、18/18条件枝COMPLETE。I007白色発泡トレーは非通常収集categoryを保持して教材用`SIMPLIFIED_ACTION`「回収・確認」へ投影
- M108府中町：10/10品目、18/18条件枝COMPLETE。全品目を通常公式categoryへ投影
- M109海田町：10/10品目、18/18条件枝COMPLETE。全品目を通常公式categoryへ投影
- M098尾道市：6内部scopeを1教材groupへ集約、10/10採点pair
- M099福山市：4内部scopeを3教材groupへ集約、30/30採点pair
- canonical：`VERIFIED + branch_completeness_confirmed=TRUE`
- scoring branch：各品目1枝
- 残り30品目：未完了を維持し、APP_READY 0/40として扱う
- UI：オンラインは画像・採点BOX・○/×、対面は主要分別箱。`SIMPLIFIED_ACTION`は自治体正式区分ではない教材用簡略行動箱で、条件・前処理・例外・特殊経路・出典は教師側に保持
- mutation RED TEAM：6自治体×9ケース＋M106/M107投影境界8ケース、62/62 PASS

## Batch 14

MASTER範囲：M136〜M143。

active：
- M137 綾川町 11
- M138 多度津町 18
- M140 三豊市 16
- M141 小竹町 7
- M142 北九州市 13
- M143 佐伯市 12

DEFERRED：
- M136 吉野川市：鴨島地区と川島・山川・美郷地区で乾電池・蛍光管等の排出単位・回収容器・経路が異なるため`SCHEMA_SCOPE_LIMITATION`
- M139 丸亀市：旧丸亀地区と本島・牛島・小手島・手島等で分類・排出単位が異なるため`SCHEMA_SCOPE_LIMITATION`

Batch 14では、多度津町の`資源ごみ`を15住民子葉へ、三豊市の`紙類・布類`を5実排出子葉へ展開した。一方、小竹町の`びん・缶`は公式に一体の収集区分なので人工分割していない。

綾川町・小竹町の2026年開始の新規拠点回収は`DROP_OFF + REFERENCE_ONLY`で保持。北九州市の`かん・びん`と`ペットボトル`は別指定袋・別収集車なので索引親の下で別子葉にした。佐伯市は資源物の実排出単位を保持し、スプレー缶の2穴ルールを具体記載のある公式資料へ行単位で結び付けた。

GitHub ActionsによるBatch 14検証は、Batch structural validation・専用RED TEAM・canonical merge・canonical validation・Schema RED TEAM・operational category semantics RED TEAM・NEXT_BATCH_GATEまでPASS。CI記録は`docs/research/batch_14_ci_status.txt`。

## 次工程

固定IDのactive自治体を追加するcategory Batchはありません。次は主に次の3系統です。

1. 固定画像10品目をルールfamily単位で確認し、優先自治体を`LESSON_READY_10`へ進める。
2. 同じ公式根拠から残り30品目を継続確認し、40/40 `APP_READY`と`APP_READINESS_GATE`解消へ進める。
3. 地域variant DEFERRED自治体向けに`district_scope`等のSchema/UI拡張を設計する。
4. M065知夫村・M086新庄村など一次資料本文の安定取得が課題の自治体を、公式資料が安定確認できる時点で再調査する。

`NEXT_BATCH_GATE=PASS`は構造上次工程へ進めることを示し、未処理active自治体が残っていることを意味しない。
