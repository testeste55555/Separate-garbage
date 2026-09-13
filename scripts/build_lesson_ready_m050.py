#!/usr/bin/env python3
"""Build M050 出雲市 LESSON_READY_10 projections and current evidence.

M050 belongs to completed research batch_05, so source/category/QA refreshes are
written identically to canonical and the completed batch bundle. Supplemental-five
review remains evidence-only until the guarded 15-item gate explicitly admits M050.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from schema_v12 import read_csv, write_csv

ROOT = Path(__file__).resolve().parents[1]
MID = "M050"
NAME = "出雲市"
CHECKED = "2026-09-14"
REVIEW = ROOT / "data/research/lesson_readiness/m050_item_review.csv"
SUPPLEMENTAL_REVIEW = ROOT / "data/research/lesson_readiness/m050_supplemental_review.csv"
SCOPE = ROOT / "data/app/lesson_mode_app_ready_scope.csv"
BOXES = ROOT / "data/app/lesson_teaching_boxes.csv"
PROJECTION = ROOT / "data/app/lesson_item_scoring_projection.csv"
PRIORITY = ROOT / "data/master/07_implementation_priority.csv"
COMPANY = ROOT / "data/app/company_municipality_mapping.csv"
VARIANTS = ROOT / "data/app/lesson_variant_groups.csv"
SOURCES_MASTER = ROOT / "data/research/03_sources_master.csv"
BATCH_SOURCES = ROOT / "data/research/batches/batch_05/batch_05_sources.csv"
CATEGORIES_MASTER = ROOT / "data/research/02_categories_master.csv"
BATCH_CATEGORIES = ROOT / "data/research/batches/batch_05/batch_05_categories.csv"
QA = ROOT / "data/research/06_qa_log.csv"
BATCH_QA = ROOT / "data/research/batches/batch_05/batch_05_qa.csv"
MUNICIPALITIES = ROOT / "data/research/04_municipalities_research.csv"
BATCH_MUNICIPALITIES = ROOT / "data/research/batches/batch_05/batch_05_municipalities.csv"
REVIEW_EVIDENCE = ROOT / "data/research/08_category_review_evidence.csv"
BATCH_REVIEW_EVIDENCE = ROOT / "data/research/batches/batch_05/batch_05_category_review_evidence.csv"

FIXED_10 = {"I001", "I004", "I006", "I007", "I013", "I014", "I017", "I029", "I031", "I033"}
SUPPLEMENTAL_5 = {"I002", "I003", "I010", "I018", "I027"}

SCOPE_FIELDS = [
    "municipality_id", "municipality_name", "lesson_mode", "scoring_status",
    "required_item_count", "required_branch_count", "review_source", "image_mapping_source", "note",
]
BOX_FIELDS = [
    "municipality_id", "teaching_box_id", "class_mode", "box_kind", "category_id",
    "display_name", "display_order", "note", "style_source_category_ids", "style_district_scope",
]
PROJECTION_FIELDS = [
    "municipality_id", "internal_item_id", "teaching_box_id", "projection_kind",
    "category_id", "review_status", "note",
]
SOURCE_FIELDS = [
    "municipality_id", "source_id", "資料名", "資料種別", "公式URL", "発行主体", "対象年度",
    "ページ更新日", "取得確認日", "使用した情報", "優先度", "現行性", "備考",
    "official_verified", "official_basis", "official_linking_url",
]
CATEGORY_FIELDS = [
    "municipality_id", "category_id", "自治体正式名称", "category_group", "parent_category_id",
    "classification_level", "表示順", "collection_channel", "代表品目", "入れてはいけない物",
    "適用条件", "条件外の扱い", "出す前の処理", "袋・容器のルール", "サイズ・条件",
    "粗大ごみ扱いか", "予約が必要か", "有料か", "料金ルール", "自治体収集外か", "注意事項",
    "source_id", "出典URL", "出典ページ・該当箇所", "確認日", "ui_role", "rule_status",
    "effective_from", "effective_to",
]

ONLINE_SPEC = [
    ("C-M050-01", "燃えるごみ", "FIXED_10_SCORING"),
    ("C-M050-02", "破砕ごみ", "FIXED_10_SCORING"),
    ("C-M050-03", "埋立ごみ", "FIXED_10_SCORING"),
    ("C-M050-05", "飲料用空き缶", "FIXED_10_SCORING"),
    ("C-M050-06", "空きびん", "FIXED_10_SCORING"),
    ("C-M050-07", "ペットボトル", "FIXED_10_SCORING"),
    ("C-M050-10", "古紙", "FIXED_10_SCORING"),
    ("C-M050-14", "回収・確認", "SIMPLIFIED_ACTION"),
]
IN_PERSON_SPEC = [
    ("C-M050-01", "燃えるごみ"),
    ("C-M050-02", "破砕ごみ"),
    ("C-M050-03", "埋立ごみ"),
    ("C-M050-05", "飲料用空き缶"),
    ("C-M050-06", "空きびん"),
    ("C-M050-07", "ペットボトル"),
    ("C-M050-10", "古紙"),
]

NEW_SOURCES = [
    {
        "municipality_id": MID, "source_id": "S-M050-04",
        "資料名": "出雲市ごみの分け方・出し方ガイドブック（分別品目一覧表27-38ページ）",
        "資料種別": "自治体公式PDF",
        "公式URL": "https://www.city.izumo.shimane.jp/www/contents/1752026038326/simple/27-38nihongo.pdf",
        "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2026-08-01", "取得確認日": CHECKED,
        "使用した情報": "固定10・補助5の品目別分別、PETふたラベル、電球材質差、紙パック内面アルミ、ライター",
        "優先度": "1", "現行性": "現行", "備考": "現行ガイドブックの50音順品目表。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "https://www.city.izumo.shimane.jp/www/contents/1752026038326/index.html",
    },
    {
        "municipality_id": MID, "source_id": "S-M050-05",
        "資料名": "充電式電池（リチウムイオン電池など）の適切な処分について",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.izumo.shimane.jp/www/contents/1755575355511/index.html",
        "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2026-05-18", "取得確認日": CHECKED,
        "使用した情報": "モバイルバッテリー、リサイクルマーク、破砕ごみ、協力店・市役所窓口、膨張破損",
        "優先度": "1", "現行性": "現行", "備考": "モバイルバッテリーは状態・マークで経路が分岐する。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M050-06",
        "資料名": "古紙・古着の出し方及びリサイクルステーション",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.izumo.shimane.jp/www/contents/1751852233443/index.html",
        "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2026-04-01", "取得確認日": CHECKED,
        "使用した情報": "新聞・段ボール・紙パック等の古紙4分類とリサイクルステーション",
        "優先度": "1", "現行性": "現行", "備考": "固定10の古紙3品目の補強根拠。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M050-07",
        "資料名": "令和8年10月から始まる電池類の分別収集について",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.izumo.shimane.jp/www/contents/1787126731273/index.html",
        "発行主体": NAME, "対象年度": "令和8年10月以降", "ページ更新日": "2026-08-21", "取得確認日": CHECKED,
        "使用した情報": "2026年10月開始予定の電池類新分別収集",
        "優先度": "2", "現行性": "現行案内中", "備考": "2026-09-14時点では施行前。現行採点には使用せず将来切替根拠として保持。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M050-08",
        "資料名": "飲料用空き缶・空きびん・ペットボトル・使用済電池などの出し方",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.izumo.shimane.jp/www/contents/1751610005231/index.html",
        "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2025-07-07", "取得確認日": CHECKED,
        "使用した情報": "飲料用缶・びん・PET・使用済筒型乾電池の現行出し方",
        "優先度": "1", "現行性": "現行", "備考": "資源系固定品目の公式導線。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M050-09",
        "資料名": "食品トレイなどを持って、お買い物へ行こう！",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.izumo.shimane.jp/www/contents/1755143325157/index.html",
        "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2025-08-26", "取得確認日": CHECKED,
        "使用した情報": "白色食品トレー等の店頭回収・リサイクル推奨",
        "優先度": "2", "現行性": "現行", "備考": "市収集の燃えるごみに対する代替リサイクル経路。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
    {
        "municipality_id": MID, "source_id": "S-M050-10",
        "資料名": "燃えるごみに発火の恐れのあるものは出さないでください",
        "資料種別": "自治体公式Webページ",
        "公式URL": "https://www.city.izumo.shimane.jp/www/contents/1604021794281/index.html",
        "発行主体": NAME, "対象年度": "現行", "ページ更新日": "2025-07-13", "取得確認日": CHECKED,
        "使用した情報": "ライターは中身を使い切って破砕ごみ、充電式電池の注意",
        "優先度": "1", "現行性": "現行", "備考": "火災防止条件の補強根拠。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    },
]

ALT_CATEGORY = {
    "municipality_id": MID,
    "category_id": "C-M050-14",
    "自治体正式名称": "充電式電池の回収・確認",
    "category_group": "充電式電池",
    "parent_category_id": "",
    "classification_level": "ALTERNATIVE",
    "表示順": "14",
    "collection_channel": "RETAILER_OR_MAKER",
    "代表品目": "モバイルバッテリー・リチウムイオン電池等の充電式電池",
    "入れてはいけない物": "NOT_STATED_IN_CITED_SOURCE",
    "適用条件": "リサイクルマーク・膨張破損等により協力店または市役所窓口への持込が必要なもの",
    "条件外の扱い": "リサイクルマークがないものは破砕ごみ",
    "出す前の処理": "持込時は電極部分をテープ等で絶縁",
    "袋・容器のルール": "",
    "サイズ・条件": "",
    "粗大ごみ扱いか": "FALSE",
    "予約が必要か": "FALSE",
    "有料か": "FALSE",
    "料金ルール": "",
    "自治体収集外か": "FALSE",
    "注意事項": "膨張・破損品は市役所本庁4階環境施設課窓口へ",
    "source_id": "S-M050-05",
    "出典URL": "https://www.city.izumo.shimane.jp/www/contents/1755575355511/index.html",
    "出典ページ・該当箇所": "出し方1～5・注意点",
    "確認日": CHECKED,
    "ui_role": "REFERENCE_ONLY",
    "rule_status": "CURRENT",
    "effective_from": "",
    "effective_to": "",
}

def replace_mid(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    current_fields, existing = read_csv(path)
    if current_fields != fields:
        raise ValueError(f"unexpected schema for {path}: {current_fields}")
    kept = [row for row in existing if row.get("municipality_id") != MID]
    write_csv(path, fields, kept + rows)

def upsert_sources(path: Path) -> None:
    fields, rows = read_csv(path)
    if fields != SOURCE_FIELDS:
        raise ValueError(f"unexpected source schema for {path}: {fields}")
    new_ids = {row["source_id"] for row in NEW_SOURCES}
    rows = [row for row in rows if not (row.get("municipality_id") == MID and row.get("source_id") in new_ids)]
    rows.extend(dict(row) for row in NEW_SOURCES)
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("source_id", "")))
    write_csv(path, fields, rows)

def upsert_alt_category(path: Path) -> None:
    fields, rows = read_csv(path)
    if fields != CATEGORY_FIELDS:
        raise ValueError(f"unexpected category schema for {path}: {fields}")
    rows = [row for row in rows if not (row.get("municipality_id") == MID and row.get("category_id") == ALT_CATEGORY["category_id"])]
    rows.append(dict(ALT_CATEGORY))
    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("category_id", "")))
    write_csv(path, fields, rows)

def sync_category_review_pair() -> None:
    reviewer = "OPENAI_GPT56_M050_LESSON_READY_15_V1"
    basis = (
        "S-M050-01の家庭ごみ13葉区分を基礎に、S-M050-05の現行充電式電池の協力店・"
        "市役所窓口回収経路を公式ALTERNATIVEとして追加確認。CURRENT非EXCLUDED_NOTICEは14区分。"
    )
    canonical_row = None
    for path in (MUNICIPALITIES, BATCH_MUNICIPALITIES):
        fields, rows = read_csv(path)
        hits = 0
        for row in rows:
            if row.get("municipality_id") != MID:
                continue
            row["最終確認日"] = CHECKED
            row["reviewed_category_count"] = "14"
            row["category_count_basis"] = basis
            row["category_count_verified"] = "TRUE"
            row["category_count_check_status"] = "MANUAL_INDEX_REVIEW"
            row["category_count_review_id"] = "CR-M050-CATEGORY-COVERAGE"
            row["category_count_reviewed_date"] = CHECKED
            row["category_count_reviewed_by"] = reviewer
            hits += 1
            if path == MUNICIPALITIES:
                canonical_row = dict(row)
        if hits != 1:
            raise ValueError(f"expected one M050 municipality row in {path}, got {hits}")
        write_csv(path, fields, rows)
    if canonical_row is None:
        raise ValueError("missing canonical M050 municipality row")

    evidence = {
        "review_evidence_id": "CRE-M050-04",
        "review_id": "CR-M050-CATEGORY-COVERAGE",
        "municipality_id": MID,
        "source_id": "S-M050-05",
        "locator": "充電式電池のリサイクルマーク・状態別処分経路",
        "evidence_role": "SUPPLEMENTAL_INDEX",
        "notes": "2026-09-14 category completeness再監査。通常13葉区分に公式ALTERNATIVE回収経路を追加。",
    }
    for path in (REVIEW_EVIDENCE, BATCH_REVIEW_EVIDENCE):
        fields, rows = read_csv(path)
        rows = [row for row in rows if row.get("review_evidence_id") != evidence["review_evidence_id"]]
        rows.append(dict(evidence))
        rows.sort(key=lambda row: row.get("review_evidence_id", ""))
        write_csv(path, fields, rows)


def sync_qa_pair() -> None:
    fields, rows = read_csv(QA)
    hits = [row for row in rows if row.get("municipality_id") == MID]
    if len(hits) != 1:
        raise ValueError(f"expected one canonical QA row for {MID}, got {len(hits)}")
    hits[0]["確認日"] = CHECKED
    write_csv(QA, fields, rows)
    canonical_row = dict(hits[0])
    batch_fields, batch_rows = read_csv(BATCH_QA)
    if batch_fields != fields:
        raise ValueError("batch_05 QA schema differs from canonical QA")
    count = 0
    for i, row in enumerate(batch_rows):
        if row.get("municipality_id") == MID:
            batch_rows[i] = dict(canonical_row)
            count += 1
    if count != 1:
        raise ValueError(f"expected one batch_05 QA row for {MID}, got {count}")
    write_csv(BATCH_QA, batch_fields, batch_rows)

def validate_review(path: Path, expected_items: set[str]) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    _, rows = read_csv(path)
    if not rows or any(row.get("municipality_id") != MID for row in rows):
        raise ValueError(f"invalid M050 review: {path}")
    if any(row.get("branch_review_status") != "COMPLETE" for row in rows):
        raise ValueError(f"incomplete M050 review branch: {path}")
    by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_item[row["internal_item_id"]].append(row)
    if set(by_item) != expected_items:
        raise ValueError(f"unexpected item set in {path}: {sorted(by_item)}")
    scoring: dict[str, dict[str, str]] = {}
    for iid, item_rows in by_item.items():
        hits = [row for row in item_rows if row.get("scoring_branch") == "TRUE"]
        if len(hits) != 1:
            raise ValueError(f"{MID}/{iid} must have exactly one scoring branch")
        scoring[iid] = hits[0]
    return rows, scoring

def update_priority() -> None:
    fields, rows = read_csv(PRIORITY)
    hits = 0
    for row in rows:
        if row.get("municipality_id") != MID:
            continue
        row["implementation_status"] = "IMPLEMENTED"
        row["readiness_status_snapshot"] = "LESSON_READY_10"
        row["checked_date"] = CHECKED
        row["note"] = "固定10品目LESSON_READY_10。C017-S05をroutingのみ有効化。補助5品目はreview完了だが15問Gateへは未接続。2026年10月電池類変更は施行前として別根拠保持。"
        hits += 1
    if hits != 1:
        raise ValueError(f"expected one priority row for {MID}, got {hits}")
    write_csv(PRIORITY, fields, rows)

def update_company() -> None:
    fields, rows = read_csv(COMPANY)
    hits = 0
    for row in rows:
        if row.get("company_id") == "C017" and row.get("site_id") == "C017-S05" and row.get("municipality_id") == MID:
            row["active"] = "TRUE"
            row["checked_date"] = CHECKED
            row["identity_resolution_note"] = (
                "公式営業拠点一覧で確認した斐川営業所の出雲市所在地をrouting metadataとして採用。"
                "M050はLESSON_READY_10整備済みのため固定10問を利用可能。会社所在地は居住地・家庭ごみ正答の根拠ではない。"
            )
            hits += 1
    if hits != 1:
        raise ValueError(f"expected one M050 C017-S05 site, got {hits}")
    write_csv(COMPANY, fields, rows)

def build() -> None:
    fixed_rows, scoring = validate_review(REVIEW, FIXED_10)
    validate_review(SUPPLEMENTAL_REVIEW, SUPPLEMENTAL_5)
    upsert_sources(SOURCES_MASTER)
    upsert_sources(BATCH_SOURCES)
    upsert_alt_category(CATEGORIES_MASTER)
    upsert_alt_category(BATCH_CATEGORIES)
    sync_category_review_pair()
    sync_qa_pair()

    scope_fields, scope_existing = read_csv(SCOPE)
    if scope_fields != SCOPE_FIELDS:
        raise ValueError(f"unexpected schema for {SCOPE}: {scope_fields}")
    scope_rows = [row for row in scope_existing if row.get("municipality_id") != MID]
    scope_rows.append({
        "municipality_id": MID, "municipality_name": NAME, "lesson_mode": "ONLINE_CLASS",
        "scoring_status": "LESSON_READY_10", "required_item_count": "10",
        "required_branch_count": str(len(fixed_rows)),
        "review_source": "data/research/lesson_readiness/m050_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "固定10品目の画像採点枝をCOMPLETE。モバイルバッテリーは画像のみで分岐確定不能のため回収・確認へ安全投影。補助5はreview済みだが15問Gate未接続。APP_READYには昇格しない。",
    })
    write_csv(SCOPE, scope_fields, sorted(scope_rows, key=lambda row: row["municipality_id"]))

    boxes: list[dict[str, str]] = []
    for order, (cid, label, kind) in enumerate(ONLINE_SPEC, 1):
        boxes.append({
            "municipality_id": MID, "teaching_box_id": f"TB-{MID}-ON-{order:02d}",
            "class_mode": "ONLINE_CLASS", "box_kind": kind, "category_id": cid,
            "display_name": label, "display_order": str(order),
            "note": "固定10品目採点用。詳細条件・例外は教師用reviewに保持。",
            "style_source_category_ids": cid if kind == "FIXED_10_SCORING" else "",
            "style_district_scope": "MUNICIPALITY_WIDE" if kind == "FIXED_10_SCORING" else "",
        })
    for order, (cid, label) in enumerate(IN_PERSON_SPEC, 1):
        boxes.append({
            "municipality_id": MID, "teaching_box_id": f"TB-{MID}-IP-{order:02d}",
            "class_mode": "IN_PERSON_CLASS", "box_kind": "MAJOR_CATEGORY", "category_id": cid,
            "display_name": label, "display_order": str(order),
            "note": "対面授業用の主要分別箱。特殊回収経路と粗大ごみは実物仕分け箱から除外。",
            "style_source_category_ids": cid, "style_district_scope": "MUNICIPALITY_WIDE",
        })
    replace_mid(BOXES, BOX_FIELDS, boxes)

    online_box_by_category = {row["category_id"]: row for row in boxes if row["class_mode"] == "ONLINE_CLASS"}
    projection: list[dict[str, str]] = []
    for iid in sorted(scoring):
        row = scoring[iid]
        cid = row["category_id"]
        box = online_box_by_category.get(cid)
        if not box:
            raise ValueError(f"no M050 online teaching box for {iid}/{cid}")
        projection.append({
            "municipality_id": MID, "internal_item_id": iid, "teaching_box_id": box["teaching_box_id"],
            "projection_kind": "SIMPLIFIED_ACTION" if iid == "I029" else "OFFICIAL_CATEGORY",
            "category_id": cid, "review_status": "COMPLETE",
            "note": "モバイルバッテリーは状態確認が必要なため回収・確認へ投影。" if iid == "I029"
                    else "公式分別区分へ投影。詳細条件・例外は教師用reviewに保持。",
        })
    replace_mid(PROJECTION, PROJECTION_FIELDS, projection)

    _, variants = read_csv(VARIANTS)
    if any(row.get("municipality_id") == MID for row in variants):
        raise ValueError("M050 must not receive a learner regional variant; current differences are collection schedule only")

    update_priority()
    update_company()
    print(
        f"M050_LESSON_READY_BUILT fixed_items={len(scoring)} fixed_branches={len(fixed_rows)} "
        f"supplemental_reviewed=5 online_boxes={len(ONLINE_SPEC)} in_person_boxes={len(IN_PERSON_SPEC)} sites=1"
    )

if __name__ == "__main__":
    build()
