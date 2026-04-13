import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# Load environment
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Initialize Client
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
qdrant.set_model("BAAI/bge-small-en-v1.5")

def test_search(query: str):
    print(f"\n[TESTING] Query: '{query}'")
    results = qdrant.query(collection_name="sahayak_schemes", query_text=query, limit=3)
    
    # Match production threshold (Audit v3 fix)
    confident_results = [r for r in results if r.score > 0.2]
    
    if not confident_results:
        print("[WARNING] No confident matches found (Score < 0.2)")
    
    for i, res in enumerate(confident_results):
        print(f"\nResult {i+1} [Score: {res.score:.4f}]")
        print(f"Scheme: {res.metadata.get('scheme', 'Unknown')}")
        print(f"Snippet: {res.document[:100]}...")

if __name__ == "__main__":
    test_search("Tell me about PM Kisan benefits")
    test_search("Ayushman Bharat card kaise banaye?")
