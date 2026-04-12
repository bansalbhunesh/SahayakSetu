import os
from typing import List
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# Load environment
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Initialize Client
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Use the one true Multilingual Model established in ingest.py and main.py
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
qdrant.set_model(MODEL)

def test_search(query: str):
    print(f"\n🔍 Testing Query: '{query}'")
    print("-" * 50)
    
    # Perform RAG Search
    results = qdrant.query(
        collection_name="sahayak_schemes",
        query_text=query,
        limit=3
    )
    
    # Apply the same score thresholding we use in the backend
    confident_results = [r for r in results if r.score > 0.4]
    
    if not confident_results:
        print("⚠️ No confident matches found (Score < 0.4)")
    
    for i, res in enumerate(confident_results):
        print(f"\nResult {i+1} [Score: {res.score:.4f}]")
        print(f"Scheme: {res.metadata.get('scheme', 'Unknown')}")
        print(f"Snippet: {res.document[:100]}...")

if __name__ == "__main__":
    # Test English
    test_search("Tell me about PM Kisan benefits")
    
    # Test Hindi/Hinglish
    test_search("Ayushman Bharat card kaise banaye?")
    
    # Test Regional (Kannada)
    test_search("Gruha Lakshmi yojana bagge heli")
    
    # Test Regional (Tamil)
    test_search("Magalir Urimai Thogai details")
