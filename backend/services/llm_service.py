"""LLM generation — Gemini primary, Groq fallback."""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import re
import threading
from collections.abc import Awaitable, Callable

from backend.config import (
    CHAT_MODEL,
    AGENT_PLAN_CALL_TIMEOUT_S,
    LLM_CALL_TIMEOUT_S,
    API_RETRY_ATTEMPTS,
    API_RETRY_BASE_DELAY_S,
    API_RETRY_MAX_DELAY_S,
    MAX_PROMPT_CHARS,
    REWRITE_QUERY_TIMEOUT_S,
    gemini_model,
    groq_client,
)
from backend.services.resilience import async_retry, with_timeout
from backend.prompts.system_prompt import SYSTEM_PROMPT
logger = logging.getLogger(__name__)

MARK_ANSWER = "<<<ANSWER>>>"
MARK_WHY = "<<<WHY_IT_FITS>>>"
MARK_NEAR = "<<<NEAR_MISS>>>"

STRUCTURED_SUFFIX = f"""
---
OUTPUT STRUCTURE (keep these marker lines EXACTLY in English; all other content in Target Language):

{MARK_ANSWER}
[Main answer. When naming a scheme from the Citation index, put its number in brackets right after the name (e.g. PM-Kisan [1]). End with a 👉 Next step line. No invented URLs.]

{MARK_WHY}
- [Bullet: only if explicitly supported by Database Context; else one line: use the exact honesty phrase from system rules]
- [Optional second bullet only if clearly evidenced]

{MARK_NEAR}
[If Near-miss context below is empty or "(none)", write exactly: None]
[Otherwise 1–2 near-miss schemes: missing condition + one practical tip each]
"""


def build_messages(
    query: str,
    context: str,
    history: list[dict],
    language: str,
    *,
    near_miss_context: str = "",
    citation_index_block: str = "",
    source_index_block: str = "",
    json_mode: bool = False,
    detected_query_language: str | None = None,
    language_register_hint: str | None = None,
) -> list[dict]:
    from backend.config import LLM_HISTORY_MESSAGE_LIMIT

    near_block = (
        near_miss_context.strip()
        if near_miss_context.strip()
        else "(none — do not invent near-miss schemes.)"
    )

    cite_section = ""
    if citation_index_block.strip():
        cite_section = (
            "Citation index (reference numbers for the main answer ONLY — use these exact [n] tokens):\n"
            f"{citation_index_block.strip()}\n\n"
        )

    if json_mode:
        source_section = ""
        if source_index_block.strip():
            source_section = f"SOURCES:\n{source_index_block.strip()}\n\n"
        user_body = (
            f"TARGET_LANGUAGE: {language}\n\n"
            f"{source_section}"
            f"Database Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Return strict JSON only with this schema:\n"
            "{"
            '"status":"ok|insufficient_context",'
            '"answer":"string|null",'
            '"claims":[{"text":"string","source_id":"S1","span":"string"}],'
            '"next_step":"string|null",'
            '"why_it_fits":["string"],'
            '"near_miss":"string|null"'
            "}\n"
            "If insufficient, return status=insufficient_context, answer=null, claims=[]."
        )
    else:
        user_body = (
            f"Database Context:\n{context}\n\n"
            f"{cite_section}"
            f"Near-miss retrieval context:\n{near_block}\n\n"
            f"Question: {query}"
            f"{STRUCTURED_SUFFIX}"
        )

    lang_extra = ""
    if detected_query_language or language_register_hint:
        parts = []
        if detected_query_language:
            parts.append(f"AUTODETECTED_QUERY_LANGUAGE (ISO 639-1): {detected_query_language}.")
        if language_register_hint:
            parts.append(language_register_hint)
        lang_extra = "\n\n" + " ".join(parts)

    messages: list[dict] = [
        {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\nTARGET RESPONSE LANGUAGE: {language}{lang_extra}",
        }
    ]
    if history:
        messages.extend(history[-LLM_HISTORY_MESSAGE_LIMIT:])
    messages.append(
        {
            "role": "user",
            "content": user_body,
        }
    )
    return messages


