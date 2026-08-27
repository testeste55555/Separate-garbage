# LESSON_READY_10 review grids

固定画像10品目をオンライン授業の自動正誤判定へ投入するための教師用監査表です。40品目`APP_READY`とは独立します。

現在の監査済みscope：

- M097 三原市：10品目・19条件枝
- M105 廿日市市：10品目・22条件枝
- M106 安芸高田市：10品目・18条件枝。I029は非通常収集categoryを保持し、教材のみ`SIMPLIFIED_ACTION`へ投影
- M098 尾道市：1 lesson variant group・10採点pair
- M099 福山市：3 lesson variant group・30採点pair

M098/M099は自治体単位の完全categoryを作らず、`data/app/district_scopes.csv`と`lesson_variant_*`の地域variant専用層で保持します。尾道市は6内部scopeの固定10品目正答が教材上同一であることを確認して1グループとし、I031の資料表記差は「有害ごみ系」へ教材正規化します。福山市の4内部scopeは教材上3グループとし、内海町・沼隈町は再分割しません。完全taxonomy・40品目`APP_READY`側の`DEFERRED`を解除するものではありません。

自治体追加時は、既存reviewをコピーして自治体・公式根拠・全条件枝を個別確認し、次を満たします。

- 固定10品目を過不足なく含む
- 分別先又は前処理が変わる条件枝を省略しない
- 全枝`ITEM_SPECIFIC / COMPLETE`
- 品目ごとに画像と一致する`scoring_branch=TRUE`を1枝だけ指定
- 通常枝だけでなく例外の公式source・URL・locatorも保持
- 地域variantの正式名称・条件を他地域と統合しない
- 非BOX経路を通常の仕分けBOXにしない
- 非通常収集categoryを保持したまま教材用簡略行動箱へ投影する場合は、`SIMPLIFIED_ACTION`を明示し、特殊回収経路・施設・条件詳細を学習者UIへ出さない

反映と検証：

```bash
python3 scripts/sync_lesson_ready_reviews.py
python3 scripts/validate_lesson_scoring_modes.py
python3 scripts/red_team_lesson_scoring_modes.py
python3 scripts/validate_lesson_variants.py
python3 scripts/red_team_lesson_variants.py
```

`sync_lesson_ready_reviews.py`はreviewをcanonicalへ`VERIFIED / COMPLETE`として投影します。`APP_READY`への昇格は行いません。
