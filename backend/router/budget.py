"""
Keeps the daily estimated spend under a cap. If today's running total
is already at the limit, every request gets forced onto the cheap
model no matter what the routing rule decided.
"""

from config import settings
from storage.db import get_today_cost


def enforce_budget(requested_tier: str) -> tuple[str, str | None]:
    if requested_tier == "small":
        return "small", None

    today_spent = get_today_cost()
    if today_spent >= settings.DAILY_BUDGET_USD:
        note = (
            f"Daily budget of ${settings.DAILY_BUDGET_USD:.2f} reached "
            f"(${today_spent:.4f} spent) - using the lightweight model instead."
        )
        return "small", note

    return "big", None