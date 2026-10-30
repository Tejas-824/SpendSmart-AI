"""Request and response shapes for the API."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    answer: str
    model_used: str
    model_tier: str  # "small" or "big"
    tokens_in: int
    tokens_out: int
    cost_usd: float
    cached: bool
    reason: str                  # why it was routed this way
    saved_usd: float             # vs always using the big model
    retried: bool = False        # small model was weak, big model re-answered
    match: str | None = None     # "exact" or "similar" when served from cache
    note: str | None = None


class DailyStat(BaseModel):
    date: str
    small_calls: int
    big_calls: int
    cache_hits: int
    cost_usd: float
    baseline_usd: float          # what the day would have cost on the big model


class StatsResponse(BaseModel):
    total_requests: int
    cache_hits: int
    cache_hit_rate: float
    small_calls: int
    big_calls: int
    retries: int
    total_tokens: int
    total_cost_usd: float
    baseline_cost_usd: float
    saved_usd: float
    saved_pct: float
    saved_by_cache_usd: float
    saved_by_routing_usd: float
    today_cost_usd: float
    daily_budget_usd: float
    budget_remaining_usd: float
    budget_used_percent: float
    budget_warn_percent: int
    daily: list[DailyStat]