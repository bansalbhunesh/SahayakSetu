"""
Sahayak — Voice-First AI Agent for Indian Government Schemes
Backend: FastAPI + Qdrant (RAG) + OpenAI (LLM) + Vapi (Voice)
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue,
    VectorParams, Distance, PointStruct
)
from openai import OpenAI

# ── Load env ────────────────────────────────────────
load_dotenv()

# ── Logging ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("sahayak")

# ── ENV validation ──────────────────────────────────
QDRANT_URL = os.environ.get("QDRANT_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
VAPI_API_KEY = os.environ.get("VAPI_API_KEY", "")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536

COLLECTION = "sahayak_schemes"
MEMORY_COLLECTION = "sahayak_memory"

# ── App ─────────────────────────────────────────────
app = FastAPI(
    title="Sahayak API",
    description="Voice-First AI Agent for Indian Government Schemes",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Clients ─────────────────────────────────────────
qdrant: Optional[QdrantClient] = None
openai_client: Optional[OpenAI] = None


def get_qdrant() -> QdrantClient:
    global qdrant
    if qdrant is None:
        qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return qdrant


def get_openai() -> OpenAI:
    global openai_client
    if openai_client is None:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return openai_client


# ── System Prompt ───────────────────────────────────
SYSTEM_PROMPT = """You are SahayakSetu (सहायक सेतु), a friendly and knowledgeable multilingual voice assistant that helps Indian citizens understand and access government welfare schemes.

CRITICAL RULES:
1. LANGUAGE: ALWAYS respond in the EXACT SAME language as the user's question.
   - Hindi → Hindi answer
   - English → English answer
   - Kannada → Kannada answer (ಕನ್ನಡ)
   - Tamil → Tamil answer (தமிழ்)
   - Telugu → Telugu answer (తెలుగు)
   - Bengali → Bengali answer (বাংলা)
   - Marathi → Marathi answer (मराठी)
   - Hinglish (mixed) → Hinglish answer
   - Any other Indian language → respond in that language OR English
2. LENGTH: Keep responses to 2-3 sentences MAX (this is for voice, not text)
3. TONE: Warm, simple, respectful. Use formal address in all languages.
4. ACCURACY: Only use information from the provided context. If context is insufficient, say so honestly.
5. ACTIONABLE: Always end with a clear next step the user can take.

RESPONSE FORMAT:
- Answer the question directly
- Mention eligibility if relevant
- Give ONE clear next step (e.g., "Visit your nearest CSC centre" or "Visit pmkisan.gov.in")

LANGUAGE-SPECIFIC FALLBACKS (when info is not in context):
- English: "I don't have complete information on this right now. You can check at your nearest Common Service Centre."
- Hindi: "Iske baare mein mujhe abhi poori jaankari nahi hai. Aap apne nearest Jan Seva Kendra mein pooch sakte hain."
- Kannada: "ಈ ಬಗ್ಗೆ ನನ್ನ ಬಳಿ ಸಂಪೂರ್ಣ ಮಾಹಿತಿ ಇಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಹತ್ತಿರದ ಸಾಮಾನ್ಯ ಸೇವಾ ಕೇಂದ್ರಕ್ಕೆ ಭೇಟಿ ನೀಡಿ."
- Tamil: "இது பற்றி என்னிடம் முழு தகவல் இல்லை. உங்கள் அருகிலுள்ள பொது சேவை மையத்தில் கேளுங்கள்."
- Telugu: "దీని గురించి నా వద్ద పూర్తి సమాచారం లేదు. దయచేసి మీ సమీపంలోని సామాన్య సేవా కేంద్రాన్ని సందర్శించండి."
- Bengali: "এই বিষয়ে আমার কাছে সম্পূর্ণ তথ্য নেই। আপনার নিকটতম কমন সার্ভিস সেন্টারে যোগাযোগ করুন।"

