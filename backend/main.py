import os
import json
import time
import asyncio
from typing import List, Optional, Tuple, Dict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Audit v5 Restoration: Startup Guards & Env Sync
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL", "https://sahayaksetu-backend-3kxl.onrender.com")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.0-flash")

if not QDRANT_URL or not GEMINI_API_KEY:
    raise RuntimeError(f"Missing required env vars. QDRANT_URL={'set' if QDRANT_URL else 'MISSING'}, GEMINI_API_KEY={'set' if GEMINI_API_KEY else 'MISSING'}")

# Initialize Clients
try:
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    qdrant.set_model("BAAI/bge-small-en-v1.5")
    qdrant.get_collections()  # Force connection test at startup
    print(f"[OK] Qdrant connected: {QDRANT_URL[:30]}...")
except Exception as _qdrant_err:
    raise RuntimeError(f"Qdrant connection failed: {_qdrant_err}")

genai.configure(api_key=GEMINI_API_KEY)
llm_model = genai.GenerativeModel(CHAT_MODEL)

groq_client = None
GROQ_API_KEY = (GROQ_API_KEY or "").strip()
if GROQ_API_KEY:
    try:
        groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        print("[OK] Groq fallback client initialized")
    except Exception as _groq_err:
        print(f"[WARNING] Groq initialization failed: {_groq_err}")
        groq_client = None

# Audit v5 Restoration: Protected In-Memory Store
conversation_store = {}

app = FastAPI(title="SahayakSetu API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchQuery(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"
    language: Optional[str] = "hi-IN"

SYSTEM_PROMPT = """# SahayakSetu (सहायक सेतु) — Pan-India Multilingual Expertise
You are SahayakSetu, the official AI bridge for Indian welfare. You handle language barriers by providing clear, empathy-driven information about government schemes.

## 🛠️ Logic Rules:
1. **Strict Script Mirroring**: ALWAYS respond in the EXACT language and script specified by the frontend 'Target Language'. If Target Language is English, respond in English. If it is Hindi/Devanagari, respond in Hindi.
2. **Translation Bridge**: Act as a fluent translator. Convert complex English scheme data into the 'Target Language' with 100% accuracy.
3. **Actionable Roadmap**: Every answer MUST conclude with a "Next Step" (which office to visit or what document to carry).
4. **Context Lockdown**: Treat context as "Absolute Truth". Never hallucinate details not found in the search results.
"""

@app.on_event("startup")
def startup_event():
    print(f"\n[STARTUP] SahayakSetu - Intelligence Activated")
    print(f"   Primary: {CHAT_MODEL}")
    print(f"   Fallback: {'Groq-Llama-3.3' if groq_client else 'None'}")
    print(f"   RAG: Qdrant @ {QDRANT_URL[:20]}...")

@app.get("/health")
def health():
    return {"status": "online", "model": CHAT_MODEL, "threshold": 0.2}

@app.get("/")
def read_root():
    return {"status": "SahayakSetu Backend Online", "model": CHAT_MODEL}

async def generate_response(messages: List[Dict]) -> Tuple[str, str]:
    """Generate LLM response with async-safe blocking calls and 30s timeout."""
    try:
        prompt_parts = [f"INSTRUCTIONS:\n{SYSTEM_PROMPT}\n"]
        for msg in messages:
            if msg["role"] != "system":
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg['content']}")

        full_prompt = "\n".join(prompt_parts)
        response = await asyncio.wait_for(
            asyncio.to_thread(llm_model.generate_content, full_prompt),
            timeout=30.0
        )
        return response.text, CHAT_MODEL
    except Exception as e:
        print(f"[WARNING] Primary LLM {CHAT_MODEL} failed: {e}")
        if groq_client:
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        groq_client.chat.completions.create,
                        model="llama-3.3-70b-versatile",
                        messages=messages,
                        temperature=0.7,
                        timeout=30
                    ),
                    timeout=35.0
                )
                return response.choices[0].message.content, "groq-llama-3.3"
            except Exception as ge:
                print(f"[ERROR] Groq fallback also failed: {ge}")
                raise HTTPException(status_code=500, detail=f"Both LLMs failed. Gemini: {e}, Groq: {ge}")
        raise HTTPException(status_code=500, detail=str(e))