def parse_structured_response(text: str) -> tuple[str, str | None, str | None]:
    """Split LLM output into main answer, why-it-fits, near-miss blocks."""
    raw = (text or "").strip()
    if MARK_ANSWER not in raw:
        return raw, None, None

    try:
        tail = raw.split(MARK_ANSWER, 1)[1]
        answer_part = why_part = near_part = None

        if MARK_WHY in tail:
            answer_part, rest = tail.split(MARK_WHY, 1)
            if MARK_NEAR in rest:
                why_part, near_part = rest.split(MARK_NEAR, 1)
            else:
                why_part = rest
        elif MARK_NEAR in tail:
            answer_part, near_part = tail.split(MARK_NEAR, 1)
        else:
            answer_part = tail

        def _clean(s: str | None) -> str | None:
            if s is None:
                return None
            s = s.strip()
            return s or None

        answer = _clean(answer_part) or raw.strip()
        why = _clean(why_part)
        near = _clean(near_part)
        if near and near.lower() in ("none", "none.", "none!"):
            near = None
        return answer, why, near
    except Exception:
        return raw, None, None


def validate_citations_in_answer(answer: str, max_n: int) -> str:
    """Strip [n] markers that are out of range vs. retrieved sources (prevents citation drift)."""
    if not answer:
        return answer

    def _repl(m: re.Match[str]) -> str:
        if max_n <= 0:
            return ""
        n = int(m.group(1))
        return m.group(0) if 1 <= n <= max_n else ""

    return re.sub(r"\[(\d+)\]", _repl, answer)


def dedupe_citations(answer: str) -> str:
    """Keep the first occurrence of each [n]; strip repeats so the answer reads curated, not raw."""
    if not answer:
        return answer

    seen: set[str] = set()

    def _repl(m: re.Match[str]) -> str:
        num = m.group(1)
        if num in seen:
            return ""
        seen.add(num)
        return f"[{num}]"

    out = re.sub(r"\[(\d+)\]", _repl, answer)
    return re.sub(r" {2,}", " ", out)


def compose_session_assistant_text(answer: str, why: str | None, near: str | None) -> str:
    """Plain text stored in session memory (no marker tokens)."""
    parts: list[str] = [answer.strip()]
    if why:
        parts.append("Why this fits:\n" + why.strip())
    if near:
        parts.append("Almost eligible:\n" + near.strip())
    return "\n\n".join(parts)


async def run_moderation_raw_prompt(prompt: str) -> str:
    """Async Gemini call for moderation JSON (short prompt text)."""
    response = await asyncio.wait_for(
        asyncio.to_thread(gemini_model.generate_content, prompt),
        timeout=10.0,
    )
    return (response.text or "").strip()


_DEGRADED_CHAT = (
    "We're having a brief issue with the AI service. Please try again in a moment. "
    "For verified government schemes, you can also browse myscheme.gov.in."
)


def _trim_messages_for_budget(messages: list[dict], max_chars: int = MAX_PROMPT_CHARS) -> list[dict]:
    if max_chars <= 0:
        return messages
    total = sum(len((m.get("content") or "")) for m in messages if isinstance(m, dict))
    if total <= max_chars:
        return messages
    out = list(messages)
    # Keep system + latest user message; trim oldest conversational history first.
    while len(out) > 2 and total > max_chars:
        removed = out.pop(1)
        total -= len((removed.get("content") or ""))
    if total <= max_chars:
        return out
    # Final guard: truncate latest user message tail-preserving instruction context.
    latest = out[-1]
    content = (latest.get("content") or "")
    keep = max(500, max_chars - sum(len((m.get("content") or "")) for m in out[:-1]))
    if len(content) > keep:
        latest["content"] = content[:keep]
    return out


