#!/usr/bin/env python3
from pathlib import Path

def patch(path, old, new):
    p=Path(path); s=p.read_text()
    if old not in s and new not in s:
        raise SystemExit(f'missing patch anchor: {path}: {old}')
    if old in s:
        s=s.replace(old,new)
    p.write_text(s)

patch('scripts/sync_lesson_ready_reviews.py','VARIANT_ONLY_LESSON_READY = {"M055"}','VARIANT_ONLY_LESSON_READY = {"M055", "M068"}')
patch('scripts/validate_lesson_scoring_modes.py','VARIANT_ONLY_LESSON_READY = {"M055"}','VARIANT_ONLY_LESSON_READY = {"M055", "M068"}')
patch('scripts/validate_lesson_scoring_modes.py','"M027": LESSON_READY, "M030": LESSON_READY, "M048": LESSON_READY, "M050": LESSON_READY, "M055": LESSON_READY, "M056": LESSON_READY, "M067": LESSON_READY, "M097": LESSON_READY,','"M027": LESSON_READY, "M030": LESSON_READY, "M048": LESSON_READY, "M050": LESSON_READY, "M055": LESSON_READY, "M056": LESSON_READY, "M067": LESSON_READY, "M068": LESSON_READY, "M097": LESSON_READY,')
p='scripts/validate_lesson_variants.py'
patch(p,'TARGETS = {"M055", "M076",','TARGETS = {"M055", "M068", "M076",')
patch(p,'STANDARD_SCOPE_VARIANT_TARGETS = {"M055"}','STANDARD_SCOPE_VARIANT_TARGETS = {"M055", "M068"}')
patch(p,'    "M055": {"LV-M055-01", "LV-M055-02"},','    "M055": {"LV-M055-01", "LV-M055-02"},\n    "M068": {"LV-M068-01", "LV-M068-02"},')
patch(p,'    "M055": "TRUE",','    "M055": "TRUE", "M068": "TRUE",')
patch(p,'    "M055": {"LV-M055-01": 4, "LV-M055-02": 2},','    "M055": {"LV-M055-01": 4, "LV-M055-02": 2},\n    "M068": {"LV-M068-01": 1, "LV-M068-02": 1},')
s=Path(p).read_text(); anchor='NEW_EXPECTED_LABELS = {\n'
addition='    "LV-M068-01": ["資源ごみ", "資源ごみ", "資源ごみ", "燃やせるごみ", "資源ごみ", "資源ごみ", "資源ごみ", "使用済み乾電池", "埋立ごみ", "燃やせるごみ"],\n    "LV-M068-02": ["資源ごみ", "資源ごみ", "資源ごみ", "資源ごみ", "資源ごみ", "資源ごみ", "資源ごみ", "体温計・乾電池", "燃えないごみ", "燃えるごみ"],\n'
if '"LV-M068-01"' not in s[s.index('NEW_EXPECTED_LABELS'):]: s=s.replace(anchor,anchor+addition)
Path(p).write_text(s)
w='.github/workflows/app-ready-lesson-modes.yml'
# Add both trigger path entries.
s=Path(w).read_text()
s=s.replace('      - "scripts/build_lesson_ready_m067.py"','      - "scripts/build_lesson_ready_m067.py"\n      - "scripts/build_lesson_ready_m068.py"') if 'scripts/build_lesson_ready_m068.py' not in s else s
# If only one occurrence was created, insert the second after the second M067 occurrence.
if s.count('      - "scripts/build_lesson_ready_m068.py"') < 2:
    positions=[]; start=0
    needle='      - "scripts/build_lesson_ready_m067.py"'
    while True:
        i=s.find(needle,start)
        if i<0: break
        positions.append(i); start=i+len(needle)
    if len(positions)>=2:
        i=positions[1]+len(needle); s=s[:i]+'\n      - "scripts/build_lesson_ready_m068.py"'+s[i:]
if '          python scripts/build_lesson_ready_m068.py' not in s:
    s=s.replace('          python scripts/build_lesson_ready_m067.py','          python scripts/build_lesson_ready_m067.py\n          python scripts/build_lesson_ready_m068.py')
for name in ['batch_07_categories.csv','batch_07_category_review_evidence.csv','batch_07_item_mapping.csv','batch_07_item_coverage.csv']:
    line=f'            data/research/batches/batch_07/{name} \\\n'
    if f'data/research/batches/batch_07/{name}' not in s:
        s=s.replace('            data/research/batches/batch_07/batch_07_sources.csv \\\n',line+'            data/research/batches/batch_07/batch_07_sources.csv \\\n')
Path(w).write_text(s)
