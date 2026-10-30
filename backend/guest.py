"""
Limits for demo visitors. Counters live in memory, so they reset when the
server restarts. That's fine for a demo project.
"""

from datetime import date

from fastapi import HTTPException, Request

from config import settings

_per_ip: dict[tuple[str, str], int] = {}
_global_count: dict[str, int] = {}


def get_client_ip(request: Request) -> str:
    # Behind Render's proxy the real IP is in this header.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_guest_limit(ip: str) -> None:
    today = date.today().isoformat()

    # Drop old days so the dicts don't grow forever.
    for key in [k for k in _per_ip if k[1] != today]:
        del _per_ip[key]
    for key in [k for k in _global_count if k != today]:
        del _global_count[key]

    if _global_count.get(today, 0) >= settings.GUEST_GLOBAL_DAILY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="The demo has hit its daily limit. Please try again tomorrow.",
        )

    if _per_ip.get((ip, today), 0) >= settings.GUEST_DAILY_LIMIT_PER_IP:
        raise HTTPException(
            status_code=429,
            detail=f"You've used your {settings.GUEST_DAILY_LIMIT_PER_IP} free demo questions for today. Come back tomorrow!",
        )

    _per_ip[(ip, today)] = _per_ip.get((ip, today), 0) + 1
    _global_count[today] = _global_count.get(today, 0) + 1