async def generate(messages: list[dict]) -> tuple[str, str]:
    """Primary chat completion. Does not raise — returns a safe string if all providers fail."""

    async def _gemini_once() -> tuple[str, str]:
        if gemini_model is None:
            raise RuntimeError("gemini_unconfigured")
        messages_budgeted = _trim_messages_for_budget(messages)
        prompt_parts = [f"INSTRUCTIONS:\n{SYSTEM_PROMPT}\n"]
        for msg in messages_budgeted:
            if msg["role"] != "system":
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg['content']}")
        full_prompt = "\n".join(prompt_parts)
        response = await with_timeout(
            asyncio.to_thread(gemini_model.generate_content, full_prompt),
            seconds=LLM_CALL_TIMEOUT_S,
            step="llm_generate_gemini",
        )
        return (response.text or "").strip(), CHAT_MODEL

    try:
        return await async_retry(
            lambda: _gemini_once(),
            attempts=API_RETRY_ATTEMPTS,
            base_delay=API_RETRY_BASE_DELAY_S,
            max_delay=API_RETRY_MAX_DELAY_S,
            step="llm_generate_gemini",
        )
    except Exception as e:
        logger.warning("primary_llm_failed", extra={"provider": CHAT_MODEL, "error": str(e)[:200]})
    if groq_client:
        try:
            response = await with_timeout(
                asyncio.to_thread(
                    groq_client.chat.completions.create,
                    model="llama-3.3-70b-versatile",
                    messages=_trim_messages_for_budget(messages),
                    temperature=0.1,
                ),
                seconds=LLM_CALL_TIMEOUT_S,
                step="llm_generate_groq",
            )
            return (response.choices[0].message.content or "").strip(), "groq-llama-3.3"
        except Exception as ge:
            logger.warning("llm_fallback_failed", extra={"error": str(ge)[:200]})
    logger.error("llm_all_providers_failed")
    return _DEGRADED_CHAT, "unavailable"


async def _pump_text_queue(
    q: queue.Queue[str | BaseException | None],
    on_token: Callable[[str], Awaitable[None]],
    *,
    timeout_s: float,
) -> str:
    """Drain a worker thread queue until None; invoke on_token for each text fragment."""
    parts: list[str] = []
    loop = asyncio.get_running_loop()
    deadline = loop.time() + float(timeout_s)
    while True:
        remaining = max(0.01, deadline - loop.time())
        try:
            item = await asyncio.wait_for(asyncio.to_thread(q.get), timeout=remaining)
        except asyncio.TimeoutError:
            raise TimeoutError("llm_stream_timeout") from None
        if item is None:
            break
        if isinstance(item, BaseException):
            raise item
        parts.append(item)
        await on_token(item)
    return "".join(parts)


async def generate_stream(
    messages: list[dict[str, str]],
    on_token: Callable[[str], Awaitable[None]],
) -> tuple[str, str]:
    """Stream chat completion from Gemini (primary) or Groq; tokens via ``on_token``."""

    async def _gemini_stream_once() -> tuple[str, str]:
        if gemini_model is None:
            raise RuntimeError("gemini_unconfigured")
        full_prompt = _flatten_prompt(messages)
        q: queue.Queue[str | BaseException | None] = queue.Queue()

        def worker() -> None:
            try:
                stream = gemini_model.generate_content_stream(full_prompt)
                for chunk in stream:
                    text = getattr(chunk, "text", None) or ""
                    if text:
                        q.put(text)
            except BaseException as exc:
                q.put(exc)
            finally:
                q.put(None)

        threading.Thread(target=worker, daemon=True).start()
        text = (await _pump_text_queue(q, on_token, timeout_s=LLM_CALL_TIMEOUT_S)).strip()
        return text, CHAT_MODEL

    try:
        return await async_retry(
            lambda: _gemini_stream_once(),
            attempts=API_RETRY_ATTEMPTS,
            base_delay=API_RETRY_BASE_DELAY_S,
            max_delay=API_RETRY_MAX_DELAY_S,
            step="llm_stream_gemini",
        )
    except Exception as e:
        logger.warning(
            "primary_llm_stream_failed",
            extra={"provider": CHAT_MODEL, "error": str(e)[:200]},
        )
    if groq_client:
        try:

            async def _groq_stream_once() -> tuple[str, str]:
                msgs = _trim_messages_for_budget(messages)
                q2: queue.Queue[str | BaseException | None] = queue.Queue()

                def groq_worker() -> None:
                    try:
                        stream = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=msgs,
                            temperature=0.1,
                            stream=True,
                        )
                        for chunk in stream:
                            if not chunk.choices:
                                continue
                            delta = chunk.choices[0].delta
                            piece = getattr(delta, "content", None) if delta else None
                            if piece:
                                q2.put(piece)
                    except BaseException as exc:
                        q2.put(exc)
                    finally:
                        q2.put(None)

                threading.Thread(target=groq_worker, daemon=True).start()
                text = (await _pump_text_queue(q2, on_token, timeout_s=LLM_CALL_TIMEOUT_S)).strip()
                return text, "groq-llama-3.3"

            return await async_retry(
                lambda: _groq_stream_once(),
                attempts=API_RETRY_ATTEMPTS,
                base_delay=API_RETRY_BASE_DELAY_S,
                max_delay=API_RETRY_MAX_DELAY_S,
                step="llm_stream_groq",
            )
        except Exception as ge:
            logger.warning("llm_stream_fallback_failed", extra={"error": str(ge)[:200]})
    logger.error("llm_stream_all_providers_failed")
    degraded = _DEGRADED_CHAT
    await on_token(degraded)
    return degraded, "unavailable"


