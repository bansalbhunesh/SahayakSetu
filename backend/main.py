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

# Initialize Qdrant
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
qdrant.set_model("BAAI/bge-small-en-v1.5")

# Initialize Gemini 2.0 Flash (Primary)
genai.configure(api_key=GEMINI_API_KEY)
llm_model = genai.GenerativeModel("gemini-2.0-flash")

# Initialize Groq Client (Fallback)
groq_client = None
if GROQ_API_KEY:
    groq_client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )

# In-memory store for conversation history (Audit v3 Memory fix)
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
2. **Translation Bridge**: Since scheme data is often in English, you act as the translator. Even when mirroring a regional language, include technical terms in both English and regional script if necessary.
3. **Actionable**: Every answer MUST include a "Next Step" (e.g., "Visit the CSC", "Keep your Aadhaar ready").
4. **No Hallucinations**: Only use the provided context. If no info found, direct them to Jan Seva Kendra.
"""

@app.get("/health")
def health():
    """Audit v3: Docker/Render health check endpoint."""
    return {"status": "online", "primary": "gemini-2.0-flash", "fallback": "groq", "threshold": 0.2}

@app.get("/")
def read_root():
    return {"status": "SahayakSetu Backend Online", "version": "2.1.0"}

async def generate_response(messages: list):
    """
    Dual-Brain Intelligence Fusion:
    Primary: Gemini 2.0 Flash (with proper system prompt + context injection)
    Fallback: Groq (OpenAI-compatible)
    """
    try:
        # Build proper prompt with system + context + history
        prompt_parts = []
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), SYSTEM_PROMPT)
        prompt_parts.append(f"INSTRUCTIONS:\n{system_msg}\n")
        
        # Add History
        for msg in messages:
            if msg["role"] != "system":
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg['content']}")
        
        full_prompt = "\n".join(prompt_parts)
        
        response = llm_model.generate_content(full_prompt)
        return response.text, "gemini-2.0-flash"
    except Exception as e:
        print(f"⚠️ Gemini error, trying Groq fallback: {e}")
        if groq_client:
            try:
                # Groq fallback handles the full messages array natively
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7
                )
                return response.choices[0].message.content, "groq-llama-3.3"
            except Exception as ge:
                print(f"❌ Groq fallback failed: {ge}")
                raise HTTPException(status_code=500, detail="Intelligence fusion failed.")
        else:
            raise HTTPException(status_code=500, detail="Gemini failed and Groq not configured.")

@app.post("/api/search")
async def api_search(data: SearchQuery):
    try:
        # 1. Retrieve Context from Qdrant
        search_results = qdrant.query(collection_name="sahayak_schemes", query_text=data.query, limit=3)
        relevant_sources = [p for p in search_results if p.score > 0.2]
        context = "\n\n".join([p.document for p in relevant_sources])
        
        # 2. Maintain Conversation History (Audit v3 Memory fix)
        history = conversation_store.get(data.user_id, [])
        
        # 3. Formulate the Orchestration Message
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history[-4:])
        messages.append({
            "role": "user", 
            "content": f"Database Context:\n{context}\n\nQuestion: {data.query}"
        })
        
        # 4. Generate Response via Fusion Engine
        text, provider = await generate_response(messages)
        
        # 5. Update History
        history.append({"role": "user", "content": data.query})
        history.append({"role": "assistant", "content": text})
        conversation_store[data.user_id] = history
        
        return {
            "answer": text,
            "provider": provider,
            "sources": [{"scheme": p.metadata.get("scheme", "Scheme"), "score": p.score} for p in relevant_sources]
        }
    except Exception as e:
        print(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    return JSONResponse(content={
        "assistant": {
            "model": {
                "provider": "custom-llm",
                "url": f"{BACKEND_URL}/chat/completions"
            }
        }
    })

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
            "message": {
                "role": "assistant",
                "content": text
            },
            "finish_reason": "stop"
        }]
    }
