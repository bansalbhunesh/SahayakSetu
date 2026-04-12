import os
import json
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from qdrant_client import QdrantClient
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Clients
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
# Tell Qdrant to use local embeddings for queries too!
qdrant.set_model("BAAI/bge-small-en-v1.5")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="SahayakSetu API")

SYSTEM_PROMPT = """# SahayakSetu — Multilingual Government Assistant
You are SahayakSetu (सहायक सेतु), an advanced AI assistant designed to bridge the gap between Indian citizens and government welfare schemes.

## Core Directives:
1. **Multilingualism**: You MUST respond in the language the user speaks (Hindi, Kannada, Tamil, Telugu, Bengali, Marathi, or English).
2. **Branding**: Always refer to yourself as "SahayakSetu".
3. **Tone**: Empathetic, professional, and clear.
4. **Tool Use**: Use the `search_schemes` tool for ANY question about eligibility, benefits, or application processes.
5. **Language Awareness**: If search results are in English but the user asked in Kannada, translate the answer accurately into Kannada.

## Handling Missing Info:
If No Relevant Results are found in the schemes database:
- **English**: "I couldn't find specific details for that scheme. Please visit your local Jan Seva Kendra or the official portal."
- **Hindi**: "Mujhe is yojana ki jaankari nahi mili. Kripya apne nazdeeki Jan Seva Kendra ya official website par dekhein."
- **Kannada**: "Ee yojaneya bagge mahiti illa. Dayavittu hattira Jan Seva Kendrakke bheti needi."
- **Tamil**: "Indha thittam patri thagaval illai. Ungal pakkathil ulla Jan Seva Maiyathai thodarbu kollungal."
- **Telugu**: "Ee yojana gurinchi samacharam ledu. Mee daggara unna Jan Seva Kendrani snatashinchandi."
- **Bengali**: "Ei prokolper bishoye kono tottho nei. Anugraho kore apnar kachher Jan Seva Kendra te jogajog korun."
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
                
                # Perform RAG Search with local embeddings!
                # query_points handles local embedding generation internally.
                search_results = qdrant.query(
                    collection_name="sahayak_schemes",
                    query_text=query,
                    limit=3
                )
                
                context = "\n".join([p.document for p in search_results])
                results.append({
                    "toolCallId": call["id"],
                    "result": context if context else "No matching scheme information found."
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

@app.get("/health")
def health():
    return {"status": "online", "branding": "SahayakSetu"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
