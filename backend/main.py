import os
import json
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Initialize Clients
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
# Tell Qdrant to use local LIGHTWEIGHT embeddings (Safe for 512MB Render Tier)
qdrant.set_model("BAAI/bge-small-en-v1.5")

# Initialize xAI (Grok) Client
xai_client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)
CHAT_MODEL = "grok-beta"

app = FastAPI(title="SahayakSetu API")

# STARTUP VALIDATION
@app.on_event("startup")
async def startup_event():
    required_vars = ["QDRANT_URL", "QDRANT_API_KEY", "XAI_API_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ CRITICAL ERROR: Missing environment variable: {var}")
    
    print("🚀 SahayakSetu Backend Initialized")
    print(f"📡 QDRANT_URL: {QDRANT_URL[:30]}...")
    print(f"🤖 MODEL: {CHAT_MODEL} (xAI Grok Activated)")
    print("🌐 EMBEDDINGS: Multilingual (sentence-transformers)")

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
You are SahayakSetu, the official AI bridge for Indian welfare. You handle language barriers by interpreting English scheme data into the user's native tongue.

## 🛠️ Logic Rules:
1. **Multilingual Interpretation**: ALWAYS respond in the language the user speaks (Hindi, Kannada, etc.). If search results are in English, translate them accurately and empathetically.
2. **Translation-RAG**: When using the `search_schemes` tool, formulate your query in English for maximum precision.
3. **Actionable**: Every answer MUST include a "Next Step" (e.g., "Visit the CSC", "Keep your Aadhaar ready").
4. **No Hallucinations**: Only use the provided context. If no info found, direct them to Jan Seva Kendra.
"""

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    """Handle Vapi tool calls and assistant requests."""
    body = await request.json()
    message = body.get("message", {})
    
    # Handle Tool Call
    if message.get("type") == "tool-calls":
        tool_calls = message.get("toolCalls", [])
        results = []
        for call in tool_calls:
            if call["function"]["name"] == "search_schemes":
                args = json.loads(call["function"]["arguments"])
                query = args.get("query")
                search_results = qdrant.query(collection_name="sahayak_schemes", query_text=query, limit=3)
                # Lower threshold to 0.2 for better regional recall
                confident_results = [p.document for p in search_results if p.score > 0.2]
                context = "\n".join(confident_results)
                results.append({
                    "toolCallId": call["id"],
                    "result": context if context else "FALLBACK: Mujhe details nahi mili."
                })
        return JSONResponse(content={"results": results})
    
    # Handle Assistant Configuration
    if message.get("type") == "assistant-request":
        return JSONResponse(content={
            "assistant": {
                "name": "SahayakSetu",
                "model": {
                    "provider": "custom-llm",
                    "url": "https://api.x.ai/v1",
                    "model": "grok-beta",
                    "systemPrompt": SYSTEM_PROMPT,
                    "temperature": 0.7
                },
                "voice": {
                    "provider": "azure",
                    "voiceId": "hi-IN-SwaraNeural"
                },
                "firstMessage": "Welcome to SahayakSetu. I can help you with government schemes. Namaste, main SahayakSetu hoon."
            }
        })
    return JSONResponse(content={})

@app.post("/api/search")
async def api_search(data: SearchQuery):
    try:
        search_results = qdrant.query(collection_name="sahayak_schemes", query_text=data.query, limit=3)
        confident_results = [p.document for p in search_results if p.score > 0.2]
        context = "\n".join(confident_results)
        
        response = xai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {data.query}"}
            ]
        )
        answer = response.choices[0].message.content
        
        return {
            "answer": answer,
            "sources": [{"scheme": p.metadata.get("scheme"), "score": p.score} for p in search_results if p.score > 0.2]
        }
    except Exception as e:
        print(f"❌ Search Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "online", "message": "SahayakSetu Backend is Stabilized with Grok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
