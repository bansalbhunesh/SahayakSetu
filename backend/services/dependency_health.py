"""Dependency readiness probes for runtime orchestration and health endpoints."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.config import CHAT_MODEL, GROQ_API_KEY, qdrant_client
from backend.services.session_service import _client


async def _qdrant_ready() -> bool:
    try:
        await asyncio.wait_for(
            asyncio.to_thread(qdrant_client.get_collections),
            timeout=2.5,
        )
        return True
    except Exception:
        return False


async def _redis_ready() -> bool:
    try:
        pong = await asyncio.wait_for(_client().ping(), timeout=2.0)
        return bool(pong)
    except Exception:
        return False


def _llm_ready() -> dict[str, Any]:
    from backend.config import GEMINI_API_KEY, gemini_model

    return {
        "primary": CHAT_MODEL if GEMINI_API_KEY and gemini_model is not None else "unconfigured",
        "fallback": "groq-llama-3.3" if GROQ_API_KEY else "none",
        "ready": bool((GEMINI_API_KEY and gemini_model is not None) or GROQ_API_KEY),
    }


async def readiness_snapshot() -> dict[str, Any]:
    qdrant_ok, redis_ok = await asyncio.gather(_qdrant_ready(), _redis_ready())
    llm = _llm_ready()
    ready = bool(qdrant_ok and redis_ok and llm["ready"])
    return {
        "ready": ready,
        "dependencies": {
            "qdrant": "up" if qdrant_ok else "down",
            "redis": "up" if redis_ok else "down",
            "llm": llm,
        },
    }
