# SahayakSetu (सहायक सेतु) 🚀🇮🇳
### **The Universal Bridge to Government Welfare — Powered by Pan-India Voice AI.**

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://sahayak-setu.vercel.app)
[![Challenge](https://img.shields.io/badge/Challenge-Accessibility_%26_Societal_Impact-blue)](#)
[![Stack](https://img.shields.io/badge/Stack-Voice--First_Dual--Brain_AI-orange)](#)
[![Status](https://img.shields.io/badge/Status-Production--Ready-success)](#)

**SahayakSetu** is a production-grade, zero-latency, multilingual voice AI agent. It acts as a linguistic and digital bridge, enabling every Indian citizen to access complex government scheme data through natural conversations in their **mother tongue**.

---

## 🔗 🌐 Live Ecosystem
*   **Live Application**: [https://sahayak-setu.vercel.app](https://sahayak-setu.vercel.app)
*   **Intelligence Orchestrator**: [https://sahayaksetu-backend-3kxl.onrender.com](https://sahayaksetu-backend-3kxl.onrender.com)
*   **Vector Infrastructure**: Qdrant Cloud Cluster

---

## ✨ Key Innovation: The "Pan-India" Engine
We have engineered SahayakSetu to be more than just a chatbot. It is a **Linguistic Mirror**:

- **Universal Language Mirroring**: Automatically detects and responds in the exact script and language used by the user (**Hindi, Kannada, Tamil, Telugu, Bengali, or English**).
- **Free Tier Fusion (Dual-Brain)**: Utilizing **Gemini 2.0 Flash** as the primary reasoning engine, with an ultra-fast **Groq (Llama 3.3 70B)** fallback to ensure 100% uptime and zero cost.
- **Script-Aware Neural TTS**: A custom voice engine that detects regional scripts and forces the correct neural accent, preventing "mechanical voice" skips.
- **Translation-Aware RAG**: Interrogates English-only scheme documentation and interprets it with empathy and local nuance.

---

## 🛠️ Technology Stack
| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Primary Intelligence** | **Google Gemini 2.0 Flash** | Flagship Multilingual Reasoning (Free Tier) |
| **Fallback Intelligence**| **Groq (Llama 3.3 70B)** | Lightning-Fast Fallback (300+ tokens/sec) |
| **Speech Orchestration** | [Vapi.ai](https://vapi.ai) | Zero-Latency Voice Streaming |
| **Vector DB** | [Qdrant Cloud](https://qdrant.tech/) | Production-Scale Knowledge Retrieval |
| **Embedding Logic** | **FastEmbed** | Lightweight, Memory-Safe Local Encoding |
| **Regional TTS** | Browser Web-Speech | Script-Aware Local Voice Synthesis |

---

## 🚀 Easy Setup & Deployment

1. **Clone & Explore**
   ```bash
   git clone https://github.com/bansalbhunesh/SahayakSetu.git
   cd SahayakSetu
   ```

2. **Configure Environment** (Create a `.env` file)
   ```env
   GEMINI_API_KEY=your_key
   GROQ_API_KEY=your_key # For Fallback Resilience
   QDRANT_URL=your_cluster_url
   QDRANT_API_KEY=your_key
   ```

3. **Install & Run**
   ```bash
   pip install -r backend/requirements.txt
   python -m uvicorn backend.main:app --host 0.0.0.0
   ```

---

## 🎯 Impact Goal
SahayakSetu aims to solve the **"Inaccessible Documentation"** crisis. By converting thousand-page English PDF guidelines into 15-second regional voice summaries, we empower the last-mile citizen to claim their rights.

---
*Built for Hackblr 2026 — Demonstrating Bangalore's spirit of high-impact technical innovation.* 🇮🇳🏆
