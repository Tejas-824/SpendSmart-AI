"""
The only file in the project that knows Groq exists. If this project
ever switches to Gemini or a local Ollama model, this is the one file
that changes.
"""

from groq import Groq, APIConnectionError, APIStatusError, RateLimitError

from config import settings

_client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

SYSTEM_PROMPT = (
    "You are a helpful, concise assistant. Answer clearly and avoid "
    "padding your response with unnecessary caveats."
)


class LLMError(Exception):
    """Raised for any problem talking to the model, with a message
    that's safe to show directly to a user."""


def ask_model(question: str, model: str) -> str:
    if _client is None:
        raise LLMError("No GROQ_API_KEY configured on the server. Add one to backend/.env.")

    try:
        response = _client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0.4,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()

    except RateLimitError:
        raise LLMError("The model provider's rate limit was hit. Wait a moment and try again.")
    except APIConnectionError:
        raise LLMError("Couldn't reach the model provider. Check your internet connection.")
    except APIStatusError as exc:
        raise LLMError(f"The model provider returned an error (status {exc.status_code}).")
    except Exception:
        raise LLMError("Something unexpected went wrong while generating a response.")