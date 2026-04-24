"""Redis-backed per-user conversation history with TTL."""

from __future__ import annotations

import json
import hashlib
import hmac
import logging
import os
import re
import uuid
from functools import wraps
from types import SimpleNamespace

try:
    import redis.asyncio as redis
except ModuleNotFoundError:  # pragma: no cover - local/dev test fallback
    redis = SimpleNamespace(  # type: ignore[assignment]
        Redis=object,
        ConnectionError=RuntimeError,
        TimeoutError=TimeoutError,
        from_url=lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("redis package missing")),
    )

from backend.config import HISTORY_WINDOW


def _strict_quota_redis_fail() -> bool:
    """When True, Redis errors deny quota (production default) instead of fail-open.

    Auto-downgrades to fail-open when Redis is known-unreachable at startup — there
    is no way to enforce a strict shared counter without the shared store, and
    returning 503 on every request would be worse than skipping the quota gate.
    """
    raw = (os.getenv("REDIS_QUOTA_STRICT") or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    from backend.services.redis_health import is_reachable
    if raw in ("1", "true", "yes", "on"):
        return is_reachable()
    if os.getenv("ENV", "development").strip().lower() != "production":
        return False
    return is_reachable()

SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", str(60 * 60 * 24)))
def _safe_redis_url() -> str:
    raw = (os.getenv("REDIS_URL") or "").strip()
    if not raw:
        return "redis://localhost:6379/0"
    if raw.startswith(("redis://", "rediss://")):
        return raw
    # Handle accidental pastes like: redis-cli --tls -u redis://...
    match = re.search(r"(rediss?://\S+)", raw)
    if match:
        return match.group(1)
    return "redis://localhost:6379/0"


REDIS_URL = _safe_redis_url()
DAILY_LLM_CAP = int(os.getenv("DAILY_LLM_CAP", "5000"))
SESSION_SECRET = os.getenv("SESSION_SECRET", "").encode("utf-8")

_redis_client: redis.Redis | None = None
logger = logging.getLogger(__name__)
_RAISE = object()


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
    except Exception as e:
        logger.warning(
            "session_history_unavailable",
            extra={"error": str(e)[:200]},
            exc_info=True,
        )
        return []


def _redis_safe(fail_default):
    """Wrap redis operations with explicit fail-open / fail-closed policy."""

    def deco(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except Exception:
                logger.warning("redis_unavailable", extra={"fn": fn.__name__}, exc_info=True)
                if fail_default is _RAISE:
                    raise
                return fail_default

        return wrapper

    return deco


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
        logger.warning("session_append_failed", extra={"user_id": user_id[:24]}, exc_info=True)


async def increment_daily_llm_counter() -> tuple[int, int]:
    """Returns (used_today, cap). In production, Redis failure blocks LLM (fail-closed)."""
    try:
        count = await _client().incr("budget:llm:today")
        if count == 1:
            await _client().expire("budget:llm:today", 86400)
        return int(count), DAILY_LLM_CAP
    except Exception:
        logger.warning("redis_unavailable", extra={"fn": "increment_daily_llm_counter"}, exc_info=True)
        if _strict_quota_redis_fail():
            return DAILY_LLM_CAP + 1, DAILY_LLM_CAP
        return 0, DAILY_LLM_CAP


async def check_user_llm_quota(user_id: str, daily_max: int = 100) -> bool:
    """Returns True if user is under daily LLM cap. In production, Redis errors deny (fail-closed)."""
    try:
        key = f"quota:llm:{user_id}"
        count = await _client().incr(key)
        if count == 1:
            await _client().expire(key, 86400)
        return int(count) <= daily_max
    except Exception:
        logger.warning("redis_unavailable", extra={"fn": "check_user_llm_quota"}, exc_info=True)
        if _strict_quota_redis_fail():
            return False
        return True