def _insufficient_json_payload() -> dict:
    return {"status": "insufficient_context", "answer": None, "claims": []}


def _flatten_prompt(messages: list[dict]) -> str:
    messages = _trim_messages_for_budget(messages)
    prompt_parts = [f"INSTRUCTIONS:\n{SYSTEM_PROMPT}\n"]
    for msg in messages:
        if msg["role"] != "system":
            role = "User" if msg["role"] == "user" else "Assistant"
            prompt_parts.append(f"{role}: {msg['content']}")
    return "\n".join(prompt_parts)


async def generate_json(messages: list[dict]) -> tuple[dict, str]:
    """Structured response path for staged rollout."""
    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["ok", "insufficient_context"]},
            "answer": {"type": ["string", "null"]},
            "next_step": {"type": ["string", "null"]},
            "why_it_fits": {"type": "array", "items": {"type": "string"}},
            "near_miss": {"type": ["string", "null"]},
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "source_id": {"type": "string"},
                        "span": {"type": "string"},
                    },
                    "required": ["text", "source_id"],
                },
            },
        },
        "required": ["status", "answer", "claims"],
    }
    prompt = _flatten_prompt(messages)

    def _parse_dict(raw: str) -> dict:
        data = json.loads((raw or "").strip())
        if not isinstance(data, dict):
            raise ValueError("Structured response is not a JSON object")
        return data

    if gemini_model is not None:
        try:
            response = await with_timeout(
                asyncio.to_thread(
                    gemini_model.generate_content,
                    prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "response_schema": schema,
                        "temperature": 0.1,
                    },
                ),
                seconds=LLM_CALL_TIMEOUT_S,
                step="llm_generate_json_gemini",
            )
            data = _parse_dict(response.text or "")
            return data, CHAT_MODEL
        except Exception as e:
            try:
                response_retry = await with_timeout(
                    asyncio.to_thread(
                        gemini_model.generate_content,
                        prompt,
                        generation_config={
                            "response_mime_type": "application/json",
                            "response_schema": schema,
                            "temperature": 0.0,
                        },
                    ),
                    seconds=LLM_CALL_TIMEOUT_S,
                    step="llm_generate_json_gemini_retry",
                )
                data_retry = _parse_dict(response_retry.text or "")
                return data_retry, CHAT_MODEL
            except Exception:
                pass
    else:
        e = RuntimeError("gemini_unconfigured")
    if not groq_client:
        logger.warning("structured_json_degraded", extra={"error": str(e)[:200]})
        return _insufficient_json_payload(), "unavailable"
    try:
        response = await with_timeout(
            asyncio.to_thread(
                groq_client.chat.completions.create,
                model="llama-3.3-70b-versatile",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
            ),
            seconds=LLM_CALL_TIMEOUT_S,
            step="llm_generate_json_groq",
        )
        data = _parse_dict(response.choices[0].message.content or "")
        return data, "groq-llama-3.3"
    except Exception as ge:
        logger.warning("structured_llm_fallback_failed", extra={"error": str(ge)[:200]})
    logger.warning("structured_json_degraded", extra={"error": str(e)[:200]})
    return _insufficient_json_payload(), "unavailable"


