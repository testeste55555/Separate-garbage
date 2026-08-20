#!/usr/bin/env python3
"""Evidence policy for APP-readiness item/category decisions.

The policy intentionally separates an item's *decision basis* from the final
mapping status.  A municipality does not need to literally name every common
item when its official category rule already determines the result, and an
ordinary item may be classified by a stable general rule when the municipality
publishes no contrary/special rule.

No function in this module mutates canonical research data.
"""
from __future__ import annotations

import re
import unicodedata

DIRECT_ITEM = "DIRECT_ITEM"
OFFICIAL_RULE_DERIVED = "OFFICIAL_RULE_DERIVED"
GENERAL_RULE_DERIVED = "GENERAL_RULE_DERIVED"
UNRESOLVED = "UNRESOLVED"

DECISION_BASIS = {
    DIRECT_ITEM,
    OFFICIAL_RULE_DERIVED,
    GENERAL_RULE_DERIVED,
    UNRESOLVED,
}

# General-rule classification is allowed for ordinary items when it resolves to
# one unambiguous CURRENT category and no municipality-specific contrary rule is
# visible.  These patterns are deliberately category concepts, not exact names.
GENERAL_CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "I009": (r"容器包装.*プラ", r"プラ.*容器包装", r"プラスチック.*容器包装", r"容器包装プラスチック"),
    "I010": (r"容器包装.*プラ", r"プラ.*容器包装", r"プラスチック.*容器包装", r"容器包装プラスチック"),
    "I011": (r"容器包装.*プラ", r"プラ.*容器包装", r"プラスチック.*容器包装", r"容器包装プラスチック"),
    "I012": (r"容器包装.*プラ", r"プラ.*容器包装", r"プラスチック.*容器包装", r"容器包装プラスチック"),
    "I019": (r"可燃", r"燃やす", r"燃える", r"もえる", r"普通ごみ", r"家庭ごみ"),
    "I020": (r"可燃", r"燃やす", r"燃える", r"もえる", r"普通ごみ", r"家庭ごみ"),
    "I023": (r"不燃", r"燃やさない", r"燃えない", r"もえない"),
    "I024": (r"不燃", r"燃やさない", r"燃えない", r"もえない"),
}

# These items can still receive a category decision from GENERAL_RULE_DERIVED,
# but APP readiness must not be inferred from the destination alone because
# preparation, size, collection route, legal route, or hazard conditions vary
# materially by municipality.
REQUIRES_EXPLICIT_CONDITION_REVIEW = {
    "I002", "I003", "I006", "I007", "I008", "I009", "I010", "I011", "I012",
    "I017", "I022", "I025", "I026", "I027", "I028", "I029", "I030", "I031",
    "I032", "I033", "I034", "I035", "I036", "I037", "I038", "I039", "I040",
}

# Words that signal that a simple general classification may be unsafe without
# reviewing the municipality-specific exception/condition text.
EXCEPTION_SIGNAL_RE = re.compile(
    r"例外|除く|対象外|不可|禁止|持込|持ち込|拠点|店頭|販売店|メーカー|予約|有料|"
    r"粗大|指定袋|別袋|穴|使い切|絶縁|長さ|大きさ|サイズ|太さ|本数|回収箱|リサイクル法"
)


def compact(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"\s+", "", text).lower()


def general_category_matches(item_id: str, category_name: str) -> bool:
    """Return whether an official category name matches an allowed general rule."""
    name = compact(category_name)
    return any(re.search(pattern, name) for pattern in GENERAL_CATEGORY_PATTERNS.get(item_id, ()))


def has_exception_signal(*texts: str) -> bool:
    return bool(EXCEPTION_SIGNAL_RE.search(" ".join(texts)))


def requires_condition_review(item_id: str) -> bool:
    return item_id in REQUIRES_EXPLICIT_CONDITION_REVIEW
