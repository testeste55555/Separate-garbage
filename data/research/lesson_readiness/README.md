# LESSON_READY_10 review grids

固定画像10品目をオンライン授業の自動正誤判定へ投入するための教師用監査表です。40品目`APP_READY`とは独立します。

現在の監査済みscope：

- M097 三原市：10品目・19条件枝
- M105 廿日市市：10品目・22条件枝

scoring viability preflightで停止中：

- M106 安芸高田市：10/10品目の通常BOX投影可否を先行確認。I029モバイルバッテリーは現行の直接品目案内で販売店・リサイクル業者の引取とされ、一般ごみ・小型家電回収BOXは不可。`BLOCKED_NON_SORT_BUCKET`として記録し、`LESSON_READY_10` scopeへ追加しない。

停止理由の正本は`lesson_ready_10_preflight_blockers.csv`です。固定10品目を詳細レビューする前に通常`SORT_BUCKET`へ投影できるかを先行確認し、非BOX品目が1つでもあれば全条件枝レビューへ進まず次の優先自治体へ移ります。

自治体追加時は、既存reviewをコピーして自治体・公式根拠・全条件枝を個別確認し、次を満たします。

- 固定10品目を過不足なく含む
- 分別先又は前処理が変わる条件枝を省略しない
- 全枝`ITEM_SPECIFIC / COMPLETE`
- 品目ごとに画像と一致する`scoring_branch=TRUE`を1枝だけ指定
- 通常枝だけでなく例外の公式source・URL・locatorも保持
- 地域variantの正式名称・条件を他地域と統合しない
- 非BOX経路を通常の仕分けBOXにしない
- preflight blockerがある自治体をlesson scopeへ追加しない

反映と検証：

```bash
python3 scripts/sync_lesson_ready_reviews.py
python3 scripts/validate_lesson_scoring_modes.py
python3 scripts/red_team_lesson_scoring_modes.py
```

`sync_lesson_ready_reviews.py`はreviewをcanonicalへ`VERIFIED / COMPLETE`として投影します。`APP_READY`への昇格は行いません。
