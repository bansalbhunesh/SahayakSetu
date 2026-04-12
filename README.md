# SahayakSetu (सहायक सेतु) 🚀
### Empowering Millions through Free, Localized, Voice-First AI for Government Welfare.

**SahayakSetu** is a production-ready, truly multilingual voice AI agent designed to bridge the digital and linguistic divide in India. Built for the all-India hackathon context, it enables citizens to enquire about government schemes in their mother tongue through a simple, natural voice conversation.

---

## 🏗️ The Problem & Our Solution

**The Problem**: 
Most government scheme Portals are in English/Hindi and are text-heavy. For millions of citizens, especially in rural areas or across diverse regions like Karnataka, Tamil Nadu, and West Bengal, navigating these portals is a massive barrier. Additionally, building high-quality RAG (Retrieval-Augmented Generation) systems often requires expensive cloud embedding APIs.

**The SahayakSetu Solution**:
- **Voice-First Accessibility**: No typing required. Just speak in your language.
- **Multilingual RAG**: Support for 7+ languages including **Kannada, Tamil, Telugu, Bengali, Hindi, Hinglish, and English**.
- **Cost-Free Embedding Engine**: Uses **FastEmbed** to generate vectors locally. This makes the system extremely cost-efficient and faster by eliminating cloud embedding API latency and costs.

---

## ✨ Key Features

- 🎙️ **Real-Time Voice Interactivity**: Powered by Vapi with a professional en-IN voice.
- 🌍 **Deep Regional Support**: Specifically tuned with knowledge of 13+ schemes (PM-Kisan, Ayushman Bharat, Gruha Lakshmi, Rythu Bharosa, etc.).
- 🧠 **Context-Aware RAG**: Seamlessly retrieves information from a Qdrant vector database using state-of-the-art `BGE-Small` embeddings.
- 💬 **Code-Mixed (Hinglish) Support**: Understands how people naturally talk (mixing local languages with English terms).
- 🔒 **Privacy & Efficiency**: Local embeddings ensure data parsing happens on the server, not via external paid APIs.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Voice Orchestration** | [Vapi.ai](https://vapi.ai) (Azure TTS + Deepgram STT) |
| **Large Language Model** | OpenAI GPT-4o-mini |
| **Vector Database** | [Qdrant Cloud](https://qdrant.tech/) |
| **Embedding Model** | **FastEmbed** (BAAI/bge-small-en-v1.5) — *Local & Free* |
| **Backend** | FastAPI (Python 3.12) |
| **Frontend** | Modern Vanilla JS + CSS3 (Glassmorphism UI) |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.12
- Qdrant Cloud Cluster (Free Tier)
- Vapi.ai Account

### 2. Setup Environment
Clone the repo and create a `.env` file:
```bash
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_key
OPENAI_API_KEY=your_openai_key
VAPI_API_KEY=your_vapi_private_key
VAPI_PUBLIC_KEY=your_vapi_public_key
```

### 3. Installation & Ingestion
```bash
# Create environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Ingest multilingual data (Uses Free FastEmbed)
python scripts/ingest.py
```

### 4. Run the Backend
```bash
cd backend
uvicorn main:app --reload
```

---

## 📈 Impact & Vision
SahayakSetu isn't just a bot; it's a **bridge** (Setu). By making government schemes accessible via voice in regional languages for **zero embedding cost**, we create a scalable solution that can be deployed by NGOs, local government bodies, and social enterprises to ensure no citizen is left behind due to a language barrier.

---
*Built for the Bangalore All-India Hackathon 2026.*
