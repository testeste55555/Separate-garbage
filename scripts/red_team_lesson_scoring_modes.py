#!/usr/bin/env python3
"""Mutation RED TEAM for APP_READY / LESSON_READY_10 scoring boundaries."""

from __future__ import annotations

import copy
import sys

from validate_lesson_scoring_modes import (
    LESSON_READY,
    LESSON_SCOPE,
    PREFLIGHT_BLOCKERS,
    ROOT,
    build_context,
    read_csv,
    read_rows,
    validate,
    validate_preflight_blockers,
    validate_scope_review,
)


def mutate(rows: list[dict[str, str]], iid: str, branch: str, field: str, value: str) -> list[dict[str, str]]:
    candidate = copy.deepcopy(rows)
    for row in candidate:
        if row.get("internal_item_id") == iid and row.get("branch_order") == branch:
            row[field] = value
            return candidate
    raise AssertionError(f"row not found: {iid}/{branch}")


def mutate_blocker(rows: list[dict[str, str]], field: str, value: str) -> list[dict[str, str]]:
    candidate = copy.deepcopy(rows)
    candidate[0][field] = value
    return candidate


def main() -> int:
    baseline_errors = validate()
    if baseline_errors:
        print("LESSON_SCORING_RED_TEAM_BASELINE_FAILED")
        for error in baseline_errors:
            print(f"- {error}")
        return 1

    context = build_context()
    cases: list[tuple[str, dict[str, str], list[str], list[dict[str, str]]]] = []
    scopes = [row for row in read_rows(LESSON_SCOPE) if row.get("scoring_status") == LESSON_READY]
    for scope in scopes:
        municipality_id = scope["municipality_id"]
        fields, baseline = read_csv(ROOT / scope["review_source"])
        prefix = f"{municipality_id}: "
        cases.append(
            (
                prefix + "item removed",
                scope,
                fields,
                [row for row in baseline if row.get("internal_item_id") != "I031"],
            )
        )
        cases.append(
            (
                prefix + "condition branch removed",
                scope,
                fields,
                [
                    row
                    for row in baseline
                    if not (row.get("internal_item_id") == "I004" and row.get("branch_order") == "2")
                ],
            )
        )
        cases.append(
            (
                prefix + "second scoring branch enabled",
                scope,
                fields,
                mutate(baseline, "I001", "2", "scoring_branch", "TRUE"),
            )
        )
        cases.append(
            (
                prefix + "condition branch incomplete",
                scope,
                fields,
                mutate(baseline, "I033", "2", "branch_review_status", "INCOMPLETE"),
            )
        )
        cases.append(
            (
                prefix + "official item source removed",
                scope,
                fields,
                mutate(baseline, "I007", "1", "item_evidence_source_id", ""),
            )
        )
        cases.append(
            (
                prefix + "exception source removed",
                scope,
                fields,
                mutate(baseline, "I029", "1", "exception_evidence_source_id", ""),
            )
        )
        cases.append(
            (
                prefix + "wrong answer category injected",
                scope,
                fields,
                mutate(baseline, "I006", "1", "category_id", "C-INVALID-01"),
            )
        )
        cases.append(
            (
                prefix + "canonical wording drift",
                scope,
                fields,
                mutate(baseline, "I014", "1", "preparation", "そのまま出す"),
            )
        )
        promoted_scope = {**scope, "scoring_status": "APP_READY", "required_item_count": "40"}
        cases.append((prefix + "10-item review falsely promoted to APP_READY", promoted_scope, fields, baseline))

    escaped: list[str] = []
    for name, candidate_scope, fields, candidate_rows in cases:
        if not validate_scope_review(candidate_scope, fields, candidate_rows, context):
            escaped.append(name)
    blocker_fields, blockers = read_csv(PREFLIGHT_BLOCKERS)
    all_scope = read_rows(LESSON_SCOPE)
    image_mapping = read_rows(ROOT / "data/app/item_image_mapping_pilot_top8.csv")
    preflight_cases = [
        (
            "preflight: blocked municipality injected into scoring scope",
            blocker_fields,
            blockers,
            [*all_scope, {"municipality_id": "M106"}],
        ),
        (
            "preflight: EXCLUDED_NOTICE replaced by sorting category",
            blocker_fields,
            mutate_blocker(blockers, "category_id", "C-M106-12"),
            all_scope,
        ),
        (
            "preflight: direct official source removed",
            blocker_fields,
            mutate_blocker(blockers, "evidence_source_id", ""),
            all_scope,
        ),
        (
            "preflight: fixed image viability check made partial",
            blocker_fields,
            mutate_blocker(blockers, "checked_item_count", "9"),
            all_scope,
        ),
    ]
    for name, fields, candidate_rows, candidate_scope in preflight_cases:
        if not validate_preflight_blockers(fields, candidate_rows, context, candidate_scope, image_mapping):
            escaped.append(name)
    if escaped:
        print("LESSON_SCORING_RED_TEAM_FAILED")
        for name in escaped:
            print(f"- mutation escaped validator: {name}")
        return 1
    mutation_count = len(cases) + len(preflight_cases)
    print(f"LESSON_SCORING_RED_TEAM_PASSED mutations={mutation_count}/{mutation_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
