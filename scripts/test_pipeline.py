import os
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from openai import OpenAI

# Load env vars
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    print("❌ Critical: Missing QDRANT_URL or QDRANT_API_KEY in .env")
    sys.exit(1)

# Initialize Clients
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
# Switch to free local embeddings for the test too!
qdrant.set_model("BAAI/bge-small-en-v1.5")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

TEST_QUERIES = [
    ("Hindi", "PM Kisan yojana mein kitna paisa milta hai aur kaise apply karein"),
    ("English", "What is the eligibility for Ayushman Bharat health insurance?"),
    ("Hinglish", "MGNREGA mein job card kaise banaye aur kitna paisa milega"),
    ("Kannada", "Gruha Lakshmi yojana bagge mahiti needi")
]

def run_test():
    print("\n🧪 SahayakSetu — Full Pipeline Test (Local & Free)")
    print("============================================================")
    
    # 1. Check Qdrant Connection
    try:
        collections = qdrant.get_collections().collections
        print(f"✅ Qdrant Connected")
    except Exception as e:
        print(f"❌ Qdrant Connection Failed: {e}")
        return

    # 2. Run Multilingual Queries
    for lang, query in TEST_QUERIES:
        print(f"\n[{lang}] Q: {query}")
        try:
            # Search using free local model
            results = qdrant.query(
                collection_name="sahayak_schemes",
                query_text=query,
                limit=1
            )
            
            if results:
                context = results[0].document
                print(f"   ✅ RAG Result (Found): {context[:80]}...")
            else:
                print(f"   ⚠️ No results found in RAG.")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n✅ Pipeline check complete!")

if __name__ == "__main__":
    run_test()
