"""Request and response shapes for the API. Kept separate so main.py
stays readable."""

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
    model_tier: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    cached: bool
    note: str | None = None


class StatsResponse(BaseModel):
    total_requests: int
    cache_hits: int
    cache_hit_rate: float
    total_tokens: int
    total_cost_usd: float
    cost_saved_by_cache_usd: float
    today_cost_usd: float
    daily_budget_usd: float
    budget_remaining_usd: float