PERSONALITY: Think of yourself as a helpful, inclusive government service assistant who genuinely wants to help ALL Indian citizens — regardless of which language they speak — access their rights and entitlements."""


# ── Embedding ───────────────────────────────────────
def embed_text(text: str) -> List[float]:
    """Generate embedding using OpenAI text-embedding-3-small."""
    client = get_openai()
    response = client.embeddings.create(
        input=text,
        model=EMBED_MODEL,
    )
    return response.data[0].embedding


# ── Qdrant Search ───────────────────────────────────
def search_schemes(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Semantic search over government scheme knowledge base."""
    client = get_qdrant()
    vector = embed_text(query)

    results = client.search(
        collection_name=COLLECTION,
        query_vector=vector,
        limit=top_k,
        with_payload=True,
    )

    chunks = []
    for r in results:
        chunks.append({
            "text": r.payload.get("text", ""),
            "scheme": r.payload.get("scheme", ""),
            "category": r.payload.get("category", ""),
            "score": round(r.score, 4),
        })

    logger.info(f"[SEARCH] query='{query[:60]}...' → {len(chunks)} results, top_score={chunks[0]['score'] if chunks else 0}")
    return chunks


# ── Memory System ───────────────────────────────────
def get_user_memory(user_id: str) -> Optional[str]:
    """Retrieve conversation memory for a user from Qdrant."""
    try:
        client = get_qdrant()
        results = client.scroll(
            collection_name=MEMORY_COLLECTION,
            scroll_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=5,
            with_payload=True,
            order_by="updated_at",
        )
        if results[0]:
            memories = [p.payload.get("summary", "") for p in results[0]]
            return " | ".join(memories[-3:])  # Last 3 interactions
    except Exception as e:
        logger.warning(f"[MEMORY] Read error for user {user_id}: {e}")
    return None


def save_user_memory(user_id: str, query: str, answer: str):
    """Save conversation turn to memory collection."""
    try:
        client = get_qdrant()
        summary = f"User asked: {query[:100]} → Answer: {answer[:100]}"
        vector = embed_text(summary)

        client.upsert(
            collection_name=MEMORY_COLLECTION,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "user_id": user_id,
                        "query": query[:200],
                        "answer": answer[:200],
                        "summary": summary,
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                )
            ],
        )
        logger.info(f"[MEMORY] Saved for user {user_id}")
    except Exception as e:
        logger.warning(f"[MEMORY] Save error: {e}")


# ── Answer Generation ───────────────────────────────
def generate_answer(query: str, chunks: List[Dict], memory: Optional[str] = None) -> str:
    """Generate answer using OpenAI with RAG context."""
    # Filter by relevance score
    relevant = [c for c in chunks if c["score"] > 0.25]

    if not relevant:
        # Detect language for appropriate fallback
        if any(c in query for c in "ಕನ್ನಡ"):
            return "ಈ ಬಗ್ಗೆ ನನ್ನ ಬಳಿ ನಿಖರ ಮಾಹಿತಿ ಇಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಹತ್ತಿರದ CSC ಕೇಂದ್ರಕ್ಕೆ ಭೇಟಿ ನೀಡಿ."
        elif any(c in query for c in "தமிழ்"):
            return "இது பற்றி என்னிடம் சரியான தகவல் இல்லை. உங்கள் அருகிலுள்ள CSC மையத்தில் கேளுங்கள்."
        elif any(c in query for c in "తెలుగు"):
            return "దీని గురించి నా వద్ద ఖచ్చితమైన సమాచారం లేదు. దయచేసి మీ సమీపంలోని CSC కేంద్రాన్ని సందర్శించండి."
        elif any(c in query for c in "বাংলা"):
            return "এই বিষয়ে আমার কাছে সঠিক তথ্য নেই। আপনার নিকটতম CSC সেন্টারে যোগাযোগ করুন।"
        elif any(c in query for c in "कृपयाक्याकैसेक्योंकबकितना"):
            return "Iske baare mein mujhe abhi poori jaankari nahi hai. Aap apne nearest Jan Seva Kendra ya CSC centre mein pooch sakte hain."
        elif any(w in query.lower() for w in ["kya", "kaise", "kitna", "kab", "mein", "hai", "chahiye", "milta", "karna"]):
            return "Iske baare mein mujhe exact jaankari nahi mili. Aap thoda aur detail bata sakte hain ya apne nearest CSC centre jaa sakte hain."
        else:
            return "I don't have specific information on this right now. You can visit your nearest Common Service Centre (CSC) or check the official government portal for details."

    # Build context
    context_parts = []
    schemes_mentioned = set()
    for c in relevant:
        context_parts.append(f"[{c['scheme']}]: {c['text']}")
        schemes_mentioned.add(c['scheme'])

    context = "\n\n".join(context_parts)

    # Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    user_content = f"Context from knowledge base:\n{context}\n\n"
    if memory:
        user_content += f"Previous conversation with this user: {memory}\n\n"
    user_content += f"User's question: {query}"

    messages.append({"role": "user", "content": user_content})

    client = get_openai()
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=200,
    )

    answer = response.choices[0].message.content.strip()
    logger.info(f"[ANSWER] schemes={list(schemes_mentioned)}, len={len(answer)}")
    return answer


