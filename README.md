# SahayakSetu (सहायक सेतु) 🚀🇮🇳
### **Empowering Every Indian: A Zero-Cost, Multilingual Voice AI Bridge for Government Welfare.**

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://sahayak-setu.vercel.app)
[![Challenge](https://img.shields.io/badge/Challenge-Accessibility_%26_Societal_Impact-blue)](#)

---

## 🏗️ The Mission: Bridging the "Inclusion Gap"
**Track:** *Voice AI Agent for Accessibility & Societal Impact*

**The Problem:** India has 1,200+ government schemes, yet documentation is stored in complex English PDFs. SahayakSetu allows citizens to speak in their **mother tongue** and receive actionable advice instantly.

## 🛠️ The 5-Step Pipeline

### **Step 2: Semantic Intelligence** 🔍
User queries are converted into 384-dimensional dense vectors using **FastEmbed** and searched against **Qdrant Vector DB** containing **35+ high-precision code-verified chunks** with a **0.2 threshold**.

### **Step 3: Intelligence Fusion & Memory** 🧠⚡
We use **Gemini 2.0 Flash** as our primary brain. Our system maintains an in-memory **Session Store** that preserves context across exchanges, allowing for natural follow-up questions.

### **Step 4: Linguistic Mirroring** 🔄🇮🇳
A custom-prompted **Master Orchestrator** detects the query script and mirrors the response in the user's exact language and script (Hindi/Kannada/Bengali/etc.).

### **Step 5: Script-Aware Neural Voice (TTS)** 🔊
Our frontend uses a **RegEx Script Detector** to force the matching regional neural voice (e.g., Azure Swara for Hindi), ensuring culturally accurate speech.

---

## 🚀 Setup & Installation

1. **Clone**
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
   BACKEND_URL=https://your-backend.onrender.com
   ```

3. **Ingest & Launch**
   ```bash
   pip install -r backend/requirements.txt
   python scripts/ingest.py
   python -m uvicorn backend.main:app --host 0.0.0.0
   ```
