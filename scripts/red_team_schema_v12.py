#!/usr/bin/env python3
"""Adversarial, batch-count-independent checks for the Schema v1.2.1 pipeline."""

from __future__ import annotations

import re
import tempfile
from collections import Counter
from pathlib import Path

from schema_v12 import (
    BATCH_MIGRATION_INPUT_SUFFIXES, BATCH_REQUIRED_SUFFIXES, COVERAGE_FIELDS, MAPPING_FIELDS,
    RESEARCH, ROOT, batch_dirs_for_migration, candidate_initial_mappings, completed_batch_dirs,
    read_csv, reconcile_mappings, write_csv,
)
from merge_research import merge_review_table
from validate_research import compare_canonical_union
from validation_v12 import READY_COVERAGE, validate_dataset


class Checks:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def add(self, name: str, passed: bool, detail: str = "") -> None:
        self.results.append((name, passed, detail))

    def finish(self) -> int:
        for name, passed, detail in self.results:
            print(f"{'PASS' if passed else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
        passed = sum(item[1] for item in self.results)
        print(f"RED_TEAM_SUMMARY={passed}/{len(self.results)}")
        if passed == len(self.results):
            print("SCHEMA_V12_RED_TEAM_PASSED")
            return 0
        print("SCHEMA_V12_RED_TEAM_FAILED")
        return 1


def paths_for(base: Path, prefix: str) -> dict[str, Path]:
    return {
        "municipality_path": base / f"{prefix}municipalities.csv",
        "category_path": base / f"{prefix}categories.csv",
        "source_path": base / f"{prefix}sources.csv",
        "qa_path": base / f"{prefix}qa.csv",
        "mapping_path": base / f"{prefix}item_mapping.csv",
        "coverage_path": base / f"{prefix}item_coverage.csv",
    }


def main() -> int:
    checks = Checks()
    pilot_paths = paths_for(RESEARCH / "pilot", "pilot_")
    canonical_paths = {
        "municipality_path": RESEARCH / "04_municipalities_research.csv",
        "category_path": RESEARCH / "02_categories_master.csv",
        "source_path": RESEARCH / "03_sources_master.csv",
        "qa_path": RESEARCH / "06_qa_log.csv",
        "mapping_path": RESEARCH / "05_item_mapping_master.csv",
        "coverage_path": RESEARCH / "07_item_mapping_coverage.csv",
    }
    datasets = [("PILOT", pilot_paths)]
    for batch in completed_batch_dirs():
        datasets.append((batch.name.upper(), paths_for(batch, batch.name + "_")))
    datasets.append(("CANONICAL", canonical_paths))

    structural_errors = {}
    for label, paths in datasets:
        errors, _, _ = validate_dataset(label=label, **paths)
        structural_errors[label] = errors
    checks.add("all discovered bundles pass structural validation", not any(structural_errors.values()),
               "; ".join(f"{label}={len(errors)}" for label, errors in structural_errors.items()))

    union_errors = compare_canonical_union()
    checks.add("canonical is a no-loss union of Pilot and completed batches", not union_errors,
               "; ".join(union_errors[:3]))

    completed_definition_ok = False
    with tempfile.TemporaryDirectory(prefix="redteam_batches_", dir=ROOT) as tmp:
        batch_root = Path(tmp)
        incomplete = batch_root / "batch_incomplete"
        complete = batch_root / "batch_complete"
        incomplete.mkdir()
        complete.mkdir()
        for suffix in BATCH_MIGRATION_INPUT_SUFFIXES:
            (incomplete / f"{incomplete.name}_{suffix}.csv").touch()
        for suffix in BATCH_REQUIRED_SUFFIXES:
            (complete / f"{complete.name}_{suffix}.csv").touch()
        migration_names = {path.name for path in batch_dirs_for_migration(batch_root)}
        completed_names = {path.name for path in completed_batch_dirs(batch_root)}
        completed_definition_ok = migration_names == {"batch_complete", "batch_incomplete"} and completed_names == {"batch_complete"}
    checks.add("completed-batch definition is centralized at six artifacts", completed_definition_ok)

    _, municipalities = read_csv(canonical_paths["municipality_path"])
    _, qa_rows = read_csv(canonical_paths["qa_path"])
    qa_status = {row["municipality_id"]: row["確認ステータス"] for row in qa_rows}
    checks.add("municipality QA status is a synchronized QA-log mirror", all(
        row["確認ステータス"] == qa_status.get(row["municipality_id"]) for row in municipalities
    ))
    _, items = read_csv(ROOT / "data" / "master" / "04_common_items_master.csv")
    _, coverage = read_csv(canonical_paths["coverage_path"])
    expected_pairs = {(m["municipality_id"], i["internal_item_id"]) for m in municipalities for i in items}
    actual_pairs = {(r["municipality_id"], r["internal_item_id"]) for r in coverage}
    checks.add("coverage is the dynamic municipality x common-item product", expected_pairs == actual_pairs,
               f"municipalities={len(municipalities)} items={len(items)} pairs={len(actual_pairs)}")

    check_states = Counter()
    evidence_ok = True
    for municipality in municipalities:
        for stem, url_field in [("search_service", "品目検索URL"), ("easy_japanese", "やさしい日本語URL"), ("multilingual", "多言語資料URL")]:
            status = municipality[f"{stem}_check_status"]
            check_states[status] += 1
            if status == "NOT_CHECKED" and (municipality[url_field] or municipality[f"{stem}_check_evidence"]):
                evidence_ok = False
            if status == "CHECKED_PRESENT" and municipality[url_field] not in municipality[f"{stem}_check_evidence"]:
                evidence_ok = False
    checks.add("optional resources distinguish checked and not checked", evidence_ok and "NOT_CHECKED" in check_states,
               str(dict(check_states)))

    _, categories = read_csv(canonical_paths["category_path"])
    explicit_role_ok = all(
        not (row["rule_status"] != "CURRENT" and row["ui_role"] != "HIDDEN")
        and not (row["ui_role"] == "SORT_BUCKET" and row["自治体収集外か"] == "TRUE")
        for row in categories
    )
    checks.add("explicit ui_role invariants hold without collection-channel inference", explicit_role_ok)

    active_scripts = ["validate_research.py", "validate_pilot.py", "validation_v12.py", "merge_research.py", "red_team_schema_v12.py"]
    script_text = "\n".join((ROOT / "scripts" / name).read_text(encoding="utf-8") for name in active_scripts)
    fixed_count = re.search(r"expected(?:_municipality_count)?\s*=\s*15\b|municipalit(?:y|ies).*!=\s*15\b", script_text)
    checks.add("active validation contains no 15-municipality expectation", fixed_count is None)
    checks.add("batch validation names its own mapping and coverage files",
               'f"{prefix}item_mapping.csv"' in (ROOT / "scripts" / "validate_research.py").read_text(encoding="utf-8"))
    checks.add("merge consumes mapping bundles instead of regenerating mappings",
               "candidate_initial_mappings" not in (ROOT / "scripts" / "merge_research.py").read_text(encoding="utf-8"))

    initial = candidate_initial_mappings(categories)
    preserved_ok = False
    reviewed_branches = []
    if initial:
        reviewed = dict(initial[0])
        reviewed.update({
            "mapping_status": "APP_READY", "evidence_scope": "ITEM_SPECIFIC", "branch_review_status": "COMPLETE",
            "reviewed_date": "2026-08-17", "reviewed_by": "RED_TEAM_FIXTURE", "自治体での品目表記": "品目別公式表記",
        })
        reviewed_alt = dict(reviewed)
        reviewed_alt.update({
            "mapping_id": reviewed["mapping_id"] + "-ALT", "branch_order": "2",
            "条件": reviewed["条件"] + "（別条件枝）", "mapping_status": "VERIFIED",
        })
        reviewed_branches = [reviewed, reviewed_alt]
        reconciled = reconcile_mappings(categories, reviewed_branches)
        matching = [row for row in reconciled if row["mapping_id"] in {reviewed["mapping_id"], reviewed_alt["mapping_id"]}]
        preserved_ok = len(matching) == 2 and len({row["条件"] for row in matching}) == 2
    merge_preserved = False
    if initial and reviewed_branches:
        with tempfile.TemporaryDirectory(prefix="redteam_merge_", dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            target, source = tmp_path / "target.csv", tmp_path / "source.csv"
            write_csv(target, MAPPING_FIELDS, reviewed_branches)
            write_csv(source, MAPPING_FIELDS, [initial[0]])
            merge_review_table(
                target, [source], ["mapping_id"],
                "mapping_status", {"VERIFIED", "APP_READY"},
            )
            _, after_merge = read_csv(target)
            merge_preserved = {row["mapping_id"] for row in after_merge} >= {
                reviewed_branches[0]["mapping_id"], reviewed_branches[1]["mapping_id"]
            }
    checks.add("mapping_id key preserves two reviewed branches to the same category", preserved_ok and merge_preserved)

    direct_edit_rejected = False
    with tempfile.TemporaryDirectory(prefix="schema_v12_redteam_") as tmp:
        tmp_path = Path(tmp)
        _, mappings = read_csv(pilot_paths["mapping_path"])
        _, pilot_coverage = read_csv(pilot_paths["coverage_path"])
        if mappings:
            mappings[0]["mapping_status"] = "APP_READY"
            pair = (mappings[0]["municipality_id"], mappings[0]["internal_item_id"])
            for row in pilot_coverage:
                if (row["municipality_id"], row["internal_item_id"]) == pair:
                    row["coverage_status"] = "APP_READY"
                    break
            mapping_path, coverage_path = tmp_path / "mapping.csv", tmp_path / "coverage.csv"
            write_csv(mapping_path, MAPPING_FIELDS, mappings)
            write_csv(coverage_path, COVERAGE_FIELDS, pilot_coverage)
            tampered = dict(pilot_paths)
            tampered.update({"mapping_path": mapping_path, "coverage_path": coverage_path})
            tamper_errors, _, _ = validate_dataset(label="TAMPERED", **tampered)
            direct_edit_rejected = any("APP_READY" in error for error in tamper_errors)
    checks.add("unsupported direct APP_READY edit is rejected", direct_edit_rejected)

    _, next_gate_errors, summary = validate_dataset(label="CANONICAL", gate_mode="next_batch", **canonical_paths)
    qa_required = summary.get("qa_required", 0)
    next_gate_consistent = (not next_gate_errors and qa_required == 0) or (bool(next_gate_errors) and qa_required > 0)
    checks.add("NEXT_BATCH_GATE is derived from structural QA without APP_READY", next_gate_consistent,
               f"qa_required={qa_required} gate_issues={len(next_gate_errors)}")

    _, gate_errors, summary = validate_dataset(label="CANONICAL", gate_mode="app_readiness", **canonical_paths)
    ready_count = summary.get("app_ready_municipalities", 0)
    gate_consistent = (not gate_errors and ready_count == len(municipalities)) or (bool(gate_errors) and ready_count < len(municipalities))
    checks.add("APP_READINESS_GATE reports PASS or HOLD from data, not batch number", gate_consistent,
               f"ready={ready_count}/{len(municipalities)} gate_issues={len(gate_errors)}")

    ready_rows = sum(row["coverage_status"] in READY_COVERAGE for row in coverage)
    checks.add("Gate readiness is derived from all 40 pairs", ready_rows == sum(
        1 for mid in {m["municipality_id"] for m in municipalities}
        for item in items if next(r for r in coverage if r["municipality_id"] == mid and r["internal_item_id"] == item["internal_item_id"])["coverage_status"] in READY_COVERAGE
    ), f"ready_pairs={ready_rows}/{len(coverage)}")

    return checks.finish()


if __name__ == "__main__":
    raise SystemExit(main())
