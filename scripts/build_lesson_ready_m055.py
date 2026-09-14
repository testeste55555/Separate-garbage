#!/usr/bin/env python3
"""Build M055 雲南市 fixed-10 regional lesson data without inventing a municipality-wide answer.

Two official disposal systems coexist inside the city.  I031 and I033 differ between
大東・加茂・木次・三刀屋 and 吉田・掛合, so fixed-10 learner scoring lives in
lesson variant data.  The municipality-wide review remains an audit of every real
branch and deliberately has no scoring_branch=TRUE.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M055"
CHECKED = "2026-09-14"
REVIEWER = "OPENAI_GPT56_M055_LESSON_READY_15_V1"
REVIEW = ROOT / "data/research/lesson_readiness/m055_item_review.csv"
SUPPLEMENTAL = ROOT / "data/research/lesson_readiness/m055_supplemental_review.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
GROUPS = ROOT / "data/app/lesson_variant_groups.csv"
SCOPES = ROOT / "data/app/district_scopes.csv"
BOXES = ROOT / "data/app/lesson_variant_teaching_boxes.csv"
SCORING = ROOT / "data/app/lesson_variant_item_scoring.csv"
VARIANT_SOURCES = ROOT / "data/research/lesson_readiness/lesson_variant_sources.csv"
SOURCES = ROOT / "data/research/03_sources_master.csv"
BATCH_SOURCES = ROOT / "data/research/batches/batch_06/batch_06_sources.csv"
MUNICIPALITIES = ROOT / "data/research/04_municipalities_research.csv"
BATCH_MUNICIPALITIES = ROOT / "data/research/batches/batch_06/batch_06_municipalities.csv"
QA = ROOT / "data/research/06_qa_log.csv"
BATCH_QA = ROOT / "data/research/batches/batch_06/batch_06_qa.csv"
CATEGORIES = ROOT / "data/research/02_categories_master.csv"
MAPPINGS = ROOT / "data/research/05_item_mapping_master.csv"
COVERAGE = ROOT / "data/research/07_item_mapping_coverage.csv"
PRIORITY = ROOT / "data/master/07_implementation_priority.csv"
COMPANY = ROOT / "data/app/company_municipality_mapping.csv"

FIXED = ["I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"]
SUPP = {"I002", "I003", "I010", "I018", "I027"}
REGIONAL_BUILDER_TARGETS = {"M076", "M100", "M120", "M123", "M127", "M136", "M139"}

NEW_SOURCE = {
    "municipality_id": MID,
    "source_id": "S-M055-05",
    "資料名": "リチウム蓄電池（電子タバコ、モバイルバッテリー等）の出し方（雲南市向け）",
    "資料種別": "一部事務組合公式PDF",
    "公式URL": "https://www.unnan-yume.net/files/5/20250718094309_6879989d183ab.pdf",
    "発行主体": "雲南市・飯南町事務組合／雲南市",
    "対象年度": "現行",
    "ページ更新日": "2025-07-17",
    "取得確認日": CHECKED,
    "使用した情報": "モバイルバッテリー等は有害ごみ。4町は不燃ごみ収集日、吉田・掛合は可燃ごみ収集日。電池を外せない小型家電は金属類。",
    "優先度": "1",
    "現行性": "現行",
    "備考": "地域で収集日は異なるが、モバイルバッテリーの分別区分は有害ごみで共通。",
    "official_verified": "TRUE",
    "official_basis": "INTERMUNICIPAL_AUTHORITY_DOMAIN",
    "official_linking_url": "",
}

GROUP_ROWS = [
    {"lesson_variant_group_id": "LV-M055-01", "municipality_id": MID, "display_name": "大東・加茂・木次・三刀屋", "learner_selection_required": "TRUE", "display_order": "1", "readiness_status": "LESSON_READY_10", "note": "雲南エネルギーセンター管内。電球と使い捨てライターの正答が吉田・掛合と異なる。"},
    {"lesson_variant_group_id": "LV-M055-02", "municipality_id": MID, "display_name": "吉田・掛合", "learner_selection_required": "TRUE", "display_order": "2", "readiness_status": "LESSON_READY_10", "note": "いいしクリーンセンター管内。電球と使い捨てライターの正答が4町側と異なる。"},
]

DISTRICT_ROWS = []
for n, name in enumerate(["大東町", "加茂町", "木次町", "三刀屋町"], 1):
    DISTRICT_ROWS.append({
        "district_scope_id": f"DS-M055-{n:02d}", "municipality_id": MID, "district_name": name,
        "lesson_variant_group_id": "LV-M055-01", "display_order": str(n), "learner_visible": "FALSE",
        "official_source_id": "S-M055-02", "official_url": "https://www.unnan-yume.net/files/format/kankyo_ebook_enesen.pdf",
        "official_locator": "雲南エネルギーセンター管内版／大東・加茂・木次・三刀屋",
        "fixed_10_answer_set_id": "M055-FIXED10-EC", "fixed_10_confirmation_status": "CONFIRMED",
        "i031_answer_family": "有害ごみ1", "i031_evidence_source_id": "S-M055-02",
        "i031_evidence_url": "https://www.unnan-yume.net/files/format/kankyo_ebook_enesen.pdf",
        "i031_evidence_locator": "50音順『電球』有害ごみ／12頁LED電球は陶器・ガラス類",
        "note": "fixed10正答セットはLV-M055-01で共通。収集日だけの差は教材groupを分けない。",
    })
for n, name in enumerate(["吉田町", "掛合町"], 5):
    DISTRICT_ROWS.append({
        "district_scope_id": f"DS-M055-{n:02d}", "municipality_id": MID, "district_name": name,
        "lesson_variant_group_id": "LV-M055-02", "display_order": str(n), "learner_visible": "FALSE",
        "official_source_id": "S-M055-03", "official_url": "https://www.unnan-yume.net/files/format/kankyo_ebook_iishi.pdf",
        "official_locator": "いいしクリーンセンター管内版／吉田・掛合",
        "fixed_10_answer_set_id": "M055-FIXED10-IISHI", "fixed_10_confirmation_status": "CONFIRMED",
        "i031_answer_family": "陶器・ガラス類", "i031_evidence_source_id": "S-M055-03",
        "i031_evidence_url": "https://www.unnan-yume.net/files/format/kankyo_ebook_iishi.pdf",
        "i031_evidence_locator": "12頁『白熱電球、LED球、豆電球は陶器・ガラス類』",
        "note": "fixed10正答セットはLV-M055-02で共通。",
    })

COMMON = {
    "I001": ("C-M055-01", "燃やせるごみ", "ペットボトル本体", "ふたを外す", "ふたはくつ類・プラスチック類"),
    "I004": ("C-M055-02", "資源ごみ（ビン・カン）", "飲食用アルミ缶", "中身を空にして洗う", "飲食用以外の金属は金属類"),
    "I006": ("C-M055-02", "資源ごみ（ビン・カン）", "飲食用びん", "中身を空にして洗う", "ガラス製品は陶器・ガラス類"),
    "I007": ("C-M055-01", "燃やせるごみ", "食品トレイ", "中身・汚れを除く", "店頭回収は代替リサイクル経路"),
    "I013": ("C-M055-03", "資源ごみ（古紙）", "新聞・折込チラシ", "ひもで十字に結ぶ", "再生できない紙は燃やせるごみ"),
    "I014": ("C-M055-03", "資源ごみ（古紙）", "ダンボール", "金属を外しまとめる", "再生できない紙は燃やせるごみ"),
    "I017": ("C-M055-03", "資源ごみ（古紙）", "通常の紙パック", "洗って開いて乾かす", "内側アルミは燃やせるごみ"),
    "I029": ("C-M055-09", "有害ごみ2", "モバイルバッテリー", "透明袋に入れ有害表示・記名", "収集日は地域で異なるが区分は共通"),
}
VARIANT = {
    "LV-M055-01": {"I031": ("C-M055-08", "有害ごみ1", "電球", "破損しないよう保護", "LED電球は陶器・ガラス類"), "I033": ("C-M055-05", "くつ類・プラスチック類", "使い捨てガスライター", "ガスを使い切りガスを抜く", "金属製ライターは金属類")},
    "LV-M055-02": {"I031": ("C-M055-04", "陶器・ガラス類", "白熱電球・LED球・豆電球", "割れないよう扱う", "蛍光灯類は有害ごみ1"), "I033": ("C-M055-06", "金属類（小型家電類含む）", "使い捨てガスライター", "ガスを使い切りガスを抜く", "中身が残るものは出さない")},
}


def replace_mid(path: Path, new_rows: list[dict[str, str]], *, mid_field: str = "municipality_id", before_regional_targets: bool = False) -> None:
    fields, rows = read_csv(path)
    kept = [r for r in rows if r.get(mid_field) != MID]
    if before_regional_targets:
        idx = next((i for i, r in enumerate(kept) if r.get(mid_field) in REGIONAL_BUILDER_TARGETS), len(kept))
        kept[idx:idx] = new_rows
        rows = kept
    else:
        rows = kept + new_rows
    write_csv(path, fields, rows)


def upsert_source(path: Path) -> None:
    fields, rows = read_csv(path)
    rows = [r for r in rows if not (r.get("municipality_id") == MID and r.get("source_id") == NEW_SOURCE["source_id"])]
    rows.append(dict(NEW_SOURCE))
    rows.sort(key=lambda r: (r.get("municipality_id", ""), r.get("source_id", "")))
    write_csv(path, fields, rows)


def source_row(path: Path, source_id: str) -> dict[str, str]:
    _, rows = read_csv(path)
    return next(r for r in rows if r.get("municipality_id") == MID and r.get("source_id") == source_id)


def sync_variant_sources() -> None:
    fields, rows = read_csv(VARIANT_SOURCES)
    rows = [r for r in rows if r.get("municipality_id") != MID]
    srcs = [source_row(SOURCES, sid) for sid in ("S-M055-02", "S-M055-03", "S-M055-05")]
    idx = next((i for i, r in enumerate(rows) if r.get("municipality_id") in REGIONAL_BUILDER_TARGETS), len(rows))
    rows[idx:idx] = srcs
    write_csv(VARIANT_SOURCES, fields, rows)


def validate_review() -> list[dict[str, str]]:
    fields, rows = read_csv(REVIEW)
    if not rows or {r.get("internal_item_id") for r in rows} != set(FIXED):
        raise ValueError("M055 fixed review must contain exactly the fixed10 item IDs")
    if any(r.get("branch_review_status") != "COMPLETE" for r in rows):
        raise ValueError("M055 fixed review has incomplete branch")
    if any(r.get("scoring_branch") != "FALSE" for r in rows):
        raise ValueError("M055 must not create a municipality-wide scoring branch")
    by = defaultdict(list)
    for r in rows: by[r["internal_item_id"]].append(r)
    for iid, branches in by.items():
        if sorted(int(r["branch_order"]) for r in branches) != list(range(1, len(branches) + 1)):
            raise ValueError(f"M055 {iid} branch order is not contiguous")
    _, supp = read_csv(SUPPLEMENTAL)
    if {r.get("internal_item_id") for r in supp} != SUPP or any(r.get("branch_review_status") != "COMPLETE" for r in supp):
        raise ValueError("M055 supplemental review is incomplete")
    return rows


def sync_mapping_coverage(review_rows: list[dict[str, str]]) -> None:
    cat_fields, cats = read_csv(CATEGORIES)
    del cat_fields
    cat_by = {(r["municipality_id"], r["category_id"]): r for r in cats}
    src_fields, srcs = read_csv(SOURCES)
    del src_fields
    src_by = {(r["municipality_id"], r["source_id"]): r for r in srcs}
    map_fields, mappings = read_csv(MAPPINGS)
    mappings = [r for r in mappings if not (r.get("municipality_id") == MID and r.get("internal_item_id") in set(FIXED))]
    for r in review_rows:
        iid, bo, cid = r["internal_item_id"], r["branch_order"], r["category_id"]
        cat = cat_by[(MID, cid)]
        csrc = src_by[(MID, cat["source_id"])]
        mappings.append({
            "mapping_id": f"MAP-{MID}-{iid}-B{int(bo):02d}", "municipality_id": MID, "internal_item_id": iid,
            "branch_order": bo, "自治体での品目表記": r["official_item_wording"], "category_id": cid,
            "分別区分正式名称": r["category_name"], "条件": r["condition"], "前処理": r["preparation"],
            "例外分別先": r["exception_destination"], "自治体収集外": cat.get("自治体収集外か", "FALSE"),
            "rule_status": cat.get("rule_status", "CURRENT"), "effective_from": cat.get("effective_from", ""), "effective_to": cat.get("effective_to", ""),
            "category_source_id": cat["source_id"], "category_source_url": csrc["公式URL"], "category_source_locator": cat["出典ページ・該当箇所"],
            "item_evidence_source_id": r["item_evidence_source_id"], "item_evidence_url": r["item_evidence_url"], "item_evidence_locator": r["item_evidence_locator"],
            "確認日": CHECKED, "mapping_status": "VERIFIED", "evidence_scope": "ITEM_SPECIFIC", "branch_review_status": "COMPLETE",
            "reviewed_date": CHECKED, "reviewed_by": REVIEWER, "備考": "LESSON_READY_10の全条件枝レビュー済み。40品目APP_READYとは独立。",
        })
    mappings.sort(key=lambda r: (r.get("municipality_id", ""), r.get("internal_item_id", ""), int(r.get("branch_order") or 0), r.get("mapping_id", "")))
    write_csv(MAPPINGS, map_fields, mappings)

    cov_fields, coverage = read_csv(COVERAGE)
    by = defaultdict(list)
    for r in review_rows: by[r["internal_item_id"]].append(r)
    cov_by = {(r["municipality_id"], r["internal_item_id"]): r for r in coverage}
    for iid, branches in by.items():
        first = sorted(branches, key=lambda r: int(r["branch_order"]))[0]
        row = cov_by[(MID, iid)]
        row.update({
            "coverage_status": "VERIFIED", "mapping_branch_count": str(len(branches)), "branch_completeness_confirmed": "TRUE",
            "evidence_scope": "ITEM_SPECIFIC", "item_evidence_source_id": first["item_evidence_source_id"],
            "item_evidence_url": first["item_evidence_url"], "item_evidence_locator": first["item_evidence_locator"],
            "reviewed_date": CHECKED, "reviewed_by": REVIEWER, "notes": "LESSON_READY_10の全条件枝COMPLETE。残り30品目未完のためAPP_READYではない。",
        })
    write_csv(COVERAGE, cov_fields, coverage)


def variant_evidence(gid: str, iid: str) -> tuple[str, str, str]:
    if iid == "I029": return "S-M055-05", NEW_SOURCE["公式URL"], "雲南市向けチラシ／モバイルバッテリーは有害ごみ"
    sid = "S-M055-02" if gid == "LV-M055-01" else "S-M055-03"
    url = "https://www.unnan-yume.net/files/format/kankyo_ebook_enesen.pdf" if gid == "LV-M055-01" else "https://www.unnan-yume.net/files/format/kankyo_ebook_iishi.pdf"
    locators = {
        "I001": "5頁 燃やせるごみ／ペットボトル", "I004": "資源ごみ（ビン・カン）／飲食用缶",
        "I006": "資源ごみ（ビン・カン）／飲食用びん", "I007": "分別表『トレイ（食品用）』",
        "I013": "7頁 資源ごみ〈古紙〉／新聞", "I014": "7頁 資源ごみ〈古紙〉／ダンボール",
        "I017": "7頁 資源ごみ〈古紙〉／紙パック",
        "I031": "50音順『電球』有害ごみ" if gid == "LV-M055-01" else "12頁『白熱電球、LED球、豆電球は陶器・ガラス類』",
        "I033": "50音順『使い捨てガスライター』くつ類・プラスチック類" if gid == "LV-M055-01" else "50音順『使い捨てガスライター』金属類",
    }
    return sid, url, locators[iid]


def build_variants() -> None:
    replace_mid(GROUPS, GROUP_ROWS, before_regional_targets=True)
    replace_mid(SCOPES, DISTRICT_ROWS, before_regional_targets=True)
    box_rows, scoring_rows = [], []
    for gid in ("LV-M055-01", "LV-M055-02"):
        answers = dict(COMMON); answers.update(VARIANT[gid])
        unique = []
        for iid in FIXED:
            cid, label, *_ = answers[iid]
            if (cid, label) not in unique: unique.append((cid, label))
        box_by_cid = {}
        for order, (cid, label) in enumerate(unique, 1):
            bid = f"TB-{gid.replace('LV-', '')}-ON-{order:02d}"
            box_by_cid[cid] = bid
            box_rows.append({"lesson_variant_group_id": gid, "teaching_box_id": bid, "class_mode": "ONLINE_CLASS", "box_kind": "FIXED_10_SCORING", "display_name": label, "display_order": str(order), "note": "固定10品目の地域別採点用", "style_source_category_ids": cid, "style_district_scope": "MUNICIPALITY_WIDE"})
        for order, (cid, label) in enumerate(unique, 1):
            box_rows.append({"lesson_variant_group_id": gid, "teaching_box_id": f"TB-{gid.replace('LV-', '')}-IP-{order:02d}", "class_mode": "IN_PERSON_CLASS", "box_kind": "MAJOR_CATEGORY", "display_name": label, "display_order": str(order), "note": "対面授業用の主要分別箱。固定10で実際に使う区分のみ表示。", "style_source_category_ids": cid, "style_district_scope": "MUNICIPALITY_WIDE"})
        for iid in FIXED:
            cid, label, condition, prep, exc = answers[iid]
            sid, url, locator = variant_evidence(gid, iid)
            scoring_rows.append({"lesson_variant_group_id": gid, "municipality_id": MID, "internal_item_id": iid, "teaching_box_id": box_by_cid[cid], "condition": condition, "preparation": prep, "exception_destination": exc, "evidence_source_id": sid, "evidence_url": url, "evidence_locator": locator, "review_status": "COMPLETE", "checked_date": CHECKED, "reviewer": REVIEWER, "note": "画像の通常状態を地域groupの公式正答で採点"})
    # box file has no municipality_id; replace M055 group rows explicitly and place them before historical regional-builder targets.
    fields, rows = read_csv(BOXES)
    m055 = box_rows
    other = [r for r in rows if not r.get("lesson_variant_group_id", "").startswith("LV-M055-")]
    idx = next((i for i,r in enumerate(other) if r.get("lesson_variant_group_id", "").split("-")[1] in REGIONAL_BUILDER_TARGETS), len(other))
    other[idx:idx] = m055
    write_csv(BOXES, fields, other)
    replace_mid(SCORING, scoring_rows, before_regional_targets=True)


def update_scope_company_priority(review_rows: list[dict[str, str]]) -> None:
    fields, rows = read_csv(SCOPE)
    rows = [r for r in rows if r.get("municipality_id") != MID]
    rows.append({"municipality_id": MID, "municipality_name": "雲南市", "lesson_mode": "ONLINE_CLASS", "scoring_status": "LESSON_READY_10", "required_item_count": "10", "required_branch_count": str(len(review_rows)), "review_source": "data/research/lesson_readiness/m055_item_review.csv", "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv", "note": "固定10は2地域groupの公式正答で採点。電球・ライターの地域差をmunicipality-wideへ潰さない。補助5はreview済みだが15問Gate未接続。"})
    write_csv(SCOPE, fields, sorted(rows, key=lambda r:r["municipality_id"]))
    fields, rows = read_csv(COMPANY)
    hits=0
    for r in rows:
        if r.get("company_id")=="C017" and r.get("site_id")=="C017-S02" and r.get("municipality_id")==MID:
            r["lesson_variant_group_id"]="LV-M055-01"; r["active"]="TRUE"; r["checked_date"]=CHECKED
            r["identity_resolution_note"]="公式営業拠点一覧で確認した雲南支店（木次町）をrouting metadataとして採用。M055はLESSON_READY_10整備済みでLV-M055-01へ一意にrouting。会社所在地は居住地・家庭ごみ正答の根拠ではない。"; hits+=1
    if hits!=1: raise ValueError(f"expected C017-S02 M055 once, got {hits}")
    write_csv(COMPANY, fields, rows)
    fields, rows = read_csv(PRIORITY); hits=0
    for r in rows:
        if r.get("municipality_id")==MID:
            r["implementation_status"]="IMPLEMENTED"; r["readiness_status_snapshot"]="LESSON_READY_10"; r["checked_date"]=CHECKED
            r["note"]="固定10を2地域groupでLESSON_READY_10化。I031/I033の実在地域差を保持。C017-S02はroutingのみ。補助5はreview済み・15問Gate未接続。"; hits+=1
    if hits!=1: raise ValueError(f"priority M055 hit={hits}")
    write_csv(PRIORITY, fields, rows)


def sync_dates() -> None:
    for path in (MUNICIPALITIES, BATCH_MUNICIPALITIES):
        fields, rows=read_csv(path); hits=0
        for r in rows:
            if r.get("municipality_id")==MID: r["最終確認日"]=CHECKED; hits+=1
        if hits!=1: raise ValueError(f"M055 municipality row count {path}={hits}")
        write_csv(path, fields, rows)
    for path in (QA, BATCH_QA):
        fields, rows=read_csv(path); hits=0
        for r in rows:
            if r.get("municipality_id")==MID: r["確認日"]=CHECKED; hits+=1
        if hits!=1: raise ValueError(f"M055 QA row count {path}={hits}")
        write_csv(path, fields, rows)


def main() -> None:
    review_rows = validate_review()
    upsert_source(SOURCES); upsert_source(BATCH_SOURCES)
    sync_variant_sources(); sync_dates(); sync_mapping_coverage(review_rows)
    build_variants(); update_scope_company_priority(review_rows)
    print(f"M055_LESSON_READY_BUILT branches={len(review_rows)} groups=2 variant_scoring=20 supplemental=5")

if __name__ == "__main__":
    main()