# Gemini JSON schema for welfare action-plan agent (grounding enforced downstream).
AGENT_PLAN_RESPONSE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["plan_ready", "need_more_info", "insufficient_data"],
        },
        "disclaimer": {"type": "string"},
        "eligibility": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scheme": {"type": "string"},
                    "source_id": {"type": "string"},
                    "verdict": {
                        "type": "string",
                        "enum": ["eligible", "likely_eligible", "likely_ineligible", "unknown"],
                    },
                    "matched_criteria": {"type": "array", "items": {"type": "string"}},
                    "missing_criteria": {"type": "array", "items": {"type": "string"}},
                    "unknown_criteria": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["scheme", "source_id", "verdict"],
            },
        },
        "documents_needed": {"type": "array", "items": {"type": "string"}},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "order": {"type": "integer"},
                    "action": {"type": "string"},
                    "where": {"type": "string"},
                    "estimated_time": {"type": "string"},
                },
                "required": ["order", "action"],
            },
        },
        "clarifying_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["status", "disclaimer"],
}


async def generate_agent_plan_json(prompt: str) -> tuple[dict, str]:
    """Schema-constrained JSON for the action-plan agent. Fails soft: returns {} on total failure."""

    def _parse_dict(raw: str) -> dict:
        data = json.loads((raw or "").strip())
        if not isinstance(data, dict):
            raise ValueError("agent plan response is not a JSON object")
        return data

    if gemini_model is not None:
        try:
            response = await with_timeout(
                asyncio.to_thread(
                    gemini_model.generate_content,
                    prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "response_schema": AGENT_PLAN_RESPONSE_SCHEMA,
                        "temperature": 0.15,
                    },
                ),
                seconds=AGENT_PLAN_CALL_TIMEOUT_S,
                step="llm_agent_plan_gemini",
            )
            return _parse_dict(response.text or ""), CHAT_MODEL
        except Exception as e:
            logger.warning(
                "agent_plan_json_primary_failed",
                extra={"error": str(e)[:200]},
            )
            try:
                response_retry = await with_timeout(
                    asyncio.to_thread(
                        gemini_model.generate_content,
                        prompt,
                        generation_config={
                            "response_mime_type": "application/json",
                            "response_schema": AGENT_PLAN_RESPONSE_SCHEMA,
                            "temperature": 0.0,
                        },
                    ),
                    seconds=AGENT_PLAN_CALL_TIMEOUT_S,
                    step="llm_agent_plan_gemini_retry",
                )
                return _parse_dict(response_retry.text or ""), CHAT_MODEL
            except Exception as e2:
                logger.warning(
                    "agent_plan_json_retry_failed",
                    extra={"error": str(e2)[:200]},
                )

    if groq_client:
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You output only a single JSON object matching the welfare action-plan schema. "
                        "No markdown, no commentary."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            response = await with_timeout(
                asyncio.to_thread(
                    groq_client.chat.completions.create,
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.1,
                ),
                seconds=AGENT_PLAN_CALL_TIMEOUT_S,
                step="llm_agent_plan_groq",
            )
            return _parse_dict(response.choices[0].message.content or ""), "groq-llama-3.3"
        except Exception as ge:
            logger.warning("agent_plan_json_groq_failed", extra={"error": str(ge)[:200]})

    return {}, CHAT_MODEL


async def generate_json_prompt(prompt: str) -> tuple[dict, str]:
    """Single-prompt strict JSON generation helper."""
    if gemini_model is None:
        return {}, CHAT_MODEL
    try:
        response = await asyncio.to_thread(
            gemini_model.generate_content,
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        )
        parsed = json.loads((response.text or "{}").strip())
        return (parsed if isinstance(parsed, dict) else {}), CHAT_MODEL
    except Exception:
        return {}, CHAT_MODEL


async def rewrite_query(query: str, language: str) -> str:
    """Query rewrite for retrieval recall. Fail-open to original query."""
    prompt = (
        "Rewrite this user request into a precise government-scheme search query for India.\n"
        "Preserve intent. Add useful retrieval hints like eligibility, benefits, documents, state if present.\n"
        "Return only the rewritten query text (no quotes, no bullets).\n\n"
        f"Target language: {language}\n"
        f"User query: {query}"
    )
    if gemini_model is None:
        return query
    try:
        resp = await with_timeout(
            asyncio.to_thread(gemini_model.generate_content, prompt),
            seconds=REWRITE_QUERY_TIMEOUT_S,
            step="rewrite_query",
        )
        rewritten = (resp.text or "").strip()
        if rewritten:
            return rewritten.splitlines()[0].strip()
        return query
    except Exception:
        return query
