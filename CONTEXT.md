# SahayakSetu — Claude Code Context

## Stack
- Backend: FastAPI (Python 3.12), deployed on Render free tier
- Frontend: Vanilla HTML/CSS/JS, deployed on Vercel (static)
- Vector DB: Qdrant Cloud — collection `sahayak_schemes`, model BAAI/bge-small-en-v1.5
- Primary LLM: Gemini 2.0 Flash (Google AI Studio)
- Fallback LLM: Groq / Llama 3.3 70B
- Voice: Vapi.ai — assistant ID in env as VAPI_ASSISTANT_ID
- STT: Deepgram nova-2 (via Vapi), fallback: browser SpeechRecognition API
- TTS: Azure Neural voices (via Vapi for calls), browser SpeechSynthesis (for text chat)

## Module Responsibilities
- `config.py`: all env vars + client singletons (single source of truth)
- `services/retrieval_service.py`: all Qdrant calls
- `services/llm_service.py`: all LLM calls (Gemini + Groq fallback)
- `services/moderation_service.py`: intent classification guard — runs BEFORE retrieval
- `services/session_service.py`: in-memory conversation history
- `routers/`: thin HTTP layer — call services, return Pydantic models

## Moderation Pipeline
- **Web `/api/search`:** `ModerationService.check(query)` → if blocked, return `redirect_message` → else RAG + LLM.
- **Voice tool `search_schemes`:** same `check()` on the tool query (language from optional arg + script inference).
- **Custom LLM `/chat/completions`:** verify optional secret → `check_conversation_transcript()` on recent User/Assistant turns (system skipped; long threads truncated) → then generate. Stops jailbreak text hidden in earlier turns without re-moderating on every intermediate hop.
- **Classifier errors:** default **fail-open** (`MODERATION_STRICT=false`, good for dev). Set **`MODERATION_STRICT=true`** in production so JSON/LLM moderation failures **fail-closed** with a generic safe message. Logs: `moderation_parse_error`, `moderation_call_error`, `moderation_fallback` (action fail_open / fail_closed).

## Knowledge Base
38 scheme chunks in `scripts/data/schemes.json`. Re-ingest with `python scripts/ingest.py`.

## Known Limitations
- Session memory is in-process only — resets on every Render deploy
- 38 chunks covers ~30 national + 8 regional schemes only
- Vapi credits are finite — browser SpeechRecognition is the fallback path

## Deployment
- Frontend: `vercel --prod` from repo root (vercel.json handles routing)
- Backend: auto-deploys from main branch via render.yaml
- Local: `docker-compose up` (bundled Qdrant uses `QDRANT_URL=http://qdrant:6333` in compose). For backend-only runs against Qdrant Cloud, override `QDRANT_URL` / run without the bundled `qdrant` service as your environment requires.

### Production checklist (backend env)
1. **`MODERATION_STRICT=true`** — fail-closed when the moderation classifier returns bad JSON or errors. The repo **`render.yaml`** sets this to **`true`** for the `sahayaksetu-backend` web service; you can override in the Render dashboard (e.g. a staging service set to `false`).
2. **`CHAT_COMPLETIONS_SECRET`** — non-empty; mirror the same value in the Vapi **custom LLM** credential (Bearer or `X-SahayakSetu-Key`) so `/chat/completions` is not an open proxy. Declared in **`render.yaml`** with `sync: false` so you set the value only in the Render dashboard.
3. Confirm startup logs show **Policy** lines you expect (printed once on boot).
