"""
Entry point. Run with: uvicorn main:app --reload

What happens on POST /api/ask, in order:
 1. Check cache - if we've seen this exact question before, return it
    for free, no model call at all.
 2. Decide small vs big model from the question itself (router/rules.py)
 3. Check today's budget - if it's already spent, force the small model
    even if the rule above picked the big one (router/budget.py)
 4. Call the model, count tokens, estimate cost
 5. Log it and cache it
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from auth import create_access_token, require_auth, verify_password
from cache import memory_cache
from config import settings
from llm.client import LLMError, ask_model
from models import AskRequest, AskResponse, LoginRequest, LoginResponse, StatsResponse
from router.budget import enforce_budget
from router.rules import classify_question, model_for_tier
from storage.db import get_stats, init_db, log_request
from utils.tokens import count_tokens, estimate_cost

app = FastAPI(title="TokenWise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    if payload.username != settings.AUTH_USERNAME or not verify_password(payload.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    token = create_access_token(payload.username)
    return LoginResponse(access_token=token)


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest, _user: str = Depends(require_auth)):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question can't be empty.")

    # 1. Cache lookup
    if settings.CACHE_ENABLED:
        cached_entry = memory_cache.get(question)
        if cached_entry:
            log_request(
                question=question,
                model_used=cached_entry["model_used"],
                model_tier=cached_entry["model_tier"],
                tokens_in=cached_entry["tokens_in"],
                tokens_out=cached_entry["tokens_out"],
                cost_usd=0.0,
                cached=True,
            )
            return AskResponse(
                answer=cached_entry["answer"],
                model_used=cached_entry["model_used"],
                model_tier=cached_entry["model_tier"],
                tokens_in=cached_entry["tokens_in"],
                tokens_out=cached_entry["tokens_out"],
                cost_usd=0.0,
                cached=True,
                note="Served from cache - no model call was made.",
            )

    # 2. Route
    requested_tier = classify_question(question)

    # 3. Budget guard
    final_tier, budget_note = enforce_budget(requested_tier)
    model = model_for_tier(final_tier)

    # 4. Call the model
    try:
        answer = ask_model(question, model)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    tokens_in = count_tokens(question)
    tokens_out = count_tokens(answer)
    cost = estimate_cost(tokens_in, tokens_out, final_tier)

    # 5. Log + cache
    log_request(
        question=question,
        model_used=model,
        model_tier=final_tier,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
        cached=False,
    )
    if settings.CACHE_ENABLED:
        memory_cache.set(
            question,
            {
                "answer": answer,
                "model_used": model,
                "model_tier": final_tier,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
            },
        )

    return AskResponse(
        answer=answer,
        model_used=model,
        model_tier=final_tier,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
        cached=False,
        note=budget_note,
    )


@app.get("/api/stats", response_model=StatsResponse)
def stats(_user: str = Depends(require_auth)):
    return get_stats()