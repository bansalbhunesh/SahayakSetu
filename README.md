# 🇮🇳 SahayakSetu (सहायक सेतु) — Multilingual Voice AI for Indian Government Schemes

<div align="center">

**Bridging the gap between citizens and government welfare schemes through multilingual voice AI**

*"Setu" (सेतु) means "bridge" — SahayakSetu bridges the information gap for ALL Indian citizens, regardless of the language they speak.*

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC382D?logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Vapi](https://img.shields.io/badge/Vapi-Voice_AI-6366F1)](https://vapi.ai)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)](https://openai.com)

</div>

---

## 🎯 Problem Statement

> India has 900+ government welfare schemes, but most citizens — especially in rural and semi-urban areas — face barriers accessing them due to **language diversity**, **literacy constraints**, and **complex bureaucratic processes**.

SahayakSetu solves this by providing a **multilingual voice-first AI assistant** that lets anyone ask about government schemes in **their own language** — English, Hindi, Kannada, Tamil, Telugu, Bengali, Marathi, or Hinglish — and get instant, accurate, actionable answers.

### Why Multilingual?

| Language | Speakers | Region Coverage |
|----------|----------|-----------------|
| English | 125M+ | Pan-India, urban |
| Hindi | 600M+ | North & Central India |
| Kannada | 45M+ | Karnataka |
| Tamil | 80M+ | Tamil Nadu, Sri Lanka |
| Telugu | 83M+ | Telangana, Andhra Pradesh |
| Bengali | 100M+ | West Bengal, Tripura |
| Marathi | 83M+ | Maharashtra |
| Hinglish | 350M+ | Urban India |

**Total addressable users: 900M+ Indians**

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              User (Voice / Text)                 │
│  🎤 Any language: English, Hindi, Kannada, etc.  │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│              Vapi (Voice Layer)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Deepgram │  │ GPT-4o   │  │ Azure TTS    │   │
│  │ STT      │→ │ Router   │→ │ en-IN Voice  │   │
│  │ (multi)  │  │          │  │ (Neerja)     │   │
│  └──────────┘  └────┬─────┘  └──────────────┘   │
└─────────────────────┼───────────────────────────┘
                      │ Function: search_schemes
                      ▼
┌─────────────────────────────────────────────────┐
│         FastAPI Backend (Webhook Handler)          │
│  ┌──────────────┐  ┌────────────────────────┐    │
│  │ Qdrant Search │  │ OpenAI Answer Gen     │    │
│  │ (Semantic)    │→ │ (Multilingual RAG)    │    │
│  └──────────────┘  └────────────────────────┘    │
│  ┌──────────────┐                                │
│  │ User Memory  │ ← Personalized context         │
│  └──────────────┘                                │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              Qdrant Cloud                         │
│  ┌───────────────────┐  ┌───────────────────┐    │
│  │ sahayak_schemes   │  │ sahayak_memory    │    │
│  │ 55+ vectors       │  │ Per-user history  │    │
│  │ 7 languages       │  │ Conversation ctx  │    │
│  └───────────────────┘  └───────────────────┘    │
└─────────────────────────────────────────────────┘
```

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎤 **Voice-First** | Speak naturally — no typing needed. Perfect for low-literacy users |
| 🌍 **7+ Languages** | English, Hindi, Kannada, Tamil, Telugu, Bengali, Marathi, Hinglish |
| 🧠 **RAG Pipeline** | Answers grounded in verified government data via Qdrant semantic search |
| 💬 **Auto Language Detection** | Responds in YOUR language automatically |
| 🔒 **Conversation Memory** | Remembers past questions for personalized follow-ups |
| 📱 **Works Everywhere** | Web browser — no app download needed |
| ⚡ **Real-Time** | Optimized voice pipeline with < 2s response time |
| 🎯 **13+ Schemes** | PM Kisan, Ayushman Bharat, Ujjwala, MGNREGA, and more |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Qdrant Cloud](https://cloud.qdrant.io) account (free tier)
- [OpenAI](https://platform.openai.com/api-keys) API key
- [Vapi](https://dashboard.vapi.ai) account (use code `vapixhackblr` for $30 free credits)

### 1. Clone & Setup
```bash
git clone https://github.com/bansalbhunesh/SahayakSetu.git
cd SahayakSetu

# Create environment
cp .env.example .env
# Edit .env with your actual keys
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Ingest Multilingual Data
```bash
python scripts/ingest.py
```
This creates Qdrant collections and loads **55+ knowledge chunks** in **7 languages** covering **13+ schemes**.

### 4. Test Pipeline
```bash
python scripts/test_pipeline.py
```
Runs multilingual end-to-end tests: embedding → search → LLM answer.

### 5. Start Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 6. Setup Vapi (Voice)
```bash
# Expose your backend (for local dev)
ngrok http 8000

# Update BACKEND_URL in .env with the ngrok URL
python scripts/setup_vapi.py
```

### 7. Open Frontend
Open `frontend/index.html` in your browser. Update `VAPI_PUBLIC_KEY` and `VAPI_ASSISTANT_ID` in `frontend/app.js`.

## 🐳 Docker Deployment
```bash
docker-compose up --build
```

## 📁 Project Structure
```
SahayakSetu/
├── backend/
│   ├── main.py              # FastAPI + Vapi webhook + Multilingual RAG
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Premium dark-theme web UI
│   ├── style.css            # Design system (Indian flag palette)
│   └── app.js               # Vapi integration + text fallback
├── scripts/
│   ├── ingest.py            # Multilingual scheme data → Qdrant
│   ├── test_pipeline.py     # End-to-end pipeline tests
│   └── setup_vapi.py        # Create Vapi assistant via API
├── .env.example             # Environment variable template
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔐 Required Credentials

| Service | Keys Needed | Where to Get |
|---------|-------------|--------------|
| **Qdrant** | `QDRANT_URL`, `QDRANT_API_KEY` | [cloud.qdrant.io](https://cloud.qdrant.io) (free tier) |
| **OpenAI** | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) |
| **Vapi** | `VAPI_API_KEY`, `VAPI_PUBLIC_KEY` | [dashboard.vapi.ai](https://dashboard.vapi.ai) (code: `vapixhackblr`) |

## 🎤 Covered Schemes (Multilingual)

| # | Scheme | Category | Benefit | Languages |
|---|--------|----------|---------|-----------|
| 1 | PM Kisan Samman Nidhi | Agriculture | ₹6,000/year | EN, HI, KN, TA, TE, BN |
| 2 | Ayushman Bharat PM-JAY | Health | ₹5L health insurance | EN, HI, KN, TA, TE, BN |
| 3 | PM Ujjwala Yojana | Energy | Free LPG connection | EN, HI, KN |
| 4 | MGNREGA | Employment | 100 days work | EN, HI, KN, TA |
| 5 | PM Awas Yojana | Housing | Home subsidy | EN, HI |
| 6 | Ration Card / PDS | Food Security | Subsidized grains | HI |
| 7 | Sukanya Samriddhi | Women & Children | 8.2% savings | HI |
| 8 | PM Jan Dhan Yojana | Financial | Zero balance a/c | HI |
| 9 | PM Mudra Yojana | Business | ₹10L loan | EN, HI |
| 10 | Ladli Behna | Women | ₹1,250/month | HI |
| 11 | Kisan Credit Card | Agriculture | 4% loan | HI |
| 12 | Atal Pension Yojana | Pension | ₹5,000/month | HI |
| 13 | PM Fasal Bima | Agriculture | Crop insurance | HI |

**Adding more regional language chunks is as simple as adding entries to `scripts/ingest.py`.**

## 🧪 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health (Qdrant + OpenAI status) |
| `/vapi-webhook` | POST | Vapi tool calls + lifecycle events |
| `/api/search` | POST | Text-based multilingual scheme search |
| `/api/schemes` | GET | List all schemes in knowledge base |
| `/api/assistant-config` | GET | Vapi assistant configuration |

## 🏆 Hackathon Impact

### Societal Impact
- **900M+ potential users** across India's linguistic diversity
- **Low-literacy accessible** — voice interface, no reading/typing needed
- **Language-inclusive** — works in 7+ Indian languages, not just Hindi/English
- **Reduces information asymmetry** — citizens learn about entitlements they didn't know existed
- **Works in rural areas** — optimized for low-bandwidth, basic devices

### Technical Innovation
- **Multilingual RAG** — semantic search works across language boundaries
- **Consistent embedding pipeline** — OpenAI `text-embedding-3-small` everywhere
- **Contextual memory** — per-user conversation history stored in Qdrant
- **Language-adaptive responses** — auto-detects and responds in user's language
- **Low-confidence detection** — honestly says when it doesn't know

## 🤝 Built With

| Technology | Role |
|------------|------|
| [Vapi](https://vapi.ai) | Voice orchestration (STT + LLM + TTS) |
| [Qdrant](https://qdrant.tech) | Vector database for semantic search + memory |
| [OpenAI](https://openai.com) | Embeddings + LLM answer generation |
| [FastAPI](https://fastapi.tiangolo.com) | Backend webhook handler |
| [Deepgram](https://deepgram.com) | Multilingual speech-to-text |
| [Azure TTS](https://azure.microsoft.com) | Indian English neural voice |

## 📜 License

MIT License — Built for Indian citizens 🇮🇳
