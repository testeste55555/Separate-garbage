#!/usr/bin/env python3
"""Validate the additive Style Research layer and NEXT_STYLE_BATCH_GATE."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
TARGET_ORDER = [
    (1, "A", "M094", "広島市"),
    (2, "A", "M099", "福山市"),
    (3, "A", "M104", "東広島市"),
    (4, "A", "M098", "尾道市"),
    (5, "A", "M095", "呉市"),
    (6, "B", "M097", "三原市"),
    (7, "B", "M105", "廿日市市"),
    (8, "B", "M106", "安芸高田市"),
    (9, "B", "M109", "海田町"),
    (10, "B", "M107", "江田島市"),
]

COLOR_STATUSES = {"OFFICIAL_CONFIRMED", "OFFICIAL_DERIVED", "FALLBACK", "NOT_CONFIRMED"}
EVIDENCE_ROLES = {"DESIGNATED_BAG", "COLLECTION_CONTAINER", "STATION_SIGN", "OFFICIAL_CALENDAR", "OFFICIAL_POSTER_GUIDE"}
SEMANTIC_FITS = {"CATEGORY_DISCRIMINATOR", "SHARED_COLLECTION_GROUP", "MULTI_METHOD_CATEGORY", "NO_SEMANTIC_COLOR", "CONFLICTING_EVIDENCE", "DECORATIVE_ONLY"}
UI_SELECTIONS = {"PRIMARY", "SUPPORTING", "REJECTED", "NOT_APPLICABLE"}
HEX_RE = re.compile(r"^#[0-9A-F]{6}$")
GENERIC_BASIS = {
    "公式資料の色", "資料の色", "自治体の色", "一般的な色", "標準色", "推定色",
}


class StyleValidationError(AssertionError):
    pass


def fail(message: str) -> None:
    raise StyleValidationError(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"missing file: {path.relative_to(path.parents[2]) if len(path.parents) > 2 else path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def require_columns(rows: list[dict[str, str]], required: set[str], label: str) -> None:
    if not rows:
        fail(f"{label}: no rows")
    missing = required.difference(rows[0].keys())
    if missing:
        fail(f"{label}: missing columns {sorted(missing)}")


def require_unique(rows: list[dict[str, str]], field: str, label: str) -> None:
    values = [row[field].strip() for row in rows]
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    if "" in values:
        fail(f"{label}: blank {field}")
    if duplicates:
        fail(f"{label}: duplicate {field}: {duplicates[:10]}")


def valid_iso_date(value: str) -> bool:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed <= date.today()


def relative_luminance(hex_color: str) -> float:
    values = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in values]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(color_a: str, color_b: str) -> float:
    a = relative_luminance(color_a)
    b = relative_luminance(color_b)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)


def official_hostname(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host.endswith(".lg.jp") or host in {
        "www.akitakata.jp",
        "akitakata.jp",
        "www.city.fukuyama.hiroshima.jp",
        "www.city.onomichi.hiroshima.jp",
        "www.city.mihara.hiroshima.jp",
        "www.city.hatsukaichi.hiroshima.jp",
        "www.city.etajima.hiroshima.jp",
    }


def normalized_rows(rows: list[dict[str, str]]) -> list[tuple[tuple[str, str], ...]]:
    return sorted(tuple(sorted((key, value.strip()) for key, value in row.items())) for row in rows)


def validate(root: Path = ROOT, *, quiet: bool = False) -> dict[str, int]:
    style_dir = root / "data/style_research"
    targets = read_csv(style_dir / "03_top10_targets.csv")
    stage_a = read_csv(style_dir / "04_stage_a_style_observations.csv")
    stage_b = read_csv(style_dir / "07_stage_b_style_observations.csv")
    observations = read_csv(style_dir / "08_style_color_observations.csv")
    projections = read_csv(style_dir / "08_style_ui_projection.csv")
    sources = read_csv(style_dir / "09_style_sources.csv")
    municipalities = read_csv(root / "data/master/01_municipalities_master.csv")
    deferred = read_csv(root / "data/master/05_deferred_municipalities.csv")
    categories = read_csv(root / "data/research/02_categories_master.csv")

    require_columns(targets, {"rank", "stage", "municipality_id", "municipality_name", "canonical_status", "style_research_status", "district_scope_required", "current_sort_bucket_count", "source_ids", "note"}, "targets")
    require_columns(observations, {"style_id", "rank", "stage", "municipality_id", "district_scope", "category_id", "自治体正式名称", "evidence_role", "official_color_label", "display_color", "color_status", "color_basis", "semantic_fit", "ui_selection", "source_id", "source_url", "source_locator", "checked_date", "reviewer", "note"}, "observations")
    require_columns(projections, {"projection_id", "rank", "municipality_id", "district_scope", "category_id", "自治体正式名称", "display_color", "border_color", "text_color", "color_status", "color_basis", "selected_style_id", "accessibility_label_required", "icon_status", "checked_date", "reviewer", "note"}, "projections")
    require_columns(sources, {"source_id", "municipality_id", "district_scope", "source_title", "source_type", "source_url", "source_locator", "evidence_roles", "priority", "currentness", "official_verified", "official_basis", "checked_date", "note"}, "sources")

    require_unique(targets, "municipality_id", "targets")
    require_unique(observations, "style_id", "observations")
    require_unique(projections, "projection_id", "projections")
    require_unique(sources, "source_id", "sources")

    actual_order = [(int(row["rank"]), row["stage"].strip(), row["municipality_id"].strip(), row["municipality_name"].strip()) for row in targets]
    if actual_order != TARGET_ORDER:
        fail(f"targets: fixed ranking or stage changed: {actual_order}")

    master_names = {row["municipality_id"].strip(): row["市町村"].strip() for row in municipalities}
    deferred_ids = {row["municipality_id"].strip() for row in deferred}
    expected_deferred = {"M098", "M099"}
    if not expected_deferred.issubset(deferred_ids):
        fail("targets: M098/M099 must remain canonical DEFERRED")

    target_by_id = {row["municipality_id"].strip(): row for row in targets}
    active_ids: set[str] = set()
    for row in targets:
        mid = row["municipality_id"].strip()
        if master_names.get(mid) != row["municipality_name"].strip():
            fail(f"targets: master name mismatch for {mid}")
        status = row["canonical_status"].strip()
        if status == "ACTIVE":
            active_ids.add(mid)
            if row["style_research_status"].strip() != "COMPLETED":
                fail(f"targets: active target not COMPLETED: {mid}")
            if row["district_scope_required"].strip() != "FALSE":
                fail(f"targets: unexpected district scope flag for {mid}")
        elif status == "DEFERRED":
            if mid not in expected_deferred:
                fail(f"targets: unexpected deferred target {mid}")
            if row["style_research_status"].strip() != "RESEARCHED_CANONICAL_DEFERRED":
                fail(f"targets: deferred target lacks explicit research status: {mid}")
            if row["district_scope_required"].strip() != "TRUE":
                fail(f"targets: deferred regional target must require scope: {mid}")
            if row["current_sort_bucket_count"].strip() != "0":
                fail(f"targets: deferred target must not invent category count: {mid}")
        else:
            fail(f"targets: invalid canonical_status {status}")
        if not row["source_ids"].strip() or not row["note"].strip():
            fail(f"targets: missing source registry or decision note for {mid}")

    category_index = {(row["municipality_id"].strip(), row["category_id"].strip()): row for row in categories}
    expected_categories = {
        (row["municipality_id"].strip(), row["category_id"].strip()): row
        for row in categories
        if row["municipality_id"].strip() in active_ids
        and row["ui_role"].strip() == "SORT_BUCKET"
        and row["rule_status"].strip() == "CURRENT"
    }
    expected_counts = Counter(mid for mid, _ in expected_categories)
    for mid in active_ids:
        saved = int(target_by_id[mid]["current_sort_bucket_count"])
        if saved != expected_counts[mid]:
            fail(f"targets: CURRENT SORT_BUCKET count mismatch for {mid}: saved={saved} canonical={expected_counts[mid]}")

    source_index = {row["source_id"].strip(): row for row in sources}
    sources_by_municipality: dict[str, set[str]] = defaultdict(set)
    scopes_by_municipality: dict[str, set[str]] = defaultdict(set)
    for row in sources:
        sid = row["source_id"].strip()
        mid = row["municipality_id"].strip()
        sources_by_municipality[mid].add(sid)
        scopes_by_municipality[mid].add(row["district_scope"].strip())
        if mid not in target_by_id:
            fail(f"sources: source for non-target municipality: {sid}")
        if not row["district_scope"].strip() or not row["source_title"].strip() or not row["source_locator"].strip():
            fail(f"sources: blank scope/title/locator: {sid}")
        if row["official_verified"].strip() != "TRUE" or row["official_basis"].strip() != "MUNICIPAL_DOMAIN":
            fail(f"sources: source is not verified municipal official: {sid}")
        url = row["source_url"].strip()
        if not url.startswith("https://") or not official_hostname(url):
            fail(f"sources: non-official or insecure URL: {sid} {url}")
        if not valid_iso_date(row["checked_date"].strip()):
            fail(f"sources: invalid checked_date: {sid}")
        roles = {value for value in row["evidence_roles"].split(";") if value}
        allowed_source_roles = EVIDENCE_ROLES | {"OFFICIAL_WEB_INDEX"}
        if not roles or not roles.issubset(allowed_source_roles):
            fail(f"sources: invalid evidence_roles for {sid}: {roles}")
        try:
            priority = int(row["priority"])
        except ValueError:
            fail(f"sources: priority must be integer: {sid}")
        if priority not in {1, 2, 3, 4}:
            fail(f"sources: invalid priority: {sid}={priority}")

    for mid, target in target_by_id.items():
        listed = {value for value in target["source_ids"].split(";") if value}
        if listed != sources_by_municipality[mid]:
            fail(f"targets: source_ids registry mismatch for {mid}")
    if not {"ONOMICHI", "MUKAISHIMA", "MITSUGI", "INNOSHIMA", "SETODA"}.issubset(scopes_by_municipality["M098"]):
        fail("sources: Onomichi must retain five regional scopes")
    if not {"CITY_GENERAL", "UCHIUMI", "NUMAKUMA"}.issubset(scopes_by_municipality["M099"]):
        fail("sources: Fukuyama must retain city/Utumi/Numakuma scopes")

    if normalized_rows(stage_a) != normalized_rows([row for row in observations if row["stage"].strip() == "A"]):
        fail("stage files: Stage A is not an exact subset of integrated observations")
    if normalized_rows(stage_b) != normalized_rows([row for row in observations if row["stage"].strip() == "B"]):
        fail("stage files: Stage B is not an exact subset of integrated observations")

    primary_by_key: Counter[tuple[str, str, str]] = Counter()
    observation_index = {row["style_id"].strip(): row for row in observations}
    for row in observations:
        style_id = row["style_id"].strip()
        mid = row["municipality_id"].strip()
        scope = row["district_scope"].strip()
        category_id = row["category_id"].strip()
        if mid in expected_deferred:
            fail(f"observations: deferred target may not invent category style: {style_id}")
        if mid not in active_ids or scope != "MUNICIPALITY_WIDE":
            fail(f"observations: invalid target/scope for active style: {style_id}")
        canonical = category_index.get((mid, category_id))
        if canonical is None:
            fail(f"observations: unknown category reference: {style_id} {category_id}")
        if canonical["ui_role"].strip() != "SORT_BUCKET" or canonical["rule_status"].strip() != "CURRENT":
            fail(f"observations: non-SORT_BUCKET/REFERENCE category mixed into style: {style_id}")
        if canonical["自治体正式名称"].strip() != row["自治体正式名称"].strip():
            fail(f"observations: canonical name snapshot mismatch: {style_id}")
        if row["stage"].strip() != target_by_id[mid]["stage"].strip() or int(row["rank"]) != int(target_by_id[mid]["rank"]):
            fail(f"observations: rank/stage mismatch: {style_id}")
        if row["evidence_role"].strip() not in EVIDENCE_ROLES:
            fail(f"observations: invalid evidence_role: {style_id}")
        status = row["color_status"].strip()
        if status not in COLOR_STATUSES:
            fail(f"observations: invalid color_status: {style_id}")
        semantic_fit = row["semantic_fit"].strip()
        selection = row["ui_selection"].strip()
        if semantic_fit not in SEMANTIC_FITS or selection not in UI_SELECTIONS:
            fail(f"observations: invalid semantic_fit/ui_selection: {style_id}")
        basis = row["color_basis"].strip()
        if not basis or basis in GENERIC_BASIS:
            fail(f"observations: generic or blank color_basis: {style_id}")
        source = source_index.get(row["source_id"].strip())
        if source is None:
            fail(f"observations: unknown source_id: {style_id}")
        if source["municipality_id"].strip() != mid or source["source_url"].strip() != row["source_url"].strip():
            fail(f"observations: source municipality/URL mismatch: {style_id}")
        if not row["source_locator"].strip() or not row["reviewer"].strip() or not valid_iso_date(row["checked_date"].strip()):
            fail(f"observations: missing locator/reviewer/date: {style_id}")
        display = row["display_color"].strip()
        note = row["note"].strip()
        if status == "OFFICIAL_DERIVED":
            if not HEX_RE.fullmatch(display) or "近似" not in note:
                fail(f"observations: derived color lacks valid HEX or approximation disclaimer: {style_id}")
        elif status == "OFFICIAL_CONFIRMED":
            if not row["official_color_label"].strip() and not display:
                fail(f"observations: confirmed color lacks official label/value: {style_id}")
            if display and (not HEX_RE.fullmatch(display) or ("RGB" not in basis and "HEX" not in basis)):
                fail(f"observations: confirmed HEX was not explicitly published: {style_id}")
        elif status == "NOT_CONFIRMED":
            if display:
                fail(f"observations: NOT_CONFIRMED must not carry a display color: {style_id}")
        elif status == "FALLBACK":
            if row["source_id"].strip() or row["source_url"].strip() or row["source_locator"].strip():
                fail(f"observations: FALLBACK must not pretend to be official evidence: {style_id}")
        if selection == "PRIMARY":
            primary_by_key[(mid, scope, category_id)] += 1
            if semantic_fit != "CATEGORY_DISCRIMINATOR" or status not in {"OFFICIAL_CONFIRMED", "OFFICIAL_DERIVED"}:
                fail(f"observations: PRIMARY must be official category discriminator: {style_id}")
        if semantic_fit in {"SHARED_COLLECTION_GROUP", "MULTI_METHOD_CATEGORY", "NO_SEMANTIC_COLOR", "CONFLICTING_EVIDENCE", "DECORATIVE_ONLY"} and selection == "PRIMARY":
            fail(f"observations: non-discriminating/decorative color selected as PRIMARY: {style_id}")

    duplicates = [key for key, count in primary_by_key.items() if count > 1]
    if duplicates:
        fail(f"observations: multiple PRIMARY observations for one category/scope: {duplicates[:5]}")

    projection_keys = [(row["municipality_id"].strip(), row["category_id"].strip()) for row in projections]
    if len(projection_keys) != len(set(projection_keys)):
        fail("projections: duplicate municipality/category row")
    if set(projection_keys) != set(expected_categories):
        missing = sorted(set(expected_categories) - set(projection_keys))
        extra = sorted(set(projection_keys) - set(expected_categories))
        fail(f"projections: canonical CURRENT SORT_BUCKET coverage mismatch missing={missing[:5]} extra={extra[:5]}")

    for row in projections:
        projection_id = row["projection_id"].strip()
        mid = row["municipality_id"].strip()
        category_id = row["category_id"].strip()
        canonical = expected_categories[(mid, category_id)]
        if row["district_scope"].strip() != "MUNICIPALITY_WIDE":
            fail(f"projections: invalid active scope: {projection_id}")
        if canonical["自治体正式名称"].strip() != row["自治体正式名称"].strip():
            fail(f"projections: official category name mismatch: {projection_id}")
        if int(row["rank"]) != int(target_by_id[mid]["rank"]):
            fail(f"projections: rank mismatch: {projection_id}")
        if row["accessibility_label_required"].strip() != "TRUE":
            fail(f"projections: color may not be the only information channel: {projection_id}")
        if row["icon_status"].strip() != "NOT_RESEARCHED_AS_OFFICIAL":
            fail(f"projections: unofficial icon state mixed into official research: {projection_id}")
        if not row["reviewer"].strip() or not valid_iso_date(row["checked_date"].strip()):
            fail(f"projections: missing reviewer/date: {projection_id}")
        status = row["color_status"].strip()
        display = row["display_color"].strip()
        selected_id = row["selected_style_id"].strip()
        if status == "NOT_CONFIRMED":
            if display or row["border_color"].strip() or row["text_color"].strip() or selected_id:
                fail(f"projections: NOT_CONFIRMED must remain blank and unselected: {projection_id}")
        elif status in {"OFFICIAL_CONFIRMED", "OFFICIAL_DERIVED"}:
            if not HEX_RE.fullmatch(display) or not HEX_RE.fullmatch(row["border_color"].strip()) or not HEX_RE.fullmatch(row["text_color"].strip()):
                fail(f"projections: official UI projection requires valid color triplet: {projection_id}")
            selected = observation_index.get(selected_id)
            if selected is None:
                fail(f"projections: missing selected observation: {projection_id}")
            if selected["municipality_id"].strip() != mid or selected["category_id"].strip() != category_id or selected["ui_selection"].strip() != "PRIMARY":
                fail(f"projections: selected observation identity mismatch: {projection_id}")
            if selected["display_color"].strip() != display or selected["color_status"].strip() != status:
                fail(f"projections: selected observation value/status mismatch: {projection_id}")
            if row["border_color"].strip() == display:
                fail(f"projections: border must remain visible independently: {projection_id}")
            if contrast_ratio(display, row["text_color"].strip()) < 4.5:
                fail(f"projections: text contrast below WCAG AA: {projection_id}")
            if status == "OFFICIAL_DERIVED" and "近似" not in row["note"]:
                fail(f"projections: derived disclaimer missing: {projection_id}")
        elif status == "FALLBACK":
            if selected_id:
                fail(f"projections: FALLBACK may not select official observation: {projection_id}")
        else:
            fail(f"projections: invalid color_status: {projection_id}")

    metrics = {
        "targets": len(targets),
        "active_municipalities": len(active_ids),
        "canonical_deferred_municipalities": len(expected_deferred),
        "sources": len(sources),
        "observations": len(observations),
        "projections": len(projections),
        "official_derived_projections": sum(row["color_status"].strip() == "OFFICIAL_DERIVED" for row in projections),
        "not_confirmed_projections": sum(row["color_status"].strip() == "NOT_CONFIRMED" for row in projections),
    }
    if not quiet:
        print("PASS Style Research validation")
        for key, value in metrics.items():
            print(f"{key}={value}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true", help="emit NEXT_STYLE_BATCH_GATE decision")
    args = parser.parse_args()
    metrics = validate(ROOT)
    if args.gate:
        print("NEXT_STYLE_BATCH_GATE=PASS")
        print("STYLE_APP_ELIGIBILITY_M098_M099=HOLD_CANONICAL_CATEGORY_DEFERRED")
        print(f"eligible_projection_rows={metrics['projections']}")


if __name__ == "__main__":
    main()
