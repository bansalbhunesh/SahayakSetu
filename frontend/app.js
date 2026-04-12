/* ══════════════════════════════════════════════════
   SahayakSetu — Frontend Application Logic
   Handles Vapi voice integration + text fallback
   Advanced Script-Aware TTS Restoration (Audit v3)
   ══════════════════════════════════════════════════ */

// ── Configuration ──────────────────────────────────
const VAPI_PUBLIC_KEY = "c0fcebfd-1570-4dfa-8b47-9280bfbaaaf8";
const VAPI_ASSISTANT_ID = "bd9bb2ff-9b1d-4f6a-86a2-11dfda391550";
const BACKEND_URL = "https://sahayaksetu-backend-3kxl.onrender.com";

// ── State ──────────────────────────────────────────
let vapiInstance = null;
let isCallActive = false;
let currentLanguage = "hi-IN"; 
let userId = "web-" + Math.random().toString(36).substr(2, 9);

// ── Init Particles ─────────────────────────────────
function initParticles() {
    const container = document.getElementById("particles");
    if (!container) return;
    for (let i = 0; i < 20; i++) {
        const p = document.createElement("div");
        p.className = "particle";
        p.style.left = Math.random() * 100 + "%";
        p.style.top = Math.random() * 100 + "%";
        p.style.animationDelay = Math.random() * 5 + "s";
        p.style.background = ["#FF6B35", "#138808", "#FFD93D", "#0066CC"][Math.floor(Math.random() * 4)];
        container.appendChild(p);
    }
}

// ── Vapi Voice Integration ─────────────────────────
function initVapi() {
    if (VAPI_PUBLIC_KEY === "YOUR_VAPI_PUBLIC_KEY") return;
    try {
        if (window.Vapi) {
            vapiInstance = new window.Vapi(VAPI_PUBLIC_KEY);
            setupVapiEvents();
            updateStatus("Ready", "green");
        } else setTimeout(initVapi, 500);
    } catch (err) { updateStatus("Voice Error", "red"); }
}

function setupVapiEvents() {
    if (!vapiInstance) return;
    vapiInstance.on("call-start", () => {
        isCallActive = true;
        updateVoiceUI(true);
        updateStatus("Listening...", "green");
    });
    vapiInstance.on("call-end", () => {
        isCallActive = false;
        updateVoiceUI(false);
        updateStatus("Ready", "green");
    });
    vapiInstance.on("message", (msg) => {
        if (msg.type === "transcript" && msg.transcriptType === "final") {
            addMessage(msg.role === "user" ? "user" : "assistant", msg.transcript);
        }
    });
}

function toggleVoice() {
    if (isCallActive) vapiInstance.stop();
    else vapiInstance.start(VAPI_ASSISTANT_ID);
}

function setLanguage(lang, el) {
    currentLanguage = lang;
    document.querySelectorAll(".lang-pill").forEach(p => p.classList.remove("active"));
    el.classList.add("active");
    const hint = document.getElementById("voiceHint");
    const names = {"hi-IN":"हिन्दी", "kn-IN":"ಕನ್ನಡ", "ta-IN":"தமிழ்", "te-IN":"తెలుగు", "bn-IN":"বাংলা", "en-IN":"English"};
    if (hint) hint.textContent = `Listening for: ${names[lang]}`;
}

async function sendQuery(query) {
    updateStatus("Thinking...", "orange");
    showTyping();
    try {
        const resp = await fetch(`${BACKEND_URL}/api/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query, user_id: userId }),
        });
        removeTyping();
        const data = await resp.json();
        addMessage("assistant", data.answer);
        
        if (data.sources && data.sources.length > 0) {
            const top = data.sources[0];
            const tag = document.createElement("span");
            tag.className = "source-tag";
            tag.textContent = `📚 ${top.scheme} (${(top.score * 100).toFixed(0)}% match)`;
            const lastMsg = document.querySelector("#conversation .message.assistant:last-child");
            if (lastMsg) lastMsg.appendChild(tag);
        }

        if (!vapiInstance || !isCallActive) speakText(data.answer);
        updateStatus("Ready", "green");
    } catch (err) {
        removeTyping();
        updateStatus("Error", "red");
    }
}

// ── Advanced Script-Aware TTS Restoration ──────────
function speakText(text) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Audit v3: High-Precision Unicode Script Detection
    const scripts = {
        "hi-IN": /[\u0900-\u097F]/, // Devanagari (Hindi/Marathi)
        "kn-IN": /[\u0C80-\u0CFF]/, // Kannada
        "te-IN": /[\u0C00-\u0C7F]/, // Telugu
        "ta-IN": /[\u0B80-\u0BFF]/, // Tamil
        "bn-IN": /[\u0980-\u09FF]/  // Bengali
    };

    let detectedLang = "en-IN"; // Default
    for (const [lang, regex] of Object.entries(scripts)) {
        if (regex.test(text)) {
            detectedLang = lang;
            break;
        }
    }
    
    // Mirror the detected script for the neural engine
    utterance.lang = (detectedLang === "en-IN") ? currentLanguage : detectedLang;
    
    // Browser Voice Priority (Azure/Google Neural)
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang === utterance.lang && (v.name.includes("Neural") || v.name.includes("Google")));
    if (preferredVoice) utterance.voice = preferredVoice;

    window.speechSynthesis.speak(utterance);
}

function addMessage(type, content) {
    const chat = document.getElementById("conversation");
    const msg = document.createElement("div");
    msg.className = `message ${type}`;
    msg.textContent = content; // XSS Secure
    chat.appendChild(msg);
    msg.scrollIntoView({ behavior: "smooth", block: "end" });
}

function sendText() {
    const input = document.getElementById("textInput");
    const q = input.value.trim();
    if (!q) return;
    addMessage("user", q);
    input.value = "";
    sendQuery(q);
}

function showTyping() {
    const chat = document.getElementById("conversation");
    const t = document.createElement("div");
    t.className = "message assistant typing-indicator";
    t.id = "typing";
    t.innerHTML = `<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>`;
    chat.appendChild(t);
}

function removeTyping() {
    const t = document.getElementById("typing");
    if (t) t.remove();
}

function updateVoiceUI(active) {
    const btn = document.getElementById("voiceBtn");
    const mic = document.getElementById("micIcon");
    const stop = document.getElementById("stopIcon");
    const label = document.getElementById("voiceLabel");
    if (active) {
        btn.classList.add("active");
        mic.classList.add("hidden");
        stop.classList.remove("hidden");
        label.textContent = "Stop";
    } else {
        btn.classList.remove("active");
        mic.classList.remove("hidden");
        stop.classList.add("hidden");
        label.textContent = "Talk";
    }
}

function updateStatus(text, color) {
    const st = document.querySelector(".status-text");
    const d = document.querySelector(".status-dot");
    if (st) st.textContent = text;
    if (d) d.style.background = {green: "#1DB954", orange: "#FF6B35", red: "#FF4444"}[color] || "#1DB954";
}

document.addEventListener("DOMContentLoaded", () => {
    initParticles();
    initVapi();
    const input = document.getElementById("textInput");
    if (input) input.addEventListener("keydown", (e) => { if (e.key === "Enter") sendText(); });
});

// Refresh voices on load
window.speechSynthesis.onvoiceschanged = () => { window.speechSynthesis.getVoices(); };
