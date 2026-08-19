#!/usr/bin/env python3
"""Fast cached entrypoint for APP evidence collection without relaxing evidence rules."""
from concurrent.futures import ThreadPoolExecutor as _Executor
from functools import lru_cache

import collect_app_readiness_evidence as base

# Cache repeated normalization of the exact same official source text.
base.compact = lru_cache(maxsize=4096)(base.compact)

# The base function captured WINDOW=420 in its default argument at definition
# time, while the CSV writer retains at most 820 compact characters. Override
# the function itself with a 400-character radius so every accepted item/category
# occurrence used by the collector remains present in the persisted audit snippet.
_original_snippet = base.snippet_from_compact

def _auditable_snippet(ctext: str, pos: int, width: int = 400) -> str:
    return _original_snippet(ctext, pos, width=400)

base.snippet_from_compact = _auditable_snippet

# Increase only fetch concurrency. The collector still accepts evidence only
# under the same item-alias + CURRENT-category local co-occurrence rules.
base.ThreadPoolExecutor = lambda max_workers=4: _Executor(max_workers=12)

# Avoid one unresponsive official site consuming a worker for too long. A
# timeout remains an audited fetch failure and can never promote evidence.
_original_get = base.requests.get

def _fast_get(*args, **kwargs):
    kwargs["timeout"] = (6, 18)
    return _original_get(*args, **kwargs)

base.requests.get = _fast_get

if __name__ == "__main__":
    raise SystemExit(base.main())
