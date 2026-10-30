"""
Decides small model vs big model, and says WHY in plain words so the
reason can be shown next to every answer.

Two rules, checked in order:
 1. Long question (over the word limit) -> big model
 2. Contains a "needs real thinking" word (explain, compare, ...) -> big model
Otherwise -> small model.

Keywords match whole words only, so "planet" no longer triggers "plan".
"""

import re
from typing import NamedTuple

from config import settings

COMPLEXITY_SIGNAL_WORDS = (
    "explain", "why", "how does", "compare", "analyze", "analyse",
    "design", "architecture", "summarize", "summarise", "write",
    "essay", "debug", "optimize", "plan",
)

_SIGNAL_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in COMPLEXITY_SIGNAL_WORDS) + r")\b"
)


class RouteDecision(NamedTuple):
    tier: str    # "small" or "big"
    reason: str  # plain-words explanation, shown in the UI


def classify_question(question: str) -> RouteDecision:
    text = question.strip().lower()
    word_count = len(text.split())

    if word_count > settings.COMPLEXITY_WORD_THRESHOLD:
        return RouteDecision(
            "big", f"long question ({word_count} words, limit {settings.COMPLEXITY_WORD_THRESHOLD})"
        )

    match = _SIGNAL_PATTERN.search(text)
    if match:
        return RouteDecision("big", f'contains "{match.group(1)}"')

    return RouteDecision("small", f"short and simple ({word_count} words)")


def model_for_tier(tier: str) -> str:
    return settings.BIG_MODEL if tier == "big" else settings.SMALL_MODEL