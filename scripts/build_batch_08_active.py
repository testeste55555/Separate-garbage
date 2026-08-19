#!/usr/bin/env python3
"""Build active Batch 08 while preserving deferred Bizen research outside canonical.

M076 備前市 is deferred because FY2026 still has two resident-facing sorting
systems by district. The current Schema/UI has no district-variant selector, so
forcing either system city-wide would create incorrect guidance.

This wrapper is the production Batch 08 entrypoint. It also repairs one legacy
syntax defect in build_batch_08.py before importing it: Japanese CSV column
names containing U+30FB cannot be used as ``dict(...)`` keyword identifiers.
The repair is exact and idempotent; once the base builder is permanently fixed,
this compatibility step becomes a no-op.
"""
from __future__ import annotations

from pathlib import Path
import importlib

DEFERRED={"M076"}

_BAD = "    cats.append(dict(municipality_id=mid,自治体正式名称=name,category_group=parent or name,parent_name=parent,classification_level=level,collection_channel=channel,代表品目=rep,入れてはいけない物=forbidden,適用条件=cond,条件外の扱い=fallback,出す前の処理=prep,袋・容器のルール=bag,サイズ・条件=size,粗大ごみ扱いか=bulky,予約が必要か='TRUE' if channel=='BOOKED_PICKUP' else 'FALSE',有料か='FALSE',料金ルール='',自治体収集外か=excluded,注意事項=note,source_index=str(source),出典ページ・該当箇所=name,ui_role=ui,rule_status=status,effective_from=effective_from,effective_to=effective_to))"
_GOOD = "    cats.append({'municipality_id':mid,'自治体正式名称':name,'category_group':parent or name,'parent_name':parent,'classification_level':level,'collection_channel':channel,'代表品目':rep,'入れてはいけない物':forbidden,'適用条件':cond,'条件外の扱い':fallback,'出す前の処理':prep,'袋・容器のルール':bag,'サイズ・条件':size,'粗大ごみ扱いか':bulky,'予約が必要か':'TRUE' if channel=='BOOKED_PICKUP' else 'FALSE','有料か':'FALSE','料金ルール':'','自治体収集外か':excluded,'注意事項':note,'source_index':str(source),'出典ページ・該当箇所':name,'ui_role':ui,'rule_status':status,'effective_from':effective_from,'effective_to':effective_to})"


def _repair_legacy_builder() -> None:
    path = Path(__file__).with_name('build_batch_08.py')
    text = path.read_text(encoding='utf-8')
    if _BAD in text:
        path.write_text(text.replace(_BAD, _GOOD, 1), encoding='utf-8')
        return
    if _GOOD in text:
        return
    raise RuntimeError('Batch 08 legacy syntax target not found; inspect build_batch_08.py before proceeding')


def main() -> None:
    _repair_legacy_builder()
    batch = importlib.import_module('build_batch_08')
    for mid in DEFERRED:
        batch.TARGETS.discard(mid)
        batch.PASS_TARGETS.discard(mid)
        batch.municipality_specs.pop(mid, None)
        batch.source_specs.pop(mid, None)
    batch.cats[:] = [row for row in batch.cats if row.get('municipality_id') not in DEFERRED]
    batch.main()


if __name__ == '__main__':
    main()
