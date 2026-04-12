# SahayakSetu (सहायक सेतु) 🚀
### Empowering Millions through Free, Localized, Voice-First AI for Government Welfare.

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://sahayak-setu.vercel.app)
[![Challenge](https://img.shields.io/badge/Challenge-Accessibility_%26_Societal_Impact-blue)](#)
[![Tech](https://img.shields.io/badge/Stack-Voice--First_AI-orange)](#)

**SahayakSetu** is a production-grade, multilingual voice AI agent designed to bridge the digital and linguistic divide in India. It enables citizens to access complex government schemes through natural voice conversations in their mother tongue.

---

## 🔗 🌐 Live Links (Quick Access)
*   **Live Website**: [https://sahayak-setu.vercel.app](https://sahayak-setu.vercel.app)
*   **Backend API**: [https://sahayaksetu-backend-3kxl.onrender.com](https://sahayaksetu-backend-3kxl.onrender.com)
*   **GitHub Repository**: [https://github.com/bansalbhunesh/SahayakSetu](https://github.com/bansalbhunesh/SahayakSetu)

---

## 🛠️ How It Works (Simple 5-Step Process)
We use a "Translation-Aware RAG" system to keep the app fast, free, and memory-safe!

1.  **Step 1: Speak Your Language** 🎤 
    The user speaks in their native tongue (Hindi, Kannada, Tamil, etc.).
2.  **Step 2: AI Interpretation** 🧠
    Google Gemini 1.5 Flash (our free-tier brain) interprets the intent into English keywords.
3.  **Step 3: Smart Search** 🔍
    We search 60+ verified scheme chunks using local, lightweight (70MB) embeddings.
4.  **Step 4: Regional Analysis** 🌐
    The AI matches the scheme data and translates the answer back to your mother tongue.
5.  **Step 5: Voice Response** 🔊
    SahayakSetu speaks back with a professional, empathetic Indian neural voice.

---

## 🎯 Our Competitive Edge
*   **Memory-Safe (512MB RAM)**: Optimized to run without crashing on lightweight cloud tiers.
*   **Zero-Cost Intelligence**: Switched to **Gemini 1.5 Flash** to eliminate expensive API bills.
*   **No "AI Tax"**: Using **Local FastEmbed** means our search logic is completely free to scale.
*   **Impact Focused**: Provides clear **Summary ➜ Eligibility ➜ Action Steps** for every scheme.

---

## 🛠️ Technology Stack
| Layer | Technology |
| :--- | :--- |
| **Voice / STT / TTS** | [Vapi.ai](https://vapi.ai) (Deepgram & Azure Neural) |
| **Intelligence** | **Google Gemini 1.5 Flash** (Free & Fast) |
| **Vector Database** | [Qdrant Cloud](https://qdrant.tech/) |
| **Embedding Engine** | **FastEmbed** (Local Brain) |
| **Hosting** | Vercel (Frontend) & Render (Backend) |

---

## 🚀 Easy Setup & Demo Instructions

1. **Clone the Project**
   ```bash
   git clone https://github.com/bansalbhunesh/SahayakSetu.git
   cd SahayakSetu
   ```

2. **Install Dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Configure Environment** (Create a `.env` file)
   - `GEMINI_API_KEY`
   - `QDRANT_URL` & `QDRANT_API_KEY`
   - `VAPI_API_KEY`

4. **Prepare the Intelligence**
   ```bash
   python scripts/ingest.py
   ```

5. **Start the Engine**
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

---
*Built for Hackblr 2026 — Supporting Bangalore's All-India Hackathon Spirit.* 🇮🇳🏆
