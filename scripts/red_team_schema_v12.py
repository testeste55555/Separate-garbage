#!/usr/bin/env python3
"""Adversarial, batch-count-independent checks for the Schema v1.2.3 pipeline."""

from __future__ import annotations

import re
import tempfile
from collections import Counter
from pathlib import Path

from schema_v12 import (
    BATCH_MIGRATION_INPUT_SUFFIXES, BATCH_REQUIRED_SUFFIXES, CATEGORY_FIELDS, CATEGORY_REVIEW_EVIDENCE_FIELDS,
    COVERAGE_FIELDS, MAPPING_FIELDS, ITEM_PATTERNS, MANUAL_MAPPING_STATUS, MUNICIPALITY_FIELDS,
    NEGATIVE_CONTEXT_FIELDS, QA_FIELDS, RESEARCH, ROOT,
    batch_dirs_for_migration,
    candidate_initial_mappings, completed_batch_dirs, compute_qa, counted_category_total,
    item_pattern_matches, latest_qa_evidence_date, read_csv, reconcile_mappings,
    sync_municipality_qa_status, write_csv,
)
from merge_research import merge_review_table
from validate_research import compare_canonical_union
from validation_v12 import (
    CATEGORY_DETAIL_FIELDS, READY_COVERAGE, is_placeholder_category_value, validate_dataset,
)


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
        "review_evidence_path": base / f"{prefix}category_review_evidence.csv",
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
        "review_evidence_path": RESEARCH / "08_category_review_evidence.csv",
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

    batch_02 = RESEARCH / "batches" / "batch_02"
    batch_02_targets = {"M012", "M014", "M015", "M016", "M017", "M018", "M019", "M020", "M021", "M022"}
    batch_02_ok = False
    batch_02_detail = "missing"
    if batch_02 in completed_batch_dirs():
        batch_02_paths = paths_for(batch_02, "batch_02_")
        _, batch_02_municipalities = read_csv(batch_02_paths["municipality_path"])
        _, batch_02_categories = read_csv(batch_02_paths["category_path"])
        _, batch_02_qa = read_csv(batch_02_paths["qa_path"])
        _, batch_02_evidence = read_csv(batch_02_paths["review_evidence_path"])
        actual_targets = {row["municipality_id"] for row in batch_02_municipalities}
        evidence_counts = Counter(row["municipality_id"] for row in batch_02_evidence)
        batch_02_ok = (
            actual_targets == batch_02_targets
            and all(row["確認ステータス"] == "QA_PASSED" for row in batch_02_qa)
            and all(row["category_count_check_status"] == "MANUAL_INDEX_REVIEW" for row in batch_02_municipalities)
            and all(
                row["reviewed_category_count"].isdigit()
                and int(row["reviewed_category_count"]) == counted_category_total(row["municipality_id"], batch_02_categories)
                and evidence_counts[row["municipality_id"]] >= 2
                for row in batch_02_municipalities
            )
        )
        batch_02_detail = (
            f"targets={len(actual_targets)}/10 qa_passed="
            f"{sum(row['確認ステータス'] == 'QA_PASSED' for row in batch_02_qa)}/10 "
            f"official_leaves={sum(counted_category_total(mid, batch_02_categories) for mid in actual_targets)}"
        )
    checks.add(
        "Batch 02 is the exact next MASTER set with complete manual-index evidence",
        batch_02_ok, batch_02_detail,
    )

    batch_02_authenticity_ok = False
    placeholder_tamper_rejected = False
    if batch_02 in completed_batch_dirs():
        batch_02_paths = paths_for(batch_02, "batch_02_")
        _, batch_02_categories = read_csv(batch_02_paths["category_path"])
        batch_02_authenticity_ok = len(batch_02_categories) == 151 and not any(
            is_placeholder_category_value(row.get(field, ""))
            for row in batch_02_categories
            for field in CATEGORY_DETAIL_FIELDS
        )
        with tempfile.TemporaryDirectory(prefix="redteam_category_placeholder_", dir=ROOT) as tmp:
            tampered_categories = [dict(row) for row in batch_02_categories]
            tampered_categories[0]["入れてはいけない物"] = "他の分別区分に該当する物"
            category_path = Path(tmp) / "categories.csv"
            write_csv(category_path, CATEGORY_FIELDS, tampered_categories)
            tampered_paths = dict(batch_02_paths)
            tampered_paths["category_path"] = category_path
            tampered_errors, _, _ = validate_dataset(label="PLACEHOLDER_CATEGORY", **tampered_paths)
            placeholder_tamper_rejected = any(
                "placeholder category detail" in error for error in tampered_errors
            )
    checks.add(
        "Batch 02 has 151 source-audited category rows and rejects filler text",
        batch_02_authenticity_ok and placeholder_tamper_rejected,
        f"authenticity_ok={batch_02_authenticity_ok} tamper_rejected={placeholder_tamper_rejected}",
    )

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
    checks.add("completed-batch definition is centralized at seven artifacts", completed_definition_ok)

    _, municipalities = read_csv(canonical_paths["municipality_path"])
    _, qa_rows = read_csv(canonical_paths["qa_path"])
    qa_status = {row["municipality_id"]: row["確認ステータス"] for row in qa_rows}
    checks.add("municipality QA status is a synchronized QA-log mirror", all(
        row["確認ステータス"] == qa_status.get(row["municipality_id"]) for row in municipalities
    ))

    _, pilot_municipalities = read_csv(pilot_paths["municipality_path"])
    _, pilot_categories = read_csv(pilot_paths["category_path"])
    _, pilot_sources = read_csv(pilot_paths["source_path"])
    _, pilot_qa = read_csv(pilot_paths["qa_path"])
    _, pilot_review_evidence = read_csv(pilot_paths["review_evidence_path"])
    manual_review_ok = False
    manual_count_mismatch_rejected = False
    if pilot_municipalities and pilot_sources:
        manual_rows = [dict(row) for row in pilot_municipalities]
        target = manual_rows[0]
        mid = target["municipality_id"]
        source = next(row for row in pilot_sources if row["municipality_id"] == mid)
        target.update({
            "official_category_count": "", "reviewed_category_count": str(counted_category_total(mid, pilot_categories)),
            "category_count_basis": "公式目次・見出しを全件手動照合", "category_count_verified": "TRUE",
            "category_count_check_status": "MANUAL_INDEX_REVIEW",
            "category_count_review_id": target["category_count_review_id"],
            "category_count_reviewed_date": "2026-08-17", "category_count_reviewed_by": "RED_TEAM_REVIEWER",
        })
        manual_qa = compute_qa(
            manual_rows, pilot_categories, pilot_sources, pilot_review_evidence, pilot_qa
        )
        sync_municipality_qa_status(manual_rows, manual_qa)
        with tempfile.TemporaryDirectory(prefix="redteam_manual_count_", dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            municipality_path, qa_path = tmp_path / "municipalities.csv", tmp_path / "qa.csv"
            write_csv(municipality_path, MUNICIPALITY_FIELDS, manual_rows)
            write_csv(qa_path, QA_FIELDS, manual_qa)
            manual_paths = dict(pilot_paths)
            manual_paths.update({"municipality_path": municipality_path, "qa_path": qa_path})
            manual_errors, _, _ = validate_dataset(label="MANUAL_INDEX", **manual_paths)
            manual_review_ok = not manual_errors

            bad_rows = [dict(row) for row in manual_rows]
            bad_target = next(row for row in bad_rows if row["municipality_id"] == mid)
            bad_target["reviewed_category_count"] = str(int(target["reviewed_category_count"]) + 1)
            bad_qa = compute_qa(
                bad_rows, pilot_categories, pilot_sources, pilot_review_evidence, manual_qa
            )
            sync_municipality_qa_status(bad_rows, bad_qa)
            write_csv(municipality_path, MUNICIPALITY_FIELDS, bad_rows)
            write_csv(qa_path, QA_FIELDS, bad_qa)
            bad_errors, _, _ = validate_dataset(label="BAD_MANUAL_INDEX", **manual_paths)
            manual_count_mismatch_rejected = any("manual reviewed category count mismatch" in error for error in bad_errors)
    checks.add(
        "MANUAL_INDEX_REVIEW permits an empty official total and verifies the reviewed count",
        manual_review_ok and manual_count_mismatch_rejected,
    )
    _, categories = read_csv(canonical_paths["category_path"])
    _, sources = read_csv(canonical_paths["source_path"])
    _, review_evidence = read_csv(canonical_paths["review_evidence_path"])
    _, items = read_csv(ROOT / "data" / "master" / "04_common_items_master.csv")

    expected_qa_dates = {
        row["municipality_id"]: latest_qa_evidence_date(row, categories, sources)
        for row in municipalities
    }
    qa_dates_dynamic = all(
        row.get("確認日") == expected_qa_dates.get(row["municipality_id"])
        for row in qa_rows
    ) and all(expected_qa_dates.values()) and 'CHECKED = "2026-08-17"' not in (
        ROOT / "scripts" / "schema_v12.py"
    ).read_text(encoding="utf-8")
    stale_qa_rejected = False
    with tempfile.TemporaryDirectory(prefix="redteam_qa_date_", dir=ROOT) as tmp:
        tampered_qa = [dict(row) for row in qa_rows]
        target_qa = next(row for row in tampered_qa if row["municipality_id"] == "M005")
        target_qa["確認日"] = "2026-08-17"
        qa_path = Path(tmp) / "qa.csv"
        write_csv(qa_path, QA_FIELDS, tampered_qa)
        stale_paths = dict(canonical_paths)
        stale_paths["qa_path"] = qa_path
        stale_errors, _, _ = validate_dataset(label="STALE_QA_DATE", **stale_paths)
        stale_qa_rejected = any("確認日" in error or "QA date" in error for error in stale_errors)
    checks.add(
        "QA dates derive from each municipality's newest persisted evidence date",
        qa_dates_dynamic and stale_qa_rejected,
        f"dates={sorted(set(expected_qa_dates.values()))} stale_rejected={stale_qa_rejected}",
    )

    multi_source_ok = all(
        len([row for row in review_evidence if row["municipality_id"] == mid]) >= 4
        for mid in ("M002", "M004")
    )
    foreign_source_rejected = False
    with tempfile.TemporaryDirectory(prefix="redteam_review_evidence_", dir=ROOT) as tmp:
        tampered_evidence = [dict(row) for row in review_evidence]
        target_evidence = next(
            row for row in tampered_evidence
            if row["municipality_id"] == "M002" and row["evidence_role"] == "SUPPLEMENTAL_INDEX"
        )
        target_evidence["source_id"] = "S-M001-01"
        evidence_path = Path(tmp) / "category_review_evidence.csv"
        write_csv(evidence_path, CATEGORY_REVIEW_EVIDENCE_FIELDS, tampered_evidence)
        evidence_paths = dict(canonical_paths)
        evidence_paths["review_evidence_path"] = evidence_path
        evidence_errors, _, _ = validate_dataset(label="FOREIGN_REVIEW_SOURCE", **evidence_paths)
        foreign_source_rejected = any("category review evidence source" in error for error in evidence_errors)
    checks.add(
        "category completeness reviews retain and validate multiple official sources",
        multi_source_ok and foreign_source_rejected,
        f"multi_source={multi_source_ok} foreign_source_rejected={foreign_source_rejected}",
    )

    reviewed_counts = {
        "M001": 14, "M002": 20, "M003": 13, "M004": 12, "M006": 16,
        "M007": 8, "M008": 9, "M009": 8, "M011": 14, "M013": 9, "M030": 10, "M094": 8,
    }
    municipality_by_id = {row["municipality_id"]: row for row in municipalities}
    category_by_id = {row["category_id"]: row for row in categories}
    required_corrections = {
        "C-M002-21": "鉄くず（衣川地域のみ）",
        "C-M003-14": "紙パック",
        "C-M005-15": "スプレー缶・ガスカートリッジ",
        "C-M005-16": "古着・布類",
        "C-M005-17": "紙パック",
        "C-M005-18": "使用済小型家電",
        "C-M005-19": "一升びん・ビールびん・リターナブルびん",
        "C-M005-20": "無色透明びん",
        "C-M005-21": "茶色びん",
        "C-M005-22": "その他色びん",
        "C-M006-17": "布類",
    }
    manual_review_regression_ok = all(
        municipality_by_id.get(mid, {}).get("category_count_check_status") == "MANUAL_INDEX_REVIEW"
        and municipality_by_id[mid].get("reviewed_category_count") == str(count)
        and counted_category_total(mid, categories) == count
        for mid, count in reviewed_counts.items()
    )
    correction_regression_ok = all(
        category_by_id.get(category_id, {}).get("自治体正式名称") == name
        for category_id, name in required_corrections.items()
    )
    m005_hazardous = category_by_id.get("C-M005-04", {})
    m005_split_ok = "スプレー缶" not in m005_hazardous.get("代表品目", "")
    checks.add(
        "12 manual index reviews and eleven official-heading corrections resist regression",
        manual_review_regression_ok and correction_regression_ok and m005_split_ok,
        f"manual_reviews={sum(mid in municipality_by_id for mid in reviewed_counts)}/{len(reviewed_counts)} "
        f"corrections={sum(category_by_id.get(cid, {}).get('自治体正式名称') == name for cid, name in required_corrections.items())}/{len(required_corrections)} "
        f"m005_spray_split={m005_split_ok}",
    )

    m005 = municipality_by_id.get("M005", {})
    bottle_parent = category_by_id.get("C-M005-10", {})
    bottle_children = [category_by_id.get(f"C-M005-{number}", {}) for number in range(19, 23)]
    m005_hierarchy_ok = (
        m005.get("category_count_check_status") == "OFFICIAL_COUNT_MATCHED"
        and m005.get("official_category_count") == "19"
        and counted_category_total("M005", categories) == 19
        and bottle_parent.get("ui_role") == "SORT_BUCKET"
        and all(
            child.get("parent_category_id") == "C-M005-10"
            and child.get("classification_level") == "SUBCATEGORY"
            and child.get("ui_role") == "REFERENCE_ONLY"
            for child in bottle_children
        )
        and sum(
            row.get("municipality_id") == "M005"
            and row.get("category_group") == "資源物（あきびん）"
            and row.get("ui_role") == "SORT_BUCKET"
            for row in categories
        ) == 1
    )
    checks.add(
        "Ishinomaki keeps 19 official leaves while projecting bottle subcategories to one UI bucket",
        m005_hierarchy_ok,
    )

    def fixture_category(category_id: str, positive_text: str = "") -> dict[str, str]:
        return {
            "municipality_id": "M-REDTEAM", "category_id": category_id,
            "自治体正式名称": positive_text, "代表品目": positive_text,
            "入れてはいけない物": "", "条件外の扱い": "", "出す前の処理": "", "注意事項": "",
            "表示順": "1", "rule_status": "CURRENT", "適用条件": "",
            "自治体収集外か": "FALSE", "effective_from": "", "effective_to": "",
            "source_id": "S-REDTEAM-01", "出典URL": "https://example.invalid/official",
            "出典ページ・該当箇所": "RED TEAM fixture", "確認日": "2026-08-18",
        }

    positive_failures = []
    negative_failures = []
    for item in items:
        item_id = item["internal_item_id"]
        sample = item["一般管理用名称"]
        positive = fixture_category(f"C-POS-{item_id}", sample)
        if not any(row["internal_item_id"] == item_id for row in candidate_initial_mappings([positive])):
            positive_failures.append(item_id)
        negative = fixture_category(f"C-NEG-{item_id}")
        for field in NEGATIVE_CONTEXT_FIELDS:
            negative[field] = sample
        if candidate_initial_mappings([negative]):
            negative_failures.append(item_id)
    checks.add(
        "all 40 common items require positive evidence and ignore negative/context fields",
        len(items) == len(ITEM_PATTERNS) == 40 and not positive_failures and not negative_failures,
        f"items={len(items)} patterns={len(ITEM_PATTERNS)} "
        f"positive_failures={positive_failures} negative_failures={negative_failures}",
    )

    collision_cases = {
        "I007": "白色以外のトレイ",
        "I021": "衣類乾燥機",
        "I030": "LED蛍光灯",
        "I034": "充電池を外せない小型家電",
        "I038": "パソコン周辺機器",
        "I039": "食用油ボトル",
    }
    collision_failures = [
        item_id for item_id, text in collision_cases.items()
        if item_pattern_matches(item_id, fixture_category(f"C-COLLISION-{item_id}", text))
    ]
    actual_initial = candidate_initial_mappings(categories)
    m001_i021 = {
        row["category_id"] for row in actual_initial
        if row["municipality_id"] == "M001" and row["internal_item_id"] == "I021"
    }
    _, canonical_mappings = read_csv(canonical_paths["mapping_path"])
    manual_mapping_keys = {
        (row["municipality_id"], row["internal_item_id"], row["category_id"])
        for row in canonical_mappings
        if row["mapping_status"] in MANUAL_MAPPING_STATUS
    }
    generated_mapping_keys = {
        (row["municipality_id"], row["internal_item_id"], row["category_id"])
        for row in actual_initial
    }
    stored_initial_keys = {
        (row["municipality_id"], row["internal_item_id"], row["category_id"])
        for row in canonical_mappings
        if row["mapping_status"] not in MANUAL_MAPPING_STATUS
    }
    initial_mapping_sync = stored_initial_keys == generated_mapping_keys - manual_mapping_keys
    stored_m001_i021 = {
        row["category_id"] for row in canonical_mappings
        if row["municipality_id"] == "M001" and row["internal_item_id"] == "I021"
    }
    checks.add(
        "known compound collisions do not generate false item candidates",
        not collision_failures and m001_i021 == stored_m001_i021 == {"C-M001-01"}
        and initial_mapping_sync,
        f"collision_failures={collision_failures} generated_M001_I021={sorted(m001_i021)} "
        f"stored_M001_I021={sorted(stored_m001_i021)} initial_mapping_sync={initial_mapping_sync}",
    )

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
            "item_evidence_source_id": reviewed["category_source_id"],
            "item_evidence_url": reviewed["category_source_url"],
            "item_evidence_locator": reviewed["category_source_locator"],
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

    separate_item_evidence_ok = False
    missing_coverage_locator_rejected = False
    _, pilot_mappings = read_csv(pilot_paths["mapping_path"])
    _, pilot_coverage = read_csv(pilot_paths["coverage_path"])
    evidence_fixture = None
    for mapping in pilot_mappings:
        alternate = next((source for source in pilot_sources if (
            source["municipality_id"] == mapping["municipality_id"]
            and source["source_id"] != mapping["category_source_id"]
        )), None)
        if alternate:
            evidence_fixture = (mapping, alternate)
            break
    if evidence_fixture:
        original_mapping, alternate = evidence_fixture
        mapping_rows = [dict(row) for row in pilot_mappings]
        mapping = next(row for row in mapping_rows if row["mapping_id"] == original_mapping["mapping_id"])
        mapping.update({
            "mapping_status": "VERIFIED", "evidence_scope": "ITEM_SPECIFIC",
            "branch_review_status": "INCOMPLETE", "reviewed_date": "2026-08-17",
            "reviewed_by": "RED_TEAM_REVIEWER", "item_evidence_source_id": alternate["source_id"],
            "item_evidence_url": alternate["公式URL"], "item_evidence_locator": "品目辞典の該当品目行",
        })
        coverage_rows = [dict(row) for row in pilot_coverage]
        pair = (mapping["municipality_id"], mapping["internal_item_id"])
        coverage_row = next(row for row in coverage_rows if (
            row["municipality_id"], row["internal_item_id"]
        ) == pair)
        coverage_row.update({
            "coverage_status": "VERIFIED", "evidence_scope": "ITEM_SPECIFIC",
            "branch_completeness_confirmed": "FALSE", "item_evidence_source_id": alternate["source_id"],
            "item_evidence_url": alternate["公式URL"], "item_evidence_locator": "品目辞典の該当品目行",
            "reviewed_date": "2026-08-17", "reviewed_by": "RED_TEAM_REVIEWER",
        })
        with tempfile.TemporaryDirectory(prefix="redteam_item_evidence_", dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            mapping_path, coverage_path = tmp_path / "mapping.csv", tmp_path / "coverage.csv"
            write_csv(mapping_path, MAPPING_FIELDS, mapping_rows)
            write_csv(coverage_path, COVERAGE_FIELDS, coverage_rows)
            evidence_paths = dict(pilot_paths)
            evidence_paths.update({"mapping_path": mapping_path, "coverage_path": coverage_path})
            evidence_errors, _, _ = validate_dataset(label="SEPARATE_ITEM_EVIDENCE", **evidence_paths)
            separate_item_evidence_ok = not evidence_errors and mapping["item_evidence_source_id"] != mapping["category_source_id"]

            coverage_row["item_evidence_locator"] = ""
            write_csv(coverage_path, COVERAGE_FIELDS, coverage_rows)
            missing_errors, _, _ = validate_dataset(label="MISSING_ITEM_LOCATOR", **evidence_paths)
            missing_coverage_locator_rejected = any(
                "lacks item-specific source/url/locator" in error for error in missing_errors
            )
    checks.add(
        "item evidence may differ from category evidence and coverage requires URL/locator",
        separate_item_evidence_ok and missing_coverage_locator_rejected,
    )

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
