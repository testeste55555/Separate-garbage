#!/usr/bin/env python3
"""One-shot preparation patch for the M110-M112 LESSON_READY_10 branch.

This file is removed by the preparation workflow after it updates the permanent
builders/validators and regenerates committed data.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one match, got {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# --- Batch 11 source/category generator ---
replace_once(
    "scripts/build_batch_11.py",
    'M106_LESSON_CHECKED = "2026-08-27"\n',
    'M106_LESSON_CHECKED = "2026-08-27"\nLESSON_CHECKED = "2026-08-28"\n',
)
replace_once(
    "scripts/build_batch_11.py",
    'guide="https://www.akiota.jp/uploaded/attachment/9505.pdf"',
    'guide="https://www.akiota.jp/uploaded/attachment/9504.pdf"',
)
replace_once(
    "scripts/build_batch_11.py",
    '''    "M110": [\n        ("熊野町 ごみの正しい出し方", "自治体公式Webページ", municipality_specs["M110"]["top"], "2026-07-01", "可燃・資源物(1)・資源物(2)・埋立・有害・大型の現行6区分", "熊野町"),\n        ("資源物（1）", "自治体公式Webページ", "https://www.town.kumano.lg.jp/8/1/3/2/1/3572.html", "2026-03-31", "紙・衣類・PET・プラ容器包装の内部小分類と前処理", "熊野町"),\n    ],\n''',
    '''    "M110": [\n        ("熊野町 ごみの正しい出し方", "自治体公式Webページ", municipality_specs["M110"]["top"], "2026-07-01", "可燃・資源物(1)・資源物(2)・埋立・有害・大型の現行6区分", "熊野町"),\n        ("資源物（1）", "自治体公式Webページ", "https://www.town.kumano.lg.jp/8/1/3/2/1/3572.html", "2026-03-31", "紙・衣類・PET・プラ容器包装の内部小分類と前処理", "熊野町"),\n        ("広報くまの（リチウムイオン電池の出し方）", "自治体公式PDF", "https://www.town.kumano.lg.jp/material/files/group/4/6903ebcd016.pdf", "2025-11", "リチウムイオン電池をステーション収集せず環境事務所へ直接搬入すること", "熊野町"),\n        ("ごみ分別50音一覧", "自治体公式Excel", "https://www.town.kumano.lg.jp/material/files/group/11/bunbetsu50onn.xls", "2026-07-01時点掲載中", "固定10品目の品目別分別先と条件", "熊野町"),\n    ],\n''',
)
replace_once(
    "scripts/build_batch_11.py",
    '    "M111": [("ごみの出し方", "自治体公式Webページ", municipality_specs["M111"]["top"], "2026-03-27", "もやせる・粗大2種・埋立・有害・資源8子葉と前処理", "坂町")],\n',
    '''    "M111": [\n        ("ごみの出し方", "自治体公式Webページ", municipality_specs["M111"]["top"], "2026-03-27", "もやせる・粗大2種・埋立・有害・資源8子葉と前処理", "坂町"),\n        ("ごみ分別表（50音順）", "自治体公式PDF", "https://www.town.saka.lg.jp/wp-content/uploads/2014/04/%E3%81%94%E3%81%BF%E5%88%86%E5%88%A5%E8%A1%A8.pdf", "取得時点掲載中", "電球・使い捨てライター・リチウム電池等の品目別分別先", "坂町"),\n    ],\n''',
)
replace_once(
    "scripts/build_batch_11.py",
    '''    "M112": [\n        ("ごみ（一般廃棄物）の分別収集と処理について", "自治体公式Webページ", municipality_specs["M112"]["top"], "2026-06-22", "現行の上位分別体系と令和8年版資料への公式導線", "安芸太田町"),\n        ("令和8年版 安芸太田町 家庭ごみ分別五十音事典", "自治体公式PDF", municipality_specs["M112"]["guide"], "令和8年版", "12住民区分、区分ごとの指定袋、前処理・穴あけ不要ルール", "安芸太田町"),\n    ],\n''',
    '''    "M112": [\n        ("ごみ（一般廃棄物）の分別収集と処理について", "自治体公式Webページ", municipality_specs["M112"]["top"], "2026-06-22", "現行の上位分別体系と令和8年版資料への公式導線", "安芸太田町"),\n        ("令和8年版 安芸太田町 家庭ごみ分別五十音事典", "自治体公式PDF", municipality_specs["M112"]["guide"], "令和8年版", "12住民区分、区分ごとの指定袋、前処理・穴あけ不要ルール", "安芸太田町"),\n        ("リチウムイオン電池・モバイルバッテリー等の出し方", "自治体公式Webページ", "https://www.akiota.jp/soshiki/13/17462.html", "2026-07-31", "モバイルバッテリー・電球等の小型電化製品及び有害物区分", "安芸太田町"),\n    ],\n''',
)
replace_once(
    "scripts/build_batch_11.py",
    'add("M110", "大型ごみ", "大型家庭ごみ", ui="REFERENCE_ONLY", bulky="TRUE", prep="電池・燃料等を外す")\n',
    '''add("M110", "大型ごみ", "大型家庭ごみ", ui="REFERENCE_ONLY", bulky="TRUE", prep="電池・燃料等を外す")\nadd(\n    "M110", "環境事務所へ直接搬入（リチウムイオン電池等）",\n    "リチウムイオン電池・モバイルバッテリー", source=3, ui="EXCLUDED_NOTICE",\n    level="EXCLUDED", channel="NOT_COLLECTED", forbidden="ごみステーションへ出さない",\n    cond="家庭から出るリチウムイオン電池等", fallback="町の通常収集区分へ出さない",\n    prep="端子を絶縁して環境事務所へ直接搬入する", excluded="TRUE",\n    note="火災防止のためステーションでは収集しない", checked=LESSON_CHECKED,\n)\n''',
)
replace_once(
    "scripts/build_batch_11.py",
    'add("M111", "白色トレイ", "白色食品トレイ", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="洗って乾かす。白色のみ")\n',
    '''add("M111", "白色トレイ", "白色食品トレイ", parent="資源ごみ", level="SUBCATEGORY", ui="REFERENCE_ONLY", prep="洗って乾かす。白色のみ")\nadd(\n    "M111", "町で収集しないごみ（リチウム電池等）",\n    "リチウム電池・モバイルバッテリー", source=2, ui="EXCLUDED_NOTICE",\n    level="EXCLUDED", channel="NOT_COLLECTED", forbidden="町の通常収集へ出さない",\n    cond="家庭から出るリチウム電池等", fallback="販売店等の回収先を確認する",\n    prep="販売店等へ相談する", excluded="TRUE",\n    note="町収集外の品目別案内", checked=LESSON_CHECKED,\n)\n''',
)
replace_once(
    "scripts/build_batch_11.py",
    '''            m106_non_collection = mid == "M106" and i == 2\n            m107_legacy_guide = mid == "M107" and i == 4\n            rows.append({\n''',
    '''            m106_non_collection = mid == "M106" and i == 2\n            m107_legacy_guide = mid == "M107" and i == 4\n            lesson_current_source = (\n                (mid == "M110" and i in {3, 4})\n                or (mid == "M111" and i == 2)\n                or (mid == "M112" and i == 3)\n            )\n            rows.append({\n''',
)
replace_once(
    "scripts/build_batch_11.py",
    '''                    "2026年度／取得時点現行" if m106_non_collection\n                    else "平成29年度" if m107_legacy_guide\n                    else "令和8年度"\n                ),\n                "ページ更新日": updated, "取得確認日": M106_LESSON_CHECKED if m106_non_collection else CHECKED,\n''',
    '''                    "2026年度／取得時点現行" if (m106_non_collection or lesson_current_source)\n                    else "平成29年度" if m107_legacy_guide\n                    else "令和8年度"\n                ),\n                "ページ更新日": updated,\n                "取得確認日": (M106_LESSON_CHECKED if m106_non_collection else LESSON_CHECKED if lesson_current_source else CHECKED),\n''',
)

# --- Lesson synchronizer: create new image-grid rows for newly scoped municipalities. ---
replace_once(
    "scripts/sync_lesson_ready_reviews.py",
    'LESSON_STATUS = "LESSON_READY_10"\n',
    'LESSON_STATUS = "LESSON_READY_10"\nIMAGE_ITEM_ORDER = ["I001", "I007", "I013", "I004", "I006", "I031", "I029", "I014", "I033", "I017"]\n',
)
replace_once(
    "scripts/sync_lesson_ready_reviews.py",
    '''    image_fields, image_rows = read_csv(IMAGE_MAPPING_PATH)\n    scoring_branch_by_pair: dict[tuple[str, str], dict[str, str]] = {}\n''',
    '''    image_fields, image_rows = read_csv(IMAGE_MAPPING_PATH)\n    scoring_branch_by_pair: dict[tuple[str, str], dict[str, str]] = {}\n''',
)
replace_once(
    "scripts/sync_lesson_ready_reviews.py",
    '''    image_updates = 0\n    for row in image_rows:\n''',
    '''    scope_name_by_mid = {row["municipality_id"]: row["municipality_name"] for row in csv_rows(SCOPE_PATH)}\n    existing_image_pairs = {(row.get("municipality_id", ""), row.get("internal_item_id", "")) for row in image_rows}\n    for pair, scoring in sorted(scoring_branch_by_pair.items()):\n        if pair in existing_image_pairs:\n            continue\n        mid, iid = pair\n        image_rows.append({\n            "pair_order": "0",\n            "municipality_id": mid,\n            "municipality_name": scope_name_by_mid[mid],\n            "internal_item_id": iid,\n            "canonical_name": scoring["canonical_name"],\n            "display_name": scoring["display_name"],\n            "review_status": "VERIFIED",\n            "evidence_basis": scoring["evidence_basis"],\n            "category_id": scoring["category_id"],\n            "category_name": scoring["category_name"],\n            "condition": scoring["condition"],\n            "preparation": scoring["preparation"],\n            "exception_destination": scoring["exception_destination"],\n            "item_evidence_source_id": scoring["item_evidence_source_id"],\n            "item_evidence_url": scoring["item_evidence_url"],\n            "item_evidence_locator": scoring["item_evidence_locator"],\n            "checked_date": scoring["checked_date"],\n            "reviewer": scoring["reviewer"],\n            "note": "LESSON_READY_10のscoring_branchと同期。詳細条件は教師用reviewに保持。",\n        })\n        existing_image_pairs.add(pair)\n\n    image_updates = 0\n    for row in image_rows:\n''',
)
replace_once(
    "scripts/sync_lesson_ready_reviews.py",
    '''        image_updates += 1\n\n    write_csv(MAPPING_PATH, MAPPING_FIELDS, new_mappings)\n''',
    '''        image_updates += 1\n\n    scope_order = {row["municipality_id"]: index for index, row in enumerate(csv_rows(SCOPE_PATH))}\n    item_order = {iid: index for index, iid in enumerate(IMAGE_ITEM_ORDER)}\n    image_rows.sort(key=lambda row: (scope_order.get(row.get("municipality_id", ""), 9999), item_order.get(row.get("internal_item_id", ""), 9999)))\n    for order, row in enumerate(image_rows, 1):\n        row["pair_order"] = str(order)\n\n    write_csv(MAPPING_PATH, MAPPING_FIELDS, new_mappings)\n''',
)

# --- Image mapping validator: the scoring scope, not a historical hardcoded 9, defines the grid. ---
replace_once(
    "scripts/validate_item_image_mapping_pilot.py",
    '"""Validate the 10 image items x 9 active Style Research municipalities pilot."""',
    '"""Validate the fixed image10 grid for all municipality-wide scoring scopes."""',
)
replace_once(
    "scripts/validate_item_image_mapping_pilot.py",
    'TARGETS = ("M094", "M095", "M097", "M104", "M105", "M106", "M107", "M108", "M109")\n',
    '',
)
replace_once(
    "scripts/validate_item_image_mapping_pilot.py",
    '''    lesson_ready_mids = {\n        r["municipality_id"]\n        for r in rows(root / "data/app/lesson_mode_app_ready_scope.csv")\n        if r.get("scoring_status") == "LESSON_READY_10"\n    }\n''',
    '''    scoring_scope = rows(root / "data/app/lesson_mode_app_ready_scope.csv")\n    target_mids = tuple(r["municipality_id"] for r in scoring_scope)\n    lesson_ready_mids = {\n        r["municipality_id"]\n        for r in scoring_scope\n        if r.get("scoring_status") == "LESSON_READY_10"\n    }\n''',
)
replace_once(
    "scripts/validate_item_image_mapping_pilot.py",
    '''    expected_pairs = {(mid, iid) for mid in TARGETS for iid in ITEMS}\n    if len(pilot) != 90:\n        errors.append(f"pilot row count must be 90: {len(pilot)}")\n''',
    '''    expected_pairs = {(mid, iid) for mid in target_mids for iid in ITEMS}\n    expected_count = len(expected_pairs)\n    if len(pilot) != expected_count:\n        errors.append(f"pilot row count must be {expected_count}: {len(pilot)}")\n''',
)
replace_once(
    "scripts/validate_item_image_mapping_pilot.py",
    '    if status_counts != Counter({"VERIFIED": 90}):\n',
    '    if status_counts != Counter({"VERIFIED": expected_count}):\n',
)
replace_once(
    "scripts/validate_item_image_mapping_pilot.py",
    '''    print(\n        "pairs=90 historical_verified=90 unresolved=0 "\n        f"canonical_app_ready={canonical_app_ready} canonical_lesson_ready={canonical_lesson_ready} "\n        "municipalities=9 image_items=10"\n    )\n''',
    '''    municipality_count = len({row["municipality_id"] for row in pilot})\n    print(\n        f"pairs={len(pilot)} verified={len(pilot)} unresolved=0 "\n        f"canonical_app_ready={canonical_app_ready} canonical_lesson_ready={canonical_lesson_ready} "\n        f"municipalities={municipality_count} image_items=10"\n    )\n''',
)

# --- Lesson scoring validator / RED TEAM regression expectations. ---
replace_once(
    "scripts/validate_lesson_scoring_modes.py",
    '''    "M107": LESSON_READY, "M108": LESSON_READY, "M109": LESSON_READY,\n}\n''',
    '''    "M107": LESSON_READY, "M108": LESSON_READY, "M109": LESSON_READY,\n    "M110": LESSON_READY, "M111": LESSON_READY, "M112": LESSON_READY,\n}\n''',
)
replace_once(
    "scripts/validate_lesson_scoring_modes.py",
    '''    expected_box_counts = {"M106": (9, 6), "M107": (5, 8), "M108": (9, 8), "M109": (8, 5)}\n''',
    '''    expected_box_counts = {\n        "M106": (9, 6), "M107": (5, 8), "M108": (9, 8), "M109": (8, 5),\n        "M110": (5, 6), "M111": (10, 6), "M112": (6, 5),\n    }\n''',
)
replace_once(
    "scripts/validate_lesson_scoring_modes.py",
    '    expected_simplified = {("M106", "I029"), ("M107", "I007")}\n',
    '    expected_simplified = {("M106", "I029"), ("M107", "I007"), ("M110", "I029"), ("M111", "I029")}\n',
)

replace_once(
    "scripts/red_team_lesson_scoring_modes.py",
    '''        (\n            "M106/I029 action projection removed",\n            teaching_boxes,\n            [\n                row for row in scoring_projection\n                if not (row.get("municipality_id") == "M106" and row.get("internal_item_id") == "I029")\n            ],\n        ),\n    ]\n''',
    '''        (\n            "M106/I029 action projection removed",\n            teaching_boxes,\n            [\n                row for row in scoring_projection\n                if not (row.get("municipality_id") == "M106" and row.get("internal_item_id") == "I029")\n            ],\n        ),\n        (\n            "M110/I029 non-normal category misprojected to SORT_BUCKET",\n            teaching_boxes,\n            mutate_projection("M110", "I029", "category_id", "C-M110-05"),\n        ),\n        (\n            "M110 learner label leaks special collection route",\n            mutate_action_box("M110", "display_name", "環境事務所へ持込"),\n            scoring_projection,\n        ),\n        (\n            "M110/I029 action projection removed",\n            teaching_boxes,\n            [row for row in scoring_projection if not (row.get("municipality_id") == "M110" and row.get("internal_item_id") == "I029")],\n        ),\n        (\n            "M111/I029 non-normal category misprojected to SORT_BUCKET",\n            teaching_boxes,\n            mutate_projection("M111", "I029", "category_id", "C-M111-05"),\n        ),\n        (\n            "M111 learner label leaks special collection route",\n            mutate_action_box("M111", "display_name", "販売店へ持込"),\n            scoring_projection,\n        ),\n        (\n            "M111/I029 action projection removed",\n            teaching_boxes,\n            [row for row in scoring_projection if not (row.get("municipality_id") == "M111" and row.get("internal_item_id") == "I029")],\n        ),\n    ]\n''',
)

# --- Permanent CI rebuild must include the new generic Batch 11 lesson builder. ---
replace_once(
    ".github/workflows/app-ready-lesson-modes.yml",
    '      - "scripts/build_lesson_ready_m107_m109.py"\n',
    '      - "scripts/build_lesson_ready_m107_m109.py"\n      - "scripts/build_lesson_ready_batch11.py"\n',
)
# The same path list occurs once under pull_request too.
replace_once(
    ".github/workflows/app-ready-lesson-modes.yml",
    '      - "scripts/build_lesson_ready_m107_m109.py"\n',
    '      - "scripts/build_lesson_ready_m107_m109.py"\n      - "scripts/build_lesson_ready_batch11.py"\n',
)
replace_once(
    ".github/workflows/app-ready-lesson-modes.yml",
    '          python scripts/build_lesson_ready_m107_m109.py\n          python scripts/sync_lesson_ready_reviews.py\n',
    '          python scripts/build_lesson_ready_m107_m109.py\n          python scripts/build_lesson_ready_batch11.py\n          python scripts/sync_lesson_ready_reviews.py\n',
)
replace_once(
    ".github/workflows/app-ready-lesson-modes.yml",
    '''            data/research/lesson_readiness/m109_item_review.csv \\\n            data/research/05_item_mapping_master.csv \\\n''',
    '''            data/research/lesson_readiness/m109_item_review.csv \\\n            data/research/lesson_readiness/m110_item_review.csv \\\n            data/research/lesson_readiness/m111_item_review.csv \\\n            data/research/lesson_readiness/m112_item_review.csv \\\n            data/research/05_item_mapping_master.csv \\\n''',
)

print("M110_M112_PERMANENT_PATCH_APPLIED")
