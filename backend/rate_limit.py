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
    # Keep rate limiting resilient: default to in-memory storage unless an explicit
    # limiter storage URI is provided. This avoids request-time 500s when shared
    # Redis env vars are malformed or temporarily unavailable.
    raw = (os.getenv("RATE_LIMIT_STORAGE_URI") or "").strip()
    if not raw:
        return "memory://"
    if raw.startswith(("redis://", "rediss://", "memory://")):
        return raw
    return "memory://"


limiter = Limiter(
    key_func=_user_key,
    storage_uri=_safe_storage_uri(),
    default_limits=["60/minute", "500/hour"],
)
