# APP_READINESS evidence policy v1.0

checked: 2026-08-20

## Purpose

APP readiness does not require every common item to be literally named in an official municipality document. The goal is to avoid unsupported guessing while still applying ordinary published sorting rules in the same way a resident would.

## Decision basis

1. `DIRECT_ITEM`
   - The municipality's official material names the item (or an accepted alias) and supports the destination/category directly.
   - This is preferred when available.

2. `OFFICIAL_RULE_DERIVED`
   - The item itself does not need to be literally named.
   - A CURRENT official municipality category definition/rule, together with the item's ordinary material/use characteristics, determines the destination.
   - Example: an official rule says plastic containers/packaging with the relevant characteristics belong in a plastics category; a lunch container meeting that rule can be mapped there without requiring the words 「弁当容器」 in the same source.

3. `GENERAL_RULE_DERIVED`
   - No item-specific wording and no already-established item mapping are available.
   - A stable ordinary classification rule and exactly one CURRENT official category concept determine the destination, and no municipality-specific contrary/special rule is found.
   - This is allowed for ordinary items; it is not a license to guess between multiple plausible categories.

4. `UNRESOLVED`
   - More than one plausible category remains, an official rule conflicts with the general rule, or a safe determination cannot be made.

## APP readiness guardrail

A supported category destination is not automatically `APP_READY`.

For items where preparation, size, collection route, legal route, retailer/manufacturer route, or hazard handling materially varies by municipality, condition review remains mandatory. Typical examples include batteries, power banks, fluorescent lamps, spray cans, lighters, blades, small appliances, bedding, regulated appliances, PCs, used cooking oil, and pruned branches.

Therefore:

- literal wording is **preferred but not mandatory**;
- unsupported municipality-specific guesses remain prohibited;
- applying an official rule is valid evidence;
- applying an unambiguous general rule is valid for category selection when no contrary rule exists;
- ambiguous or special-rule cases remain `UNRESOLVED` or condition-review-required;
- APP readiness still requires branch/condition completeness, not merely a destination category.

## Audit requirement

Every pair must retain the basis used (`DIRECT_ITEM`, `OFFICIAL_RULE_DERIVED`, `GENERAL_RULE_DERIVED`, or `UNRESOLVED`), the official category/source used where applicable, and whether condition review is still required.
