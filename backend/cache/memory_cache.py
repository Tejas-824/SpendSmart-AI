"""
In-memory cache with two upgrades over "exact match only":

 1. EXPIRY - an answer is thrown away after CACHE_TTL_SECONDS (24h default),
    so old answers don't live forever.
 2. SIMILAR QUESTIONS - "what is a REST API?" and "what's REST API" share
    one answer. We drop filler words, then compare the leftover keywords.
    This is word overlap, NOT embeddings or a vector database.

Resets when the server restarts.
"""

import re
import time

from config import settings

MAX_ENTRIES = 500

# Filler words ignored when comparing. Words that carry meaning
# (not, explain, compare, numbers...) are kept on purpose.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "what", "whats", "s", "of",
    "to", "in", "on", "for", "and", "or", "me", "please", "tell", "about",
    "give", "i", "you", "can", "could", "do", "does", "it", "this", "that",
}

_store: dict[str, dict] = {}


def _normalize(question: str) -> str:
    return " ".join(question.strip().lower().split())


def _keywords(question: str) -> frozenset:
    words = re.findall(r"[a-z0-9]+", question.lower())
    return frozenset(w for w in words if w not in STOPWORDS)


def _is_fresh(entry: dict) -> bool:
    return time.time() - entry["saved_at"] < settings.CACHE_TTL_SECONDS


def get(question: str) -> tuple[dict, str] | None:
    """Returns (entry, "exact" or "similar"), or None on a miss."""
    key = _normalize(question)

    entry = _store.get(key)
    if entry is not None:
        if _is_fresh(entry):
            return entry, "exact"
        del _store[key]

    words = _keywords(question)
    if len(words) < 2:  # too little to compare safely
        return None

    best, best_score = None, 0.0
    for stored_key, stored in list(_store.items()):
        if not _is_fresh(stored):
            del _store[stored_key]
            continue
        union = len(words | stored["keywords"])
        score = len(words & stored["keywords"]) / union if union else 0.0
        if score > best_score:
            best, best_score = stored, score

    if best is not None and best_score >= settings.CACHE_SIMILARITY:
        return best, "similar"
    return None


def set(question: str, entry: dict) -> None:
    if len(_store) >= MAX_ENTRIES:
        oldest = min(_store, key=lambda k: _store[k]["saved_at"])
        del _store[oldest]
    _store[_normalize(question)] = {
        **entry,
        "saved_at": time.time(),
        "keywords": _keywords(question),
    }


def size() -> int:
    return len(_store)