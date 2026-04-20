"""Intent moderation — runs before retrieval."""

from __future__ import annotations

import json
import logging
import re

from backend.config import MODERATION_STRICT
from backend.models.response_models import ModerationResult
from backend.prompts.moderation_prompt import MODERATION_PROMPT, MODERATION_PROMPT_TRANSCRIPT
from backend.services import llm_service

logger = logging.getLogger(__name__)

_FAIL_CLOSED = ModerationResult(
    allowed=False,
    category="moderation_error",
    redirect_message="Sorry, we couldn't verify your request. Please try again shortly.",
)

_FAIL_OPEN = ModerationResult(
    allowed=True,
    category="welfare_scheme",
    redirect_message=None,
)


def _build_moderation_prompt(classifier_input: str, *, conversation: bool) -> str:
    if conversation:
        return MODERATION_PROMPT_TRANSCRIPT.format(transcript=classifier_input)
    return MODERATION_PROMPT.format(query=classifier_input)


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_json_best_effort(raw: str) -> dict:
    cleaned = _strip_json_fences(raw)
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        # Some model responses include a short preface/postfix around JSON.
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            raise
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}


async def _classify_intent(classifier_input: str, *, conversation: bool) -> ModerationResult:
    prompt = _build_moderation_prompt(classifier_input, conversation=conversation)
    raw = ""
    try:
        raw = await llm_service.run_moderation_raw_prompt(prompt)
        data = _parse_json_best_effort(raw)
        allowed = bool(data.get("allowed", True))
        category = str(data.get("category", "welfare_scheme"))
        redirect = data.get("redirect_message")
        redirect_message = str(redirect) if redirect is not None else None
        if redirect_message == "null":
            redirect_message = None
        return ModerationResult(
            allowed=allowed,
            category=category,
            redirect_message=redirect_message,
        )
    except json.JSONDecodeError as exc:
        logger.warning(
            "moderation_parse_error reason=json_decode strict=%s conversation=%s error=%s raw_preview=%r",
            MODERATION_STRICT,
            conversation,
            exc,
            (raw[:500] + "…") if len(raw) > 500 else raw,
        )
        if MODERATION_STRICT:
            logger.warning(
                "moderation_fallback action=fail_closed reason=json_parse_error strict=%s",
                MODERATION_STRICT,
            )
            return _FAIL_CLOSED
        logger.warning(
            "moderation_fallback action=fail_open reason=json_parse_error strict=%s",
            MODERATION_STRICT,
        )
        return _FAIL_OPEN
    except Exception as exc:
        logger.warning(
            "moderation_call_error strict=%s conversation=%s error=%s",
            MODERATION_STRICT,
            conversation,
            exc,
            exc_info=True,
        )
        if MODERATION_STRICT:
            logger.warning(
                "moderation_fallback action=fail_closed reason=moderation_call_error strict=%s",
                MODERATION_STRICT,
            )
            return _FAIL_CLOSED
        logger.warning(
            "moderation_fallback action=fail_open reason=moderation_call_error strict=%s",
            MODERATION_STRICT,
        )
        return _FAIL_OPEN


async def check(query: str, language: str) -> ModerationResult:  # noqa: ARG001 — language reserved for future heuristics
    return await _classify_intent(query, conversation=False)


async def check_conversation_transcript(transcript: str, language: str) -> ModerationResult:  # noqa: ARG001
    """Single moderation pass over full dialogue (e.g. custom LLM) before generation."""
    text = (transcript or "").strip()
    if not text:
        return ModerationResult(allowed=True, category="welfare_scheme", redirect_message=None)
    return await _classify_intent(text, conversation=True)
