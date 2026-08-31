#!/usr/bin/env python3
"""Promote Hatsukaichi City (M105) from LESSON_READY_10 to complete 40-item APP_READY.

The existing ten-item lesson review remains the authoritative source for its reviewed
branches.  This script adds the remaining thirty common items from the current R8
official 50-on table and current special-disposal pages, then performs an atomic
40-item canonical replacement following the existing M094/M095/M104 APP_READY model.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from schema_v12 import (
    CATEGORY_FIELDS, COVERAGE_FIELDS, MAPPING_FIELDS, MUNICIPALITY_FIELDS,
    QA_FIELDS, SOURCE_FIELDS, compute_qa, read_csv, sync_municipality_qa_status,
    write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data/research"
MASTER = ROOT / "data/master"
APP = ROOT / "data/app"
MID = "M105"
CHECKED = "2026-08-31"
REVIEWER = "OPENAI_M105_APP_READY_V1"
LESSON_REVIEW = RESEARCH / "lesson_readiness/m105_item_review.csv"
AUDIT_PATH = RESEARCH / "app_readiness/m105_item_review.csv"
SCOPE_PATH = APP / "lesson_mode_app_ready_scope.csv"
PRIORITY_PATH = MASTER / "07_implementation_priority.csv"
COMPANY_PATH = APP / "company_municipality_mapping.csv"

AUDIT_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "canonical_name",
    "display_name", "official_item_wording", "category_id", "category_name",
    "condition", "preparation", "exception_destination", "evidence_basis",
    "item_evidence_source_id", "item_evidence_url", "item_evidence_locator",
    "branch_review_status", "checked_date", "reviewer", "note",
]

TABLE_URL = "https://www.city.hatsukaichi.hiroshima.jp/soshiki/31/78355.html"
BATTERY_URL = "https://www.city.hatsukaichi.hiroshima.jp/soshiki/31/128679.html"
EXCLUDED_URL = "https://www.city.hatsukaichi.hiroshima.jp/soshiki/31/12524.html"
SPRAY_URL = "https://www.city.hatsukaichi.hiroshima.jp/soshiki/31/128930.html"


@dataclass(frozen=True)
class Branch:
    category_id: str
    source_id: str
    locator: str
    wording: str
    condition: str = ""
    preparation: str = ""
    exception: str = ""
    basis: str = "DIRECT_ITEM"
    note: str = ""


def b(category_id: str, source_id: str, locator: str, wording: str,
      condition: str = "", preparation: str = "", exception: str = "",
      basis: str = "DIRECT_ITEM", note: str = "") -> Branch:
    return Branch(category_id, source_id, locator, wording, condition, preparation, exception, basis, note)


EXTRA: dict[str, list[Branch]] = {
    "I002": [b("C-M105-01", "IS-M105-04", "分別50音表：ペットボトルのキャップ・ラベルは燃やせるごみ", "ペットボトルのキャップ", preparation="本体から外す")],
    "I003": [b("C-M105-01", "IS-M105-04", "分別50音表：ペットボトルのキャップ・ラベルは燃やせるごみ", "ペットボトルのラベル", preparation="本体から外す")],
    "I005": [b("C-M105-03", "IS-M105-04", "分別50音表 No.132『スチール缶（飲料缶、かんづめ缶）』", "スチール缶（飲料缶、かんづめ缶）", preparation="中を洗う")],
    "I008": [b("C-M105-01", "IS-M105-04", "分別50音表 No.242『食品トレイ（白色の発泡スチロール製以外）』", "食品トレイ（白色以外）")],
    "I009": [b("C-M105-01", "IS-M105-04", "分別50音表：食品包装用のプラスチック容器は限定7品目外を燃やせるごみとして扱う", "弁当容器", preparation="食品残渣を除く", basis="OFFICIAL_RULE_DERIVED", note="共通品目『弁当容器』は限定7品目の資源容器に含まれない一般的な食品用プラスチック容器として判定。")],
    "I010": [b("C-M105-01", "IS-M105-04", "分別50音表 No.87『菓子袋』", "菓子袋")],
    "I011": [
        b("C-M105-01", "IS-M105-04", "分別50音表 No.657『レジ袋』", "レジ袋", condition="長さ30cm未満", preparation="必要に応じ30cm未満に切る"),
        b("C-M105-09", "IS-M105-04", "分別50音表 No.657『レジ袋』のサイズ条件", "レジ袋", condition="長さ30cm以上", exception="大型ごみ"),
    ],
    "I012": [
        b("C-M105-01", "IS-M105-04", "分別50音表 No.452『発泡スチロール』", "発泡スチロール", condition="長さ30cm未満", preparation="30cm未満に切る"),
        b("C-M105-09", "IS-M105-04", "分別50音表 No.452『発泡スチロール』のサイズ条件", "発泡スチロール", condition="長さ30cm以上で切らない場合", exception="大型ごみ", basis="OFFICIAL_RULE_DERIVED"),
    ],
    "I015": [b("C-M105-05", "IS-M105-04", "分別50音表：雑誌・雑がみを資源ごみ(3)紙類として束ねる各品目行", "雑誌", preparation="紙類としてひもで束ねる", basis="OFFICIAL_RULE_DERIVED")],
    "I016": [
        b("C-M105-05", "IS-M105-04", "分別50音表 No.86『菓子の箱（紙製）』", "菓子の箱（紙製）", condition="資源化できる乾いた紙箱", preparation="たたんでひもで束ねる"),
        b("C-M105-01", "IS-M105-04", "分別50音表：汚れた紙・資源化できない紙は燃やせるごみ", "汚れた雑紙・紙箱", condition="汚れ・加工等で資源化できない", basis="OFFICIAL_RULE_DERIVED"),
    ],
    "I018": [b("C-M105-01", "IS-M105-04", "分別50音表 No.421『生ごみ』", "生ごみ", preparation="水分をよく切り、新聞紙などに包む")],
    "I019": [b("C-M105-01", "IS-M105-04", "分別50音表 No.102『紙くず』", "使用済みティッシュ", preparation="燃やせるごみとして出す", basis="OFFICIAL_RULE_DERIVED", note="ティッシュ固有行ではなく、使用済みティッシュを資源化できない紙くずとして判定。")],
    "I020": [b("C-M105-01", "IS-M105-04", "分別50音表 No.60『おむつ（紙）（布）』", "紙おむつ", preparation="白色指定袋（特例）に直接入れ『オムツ』と記入", exception="ペット用は特例対象外")],
    "I021": [
        b("C-M105-06", "IS-M105-04", "分別50音表 No.432『布類（衣服）』", "衣類", condition="資源化対象の衣服"),
        b("C-M105-01", "IS-M105-04", "分別50音表：布きれ・手袋等の資源対象外布製品", "資源対象外の布類", condition="布きれ等、資源ごみ(4)の対象外", preparation="30cm未満に切る", basis="OFFICIAL_RULE_DERIVED"),
    ],
    "I022": [
        b("C-M105-09", "IS-M105-04", "分別50音表 No.84『傘』", "傘", condition="長さ30cm以上"),
        b("C-M105-10", "IS-M105-04", "分別50音表 No.84『傘』", "傘", condition="長さ30cm未満", exception="小型および複雑ごみ"),
    ],
    "I023": [b("C-M105-08", "IS-M105-04", "分別50音表 No.398『陶磁器』", "陶磁器", preparation="割れて危険な場合は丈夫な紙などに包み『危険』と記入")],
    "I024": [b("C-M105-08", "IS-M105-04", "分別50音表 No.113『ガラス』", "ガラス製品", preparation="割れて危険な場合は丈夫な紙などに包み『危険』と記入")],
    "I025": [b("C-M105-08", "IS-M105-04", "分別50音表 No.113『ガラス』", "割れたガラス", preparation="丈夫な紙などに包み『危険』と記入")],
    "I026": [
        b("C-M105-10", "IS-M105-04", "分別50音表 No.573『包丁』", "包丁", condition="長さ30cm未満", preparation="丈夫な紙などに包み『危険』と記入"),
        b("C-M105-09", "IS-M105-04", "分別50音表 No.573『包丁』", "包丁", condition="長さ30cm以上", preparation="刃を安全に保護", exception="大型ごみ"),
    ],
    "I027": [b("C-M105-11", "IS-M105-04", "分別50音表 No.147『乾電池』", "乾電池", exception="市役所・各支所の使用済電池回収ボックスも利用可")],
    "I028": [b("C-M105-11", "IS-M105-04", "分別50音表 No.587『ボタン電池』", "ボタン電池", exception="市役所・各支所の使用済電池回収ボックスも利用可")],
    "I030": [b("C-M105-11", "IS-M105-04", "分別50音表 No.388『蛍光管』", "蛍光管", preparation="空ケースに入れる。ケースがなければそのまま又は新聞紙等で保護。複数は結束")],
    "I032": [b("C-M105-03", "IS-M105-07", "スプレー缶の捨て方：使い切り・穴あけ不要・資源ごみびんかん類", "スプレー缶", preparation="通気性のよい火気のない屋外で中身を使い切る。穴を開けない")],
    "I034": [
        b("C-M105-10", "IS-M105-04", "分別50音表：デジタルカメラ・電気カミソリ等の小型家電例", "小型家電", condition="長さ30cm未満", preparation="取り外せる電池は外して有害ごみへ", basis="OFFICIAL_RULE_DERIVED"),
        b("C-M105-09", "IS-M105-04", "分別50音表：小型家電各品目の30cm以上条件", "小型家電", condition="長さ30cm以上", exception="大型ごみ", basis="OFFICIAL_RULE_DERIVED"),
    ],
    "I035": [
        b("C-M105-10", "IS-M105-05", "『機器からリチウムイオン電池の取り外しが出来ない場合』", "充電池を外せない小型家電", condition="機器の長さ30cm未満・電池に異常なし", preparation="無理に電池を外さずそのまま排出", exception="小型家電回収ボックス又は宅配回収も利用可"),
        b("C-M105-09", "IS-M105-05", "『機器からリチウムイオン電池の取り外しが出来ない場合』", "充電池を外せない小型家電", condition="機器の長さ30cm以上・電池に異常なし", preparation="無理に電池を外さずそのまま排出", exception="大型ごみ"),
        b("C-M105-13", "IS-M105-05", "『リチウムイオン電池に異常がある場合』", "異常のある充電池内蔵機器", condition="破損・膨張・発熱など異常あり", preparation="ごみステーションや小型家電回収ボックスへ出さない", exception="処理施設へ直接持込", basis="DIRECT_ITEM", note="異常品は通常収集から外れるため収集しません参照区分へ投影。"),
    ],
    "I036": [
        b("C-M105-09", "IS-M105-04", "分別50音表：布団・寝具類の大型ごみ扱い", "布団", condition="折りたたみ・結束後の最長部30cm以上", basis="OFFICIAL_RULE_DERIVED"),
        b("C-M105-10", "IS-M105-04", "分別50音表：大型ごみを折りたたみ結束し30cm未満とした場合の小型および複雑ごみ規則", "布団", condition="1枚を折りたたみひもで縛り最長部30cm未満", exception="小型および複雑ごみ", basis="OFFICIAL_RULE_DERIVED"),
    ],
    "I037": [b("C-M105-12", "IS-M105-06", "市が処理しないごみ：特定家電製品", "家電4品目", preparation="市の通常収集へ出さない", exception="販売店・指定引取場所等の家電リサイクル法ルート")],
    "I038": [b("C-M105-13", "IS-M105-06", "市が処理しないごみ：家庭用パソコン", "家庭用パソコン", preparation="市の通常収集へ出さない", exception="メーカー・パソコン3R推進協会・連携宅配回収等")],
    "I039": [b("C-M105-01", "IS-M105-04", "分別50音表 No.377『天ぷら油』／No.7『油（食用油）』", "使用済み食用油", preparation="布や紙に染み込ませるか固化剤で固める")],
    "I040": [b("C-M105-07", "IS-M105-04", "分別50音表 No.46『枝（剪定枝）』", "剪定枝", condition="長さ1m以下・直径10cm以下", preparation="5kg以内に束ね、ひもで縛る", exception="条件を超える太い枝は要確認")],
}


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def source_row(source_id: str, title: str, url: str, used: str) -> dict[str, str]:
    return {
        "municipality_id": MID, "source_id": source_id, "資料名": title,
        "資料種別": "自治体公式Web", "公式URL": url, "発行主体": "廿日市市",
        "対象年度": "令和8年度／取得時点現行", "ページ更新日": "", "取得確認日": CHECKED,
        "使用した情報": used, "優先度": "1", "現行性": "CURRENT",
        "備考": "M105 40品目APP_READYの品目別公式根拠。", "official_verified": "TRUE",
        "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    }


NEW_SOURCES = [
    source_row("IS-M105-06", "市が処理・収集しないごみ", EXCLUDED_URL, "特定家電製品・家庭用パソコン・その他市収集外品の処理経路"),
    source_row("IS-M105-07", "スプレー缶の捨て方", SPRAY_URL, "スプレー缶は中身を使い切り穴を開けず資源ごみびん・かん類へ出す"),
]


def excluded_category(category_id: str, name: str, representative: str, source_id: str, locator: str) -> dict[str, str]:
    return {
        "municipality_id": MID, "category_id": category_id, "自治体正式名称": name,
        "category_group": name, "parent_category_id": "", "classification_level": "EXCLUDED",
        "表示順": category_id.rsplit("-", 1)[-1], "collection_channel": "NOT_COLLECTED",
        "代表品目": representative, "入れてはいけない物": "市の通常収集対象ごみ",
        "適用条件": "市が処理・収集しない指定品", "条件外の扱い": "品目ごとの通常区分",
        "出す前の処理": "指定された回収・処理経路を確認", "袋・容器のルール": "市指定袋へ入れない",
        "サイズ・条件": "", "粗大ごみ扱いか": "FALSE", "予約が必要か": "CONDITIONAL",
        "有料か": "CONDITIONAL", "料金ルール": "回収経路により異なる", "自治体収集外か": "TRUE",
        "注意事項": "通常のごみステーションへ出さず、市公式案内の処理経路を利用",
        "source_id": source_id, "出典URL": EXCLUDED_URL if source_id == "IS-M105-06" else BATTERY_URL,
        "出典ページ・該当箇所": locator, "確認日": CHECKED, "ui_role": "EXCLUDED_NOTICE",
        "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
    }


def lesson_branches() -> dict[str, list[Branch]]:
    grouped: dict[str, list[Branch]] = {}
    for row in csv_rows(LESSON_REVIEW):
        iid = row["internal_item_id"].strip()
        grouped.setdefault(iid, []).append(b(
            row["category_id"].strip(), row["item_evidence_source_id"].strip(),
            row["item_evidence_locator"].strip(), row["official_item_wording"].strip(),
            row["condition"].strip(), row["preparation"].strip(), row["exception_destination"].strip(),
            row["evidence_basis"].strip() or "DIRECT_ITEM", row["note"].strip(),
        ))
    return grouped


def update_small_csvs(branch_count: int) -> None:
    scope_fields, scope_rows = read_csv(SCOPE_PATH)
    for row in scope_rows:
        if row["municipality_id"] == MID:
            row.update({
                "scoring_status": "APP_READY", "required_item_count": "40",
                "required_branch_count": str(branch_count),
                "review_source": "data/research/app_readiness/m105_item_review.csv",
                "note": "40品目全条件枝COMPLETE。授業画像は既存固定10品目を使用し、自動正誤判定は画像固有mapping VERIFIEDの場合のみ有効。",
            })
    write_csv(SCOPE_PATH, scope_fields, scope_rows)

    priority_fields, priority_rows = read_csv(PRIORITY_PATH)
    for row in priority_rows:
        if row["municipality_id"] == MID:
            row["implementation_status"] = "IMPLEMENTED"
            row["readiness_status_snapshot"] = "APP_READY"
            row["checked_date"] = CHECKED
    write_csv(PRIORITY_PATH, priority_fields, priority_rows)

    company_fields, company_rows = read_csv(COMPANY_PATH)
    for row in company_rows:
        if row["company_id"] == "C003" and row["municipality_id"] == MID:
            row["active"] = "TRUE"
    write_csv(COMPANY_PATH, company_fields, company_rows)


def main() -> None:
    branches = lesson_branches()
    overlap = set(branches) & set(EXTRA)
    assert not overlap, f"duplicate fixed/extra items: {sorted(overlap)}"
    branches.update(EXTRA)
    expected = {f"I{i:03d}" for i in range(1, 41)}
    assert set(branches) == expected, (sorted(expected - set(branches)), sorted(set(branches) - expected))
    assert all(branches.values())

    _, items = read_csv(MASTER / "04_common_items_master.csv")
    _, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, qa = read_csv(RESEARCH / "06_qa_log.csv")
    _, review_evidence = read_csv(RESEARCH / "08_category_review_evidence.csv")
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")

    item_by = {row["internal_item_id"]: row for row in items}
    source_by = {(row["municipality_id"], row["source_id"]): row for row in sources}
    for row in NEW_SOURCES:
        source_by[(MID, row["source_id"])] = row
    sources = sorted(source_by.values(), key=lambda row: (row["municipality_id"], row["source_id"]))
    source_by = {(row["municipality_id"], row["source_id"]): row for row in sources}

    category_by = {(row["municipality_id"], row["category_id"]): row for row in categories}
    category_by[(MID, "C-M105-12")] = excluded_category(
        "C-M105-12", "特定家電製品", "エアコン・テレビ・冷蔵庫/冷凍庫・洗濯機/衣類乾燥機",
        "IS-M105-06", "市が処理しないごみ：特定家電製品",
    )
    category_by[(MID, "C-M105-13")] = excluded_category(
        "C-M105-13", "収集しません", "家庭用パソコン・異常のあるリチウムイオン電池等",
        "IS-M105-06", "市が処理・収集しないごみ／リチウムイオン電池の異常品案内",
    )
    categories = sorted(category_by.values(), key=lambda row: (row["municipality_id"], row["category_id"]))
    category_by = {(row["municipality_id"], row["category_id"]): row for row in categories}

    existing_by_item: dict[str, list[dict[str, str]]] = {}
    for row in mappings:
        if row["municipality_id"] == MID:
            existing_by_item.setdefault(row["internal_item_id"], []).append(row)
    for rows in existing_by_item.values():
        rows.sort(key=lambda row: (int(row.get("branch_order") or 0), row["mapping_id"]))

    retained = [row for row in mappings if row["municipality_id"] != MID]
    used_ids = {row["mapping_id"] for row in retained}
    generated = []
    audit = []

    for iid in sorted(expected):
        old_rows = existing_by_item.get(iid, [])
        for order, spec in enumerate(branches[iid], start=1):
            category = category_by[(MID, spec.category_id)]
            evidence = source_by[(MID, spec.source_id)]
            mapping_id = old_rows[order - 1]["mapping_id"] if order <= len(old_rows) else f"MAP-{MID}-{iid}-APP-{order:02d}"
            if mapping_id in used_ids:
                mapping_id = f"MAP-{MID}-{iid}-APP-{order:02d}"
            assert mapping_id not in used_ids
            used_ids.add(mapping_id)
            mapping = {field: "" for field in MAPPING_FIELDS}
            mapping.update({
                "mapping_id": mapping_id, "municipality_id": MID, "internal_item_id": iid,
                "branch_order": str(order), "自治体での品目表記": spec.wording,
                "category_id": spec.category_id, "分別区分正式名称": category["自治体正式名称"],
                "条件": spec.condition, "前処理": spec.preparation, "例外分別先": spec.exception,
                "自治体収集外": category["自治体収集外か"], "rule_status": category["rule_status"],
                "effective_from": category["effective_from"], "effective_to": category["effective_to"],
                "category_source_id": category["source_id"], "category_source_url": category["出典URL"],
                "category_source_locator": category["出典ページ・該当箇所"],
                "item_evidence_source_id": spec.source_id, "item_evidence_url": evidence["公式URL"],
                "item_evidence_locator": spec.locator, "確認日": CHECKED,
                "mapping_status": "APP_READY", "evidence_scope": "ITEM_SPECIFIC",
                "branch_review_status": "COMPLETE", "reviewed_date": CHECKED, "reviewed_by": REVIEWER,
                "備考": (f"M105 40品目APP_READY手動レビュー。{spec.basis}。 " + spec.note).strip(),
            })
            generated.append(mapping)
            item = item_by[iid]
            audit.append({
                "municipality_id": MID, "internal_item_id": iid, "branch_order": str(order),
                "canonical_name": item["一般管理用名称"], "display_name": item["教材表示名"],
                "official_item_wording": spec.wording, "category_id": spec.category_id,
                "category_name": category["自治体正式名称"], "condition": spec.condition,
                "preparation": spec.preparation, "exception_destination": spec.exception,
                "evidence_basis": spec.basis, "item_evidence_source_id": spec.source_id,
                "item_evidence_url": evidence["公式URL"], "item_evidence_locator": spec.locator,
                "branch_review_status": "COMPLETE", "checked_date": CHECKED, "reviewer": REVIEWER,
                "note": spec.note or "公式品目行または公式区分ルールと条件を照合。",
            })

    mappings = sorted(retained + generated, key=lambda row: (
        row["municipality_id"], row["internal_item_id"], int(row.get("branch_order") or 0), row["mapping_id"]
    ))
    coverage_by = {(row["municipality_id"], row["internal_item_id"]): row for row in coverage}
    for iid in sorted(expected):
        first = branches[iid][0]
        evidence = source_by[(MID, first.source_id)]
        coverage_by[(MID, iid)].update({
            "coverage_status": "APP_READY", "mapping_branch_count": str(len(branches[iid])),
            "branch_completeness_confirmed": "TRUE", "evidence_scope": "ITEM_SPECIFIC",
            "item_evidence_source_id": first.source_id, "item_evidence_url": evidence["公式URL"],
            "item_evidence_locator": first.locator, "reviewed_date": CHECKED, "reviewed_by": REVIEWER,
            "notes": "M105全40品目の必要条件枝を現行公式資料へ照合しatomic APP_READY昇格。",
        })
    coverage = sorted(coverage_by.values(), key=lambda row: (row["municipality_id"], row["internal_item_id"]))

    # Keep Batch 11's source/category/QA bundle aligned with canonical additions.
    batch = RESEARCH / "batches/batch_11"
    _, batch_municipalities = read_csv(batch / "batch_11_municipalities.csv")
    _, batch_categories = read_csv(batch / "batch_11_categories.csv")
    _, batch_sources = read_csv(batch / "batch_11_sources.csv")
    _, batch_qa = read_csv(batch / "batch_11_qa.csv")
    _, batch_review_evidence = read_csv(batch / "batch_11_category_review_evidence.csv")
    batch_category_by = {(row["municipality_id"], row["category_id"]): row for row in batch_categories}
    for cid in ("C-M105-12", "C-M105-13"):
        batch_category_by[(MID, cid)] = category_by[(MID, cid)]
    batch_categories = sorted(batch_category_by.values(), key=lambda row: (row["municipality_id"], row["category_id"]))
    batch_source_by = {(row["municipality_id"], row["source_id"]): row for row in batch_sources}
    for row in NEW_SOURCES:
        batch_source_by[(MID, row["source_id"])] = row
    batch_sources = sorted(batch_source_by.values(), key=lambda row: (row["municipality_id"], row["source_id"]))

    qa = compute_qa(municipalities, categories, sources, review_evidence, qa)
    municipalities = sync_municipality_qa_status(municipalities, qa)
    batch_qa = compute_qa(batch_municipalities, batch_categories, batch_sources, batch_review_evidence, batch_qa)
    batch_municipalities = sync_municipality_qa_status(batch_municipalities, batch_qa)

    write_csv(RESEARCH / "02_categories_master.csv", CATEGORY_FIELDS, categories)
    write_csv(RESEARCH / "03_sources_master.csv", SOURCE_FIELDS, sources)
    write_csv(RESEARCH / "04_municipalities_research.csv", MUNICIPALITY_FIELDS, municipalities)
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    write_csv(RESEARCH / "06_qa_log.csv", QA_FIELDS, qa)
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", COVERAGE_FIELDS, coverage)
    write_csv(AUDIT_PATH, AUDIT_FIELDS, audit)
    write_csv(batch / "batch_11_municipalities.csv", MUNICIPALITY_FIELDS, batch_municipalities)
    write_csv(batch / "batch_11_categories.csv", CATEGORY_FIELDS, batch_categories)
    write_csv(batch / "batch_11_sources.csv", SOURCE_FIELDS, batch_sources)
    write_csv(batch / "batch_11_qa.csv", QA_FIELDS, batch_qa)

    update_small_csvs(len(generated))
    print(f"M105_APP_READY_APPLIED items=40 branches={len(generated)} sources_added=2 excluded_categories=2")


if __name__ == "__main__":
    main()
