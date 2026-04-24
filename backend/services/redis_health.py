"""Shared Redis-reachability probe used by rate_limit + session/quota code.

Runs exactly once per process lifetime. Short socket timeout so DNS failures
don't block startup. Result is cached.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_checked = False
_reachable = False


def _probe() -> bool:
    url = (os.getenv("REDIS_URL") or "").strip()
    if not url.startswith(("redis://", "rediss://")):
        return False
    try:
        import redis as _redis
        client = _redis.from_url(
            url,
            socket_timeout=2,
            socket_connect_timeout=2,
        )
        try:
            client.ping()
            return True
        finally:
            try:
                client.close()
            except Exception:
                pass
    except Exception as e:
        logger.warning(
            "redis_health_probe_failed",
            extra={"url_prefix": (url or "")[:30], "error": str(e)[:200]},
        )
        return False


def is_reachable() -> bool:
    """Cached boolean — safe to call from any code path, returns instantly after first call."""
    global _checked, _reachable
    if not _checked:
        _reachable = _probe()
        _checked = True
        if not _reachable:
            print(
                "[WARN] Redis probe failed — quota + session services will fail-open.",
                flush=True,
            )
    return _reachable
