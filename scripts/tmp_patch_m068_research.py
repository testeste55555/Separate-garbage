#!/usr/bin/env python3
from pathlib import Path

path = Path('scripts/build_lesson_ready_m068.py')
text = path.read_text()
text = text.replace('"official_basis": "MUNICIPALITY_DOMAIN"', '"official_basis": "MUNICIPAL_DOMAIN"')
replacements = {
    'row.update({"適用条件": "真備地区以外", "条件外の扱い": "真備地区はC-M068-07 燃えるごみ", "source_id": "S-M068-03", "出典URL": URL03, "出典ページ・該当箇所": "真備地区以外／燃やせるごみ", "確認日": CHECKED})':
    'row.update({"適用条件": "真備地区以外", "条件外の扱い": "真備地区はC-M068-07 燃えるごみ", "確認日": CHECKED})',
    'row.update({"適用条件": "市内（品目・排出方法は地域別公式資料に従う）", "source_id": "S-M068-03", "出典URL": URL03, "出典ページ・該当箇所": "資源ごみ。真備地区はS-M068-07でも確認", "確認日": CHECKED})':
    'row.update({"適用条件": "市内（品目・排出方法は地域別公式資料に従う）", "確認日": CHECKED})',
    'row.update({"適用条件": "真備地区以外", "条件外の扱い": "真備地区の該当品はC-M068-08 燃えないごみ", "source_id": "S-M068-03", "出典URL": URL03, "出典ページ・該当箇所": "真備地区以外／埋立ごみ", "確認日": CHECKED})':
    'row.update({"適用条件": "真備地区以外", "条件外の扱い": "真備地区の該当品はC-M068-08 燃えないごみ", "確認日": CHECKED})',
    'row.update({"適用条件": "真備地区以外", "条件外の扱い": "真備地区はC-M068-09 体温計・乾電池", "代表品目": "乾電池・モバイルバッテリー等の対象使用済み電池", "source_id": "S-M068-08", "出典URL": URL08, "出典ページ・該当箇所": "令和8年4月から使用済み電池をステーション回収", "確認日": CHECKED})':
    'row.update({"適用条件": "真備地区以外", "条件外の扱い": "真備地区はC-M068-09 体温計・乾電池", "代表品目": "乾電池・モバイルバッテリー等の対象使用済み電池", "確認日": CHECKED})',
}
for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new)
    elif new not in text:
        raise SystemExit(f'M068 category patch anchor not found: {old[:80]}')

old_import = 'from schema_v12 import read_csv, write_csv'
new_import = 'from schema_v12 import build_coverage, read_csv, reconcile_mappings, write_csv'
if old_import in text:
    text = text.replace(old_import, new_import)
elif new_import not in text:
    raise SystemExit('M068 mapping refresh import anchor not found')

refresh_fn = '''\n\ndef refresh_initial_mapping_layer() -> None:\n    """Reconcile category-derived initial mappings after adding regional categories.\n\n    New M068 regional categories add positive item evidence for non-lesson items too.\n    Keep the canonical initial mapping/coverage layer synchronized before projecting\n    the audited fixed-10 review, so completed Batch07 remains merge-idempotent.\n    """\n    _, categories = read_csv(CATEGORIES)\n    mapping_fields, mappings = read_csv(MAPPINGS)\n    _, municipalities = read_csv(MUNICIPALITIES)\n    coverage_fields, coverage = read_csv(COVERAGE)\n    _, items = read_csv(ROOT / "data/master/04_common_items_master.csv")\n    mappings = reconcile_mappings(categories, mappings)\n    coverage = build_coverage(municipalities, items, mappings, coverage)\n    write_csv(MAPPINGS, mapping_fields, mappings)\n    write_csv(COVERAGE, coverage_fields, coverage)\n'''
anchor = '\n\ndef sync_category_evidence(path: Path) -> None:'
if 'def refresh_initial_mapping_layer() -> None:' not in text:
    if anchor not in text:
        raise SystemExit('M068 refresh function insertion anchor not found')
    text = text.replace(anchor, refresh_fn + anchor)

call_anchor = '    upsert_categories(CATEGORIES)\n    sync_category_evidence(CATEGORY_EVIDENCE)'
call_replacement = '    upsert_categories(CATEGORIES)\n    refresh_initial_mapping_layer()\n    sync_category_evidence(CATEGORY_EVIDENCE)'
if call_anchor in text:
    text = text.replace(call_anchor, call_replacement)
elif call_replacement not in text:
    raise SystemExit('M068 refresh call anchor not found')

path.write_text(text)
