#!/usr/bin/env python3
"""Mutation RED TEAM for M098/M099 lesson-variant boundaries."""

from __future__ import annotations

import copy
import sys

from validate_lesson_variants import records, validate, validate_records


def row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    return next(candidate for candidate in rows if candidate.get(key) == value)


def mutation(label: str, base: dict[str, list[dict[str, str]]], change) -> tuple[str, dict[str, list[dict[str, str]]]]:
    candidate = copy.deepcopy(base)
    change(candidate)
    return label, candidate


def main() -> int:
    baseline_errors = validate()
    if baseline_errors:
        print("LESSON_VARIANT_RED_TEAM_BASELINE_FAILED")
        for error in baseline_errors:
            print(f"- {error}")
        return 1

    base = records()
    cases = [
        mutation("M098 learner region selector forced", base, lambda d: row(d["variant_groups"], "lesson_variant_group_id", "LV-M098-01").update({"learner_selection_required": "TRUE"})),
        mutation("M098 Tachibana split into a fake learner group", base, lambda d: row(d["district_scopes"], "district_scope_id", "DS-M098-03").update({"lesson_variant_group_id": "LV-M098-02"})),
        mutation("M098 district scope removed", base, lambda d: d.update({"district_scopes": [r for r in d["district_scopes"] if r.get("district_scope_id") != "DS-M098-06"]})),
        mutation("M098 fixed-10 answer set split", base, lambda d: row(d["district_scopes"], "district_scope_id", "DS-M098-05").update({"fixed_10_answer_set_id": "M098-FIXED10-OTHER"})),
        mutation("M098 I031 teaching family diverged", base, lambda d: row(d["district_scopes"], "district_scope_id", "DS-M098-04").update({"i031_answer_family": "もやせないごみ系"})),
        mutation("M098 Innoshima I031 reverted to conflicting web locator", base, lambda d: row(d["district_scopes"], "district_scope_id", "DS-M098-05").update({"i031_evidence_source_id": "S-M098-04", "i031_evidence_url": "https://www.city.onomichi.hiroshima.jp/soshiki/18/3322.html", "i031_evidence_locator": "ページ内の電球案内"})),
        mutation("M099 Numakuma assigned to general", base, lambda d: row(d["district_scopes"], "district_scope_id", "DS-M099-03").update({"lesson_variant_group_id": "LV-M099-01"})),
        mutation("M099 general milk carton falsely scored as paper", base, lambda d: row([r for r in d["item_scoring"] if r.get("lesson_variant_group_id") == "LV-M099-01"], "internal_item_id", "I017").update({"teaching_box_id": "TB-M099-01-03"})),
        mutation("M099 Uchi/Numakuma milk carton removed from paper", base, lambda d: row([r for r in d["item_scoring"] if r.get("lesson_variant_group_id") == "LV-M099-02"], "internal_item_id", "I017").update({"teaching_box_id": "TB-M099-02-05"})),
        mutation("M099 Hashirijima newspaper falsely scored as paper", base, lambda d: row([r for r in d["item_scoring"] if r.get("lesson_variant_group_id") == "LV-M099-03"], "internal_item_id", "I013").update({"teaching_box_id": "TB-M099-01-03"})),
        mutation("M099 Hashirijima cardboard falsely scored as paper", base, lambda d: row([r for r in d["item_scoring"] if r.get("lesson_variant_group_id") == "LV-M099-03"], "internal_item_id", "I014").update({"teaching_box_id": "TB-M099-01-03"})),
        mutation("M099 Hashirijima milk carton falsely scored as paper", base, lambda d: row([r for r in d["item_scoring"] if r.get("lesson_variant_group_id") == "LV-M099-03"], "internal_item_id", "I017").update({"teaching_box_id": "TB-M099-01-03"})),
        mutation("fixed item removed from variant", base, lambda d: d.update({"item_scoring": [r for r in d["item_scoring"] if not (r.get("lesson_variant_group_id") == "LV-M098-01" and r.get("internal_item_id") == "I031")]})),
        mutation("duplicate scoring pair injected", base, lambda d: d["item_scoring"].append(copy.deepcopy(d["item_scoring"][0]))),
        mutation("official evidence removed", base, lambda d: row(d["item_scoring"], "lesson_variant_group_id", "LV-M098-01").update({"evidence_source_id": ""})),
        mutation("review marked incomplete", base, lambda d: row([r for r in d["item_scoring"] if r.get("lesson_variant_group_id") == "LV-M099-03"], "internal_item_id", "I033").update({"review_status": "INCOMPLETE"})),
        mutation("internal district exposed to learner", base, lambda d: row(d["district_scopes"], "district_scope_id", "DS-M098-01").update({"learner_visible": "TRUE"})),
        mutation("fixed-10-only box leaked into in-person mode", base, lambda d: row(d["teaching_boxes"], "teaching_box_id", "TB-M098-IP-01").update({"box_kind": "FIXED_10_SCORING"})),
        mutation("Hashirijima ferry route leaked into learner box", base, lambda d: row(d["teaching_boxes"], "teaching_box_id", "TB-M099-03-IP-07").update({"display_name": "フェリー持込施設"})),
    ]

    escaped = [label for label, candidate in cases if not validate_records(candidate)]
    if escaped:
        print("LESSON_VARIANT_RED_TEAM_FAILED")
        for label in escaped:
            print(f"- mutation escaped validator: {label}")
        return 1
    print(f"LESSON_VARIANT_RED_TEAM_PASSED mutations={len(cases)}/{len(cases)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
