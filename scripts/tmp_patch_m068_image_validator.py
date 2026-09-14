#!/usr/bin/env python3
from pathlib import Path

path = Path('scripts/validate_item_image_mapping_pilot.py')
text = path.read_text()
old = 'VARIANT_HOLD = {"M055", "M098", "M099"}'
new = 'VARIANT_HOLD = {"M055", "M068", "M098", "M099"}'
if old in text:
    text = text.replace(old, new)
elif new not in text:
    raise SystemExit('image validator VARIANT_HOLD anchor missing')
text = text.replace(
    'variant-only M055/M098/M099 must not enter this municipality-wide pilot',
    'variant-only M055/M068/M098/M099 must not enter this municipality-wide pilot',
)
path.write_text(text)
