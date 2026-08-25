# Lesson scoring-mode validation

`validate_lesson_scoring_modes.py`は、学習者UIの自動正誤判定が`APP_READY`または`LESSON_READY_10`の明示的安全境界に限定されていることを検証します。旧`validate_app_ready_lesson_modes.py`は互換entrypointです。

主な検証点：

- APP_READYレビューが各40共通品目をカバーすること
- LESSON_READY_10レビューが固定画像10品目をカバーし、各品目にscoring branchを1つだけ持つこと
- `lesson_mode_app_ready_scope.csv` の対象が実装済みレビューと完全一致すること
- 全条件枝が `branch_review_status=COMPLETE` であること
- canonical mapping/coverageがレビューと一致し、LESSON_READY_10をAPP_READYとして数えないこと
- 画像問題のmappingが `VERIFIED` であること
- 画像アセットが `CONFIRMED` で実ファイルと対応すること
- 正解categoryがCURRENTなSORT_BUCKETへ安全に投影できること
- 学習者画面に品目名、条件、前処理、例外説明を出さないこと
- オンライン／対面がネットワーク状態ではなく授業モードとして実装されること

`red_team_lesson_scoring_modes.py`は、10品目欠落、二重scoring branch、条件枝未完、公式根拠欠落、誤category、10品目からAPP_READYへの偽昇格をmutationで検出します。旧`red_team_app_ready_lesson_modes.py`は互換entrypointです。
