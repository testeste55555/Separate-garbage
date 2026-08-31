#!/usr/bin/env python3
"""Idempotent M099 APP_READY entry point used by CI.

M099 was previously DEFERRED, so the repository had neither a Fukuyama official-host
registry row nor a completed canonical bundle for the municipality. This entry point
adds only M099 to the existing Batch 10 ordinary research union; it deliberately does
not re-migrate or rewrite already-completed municipalities' mapping rows.

I040 keeps one municipal-collection branch. Larger-quantity direct haul remains an
exception_destination, not the generic public drop-off category used for small
appliances, batteries and old paper.
"""
from __future__ import annotations

from pathlib import Path

import apply_app_readiness_m099 as build
from schema_v12 import (
    CATEGORY_FIELDS,
    CATEGORY_REVIEW_EVIDENCE_FIELDS,
    COVERAGE_FIELDS,
    MAPPING_FIELDS,
    MUNICIPALITY_FIELDS,
    QA_FIELDS,
    SOURCE_FIELDS,
    compute_qa,
    read_csv,
    sync_municipality_qa_status,
    write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/master/02_official_domain_registry.csv"
BATCH10 = ROOT / "data/research/batches/batch_10"
MID = build.MID


def ensure_fukuyama_registry() -> None:
    fields, rows = read_csv(REGISTRY)
    wanted = {
        "municipality_id": MID,
        "host": "www.city.fukuyama.hiroshima.jp",
        "authority_type": "MUNICIPAL_DOMAIN",
        "authority_name": "福山市",
        "verification_url": "https://www.city.fukuyama.hiroshima.jp/site/kankyo/314133.html",
        "verified_date": build.CHECKED,
        "notes": "M099 APP_READY promotion: Fukuyama municipal official source host",
    }
    rows = [
        row for row in rows
        if not (row.get("municipality_id") == MID and row.get("host") == wanted["host"])
    ]
    rows.append(wanted)
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("host", "")))
    write_csv(REGISTRY, fields, rows)


def safe_prepare_batch10():
    paths = {
        "municipalities": BATCH10 / "batch_10_municipalities.csv",
        "categories": BATCH10 / "batch_10_categories.csv",
        "sources": BATCH10 / "batch_10_sources.csv",
        "qa": BATCH10 / "batch_10_qa.csv",
        "mapping": BATCH10 / "batch_10_item_mapping.csv",
        "coverage": BATCH10 / "batch_10_item_coverage.csv",
        "review": BATCH10 / "batch_10_category_review_evidence.csv",
    }
    m_fields, municipalities = read_csv(paths["municipalities"])
    c_fields, categories = read_csv(paths["categories"])
    s_fields, sources = read_csv(paths["sources"])
    q_fields, qa = read_csv(paths["qa"])
    map_fields, mappings = read_csv(paths["mapping"])
    cov_fields, coverage = read_csv(paths["coverage"])
    rev_fields, review = read_csv(paths["review"])

    m099_qa = compute_qa(
        [dict(build.MUNICIPALITY)],
        [dict(row) for row in build.CATEGORIES],
        [dict(row) for row in build.SOURCES],
        [dict(row) for row in build.CATEGORY_REVIEW],
        [],
    )
    m099_municipality = sync_municipality_qa_status([dict(build.MUNICIPALITY)], m099_qa)[0]
    if len(m099_qa) != 1 or m099_qa[0].get("確認ステータス") != "QA_PASSED":
        raise ValueError(f"M099 ordinary research QA did not pass: {m099_qa}")

    municipalities = [r for r in municipalities if r.get("municipality_id") != MID] + [m099_municipality]
    categories = [r for r in categories if r.get("municipality_id") != MID] + [dict(r) for r in build.CATEGORIES]
    sources = [r for r in sources if r.get("municipality_id") != MID] + [dict(r) for r in build.SOURCES]
    qa = [r for r in qa if r.get("municipality_id") != MID] + m099_qa
    review = [r for r in review if r.get("municipality_id") != MID] + [dict(r) for r in build.CATEGORY_REVIEW]

    mappings = [r for r in mappings if r.get("municipality_id") != MID]
    coverage = [r for r in coverage if r.get("municipality_id") != MID] + [
        build.not_researched_coverage(f"I{i:03d}") for i in range(1, 41)
    ]

    write_csv(paths["municipalities"], m_fields or MUNICIPALITY_FIELDS, sorted(municipalities, key=lambda r: r["municipality_id"]))
    write_csv(paths["categories"], c_fields or CATEGORY_FIELDS, sorted(categories, key=lambda r: (r["municipality_id"], r["category_id"])))
    write_csv(paths["sources"], s_fields or SOURCE_FIELDS, sorted(sources, key=lambda r: (r["municipality_id"], r["source_id"])))
    write_csv(paths["qa"], q_fields or QA_FIELDS, sorted(qa, key=lambda r: r["municipality_id"]))
    write_csv(paths["mapping"], map_fields or MAPPING_FIELDS, mappings)
    write_csv(paths["coverage"], cov_fields or COVERAGE_FIELDS, sorted(coverage, key=lambda r: (r["municipality_id"], r["internal_item_id"])))
    write_csv(paths["review"], rev_fields or CATEGORY_REVIEW_EVIDENCE_FIELDS, sorted(review, key=lambda r: (r["municipality_id"], r["review_evidence_id"])))

    return (
        m099_municipality,
        [dict(r) for r in build.CATEGORIES],
        [dict(r) for r in build.SOURCES],
        m099_qa[0],
        [dict(r) for r in build.CATEGORY_REVIEW],
    )


def main() -> None:
    ensure_fukuyama_registry()
    pruning = build.RULES["I040"]
    if not pruning:
        raise ValueError("M099 I040 pruning review is empty")
    build.RULES["I040"] = [pruning[0]]
    build.prepare_batch10 = safe_prepare_batch10
    build.main()


if __name__ == "__main__":
    main()
