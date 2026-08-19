#!/usr/bin/env python3
"""Cached entrypoint for collect_app_readiness_evidence without changing semantics."""
from functools import lru_cache

import collect_app_readiness_evidence as base

# The collector normalizes the same official source text repeatedly for 40
# common items.  Cache normalization by exact input string; evidence rules and
# matching semantics remain unchanged.
base.compact = lru_cache(maxsize=4096)(base.compact)

if __name__ == "__main__":
    raise SystemExit(base.main())
