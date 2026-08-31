# Classroom pilot APP_READY plan — 2026-08-31

## Target companies

Classroom pilot company selection is introduced independently from garbage-rule readiness. Company metadata resolves teacher selection to an existing municipality / lesson variant and never acts as garbage evidence.

## Target municipalities

- M094 広島市 — already APP_READY; regression only
- M098 尾道市 — LESSON_READY_10 -> APP_READY target
- M099 福山市 — LESSON_READY_10 -> APP_READY target
- M105 廿日市市 — LESSON_READY_10 -> APP_READY target
- M020 静岡市 — direct APP_READY target
- M009 大江町 — direct APP_READY target

## Safe staged activation

`data/app/company_municipality_mapping.csv` contains the 11 requested companies, but a site is teacher-selectable only when both conditions are true:

1. mapping `active=TRUE`
2. the mapped municipality is `APP_READY` in `lesson_mode_app_ready_scope.csv`

At initial introduction only the two companies mapped to already-APP_READY M094 are active. Other rows remain visible as preparation targets but are disabled by the UI until their 40-item APP_READY promotion is complete.

## Regional resolution

- M098 company sites resolve to `LV-M098-01`; learner region selection remains unnecessary.
- M099 新舶信鋼業 / 大信工業 resolve to `LV-M099-02` (内海町・沼隈町).
- M099 村上工業 resolves to `LV-M099-01` (一般地域).

Company/site metadata must not change canonical garbage categories or readiness decisions.

## APP_READY rule

No municipality is promoted by label change alone. Each target must meet the existing 40-item APP_READY evidence and branch-completeness standard used for M094/M095/M104. Unknown or category-level-only rows stay incomplete until supported by current official sources.