MAX_QUERY_LENGTH = 500
CONVERSATION_TTL = 3600  # seconds


def _get_metadata_field(metadata, field: str, default: str) -> str:
    if isinstance(metadata, dict):
        return metadata.get(field, default)
    return getattr(metadata, field, default)


def _cleanup_conversation_store():
    now = time.time()
    expired = [uid for uid, conv in conversation_store.items()
               if now - conv.get("ts", now) > CONVERSATION_TTL]
    for uid in expired:
        del conversation_store[uid]
    # Hard cap: if still over 500, evict oldest by timestamp
    if len(conversation_store) > 500:
        sorted_keys = sorted(conversation_store, key=lambda k: conversation_store[k].get("ts", 0))
        for key in sorted_keys[:len(conversation_store) - 500]:
            del conversation_store[key]


@app.post("/api/search")
async def api_search(data: SearchQuery):
    if not data.query or not data.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if len(data.query) > MAX_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail=f"Query exceeds {MAX_QUERY_LENGTH} characters")

    query = data.query.strip()
    try:
        search_results = qdrant.query(collection_name="sahayak_schemes", query_text=query, limit=3)
        relevant = [p for p in (search_results or []) if hasattr(p, "score") and p.score > 0.2]
        context = "\n\n".join([p.document for p in relevant if hasattr(p, "document")]) or "No relevant schemes found."

        history = conversation_store.get(data.user_id, {}).get("msgs", [])
        messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\nTARGET RESPONSE LANGUAGE: {data.language}"}]
        messages.extend(history[-4:])
        messages.append({"role": "user", "content": f"Database Context:\n{context}\n\nQuestion: {query}"})

        text, provider = await generate_response(messages)

        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": text})
        conversation_store[data.user_id] = {"msgs": history[-20:], "ts": time.time()}

        _cleanup_conversation_store()

        return {
            "answer": text,
            "provider": provider,
            "sources": [
                {"scheme": _get_metadata_field(p.metadata, "scheme", "Scheme"), "score": p.score}
                for p in relevant
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] /api/search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Invalid request body")
        message = body.get("message", {})
        if not isinstance(message, dict):
            raise HTTPException(status_code=400, detail="Invalid message field")

        if message.get("type") == "assistant-request":
            return JSONResponse(content={
                "assistant": {
                    "model": {"provider": "custom-llm", "url": f"{BACKEND_URL}/chat/completions"},
                    "voice": {"provider": "azure", "voiceId": "hi-IN-SwaraNeural"},
                    "firstMessage": "Namaste! Main SahayakSetu hoon. Aap kisi bhi sarkari yojna ke baare mein pooch sakte hain."
                }
            })

        if message.get("type") == "tool-calls":
            tool_calls = message.get("toolCalls", [])
            results = []
            for call in tool_calls:
                call_id = call.get("id", "unknown")
                try:
                    if call.get("function", {}).get("name") == "search_schemes":
                        args = json.loads(call["function"]["arguments"])
                        query = args.get("query", "").strip()
                        if not query:
                            results.append({"toolCallId": call_id, "result": "Query is empty."})
                            continue
                        search_results = qdrant.query(
                            collection_name="sahayak_schemes", query_text=query, limit=3
                        )
                        context = "\n".join([
                            p.document for p in (search_results or [])
                            if hasattr(p, "score") and p.score > 0.2 and hasattr(p, "document")
                        ])
                        results.append({"toolCallId": call_id, "result": context or "Mujhe details nahi mili."})
                except (json.JSONDecodeError, KeyError) as call_err:
                    print(f"[ERROR] vapi tool-call processing failed: {call_err}")
                    results.append({"toolCallId": call_id, "result": "Tool call processing failed."})
            return JSONResponse(content={"results": results})

        return JSONResponse(content={})
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] /vapi-webhook failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@app.post("/chat/completions")
async def chat_completions(request: Request):
    try:
        body = await request.json()
        messages = body.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="messages field is required")
        text, provider = await generate_response(messages)
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": provider,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop"
            }]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] /chat/completions failed: {e}")
        raise HTTPException(status_code=500, detail="LLM request failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
