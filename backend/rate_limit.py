"""Shared SlowAPI limiter configuration."""

from __future__ import annotations

import os
import re

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None or not str(v).strip():
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def _user_key(request: Request) -> str:
    # Prefer network identity; never trust client user-id first.
    return (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or get_remote_address(request)
        or request.headers.get("x-user-id")
    )


def _safe_storage_uri() -> str:
    # Explicit URI wins. Otherwise, in production (or RATE_LIMIT_USE_REDIS), share REDIS_URL
    # so limits apply across multiple app instances.
    raw = (os.getenv("RATE_LIMIT_STORAGE_URI") or "").strip()
    if raw.startswith(("redis://", "rediss://", "memory://")):
        return raw
    if raw:
        return "memory://"
    use_redis = _env_bool(
        "RATE_LIMIT_USE_REDIS",
        os.getenv("ENV", "development").strip().lower() == "production",
    )
    if use_redis:
        red = (os.getenv("REDIS_URL") or "").strip()
        if red.startswith(("redis://", "rediss://")):
            return red
    return "memory://"


limiter = Limiter(
    key_func=_user_key,
    storage_uri=_safe_storage_uri(),
    default_limits=["60/minute", "500/hour"],
)
