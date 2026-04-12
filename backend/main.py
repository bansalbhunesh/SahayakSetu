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
BACKEND_URL = os.getenv("BACKEND_URL", "https://sahayaksetu-backend-3kxl.onrender.com")

# Initialize Clients
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
qdrant.set_model("BAAI/bge-small-en-v1.5")

genai.configure(api_key=GEMINI_API_KEY)
llm_model = genai.GenerativeModel("gemini-2.0-flash")

groq_client = None
if GROQ_API_KEY:
    groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

# Conversation store
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

SYSTEM_PROMPT = """# SahayakSetu (सहायक सेतु) — Pan-India Multilingual Expertise
You are SahayakSetu, the official AI bridge for Indian welfare. You handle language barriers by providing clear, empathy-driven information about government schemes.

## 🛠️ Logic Rules:
1. **Universal Language Mirroring**: ALWAYS respond in the EXACT language and script used by the user. 
2. **Translation Bridge**: Since scheme data is often in English, you act as the translator. 
3. **Actionable**: Every answer MUST include a "Next Step".
4. **No Hallucinations**: Only use the provided context.
"""

@app.on_event("startup")
async def startup_event():
    """Audit v4 Restoration: Initialization logging."""
    print("\n🚀 SahayakSetu — Intelligence Activated")
    print(f"   Primary: Gemini 2.0 Flash")
    print(f"   Fallback: {'Groq-Llama-3.3' if groq_client else 'None'}")
    print(f"   RAG: Qdrant @ {QDRANT_URL[:20]}...")

@app.get("/health")
def health():
    return {"status": "online", "primary": "gemini-2.0-flash", "threshold": 0.2}

@app.get("/")
def read_root():
    return {"status": "SahayakSetu Backend Online"}

async def generate_response(messages: list):
    try:
        prompt_parts = [f"INSTRUCTIONS:\n{SYSTEM_PROMPT}\n"]
        for msg in messages:
            if msg["role"] != "system":
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg['content']}")
        
        full_prompt = "\n".join(prompt_parts)
        response = llm_model.generate_content(full_prompt)
        return response.text, "gemini-2.0-flash"
    except Exception:
        if groq_client:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content, "groq-llama-3.3"
        raise HTTPException(status_code=500, detail="Intelligence failure.")

@app.post("/api/search")
async def api_search(data: SearchQuery):
    try:
        search_results = qdrant.query(collection_name="sahayak_schemes", query_text=data.query, limit=3)
        relevant = [p for p in search_results if p.score > 0.2]
        context = "\n\n".join([p.document for p in relevant])
        
        history = conversation_store.get(data.user_id, [])
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history[-4:])
        messages.append({"role": "user", "content": f"Database Context:\n{context}\n\nQuestion: {data.query}"})
        
        text, provider = await generate_response(messages)
        
        history.append({"role": "user", "content": data.query})
        history.append({"role": "assistant", "content": text})
        conversation_store[data.user_id] = history
        
        return {
            "answer": text,
            "provider": provider,
            "sources": [{"scheme": p.metadata.get("scheme", "Scheme"), "score": p.score} for p in relevant]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    """Audit v4 Restoration: Multi-payload handling (Assistant-Request & Tool-Calls)."""
    body = await request.json()
    message = body.get("message", {})
    
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
            if call["function"]["name"] == "search_schemes":
                args = json.loads(call["function"]["arguments"])
                search_results = qdrant.query(collection_name="sahayak_schemes", query_text=args.get("query"), limit=3)
                context = "\n".join([p.document for p in search_results if p.score > 0.2])
                results.append({"toolCallId": call["id"], "result": context or "Mujhe details nahi mili."})
        return JSONResponse(content={"results": results})
    
    return JSONResponse(content={})

@app.post("/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
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

if __name__ == "__main__":
    """Audit v4 Restoration: Local development entry point."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
