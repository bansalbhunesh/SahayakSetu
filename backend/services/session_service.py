"""Redis-backed per-user conversation history with TTL."""

from __future__ import annotations

import json
import hashlib
import hmac
import os
import uuid

import redis.asyncio as redis

from backend.config import HISTORY_WINDOW

SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", str(60 * 60 * 24)))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DAILY_LLM_CAP = int(os.getenv("DAILY_LLM_CAP", "5000"))
SESSION_SECRET = os.getenv("SESSION_SECRET", "").encode("utf-8")

_redis_client: redis.Redis | None = None


def _client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2,
            retry_on_timeout=True,
        )
    return _redis_client


def _key(user_id: str) -> str:
    return f"sess:{user_id}"


def signed_user_id(raw_id: str) -> str:
    if not SESSION_SECRET:
        return raw_id
    sig = hmac.new(SESSION_SECRET, raw_id.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return f"{raw_id}:{sig}"


def verify_user_id(signed: str) -> str | None:
    if not SESSION_SECRET:
        return signed
    if ":" not in signed:
        return None
    raw, sig = signed.rsplit(":", 1)
    expected = hmac.new(SESSION_SECRET, raw.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return raw if hmac.compare_digest(sig, expected) else None


def resolve_user_id(provided: str | None) -> tuple[str, str]:
    token = (provided or "").strip()
    if token:
        verified = verify_user_id(token)
        if verified:
            return verified, token if SESSION_SECRET else verified
    if SESSION_SECRET:
        raw = f"u-{uuid.uuid4().hex[:16]}"
        return raw, signed_user_id(raw)
    # Local/dev fallback if SESSION_SECRET is not configured.
    return (token or "anonymous"), (token or "anonymous")


async def get_history(user_id: str) -> list[dict]:
    try:
        raw = await _client().lrange(_key(user_id), -HISTORY_WINDOW * 2, -1)
        out: list[dict] = []
        for line in raw:
            try:
                payload = json.loads(line)
                if isinstance(payload, dict):
                    out.append(payload)
            except Exception:
                continue
        return out
    except Exception:
        # Best-effort memory: never block user flow due to cache/storage outages.
        return []


async def append(user_id: str, query: str, answer: str) -> None:
    try:
        key = _key(user_id)
        pipe = _client().pipeline()
        pipe.rpush(key, json.dumps({"role": "user", "content": query}))
        pipe.rpush(key, json.dumps({"role": "assistant", "content": answer}))
        pipe.ltrim(key, -HISTORY_WINDOW * 2, -1)
        pipe.expire(key, SESSION_TTL_SECONDS)
        await pipe.execute()
    except Exception:
        pass


async def increment_daily_llm_counter() -> tuple[int, int]:
    """Returns (used_today, cap). Fail-open if Redis unavailable."""
    try:
        count = await _client().incr("budget:llm:today")
        if count == 1:
            await _client().expire("budget:llm:today", 86400)
        return int(count), DAILY_LLM_CAP
    except Exception:
        return 0, DAILY_LLM_CAP
