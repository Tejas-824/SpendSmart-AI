"""
Calls the model, with two safety nets:

 1. FALLBACK - if the chosen model fails (rate limit, retired model, down),
    try the other one before giving up.
 2. ESCALATION - if the small model gives a weak answer ("I don't know"),
    ask the big model instead, as long as today's budget allows it.

Cost is the sum of every call made, so a retry is never hidden.
"""

from dataclasses import dataclass, field

from llm.client import LLMError, ask_model
from router.budget import enforce_budget
from router.rules import model_for_tier
from utils.tokens import estimate_cost

# If the start of a small-model answer contains one of these, it gave up.
WEAK_PHRASES = (
    "i don't know", "i do not know", "i'm not sure", "i am not sure",
    "i cannot", "i can't", "as an ai", "unable to",
)


@dataclass
class Result:
    answer: str
    model: str
    tier: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    retried: bool = False
    notes: list[str] = field(default_factory=list)


def looks_weak(answer: str) -> bool:
    start = answer.strip().lower()[:120]
    return any(phrase in start for phrase in WEAK_PHRASES)


def _call(question: str, tier: str):
    model = model_for_tier(tier)
    answer, tokens_in, tokens_out = ask_model(question, model)
    return model, answer, tokens_in, tokens_out, estimate_cost(tokens_in, tokens_out, tier)


def answer_question(question: str, tier: str, username: str) -> Result:
    notes: list[str] = []
    other = "small" if tier == "big" else "big"

    try:
        model, answer, t_in, t_out, cost = _call(question, tier)
        used = tier
    except LLMError as first_error:
        # Fallback. Never fall UP to the big model if the budget is spent.
        if other == "big" and enforce_budget("big", username)[0] == "small":
            raise first_error
        try:
            model, answer, t_in, t_out, cost = _call(question, other)
        except LLMError:
            raise first_error
        used = other
        notes.append(f"The {tier} model failed, so the {other} model answered instead.")

    result = Result(answer, model, used, t_in, t_out, cost, notes=notes)

    # Escalation: small model gave a weak answer, try the big one.
    if used == "small" and looks_weak(answer) and enforce_budget("big", username)[0] == "big":
        try:
            model2, answer2, in2, out2, cost2 = _call(question, "big")
        except LLMError:
            return result  # keep the small answer, nothing lost
        result = Result(
            answer2, model2, "big",
            t_in + in2, t_out + out2, round(cost + cost2, 8),
            retried=True,
            notes=notes + ["The small model wasn't confident, so the big model answered."],
        )

    return result