# APP readiness decision-basis audit

checked: 2026-08-20

Literal item wording is preferred but is not required when an official rule or an unambiguous general rule determines the category. This report is audit-only and creates no APP_READY claim.

- pairs: 5280
- DIRECT_ITEM: 324
- OFFICIAL_RULE_DERIVED: 896
- GENERAL_RULE_DERIVED: 399
- UNRESOLVED: 3661

## Decision status

- CATEGORY_SUPPORTED: 563
- CATEGORY_SUPPORTED_CONDITION_REVIEW_REQUIRED: 1056
- UNRESOLVED: 3661

## Policy guardrail

GENERAL_RULE_DERIVED only resolves a destination when one allowed general category concept matches exactly one CURRENT official leaf. Hazard/size/route-sensitive items still require explicit condition review before APP_READY.
