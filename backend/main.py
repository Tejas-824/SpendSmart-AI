"""
Entry point. Run with: uvicorn main:app --reload

What happens on POST /api/ask, in order:
 1. Cache - same or similar question seen recently? Return it free.
 2. Route - small or big model, and WHY (router/rules.py)
 3. Budget - if today's budget is spent, force the small model
 4. Call the model with fallback + escalation (router/pipeline.py)
 5. Log real tokens and cost, cache the answer, add a budget warning
"""

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from auth import create_access_token, require_auth, verify_password
from cache import memory_cache
from config import settings
from guest import check_guest_limit, get_client_ip
from llm.client import LLMError
from models import AskRequest, AskResponse, LoginRequest, LoginResponse, StatsResponse
from router.budget import budget_warning, enforce_budget
from router.pipeline import answer_question
from router.rules import classify_question
from storage.db import get_stats, init_db, log_request
from utils.tokens import cost_if_big

app = FastAPI(title="TokenWise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
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
    return LoginResponse(access_token=create_access_token(payload.username))


@app.post("/api/auth/guest", response_model=LoginResponse)
def guest_login():
    # Guests get a short 1-hour token.
    return LoginResponse(access_token=create_access_token("guest", expire_minutes=60))


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest, request: Request, user: str = Depends(require_auth)):
    if user == "guest":
        check_guest_limit(get_client_ip(request))

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question can't be empty.")

    # 1. Cache
    if settings.CACHE_ENABLED:
        hit = memory_cache.get(question)
        if hit:
            entry, match = hit
            reason = "answered from cache" if match == "exact" else "matched a similar earlier question"
            log_request(
                question=question,
                model_used=entry["model_used"],
                model_tier=entry["model_tier"],
                tokens_in=entry["tokens_in"],
                tokens_out=entry["tokens_out"],
                cost_usd=0.0,
                cached=True,
                username=user,
                reason=reason,
                retried=False,
            )
            return AskResponse(
                answer=entry["answer"],
                model_used=entry["model_used"],
                model_tier=entry["model_tier"],
                tokens_in=entry["tokens_in"],
                tokens_out=entry["tokens_out"],
                cost_usd=0.0,
                cached=True,
                reason=reason,
                saved_usd=cost_if_big(entry["tokens_in"], entry["tokens_out"]),
                match=match,
                note=(
                    "Served from cache - no model call was made."
                    if match == "exact"
                    else "Matched a similar earlier question - no model call was made."
                ),
            )

    # 2 + 3. Route, then check the budget
    decision = classify_question(question)
    final_tier, budget_note = enforce_budget(decision.tier, user)

    # 4. Call the model (fallback + escalation live inside)
    try:
        result = answer_question(question, final_tier, user)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # 5. Log, cache, warn
    log_request(
        question=question,
        model_used=result.model,
        model_tier=result.tier,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        cost_usd=result.cost_usd,
        cached=False,
        username=user,
        reason=decision.reason,
        retried=result.retried,
    )
    if settings.CACHE_ENABLED:
        memory_cache.set(
            question,
            {
                "answer": result.answer,
                "model_used": result.model,
                "model_tier": result.tier,
                "tokens_in": result.tokens_in,
                "tokens_out": result.tokens_out,
            },
        )

    # If the budget already forced the small model, that note says it all.
    warning = None if budget_note else budget_warning(user)
    notes = [budget_note, *result.notes, warning]
    return AskResponse(
        answer=result.answer,
        model_used=result.model,
        model_tier=result.tier,
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        cost_usd=result.cost_usd,
        cached=False,
        reason=decision.reason,
        saved_usd=round(cost_if_big(result.tokens_in, result.tokens_out) - result.cost_usd, 8),
        retried=result.retried,
        note=" ".join(n for n in notes if n) or None,
    )


@app.get("/api/stats", response_model=StatsResponse)
def stats(user: str = Depends(require_auth)):
    return get_stats(user)