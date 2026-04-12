# SahayakSetu (सहायक सेतु) 🚀
### Your Multilingual Voice Bridge to Government Welfare

**SahayakSetu** is a smart AI assistant that helps anyone in India find government schemes just by speaking their mother tongue. 

---

## 🔗 Quick Links (Live Now!)
*   **Live Website**: [https://sahayak-setu.vercel.app](https://sahayak-setu.vercel.app)
*   **Backend API**: [https://sahayaksetu-backend-3kxl.onrender.com](https://sahayaksetu-backend-3kxl.onrender.com)
*   **GitHub Code**: [https://github.com/bansalbhunesh/SahayakSetu](https://github.com/bansalbhunesh/SahayakSetu)

---

## 🛠️ How It Works (Simple Steps)
We use a high-performance "Translation-RAG" system to keep the app fast and free!

**The User Journey:**
1.  **You Speak** (Kannada, Hindi, Tamil, etc.) ➔ 
2.  **AI Understands** (GPT-4o interprets your intent) ➔ 
3.  **Smart Search** (AI searches our English database for exact scheme matches) ➔ 
4.  **Local Brain** (FastEmbed retrieves info with zero data costs) ➔ 
5.  **Voice Response** (AI explains everything back to you in your native language!)

---

## 🌟 Why This Wins
*   **No Cost AI**: We use local embedding models, so we don't pay "AI taxes" for searching data.
*   **Truly Inclusive**: It doesn't matter if you can't read or write—just talk to SahayakSetu.
*   **Memory-Safe**: Optimized to run on lightweight cloud servers (Fits in 512MB RAM safely).
*   **Action Oriented**: It doesn't just give answers; it tells you exactly where to go next.

---

## 🚀 Easy Setup to Run Locally

### Step 1: Clone the Project
`git clone https://github.com/bansalbhunesh/SahayakSetu.git` ➔ `cd SahayakSetu`

### Step 2: Install Python Tools
`pip install -r backend/requirements.txt`

### Step 3: Add Your Keys
Create a `.env` file in the backend folder and add:
*   `OPENAI_API_KEY`
*   `QDRANT_URL`
*   `VAPI_API_KEY`

### Step 4: Load the Data
`python scripts/ingest.py` (This ➔ Loads 60+ schemes into your AI brain)

### Step 5: Start the App!
`python -m uvicorn backend.main:app --reload` ➔ **Visit http://localhost:5500**

---

### **Built for Hackblr 2026 — Innovation for Impact** 🇮🇳🏆
*Bridging the gap between technology and the citizens who need it most.*
