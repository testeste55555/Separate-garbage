#!/usr/bin/env python3
"""Production adversarial checks for Batch 13 resident-facing authenticity."""
from __future__ import annotations

from collections import Counter

from schema_v12 import MASTER, RESEARCH, counted_category_total, read_csv
from validation_v12 import CATEGORY_DETAIL_FIELDS, is_placeholder_category_value, validate_dataset

TARGETS = {"M126","M128","M129","M130","M131","M132","M133","M134","M135"}
EXPECTED = {"M126":10,"M128":11,"M129":12,"M130":12,"M131":11,"M132":12,"M133":12,"M134":12,"M135":5}


def main() -> int:
    b = RESEARCH / "batches" / "batch_13"
    p = "batch_13_"
    paths = {
        "municipality_path": b/f"{p}municipalities.csv", "category_path": b/f"{p}categories.csv",
        "source_path": b/f"{p}sources.csv", "qa_path": b/f"{p}qa.csv",
        "mapping_path": b/f"{p}item_mapping.csv", "coverage_path": b/f"{p}item_coverage.csv",
        "review_evidence_path": b/f"{p}category_review_evidence.csv",
    }
    errors, _, _ = validate_dataset(label="BATCH_13", **paths)
    _, munis = read_csv(paths["municipality_path"])
    _, cats = read_csv(paths["category_path"])
    _, qa = read_csv(paths["qa_path"])
    _, cov = read_csv(paths["coverage_path"])
    _, evidence = read_csv(paths["review_evidence_path"])
    _, deferred = read_csv(MASTER / "05_deferred_municipalities.csv")

    by = {r["municipality_id"]: r for r in munis}
    q = {r["municipality_id"]: r for r in qa}
    evc = Counter(r["municipality_id"] for r in evidence)
    current = [r for r in cats if r.get("rule_status") == "CURRENT"]
    names = {mid: {r["自治体正式名称"] for r in current if r["municipality_id"] == mid} for mid in TARGETS}
    rows = {(r["municipality_id"], r["自治体正式名称"]): r for r in current}
    children = Counter(r.get("parent_category_id", "") for r in current if r.get("parent_category_id"))
    deferred_by = {r["municipality_id"]: r for r in deferred}

    checks: list[tuple[str, bool, str]] = []
    checks.append(("structural validation passes", not errors, f"errors={len(errors)} {errors[:5]}"))
    checks.append(("exact active Batch 13 target set", set(by) == TARGETS, str(sorted(by))))
    checks.append(("all nine active municipalities QA_PASSED", all(q[mid]["確認ステータス"] == "QA_PASSED" for mid in TARGETS), ""))
    checks.append(("official leaf counts match reviewed design", all(counted_category_total(mid, cats) == EXPECTED[mid] for mid in TARGETS), str({mid: counted_category_total(mid, cats) for mid in sorted(TARGETS)})))
    checks.append(("all counts use MANUAL_INDEX_REVIEW", all(by[mid]["category_count_check_status"] == "MANUAL_INDEX_REVIEW" and not by[mid]["official_category_count"] for mid in TARGETS), ""))
    checks.append(("all municipalities have formal review evidence", all(evc[mid] >= 1 for mid in TARGETS), str(evc)))

    mine = deferred_by.get("M127", {})
    checks.append(("M127 Mine is regional-variant DEFERRED", mine.get("status") == "DEFERRED" and mine.get("decision_source") == "SCHEMA_SCOPE_LIMITATION" and all(token in mine.get("reason", "") for token in ["美祢地域","美東地域","秋芳地域"]), mine.get("reason", "")))

    # M126 柳井市
    b126 = rows[("M126", "ビン・乾電池")]
    p126 = rows[("M126", "ペットボトル・古紙")]
    checks.append(("M126 bottle/battery heading resolves to two separate leaves", children[b126["category_id"]] == 2 and {"ガラスビン","乾電池"}.issubset(names["M126"]), ""))
    checks.append(("M126 PET/old-paper heading resolves to four leaves", children[p126["category_id"]] == 4 and {"ペットボトル","新聞・チラシ","段ボール","雑誌・本・その他の紙"}.issubset(names["M126"]), ""))
    checks.append(("M126 PET remains dedicated DROP_OFF route", rows[("M126", "ペットボトル")].get("collection_channel") == "DROP_OFF", ""))
    checks.append(("M126 spray cans retain puncture rule", "穴を開ける" in rows[("M126", "カン・金属類")].get("出す前の処理", ""), rows[("M126", "カン・金属類")].get("出す前の処理", "")))

    # M128 周南市
    for parent, expected_children in [("古紙・衣類",2),("びん・缶類、ペットボトル",2),("容器包装プラスチック、その他プラスチック",2)]:
        pr = rows[("M128", parent)]
        checks.append((f"M128 {parent} preserves resident child leaves", children[pr["category_id"]] == expected_children, f"children={children[pr['category_id']]}"))
    checks.append(("M128 spray cans retain puncture rule", "穴を開ける" in rows[("M128", "処理困難物")].get("出す前の処理", ""), ""))
    checks.append(("M128 small appliances remain DROP_OFF reference", rows[("M128", "使用済小型家電")].get("collection_channel") == "DROP_OFF" and rows[("M128", "使用済小型家電")].get("ui_role") == "REFERENCE_ONLY", ""))

    # M129 山陽小野田市
    paper129 = rows[("M129", "古紙類")]
    checks.append(("M129 old paper has four child leaves", children[paper129["category_id"]] == 4 and {"新聞","雑誌類","ダンボール","紙パック"}.issubset(names["M129"]), ""))
    checks.append(("M129 generic burnable preparation removed", rows[("M129", "燃やせるごみ")].get("出す前の処理") == "NOT_STATED_IN_CITED_SOURCE", rows[("M129", "燃やせるごみ")].get("出す前の処理", "")))

    # M130 周防大島町
    checks.append(("M130 current search exposes exactly twelve official leaves", counted_category_total("M130", cats) == 12 and {"燃やせるごみ","容器包装プラスチック","その他プラスチック","空ビン","ペットボトル","空カン","金属類","埋立ごみ","有害ごみ","粗大ごみ","特定家庭用機器","家庭用パソコン"}.issubset(names["M130"]), str(names["M130"])))
    checks.append(("M130 two not-collected notices remain excluded from leaf count", {"収集できないごみ","収集も処理もできないごみ"}.issubset(names["M130"]) and all(rows[("M130", n)].get("ui_role") == "EXCLUDED_NOTICE" for n in ["収集できないごみ","収集も処理もできないごみ"]), ""))
    checks.append(("M130 official search service is formally CHECKED_PRESENT", by["M130"].get("search_service_check_status") == "CHECKED_PRESENT" and by["M130"].get("品目検索URL") in by["M130"].get("search_service_check_evidence", "") and "checked:2026-08-19" in by["M130"].get("search_service_check_evidence", ""), by["M130"].get("search_service_check_evidence", "")))
    checks.append(("M130 spray cans retain no-hole rule", "穴あけ不要" in rows[("M130", "空カン")].get("出す前の処理", ""), rows[("M130", "空カン")].get("出す前の処理", "")))

    # M131 和木町
    checks.append(("M131 exact eleven resident labels retained", counted_category_total("M131", cats) == 11 and {"焼却ごみ","プラマークごみ","金属・不燃ごみ","粗大ごみ","ペットボトル","リサイクルびん","陶器・ガラス類","蛍光灯類","電池・ライター・スプレー類","新聞・雑誌、ダンボール","リサイクル衣類"}.issubset(names["M131"]), str(names["M131"])))
    checks.append(("M131 spray cans retain no-hole rule", "穴を開けず" in rows[("M131", "電池・ライター・スプレー類")].get("出す前の処理", ""), rows[("M131", "電池・ライター・スプレー類")].get("出す前の処理", "")))

    # M132 上関町
    paper132 = rows[("M132", "古紙・紙パック")]
    checks.append(("M132 old paper/paper-pack heading has four child leaves", children[paper132["category_id"]] == 4 and {"新聞紙・チラシ","雑誌","段ボール","紙パック"}.issubset(names["M132"]), ""))
    checks.append(("M132 PET remains dedicated DROP_OFF route", rows[("M132", "ペットボトル")].get("collection_channel") == "DROP_OFF" and rows[("M132", "ペットボトル")].get("ui_role") == "REFERENCE_ONLY", ""))
    checks.append(("M132 spray prep states use-up only, without invented puncture instruction", "使い切る" in rows[("M132", "金属類")].get("出す前の処理", "") and "穴" not in rows[("M132", "金属類")].get("出す前の処理", ""), rows[("M132", "金属類")].get("出す前の処理", "")))

    # M133/M134 田布施町・平生町
    for mid in ["M133","M134"]:
        cm = rows[(mid, "缶・金属類")]
        res = rows[(mid, "資源ごみ")]
        checks.append((f"{mid} seven-heading view is not misused as leaf total", counted_category_total(mid, cats) == 12 and by[mid].get("category_count_check_status") == "MANUAL_INDEX_REVIEW", ""))
        checks.append((f"{mid} cans and metals are separate bag leaves", children[cm["category_id"]] == 2 and {"缶","金属類"}.issubset(names[mid]), ""))
        checks.append((f"{mid} resource parent has five resident leaves", children[res["category_id"]] == 5 and {"新聞","雑誌","段ボール","古着","紙パック"}.issubset(names[mid]), ""))

    # M135 阿武町
    checks.append(("M135 April 2026 keeps three resident bag categories", {"可燃ごみ","不燃ごみ","資源ごみ"}.issubset(names["M135"]) and all(rows[("M135", n)].get("ui_role") == "SORT_BUCKET" for n in ["可燃ごみ","不燃ごみ","資源ごみ"]), str(names["M135"])))
    checks.append(("M135 resource bag is not artificially split into can/bottle/PET/plastic leaves", not ({"缶","ビン","ペットボトル","容器包装プラスチック"} & names["M135"]) and counted_category_total("M135", cats) == 5, str(names["M135"])))
    checks.append(("M135 resource preparation contains no modelling prose", rows[("M135", "資源ごみ")].get("出す前の処理") == "資源ごみ指定袋へ", rows[("M135", "資源ごみ")].get("出す前の処理", "")))
    checks.append(("M135 old-paper route does not use filler preparation", rows[("M135", "古紙等")].get("出す前の処理") == "NOT_STATED_IN_CITED_SOURCE", rows[("M135", "古紙等")].get("出す前の処理", "")))

    checks.append(("coverage exactly nine x forty", len(cov) == 360 and Counter(r["municipality_id"] for r in cov) == Counter({mid:40 for mid in TARGETS}), f"coverage={len(cov)}"))
    checks.append(("no generic/filler category detail survives", not any(is_placeholder_category_value(r.get(f, "")) for r in cats for f in CATEGORY_DETAIL_FIELDS), f"categories={len(cats)}"))
    checks.append(("all category evidence uses research date", all(r.get("確認日") == "2026-08-19" for r in cats), ""))

    passed = sum(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    print(f"BATCH13_RED_TEAM_SUMMARY={passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
