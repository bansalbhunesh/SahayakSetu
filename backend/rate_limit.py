"""Shared SlowAPI limiter configuration."""

from __future__ import annotations

import os
import re

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _user_key(request: Request) -> str:
    # Prefer network identity; never trust client user-id first.
    return (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or get_remote_address(request)
        or request.headers.get("x-user-id")
    )


def _safe_storage_uri() -> str:
    raw = (os.getenv("REDIS_URL") or "").strip()
    if not raw:
        return "memory://"
    if raw.startswith(("redis://", "rediss://", "memory://")):
        return raw
    # Handle accidental pastes like: redis-cli --tls -u redis://...
    match = re.search(r"(rediss?://\S+)", raw)
    if match:
        return match.group(1)
    return "memory://"


limiter = Limiter(
    key_func=_user_key,
    storage_uri=_safe_storage_uri(),
    default_limits=["60/minute", "500/hour"],
)
