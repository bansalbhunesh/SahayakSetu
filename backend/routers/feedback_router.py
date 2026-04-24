"""Collects 👍/👎 reactions and stores them in Redis for quality monitoring."""

import logging
import time

from fastapi import APIRouter, Body, Request
from pydantic import BaseModel, Field

from backend.rate_limit import limiter
from backend.services.session_service import _client as _redis

router = APIRouter(tags=["feedback"])
logger = logging.getLogger(__name__)

_FEEDBACK_KEY = "feedback:reactions"
_MAX_STORED = 1000


class FeedbackRequest(BaseModel):
    value: str = Field(..., pattern="^(up|down)$")
    trace_id: str | None = Field(default=None, max_length=64)
    session_user_id: str | None = Field(default=None, max_length=128)
    answer_preview: str | None = Field(default=None, max_length=200)
    query_preview: str | None = Field(default=None, max_length=100)


@router.post(
    "/api/feedback",
    summary="Record user 👍/👎 reaction",
    description="Stores last 1000 reactions in Redis sorted-set keyed to trace IDs.",
)
@limiter.limit("20/minute")
async def handle_feedback(request: Request, body: FeedbackRequest = Body(...)):
    try:
        member = "|".join([
            body.value,
            body.trace_id or "anon",
            (body.query_preview or "")[:80],
            (body.answer_preview or "")[:120],
        ])
        client = _redis()
        pipe = client.pipeline()
        pipe.zadd(_FEEDBACK_KEY, {member: time.time()})
        pipe.zremrangebyrank(_FEEDBACK_KEY, 0, -(_MAX_STORED + 1))
        await pipe.execute()
        logger.info(
            "feedback_stored",
            extra={
                "value": body.value,
                "trace_id": (body.trace_id or "")[:16],
                "session_prefix": (body.session_user_id or "")[:8],
            },
        )
    except Exception:
        logger.warning("feedback_store_failed", exc_info=True)
    return {"ok": True}
