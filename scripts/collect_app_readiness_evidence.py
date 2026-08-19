#!/usr/bin/env python3
"""Collect conservative ITEM_SPECIFIC evidence candidates from registered official sources.

This script NEVER promotes mappings or coverage by itself.  It downloads each
existing official source once, extracts text, and records a candidate only when
an item alias and a CURRENT municipality category name occur in the same local
text window.  The output is an audit queue for the next promotion/review step.
"""
from __future__ import annotations

import csv
import io
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from schema_v12 import MASTER, RESEARCH, ROOT, read_csv

OUT_DIR = RESEARCH / "app_readiness"
CANDIDATE_PATH = OUT_DIR / "item_evidence_candidates.csv"
PAIR_PATH = OUT_DIR / "item_evidence_pair_status.csv"
FETCH_PATH = OUT_DIR / "official_source_fetch_status.csv"
REPORT_PATH = ROOT / "docs" / "research" / "app_readiness_evidence_collection_report.md"
CHECKED = "2026-08-20"
WINDOW = 420
MAX_SOURCE_BYTES = 35_000_000

ALIASES = {
    "I001": ["ペットボトル", "PETボトル"],
    "I002": ["ペットボトルのキャップ", "ペットボトルキャップ", "ボトルキャップ", "キャップ"],
    "I003": ["ペットボトルのラベル", "ペットボトルラベル", "ラベル"],
    "I004": ["アルミ缶"],
    "I005": ["スチール缶"],
    "I006": ["ガラスびん", "ガラスビン", "空きびん", "空きビン"],
    "I007": ["白色食品トレー", "白色トレー", "白いトレー"],
    "I008": ["色柄食品トレー", "色付きトレー", "色柄トレー", "白色以外のトレー"],
    "I009": ["弁当容器", "弁当の容器", "弁当パック"],
    "I010": ["お菓子の袋", "菓子袋", "スナック菓子の袋"],
    "I011": ["レジ袋"],
    "I012": ["発泡スチロール"],
    "I013": ["新聞"],
    "I014": ["段ボール", "ダンボール"],
    "I015": ["雑誌"],
    "I016": ["雑がみ", "雑紙", "菓子箱", "紙箱"],
    "I017": ["紙パック", "牛乳パック"],
    "I018": ["生ごみ", "生ゴミ"],
    "I019": ["ティッシュ", "ちり紙"],
    "I020": ["紙おむつ", "紙オムツ", "おむつ"],
    "I021": ["古着", "衣類"],
    "I022": ["傘"],
    "I023": ["陶磁器", "茶わん", "茶碗"],
    "I024": ["ガラス製品", "ガラスコップ", "コップ"],
    "I025": ["割れたガラス", "割れガラス", "ガラスくず"],
    "I026": ["包丁", "刃物"],
    "I027": ["乾電池"],
    "I028": ["ボタン電池"],
    "I029": ["モバイルバッテリー"],
    "I030": ["蛍光管", "蛍光灯"],
    "I031": ["電球"],
    "I032": ["スプレー缶", "エアゾール缶"],
    "I033": ["使い捨てライター", "ライター"],
    "I034": ["小型家電"],
    "I035": ["充電池を外せない小型家電", "電池を外せない小型家電", "電池を取り外せない小型家電", "充電式小型家電"],
    "I036": ["布団", "ふとん"],
    "I037": ["家電4品目", "家電４品目", "家電リサイクル法対象品"],
    "I038": ["家庭用パソコン", "パソコン"],
    "I039": ["使用済み食用油", "廃食用油", "食用油"],
    "I040": ["剪定枝", "せん定枝", "枝木"],
}

CANDIDATE_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "category_id", "category_name",
    "source_id", "official_url", "alias", "locator", "snippet", "match_type", "checked_date",
]
PAIR_FIELDS = [
    "municipality_id", "internal_item_id", "existing_branch_count", "direct_branch_evidence_count",
    "distinct_candidate_categories", "status", "notes",
]
FETCH_FIELDS = ["municipality_id", "source_id", "url", "http_status", "bytes", "text_chars", "status", "error"]


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def compact(text: str) -> str:
    return re.sub(r"\s+", "", norm(text)).lower()


def extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return norm("\n".join(parts))


