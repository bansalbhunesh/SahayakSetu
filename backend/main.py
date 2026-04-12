import os
import json
import time
from typing import List, Optional
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

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RENDER_URL = "https://sahayaksetu-backend-3kxl.onrender.com"

# Initialize Qdrant
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
qdrant.set_model("BAAI/bge-small-en-v1.5")

# Initialize Gemini 2.0 Flash (Primary)
genai.configure(api_key=GEMINI_API_KEY)
# We use gemini-2.0-flash as it is free, fast, and multilingual on v1beta
llm_model = genai.GenerativeModel("gemini-2.0-flash")

# Initialize Groq Client (Fallback)
# Groq handles Llama 3.3 70B at 300+ t/s for free
groq_client = None
if GROQ_API_KEY:
    groq_client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )

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

SYSTEM_PROMPT = """# SahayakSetu (सहायक सेतु) — Multilingual Expertise
You are SahayakSetu, the official AI bridge for Indian welfare. You handle language barriers by providing clear, empathy-driven information about government schemes.

## 🛠️ Logic Rules:
1. **Language Mirroring**: ALWAYS respond in the EXACT language used by the user. If the user asks in English, respond in English. If they ask in Hindi, respond in Hindi.
2. **Translation Bridge**: Since scheme data is often in English, you act as the translator. Even when mirroring a regional language, ensure technical terms from the English data are explained clearly.
3. **Actionable**: Every answer MUST include a "Next Step" (e.g., "Visit the CSC", "Keep your Aadhaar ready").
4. **No Hallucinations**: Only use the provided context. If no info found, direct them to Jan Seva Kendra.
"""

@app.on_event("startup")
async def startup_event():
    print("🚀 SahayakSetu Free Tier Fusion Initialized")
    print("🧠 Primary: Gemini 2.0 Flash")
    if groq_client:
        print("⚡ Fallback: Groq (Llama 3.3 70B) READY")
    else:
        print("⚠️ Fallback: Groq NOT Configured (Add GROQ_API_KEY to .env)")

# ── Intelligence Fusion Helper ─────────────────────
async def generate_response(messages: list):
    """Try Gemini 2.0 Flash first, fallback to Groq if Gemini fails."""
    last_user_msg = messages[-1]["content"] if messages else ""
    
    try:
        # 1. Try Gemini
        response = llm_model.generate_content(last_user_msg)
        return response.text, "gemini-2.0-flash"
    except Exception as e:
        print(f"⚠️ Gemini error, trying Groq fallback: {e}")
        if groq_client:
            try:
                # 2. Try Groq (Llama 3.3)
                groq_resp = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7
                )
                return groq_resp.choices[0].message.content, "llama-3.3-70b-versatile"
            except Exception as ge:
                print(f"❌ Groq fallback failed: {ge}")
                raise HTTPException(status_code=500, detail="Intelligence fusion failed.")
        else:
            raise HTTPException(status_code=500, detail="Gemini failed and Groq not configured.")

# ── Vapi Webhook (The Handshake) ───────────────────
@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    body = await request.json()
    message = body.get("message", {})
    
    if message.get("type") == "assistant-request":
        return JSONResponse(content={
            "assistant": {
                "name": "SahayakSetu",
                "model": {
                    "provider": "custom-llm",
                    "url": RENDER_URL,
                    "model": "gemini-2.0-flash",
                    "systemPrompt": SYSTEM_PROMPT,
                    "temperature": 0.5
                },
                "voice": {
                    "provider": "azure",
                    "voiceId": "hi-IN-SwaraNeural"
                },
                "firstMessage": "Welcome to SahayakSetu. Main aapki sarkari schemes mein madad kar sakti hoon."
            }
        })
    
    if message.get("type") == "tool-calls":
        tool_calls = message.get("toolCalls", [])
        results = []
        for call in tool_calls:
            if call["function"]["name"] == "search_schemes":
                args = json.loads(call["function"]["arguments"])
                query = args.get("query")
                search_results = qdrant.query(collection_name="sahayak_schemes", query_text=query, limit=3)
                confident_results = [p.document for p in search_results if p.score > 0.2]
                context = "\n".join(confident_results)
                results.append({
                    "toolCallId": call["id"],
                    "result": context if context else "Mujhe details nahi mili."
                })
        return JSONResponse(content={"results": results})
    
    return JSONResponse(content={})

# ── Custom LLM Endpoint (The Orchestrator) ──────────
@app.post("/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    
    text, provider = await generate_response(messages)
    
    # Return OpenAI-compatible response for Vapi
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": provider,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": text
            },
            "finish_reason": "stop"
        }]
    }

@app.post("/api/search")
async def api_search(data: SearchQuery):
    try:
        search_results = qdrant.query(collection_name="sahayak_schemes", query_text=data.query, limit=3)
        confident_results = [p.document for p in search_results if p.score > 0.2]
        context = "\n".join(confident_results)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {data.query}"}
        ]
        
        text, provider = await generate_response(messages)
        
        return {
            "answer": text,
            "provider": provider,
            "sources": [{"scheme": p.metadata.get("scheme"), "score": p.score} for p in search_results if p.score > 0.2]
        }
    except Exception as e:
        print(f"❌ Search Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "online", "message": "SahayakSetu Fusion is ACTIVE"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
