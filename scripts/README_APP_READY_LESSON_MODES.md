# APP_READY lesson-mode validation

`validate_app_ready_lesson_modes.py` は、学習者UIの自動正誤判定がAPP_READY自治体に限定されていることを検証します。

主な検証点：

- M094・M095・M104のレビューが各40共通品目をカバーすること
- `lesson_mode_app_ready_scope.csv` の対象が実装済みレビューと完全一致すること
- 全条件枝が `branch_review_status=COMPLETE` であること
- 画像問題のmappingが `VERIFIED` であること
- 画像アセットが `CONFIRMED` で実ファイルと対応すること
- 正解categoryがCURRENTなSORT_BUCKETへ安全に投影できること
- 学習者画面に品目名、条件、前処理、例外説明を出さないこと
- オンライン／対面がネットワーク状態ではなく授業モードとして実装されること

`red_team_app_ready_lesson_modes.py` は、APP_READYゲートの欠落、ネットワーク状態との混同、学習者画面への説明漏出、○/×以外の正答説明への回帰を静的に検出します。