def extract_html(data: bytes, encoding: str | None) -> str:
    if encoding:
        try:
            html = data.decode(encoding, errors="replace")
        except LookupError:
            html = data.decode("utf-8", errors="replace")
    else:
        html = data.decode("utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return norm(soup.get_text("\n"))


def fetch_source(source: dict[str, str]) -> tuple[dict[str, str], str]:
    mid, sid, url = source["municipality_id"], source["source_id"], source["公式URL"]
    status = {"municipality_id": mid, "source_id": sid, "url": url, "http_status": "", "bytes": "0", "text_chars": "0", "status": "ERROR", "error": ""}
    headers = {"User-Agent": "Separate-garbage-official-evidence-audit/1.0 (+public educational research)"}
    try:
        r = requests.get(url, timeout=(8, 30), headers=headers, allow_redirects=True)
        status["http_status"] = str(r.status_code)
        r.raise_for_status()
        data = r.content
        status["bytes"] = str(len(data))
        if len(data) > MAX_SOURCE_BYTES:
            raise ValueError(f"source too large: {len(data)}")
        ctype = (r.headers.get("content-type") or "").lower()
        is_pdf = "pdf" in ctype or urlparse(r.url).path.lower().endswith(".pdf") or data[:5] == b"%PDF-"
        text = extract_pdf(data) if is_pdf else extract_html(data, r.encoding)
        status["text_chars"] = str(len(text))
        if len(compact(text)) < 20:
            raise ValueError("extracted text too short")
        status["status"] = "OK"
        return status, text
    except Exception as exc:
        status["error"] = f"{type(exc).__name__}: {exc}"[:500]
        return status, ""


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows([{k: r.get(k, "") for k in fields} for r in rows])


def find_occurrences(text: str, aliases: list[str]) -> list[tuple[int, str]]:
    ctext = compact(text)
    found: list[tuple[int, str]] = []
    for alias in aliases:
        ca = compact(alias)
        if not ca:
            continue
        start = 0
        while True:
            pos = ctext.find(ca, start)
            if pos < 0:
                break
            found.append((pos, alias))
            start = pos + max(1, len(ca))
            if len(found) >= 80:
                return found
    return sorted(found)


def snippet_from_compact(ctext: str, pos: int, width: int = WINDOW) -> str:
    lo, hi = max(0, pos - width), min(len(ctext), pos + width)
    return ctext[lo:hi]


def main() -> int:
    _, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, items = read_csv(MASTER / "04_common_items_master.csv")

    mids = {r["municipality_id"] for r in municipalities}
    item_ids = [r["internal_item_id"] for r in items]
    current_categories: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in categories:
        if r["municipality_id"] in mids and r.get("rule_status") == "CURRENT" and r.get("ui_role") != "EXCLUDED_NOTICE":
            current_categories[r["municipality_id"]].append(r)

    source_rows = [r for r in sources if r["municipality_id"] in mids and r.get("official_verified") == "TRUE"]
    source_by_key = {(r["municipality_id"], r["source_id"]): r for r in source_rows}

    fetch_status: list[dict[str, str]] = []
    text_by_key: dict[tuple[str, str], str] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        future_map = {pool.submit(fetch_source, src): src for src in source_rows}
        for fut in as_completed(future_map):
            status, text = fut.result()
            fetch_status.append(status)
            if status["status"] == "OK":
                text_by_key[(status["municipality_id"], status["source_id"])] = text
            time.sleep(0.01)

    mappings_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in mappings:
        if r["municipality_id"] in mids:
            mappings_by_pair[(r["municipality_id"], r["internal_item_id"])].append(r)

    candidate_rows: list[dict[str, str]] = []
    pair_rows: list[dict[str, str]] = []

    for mid in sorted(mids):
        cat_rows = current_categories[mid]
        cat_compact = [(r, compact(r["自治体正式名称"])) for r in cat_rows if r.get("自治体正式名称")]
        mid_sources = [r for r in source_rows if r["municipality_id"] == mid and (mid, r["source_id"]) in text_by_key]

        for item_id in item_ids:
            aliases = ALIASES.get(item_id, [])
            existing = sorted(mappings_by_pair.get((mid, item_id), []), key=lambda r: int(r.get("branch_order", "0") or 0))
            direct_branches: set[str] = set()
            candidate_categories: set[str] = set()
            seen = set()

            for src in mid_sources:
                text = text_by_key[(mid, src["source_id"])]
                ctext = compact(text)
                occurrences = find_occurrences(text, aliases)
                if not occurrences:
                    continue
                for pos, alias in occurrences[:40]:
                    snip = snippet_from_compact(ctext, pos)
                    matched_categories = [(r, cname) for r, cname in cat_compact if cname and cname in snip]
                    if not matched_categories:
                        continue
                    for cat, _ in matched_categories:
                        candidate_categories.add(cat["category_id"])
                        branch_order = ""
                        match_type = "ITEM_AND_CATEGORY_LOCAL"
                        for branch in existing:
                            if branch.get("category_id") == cat["category_id"]:
                                branch_order = branch.get("branch_order", "")
                                direct_branches.add(branch_order)
                                match_type = "EXISTING_BRANCH_DIRECT"
                                break
                        key = (mid, item_id, branch_order, cat["category_id"], src["source_id"], alias, pos)
                        if key in seen:
                            continue
                        seen.add(key)
                        display_snip = snip[:820]
                        candidate_rows.append({
                            "municipality_id": mid,
                            "internal_item_id": item_id,
                            "branch_order": branch_order,
                            "category_id": cat["category_id"],
                            "category_name": cat["自治体正式名称"],
                            "source_id": src["source_id"],
                            "official_url": src["公式URL"],
                            "alias": alias,
                            "locator": f"text-match:{alias} + {cat['自治体正式名称']}",
                            "snippet": display_snip,
                            "match_type": match_type,
                            "checked_date": CHECKED,
                        })

            branch_count = len(existing)
            direct_count = len(direct_branches)
            if branch_count and direct_count == branch_count:
                status = "ALL_EXISTING_BRANCHES_HAVE_DIRECT_CANDIDATE"
                notes = "all existing mapping branches have item+category local evidence candidates"
            elif direct_count:
                status = "PARTIAL_EXISTING_BRANCH_EVIDENCE"
                notes = f"direct evidence for {direct_count}/{branch_count} existing branches"
            elif not branch_count and len(candidate_categories) == 1:
                status = "ONE_INFERRED_CATEGORY_CANDIDATE"
                notes = "no existing mapping; exactly one category co-occurs with item alias"
            elif len(candidate_categories) > 1:
                status = "AMBIGUOUS_CATEGORY_CANDIDATES"
                notes = f"{len(candidate_categories)} category candidates"
            else:
                any_item = False
                for src in mid_sources:
                    if find_occurrences(text_by_key[(mid, src["source_id"])], aliases):
                        any_item = True
                        break
                status = "ITEM_MATCH_WITHOUT_CATEGORY" if any_item else "NO_ITEM_MATCH_IN_FETCHED_OFFICIAL_SOURCES"
                notes = "manual/alternate official source research required"
            pair_rows.append({
                "municipality_id": mid,
                "internal_item_id": item_id,
                "existing_branch_count": str(branch_count),
                "direct_branch_evidence_count": str(direct_count),
                "distinct_candidate_categories": str(len(candidate_categories)),
                "status": status,
                "notes": notes,
            })

    write_rows(CANDIDATE_PATH, CANDIDATE_FIELDS, candidate_rows)
    write_rows(PAIR_PATH, PAIR_FIELDS, pair_rows)
    write_rows(FETCH_PATH, FETCH_FIELDS, sorted(fetch_status, key=lambda r: (r["municipality_id"], r["source_id"])))

    status_counts = Counter(r["status"] for r in pair_rows)
    fetch_counts = Counter(r["status"] for r in fetch_status)
    item_direct = Counter()
    for r in pair_rows:
        if r["status"] == "ALL_EXISTING_BRANCHES_HAVE_DIRECT_CANDIDATE":
            item_direct[r["internal_item_id"]] += 1

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("# APP readiness ITEM_SPECIFIC evidence collection report\n\n")
        f.write(f"checked: {CHECKED}\n\n")
        f.write("This is a conservative evidence-candidate harvest. No mapping/coverage status is promoted by this collector.\n\n")
        f.write(f"- active municipalities: {len(mids)}\n")
        f.write(f"- municipality-item pairs: {len(pair_rows)}\n")
        f.write(f"- official source rows attempted: {len(fetch_status)}\n")
        f.write(f"- source fetch OK: {fetch_counts.get('OK', 0)}\n")
        f.write(f"- source fetch ERROR: {fetch_counts.get('ERROR', 0)}\n")
        f.write(f"- candidate evidence rows: {len(candidate_rows)}\n\n")
        f.write("## Pair status\n\n")
        for k, v in status_counts.most_common():
            f.write(f"- {k}: {v}\n")
        f.write("\n## Existing-branch direct evidence candidates by item\n\n")
        for item_id in item_ids:
            f.write(f"- {item_id}: {item_direct.get(item_id, 0)}/{len(mids)} municipalities\n")
        f.write("\n## Guardrail\n\n")
        f.write("A candidate is not APP_READY. Promotion requires source-level review, item-specific locator confirmation, and complete conditional branch review.\n")

    print(f"APP_EVIDENCE_COLLECTION_DONE pairs={len(pair_rows)} candidates={len(candidate_rows)} fetch={dict(fetch_counts)} status={dict(status_counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
