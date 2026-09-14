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

old_category_sort = '    rows.sort(key=lambda row: (row.get("municipality_id", ""), int(row.get("表示順") or 999), row.get("category_id", "")))'
new_category_sort = '    rows.sort(key=lambda row: (row.get("municipality_id", ""), row.get("category_id", "")))'
if old_category_sort in text:
    text = text.replace(old_category_sort, new_category_sort)
elif new_category_sort not in text:
    raise SystemExit('M068 canonical category sort anchor not found')

refresh_fn = '''\n\ndef refresh_initial_mapping_layer() -> None:\n    """Refresh only M068 category-derived initial mappings and coverage.\n\n    The new M068 regional categories create legitimate automatic candidates for\n    non-lesson items. Reconcile only M068 so unrelated municipalities and their\n    manually reviewed coverage remain byte-for-byte untouched.\n    """\n    _, all_categories = read_csv(CATEGORIES)\n    mapping_fields, all_mappings = read_csv(MAPPINGS)\n    _, all_municipalities = read_csv(MUNICIPALITIES)\n    coverage_fields, all_coverage = read_csv(COVERAGE)\n    _, items = read_csv(ROOT / "data/master/04_common_items_master.csv")\n\n    categories = [row for row in all_categories if row.get("municipality_id") == MID]\n    mappings = [row for row in all_mappings if row.get("municipality_id") == MID]\n    municipalities = [row for row in all_municipalities if row.get("municipality_id") == MID]\n    coverage = [row for row in all_coverage if row.get("municipality_id") == MID]\n\n    refreshed_mappings = reconcile_mappings(categories, mappings)\n    refreshed_coverage = build_coverage(municipalities, items, refreshed_mappings, coverage)\n\n    merged_mappings = [row for row in all_mappings if row.get("municipality_id") != MID] + refreshed_mappings\n    merged_mappings.sort(key=lambda row: (\n        row.get("municipality_id", ""), row.get("internal_item_id", ""),\n        int(row.get("branch_order") or 0), row.get("mapping_id", ""),\n    ))\n    merged_coverage = [row for row in all_coverage if row.get("municipality_id") != MID] + refreshed_coverage\n    merged_coverage.sort(key=lambda row: (row.get("municipality_id", ""), row.get("internal_item_id", "")))\n\n    write_csv(MAPPINGS, mapping_fields, merged_mappings)\n    write_csv(COVERAGE, coverage_fields, merged_coverage)\n'''
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
