"""Redis answer cache for repeated queries."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from backend.services.session_service import _client

CACHE_TTL_SECONDS = int(os.getenv("ANSWER_CACHE_TTL_SECONDS", str(60 * 60 * 6)))


def _cache_key(query: str, language: str) -> str:
    normalized = " ".join(query.strip().lower().split())
    digest = hashlib.sha256(f"{normalized}|{language}".encode("utf-8")).hexdigest()[:24]
    return f"cache:answer:{digest}"


async def get(query: str, language: str) -> dict[str, Any] | None:
    try:
        raw = await _client().get(_cache_key(query, language))
        if not raw:
            return None
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return payload
        return None
    except Exception:
        return None


async def set(query: str, language: str, payload: dict[str, Any]) -> None:
    try:
        await _client().setex(
            _cache_key(query, language),
            CACHE_TTL_SECONDS,
            json.dumps(payload, ensure_ascii=False),
        )
    except Exception:
        pass
