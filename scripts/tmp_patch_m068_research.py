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
path.write_text(text)
