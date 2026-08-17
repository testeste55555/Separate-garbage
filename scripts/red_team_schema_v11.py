#!/usr/bin/env python3
"""Run the twelve Schema v1.1 RED TEAM checks required before the next batch."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from migrate_schema_v11 import CATEGORY_FIELDS, MUNICIPALITY_FIELDS, SOURCE_FIELDS, read_csv
from validation_v11 import (
    CORE_REQUIRED_CATEGORY_FIELDS,
    REFERENCE_CATEGORY_FIELDS,
    RESEARCH,
    ROOT,
    expected_ui_role,
    validate_dataset,
)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    checks: list[tuple[str, str]] = []
    _, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, qa = read_csv(RESEARCH / "06_qa_log.csv")
    _, items = read_csv(ROOT / "data" / "master" / "04_common_items_master.csv")

    # 1. Loss detection: legacy entity/row counts and every legacy column remain.
    legacy_category_fields = set(CATEGORY_FIELDS[:25])
    legacy_source_fields = set(SOURCE_FIELDS[:13])
    legacy_municipality_fields = set(MUNICIPALITY_FIELDS[:14])
    fields_ok = all(legacy_category_fields <= set(row) for row in categories) and all(legacy_source_fields <= set(row) for row in sources) and all(legacy_municipality_fields <= set(row) for row in municipalities)
    before = len(errors)
    require((len(municipalities), len(categories), len(sources), len(qa)) == (15, 194, 57, 15), "legacy row counts changed", errors)
    require(fields_ok, "legacy columns were lost", errors)
    checks.append(("1", "PASS" if len(errors) == before else "FAIL"))

    # 2. Current/future rules cannot share learner buckets.
    before = len(errors)
    require(all(row["rule_status"] == "CURRENT" or row["ui_role"] == "HIDDEN" for row in categories), "non-current rule is visible", errors)
    require(sum(row["rule_status"] == "PLANNED" for row in categories) == 1, "planned-rule migration count differs", errors)
    checks.append(("2", "PASS" if len(errors) == before else "FAIL"))

    # 3. REFERENCE fields are outside the CORE-required set.
    before = len(errors)
    require(not (set(CORE_REQUIRED_CATEGORY_FIELDS) & REFERENCE_CATEGORY_FIELDS), "REFERENCE remains CORE-required", errors)
    checks.append(("3", "PASS" if len(errors) == before else "FAIL"))

    # 4. ui_role alone deterministically projects current learner buckets.
    before = len(errors)
    require(all(row["ui_role"] == expected_ui_role(row) for row in categories), "ui_role is not deterministic", errors)
    require(all(any(row["municipality_id"] == mid and row["ui_role"] == "SORT_BUCKET" for row in categories) for mid in {row["municipality_id"] for row in municipalities}), "municipality lacks a learner bucket", errors)
    checks.append(("4", "PASS" if len(errors) == before else "FAIL"))

    # 5. Mapping schema retains multiple conditional branches.
    before = len(errors)
    pair_counts = Counter((row["municipality_id"], row["internal_item_id"]) for row in mappings)
    require(any(count > 1 for count in pair_counts.values()), "no conditional mapping branch exists", errors)
    require(all(row["条件"] and row["前処理"] and row["例外分別先"] for row in mappings), "mapping branch loses a condition", errors)
    checks.append(("5", "PASS" if len(errors) == before else "FAIL"))

    # 6. Every common item has an operational safety class and note.
    before = len(errors)
    safety = {"SAFE_REAL", "EMPTY_CLEAN_ONLY", "TEACHER_ONLY", "MOCK_ONLY"}
    require(30 <= len(items) <= 50, "common item count outside 30-50", errors)
    require(all(row["handling_safety"] in safety and row["safety_note"] for row in items), "common item safety is incomplete", errors)
    checks.append(("6", "PASS" if len(errors) == before else "FAIL"))

    # 7. Reuse the full relational and mechanical QA validator.
    before = len(errors)
    validation_errors, _ = validate_dataset(
        label="RED_TEAM",
        municipality_path=RESEARCH / "04_municipalities_research.csv",
        category_path=RESEARCH / "02_categories_master.csv",
        source_path=RESEARCH / "03_sources_master.csv",
        qa_path=RESEARCH / "06_qa_log.csv",
        expected_municipality_count=15,
    )
    errors.extend(f"relational validation: {message}" for message in validation_errors)
    checks.append(("7", "PASS" if len(errors) == before else "FAIL"))

    # 8 and 9 are hash-tested by the documented command sequence; verify the
    # immutable source split and unique merged keys here as a second guard.
    before = len(errors)
    pilot_ids = {row["municipality_id"] for row in read_csv(RESEARCH / "pilot" / "pilot_municipalities.csv")[1]}
    batch_ids = {row["municipality_id"] for row in read_csv(RESEARCH / "batches" / "batch_01" / "batch_01_municipalities.csv")[1]}
    require(pilot_ids.isdisjoint(batch_ids) and pilot_ids | batch_ids == {row["municipality_id"] for row in municipalities}, "Pilot/Batch source partition is unstable", errors)
    checks.append(("8", "PASS" if len(errors) == before else "FAIL"))
    before = len(errors)
    require(len({(row["municipality_id"], row["category_id"]) for row in categories}) == len(categories), "merge produced duplicate categories", errors)
    require(len({(row["municipality_id"], row["source_id"]) for row in sources}) == len(sources), "merge produced duplicate sources", errors)
    checks.append(("9", "PASS" if len(errors) == before else "FAIL"))

    # 10. Validators must contain no municipality-specific ID branches.
    before = len(errors)
    validator_text = "\n".join((ROOT / "scripts" / name).read_text(encoding="utf-8") for name in ["validation_v11.py", "validate_pilot.py", "validate_research.py"])
    require(re.search(r"\bM\d{3}\b", validator_text) is None, "municipality-specific hardcode remains in validator", errors)
    checks.append(("10", "PASS" if len(errors) == before else "FAIL"))

    # 11. Municipal domains, authorities, and linked external services differ.
    before = len(errors)
    basis = Counter(row["official_basis"] for row in sources)
    linked = [row for row in sources if row["official_basis"] == "MUNICIPAL_LINKED_SERVICE"]
    require(basis["MUNICIPAL_DOMAIN"] > 0 and basis["INTERMUNICIPAL_AUTHORITY_DOMAIN"] > 0 and linked, "official-source classes are not distinguished", errors)
    require(all(row["official_linking_url"].startswith("https://") for row in linked), "linked service lacks municipal linking URL", errors)
    checks.append(("11", "PASS" if len(errors) == before else "FAIL"))

    # 12. README exposes the exact successful reproduction commands.
    before = len(errors)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    commands = [
        "python3 scripts/validate_pilot.py",
        "python3 scripts/validate_research.py --batch batch_01",
        "python3 scripts/merge_research.py",
        "python3 scripts/validate_research.py",
        "python3 scripts/red_team_schema_v11.py",
    ]
    require(all(command in readme for command in commands), "README reproduction command is missing", errors)
    checks.append(("12", "PASS" if len(errors) == before else "FAIL"))

    print("SCHEMA_V11_RED_TEAM_" + ("PASSED" if not errors else "FAILED"))
    print("checks=" + ",".join(f"{number}:{status}" for number, status in checks))
    print(f"rows=municipalities:{len(municipalities)},categories:{len(categories)},sources:{len(sources)},items:{len(items)},mappings:{len(mappings)},qa:{len(qa)}")
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
