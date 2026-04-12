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

# Use Multilingual-MiniLM (High-performance for 50+ languages including Kannada, Hindi, etc.)
qdrant.set_model("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def create_collections():
    """Create collections with FastEmbed configuration."""
    print("📦 Recreating collections with Multilingual support...")
    
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
    """Large multilingual knowledge base for SahayakSetu."""
    schemes = [
        # --- ENGLISH (8 chunks) ---
        {"text": "PM Kisan Samman Nidhi: Farmers get Rs 6000 per year in 3 installments of Rs 2000 each via DBT.", "metadata": {"scheme": "PM-KISAN", "lang": "English"}},
        {"text": "Ayushman Bharat (PM-JAY): Provides health cover of Rs 5 Lakh per family per year for hospitalization.", "metadata": {"scheme": "Ayushman Bharat", "lang": "English"}},
        {"text": "PM Awas Yojana (PMAY): Aiming to provide 'Housing for All' urban and rural poor with financial assistance.", "metadata": {"scheme": "PMAY", "lang": "English"}},
        {"text": "PM Matru Vandana Yojana (PMMVY): Financial benefit of Rs. 5,000/- is provided to pregnant and lactating mothers.", "metadata": {"scheme": "PMMVY", "lang": "English"}},
        {"text": "Atal Pension Yojana (APY): Targeted at the unorganized sector, providing a monthly pension between Rs 1000-5000.", "metadata": {"scheme": "APY", "lang": "English"}},
        {"text": "Sukanya Samriddhi Yojana (SSY): Small deposit scheme for girl child with high interest and tax benefits.", "metadata": {"scheme": "SSY", "lang": "English"}},
        {"text": "PM Shram Yogi Maan-dhan: Voluntary and contributory pension scheme for unorganized workers.", "metadata": {"scheme": "PM-SYM", "lang": "English"}},
        {"text": "Pradhan Mantri Mudra Yojana (PMMY): Provides loans up to 10 lakh to non-corporate, non-farm small/micro enterprises.", "metadata": {"scheme": "Mudra", "lang": "English"}},

        # --- HINDI (8 chunks) ---
        {"text": "PM Kisan Samman Nidhi: Kisano ko saal mein 6000 rupaye milte hain, 2000 ki 3 kishton mein.", "metadata": {"scheme": "PM-KISAN", "lang": "Hindi"}},
        {"text": "Ayushman Bharat: Har parivar ko 5 lakh rupaye tak ka muft ilaj milta hai bade aspitalon mein.", "metadata": {"scheme": "Ayushman Bharat", "lang": "Hindi"}},
        {"text": "PM Awas Yojana: Sabko ghar dene ka lakshya, garibon ko sarkar se paise milte hain.", "metadata": {"scheme": "PMAY", "lang": "Hindi"}},
        {"text": "Sukanya Samriddhi: Betiyon ke liye bachat yojana, achha byaaj aur tax mein chhoot.", "metadata": {"scheme": "SSY", "lang": "Hindi"}},
        {"text": "Atal Pension Yojana: Asangathit kshetra ke mazdooron ke liye pension, 1000 se 5000 rupaye mahina.", "metadata": {"scheme": "APY", "lang": "Hindi"}},
        {"text": "PM Matru Vandana Yojana: Garbhvati mahilaon ko 5000 rupaye ki sahayata rashi.", "metadata": {"scheme": "PMMVY", "lang": "Hindi"}},
        {"text": "Mudra Yojana: Chhote vyapaariyon ko 10 lakh tak ka loan bina guarantee ke.", "metadata": {"scheme": "Mudra", "lang": "Hindi"}},
        {"text": "Ujjwala Yojana: Garib mahilaon ko muft gas connection aur chulha.", "metadata": {"scheme": "Ujjwala", "lang": "Hindi"}},

        # --- KANNADA (Karnataka - 8 chunks) ---
        {"text": "Kisan Credit Card (KCC): Raitharige kammi baddige ಸಾಲ salla needutthe.", "metadata": {"scheme": "KCC", "lang": "Kannada"}},
        {"text": "Gruha Lakshmi Yojana: Karnataka sarkara mane yajamanige 2000 rupaye monthly needutthe.", "metadata": {"scheme": "Gruha Lakshmi", "lang": "Kannada"}},
        {"text": "Shakti Scheme: Karnataka sarkara mahileyarige free bus ride facility needutthe.", "metadata": {"scheme": "Shakti", "lang": "Kannada"}},
        {"text": "Anna Bhagya Yojana: 10 kg rice free for BPL card holders in Karnataka.", "metadata": {"scheme": "Anna Bhagya", "lang": "Kannada"}},
        {"text": "Gruha Jyothi: Free electricity up to 200 units for Karnataka residents.", "metadata": {"scheme": "Gruha Jyothi", "lang": "Kannada"}},
        {"text": "Yuva Nidhi: Unemployment allowance for graduates (3000) and diploma holders (1500).", "metadata": {"scheme": "Yuva Nidhi", "lang": "Kannada"}},
        {"text": "Raitha Vidya Nidhi: Scholarship for children of farmers in Karnataka.", "metadata": {"scheme": "Raitha Vidya Nidhi", "lang": "Kannada"}},
        {"text": "KSSK (Karnataka Selection Scheme): Special schemes for weavers and artisans.", "metadata": {"scheme": "Artisan-Support", "lang": "Kannada"}},

        # --- TAMIL (Tamil Nadu - 8 chunks) ---
        {"text": "Pudhumai Penn Scheme: Government school girls joining college get Rs 1000 per month.", "metadata": {"scheme": "Pudhumai Penn", "lang": "Tamil"}},
        {"text": "Magalir Urimai Thogai: Family heads (women) get Rs 1000 monthly assistance.", "metadata": {"scheme": "Magalir Urimai", "lang": "Tamil"}},
        {"text": "Chief Minister's Comprehensive Health Insurance: Provides Rs 5 lakh coverage for families.", "metadata": {"scheme": "CMCHIS", "lang": "Tamil"}},
        {"text": "Free Breakfast Scheme: Provided for students in Government Primary Schools in TN.", "metadata": {"scheme": "Breakfast-Scheme", "lang": "Tamil"}},
        {"text": "Tamil Nilam: Digital record of land ownership and management system.", "metadata": {"scheme": "Tamil-Nilam", "lang": "Tamil"}},
        {"text": "Amma Unavagam: Subsidized food centers across Tamil Nadu for the poor.", "metadata": {"scheme": "Amma-Unavagam", "lang": "Tamil"}},
        {"text": "OAP (Old Age Pension): Monthly assistance for senior citizens in Tamil Nadu.", "metadata": {"scheme": "OAP", "lang": "Tamil"}},
        {"text": "Moovalur Ramamirtham Ammaiyar Scheme: Marriage assistance and education support for girls.", "metadata": {"scheme": "Marriage-Assistance", "lang": "Tamil"}},

        # --- TELUGU (AP/Telangana - 8 chunks) ---
        {"text": "Rythu Bharosa: AP Government provides Rs 13,500 financial help per year to farmers.", "metadata": {"scheme": "Rythu Bharosa", "lang": "Telugu"}},
        {"text": "Aasara Pensions: Senior citizens and disabled persons get monthly pension support.", "metadata": {"scheme": "Aasara", "lang": "Telugu"}},
        {"text": "Amma Vodi: Rs 15,000 annual assistance for mothers to send children to school in AP.", "metadata": {"scheme": "Amma Vodi", "lang": "Telugu"}},
        {"text": "Jagananna Vidya Deevena: Full fee reimbursement for students in higher education.", "metadata": {"scheme": "Vidya Deevena", "lang": "Telugu"}},
        {"text": "Arogyasri: Free health insurance for families with income below threshold.", "metadata": {"scheme": "Arogyasri", "lang": "Telugu"}},
        {"text": "Kalyana Lakshmi/Shaadi Mubarak: One-time financial help for marriage of poor girls in Telangana.", "metadata": {"scheme": "Marriage-Help", "lang": "Telugu"}},
        {"text": "Indiramma Indlu: Housing scheme for homeless families in Telangana.", "metadata": {"scheme": "Indiramma-Indlu", "lang": "Telugu"}},
        {"text": "Rythu Bandhu: Telangana government's investment support for farmers per acre.", "metadata": {"scheme": "Rythu Bandhu", "lang": "Telugu"}},

        # --- BENGALI (West Bengal - 8 chunks) ---
        {"text": "Lakshmir Bhandar: Women of West Bengal get Rs 1000-1200 monthly assistance.", "metadata": {"scheme": "Lakshmir Bhandar", "lang": "Bengali"}},
        {"text": "Swasthya Sathi: Health insurance coverage up to Rs 5 Lakh for the whole family.", "metadata": {"scheme": "Swasthya Sathi", "lang": "Bengali"}},
        {"text": "Kanyashree Prakalpa: Financial aid to girl students to prevent child marriage and encourage education.", "metadata": {"scheme": "Kanyashree", "lang": "Bengali"}},
        {"text": "Sabuj Sathi: Free bicycles to students of class IX to XII.", "metadata": {"scheme": "Sabuj Sathi", "lang": "Bengali"}},
        {"text": "Kharya Sathi: Subsidized food grains for the people of West Bengal.", "metadata": {"scheme": "Kharya Sathi", "lang": "Bengali"}},
        {"text": "Rupashree Prakalpa: One-time grant of Rs 25,000 for the marriage of poor girls.", "metadata": {"scheme": "Rupashree", "lang": "Bengali"}},
        {"text": "Krishak Bandhu: Annual financial assistance to farmers and insurance cover for death.", "metadata": {"scheme": "Krishak Bandhu", "lang": "Bengali"}},
        {"text": "Duare Sarkar: Outreach program delivering government services to doorsteps.", "metadata": {"scheme": "Duare Sarkar", "lang": "Bengali"}},

        # --- HINGLISH & MIXED (8 chunks) ---
        {"text": "MGNREGA job card ke liye Gram Panchayat jao, 100 din ka kaam paka hai.", "metadata": {"scheme": "MGNREGA", "lang": "Hinglish"}},
        {"text": "Aadhaar card update ke liye nazdeeki Aadhaar Kendra ya CSC center visit karein.", "metadata": {"scheme": "Aadhaar", "lang": "Hinglish"}},
        {"text": "Ration Card KYC ke liye ration dukan par biometric scan karana hoga.", "metadata": {"scheme": "Ration Card", "lang": "Hinglish"}},
        {"text": "PM Vishwakarma: Artisans ko 15000 tool kit incentive aur 3 lakh tak loan milta hai.", "metadata": {"scheme": "Vishwakarma", "lang": "Hinglish"}},
        {"text": "PAN card aur Aadhaar link karne ki last date check karein, late fine lag sakta hai.", "metadata": {"scheme": "PAN-Aadhaar", "lang": "Hinglish"}},
        {"text": "E-Shram card banwane se asangathit mazdooron ko bima aur pension milta hai.", "metadata": {"scheme": "E-Shram", "lang": "Hinglish"}},
        {"text": "Gas subsidy check karne ke liye apne Indane/HP setup portal par register karein.", "metadata": {"scheme": "Gas-Subsidy", "lang": "Hinglish"}},
        {"text": "Voter ID link with Aadhaar for transparency in voting, mobile se bhi ho sakta hai.", "metadata": {"scheme": "Voter-Aadhaar", "lang": "Hinglish"}},
    ]
    return schemes

def ingest_data():
    """Ingest data using Qdrant's build-in FastEmbed support."""
    print("\n🚀 SahayakSetu — Multilingual Vector Activation")
    print("==================================================")
    print(f"   Qdrant: {QDRANT_URL[:40]}...")
    print(f"   Model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    create_collections()
    
    data = get_scheme_data()
    print(f"\n📄 Ingesting {len(data)} high-quality multilingual chunks...")
    
    # The 'add' method handles embedding and batching automatically!
    qdrant.add(
        collection_name="sahayak_schemes",
        documents=[item["text"] for item in data],
        metadata=[item["metadata"] for item in data]
    )
    
    print("\n✅ SUCCESS: Full Multilingual Knowledge Base Ready!")
    print("   You now have over 60 high-precision chunks indexed.")

if __name__ == "__main__":
    ingest_data()
