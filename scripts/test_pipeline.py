"""
Sahayak — Test Pipeline
Tests the RAG pipeline end-to-end without needing Vapi.

Usage:
    python scripts/test_pipeline.py
"""

import os
import sys
import time

from dotenv import load_dotenv
load_dotenv()

# Check env vars
required = ["QDRANT_URL", "QDRANT_API_KEY", "OPENAI_API_KEY"]
missing = [k for k in required if not os.environ.get(k)]
if missing:
    print(f"❌ Missing env vars: {', '.join(missing)}")
    print("   Copy .env.example to .env and fill in your keys")
    sys.exit(1)

from qdrant_client import QdrantClient
from openai import OpenAI

# ── Config ──────────────────────────────────────────
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
CHAT_MODEL = os.environ.get("CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = "text-embedding-3-small"
COLLECTION = "sahayak_schemes"

qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ── Test Queries ────────────────────────────────────
TEST_QUERIES = [
    ("Hindi", "PM Kisan yojana mein kitna paisa milta hai aur kaise apply karein"),
    ("English", "What is the eligibility for Ayushman Bharat health insurance?"),
    ("Hinglish", "MGNREGA mein job card kaise banaye aur kitna paisa milega"),
    ("Hindi", "Gas connection ke liye kya documents chahiye"),
    ("English", "How to apply for PM Awas Yojana housing scheme?"),
    ("Hinglish", "Sukanya Samriddhi Yojana mein interest rate kya hai"),
    ("Hindi", "Ration card kaise banaye"),
    ("English", "What loans are available for small businesses?"),
]

SYSTEM_PROMPT = """You are Sahayak, a helpful assistant for Indian government schemes.
Reply in SAME language as the question. Keep it to 2-3 sentences max.
Give 1 clear next step. If unsure, say honestly."""


def embed(text: str):
    return openai_client.embeddings.create(input=text, model=EMBED_MODEL).data[0].embedding


def search(query: str, top_k: int = 3):
    return qdrant.search(
        collection_name=COLLECTION,
        query_vector=embed(query),
        limit=top_k,
        with_payload=True,
    )


def answer(query: str, results):
    context = "\n\n".join([
        f"[{r.payload['scheme']}]: {r.payload['text']}"
        for r in results
        if r.score > 0.25
    ])

    if not context:
        return "❌ No relevant context found (all scores below threshold)"

    resp = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
        max_tokens=200,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def main():
    print("\n🧪 Sahayak — Full Pipeline Test")
    print("=" * 60)

    # Check collection exists
    try:
        info = qdrant.get_collection(COLLECTION)
        count = info.points_count
        print(f"✅ Qdrant: {count} vectors in {COLLECTION}")
        if count == 0:
            print("  ⚠️  No vectors found! Run: python scripts/ingest.py first")
            return
    except Exception as e:
        print(f"❌ Qdrant error: {e}")
        print("   Run: python scripts/ingest.py first")
        return

    print(f"✅ OpenAI: {CHAT_MODEL}")
    print(f"✅ Embed: {EMBED_MODEL}")
    print()

    passed = 0
    total = len(TEST_QUERIES)

    for lang, query in TEST_QUERIES:
        print(f"[{lang}] Q: {query}")
        try:
            start = time.time()
            results = search(query)
            search_time = time.time() - start

            top_scheme = results[0].payload["scheme"] if results else "none"
            top_score = round(results[0].score, 3) if results else 0
            print(f"       🔍 Qdrant: '{top_scheme}' (score: {top_score}, {search_time:.2f}s)")

            start = time.time()
            ans = answer(query, results)
            llm_time = time.time() - start
            print(f"       💬 A: {ans}")
            print(f"       ⏱️  Search: {search_time:.2f}s | LLM: {llm_time:.2f}s")

            if top_score > 0.3:
                passed += 1
                print(f"       ✅ PASS")
            else:
                print(f"       ⚠️  LOW SCORE (< 0.3)")

        except Exception as e:
            print(f"       ❌ Error: {e}")
        print()

    print("=" * 60)
    print(f"📊 Results: {passed}/{total} queries passed (score > 0.3)")
    print()
    print("✅ Pipeline test complete!")
    print("\n🎤 Next steps:")
    print("   1. Start backend: cd backend && uvicorn main:app --reload")
    print("   2. Setup Vapi:    python scripts/setup_vapi.py")
    print("   3. Open frontend: open frontend/index.html")


if __name__ == "__main__":
    main()