# ── Vapi Webhook ────────────────────────────────────
@app.post("/vapi-webhook")
async def vapi_webhook(req: Request):
    """
    Handle all Vapi webhook events:
    - tool-calls: Function calling from the LLM
    - assistant-request: Dynamic assistant config
    - status-update: Call lifecycle events
    - transcript: Real-time transcription
    - hang: Assistant failed to reply
    - end-of-call-report: Post-call summary
    """
    try:
        body = await req.json()
        message = body.get("message", {})
        msg_type = message.get("type", "")

        logger.info(f"[VAPI] Event: {msg_type}")

        # ── Tool Calls (Function Calling) ───────────
        if msg_type == "tool-calls":
            tool_calls = message.get("toolCalls", [])
            results = []

            for tc in tool_calls:
                tool_call_id = tc.get("id", "")
                fn = tc.get("function", {})
                fn_name = fn.get("name", "")
                fn_args = fn.get("arguments", {})

                logger.info(f"[VAPI] Tool call: {fn_name}, args={fn_args}")

                if fn_name == "search_schemes":
                    query = fn_args.get("query", "")
                    user_id = message.get("call", {}).get("id", "anonymous")

                    # Search knowledge base
                    chunks = search_schemes(query)

                    # Get user memory
                    memory = get_user_memory(user_id)

                    # Generate answer
                    answer = generate_answer(query, chunks, memory)

                    # Save to memory
                    save_user_memory(user_id, query, answer)

                    results.append({
                        "toolCallId": tool_call_id,
                        "result": answer,
                    })
                else:
                    results.append({
                        "toolCallId": tool_call_id,
                        "result": "This function is not available.",
                    })

            return JSONResponse({"results": results})

        # ── Assistant Request ───────────────────────
        elif msg_type == "assistant-request":
            logger.info("[VAPI] Assistant request received")
            return JSONResponse({
                "assistant": get_assistant_config()
            })

        # ── Status Update ───────────────────────────
        elif msg_type == "status-update":
            status = message.get("status", "")
            logger.info(f"[VAPI] Status: {status}")
            return JSONResponse({"status": "ok"})

        # ── Transcript ──────────────────────────────
        elif msg_type == "transcript":
            role = message.get("role", "")
            text = message.get("transcript", "")
            logger.info(f"[VAPI] Transcript [{role}]: {text[:100]}")
            return JSONResponse({"status": "ok"})

        # ── Hang ────────────────────────────────────
        elif msg_type == "hang":
            logger.warning("[VAPI] Hang event — assistant failed to respond")
            return JSONResponse({"status": "ok"})

        # ── End of Call Report ──────────────────────
        elif msg_type == "end-of-call-report":
            summary = message.get("summary", "")
            duration = message.get("endedReason", "")
            logger.info(f"[VAPI] Call ended: reason={duration}, summary={summary[:100]}")
            return JSONResponse({"status": "ok"})

        # ── Default ─────────────────────────────────
        else:
            logger.info(f"[VAPI] Unhandled event: {msg_type}")
            return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"[VAPI] Webhook error: {e}", exc_info=True)
        return JSONResponse(
            {"results": [{"toolCallId": "error", "result": "There was a temporary system issue. Please try again."}]},
            status_code=200,  # Vapi needs 200
        )


