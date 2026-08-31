# LESSON_READY_10 regional batch — 2026-08-28

## Scope boundary

This batch implements only the fixed ten lesson items (`I001`, `I004`, `I006`, `I007`, `I013`, `I014`, `I017`, `I029`, `I031`, `I033`). It does not promote any target to the canonical 40-item `APP_READY` layer. Canonical `DEFERRED` rows therefore remain in `data/master/05_deferred_municipalities.csv`, while lesson readiness is recorded independently in the variant layer.

The learner sees a regional choice only when a fixed-ten answer or a principal teaching BOX changes. Collection-day differences alone remain internal district provenance.

## Implemented municipalities

| Municipality | Learner groups | Selection | Decision boundary |
|---|---:|---|---|
| M076 備前市 | 2 | required | 9種23分別地域 / 旧分別地域 |
| M100 広島県府中市 | 2 | required | 府中地区 / 上下地区 |
| M120 萩市 | 1 | not required | 本土側のみを教材対象。島しょ部はreadiness・scoring・BOXから除外 |
| M123 岩国市 | 2 | required | 食品トレーの正答/action差で4地区ずつに統合 |
| M127 美祢市 | 3 | required | 美祢 / 美東 / 秋芳 |
| M136 吉野川市 | 1 | not required | 鴨島A/B・川島・山川・美郷のcalendar差はfixed10正答を変えない |
| M139 丸亀市 | 1 | not required | 旧丸亀・綾歌飯山・島部等のcalendar差だけでは分割しない |

M098 尾道市の1 learner groupとM099 福山市の3 learner groupsは変更せず、regression matrixで固定した。

## Material answer-changing conditions retained

- M076: 旧分別の白色食品トレーは「もえるごみ」。紙パックとモバイルバッテリーは回収行動BOX。9種23分別地域のI031画像は、LED以外の割れていない一般電球として「びん類 その他」を採点する。
- M100: 上下地区では、缶・びん・小型家電、新聞・紙パック、段ボールが別の公式記号群になる。
- M120: 本土側ではモバイルバッテリーと使い捨てライターを「有害ごみ」、電球を「燃やせない」とする。島しょ部不足はHOLD理由にしない。
- M123: group Aの白色食品トレーは回収BOX action。group Bの教材画像はプラマーク付きの清浄なトレーとして「プラスチック類」を採点し、店頭回収可・マークなし・汚れありの例外をevidence層に保持する。
- M127: 美祢の割れていない電球は「リサイクルステーション」、割れたものは「その他のごみ」。美祢の使い捨てライターは「硬質プラスチック類」。美東・秋芳の両品目は「有害ごみ」。
- M136: 電球と使い捨てライターは「埋立・危険なごみ」。乾電池・蛍光管の地区別手順はfixed10のlearner variantを増やさない。
- M139: fixed10は市共通の主要区分で採点し、モバイルバッテリーだけを回収行動BOXとする。

Item-level official URL, locator, checked date, condition, preparation and answer-changing exception are stored in `lesson_variant_sources.csv` and `lesson_variant_item_scoring.csv`.

## Holds and priority

- M065 知夫村 and M086 新庄村 remain `DEFERRED`; no fixed-ten values were guessed.
- `data/master/07_implementation_priority.csv` separates `implementation_status`, `priority_status`, `company_link_status`, and the readiness snapshot for all 143 municipalities.
- The specified 36 municipalities plus 24 Chugoku candidates are `PRIORITY` (60 total). Because this repository contains no registered company-link primary evidence for those rows, all remain `PENDING_COMPANY_LINK`; this state does not affect readiness.

## Reproduction and checks

```bash
python scripts/build_lesson_ready_regional_batch.py
python scripts/validate_lesson_variants.py
python scripts/validate_implementation_priority.py
python scripts/red_team_lesson_variants.py
python scripts/red_team_implementation_priority.py
```
