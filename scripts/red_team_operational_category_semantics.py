#!/usr/bin/env python3
"""Adversarial check for Schema v1.2.4 resident-facing category semantics."""
from schema_v12 import RESEARCH, read_csv


def main() -> int:
    base = RESEARCH / "batches" / "batch_03"
    _, qa = read_csv(base / "batch_03_qa.csv")
    _, municipalities = read_csv(base / "batch_03_municipalities.csv")
    _, evidence = read_csv(base / "batch_03_category_review_evidence.csv")
    q = next(row for row in qa if row["municipality_id"] == "M028")
    m = next(row for row in municipalities if row["municipality_id"] == "M028")
    e = [row for row in evidence if row["municipality_id"] == "M028"]
    ok = (
        q["確認ステータス"] == "QA_PASSED"
        and q["危険有害"] == "FALSE"
        and q["収集しない物"] == "FALSE"
        and m["category_count_check_status"] == "MANUAL_INDEX_REVIEW"
        and m["reviewed_category_count"] == "5"
        and {row["evidence_role"] for row in e} >= {"PRIMARY_INDEX", "SUPPLEMENTAL_INDEX"}
    )
    print(f"{'PASS' if ok else 'FAIL'} resident-facing category QA does not invent hazard/excluded buckets")
    print(f"OPERATIONAL_CATEGORY_RED_TEAM_SUMMARY={1 if ok else 0}/1")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
