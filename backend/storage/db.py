"""
Plain SQLite. Every request gets one row: what was asked, which model
handled it, how many tokens it used, what it cost, and whether it
came from cache.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

from config import settings

os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)


@contextmanager
def get_connection():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                question TEXT NOT NULL,
                model_used TEXT NOT NULL,
                model_tier TEXT NOT NULL,
                tokens_in INTEGER NOT NULL,
                tokens_out INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                cached INTEGER NOT NULL
            )
            """
        )


def log_request(question, model_used, model_tier, tokens_in, tokens_out, cost_usd, cached) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO requests
                (created_at, question, model_used, model_tier, tokens_in, tokens_out, cost_usd, cached)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                question, model_used, model_tier, tokens_in, tokens_out, cost_usd, int(cached),
            ),
        )


def get_today_cost() -> float:
    today_prefix = date.today().isoformat()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(cost_usd), 0) AS total
            FROM requests
            WHERE cached = 0 AND created_at LIKE ?
            """,
            (f"{today_prefix}%",),
        ).fetchone()
        return float(row["total"])


def get_stats() -> dict:
    with get_connection() as conn:
        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS total_requests,
                COALESCE(SUM(cached), 0) AS cache_hits,
                COALESCE(SUM(tokens_in + tokens_out), 0) AS total_tokens,
                COALESCE(SUM(cost_usd), 0) AS total_cost
            FROM requests
            """
        ).fetchone()

        would_have_cost = conn.execute(
            """
            SELECT COALESCE(SUM(
                (CAST(tokens_in AS REAL) + tokens_out) / 1000.0 *
                CASE WHEN model_tier = 'big' THEN ? ELSE ? END
            ), 0) AS total
            FROM requests
            WHERE cached = 1
            """,
            (settings.BIG_MODEL_PRICE_PER_1K, settings.SMALL_MODEL_PRICE_PER_1K),
        ).fetchone()

    total_requests = totals["total_requests"]
    cache_hits = totals["cache_hits"]
    today_cost = get_today_cost()

    return {
        "total_requests": total_requests,
        "cache_hits": cache_hits,
        "cache_hit_rate": round(cache_hits / total_requests, 4) if total_requests else 0.0,
        "total_tokens": totals["total_tokens"],
        "total_cost_usd": round(totals["total_cost"], 6),
        "cost_saved_by_cache_usd": round(would_have_cost["total"], 6),
        "today_cost_usd": round(today_cost, 6),
        "daily_budget_usd": settings.DAILY_BUDGET_USD,
        "budget_remaining_usd": round(max(settings.DAILY_BUDGET_USD - today_cost, 0), 6),
    }