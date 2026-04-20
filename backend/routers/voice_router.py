import hmac
import json
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi.util import get_remote_address

from backend.config import (
    BACKEND_URL,
    CHAT_COMPLETIONS_SECRET,
    ENV,
    SIMILARITY_THRESHOLD,
    VAPI_WEBHOOK_SECRET,
)
from backend.rate_limit import limiter
from backend.services import injection_guard, moderation_service, pii_scrubber, retrieval_service
from backend.services.language_hint import infer_bcp47
from backend.services.llm_service import generate

router = APIRouter(tags=["voice"])


def _verify_chat_completions_secret(request: Request) -> None:
    if not CHAT_COMPLETIONS_SECRET:
        return
    auth = (request.headers.get("authorization") or "").strip()
    token = ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if not token:
        token = (request.headers.get("x-sahayaksetu-key") or "").strip()
    if len(token) != len(CHAT_COMPLETIONS_SECRET) or not hmac.compare_digest(
        token.encode("utf-8"), CHAT_COMPLETIONS_SECRET.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _verify_vapi_signature(request: Request, raw_body: bytes) -> None:
    if not VAPI_WEBHOOK_SECRET:
        if ENV == "production":
            raise HTTPException(status_code=500, detail="Webhook secret not configured")
        return
    sig = (request.headers.get("x-vapi-signature") or "").strip()
    expected = hmac.new(VAPI_WEBHOOK_SECRET.encode("utf-8"), raw_body, "sha256").hexdigest()
    if len(sig) != len(expected) or not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")


def _message_plaintext(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        chunks: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                chunks.append(str(block.get("text", "")))
            elif isinstance(block, str):
                chunks.append(block)
        return " ".join(chunks).strip()
    return ""


def _last_user_plain_text(messages: list[Any]) -> str | None:
    for m in reversed(messages):
        if not isinstance(m, dict) or m.get("role") != "user":
            continue
        body = _message_plaintext(m.get("content"))
        if body:
            return body
    return None


def _conversation_transcript_for_moderation(messages: list[Any], max_chars: int = 12000) -> str | None:
    """Chronological User/Assistant lines (system skipped) for one moderation pass before LLM."""
    lines: list[str] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        if role not in ("user", "assistant"):
            continue
        body = _message_plaintext(m.get("content"))
        if not body:
            continue
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {body}")
    if not lines:
        return None
    out = "\n".join(lines)
    if len(out) > max_chars:
        out = "...[truncated older turns]\n" + out[-max_chars:]
    return out


def _sanitize_chat_messages(messages: list[Any]) -> tuple[list[Any], bool]:
    """Sanitize text parts for chat/completions and flag suspicious injection prompts."""
    sanitized: list[Any] = []
    suspicious = False
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if role not in ("user", "assistant"):
            sanitized.append(m)
            continue
        if isinstance(content, str):
            safe, flag = injection_guard.sanitize_query(content)
            safe, _ = pii_scrubber.scrub(safe)
            suspicious = suspicious or flag
            sanitized.append({**m, "content": safe})
            continue
        if isinstance(content, list):
            blocks = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    safe, flag = injection_guard.sanitize_query(str(block.get("text", "")))
                    safe, _ = pii_scrubber.scrub(safe)
                    suspicious = suspicious or flag
                    blocks.append({**block, "text": safe})
                else:
                    blocks.append(block)
            sanitized.append({**m, "content": blocks})
            continue
        sanitized.append(m)
    return sanitized, suspicious


@router.post("/vapi-webhook")
@limiter.limit(
    "30/minute",
    key_func=lambda request: request.headers.get("x-vapi-signature")
    or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    or get_remote_address(request),
)
async def handle_vapi_webhook(request: Request):
    raw_body = await request.body()
    _verify_vapi_signature(request, raw_body)
    webhook_body: dict[str, Any] = json.loads(raw_body)
    message = webhook_body.get("message", {})

    if message.get("type") == "assistant-request":
        return JSONResponse(
            content={
                "assistant": {
                    "model": {
                        "provider": "custom-llm",
                        "url": f"{BACKEND_URL}/chat/completions",
                    },
                    "voice": {"provider": "azure", "voiceId": "hi-IN-SwaraNeural"},
                    "firstMessage": (
                        "Namaste! Main SahayakSetu hoon. Aap kisi bhi sarkari yojna ke baare mein pooch sakte hain."
                    ),
                }
            }
        )

    if message.get("type") == "tool-calls":
        tool_calls = message.get("toolCalls", [])
        results = []
        for call in tool_calls:
            if call["function"]["name"] == "search_schemes":
                args = json.loads(call["function"]["arguments"])
                query_text = args.get("query", "")
                query_text, suspicious = injection_guard.sanitize_query(query_text)
                query_text, _ = pii_scrubber.scrub(query_text)
                lang = args.get("language") or infer_bcp47(query_text)

                if suspicious:
                    results.append(
                        {
                            "toolCallId": call["id"],
                            "result": "Please ask a normal welfare-scheme question and avoid instruction-style prompts.",
                        }
                    )
                    continue

                moderation = await moderation_service.check(query_text, lang)
                if not moderation.allowed:
                    block_text = (
                        moderation.redirect_message
                        or "Please ask about Indian government schemes or civic services."
                    )
                    results.append({"toolCallId": call["id"], "result": block_text})
                    continue

                relevant_results, _near_miss_results, context, near_ctx = (
                    retrieval_service.retrieve_for_rag(query_text, SIMILARITY_THRESHOLD)
                )
                context_parts = [context] if context.strip() else []
                if near_ctx.strip():
                    context_parts.append(near_ctx)
                context = "\n\n".join(context_parts) if context_parts else ""
                results.append(
                    {
                        "toolCallId": call["id"],
                        "result": context or "Mujhe details nahi mili.",
                    }
                )
        return JSONResponse(content={"results": results})

    return JSONResponse(content={})


@router.post("/chat/completions")
@limiter.limit("20/minute")
async def handle_chat_completions(request: Request):
    _verify_chat_completions_secret(request)
    webhook_body: dict[str, Any] = await request.json()
    messages = webhook_body.get("messages", [])
    messages, suspicious = _sanitize_chat_messages(messages)
    if suspicious:
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "security",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Please ask a normal welfare-scheme question and avoid instruction-style prompts.",
                    },
                    "finish_reason": "stop",
                }
            ],
        }
    transcript = _conversation_transcript_for_moderation(messages)
    last_user = _last_user_plain_text(messages)
    mod_lang = infer_bcp47(last_user or transcript or "")
    if transcript:
        moderation = await moderation_service.check_conversation_transcript(transcript, mod_lang)
        if not moderation.allowed:
            block_text = (
                moderation.redirect_message
                or "Please ask about Indian government schemes or civic services."
            )
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "moderation",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": block_text},
                        "finish_reason": "stop",
                    }
                ],
            }
    text, provider = await generate(messages)
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": provider,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
    }
