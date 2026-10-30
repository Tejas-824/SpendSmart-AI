"""
Daily budget guard. Admin and guests each have their own budget, so
demo visitors can never use up yours.

 - Under the limit: the routing rule decides.
 - Over the limit: everything is forced onto the small model.
 - At 80% (BUDGET_WARN_PERCENT): the answer carries a warning note.
"""

from config import settings
from storage.db import get_today_cost


def budget_used_percent(username: str) -> float:
    limit = settings.budget_for(username)
    if limit <= 0:
        return 100.0
    return round(get_today_cost(username) / limit * 100, 1)


def enforce_budget(requested_tier: str, username: str) -> tuple[str, str | None]:
    """Returns (final_tier, note). note is None unless the budget changed
    the outcome."""
    if requested_tier == "small":
        return "small", None

    spent = get_today_cost(username)
    limit = settings.budget_for(username)
    if spent >= limit:
        note = (
            f"Daily budget of ${limit:.4f} reached (${spent:.6f} spent) - "
            "using the small model instead."
        )
        return "small", note

    return "big", None


def budget_warning(username: str) -> str | None:
    """Call AFTER logging a request, so the percentage includes it."""
    percent = budget_used_percent(username)
    if percent >= 100:
        return "Daily budget reached - new requests will use the small model."
    if percent >= settings.BUDGET_WARN_PERCENT:
        return f"Heads up: {percent:.0f}% of today's budget is used."
    return None