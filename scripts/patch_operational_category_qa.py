#!/usr/bin/env python3
"""Align category QA with resident-facing operational sorting semantics.

Presence of an explicit hazardous-waste bucket or explicit not-collected bucket is
tracked in QA, but is not universally required for category-completeness PASS.
Safety and excluded-route correctness are enforced item-by-item at APP_READY.
"""
from pathlib import Path

p = Path("scripts/schema_v12.py")
s = p.read_text(encoding="utf-8")
old = '''        required = [
            "ごみトップ", "現行ルール", "全分別区分", "正式名称", "代表品目", "前処理", "危険有害",
            "収集しない物", "公式出典", "参照整合性", "Schema検証", "category_count_verified",
            "rule_status検証", "ui_role検証",
        ]'''
new = '''        # Category QA asks whether the resident-facing sorting system is faithfully
        # represented. A municipality does not need a *separate* hazardous-waste or
        # not-collected bucket to pass this gate; those two QA columns remain
        # informational. Safety/excluded-route correctness is verified item-by-item
        # before APP_READY (batteries, spray cans, appliances, PCs, etc.).
        required = [
            "ごみトップ", "現行ルール", "全分別区分", "正式名称", "代表品目", "前処理",
            "公式出典", "参照整合性", "Schema検証", "category_count_verified",
            "rule_status検証", "ui_role検証",
        ]'''
if old not in s:
    if new not in s:
        raise RuntimeError("compute_qa required-list patch target not found")
else:
    s = s.replace(old, new)
s = s.replace('"Schema v1.2.3で機械再計算"', '"Schema v1.2.4で機械再計算"')
p.write_text(s, encoding="utf-8")

Path("docs/schema/13_schema_v1.2.4.md").write_text('''# Schema v1.2.4 — resident-facing category QA semantics

制定日: 2026-08-19

v1.2.3の列・主キー・証拠モデルは維持し、category QAの合格意味だけを明確化する。

## category completeness

`QA_PASSED` が要求するのは、住民が家庭ごみを排出するときに選択する自治体公式の分別体系を、公式sourceとlocator付きで忠実に保持していること。

次のQA列は引き続き計算・表示するが、全自治体共通の必須TRUEとはしない。

- `危険有害`
- `収集しない物`

理由: 自治体によって、乾電池・スプレー缶・収集不可品を独立categoryにする場合と、資源ごみ等の内部品目・別ページの例外ルールとして扱う場合がある。独立categoryの存在を全自治体に強制すると、住民向け公式分類を人工的に細分化する。

## safety / excluded routes

安全性を緩和しない。乾電池、モバイルバッテリー、蛍光管、スプレー缶、ライター、家電4品目、PC等は40品目のitem mapping / coverageで個別に公式source・URL・locatorを確認する。

`APP_READY` は従来どおりITEM_SPECIFIC evidence、全条件枝COMPLETE、reviewer/dateを必須とする。

## currentness

公開日が古い公式住民向けページでも、現在も公式公開され、現年度カレンダー等が同じ分別体系の稼働を示す場合はCURRENTとして利用できる。publication ageとrule retirementを分離する。
''', encoding="utf-8")

Path("docs/schema/14_data_dictionary_v1.2.4.md").write_text('''# Data Dictionary v1.2.4 amendment

## QA.危険有害
自治体category群に危険・有害・電池・蛍光管・水銀・スプレー缶・ライター等の明示があるかを示す情報列。FALSEは「自治体に危険物ルールがない」ことを意味しない。category QAの必須TRUEではない。

## QA.収集しない物
`ui_role=EXCLUDED_NOTICE` のcategoryが存在するかを示す情報列。FALSEは「収集不可品が存在しない」ことを意味しない。category QAの必須TRUEではない。

## QA_PASSED
住民向け公式分別体系の区分網羅性・正式名称・CORE詳細・公式source・参照整合性・rule_status・ui_roleが検証済みであることを示す。危険品目・収集不可品目の最終的な処理判断はitem-level APP_READYで検証する。
''', encoding="utf-8")
print("Operational category QA semantics patched")
