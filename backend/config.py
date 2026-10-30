"""
Every setting the app needs lives here, read from environment variables.
Nothing secret is ever hardcoded - see .env.example for what to fill in.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes")


class Settings:
    # --- LLM provider (Groq) ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    SMALL_MODEL: str = os.getenv("SMALL_MODEL", "openai/gpt-oss-20b")
    BIG_MODEL: str = os.getenv("BIG_MODEL", "openai/gpt-oss-120b")
    MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "1024"))
    # gpt-oss models "think" before answering. Low effort keeps that cheap.
    # Set to empty to turn it off.
    REASONING_EFFORT: str = os.getenv("REASONING_EFFORT", "low")

    # --- Prices in USD per 1 million tokens (Groq's public pricing) ---
    # Input and output are priced separately, so we use the real
    # token counts Groq sends back instead of one blended guess.
    SMALL_INPUT_PER_M: float = float(os.getenv("SMALL_INPUT_PER_M", "0.075"))
    SMALL_OUTPUT_PER_M: float = float(os.getenv("SMALL_OUTPUT_PER_M", "0.30"))
    BIG_INPUT_PER_M: float = float(os.getenv("BIG_INPUT_PER_M", "0.15"))
    BIG_OUTPUT_PER_M: float = float(os.getenv("BIG_OUTPUT_PER_M", "0.60"))

    # --- Budgets (estimated USD per day) ---
    DAILY_BUDGET_USD: float = float(os.getenv("DAILY_BUDGET_USD", "1.00"))
    GUEST_DAILY_BUDGET_USD: float = float(os.getenv("GUEST_DAILY_BUDGET_USD", "0.05"))
    BUDGET_WARN_PERCENT: int = int(os.getenv("BUDGET_WARN_PERCENT", "80"))

    # A question longer than this many words is treated as "complex".
    COMPLEXITY_WORD_THRESHOLD: int = int(os.getenv("COMPLEXITY_WORD_THRESHOLD", "15"))

    # --- Cache ---
    CACHE_ENABLED: bool = _get_bool("CACHE_ENABLED", True)
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24 hours
    # 0 to 1. How much two questions must overlap to count as "the same".
    CACHE_SIMILARITY: float = float(os.getenv("CACHE_SIMILARITY", "0.75"))

    # --- Auth ---
    AUTH_USERNAME: str = os.getenv("AUTH_USERNAME", "admin")
    AUTH_PASSWORD_HASH: str = os.getenv("AUTH_PASSWORD_HASH", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))

    # --- Guest demo mode ---
    GUEST_DAILY_LIMIT_PER_IP: int = int(os.getenv("GUEST_DAILY_LIMIT_PER_IP", "5"))
    GUEST_GLOBAL_DAILY_LIMIT: int = int(os.getenv("GUEST_GLOBAL_DAILY_LIMIT", "100"))

    # --- Server ---
    FRONTEND_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    DB_PATH: str = os.getenv(
        "DB_PATH", os.path.join(os.path.dirname(__file__), "storage", "logs.db")
    )

    def budget_for(self, username: str) -> float:
        """Guests get their own small budget so they can't use up yours."""
        return self.GUEST_DAILY_BUDGET_USD if username == "guest" else self.DAILY_BUDGET_USD


settings = Settings()