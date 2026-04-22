"""Redis answer cache for repeated queries."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import unicodedata
from typing import Any

from backend.services.session_service import _client

CACHE_TTL_SECONDS = int(os.getenv("ANSWER_CACHE_TTL_SECONDS", str(60 * 60 * 6)))
logger = logging.getLogger(__name__)


def _normalize_cache_query(query: str) -> str:
    """Unicode NFKC + casefold + whitespace collapse so cache keys match user intent."""
    s = unicodedata.normalize("NFKC", (query or ""))
    return " ".join(s.strip().casefold().split())


def _cache_key(query: str, language: str) -> str:
    normalized = _normalize_cache_query(query)
    lang = (language or "").strip().casefold()
    digest = hashlib.sha256(f"{normalized}|{lang}".encode("utf-8")).hexdigest()[:24]
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
        logger.warning("answer_cache_get_failed", exc_info=True)
        return None


async def set(query: str, language: str, payload: dict[str, Any]) -> None:
    try:
        await _client().setex(
            _cache_key(query, language),
            CACHE_TTL_SECONDS,
            json.dumps(payload, ensure_ascii=False),
        )
    except Exception:
        logger.warning("answer_cache_set_failed", exc_info=True)
