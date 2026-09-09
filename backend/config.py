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
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    SMALL_MODEL: str = os.getenv("SMALL_MODEL", "llama-3.1-8b-instant")
    BIG_MODEL: str = os.getenv("BIG_MODEL", "llama-3.3-70b-versatile")

    SMALL_MODEL_PRICE_PER_1K: float = float(os.getenv("SMALL_MODEL_PRICE_PER_1K", "0.00005"))
    BIG_MODEL_PRICE_PER_1K: float = float(os.getenv("BIG_MODEL_PRICE_PER_1K", "0.00059"))
    DAILY_BUDGET_USD: float = float(os.getenv("DAILY_BUDGET_USD", "1.00"))

    COMPLEXITY_WORD_THRESHOLD: int = int(os.getenv("COMPLEXITY_WORD_THRESHOLD", "15"))

    AUTH_USERNAME: str = os.getenv("AUTH_USERNAME", "admin")
    AUTH_PASSWORD_HASH: str = os.getenv("AUTH_PASSWORD_HASH", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))

    FRONTEND_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
    if origin.strip()
]
    DB_PATH: str = os.getenv(
        "DB_PATH", os.path.join(os.path.dirname(__file__), "storage", "logs.db")
    )
    CACHE_ENABLED: bool = _get_bool("CACHE_ENABLED", True)


settings = Settings()