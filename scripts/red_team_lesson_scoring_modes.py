#!/usr/bin/env python3
"""Mutation RED TEAM for APP_READY / LESSON_READY_10 scoring boundaries."""

from __future__ import annotations

import copy
import sys

from validate_lesson_scoring_modes import (
    LESSON_READY,
    LESSON_SCOPE,
    ROOT,
    build_context,
    read_csv,
    read_rows,
    validate,
    validate_scope_review,
)


def mutate(rows: list[dict[str, str]], iid: str, branch: str, field: str, value: str) -> list[dict[str, str]]:
    candidate = copy.deepcopy(rows)
    for row in candidate:
        if row.get("internal_item_id") == iid and row.get("branch_order") == branch:
            row[field] = value
            return candidate
    raise AssertionError(f"row not found: {iid}/{branch}")


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
    if escaped:
        print("LESSON_SCORING_RED_TEAM_FAILED")
        for name in escaped:
            print(f"- mutation escaped validator: {name}")
        return 1
    print(f"LESSON_SCORING_RED_TEAM_PASSED mutations={len(cases)}/{len(cases)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
