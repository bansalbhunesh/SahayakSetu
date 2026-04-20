"""Shared SlowAPI limiter configuration."""

from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _user_key(request: Request) -> str:
    # Prefer app-provided user id, then forwarded IP, then socket IP.
    return (
        request.headers.get("x-user-id")
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or get_remote_address(request)
    )


limiter = Limiter(
    key_func=_user_key,
    storage_uri=os.getenv("REDIS_URL", "memory://"),
    default_limits=["60/minute", "500/hour"],
)
