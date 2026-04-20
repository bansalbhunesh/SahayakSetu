"""LLM generation — Gemini primary, Groq fallback."""

from __future__ import annotations

import json
import re

from fastapi import HTTPException

from backend.config import CHAT_MODEL, gemini_model, groq_client
from backend.prompts.system_prompt import SYSTEM_PROMPT

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

    messages: list[dict] = [
        {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\nTARGET RESPONSE LANGUAGE: {language}",
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


def run_moderation_raw_prompt(prompt: str) -> str:
    """Synchronous Gemini call for moderation JSON (short prompt text)."""
    response = gemini_model.generate_content(prompt)
    return (response.text or "").strip()


async def generate(messages: list[dict]) -> tuple[str, str]:
    try:
        prompt_parts = [f"INSTRUCTIONS:\n{SYSTEM_PROMPT}\n"]
        for msg in messages:
            if msg["role"] != "system":
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg['content']}")

        full_prompt = "\n".join(prompt_parts)
        response = gemini_model.generate_content(full_prompt)
        return response.text, CHAT_MODEL
    except Exception as e:
        print(f"[WARNING] Primary LLM {CHAT_MODEL} failed: {e}")
        if groq_client:
            try:
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7,
                )
                return response.choices[0].message.content, "groq-llama-3.3"
            except Exception as ge:
                print(f"[ERROR] Groq fallback also failed: {ge}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Both LLMs failed. Gemini: {e}, Groq: {ge}",
                ) from ge
        raise HTTPException(status_code=500, detail=str(e)) from e


def _flatten_prompt(messages: list[dict]) -> str:
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

    try:
        response = gemini_model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": schema,
                "temperature": 0.1,
            },
        )
        data = _parse_dict(response.text or "")
        return data, CHAT_MODEL
    except Exception as e:
        # One deterministic retry at temperature 0 before fallback.
        try:
            response_retry = gemini_model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                    "temperature": 0.0,
                },
            )
            data_retry = _parse_dict(response_retry.text or "")
            return data_retry, CHAT_MODEL
        except Exception:
            pass
        if groq_client:
            try:
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                data = _parse_dict(response.choices[0].message.content or "")
                return data, "groq-llama-3.3"
            except Exception as ge:
                raise HTTPException(
                    status_code=500,
                    detail=f"Structured JSON generation failed. Gemini: {e}, Groq: {ge}",
                ) from ge
        raise HTTPException(status_code=500, detail=f"Structured JSON generation failed: {e}") from e


async def generate_json_prompt(prompt: str) -> tuple[dict, str]:
    """Single-prompt strict JSON generation helper."""
    try:
        response = gemini_model.generate_content(
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
    try:
        resp = gemini_model.generate_content(prompt)
        rewritten = (resp.text or "").strip()
        if rewritten:
            return rewritten.splitlines()[0].strip()
        return query
    except Exception:
        return query
