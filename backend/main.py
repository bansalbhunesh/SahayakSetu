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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = "gpt-4o-mini"

# Initialize Clients
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
# Tell Qdrant to use local LIGHTWEIGHT embeddings (Safe for 512MB Render Tier)
qdrant.set_model("BAAI/bge-small-en-v1.5")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="SahayakSetu API")

# STARTUP VALIDATION: Ensure demo doesn't fail due to env issues
@app.on_event("startup")
async def startup_event():
    required_vars = ["QDRANT_URL", "QDRANT_API_KEY", "OPENAI_API_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ CRITICAL ERROR: Missing environment variable: {var}")
            # In production, we'd raise an error, for demo we print clearly
    
    print("🚀 SahayakSetu Backend Initialized")
    print(f"📡 QDRANT_URL: {QDRANT_URL[:30]}...")
    print(f"🤖 MODEL: {CHAT_MODEL}")
    print(f"🌐 EMBEDDINGS: Multilingual (sentence-transformers)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for the hackathon (including localhost and Vercel)
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

## ⚠️ Fallback:
If no info is found: "Mujhe iske baare mein pakki jaankari nahi mili. Kripya apne nazdeeki Jan Seva Kendra ya official portal dekhein." (Translate to user's language).
"""

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    """Handle Vapi tool calls and assistant requests."""
    body = await request.json()
    message = body.get("message", {})
    
    # Handle Tool Call (Function Calling)
    if message.get("type") == "tool-calls":
        tool_calls = message.get("toolCalls", [])
        results = []
        
        for call in tool_calls:
            if call["function"]["name"] == "search_schemes":
                args = json.loads(call["function"]["arguments"])
                query = args.get("query")
                
                # Perform RAG Search with local Multilingual embeddings!
                search_results = qdrant.query(
                    collection_name="sahayak_schemes",
                    query_text=query,
                    limit=3
                )
                
                # SCORE THRESHOLDING: Only take matches > 0.4
                confident_results = [p.document for p in search_results if p.score > 0.4]
                context = "\n".join(confident_results)
                
                print(f"🔍 [QDRANT SEARCH] Query: {query} | Found {len(confident_results)} confident chunks")
                
                results.append({
                    "toolCallId": call["id"],
                    "result": context if context else "FALLBACK: Mujhe is scheme ki details database mein nahi mili."
                })
        
        return JSONResponse(content={"results": results})
    
    # Handle Assistant Configuration (Vapi request for prompt/voice)
    if message.get("type") == "assistant-request":
        return JSONResponse(content={
            "assistant": {
                "name": "SahayakSetu",
                "model": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "systemPrompt": SYSTEM_PROMPT,
                    "temperature": 0.7
                },
                "voice": {
                    "provider": "azure",
                    "voiceId": "en-IN-NeerjaNeural"
                },
                "firstMessage": "Welcome to SahayakSetu. I can help you with government schemes in multiple languages. Namaste, main SahayakSetu hoon. Aapki kaise sahayata kar sakti hoon?"
            }
        })
    
    return JSONResponse(content={})

@app.post("/api/search")
async def api_search(data: SearchQuery):
    """
    Direct API endpoint for text-based chat/search.
    """
    try:
        # Perform RAG search using Multilingual FastEmbed
        search_results = qdrant.query(
            collection_name="sahayak_schemes",
            query_text=data.query,
            limit=3
        )
        
        # SCORE THRESHOLDING: Only take matches > 0.4
        confident_results = [p.document for p in search_results if p.score > 0.4]
        context = "\n".join(confident_results)
        
        print(f"🔍 [WEB SEARCH] Query: {data.query} | Found {len(confident_results)} confident chunks")
        
        # Generate Answer
        response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context if context else 'FALLBACK: No relevant info found.'}\n\nQuestion: {data.query}"}
            ]
        )
        
        answer = response.choices[0].message.content
        
        return {
            "answer": answer,
            "sources": [{"scheme": p.metadata.get("scheme"), "score": p.score} for p in search_results if p.score > 0.4]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Search Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "online", "message": "SahayakSetu Backend is Live"}

@app.get("/health")
def health():
    return {"status": "online", "branding": "SahayakSetu"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
