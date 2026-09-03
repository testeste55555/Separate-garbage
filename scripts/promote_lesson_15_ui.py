#!/usr/bin/env python3
"""Promote the confirmed supplemental-five assets into the learner 15-item UI.

This script is intentionally deterministic and is used once on the feature branch.
It preserves LESSON_READY_10 semantics; only the six current APP_READY company
municipalities receive the supplemental-five learner questions.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "data/app/item_image_assets.csv"
APP = ROOT / "app/app.js"
VALIDATOR = ROOT / "scripts/validate_item_image_assets.py"
README = ROOT / "data/app/README.md"

SUPPLEMENTAL_ASSETS = [
    (11, "I002", "ペットボトルのキャップ", "キャップ", "I002_pet_cap.webp"),
    (12, "I003", "ペットボトルのラベル", "ラベル", "I003_pet_label.webp"),
    (13, "I027", "乾電池", "乾電池", "I027_dry_battery.webp"),
    (14, "I018", "生ごみ", "生ごみ", "I018_food_waste.webp"),
    (15, "I010", "お菓子の袋", "お菓子の袋", "I010_snack_bag.webp"),
]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def update_assets() -> None:
    with ASSETS.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = ["pilot_order", "internal_item_id", "canonical_name", "display_name", "image_file", "asset_status"]
    by_id = {row["internal_item_id"]: row for row in rows}
    for order, item_id, canonical, display, image_file in SUPPLEMENTAL_ASSETS:
        expected = {
            "pilot_order": str(order),
            "internal_item_id": item_id,
            "canonical_name": canonical,
            "display_name": display,
            "image_file": image_file,
            "asset_status": "CONFIRMED",
        }
        if item_id in by_id:
            if by_id[item_id] != expected:
                raise SystemExit(f"asset row mismatch for {item_id}")
        else:
            rows.append(expected)
    rows.sort(key=lambda row: int(row["pilot_order"]))
    with ASSETS.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def update_asset_validator() -> None:
    text = VALIDATOR.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '    (10, "I017", "I017_milk_carton.png"),\n]',
        '    (10, "I017", "I017_milk_carton.png"),\n'
        '    (11, "I002", "I002_pet_cap.webp"),\n'
        '    (12, "I003", "I003_pet_label.webp"),\n'
        '    (13, "I027", "I027_dry_battery.webp"),\n'
        '    (14, "I018", "I018_food_waste.webp"),\n'
        '    (15, "I010", "I010_snack_bag.webp"),\n]',
        "validator item list",
    )
    text = replace_once(
        text,
        'IMAGE_FILE_RE = re.compile(r"^(I\\d{3})_[a-z0-9]+(?:_[a-z0-9]+)*\\.png$")\nPNG_SIGNATURE = b"\\x89PNG\\r\\n\\x1a\\n"',
        'IMAGE_FILE_RE = re.compile(r"^(I\\d{3})_[a-z0-9]+(?:_[a-z0-9]+)*\\.(?:png|webp)$")\n'
        'PNG_SIGNATURE = b"\\x89PNG\\r\\n\\x1a\\n"\nWEBP_RIFF = b"RIFF"\nWEBP_TAG = b"WEBP"',
        "validator image regex",
    )
    text = replace_once(
        text,
        '        with image_path.open("rb") as handle:\n'
        '            if handle.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:\n'
        '                fail(f"image asset is not a PNG: {image_file}")',
        '        data = image_path.read_bytes()[:12]\n'
        '        if image_file.endswith(".png"):\n'
        '            if not data.startswith(PNG_SIGNATURE):\n'
        '                fail(f"image asset is not a PNG: {image_file}")\n'
        '        elif image_file.endswith(".webp"):\n'
        '            if len(data) < 12 or data[:4] != WEBP_RIFF or data[8:12] != WEBP_TAG:\n'
        '                fail(f"image asset is not a WEBP: {image_file}")\n'
        '        else:\n'
        '            fail(f"unsupported image asset format: {image_file}")',
        "validator signature block",
    )
    VALIDATOR.write_text(text, encoding="utf-8", newline="\n")


def update_app() -> None:
    text = APP.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '    lessonVariantBoxes: "../data/app/lesson_variant_teaching_boxes.csv",\n'
        '    lessonVariantScoring: "../data/app/lesson_variant_item_scoring.csv"',
        '    lessonVariantBoxes: "../data/app/lesson_variant_teaching_boxes.csv",\n'
        '    lessonVariantScoring: "../data/app/lesson_variant_item_scoring.csv",\n'
        '    lessonSupplementalScoring: "../data/app/lesson_supplemental_item_scoring.csv",\n'
        '    lessonSupplementalBoxes: "../data/app/lesson_supplemental_teaching_boxes.csv"',
        "app data paths",
    )
    text = replace_once(
        text,
        '  const SAFE_IMAGE_RE = /^I\\d{3}_[A-Za-z0-9_]+\\.png$/;',
        '  const SAFE_IMAGE_RE = /^I\\d{3}_[A-Za-z0-9_]+\\.(?:png|webp)$/;',
        "app image regex",
    )
    text = replace_once(
        text,
        '  const LESSON_IMAGE_ITEM_IDS = new Set([\n'
        '    "I001", "I004", "I006", "I007", "I013",\n'
        '    "I014", "I017", "I029", "I031", "I033"\n'
        '  ]);',
        '  const LESSON_IMAGE_ITEM_IDS = new Set([\n'
        '    "I001", "I004", "I006", "I007", "I013",\n'
        '    "I014", "I017", "I029", "I031", "I033"\n'
        '  ]);\n'
        '  const SUPPLEMENTAL_IMAGE_ITEM_IDS = new Set(["I002", "I003", "I027", "I018", "I010"]);\n'
        '  const SUPPLEMENTAL_TARGET_MUNICIPALITIES = new Set(["M009", "M020", "M094", "M098", "M099", "M105"]);',
        "app supplemental constants",
    )
    text = replace_once(
        text,
        '  let lessonVariantItemsByGroup = new Map();\n'
        '  let activeLessonVariantGroupId = "";',
        '  let lessonVariantItemsByGroup = new Map();\n'
        '  let supplementalItemsByMunicipality = new Map();\n'
        '  let supplementalVariantItemsByGroup = new Map();\n'
        '  let supplementalBoxesByGroup = new Map();\n'
        '  let supplementalImageGateReady = false;\n'
        '  let activeLessonVariantGroupId = "";',
        "app supplemental state",
    )

    insert_before = '  function findAppStyleSheet() {'
    supplemental_function = '''  function buildLessonSupplementalData(scoringRows, supplementalBoxRows) {\n    supplementalItemsByMunicipality = new Map();\n    supplementalVariantItemsByGroup = new Map();\n    supplementalBoxesByGroup = new Map();\n    supplementalImageGateReady = [...SUPPLEMENTAL_IMAGE_ITEM_IDS].every((itemId) => assetsByItem.has(itemId));\n    if (!supplementalImageGateReady) return;\n\n    for (const row of supplementalBoxRows) {\n      const groupId = row.lesson_variant_group_id?.trim();\n      const boxId = row.teaching_box_id?.trim();\n      if (!groupId || !boxId || row.class_mode?.trim() !== ONLINE_CLASS_MODE) continue;\n      if (!lessonVariantGroupById.has(groupId)) continue;\n      if (!supplementalBoxesByGroup.has(groupId)) supplementalBoxesByGroup.set(groupId, []);\n      supplementalBoxesByGroup.get(groupId).push(row);\n    }\n    for (const rows of supplementalBoxesByGroup.values()) {\n      rows.sort((a, b) => numericOrder(a.display_order) - numericOrder(b.display_order));\n    }\n\n    for (const row of scoringRows) {\n      const municipalityId = row.municipality_id?.trim();\n      const groupId = row.lesson_variant_group_id?.trim();\n      const itemId = row.internal_item_id?.trim();\n      if (!municipalityId || !itemId || row.review_status?.trim() !== "COMPLETE") continue;\n      if (!SUPPLEMENTAL_TARGET_MUNICIPALITIES.has(municipalityId) || !SUPPLEMENTAL_IMAGE_ITEM_IDS.has(itemId)) continue;\n      const asset = assetsByItem.get(itemId);\n      const imageFile = asset?.image_file?.trim();\n      if (!asset || !SAFE_IMAGE_RE.test(imageFile ?? "") || !imageFile.startsWith(`${itemId}_`)) continue;\n\n      if (groupId) {\n        const group = lessonVariantGroupById.get(groupId);\n        if (!group || group.municipality_id?.trim() !== municipalityId) continue;\n        const baseBoxes = lessonVariantBoxesByGroupAndMode.get(`${groupId}::${ONLINE_CLASS_MODE}`) ?? [];\n        const extraBoxes = supplementalBoxesByGroup.get(groupId) ?? [];\n        const boxId = row.teaching_box_id?.trim();\n        if (!boxId || ![...baseBoxes, ...extraBoxes].some((box) => box.teaching_box_id?.trim() === boxId)) continue;\n        if (!supplementalVariantItemsByGroup.has(groupId)) supplementalVariantItemsByGroup.set(groupId, []);\n        supplementalVariantItemsByGroup.get(groupId).push({\n          municipalityId, itemId, imageFile, pairOrder: numericOrder(row.display_order), uiCategoryId: boxId\n        });\n        continue;\n      }\n\n      const sortBucket = findSortBucket(municipalityId, row.category_id?.trim());\n      if (!sortBucket) continue;\n      if (!supplementalItemsByMunicipality.has(municipalityId)) supplementalItemsByMunicipality.set(municipalityId, []);\n      supplementalItemsByMunicipality.get(municipalityId).push({\n        municipalityId, itemId, imageFile, pairOrder: numericOrder(row.display_order), uiCategoryId: sortBucket.category_id.trim()\n      });\n    }\n\n    for (const rows of [...supplementalItemsByMunicipality.values(), ...supplementalVariantItemsByGroup.values()]) {\n      rows.sort((a, b) => a.pairOrder - b.pairOrder);\n    }\n  }\n\n  function supplementalSetReady(rows) {\n    return supplementalImageGateReady && rows.length === SUPPLEMENTAL_IMAGE_ITEM_IDS.size &&\n      new Set(rows.map((row) => row.itemId)).size === SUPPLEMENTAL_IMAGE_ITEM_IDS.size;\n  }\n\n'''
    text = replace_once(text, insert_before, supplemental_function + insert_before, "app supplemental functions")

    old_display = '''  function displayRows(id) {\n    if (activeLessonVariantGroupId) {\n      const classMode = lessonModeSelect.value;\n      if (![ONLINE_CLASS_MODE, IN_PERSON_CLASS_MODE].includes(classMode)) return [];\n      return lessonVariantBoxesByGroupAndMode.get(`${activeLessonVariantGroupId}::${classMode}`) ?? [];\n    }\n    const classMode = lessonModeSelect.value;\n    const lessonRows = lessonBoxesByMunicipalityAndMode.get(`${id}::${classMode}`) ?? [];\n    if (lessonRows.length > 0) return lessonRows;\n    return bucketsByMunicipality.get(id) ?? [];\n  }'''
    new_display = '''  function displayRows(id) {\n    if (activeLessonVariantGroupId) {\n      const classMode = lessonModeSelect.value;\n      if (![ONLINE_CLASS_MODE, IN_PERSON_CLASS_MODE].includes(classMode)) return [];\n      const baseRows = lessonVariantBoxesByGroupAndMode.get(`${activeLessonVariantGroupId}::${classMode}`) ?? [];\n      const supplementalItems = supplementalVariantItemsByGroup.get(activeLessonVariantGroupId) ?? [];\n      if (classMode !== ONLINE_CLASS_MODE || !supplementalSetReady(supplementalItems)) return baseRows;\n      const extraRows = supplementalBoxesByGroup.get(activeLessonVariantGroupId) ?? [];\n      const seen = new Set();\n      return [...baseRows, ...extraRows]\n        .filter((row) => {\n          const boxId = row.teaching_box_id?.trim();\n          if (!boxId || seen.has(boxId)) return false;\n          seen.add(boxId);\n          return true;\n        })\n        .sort((a, b) => numericOrder(a.display_order) - numericOrder(b.display_order));\n    }\n    const classMode = lessonModeSelect.value;\n    const lessonRows = lessonBoxesByMunicipalityAndMode.get(`${id}::${classMode}`) ?? [];\n    if (lessonRows.length > 0) return lessonRows;\n    return bucketsByMunicipality.get(id) ?? [];\n  }'''
    text = replace_once(text, old_display, new_display, "app display rows")

    old_active = '''    activeItems = lessonMode === ONLINE_CLASS_MODE && id\n      ? activeLessonVariantGroupId\n        ? [...(lessonVariantItemsByGroup.get(activeLessonVariantGroupId) ?? [])]\n        : [...(itemsByMunicipality.get(id) ?? [])]\n      : [];'''
    new_active = '''    activeItems = [];\n    if (lessonMode === ONLINE_CLASS_MODE && id) {\n      if (activeLessonVariantGroupId) {\n        const coreItems = lessonVariantItemsByGroup.get(activeLessonVariantGroupId) ?? [];\n        const supplementalItems = supplementalVariantItemsByGroup.get(activeLessonVariantGroupId) ?? [];\n        activeItems = supplementalSetReady(supplementalItems) ? [...coreItems, ...supplementalItems] : [...coreItems];\n      } else {\n        const coreItems = itemsByMunicipality.get(id) ?? [];\n        const supplementalItems = supplementalItemsByMunicipality.get(id) ?? [];\n        activeItems = SUPPLEMENTAL_TARGET_MUNICIPALITIES.has(id) && supplementalSetReady(supplementalItems)\n          ? [...coreItems, ...supplementalItems]\n          : [...coreItems];\n      }\n    }'''
    text = replace_once(text, old_active, new_active, "app active items")

    text = replace_once(
        text,
        '        fetchText(DATA_PATHS.lessonVariantBoxes),\n'
        '        fetchText(DATA_PATHS.lessonVariantScoring)\n'
        '      ];',
        '        fetchText(DATA_PATHS.lessonVariantBoxes),\n'
        '        fetchText(DATA_PATHS.lessonVariantScoring),\n'
        '        fetchText(DATA_PATHS.lessonSupplementalScoring),\n'
        '        fetchText(DATA_PATHS.lessonSupplementalBoxes)\n'
        '      ];',
        "app load requests",
    )
    text = replace_once(
        text,
        '        teachingBoxText, scoringProjectionText,\n'
        '        districtScopeText, variantGroupText, variantBoxText, variantScoringText\n'
        '      ] = texts;',
        '        teachingBoxText, scoringProjectionText,\n'
        '        districtScopeText, variantGroupText, variantBoxText, variantScoringText,\n'
        '        supplementalScoringText, supplementalBoxText\n'
        '      ] = texts;',
        "app load destructuring",
    )
    text = replace_once(
        text,
        '      buildLessonVariantData(\n'
        '        parseCsv(districtScopeText),\n'
        '        parseCsv(variantGroupText),\n'
        '        parseCsv(variantBoxText),\n'
        '        parseCsv(variantScoringText)\n'
        '      );\n'
        '      installOfficialStyleRules();',
        '      buildLessonVariantData(\n'
        '        parseCsv(districtScopeText),\n'
        '        parseCsv(variantGroupText),\n'
        '        parseCsv(variantBoxText),\n'
        '        parseCsv(variantScoringText)\n'
        '      );\n'
        '      buildLessonSupplementalData(parseCsv(supplementalScoringText), parseCsv(supplementalBoxText));\n'
        '      installOfficialStyleRules();',
        "app supplemental build call",
    )
    APP.write_text(text, encoding="utf-8", newline="\n")


def update_readme() -> None:
    text = README.read_text(encoding="utf-8")
    old = "`SUPPLEMENTAL_5`は授業用の正式追加5品目ですが、5点すべての画像assetが`CONFIRMED`になるまでは学習者UIへ追加しません。画像Gateは0/5→5/5のall-or-nothingとし、途中状態で11〜14問へ拡張しません。"
    new = "`SUPPLEMENTAL_5`の5点画像assetはすべて`CONFIRMED`済みです。画像Gateは5/5で成立し、上記6自治体だけオンライン画像練習を15問へ拡張します。その他の`LESSON_READY_10`自治体は引き続き10問のままです。"
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        text += "\n" + new + "\n"
    README.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    update_assets()
    update_asset_validator()
    update_app()
    update_readme()
    print("Promoted supplemental five to guarded 15-item learner UI")


if __name__ == "__main__":
    main()
