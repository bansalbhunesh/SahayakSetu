"""Vapi webhook freshness + idempotency (replay mitigation within a short window)."""

from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def _parse_epoch_seconds(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        if v > 1e12:  # milliseconds
            return v / 1000.0
        return v
    s = str(value).strip()
    if not s:
        return None
    if s.isdigit():
        vi = int(s)
        return vi / 1000.0 if vi > 1e12 else float(vi)
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).timestamp()
    except Exception:
        return None


def extract_webhook_timestamp_seconds(parsed: dict[str, Any]) -> float | None:
    """Best-effort timestamp from signed JSON (body fields only — not unsigned headers)."""
    candidates: list[float] = []
    for key in ("timestamp", "createdAt", "startedAt", "date"):
        ts = _parse_epoch_seconds(parsed.get(key))
        if ts is not None:
            candidates.append(ts)
    msg = parsed.get("message")
    if isinstance(msg, dict):
        for key in ("timestamp", "createdAt", "startedAt"):
            ts = _parse_epoch_seconds(msg.get(key))
            if ts is not None:
                candidates.append(ts)
    return max(candidates) if candidates else None


def assert_webhook_timestamp_fresh(
    *,
    parsed: dict[str, Any],
    max_skew_seconds: int,
    require_timestamp: bool,
) -> None:
    ts = extract_webhook_timestamp_seconds(parsed)
    if ts is None:
        if require_timestamp:
            raise HTTPException(
                status_code=401,
                detail="Webhook payload must include a recognizable timestamp (e.g. message.createdAt).",
            )
        return
    now = time.time()
    if abs(now - ts) > max_skew_seconds:
        raise HTTPException(status_code=401, detail="Webhook timestamp outside allowed window.")


async def reserve_vapi_webhook_idempotency(raw_body: bytes, ttl_seconds: int = 600) -> bool:
    """
    Returns True if this request should be processed, False if it is a near-term replay
    of an identical body (same HMAC-valid payload resent).
    """
    from backend.services.session_service import _client

    digest = hashlib.sha256(raw_body).hexdigest()
    key = f"vapi:webhook:dedupe:{digest}"
    try:
        # True when key was set; None/False when key already existed (NX miss).
        ok = await _client().set(key, "1", nx=True, ex=ttl_seconds)
        return ok is True
    except Exception:
        logger.warning("vapi_webhook_dedupe_redis_failed", exc_info=True)
        return True
