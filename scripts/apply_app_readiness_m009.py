#!/usr/bin/env python3
"""Promote Oe Town (M009) to full 40-item APP_READY from the current official guide."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from schema_v12 import (
    CATEGORY_FIELDS, CATEGORY_REVIEW_EVIDENCE_FIELDS, COVERAGE_FIELDS, MAPPING_FIELDS,
    MUNICIPALITY_FIELDS, QA_FIELDS, compute_qa, read_csv, sync_municipality_qa_status, write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data/research"
MASTER = ROOT / "data/master"
APP = ROOT / "data/app"
BATCH = RESEARCH / "batches/batch_01"
MID = "M009"
CHECKED = "2026-08-31"
REVIEWER = "OPENAI_M009_APP_READY_V1"
SOURCE_ID = "S-M009-02"
GUIDE_URL = "https://www.town.oe.yamagata.jp/files/original/202403191138227511fcddfbe.pdf"
AUDIT_PATH = RESEARCH / "app_readiness/m009_item_review.csv"
SCOPE_PATH = APP / "lesson_mode_app_ready_scope.csv"
IMAGE_PATH = APP / "item_image_mapping_pilot_top8.csv"
PRIORITY_PATH = MASTER / "07_implementation_priority.csv"
COMPANY_PATH = APP / "company_municipality_mapping.csv"
VARIANT_PATH = APP / "lesson_variant_groups.csv"

AUDIT_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "canonical_name", "display_name",
    "official_item_wording", "category_id", "category_name", "condition", "preparation",
    "exception_destination", "evidence_basis", "item_evidence_source_id", "item_evidence_url",
    "item_evidence_locator", "branch_review_status", "checked_date", "reviewer", "note",
]
IMAGE_FIELDS = [
    "pair_order", "municipality_id", "municipality_name", "internal_item_id", "canonical_name",
    "display_name", "review_status", "evidence_basis", "category_id", "category_name", "condition",
    "preparation", "exception_destination", "item_evidence_source_id", "item_evidence_url",
    "item_evidence_locator", "checked_date", "reviewer", "note",
]
IMAGE_ITEMS = ("I001", "I007", "I013", "I004", "I006", "I031", "I029", "I014", "I033", "I017")


@dataclass(frozen=True)
class Branch:
    category_id: str
    locator: str
    wording: str
    condition: str
    preparation: str
    exception: str
    basis: str = "DIRECT_ITEM"
    note: str = ""


def b(category_id: str, locator: str, wording: str, condition: str, preparation: str,
      exception: str, basis: str = "DIRECT_ITEM", note: str = "") -> Branch:
    return Branch(category_id, locator, wording, condition, preparation, exception, basis, note)


RULES: dict[str, list[Branch]] = {
    "I001": [b("C-M009-05", "P6・分別早見表『ペットボトル（認識マークあり）』", "ペットボトル", "PET認識マークのある飲料・酒類・しょうゆ用ボトル", "キャップとラベルを外し、中をすすぐ", "認識マークなしはもやせるごみ")],
    "I002": [b("C-M009-01", "P6・分別早見表『ペットボトル』注意事項", "ペットボトルのキャップ", "ペットボトルから外したプラスチック製キャップ", "本体から外してもやせるごみへ出す", "ペットボトル本体とは分ける")],
    "I003": [b("C-M009-01", "P6・分別早見表『ペットボトル』注意事項", "ペットボトルのラベル", "ペットボトルから外したラベル", "本体から外してもやせるごみへ出す", "ペットボトル本体とは分ける")],
    "I004": [b("C-M009-04", "分別早見表『缶（飲料・食料・調味料用）』", "アルミ缶", "飲料・食品用のアルミ缶", "中身を空にし、必要に応じすすぐ", "内側コーティング等の対象外缶はもやせないごみ")],
    "I005": [b("C-M009-04", "分別早見表『缶（飲料・食料・調味料用）』", "スチール缶", "飲料・食品用のスチール缶", "中身を空にし、必要に応じすすぐ", "内側コーティング等の対象外缶はもやせないごみ")],
    "I006": [b("C-M009-03", "分別早見表『びん（飲料・調味料用）』", "ガラスびん", "割れていない飲料・食品・調味料用びん", "キャップを外し、中をすすぐ", "割れたびん・ガラス製品はもやせないごみ")],
    "I007": [b("C-M009-01", "分別早見表 P23『食品トレイ（白色トレイ）』", "白色食品トレー", "白色の食品トレイ", "食品残渣を除いてもやせるごみへ出す", "洗浄して店頭回収への協力も可")],
    "I008": [b("C-M009-01", "分別早見表『食品トレイ（白色トレイ以外）』", "色柄食品トレー", "白色以外の食品トレイ", "食品残渣を除いてもやせるごみへ出す", "店頭回収の対象条件は回収先に従う")],
    "I009": [b("C-M009-01", "分別早見表『コンビニ弁当箱』", "弁当容器", "家庭から出るプラスチック製弁当容器", "中身を除いてもやせるごみへ出す", "汚れ・材質に応じて個別品目表を確認", "OFFICIAL_RULE_DERIVED")],
    "I010": [b("C-M009-01", "分別早見表 P18『菓子袋（紙・ビニール・プラスチック製）』", "お菓子の袋", "家庭から出る菓子袋", "中身を除いてもやせるごみへ出す", "金属製の容器は別区分")],
    "I011": [b("C-M009-01", "分別早見表 P18『買い物袋（レジ袋・エコバッグ）』", "レジ袋", "家庭から出るレジ袋", "中身を除いてもやせるごみへ出す", "材質が異なる大型品は個別品目表を確認")],
    "I012": [b("C-M009-01", "分別早見表『発泡スチロール』", "発泡スチロール", "家庭から出る発泡スチロール", "異物を除いてもやせるごみへ出す", "大型・特殊用途品は個別品目表を確認")],
    "I013": [b("C-M009-01", "分別早見表 P23『新聞紙』", "新聞", "新聞・折込広告", "まとめてもやせるごみへ出す", "資源回収への協力も可")],
    "I014": [b("C-M009-01", "分別早見表『段ボール』", "段ボール", "家庭から出る段ボール", "折りたたみ、もやせるごみとして出す", "資源回収への協力も可")],
    "I015": [b("C-M009-01", "分別早見表『雑誌類』", "雑誌", "家庭から出る雑誌", "まとめてもやせるごみへ出す", "資源回収への協力も可")],
    "I016": [b("C-M009-01", "分別早見表 P18『菓子箱（木製・紙製）』", "雑紙・菓子箱", "紙製の菓子箱・雑紙", "紙以外の異物を除いてもやせるごみへ出す", "資源回収可能な紙は地域回収も可", "OFFICIAL_RULE_DERIVED")],
    "I017": [b("C-M009-01", "分別早見表 P19『紙パック類』／P12店頭回収協力", "紙パック", "家庭から出る紙パック", "中身を除き、もやせるごみとして出す", "牛乳パック等は店頭回収への協力も可")],
    "I018": [b("C-M009-01", "分別早見表『生ごみ』／もやせるごみ", "生ごみ", "家庭から出る生ごみ", "水をよく切って指定袋へ入れる", "資源・不燃物を混ぜない")],
    "I019": [b("C-M009-01", "もやせるごみ『紙くず』／分別早見表", "使用済みティッシュ", "家庭から出る汚れたティッシュ等の紙くず", "もやせるごみの指定袋へ入れる", "資源化できる紙は地域回収を利用", "OFFICIAL_RULE_DERIVED")],
    "I020": [b("C-M009-01", "分別早見表 P19『紙おむつ』", "紙おむつ", "家庭から出る紙おむつ", "汚物をトイレで除去してもやせるごみへ出す", "衛生上、使用済み実物は教材に使用しない")],
    "I021": [b("C-M009-01", "分別早見表 P17『衣類』", "衣類", "家庭から出る衣類", "もやせるごみの指定袋へ入れる", "再使用・資源回収が可能な場合はそちらも可")],
    "I022": [b("C-M009-02", "分別早見表 P18『傘』", "傘", "家庭から出る傘", "先端を安全に扱い、もやせないごみへ出す", "袋に入らない大型品は品目表の粗大条件を確認")],
    "I023": [b("C-M009-02", "分別早見表『陶磁器製品』", "陶磁器", "茶わん等の陶磁器製品", "割れた部分は新聞・紙袋等で包み内容を表示", "資源びんには混ぜない")],
    "I024": [b("C-M009-02", "分別早見表 P19『ガラスコップ』", "ガラス製品", "コップ等のガラス製品", "割れた場合は新聞・紙袋等で包み内容を表示", "飲食用の対象びんは資源ごみ（びん類）")],
    "I025": [b("C-M009-02", "分別早見表 P19『ガラスくず（窓ガラス等）』", "割れたガラス", "割れたガラス・ガラスくず", "新聞・紙袋等で包み中身を袋に表示", "割れていない対象びんは資源ごみ（びん類）")],
    "I026": [b("C-M009-02", "分別早見表『包丁・刃物』", "包丁・刃物", "家庭用の包丁・刃物", "刃物部分を安全に保護してもやせないごみへ出す", "大型工具等は個別品目表を確認")],
    "I027": [b("C-M009-06", "P9『有害ごみ／乾電池』", "乾電池", "アルカリ・マンガン等の家庭用乾電池", "金属端子部を絶縁し、外袋二重又は透明袋に入れて指定日に出す", "鉛バッテリーはクリーンセンター受付不可")],
    "I028": [b("C-M009-06", "P9『乾電池』：ボタン電池を対象として明記", "ボタン電池", "家庭用ボタン電池", "金属端子部を絶縁し、外袋二重又は透明袋に入れて指定日に出す", "鉛バッテリーは対象外")],
    "I029": [b("C-M009-06", "P9『モバイルバッテリーも乾電池と一緒に出す』", "モバイルバッテリー", "家庭で使用したモバイルバッテリー", "金属端子部を絶縁し、乾電池と一緒に指定日に出す", "対象充電池は電器店のリサイクルボックスも利用可")],
    "I030": [b("C-M009-07", "分別早見表 P20『蛍光管』／水銀含有ごみ", "蛍光管", "家庭用の蛍光管・水銀使用製品", "破損しないよう保護して水銀含有ごみとして出す", "白熱・LED電球はもやせないごみ")],
    "I031": [b("C-M009-02", "分別早見表『電球（白熱・LED）』", "電球", "白熱電球・LED電球", "破損しないよう扱い、もやせないごみへ出す", "蛍光管は水銀含有ごみ")],
    "I032": [b("C-M009-02", "分別早見表『スプレー缶・カセットボンベ』", "スプレー缶", "家庭から出るスプレー缶・カセットボンベ", "中身を使い切り、穴をあけずにもやせないごみへ出す", "飲料缶等の資源缶とは分ける")],
    "I033": [b("C-M009-02", "分別早見表『ライター』", "使い捨てライター", "家庭から出る使い捨てライター", "燃料を使い切ってもやせないごみへ出す", "燃料が残る場合は無理に処理せず町・クリーンセンターへ確認")],
    "I034": [b("C-M009-02", "もやせないごみ『小型家電』／分別早見表（カメラ等）", "小型家電", "指定袋に入る家庭用小型家電", "取り外せる乾電池等は外し、もやせないごみへ出す", "袋に入らない大型品は粗大ごみ", "OFFICIAL_RULE_DERIVED")],
    "I035": [b("C-M009-02", "もやせないごみ『小型家電』＋P9充電池ルール", "充電池を外せない小型家電", "指定袋に入る充電池内蔵小型家電で破損・膨張等の異常がないもの", "無理に分解せず、本体をもやせないごみとして出す", "破損・膨張・発熱等がある場合は通常排出せず町・クリーンセンターへ確認", "OFFICIAL_RULE_DERIVED", "小型家電の通常区分と、取り外した充電池の乾電池区分から whole-device route を必要最小限に導出。")],
    "I036": [b("C-M009-08", "分別早見表 P17『羽毛布団（1枚）』『ウレタン敷布団（1枚）』", "布団", "家庭から出る布団1枚", "粗大ごみの申込・証紙ルールに従う", "品目・枚数に応じた粗大ごみ料金を確認")],
    "I037": [b("C-M009-09", "P8『家電4品目』：クリーンセンター受入不可", "家電4品目", "エアコン・テレビ・冷蔵庫/冷凍庫・洗濯機/衣類乾燥機", "町の通常収集・クリーンセンターへ出さず家電リサイクル法ルートを利用", "販売店・指定引取場所等へ")],
    "I038": [b("C-M009-10", "P9『パソコン』：家庭用PCはクリーンセンターへ直接搬入可", "家庭用パソコン", "家庭で使用したパソコン・対象モニター", "個人情報・データを消去してクリーンセンターへ直接搬入する", "メーカーへ直接申し込みリサイクルする方法も可")],
    "I039": [b("C-M009-01", "分別早見表 P18『固めた食用油』", "使用済み食用油", "家庭から出る使用済み食用油", "固化剤で固める等、漏れない状態にしてもやせるごみへ出す", "液体のまま指定袋へ入れない", "OFFICIAL_RULE_DERIVED")],
    "I040": [
        b("C-M009-01", "P1『枝木類』：長さ80cm以下・直径20cm以内", "剪定枝", "1本の太さ直径20cm以内・長さ80cm以下", "両側を丈夫なひもで結束してもやせるごみへ出す", "制限を超える樹木はクリーンセンター処理不可"),
        b("C-M009-09", "P12『樹木（制限を超える大きさのもの）』", "制限超過の樹木", "長さ・太さ等が町の受入制限を超える", "通常収集・クリーンセンターへ出さない", "販売店・専門業者へ処理を依頼"),
    ],
}


def pc_category() -> dict[str, str]:
    return {
        "municipality_id": MID, "category_id": "C-M009-10",
        "自治体正式名称": "家庭用パソコン（直接搬入）", "category_group": "特別搬入",
        "parent_category_id": "", "classification_level": "ALTERNATIVE", "表示順": "10",
        "collection_channel": "DIRECT_HAUL",
        "代表品目": "家庭で使用したデスクトップ・ノート・一体型パソコン、対象モニター",
        "入れてはいけない物": "事業所から出るパソコン・家電4品目",
        "適用条件": "不用になった家庭用パソコン",
        "条件外の扱い": "事業系は受付不可。家電4品目は家電リサイクル法ルート",
        "出す前の処理": "個人情報やデータを全て消去",
        "袋・容器のルール": "クリーンセンターへ直接搬入",
        "サイズ・条件": "家庭用に限る", "粗大ごみ扱いか": "FALSE",
        "予約が必要か": "FALSE", "有料か": "CONDITIONAL", "料金ルール": "施設の搬入条件に従う",
        "自治体収集外か": "FALSE",
        "注意事項": "メーカーへ直接申し込みリサイクルする方法も利用可",
        "source_id": SOURCE_ID, "出典URL": GUIDE_URL,
        "出典ページ・該当箇所": "P9 パソコン：家庭用パソコンはクリーンセンターへ直接搬入可能",
        "確認日": CHECKED, "ui_role": "REFERENCE_ONLY", "rule_status": "CURRENT",
        "effective_from": "", "effective_to": "",
    }


def update_category(row: dict[str, str]) -> dict[str, str]:
    row = dict(row)
    if row.get("municipality_id") != MID:
        return row
    row["確認日"] = CHECKED
    if row.get("category_id") == "C-M009-06":
        row.update({
            "代表品目": "アルカリ乾電池・マンガン乾電池・ニカド電池・ニッケル水素電池・リチウムイオン電池・ボタン電池・モバイルバッテリー",
            "入れてはいけない物": "鉛バッテリー・クリーンセンター対象外製品",
            "適用条件": "家庭用の対象電池・モバイルバッテリー",
            "条件外の扱い": "鉛バッテリー等は取扱店へ問い合わせ",
            "出す前の処理": "金属端子部を絶縁テープで絶縁",
            "袋・容器のルール": "指定ごみ袋の外袋を2枚重ねにした袋または透明袋",
            "出典ページ・該当箇所": "P9 有害ごみ・乾電池・モバイルバッテリー",
        })
    if row.get("category_id") == "C-M009-09":
        row["代表品目"] = "家電4品目・消火器・タイヤ・ガスボンベ・鉛バッテリー・廃油・農薬・建築廃材・医療廃棄物・制限超過樹木"
        row["注意事項"] = "家庭用パソコンはクリーンセンターへ直接搬入可能なため、この収集外区分には含めない"
    return row


def update_municipality(row: dict[str, str]) -> dict[str, str]:
    row = dict(row)
    if row.get("municipality_id") != MID:
        return row
    row["最終確認日"] = CHECKED
    row["備考"] = "令和8年度ページが現行案内する令和6年4月ガイドを40品目再監査。家庭用PCの直接搬入を独立特殊ルートとして反映。"
    row["reviewed_category_count"] = "9"
    row["category_count_basis"] = "現行ガイドP1〜15の分別章とP9家庭用パソコン直接搬入ルートを全件再監査。CURRENT非EXCLUDEDの公式葉区分は9。"
    row["category_count_verified"] = "TRUE"
    row["category_count_check_status"] = "MANUAL_INDEX_REVIEW"
    row["category_count_review_id"] = "CR-M009-CATEGORY-COVERAGE"
    row["category_count_reviewed_date"] = CHECKED
    row["category_count_reviewed_by"] = REVIEWER
    return row


def update_review_evidence(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [dict(r) for r in rows]
    found = False
    for row in rows:
        if row.get("review_evidence_id") == "CRE-M009-01":
            row["locator"] = "現行ガイドP1〜15の分別章＋P9家庭用パソコン直接搬入ルート"
            row["notes"] = "2026-08-31 category completeness再監査。PC直接搬入を公式特殊ルートとして追加。"
            found = True
    if not found:
        rows.append({
            "review_evidence_id": "CRE-M009-01", "review_id": "CR-M009-CATEGORY-COVERAGE",
            "municipality_id": MID, "source_id": SOURCE_ID,
            "locator": "現行ガイドP1〜15の分別章＋P9家庭用パソコン直接搬入ルート",
            "evidence_role": "PRIMARY_INDEX", "notes": "2026-08-31 category completeness再監査。",
        })
    return sorted(rows, key=lambda r: (r.get("municipality_id", ""), r.get("review_id", ""), r.get("review_evidence_id", "")))


def update_scope(branch_count: int) -> None:
    fields, rows = read_csv(SCOPE_PATH)
    rows = [r for r in rows if r.get("municipality_id") != MID]
    rows.append({
        "municipality_id": MID, "municipality_name": "大江町", "lesson_mode": "ONLINE_CLASS",
        "scoring_status": "APP_READY", "required_item_count": "40", "required_branch_count": str(branch_count),
        "review_source": "data/research/app_readiness/m009_item_review.csv",
        "image_mapping_source": "data/app/item_image_mapping_pilot_top8.csv",
        "note": "40品目全条件枝COMPLETE。店頭回収・直接搬入は内部根拠に保持し、固定10は町の通常分別区分で採点。",
    })
    write_csv(SCOPE_PATH, fields, sorted(rows, key=lambda r: r["municipality_id"]))


def update_priority_company() -> None:
    fields, rows = read_csv(PRIORITY_PATH)
    for row in rows:
        if row.get("municipality_id") == MID:
            row["implementation_status"] = "IMPLEMENTED"
            row["readiness_status_snapshot"] = "APP_READY"
            row["checked_date"] = CHECKED
            row["note"] = "40品目APP_READY。会社紐付けはrouting metadataのみ。"
    write_csv(PRIORITY_PATH, fields, rows)
    fields, rows = read_csv(COMPANY_PATH)
    for row in rows:
        if row.get("company_id") == "C011" and row.get("municipality_id") == MID:
            row["active"] = "TRUE"
    write_csv(COMPANY_PATH, fields, rows)


def write_images(item_by: dict[str, dict[str, str]], category_by: dict[tuple[str, str], dict[str, str]], source: dict[str, str]) -> None:
    fields, rows = read_csv(IMAGE_PATH)
    if fields != IMAGE_FIELDS:
        raise ValueError("image mapping header mismatch")
    rows = [r for r in rows if r.get("municipality_id") != MID]
    for iid in IMAGE_ITEMS:
        spec = RULES[iid][0]
        item = item_by[iid]
        category = category_by[(MID, spec.category_id)]
        rows.append({
            "pair_order": "", "municipality_id": MID, "municipality_name": "大江町",
            "internal_item_id": iid, "canonical_name": item["一般管理用名称"], "display_name": item["教材表示名"],
            "review_status": "VERIFIED", "evidence_basis": spec.basis, "category_id": spec.category_id,
            "category_name": category["自治体正式名称"], "condition": spec.condition,
            "preparation": spec.preparation, "exception_destination": spec.exception,
            "item_evidence_source_id": SOURCE_ID, "item_evidence_url": source["公式URL"],
            "item_evidence_locator": spec.locator, "checked_date": CHECKED, "reviewer": REVIEWER,
            "note": "M009 APP_READY reviewの固定10通常状態を採用。店頭回収等の任意ルートは正答を置き換えない。",
        })
    for order, row in enumerate(rows, start=1):
        row["pair_order"] = str(order)
    write_csv(IMAGE_PATH, fields, rows)


def main() -> None:
    expected = {f"I{i:03d}" for i in range(1, 41)}
    if set(RULES) != expected or any(not RULES[iid] for iid in expected):
        raise ValueError("M009 rules must cover exact 40 items")

    _, items = read_csv(MASTER / "04_common_items_master.csv")
    item_by = {r["internal_item_id"]: r for r in items}
    _, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, qa = read_csv(RESEARCH / "06_qa_log.csv")
    _, review_evidence = read_csv(RESEARCH / "08_category_review_evidence.csv")
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")

    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    source = source_by[(MID, SOURCE_ID)]
    if source.get("official_verified") != "TRUE" or source.get("公式URL") != GUIDE_URL:
        raise ValueError("M009 current official guide source missing")

    category_by = {(r["municipality_id"], r["category_id"]): update_category(r) for r in categories}
    category_by[(MID, "C-M009-10")] = pc_category()
    categories = sorted(category_by.values(), key=lambda r: (r["municipality_id"], r["category_id"]))
    category_by = {(r["municipality_id"], r["category_id"]): r for r in categories}
    municipalities = [update_municipality(r) for r in municipalities]
    review_evidence = update_review_evidence(review_evidence)

    existing_by_item: dict[str, list[dict[str, str]]] = {}
    for row in mappings:
        if row.get("municipality_id") == MID:
            existing_by_item.setdefault(row["internal_item_id"], []).append(row)
    for value in existing_by_item.values():
        value.sort(key=lambda r: (int(r.get("branch_order") or 0), r["mapping_id"]))
    retained = [r for r in mappings if r.get("municipality_id") != MID]
    used_ids = {r["mapping_id"] for r in retained}
    generated: list[dict[str, str]] = []
    audit: list[dict[str, str]] = []

    for iid in sorted(expected):
        old_rows = existing_by_item.get(iid, [])
        for order, spec in enumerate(RULES[iid], start=1):
            category = category_by[(MID, spec.category_id)]
            mapping_id = old_rows[order - 1]["mapping_id"] if order <= len(old_rows) else f"MAP-{MID}-{iid}-APP-{order:02d}"
            if mapping_id in used_ids:
                mapping_id = f"MAP-{MID}-{iid}-APP-{order:02d}"
            if mapping_id in used_ids:
                raise ValueError(f"duplicate mapping id {mapping_id}")
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
                "item_evidence_source_id": SOURCE_ID, "item_evidence_url": source["公式URL"],
                "item_evidence_locator": spec.locator, "確認日": CHECKED,
                "mapping_status": "APP_READY", "evidence_scope": "ITEM_SPECIFIC",
                "branch_review_status": "COMPLETE", "reviewed_date": CHECKED, "reviewed_by": REVIEWER,
                "備考": (f"M009 40品目APP_READY手動レビュー。{spec.basis}。{spec.note}").strip(),
            })
            generated.append(mapping)
            item = item_by[iid]
            audit.append({
                "municipality_id": MID, "internal_item_id": iid, "branch_order": str(order),
                "canonical_name": item["一般管理用名称"], "display_name": item["教材表示名"],
                "official_item_wording": spec.wording, "category_id": spec.category_id,
                "category_name": category["自治体正式名称"], "condition": spec.condition,
                "preparation": spec.preparation, "exception_destination": spec.exception,
                "evidence_basis": spec.basis, "item_evidence_source_id": SOURCE_ID,
                "item_evidence_url": source["公式URL"], "item_evidence_locator": spec.locator,
                "branch_review_status": "COMPLETE", "checked_date": CHECKED, "reviewer": REVIEWER,
                "note": spec.note or "現行公式ガイドの品目行・分別ルールを照合。",
            })

    mappings = sorted(retained + generated, key=lambda r: (r["municipality_id"], r["internal_item_id"], int(r.get("branch_order") or 0), r["mapping_id"]))
    coverage_by = {(r["municipality_id"], r["internal_item_id"]): dict(r) for r in coverage}
    for iid in sorted(expected):
        row = coverage_by.get((MID, iid), {field: "" for field in COVERAGE_FIELDS})
        first = RULES[iid][0]
        row.update({
            "municipality_id": MID, "internal_item_id": iid, "coverage_status": "APP_READY",
            "mapping_branch_count": str(len(RULES[iid])), "branch_completeness_confirmed": "TRUE",
            "evidence_scope": "ITEM_SPECIFIC", "item_evidence_source_id": SOURCE_ID,
            "item_evidence_url": source["公式URL"], "item_evidence_locator": first.locator,
            "reviewed_date": CHECKED, "reviewed_by": REVIEWER,
            "notes": "M009全40品目の必要条件枝を令和8年度現行案内の公式ガイドへ照合しatomic APP_READY昇格。",
        })
        coverage_by[(MID, iid)] = row
    coverage = sorted(coverage_by.values(), key=lambda r: (r["municipality_id"], r["internal_item_id"]))

    _, batch_municipalities = read_csv(BATCH / "batch_01_municipalities.csv")
    _, batch_categories = read_csv(BATCH / "batch_01_categories.csv")
    _, batch_sources = read_csv(BATCH / "batch_01_sources.csv")
    _, batch_qa = read_csv(BATCH / "batch_01_qa.csv")
    _, batch_review = read_csv(BATCH / "batch_01_category_review_evidence.csv")
    batch_category_by = {(r["municipality_id"], r["category_id"]): update_category(r) for r in batch_categories}
    batch_category_by[(MID, "C-M009-10")] = pc_category()
    batch_categories = sorted(batch_category_by.values(), key=lambda r: (r["municipality_id"], r["category_id"]))
    batch_municipalities = [update_municipality(r) for r in batch_municipalities]
    batch_review = update_review_evidence(batch_review)

    qa = compute_qa(municipalities, categories, sources, review_evidence, qa)
    municipalities = sync_municipality_qa_status(municipalities, qa)
    batch_qa = compute_qa(batch_municipalities, batch_categories, batch_sources, batch_review, batch_qa)
    batch_municipalities = sync_municipality_qa_status(batch_municipalities, batch_qa)

    write_csv(RESEARCH / "02_categories_master.csv", CATEGORY_FIELDS, categories)
    write_csv(RESEARCH / "04_municipalities_research.csv", MUNICIPALITY_FIELDS, municipalities)
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    write_csv(RESEARCH / "06_qa_log.csv", QA_FIELDS, qa)
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", COVERAGE_FIELDS, coverage)
    write_csv(RESEARCH / "08_category_review_evidence.csv", CATEGORY_REVIEW_EVIDENCE_FIELDS, review_evidence)
    write_csv(AUDIT_PATH, AUDIT_FIELDS, audit)
    write_csv(BATCH / "batch_01_municipalities.csv", MUNICIPALITY_FIELDS, batch_municipalities)
    write_csv(BATCH / "batch_01_categories.csv", CATEGORY_FIELDS, batch_categories)
    write_csv(BATCH / "batch_01_qa.csv", QA_FIELDS, batch_qa)
    write_csv(BATCH / "batch_01_category_review_evidence.csv", CATEGORY_REVIEW_EVIDENCE_FIELDS, batch_review)

    update_scope(len(generated))
    update_priority_company()
    write_images(item_by, category_by, source)
    _, variants = read_csv(VARIANT_PATH)
    if any(r.get("municipality_id") == MID for r in variants):
        raise ValueError("M009 must not receive a learner regional variant")
    print(f"M009_APP_READY_APPLIED items=40 branches={len(generated)} current_category_leaves=9 image_pairs=10")


if __name__ == "__main__":
    main()
