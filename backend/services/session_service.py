"""In-memory per-user conversation history."""

from __future__ import annotations

from backend.config import EVICT_COUNT, HISTORY_WINDOW, MAX_SESSION_STORE_SIZE

_session_store: dict[str, list[dict]] = {}


def get_history(user_id: str) -> list[dict]:
    stored = _session_store.get(user_id, [])
    return list(stored)


def evict_if_needed() -> None:
    if len(_session_store) > MAX_SESSION_STORE_SIZE:
        for key in list(_session_store.keys())[:EVICT_COUNT]:
            del _session_store[key]


def append(user_id: str, query: str, answer: str) -> None:
    history = _session_store.setdefault(user_id, [])
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": answer})
    _session_store[user_id] = history[-HISTORY_WINDOW:]
    evict_if_needed()
