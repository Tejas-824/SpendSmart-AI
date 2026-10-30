"""
Plain SQLite. One row per question: what was asked, which model answered,
real tokens, cost, who asked, why it was routed that way, and whether it
came from cache or needed a retry.

All dates are UTC, so "today" means the same thing everywhere.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

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


def _utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


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
                cached INTEGER NOT NULL,
                username TEXT NOT NULL DEFAULT 'admin',
                reason TEXT NOT NULL DEFAULT '',
                retried INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # Older databases don't have the newer columns. Add them in place
        # so nobody has to delete logs.db.
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(requests)")}
        migrations = {
            "username": "ALTER TABLE requests ADD COLUMN username TEXT NOT NULL DEFAULT 'admin'",
            "reason": "ALTER TABLE requests ADD COLUMN reason TEXT NOT NULL DEFAULT ''",
            "retried": "ALTER TABLE requests ADD COLUMN retried INTEGER NOT NULL DEFAULT 0",
        }
        for column, statement in migrations.items():
            if column not in existing:
                conn.execute(statement)


def log_request(
    question: str,
    model_used: str,
    model_tier: str,
    tokens_in: int,
    tokens_out: int,
    cost_usd: float,
    cached: bool,
    username: str,
    reason: str,
    retried: bool,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO requests
                (created_at, question, model_used, model_tier, tokens_in, tokens_out,
                 cost_usd, cached, username, reason, retried)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                question, model_used, model_tier, tokens_in, tokens_out,
                cost_usd, int(cached), username, reason, int(retried),
            ),
        )


def get_today_cost(username: str) -> float:
    """Money spent today by this kind of user (guest vs everyone else).
    Cache hits cost nothing, so they don't count."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(cost_usd), 0) AS total
            FROM requests
            WHERE cached = 0
              AND created_at LIKE ?
              AND (username = 'guest') = ?
            """,
            (f"{_utc_today()}%", int(username == "guest")),
        ).fetchone()
        return float(row["total"])


def get_stats(username: str) -> dict:
    big_in, big_out = settings.BIG_INPUT_PER_M, settings.BIG_OUTPUT_PER_M
    small_in, small_out = settings.SMALL_INPUT_PER_M, settings.SMALL_OUTPUT_PER_M
    since = (datetime.now(timezone.utc).date() - timedelta(days=6)).isoformat()

    with get_connection() as conn:
        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS total_requests,
                COALESCE(SUM(cached), 0) AS cache_hits,
                COALESCE(SUM(retried), 0) AS retries,
                COALESCE(SUM(CASE WHEN cached = 0 AND model_tier = 'small' THEN 1 ELSE 0 END), 0) AS small_calls,
                COALESCE(SUM(CASE WHEN cached = 0 AND model_tier = 'big' THEN 1 ELSE 0 END), 0) AS big_calls,
                COALESCE(SUM(tokens_in + tokens_out), 0) AS total_tokens,
                COALESCE(SUM(cost_usd), 0) AS total_cost,
                COALESCE(SUM((tokens_in * ? + tokens_out * ?) / 1000000.0), 0) AS baseline
            FROM requests
            """,
            (big_in, big_out),
        ).fetchone()

        # What the cache hits would have cost if they'd called their own model.
        cache_saved = conn.execute(
            """
            SELECT COALESCE(SUM(
                CASE WHEN model_tier = 'big'
                     THEN (tokens_in * ? + tokens_out * ?)
                     ELSE (tokens_in * ? + tokens_out * ?) END
            ) / 1000000.0, 0) AS total
            FROM requests
            WHERE cached = 1
            """,
            (big_in, big_out, small_in, small_out),
        ).fetchone()["total"]

        day_rows = conn.execute(
            """
            SELECT
                substr(created_at, 1, 10) AS day,
                SUM(CASE WHEN cached = 0 AND model_tier = 'small' THEN 1 ELSE 0 END) AS small_calls,
                SUM(CASE WHEN cached = 0 AND model_tier = 'big' THEN 1 ELSE 0 END) AS big_calls,
                SUM(cached) AS cache_hits,
                SUM(cost_usd) AS cost,
                SUM((tokens_in * ? + tokens_out * ?) / 1000000.0) AS baseline
            FROM requests
            WHERE created_at >= ?
            GROUP BY day
            """,
            (big_in, big_out, since),
        ).fetchall()

    by_day = {row["day"]: row for row in day_rows}
    daily = []
    for offset in range(6, -1, -1):
        day = (datetime.now(timezone.utc).date() - timedelta(days=offset)).isoformat()
        row = by_day.get(day)
        daily.append(
            {
                "date": day,
                "small_calls": int(row["small_calls"]) if row else 0,
                "big_calls": int(row["big_calls"]) if row else 0,
                "cache_hits": int(row["cache_hits"]) if row else 0,
                "cost_usd": round(row["cost"], 8) if row else 0.0,
                "baseline_usd": round(row["baseline"], 8) if row else 0.0,
            }
        )

    total_requests = totals["total_requests"]
    baseline = totals["baseline"]
    saved_total = baseline - totals["total_cost"]
    today_cost = get_today_cost(username)
    budget = settings.budget_for(username)

    return {
        "total_requests": total_requests,
        "cache_hits": totals["cache_hits"],
        "cache_hit_rate": round(totals["cache_hits"] / total_requests, 4) if total_requests else 0.0,
        "small_calls": totals["small_calls"],
        "big_calls": totals["big_calls"],
        "retries": totals["retries"],
        "total_tokens": totals["total_tokens"],
        "total_cost_usd": round(totals["total_cost"], 8),
        "baseline_cost_usd": round(baseline, 8),
        "saved_usd": round(saved_total, 8),
        "saved_pct": round(saved_total / baseline, 4) if baseline > 0 else 0.0,
        "saved_by_cache_usd": round(cache_saved, 8),
        "saved_by_routing_usd": round(saved_total - cache_saved, 8),
        "today_cost_usd": round(today_cost, 8),
        "daily_budget_usd": budget,
        "budget_remaining_usd": round(max(budget - today_cost, 0), 8),
        "budget_used_percent": round(today_cost / budget * 100, 1) if budget > 0 else 100.0,
        "budget_warn_percent": settings.BUDGET_WARN_PERCENT,
        "daily": daily,
    }