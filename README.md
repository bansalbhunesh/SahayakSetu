# SahayakSetu (सहायक सेतु) 🚀🇮🇳
### **Empowering Every Indian: A Zero-Cost, Multilingual Voice AI Bridge for Government Welfare.**

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://sahayak-setu.vercel.app)
[![Challenge](https://img.shields.io/badge/Challenge-Accessibility_%26_Societal_Impact-blue)](#)
[![Stack](https://img.shields.io/badge/Stack-Voice--First_Dual--Brain_AI-orange)](#)
[![Status](https://img.shields.io/badge/Status-Production--Ready-success)](#)

---

## 🏗️ Problem Statement: The "Inclusion Gap" (Solution for PS #2026)
**The Problem:** India has 1,200+ government schemes, yet millions remain unaware of their eligibility because documentation is overwhelmingly stored in complex English PDFs. For the last-mile citizen—especially the rural, elderly, or non-literate—this creates a **Digital & Linguistic Barrier** to their basic rights.

**The Solution (SahayakSetu):** We have built a production-grade, voice-first AI "bridge" that allows citizens to speak their questions in their **mother tongue** and receive actionable, verified advice instantly—eliminating the need for English literacy or digital expertise.

---

## 🔗 🌐 Live Ecosystem
*   **Live Application**: [https://sahayak-setu.vercel.app](https://sahayak-setu.vercel.app)
*   **Intelligence Orchestrator**: [https://sahayaksetu-backend-3kxl.onrender.com](https://sahayaksetu-backend-3kxl.onrender.com)
*   **Infrastructure**: Qdrant Cloud (Vector Store) | Render (Orchestrator) | Vercel (UI)

---

## 🛠️ The 5-Step Pipeline: What & How It Happens

### **Step 1: Regional Voice Capture (STT)** 🎤
*   **What**: The system captures the user's voice in 6 core Indian languages.
*   **How**: Using **Vapi.ai** integrated with **Azure Neural STT**, we achieve sub-second latency for regional dialects, supporting real-time "interim results" for a responsive UI.

### **Step 2: Semantic Intelligence (Vector Search)** 🔍
*   **What**: We don't just search keywords; we search **meaning**.
*   **How**: User queries are converted into 384-dimensional dense vectors using **FastEmbed**. These are searched against a **Qdrant Vector Database** containing 70+ verified government scheme chunks with a strict **0.2 similarity threshold** to ensure precise grounding.

### **Step 3: Intelligence Fusion (The Dual-Brain)** 🧠⚡
*   **What**: Heavyweight reasoning with zero downtime.
*   **How**: We use **Gemini 2.0 Flash** as our primary free-tier brain. If rate limits are hit, our custom orchestrator instantly falls back to **Groq (Llama 3.3 70B)**. This "Dual-Brain" architecture ensures SahayakSetu is always online and free.

### **Step 4: Linguistic Mirroring (Cultural Adaptation)** 🔄🇮🇳
*   **What**: The AI responds in the specific language used by the user.
*   **How**: A custom-prompted **Master Orchestrator** detects the query script and mirrors the response. If the query is English, the answer stays English. If it's Hindi/Kannada, the answer is fluently translated with empathy.

### **Step 5: Script-Aware Neural Voice (TTS)** 🔊
*   **What**: High-fidelity regional speech response.
*   **How**: Our frontend uses a **RegEx Script Detector** to analyze the AI's response text. It then forces the browser to load the matching regional neural voice, ensuring that "3000 Rs" in a Hindi paragraph is read with a perfect Hindi accent.

---

## 🎯 Societal Impact & Scalability
- **Zero Hallucination Transparency**: Every response features a **Semantic Confidence Tag (Match %)**, proving the advice is grounded in verified government data.
- **Last-Mile Accessibility**: No typing required. No English required. Just tap and talk.
- **Sustainable Scaling**: Built entirely on **Free Tier infrastructure** (Google AI Studio, Groq Free, Qdrant Free), making it viable for 100% free deployment to millions of citizens.

---

## 🚀 Setup & Installation

1. **Clone & Explore**
   ```bash
   git clone https://github.com/bansalbhunesh/SahayakSetu.git
   cd SahayakSetu
   ```

2. **Configure Environment** (`.env`)
   ```env
   GEMINI_API_KEY=your_key
   GROQ_API_KEY=your_key
   QDRANT_URL=your_cluster_url
   QDRANT_API_KEY=your_key
   ```

3. **Install & Launch**
   ```bash
   pip install -r backend/requirements.txt
   python -m uvicorn backend.main:app --host 0.0.0.0
   ```

---
*Built for Hackblr 2026 — Bridging the gap for a Digital, Inclusive India.* 🇮🇳🏆
