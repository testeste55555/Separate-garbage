#!/usr/bin/env python3
"""Mutation-based RED TEAM for the Style Research Pilot."""

from __future__ import annotations

import csv
import shutil
import tempfile
from pathlib import Path
from typing import Callable

from validate_style_research import ROOT, StyleValidationError, validate


Mutator = Callable[[Path], None]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def mutate_rows(root: Path, relative: str, mutator: Callable[[list[dict[str, str]]], None]) -> None:
    path = root / relative
    rows = read_csv(path)
    mutator(rows)
    write_csv(path, rows)


def row_by(rows: list[dict[str, str]], field: str, value: str) -> dict[str, str]:
    return next(row for row in rows if row[field] == value)


def expect_rejected(number: int, label: str, mutator: Mutator) -> None:
    with tempfile.TemporaryDirectory(prefix="style-red-team-") as tmp:
        test_root = Path(tmp) / "repo"
        shutil.copytree(ROOT / "data", test_root / "data")
        mutator(test_root)
        try:
            validate(test_root, quiet=True)
        except StyleValidationError:
            print(f"PASS {number:02d}/24 reject {label}")
            return
        raise AssertionError(f"RED TEAM attack was not rejected: {label}")


def main() -> None:
    metrics = validate(ROOT, quiet=True)
    if metrics["targets"] != 10 or metrics["projections"] != 51:
        raise AssertionError("baseline metrics unexpectedly changed")
    print("PASS 01/24 accept authentic baseline")

    expect_rejected(2, "fixed ranking rewrite", lambda root: mutate_rows(
        root, "data/style_research/03_top10_targets.csv",
        lambda rows: row_by(rows, "municipality_id", "M094").update({"rank": "2"}),
    ))
    expect_rejected(3, "Onomichi municipality-only scope collapse", lambda root: mutate_rows(
        root, "data/style_research/09_style_sources.csv",
        lambda rows: row_by(rows, "source_id", "SS-M098-02").update({"district_scope": "MUNICIPALITY_WIDE"}),
    ))
    expect_rejected(4, "Fukuyama missing Numakuma scope", lambda root: mutate_rows(
        root, "data/style_research/09_style_sources.csv",
        lambda rows: row_by(rows, "source_id", "SS-M099-04").update({"district_scope": "CITY_GENERAL"}),
    ))
    expect_rejected(5, "orphan category reference", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M094-001").update({"category_id": "C-M094-999"}),
    ))
    expect_rejected(6, "REFERENCE_ONLY as normal style bucket", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M094-001").update({"category_id": "C-M094-08", "自治体正式名称": "大型ごみ（有料）"}),
    ))
    expect_rejected(7, "invented deferred-municipality category style", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M094-001").update({"municipality_id": "M099"}),
    ))
    expect_rejected(8, "shared designated-bag color promoted to primary", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M104-010").update({"ui_selection": "PRIMARY"}),
    ))
    expect_rejected(9, "multiple primary observations for one category", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M104-010").update({"ui_selection": "PRIMARY", "semantic_fit": "CATEGORY_DISCRIMINATOR"}),
    ))
    expect_rejected(10, "decorative color promoted to primary", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M104-010").update({"ui_selection": "PRIMARY", "semantic_fit": "DECORATIVE_ONLY"}),
    ))
    expect_rejected(11, "conflicting Kaita resource color promoted", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M109-005").update({"ui_selection": "PRIMARY"}),
    ))
    expect_rejected(12, "derived color without approximation disclaimer", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M094-001").update({"note": "公式PDFから取得"}),
    ))
    expect_rejected(13, "invalid derived HEX", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M094-001").update({"display_color": "orange"}),
    ))
    expect_rejected(14, "named official color rewritten as confirmed guessed HEX", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M104-010").update({"display_color": "#FFA500"}),
    ))
    expect_rejected(15, "NOT_CONFIRMED with invented display color", lambda root: mutate_rows(
        root, "data/style_research/08_style_ui_projection.csv",
        lambda rows: row_by(rows, "category_id", "C-M105-02").update({"display_color": "#00FF00"}),
    ))
    expect_rejected(16, "FALLBACK pretending to have official source", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M105-002").update({"color_status": "FALLBACK"}),
    ))
    expect_rejected(17, "blank observation locator", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M094-001").update({"source_locator": ""}),
    ))
    expect_rejected(18, "cross-municipality source reference", lambda root: mutate_rows(
        root, "data/style_research/08_style_color_observations.csv",
        lambda rows: row_by(rows, "style_id", "STY-M094-001").update({"source_id": "SS-M104-01"}),
    ))

    def nonofficial_source(root: Path) -> None:
        mutate_rows(root, "data/style_research/09_style_sources.csv", lambda rows: row_by(rows, "source_id", "SS-M094-01").update({"source_url": "https://example.com/guide.pdf"}))
        mutate_rows(root, "data/style_research/08_style_color_observations.csv", lambda rows: [row.update({"source_url": "https://example.com/guide.pdf"}) for row in rows if row["source_id"] == "SS-M094-01"])

    expect_rejected(19, "non-official source domain", nonofficial_source)
    expect_rejected(20, "blank source-registry locator", lambda root: mutate_rows(
        root, "data/style_research/09_style_sources.csv",
        lambda rows: row_by(rows, "source_id", "SS-M094-01").update({"source_locator": ""}),
    ))
    expect_rejected(21, "Stage A and integrated data drift", lambda root: mutate_rows(
        root, "data/style_research/04_stage_a_style_observations.csv",
        lambda rows: rows.pop(0),
    ))
    expect_rejected(22, "missing canonical SORT_BUCKET projection", lambda root: mutate_rows(
        root, "data/style_research/08_style_ui_projection.csv",
        lambda rows: rows.pop(0),
    ))

    def deferred_projection(root: Path) -> None:
        def append(rows: list[dict[str, str]]) -> None:
            extra = dict(rows[0])
            extra.update({"projection_id": "STP-M099-FAKE", "municipality_id": "M099"})
            rows.append(extra)
        mutate_rows(root, "data/style_research/08_style_ui_projection.csv", append)

    expect_rejected(23, "projection row for canonical-deferred municipality", deferred_projection)
    expect_rejected(24, "insufficient text contrast", lambda root: mutate_rows(
        root, "data/style_research/08_style_ui_projection.csv",
        lambda rows: row_by(rows, "category_id", "C-M094-01").update({"text_color": "#FFFFFF"}),
    ))

    print("PASS Style Research RED TEAM 24/24")


if __name__ == "__main__":
    main()