def get_assistant_config() -> dict:
    """Return dynamic assistant configuration for Vapi."""
    return {
        "name": "Sahayak",
        "model": {
            "provider": "openai",
            "model": CHAT_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "search_schemes",
                        "description": "Search the knowledge base for information about Indian government welfare schemes. Use this tool whenever the user asks about any government scheme, benefit, eligibility, application process, or entitlement.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The user's question about government schemes, translated to a clear search query",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                }
            ],
        },
        "voice": {
            "provider": "azure",
            "voiceId": "en-IN-NeerjaNeural",
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "multi",
        },
        "firstMessage": "Namaste! I'm SahayakSetu — your government scheme assistant. You can ask me about any Indian government welfare scheme in English, Hindi, Kannada, Tamil, Telugu, or any language you prefer. How can I help you today?",
        "serverUrl": os.environ.get("BACKEND_URL", "http://localhost:8000") + "/vapi-webhook",
    }


# ── REST API Endpoints ──────────────────────────────

@app.get("/")
async def root():
    """Health check."""
    return {
        "service": "Sahayak API",
        "version": "1.0.0",
        "status": "healthy",
        "description": "Voice-First AI Agent for Indian Government Schemes",
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    checks = {"api": True, "qdrant": False, "openai": False}

    try:
        client = get_qdrant()
        info = client.get_collection(COLLECTION)
        checks["qdrant"] = True
        checks["qdrant_vectors"] = info.points_count
    except Exception as e:
        checks["qdrant_error"] = str(e)

    try:
        get_openai()
        checks["openai"] = True
    except Exception as e:
        checks["openai_error"] = str(e)

    return checks


@app.post("/api/search")
async def api_search(req: Request):
    """REST endpoint for scheme search (used by frontend text mode)."""
    body = await req.json()
    query = body.get("query", "")

    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    chunks = search_schemes(query)
    memory = get_user_memory(body.get("user_id", "web-user"))
    answer = generate_answer(query, chunks, memory)
    save_user_memory(body.get("user_id", "web-user"), query, answer)

    return {
        "answer": answer,
        "sources": [{"scheme": c["scheme"], "score": c["score"]} for c in chunks[:3]],
    }


@app.get("/api/schemes")
async def list_schemes():
    """List all unique schemes in the knowledge base."""
    try:
        client = get_qdrant()
        results = client.scroll(
            collection_name=COLLECTION,
            limit=100,
            with_payload=True,
        )
        schemes = set()
        for point in results[0]:
            schemes.add(point.payload.get("scheme", "Unknown"))
        return {"schemes": sorted(list(schemes)), "count": len(schemes)}
    except Exception as e:
        return {"schemes": [], "error": str(e)}


@app.get("/api/assistant-config")
async def assistant_config():
    """Return the Vapi assistant configuration (for setup script)."""
    return get_assistant_config()


# ── Startup ─────────────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info("=" * 50)
    logger.info("🚀 Sahayak API Starting...")
    logger.info(f"   Qdrant: {QDRANT_URL[:30]}...")
    logger.info(f"   Model: {CHAT_MODEL}")
    logger.info(f"   Embed: {EMBED_MODEL}")
    logger.info("=" * 50)

    # Validate env
    missing = []
    if not QDRANT_URL:
        missing.append("QDRANT_URL")
    if not QDRANT_API_KEY:
        missing.append("QDRANT_API_KEY")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if missing:
        logger.error(f"❌ Missing env vars: {', '.join(missing)}")
        logger.error("   Copy .env.example → .env and fill in your keys")
    else:
        logger.info("✅ All required env vars present")

        # Test Qdrant connection
        try:
            client = get_qdrant()
            info = client.get_collection(COLLECTION)
            logger.info(f"✅ Qdrant: {info.points_count} vectors in {COLLECTION}")
        except Exception as e:
            logger.warning(f"⚠️  Qdrant: {e} — Run 'python scripts/ingest.py' first")
