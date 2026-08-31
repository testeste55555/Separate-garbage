from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "data/app/company_municipality_mapping.csv"
MUNICIPALITIES = ROOT / "data/master/01_municipalities_master.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
VARIANTS = ROOT / "data/app/lesson_variant_groups.csv"

REQUIRED = {
    "company_id", "company_display_name", "company_normalized_name", "company_aliases",
    "site_id", "site_display_name", "municipality_id", "lesson_variant_group_id",
    "mapping_status", "source_url", "checked_date", "identity_resolution_note",
    "display_order", "active",
}


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate(mapping_path=MAPPING, municipality_path=MUNICIPALITIES, scope_path=SCOPE, variant_path=VARIANTS):
    errors = []
    rows = read_rows(Path(mapping_path))
    if not rows:
        return ["company mapping is empty"]

    columns = set(rows[0])
    missing = REQUIRED - columns
    extra = columns - REQUIRED
    if missing:
        errors.append("missing columns: " + ",".join(sorted(missing)))
    if extra:
        errors.append("unexpected columns: " + ",".join(sorted(extra)))

    municipalities = {row["municipality_id"].strip() for row in read_rows(Path(municipality_path))}
    app_ready = {
        row["municipality_id"].strip()
        for row in read_rows(Path(scope_path))
        if row.get("scoring_status", "").strip() == "APP_READY"
    }
    variants = {
        row["lesson_variant_group_id"].strip(): row["municipality_id"].strip()
        for row in read_rows(Path(variant_path))
        if row.get("lesson_variant_group_id", "").strip()
    }

    site_ids = set()
    aliases = {}
    companies = {}

    for line_number, row in enumerate(rows, start=2):
        company_id = row.get("company_id", "").strip()
        site_id = row.get("site_id", "").strip()
        municipality_id = row.get("municipality_id", "").strip()
        if not company_id or not site_id:
            errors.append(f"line {line_number}: missing company_id/site_id")
            continue

        if site_id in site_ids:
            errors.append(f"line {line_number}: duplicate site_id {site_id}")
        site_ids.add(site_id)
        if not site_id.startswith(company_id + "-S"):
            errors.append(f"line {line_number}: site_id {site_id} does not belong to {company_id}")
        if municipality_id not in municipalities:
            errors.append(f"line {line_number}: unknown municipality_id {municipality_id}")

        mapping_status = row.get("mapping_status", "").strip()
        if mapping_status not in {"CONFIRMED", "HOLD"}:
            errors.append(f"line {line_number}: invalid mapping_status")

        active = row.get("active", "").strip().upper()
        if active not in {"TRUE", "FALSE"}:
            errors.append(f"line {line_number}: active must be TRUE/FALSE")
        if active == "TRUE" and mapping_status != "CONFIRMED":
            errors.append(f"line {line_number}: active mapping must be CONFIRMED")
        if active == "TRUE" and municipality_id not in app_ready:
            errors.append(f"line {line_number}: active site municipality {municipality_id} is not APP_READY")

        variant = row.get("lesson_variant_group_id", "").strip()
        if variant:
            if variant not in variants:
                errors.append(f"line {line_number}: unknown lesson_variant_group_id {variant}")
            elif variants[variant] != municipality_id:
                errors.append(
                    f"line {line_number}: variant {variant} belongs to {variants[variant]}, not {municipality_id}"
                )

        source = row.get("source_url", "").strip()
        parsed = urlparse(source)
        if mapping_status == "CONFIRMED" and (parsed.scheme not in {"http", "https"} or not parsed.netloc):
            errors.append(f"line {line_number}: confirmed mapping needs source_url")
        if not row.get("checked_date", "").strip():
            errors.append(f"line {line_number}: checked_date missing")
        if not row.get("company_normalized_name", "").strip():
            errors.append(f"line {line_number}: normalized name missing")

        companies.setdefault(company_id, 0)
        companies[company_id] += 1
        names = [
            row.get("company_display_name", "").strip(),
            *[alias.strip() for alias in row.get("company_aliases", "").split(";") if alias.strip()],
        ]
        for name in names:
            key = name.casefold()
            owner = aliases.get(key)
            if owner and owner != company_id:
                errors.append(f"line {line_number}: alias collision {name!r}: {owner} vs {company_id}")
            aliases[key] = company_id

    for company_id, count in companies.items():
        if count < 1:
            errors.append(f"{company_id}: no site")

    return errors


if __name__ == "__main__":
    validation_errors = validate()
    if validation_errors:
        print("COMPANY_MAPPING_VALIDATION: FAIL")
        for error in validation_errors:
            print("-", error)
        raise SystemExit(1)
    print("COMPANY_MAPPING_VALIDATION: PASS")
