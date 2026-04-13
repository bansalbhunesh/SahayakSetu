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
qdrant.set_model("BAAI/bge-small-en-v1.5")

def create_collections():
    print("📦 Recreating collections with Memory-Safe support...")
    qdrant.recreate_collection(
        collection_name="sahayak_schemes",
        vectors_config=qdrant.get_fastembed_vector_params()
    )
    print("   ✅ Created: sahayak_schemes")

def get_scheme_data() -> List[Dict]:
    """Large knowledge base for SahayakSetu (Definitive 38 Chunks)."""
    schemes = [
        # --- NATIONAL SCHEMES (1-20) ---
        {"text": "PM Kisan Samman Nidhi: Farmers get Rs 6000 per year in 3 installments of Rs 2000 each via DBT.", "metadata": {"scheme": "PM-KISAN"}},
        {"text": "Ayushman Bharat (PM-JAY): Provides health cover of Rs 5 Lakh per family per year for hospitalization.", "metadata": {"scheme": "Ayushman Bharat"}},
        {"text": "PM Awas Yojana (PMAY): Providing 'Housing for All' to urban and rural poor with financial assistance.", "metadata": {"scheme": "PMAY"}},
        {"text": "PM Matru Vandana Yojana (PMMVY): Financial benefit of Rs. 5,000/- provided to pregnant mothers.", "metadata": {"scheme": "PMMVY"}},
        {"text": "Atal Pension Yojana (APY): Monthly pension between Rs 1000-5000 for unorganized sector workers.", "metadata": {"scheme": "APY"}},
        {"text": "Sukanya Samriddhi Yojana (SSY): High-interest savings scheme for the girl child with tax benefits.", "metadata": {"scheme": "SSY"}},
        {"text": "PM Mudra Yojana: Loans up to 10 lakh for small enterprises without security.", "metadata": {"scheme": "Mudra"}},
        {"text": "Ujjwala Yojana: Free LPG connection and stove for women from BPL households.", "metadata": {"scheme": "Ujjwala"}},
        {"text": "MGNREGA: Guaranteed 100 days of wage employment in a financial year to rural households.", "metadata": {"scheme": "MGNREGA"}},
        {"text": "PM Vishwakarma: Support for traditional artisans with toolkits (15k) and low-interest loans (3L).", "metadata": {"scheme": "Vishwakarma"}},
        {"text": "Jan Dhan Yojana: Basic savings account with zero balance, insurance, and overdraft facility.", "metadata": {"scheme": "Jan Dhan"}},
        {"text": "PM SVANidhi: Micro-credit facility for street vendors to access collateral-free loans up to Rs 50,000.", "metadata": {"scheme": "SVANidhi"}},
        {"text": "Stand-Up India: Bank loans (10L-1Cr) for at least one SC/ST and one woman borrower per branch.", "metadata": {"scheme": "Stand-Up India"}},
        {"text": "PM Suraksha Bima Yojana (PMSBY): Accidental death/disability cover of 2L for Rs 20/year.", "metadata": {"scheme": "PMSBY"}},
        {"text": "PM Jeevan Jyoti Bima Yojana (PMJJBY): Life insurance cover of 2L for Rs 436/year.", "metadata": {"scheme": "PMJJBY"}},
        {"text": "PM Shram Yogi Maan-dhan: Contributory pension scheme for unorganized workers with Rs 3000 monthly pension.", "metadata": {"scheme": "PM-SYM"}},
        {"text": "PM Vaya Vandana Yojana: Pension scheme for seniors (60+) with 7.4% assured returns.", "metadata": {"scheme": "Vaya Vandana"}},
        {"text": "One Nation One Ration Card: Allows beneficiaries to lift foodgrains from any FPS in India via Aadhaar.", "metadata": {"scheme": "ONORC"}},
        {"text": "Digital India (CSC): Common Service Centers provide G2C services like Aadhaar and PAN.", "metadata": {"scheme": "Digital India"}},
        {"text": "Skill India (PMKVY): Short-term training/certification for youth with financial rewards.", "metadata": {"scheme": "PMKVY"}},
        
        # --- NATIONAL SECONDARY (21-30) ---
        {"text": "PM Poshan (Mid-Day Meal): Ensures nutritional food for all school-going children in gov schools.", "metadata": {"scheme": "PM Poshan"}},
        {"text": "Jal Jeevan Mission: Target to provide Har Ghar Jal (piped water) to every rural household.", "metadata": {"scheme": "Jal Jeevan"}},
        {"text": "Mission Indradhanush: Immunization coverage for pregnant women and children against diseases.", "metadata": {"scheme": "Indradhanush"}},
        {"text": "PM-GKAY: Free 5kg food grains per person per month to NFSA beneficiaries.", "metadata": {"scheme": "PM-GKAY"}},
        {"text": "PMAY-Gramin: Interest subvention and financial help for rural housing construction.", "metadata": {"scheme": "PMAY-G"}},
        {"text": "Kisan Credit Card (KCC): Provides timely credit to farmers for seasonal agriculture.", "metadata": {"scheme": "KCC"}},
        {"text": "PM SVANidhi Part 2: Working capital loan 2nd tranche (20k) and 3rd tranche (50k) eligibility.", "metadata": {"scheme": "SVANidhi"}},
        {"text": "Rashtriya Krishi Vikas Yojana: Supporting holistic development of agriculture sectors.", "metadata": {"scheme": "RKVY"}},
        {"text": "PM-CARES for Children: Support for children orphaned by COVID-19 pandemic.", "metadata": {"scheme": "PM-CARES"}},
        {"text": "Sovereign Gold Bond (SGB): Government securities denominated in grams of gold.", "metadata": {"scheme": "SGB"}},

        # --- REGIONAL & RESTORED (31-38) ---
        {"text": "Gruha Lakshmi (Karnataka): Monthly financial assistance of Rs 2,000 to the woman head of house.", "metadata": {"scheme": "Gruha Lakshmi"}},
        {"text": "Shakti Scheme (Karnataka): Free bus travel facility for women and students.", "metadata": {"scheme": "Shakti"}},
        {"text": "Anna Bhagya (Karnataka): 10 kg of free food grains for BPL and Antyodaya cardholders.", "metadata": {"scheme": "Anna Bhagya"}},
        {"text": "Rythu Bharosa (AP): Financial assistance of Rs 13,500 per year to farmers in Andhra Pradesh.", "metadata": {"scheme": "Rythu Bharosa"}},
        {"text": "Pudhumai Penn (Tamil Nadu): Rs 1,000 monthly scholarship for gov school girls joining college.", "metadata": {"scheme": "Pudhumai Penn"}},
        {"text": "Magalir Urimai Thogai (Tamil Nadu): Financial help of Rs 1,000 per month for women heads.", "metadata": {"scheme": "Magalir Urimai"}},
        {"text": "Swachh Bharat (Gramin): Financial incentive of Rs 12,000 provided for toilet construction.", "metadata": {"scheme": "Swachh Bharat"}},
        {"text": "Deendayal Antyodaya (NRLM): Organizing rural poor into self-help groups for livelihoods.", "metadata": {"scheme": "NRLM"}},
    ]
    return schemes

def ingest_data():
    print("\n🚀 SahayakSetu — Definitive Knowledge Lockdown")
    create_collections()
    data = get_scheme_data()
    print(f"\n📄 Ingesting {len(data)} definitive chunks (Audit v6 High-Coverage)...")
    qdrant.add(
        collection_name="sahayak_schemes",
        documents=[item["text"] for item in data],
        metadata=[item["metadata"] for item in data]
    )
    print("\n✅ SUCCESS: 38-Chunk Honesty Repository Ready!")

if __name__ == "__main__":
    ingest_data()
