#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parent / 'validation_v12.py'
text = path.read_text(encoding='utf-8')
old = '''        for field in ("自治体ごみトップURL", "分別ガイドURL"):\n            if not row.get(field, "").startswith("https://"):\n                errors.append(f"non-HTTPS required municipality URL: {mid} {field}")\n        count_status = row.get("category_count_check_status", "")\n'''
new = '''        # The municipality top URL is always required. A dedicated guide URL is\n        # required once category completeness is reviewed, but may legitimately be\n        # unknown while the municipality remains NOT_REVIEWED / QA_REQUIRED. Do not\n        # fill the homepage into 分別ガイドURL merely to satisfy structure.\n        if not row.get("自治体ごみトップURL", "").startswith("https://"):\n            errors.append(f"non-HTTPS required municipality URL: {mid} 自治体ごみトップURL")\n        count_status = row.get("category_count_check_status", "")\n        guide_url = row.get("分別ガイドURL", "")\n        if count_status == "NOT_REVIEWED":\n            if guide_url and not guide_url.startswith("https://"):\n                errors.append(f"non-HTTPS optional municipality guide URL: {mid} 分別ガイドURL")\n        elif not guide_url.startswith("https://"):\n            errors.append(f"non-HTTPS required municipality URL: {mid} 分別ガイドURL")\n'''
if old not in text:
    if new in text:
        print('already patched')
        raise SystemExit(0)
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new), encoding='utf-8')
print('patched NOT_REVIEWED guide URL semantics')
