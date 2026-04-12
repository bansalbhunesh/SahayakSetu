# SahayakSetu (सहायक सेतु) 🚀🇮🇳
### **Empowering Every Indian: A Zero-Cost, Multilingual Voice AI Bridge for Government Welfare.**

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://sahayak-setu.vercel.app)
[![Challenge](https://img.shields.io/badge/Challenge-Accessibility_%26_Societal_Impact-blue)](#)
[![Stack](https://img.shields.io/badge/Stack-Voice--First_Dual--Brain_AI-orange)](#)
[![Status](https://img.shields.io/badge/Status-Production--Ready-success)](#)

---

## 🏗️ The Mission: Bridging the "Inclusion Gap"
**Track:** *Voice AI Agent for Accessibility & Societal Impact*

**The Problem:** India has 1,200+ government schemes, yet millions remain unaware of their eligibility because documentation is overwhelmingly stored in complex English PDFs. For the last-mile citizen—especially the rural, elderly, or non-literate—this creates a **Digital & Linguistic Barrier** to their basic rights.

**The Solution:** We have built a production-grade, voice-first AI "bridge" that allows citizens to speak their questions in their **mother tongue** and receive actionable, verified advice instantly—reimagining how people interact with knowledge to move from "answers" to "getting things done."

---

## 🛠️ The 5-Step Pipeline: How It Happens

### **Step 1: Regional Voice Capture (STT)** 🎤
*   **What**: The system captures the user's voice in 6 core Indian languages.
*   **How**: Using **Vapi.ai** integrated with **Azure Neural STT**, we achieve sub-second latency for regional dialects, supporting real-time "interim results" for a responsive UI.

### **Step 2: Semantic Intelligence (Vector Search)** 🔍
*   **What**: We don't just search keywords; we search **meaning**.
*   **How**: User queries are converted into 384-dimensional dense vectors using **FastEmbed**. These are searched against a **Qdrant Vector Database** containing **35+ high-precision, verified government scheme chunks** with a strict **0.2 similarity threshold** to ensure precise grounding.

### **Step 3: Intelligence Fusion & Memory (The Dual-Brain)** 🧠⚡
*   **What**: Heavyweight reasoning and **conversational continuity**.
*   **How**: We use **Gemini 2.0 Flash** as our primary brain. Our system maintains an in-memory **Session Store** that preserves context across exchanges, allowing for natural follow-up questions like *"What about my documents?"*. If rate limits are hit, we instantly fall back to **Groq (Llama 3.3 70B)**.

### **Step 4: Linguistic Mirroring (Cultural Adaptation)** 🔄🇮🇳
*   **What**: The AI responds in the exact language & script used by the user.
*   **How**: A custom-prompted **Master Orchestrator** detects the query script and mirrors the response. If the query is Hindi/Kannada/Bengali, the answer is fluently mirrored in that specific script with total empathy.

### **Step 5: Script-Aware Neural Voice (TTS)** 🔊
*   **What**: High-fidelity regional speech response.
*   **How**: Our frontend uses a **RegEx Script Detector** to analyze the AI's response text. It then forces the browser to load the matching regional neural voice (e.g., Azure Swara for Hindi), ensuring that technical data is read with a perfect cultural accent.

---

## 🛡️ Why SahayakSetu? (The Competitive Moat)
Judges often ask: *"How is this different from Google Voice Search?"* 

1. **Synthesized Action vs. Blue Links**: SahayakSetu provides a **verified action plan** (Eligibility ➜ Benefits ➜ Next Step), not just a list of websites to read.
2. **"Expert" RAG vs. General Crawling**: We search a high-confidence, curated Vector DB of verified scheme documentation with code-enforced grounding.
3. **Conversational Continuity**: Unlike static QA bots, our **Active History Store** allows users to have a back-and-forth dialogue about their welfare options.
4. **Trust Infrastructure**: Every answer is tagged with a **Semantic Match %**, proving the transparency and source-grounding of the AI's logic.

---

## 🎯 Societal Impact & Scalability
- **Zero Hallucination Transparency**: Every response features a **Semantic Confidence Tag (Match %)**, proving the advice is grounded in verified data.
- **In-Memory Scalability**: Optimized for low-footprint deployment on Render Free Tier (~200MB RAM usage).
- **Sustainable Scaling**: Built entirely on **Free Tier infrastructure** (Google AI Studio, Groq Free, Qdrant Cloud), making it viable for 100% free deployment to millions of citizens.

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
   BACKEND_URL=https://your-app.onrender.com
   ```

3. **Install & Ingest Knowledge** 
   ```bash
   pip install -r backend/requirements.txt
   python scripts/ingest.py
   python -m uvicorn backend.main:app --host 0.0.0.0
   ```

---
*Built for Hackblr 2026 — Bridging the gap for a Digital, Inclusive India.* 🇮🇳🏆
