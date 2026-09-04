# Lesson V1.0.0 baseline

## Status

- Human Gate: PASSED
- Human Gate date: 2026-09-04
- Baseline implementation commit: `af343d93e708e20d9a1f0b1da9f0efc61694363a`
- Source branch at decision: `main`
- Release branch: `release/lesson-v1.0.0`

## Scope

This baseline fixes the classroom version used after PR #27.

- 11 active company routes are available through company selection.
- Six current company-deployed APP_READY municipalities use the formal 15-item online image practice set:
  - M009 大江町
  - M020 静岡市
  - M094 広島市
  - M098 尾道市
  - M099 福山市
  - M105 廿日市市
- The supplemental five items are:
  - I002 ペットボトルのキャップ
  - I003 ペットボトルのラベル
  - I027 乾電池
  - I018 生ごみ
  - I010 お菓子の袋
- Supplemental activation is all-or-nothing: 5/5 confirmed assets and a complete five-item scoring set are required before the learner UI expands from 10 to 15 questions.
- Existing `LESSON_READY_10` municipalities remain fixed to the core 10 items.
- M098 keeps one lesson variant group with no learner region selection.
- M099 keeps three audited regional lesson variants.
- Learner UI remains limited to image, sorting boxes, correctness feedback, and progression. Evidence details remain internal/teacher-side.

## Verification at Human Gate

The baseline was accepted after the following checks on `main`:

- merge-after PR #27 main CI completed successfully
- formal 15-item set validator passed
- supplemental-five scoring builder/validator passed
- guarded 15-item learner UI validator passed
- guarded 15-item mutation RED TEAM passed
- existing LESSON_READY_10 scoring regression passed
- regional variant validator / RED TEAM passed
- image asset validator passed with all 15 assets confirmed
- Teaching Display Layer regression passed
- Style Research gate passed
- GitHub Pages build and deployment succeeded
- human real-device review passed without an additional UI change request

## Change policy after V1

`lesson-v1.0.0` is the classroom baseline. Future work should be handled as a delta from this state.

- mechanical fixes and data maintenance may be generated and verified by AI
- new municipalities / companies are added on demand
- changes that alter learner-facing educational behavior, scoring interpretation, regional-rule interpretation, or classroom operation return to a Human Decision point
- RED TEAM should compress and prioritize issues before a Human Gate rather than increase human review load

## Rollback reference

If a later change must be compared against or rolled back to the accepted classroom implementation, use:

`af343d93e708e20d9a1f0b1da9f0efc61694363a`
