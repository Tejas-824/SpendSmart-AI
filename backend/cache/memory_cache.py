"""
The whole cache is one dictionary. If someone asks the exact same
question (ignoring case/whitespace) twice, we skip calling the LLM
entirely and return the saved answer. Resets on server restart.
"""

_store: dict[str, dict] = {}


def _normalize(question: str) -> str:
    return " ".join(question.strip().lower().split())


def get(question: str) -> dict | None:
    return _store.get(_normalize(question))


def set(question: str, entry: dict) -> None:
    _store[_normalize(question)] = entry


def size() -> int:
    return len(_store)