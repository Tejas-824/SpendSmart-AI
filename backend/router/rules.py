"""
The actual "brain" of the router. Nothing fancy on purpose - a project
like this doesn't need a classifier model to decide if a question is
simple or not, it needs a rule that's easy to explain in an interview.
"""

from config import settings

COMPLEXITY_SIGNAL_WORDS = (
    "explain", "why", "how does", "compare", "analyze", "analyse",
    "design", "architecture", "summarize", "summarise", "write",
    "essay", "debug", "optimize", "plan",
)


def classify_question(question: str) -> str:
    text = question.strip().lower()
    word_count = len(text.split())

    if word_count > settings.COMPLEXITY_WORD_THRESHOLD:
        return "big"

    if any(signal in text for signal in COMPLEXITY_SIGNAL_WORDS):
        return "big"

    return "small"


def model_for_tier(tier: str) -> str:
    return settings.BIG_MODEL if tier == "big" else settings.SMALL_MODEL