# SahayakSetu (सहायक सेतु) 🚀
### Empowering Millions through Free, Localized, Voice-First AI for Government Welfare.

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://sahayak-setu.vercel.app)
[![Challenge](https://img.shields.io/badge/Challenge-Accessibility_%26_Societal_Impact-blue)](#)
[![Tech](https://img.shields.io/badge/Stack-Voice--First_AI-orange)](#)

**SahayakSetu** is a production-grade, multilingual voice AI agent designed to bridge the digital and linguistic divide in India. It enables citizens to access complex government schemes through natural voice conversations in their mother tongue.

---

## 🔗 Quick Links (Live Now!)
*   **Live Website**: [https://sahayak-setu.vercel.app](https://sahayak-setu.vercel.app)
*   **Backend API**: [https://sahayaksetu-backend-3kxl.onrender.com](https://sahayaksetu-backend-3kxl.onrender.com)
*   **GitHub**: [https://github.com/bansalbhunesh/SahayakSetu](https://github.com/bansalbhunesh/SahayakSetu)

---

## 🏛️ How It Works: The Smart Pipeline
We use an innovative **Translation-Aware RAG Architecture** that allows us to support dozens of languages with zero cloud memory crashes.

1.  **Voice Input**: The user speaks to the AI in their native language (Hindi, Kannada, etc.).
2.  **Intent Interpretation**: **Google Gemini 1.5 Flash** interprets the spoken intent and translates it into a precise English keyword.
3.  **Semantic Search**: We use **FastEmbed** and **Qdrant** to find matching scheme data from 60+ verified chunks.
4.  **Actionable Answer**: The AI synthesizes the answer back into the user's native tongue.
5.  **Voice Feedback**: The final response is spoken back via high-quality neural voices.

---

## 🎯 Hackathon Challenge: Accessibility & Impact
SahayakSetu directly addresses **Hackblr Challenge #3**. Most portals are text-heavy barriers; we turned them into a empathetic conversation.

### 1. Breaking the Linguistic Divide
- **Innovation**: By using "Translation-Aware" logic, we use lightweight (70MB) models to handle heavy regional language queries, preventing server crashes.
- **Coverage**: English, Hindi, Kannada, Tamil, Telugu, Bengali, Hinglish.

### 2. Zero-Cost RAG Scaling
- **Innovation**: Utilizing **FastEmbed** for local vector generation and **Google Gemini 1.5 Flash (Free Tier)** eliminated all external API costs.

### 3. Actionable Welfare Access
- We provide a clear **Summary ➔ Eligibility ➔ Action Steps** to ensure welfare reaches the last mile.

---

## 🛠️ Technology Stack
| Layer | Technology |
| :--- | :--- |
| **Voice / STT / TTS** | [Vapi.ai](https://vapi.ai) with Deepgram & Azure Neural Voices |
| **Intelligence** | **Google Gemini 1.5 Flash** (Zero-cost, high-performance) |
| **Vector Database** | [Qdrant Cloud](https://qdrant.tech/) |
| **Embedding Engine** | **FastEmbed** (BAAI/bge-small-en-v1.5) |
| **Backend** | FastAPI (Python 3.12) |
| **Frontend** | Vanilla JS + Glassmorphism CSS |

---

## 🚀 Easy Setup & Development

1. **Clone & Install**
   ```bash
   git clone https://github.com/bansalbhunesh/SahayakSetu.git
   pip install -r backend/requirements.txt
   ```

2. **Environment Setup** (Create a `.env` in `backend/`)
   - `GEMINI_API_KEY`
   - `QDRANT_URL` & `QDRANT_API_KEY`
   - `VAPI_API_KEY`

3. **Ingest & Launch**
   ```bash
   python scripts/ingest.py
   python -m uvicorn backend.main:app --reload
   ```

---
*Built for Hackblr 2026 — Supporting Bangalore's All-India Hackathon Spirit.* 🇮🇳🏆
