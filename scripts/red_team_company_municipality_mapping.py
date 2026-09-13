from __future__ import annotations

import csv
import tempfile
from pathlib import Path

from validate_company_municipality_mapping import MAPPING, MUNICIPALITIES, SCORING_READY, SCOPE, VARIANTS, read_rows, validate


def write_rows(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def mutate_and_expect_failure(name, mutator):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "company.csv"
        rows = read_rows(MAPPING)
        mutator(rows)
        write_rows(path, rows)
        errors = validate(path, MUNICIPALITIES, SCOPE, VARIANTS)
        if not errors:
            raise AssertionError(f"{name}: validator failed to reject mutation")
        print(f"PASS {name}: {errors[0]}")


def activate_non_ready(rows):
    """Activate one confirmed site whose municipality is outside the current scoring scope.

    The negative fixture follows the readiness data instead of hard-coding a municipality
    that may legitimately become LESSON_READY in a later batch.
    """
    scoring_ready = {
        row["municipality_id"].strip()
        for row in read_rows(SCOPE)
        if row.get("scoring_status", "").strip() in SCORING_READY
    }
    for row in rows:
        if (
            row.get("mapping_status", "").strip() == "CONFIRMED"
            and row.get("municipality_id", "").strip() not in scoring_ready
        ):
            row["lesson_variant_group_id"] = ""
            row["active"] = "TRUE"
            return
    raise AssertionError("no confirmed non-ready company site available for RED TEAM mutation")


def main():
    baseline = validate()
    if baseline:
        raise AssertionError("baseline invalid: " + "; ".join(baseline))

    tests = [
        ("unknown municipality", lambda rows: rows[0].__setitem__("municipality_id", "M999")),
        ("duplicate site id", lambda rows: rows[1].__setitem__("site_id", rows[0]["site_id"])),
        ("alias collision", lambda rows: rows[1].__setitem__("company_aliases", rows[0]["company_display_name"])),
        ("wrong variant municipality", lambda rows: rows[4].__setitem__("lesson_variant_group_id", "LV-M098-01")),
        ("activate non-ready municipality", activate_non_ready),
        ("active hold mapping", lambda rows: (rows[1].__setitem__("mapping_status", "HOLD"), rows[1].__setitem__("active", "TRUE"))),
        ("missing confirmed source", lambda rows: rows[1].__setitem__("source_url", "")),
    ]

    for name, mutator in tests:
        mutate_and_expect_failure(name, mutator)
    print(f"COMPANY_MAPPING_RED_TEAM: {len(tests)}/{len(tests)} PASS")


if __name__ == "__main__":
    main()
