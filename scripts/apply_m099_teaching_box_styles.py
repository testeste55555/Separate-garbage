#!/usr/bin/env python3
"""Apply audited Fukuyama (M099) teaching-box color projection.

The historical Style Research pilot intentionally kept M099 category styles out while
M099 was canonical-DEFERRED.  M099 is now independently APP_READY.  This additive UI
projection uses the official Fukuyama B3 household-waste poster's category bands as
visual evidence; HEX values are image-derived approximations, never claimed as
municipality-published color codes.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTION = ROOT / "data/style_research/08_style_ui_projection.csv"
VARIANT_BOXES = ROOT / "data/app/lesson_variant_teaching_boxes.csv"
MID = "M099"
PREFIX = "APP-STP-M099-"
CHECKED_DATE = "2026-08-31"
REVIEWER = "OPENAI_M099_APP_READY_STYLE_HOTFIX"
SOURCE_ID = "SS-M099-01"

# Approximate colors visually sampled from the official Fukuyama city B3 poster.
# These are presentation values only; waste-rule evidence remains in the canonical
# research layer and is not inferred from color.
STYLES = {
    "C-M099-01": ("燃やせるごみ", "#E85D7F", "#803346", "#000000", "分別区分帯"),
    "C-M099-02": ("容器包装プラスチックごみ", "#6F79B8", "#3D4365", "#000000", "分別区分帯"),
    "C-M099-03": ("紙類", "#D4A515", "#755B0C", "#000000", "分別区分帯"),
    "C-M099-04": ("資源ごみ", "#75B72C", "#406518", "#000000", "分別区分帯"),
    "C-M099-05": ("不燃（破砕）ごみ", "#8C6F54", "#4D3D2E", "#FFFFFF", "分別区分帯"),
    "C-M099-06": ("燃やせる粗大ごみ", "#D87920", "#774312", "#000000", "分別区分帯"),
    "C-M099-07": ("使用済乾電池等", "#E4A72B", "#7D5C18", "#000000", "特殊品目共有帯"),
}

DISPLAY_TO_CATEGORY = {name: category_id for category_id, (name, *_rest) in STYLES.items()}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def projection_rows(fields: list[str]) -> list[dict[str, str]]:
    required = {
        "projection_id", "rank", "municipality_id", "district_scope", "category_id",
        "自治体正式名称", "display_color", "border_color", "text_color", "color_status",
        "color_basis", "selected_style_id", "accessibility_label_required", "icon_status",
        "checked_date", "reviewer", "note",
    }
    missing = required.difference(fields)
    if missing:
        raise ValueError(f"style projection header missing columns: {sorted(missing)}")

    result: list[dict[str, str]] = []
    for index, (category_id, (name, display, border, text, evidence_kind)) in enumerate(STYLES.items(), start=1):
        row = {field: "" for field in fields}
        row.update({
            "projection_id": f"{PREFIX}{index:02d}",
            "rank": "2",
            "municipality_id": MID,
            "district_scope": "MUNICIPALITY_WIDE",
            "category_id": category_id,
            "自治体正式名称": name,
            "display_color": display,
            "border_color": border,
            "text_color": text,
            "color_status": "OFFICIAL_DERIVED",
            "color_basis": f"福山市公式B3ポスター市内版・左端{evidence_kind}の視覚表現（APP_READY後UI投影）",
            # Historical Style Research observations intentionally remain untouched.
            "selected_style_id": "",
            "accessibility_label_required": "TRUE",
            "icon_status": "NOT_RESEARCHED_AS_OFFICIAL",
            "checked_date": CHECKED_DATE,
            "reviewer": REVIEWER,
            "note": (
                "PDF画像からの近似値。自治体公式HEXではない。"
                f"source={SOURCE_ID}。M099 APP_READY後のUI投影であり、色を分別正答の根拠には使用しない。"
                "地域版で別の公式色が確認された場合はstyle_district_scopeで上書きする。"
            ),
        })
        result.append(row)
    return result


def apply_projection() -> int:
    fields, rows = read_csv(PROJECTION)
    kept = [row for row in rows if not row.get("projection_id", "").startswith(PREFIX)]
    overlay = projection_rows(fields)
    write_csv(PROJECTION, fields, kept + overlay)
    return len(overlay)


def apply_teaching_box_sources() -> int:
    fields, rows = read_csv(VARIANT_BOXES)
    required = {"lesson_variant_group_id", "box_kind", "display_name", "style_source_category_ids", "style_district_scope"}
    missing = required.difference(fields)
    if missing:
        raise ValueError(f"variant teaching box header missing columns: {sorted(missing)}")

    updated = 0
    for row in rows:
        if not row.get("lesson_variant_group_id", "").startswith("LV-M099-"):
            continue
        if row.get("box_kind") == "SIMPLIFIED_ACTION":
            row["style_source_category_ids"] = ""
            row["style_district_scope"] = ""
            continue
        category_id = DISPLAY_TO_CATEGORY.get(row.get("display_name", ""))
        if not category_id:
            raise ValueError(
                f"M099 official teaching box has no canonical style source mapping: "
                f"{row.get('lesson_variant_group_id')}/{row.get('teaching_box_id')} {row.get('display_name')}"
            )
        row["style_source_category_ids"] = category_id
        row["style_district_scope"] = "MUNICIPALITY_WIDE"
        updated += 1
    write_csv(VARIANT_BOXES, fields, rows)
    return updated


def main() -> None:
    projections = apply_projection()
    boxes = apply_teaching_box_sources()
    print(f"M099_TEACHING_BOX_STYLES_APPLIED projections={projections} teaching_boxes={boxes}")


if __name__ == "__main__":
    main()
