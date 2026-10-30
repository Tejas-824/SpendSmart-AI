"""
The only file that talks to Groq. Returns the answer AND the real token
counts Groq reports, so cost is measured, not guessed.
"""

from groq import APIConnectionError, APIStatusError, Groq, RateLimitError

from config import settings
from utils.tokens import count_tokens

_client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

SYSTEM_PROMPT = (
    "You are a helpful, concise assistant. Answer clearly and avoid "
    "padding your response with unnecessary caveats."
)


class LLMError(Exception):
    """Any problem talking to the model, with a message safe to show a user."""


def ask_model(question: str, model: str) -> tuple[str, int, int]:
    """Returns (answer, tokens_in, tokens_out)."""
    if _client is None:
        raise LLMError("No GROQ_API_KEY configured on the server. Add one to backend/.env.")

    extra = {}
    if settings.REASONING_EFFORT and model.startswith("openai/gpt-oss"):
        extra["reasoning_effort"] = settings.REASONING_EFFORT

    try:
        response = _client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0.4,
            max_completion_tokens=settings.MAX_OUTPUT_TOKENS,
            **extra,
        )
    except RateLimitError:
        raise LLMError("The model provider's rate limit was hit. Wait a moment and try again.")
    except APIConnectionError:
        raise LLMError("Couldn't reach the model provider. Check your internet connection.")
    except APIStatusError as exc:
        raise LLMError(f"The model provider returned an error (status {exc.status_code}).")
    except Exception:
        raise LLMError("Something unexpected went wrong while generating a response.")

    answer = (response.choices[0].message.content or "").strip()
    if not answer:
        raise LLMError("The model returned an empty answer. Try again.")

    usage = getattr(response, "usage", None)
    if usage and usage.prompt_tokens is not None and usage.completion_tokens is not None:
        return answer, usage.prompt_tokens, usage.completion_tokens

    # Groq didn't send usage for some reason - estimate instead.
    return answer, count_tokens(question), count_tokens(answer)