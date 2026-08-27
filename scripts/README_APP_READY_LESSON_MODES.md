# Lesson scoring-mode validation

`validate_lesson_scoring_modes.py`は、学習者UIの自動正誤判定が`APP_READY`または`LESSON_READY_10`の明示的安全境界に限定されていることを検証します。旧`validate_app_ready_lesson_modes.py`は互換entrypointです。

主な検証点：

- APP_READYレビューが各40共通品目をカバーすること
- LESSON_READY_10レビューが固定画像10品目をカバーし、各品目にscoring branchを1つだけ持つこと
- scopeに固定した必須条件枝数とreview行数が一致し、例外枝だけの削除も拒否すること
- `lesson_mode_app_ready_scope.csv` の対象が実装済みレビューと完全一致すること
- 全条件枝が `branch_review_status=COMPLETE` であること
- canonical mapping/coverageがレビューと一致し、LESSON_READY_10をAPP_READYとして数えないこと
- 画像問題のmappingが `VERIFIED` であること
- 画像アセットが `CONFIRMED` で実ファイルと対応すること
- 正解categoryがCURRENTなSORT_BUCKETへ安全に投影できること
- 学習者画面に品目名、条件、前処理、例外説明を出さないこと
- オンライン／対面がネットワーク状態ではなく授業モードとして実装されること

`red_team_lesson_scoring_modes.py`は、scope内のすべての`LESSON_READY_10`自治体に対して、10品目欠落、条件枝削除、二重scoring branch、条件枝未完、公式根拠欠落、誤category、10品目からAPP_READYへの偽昇格をmutationで検出します。旧`red_team_app_ready_lesson_modes.py`は互換entrypointです。

`validate_lesson_variants.py`は、M098/M099の`district_scope`と`lesson_variant_group`を分離して検証します。尾道市6 scopeの固定10品目正答セットとI031教材分類が共通であること、福山市で紙類の正答差を3グループに維持すること、内海町・沼隈町を再分割しないこと、オンライン固定10品目BOXと対面主要分別箱を混同しないこと、教師用条件・例外・特殊経路を学習者UIへ出さないことを確認します。

`red_team_lesson_variants.py`は、向島町立花の不要分割、M098共通正答・I031分類の崩壊、因島I031を競合するWeb locatorへ戻す変更、沼隈町の誤グループ化、福山市3グループの紙パック・新聞・段ボールの誤採点、対面モードへの固定10品目専用BOX混入、走島町の特殊経路露出など19 mutationを拒否します。
