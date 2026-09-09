"""
Rough token counting and cost estimation. Falls back to a character-
based estimate if tiktoken can't download its encoding file.
"""

from config import settings

_encoding = None
try:
    import tiktoken
    _encoding = tiktoken.get_encoding("cl100k_base")
except Exception:
    _encoding = None


def count_tokens(text: str) -> int:
    if not text:
        return 0
    if _encoding is not None:
        return len(_encoding.encode(text))
    return max(1, len(text) // 4)


def estimate_cost(tokens_in: int, tokens_out: int, tier: str) -> float:
    price_per_1k = (
        settings.BIG_MODEL_PRICE_PER_1K if tier == "big" else settings.SMALL_MODEL_PRICE_PER_1K
    )
    total_tokens = tokens_in + tokens_out
    return round((total_tokens / 1000) * price_per_1k, 6)