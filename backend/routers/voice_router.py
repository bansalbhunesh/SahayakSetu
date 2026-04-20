import hmac
import json
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi.util import get_remote_address

from backend.config import BACKEND_URL, CHAT_COMPLETIONS_SECRET, SIMILARITY_THRESHOLD
from backend.rate_limit import limiter
from backend.services import moderation_service, retrieval_service
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


@router.post("/vapi-webhook")
@limiter.limit(
    "30/minute",
    key_func=lambda request: request.headers.get("x-vapi-signature")
    or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    or get_remote_address(request),
)
async def handle_vapi_webhook(request: Request):
    webhook_body: dict[str, Any] = await request.json()
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
                lang = args.get("language") or infer_bcp47(query_text)

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
