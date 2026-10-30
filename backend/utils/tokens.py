"""
Token counting (only used as a fallback now) and cost maths.

Groq sends back the real token counts with every answer, so we use those.
tiktoken is only used if that info is ever missing.
"""

from config import settings

_encoding = None
try:
    import tiktoken

    _encoding = tiktoken.get_encoding("cl100k_base")
except Exception:
    # No internet on first run, blocked network, etc. Fall back below
    # instead of crashing the whole app over a token counter.
    _encoding = None


def count_tokens(text: str) -> int:
    if not text:
        return 0
    if _encoding is not None:
        return len(_encoding.encode(text))
    return max(1, len(text) // 4)  # rough rule: 4 characters per token


def estimate_cost(tokens_in: int, tokens_out: int, tier: str) -> float:
    """Cost in USD. Input and output tokens have different prices."""
    if tier == "big":
        price_in, price_out = settings.BIG_INPUT_PER_M, settings.BIG_OUTPUT_PER_M
    else:
        price_in, price_out = settings.SMALL_INPUT_PER_M, settings.SMALL_OUTPUT_PER_M
    return round((tokens_in * price_in + tokens_out * price_out) / 1_000_000, 8)


def cost_if_big(tokens_in: int, tokens_out: int) -> float:
    """What the same tokens would cost on the big model. Used for the
    'how much did routing and caching save me' numbers."""
    return estimate_cost(tokens_in, tokens_out, "big")