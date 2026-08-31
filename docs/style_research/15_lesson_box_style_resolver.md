# Lesson BOX style resolver

## Resolution contract

`app/app.js` resolves every displayed BOX at runtime in this order:

1. A teaching BOX backed by one current official category inherits the resolved `SORT_BUCKET` style.
2. A teaching BOX backed by multiple official categories inherits a style only when every resolved style triplet is identical.
3. A district-specific official style may be used when `style_district_scope` resolves it uniquely; otherwise the municipality-wide official style is considered.
4. Missing official style, a category-reference failure, conflicting official styles, or a learner-created BOX resolves to `FALLBACK`.
5. `SIMPLIFIED_ACTION` always resolves to `FALLBACK`, even if a category reference is accidentally supplied.

Runtime audit attributes are attached to the BOX:

- `data-style-provenance`: `OFFICIAL_CONFIRMED`, `OFFICIAL_DERIVED`, or `FALLBACK`
- `data-style-reason`: resolver decision reason
- `data-source-category-ids`: semicolon-separated source category IDs
- `data-box-kind`: official/scoring/action role

The optional `style_source_category_ids` field can represent one or more official categories. `style_district_scope` can identify a unique official district style. Standard teaching boxes explicitly snapshot their single official category; regional variant boxes remain blank until canonical category/style evidence exists.

## Runtime fallback safety surface

FALLBACK uses a non-white neutral surface, a strong dark border, the BOX name, and a diagonal pattern. `SIMPLIFIED_ACTION` also uses a dashed border and a distinct pattern. This prevents white/invisible BOX regression and prevents color from becoming the only cue.

This neutral surface is display assistance only. It is not an approved global palette and is never written to category or official style data. The proposed multi-color global fallback palette remains a Human Gate decision.

## Safety checks

```bash
node --check app/app.js
python scripts/validate_lesson_box_style_resolver.py
python scripts/red_team_lesson_box_style_resolver.py
python scripts/validate_style_research.py
python scripts/red_team_style_research.py
```

The resolver validator rejects persisted fallback color in the official projection, style claims on action boxes, white fallback surfaces, missing patterns/borders, and missing provenance/reason audit fields.
