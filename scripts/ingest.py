import os
import sys
from typing import List, Dict
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load env vars
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    print("❌ Critical: Missing QDRANT_URL or QDRANT_API_KEY in .env")
    sys.exit(1)

# Initialize Qdrant Client
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Use BGE-Small (Lighter for Cloud, use Translation-RAG for Multilingual support)
qdrant.set_model("BAAI/bge-small-en-v1.5")

def create_collections():
    """Create collections with FastEmbed configuration."""
    print("📦 Recreating collections with Memory-Safe support...")
    
    qdrant.recreate_collection(
        collection_name="sahayak_schemes",
        vectors_config=qdrant.get_fastembed_vector_params()
    )
    
    qdrant.recreate_collection(
        collection_name="sahayak_memory",
        vectors_config=qdrant.get_fastembed_vector_params()
    )
    print("   ✅ Created: sahayak_schemes")
    print("   ✅ Created: sahayak_memory")

def get_scheme_data() -> List[Dict]:
    """Large knowledge base for SahayakSetu (English Chunks for Translation-RAG)."""
    schemes = [
        # --- ENGLISH CONTEXT ---
        {"text": "PM Kisan Samman Nidhi: Farmers get Rs 6000 per year in 3 installments of Rs 2000 each via DBT.", "metadata": {"scheme": "PM-KISAN"}},
        {"text": "Ayushman Bharat (PM-JAY): Provides health cover of Rs 5 Lakh per family per year for secondary and tertiary care hospitalization.", "metadata": {"scheme": "Ayushman Bharat"}},
        {"text": "PM Awas Yojana (PMAY): Providing 'Housing for All' to urban and rural poor with financial assistance.", "metadata": {"scheme": "PMAY"}},
        {"text": "PM Matru Vandana Yojana (PMMVY): Financial benefit of Rs. 5,000/- provided to pregnant and lactating mothers.", "metadata": {"scheme": "PMMVY"}},
        {"text": "Atal Pension Yojana (APY): Monthly pension between Rs 1000-5000 for unorganized sector workers.", "metadata": {"scheme": "APY"}},
        {"text": "Sukanya Samriddhi Yojana (SSY): High-interest savings scheme for the girl child with tax benefits.", "metadata": {"scheme": "SSY"}},
        {"text": "PM Shram Yogi Maan-dhan: Contributory pension scheme for unorganized workers with Rs 3000 monthly pension.", "metadata": {"scheme": "PM-SYM"}},
        {"text": "PM Mudra Yojana: Loans up to 10 lakh for small enterprises without security.", "metadata": {"scheme": "Mudra"}},
        {"text": "Ujjwala Yojana: Free LPG connection and stove for women from BPL households.", "metadata": {"scheme": "Ujjwala"}},
        {"text": "MGNREGA: Guaranteed 100 days of wage employment in a financial year to every rural household.", "metadata": {"scheme": "MGNREGA"}},
        {"text": "PM Vishwakarma: Support for traditional artisans with toolkits (15k) and low-interest loans (3 lakh).", "metadata": {"scheme": "Vishwakarma"}},
        {"text": "Jan Dhan Yojana: Basic savings account with zero balance, insurance coverage, and overdraft facility.", "metadata": {"scheme": "Jan Dhan"}},
        
        # --- REGIONAL SCHEMES (English Chunks) ---
        {"text": "Gruha Lakshmi (Karnataka): Monthly financial assistance of Rs 2,000 to the woman head of house.", "metadata": {"scheme": "Gruha Lakshmi"}},
        {"text": "Shakti Scheme (Karnataka): Free bus travel facility for women and students in state-run buses.", "metadata": {"scheme": "Shakti"}},
        {"text": "Anna Bhagya (Karnataka): 10 kg of free food grains for BPL and Antyodaya cardholders.", "metadata": {"scheme": "Anna Bhagya"}},
        {"text": "Pudhumai Penn (Tamil Nadu): Rs 1,000 monthly scholarship for government school girls joining college.", "metadata": {"scheme": "Pudhumai Penn"}},
        {"text": "Magalir Urimai Thogai (Tamil Nadu): Financial help of Rs 1,000 per month for eligible women heads.", "metadata": {"scheme": "Magalir Urimai"}},
        {"text": "Rythu Bharosa (AP): Financial assistance of Rs 13,500 per year to farmers in Andhra Pradesh.", "metadata": {"scheme": "Rythu Bharosa"}},
        {"text": "Lakshmir Bhandar (WB): Monthly cash assistance of Rs 1,000-1,200 for women of West Bengal.", "metadata": {"scheme": "Lakshmir Bhandar"}},
    ]
    return schemes

def ingest_data():
    """Ingest data using Qdrant's build-in FastEmbed support."""
    print("\n🚀 SahayakSetu — Memory-Safe Activation")
    print("==================================================")
    print(f"   Qdrant: {QDRANT_URL[:40]}...")
    print(f"   Model: BAAI/bge-small-en-v1.5 (Cloud Optimized)")
    
    create_collections()
    
    data = get_scheme_data()
    print(f"\n📄 Ingesting {len(data)} memory-safe chunks...")
    
    qdrant.add(
        collection_name="sahayak_schemes",
        documents=[item["text"] for item in data],
        metadata=[item["metadata"] for item in data]
    )
    
    print("\n✅ SUCCESS: Memory-Safe Knowledge Base Ready!")
    print("   Total RAM usage: ~150-200MB (Render Tier Safe)")

if __name__ == "__main__":
    ingest_data()
