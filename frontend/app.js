/* ══════════════════════════════════════════════════
   SahayakSetu — Frontend Application Logic
   Handles Vapi voice integration + Browser Fallback
   Audit v4 Stability Restoration
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
    } catch (err) { updateStatus("Voice unavailable", "yellow"); }
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
    /** Audit v4 Restoration: Safety null-checks and Browser Fallback */
    if (isCallActive) {
        if (vapiInstance) vapiInstance.stop();
        isCallActive = false;
        updateVoiceUI(false);
        updateStatus("Ready", "green");
    } else {
        if (vapiInstance && VAPI_ASSISTANT_ID !== "YOUR_VAPI_ASSISTANT_ID") {
            vapiInstance.start(VAPI_ASSISTANT_ID);
        } else {
            startBrowserSpeech(); // Safety net
        }
    }
}

function startBrowserSpeech() {
    /** Audit v4 Restoration: Browser speech recognition safety net */
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        addMessage("assistant", "Sorry, voice recognition is not supported in this browser.");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = currentLanguage;
    recognition.start();

    updateStatus("Listening...", "green");
    updateVoiceUI(true);
    isCallActive = true;

    recognition.onresult = (event) => {
        const query = event.results[0][0].transcript;
        addMessage("user", query);
        sendQuery(query);
        isCallActive = false;
        updateVoiceUI(false);
    };

    recognition.onerror = () => {
        updateStatus("Ready", "green");
        updateVoiceUI(false);
        isCallActive = false;
    };
}

function askAbout(query) {
    /** Audit v4 Restoration: helper for scheme card clicks */
    addMessage("user", query);
    sendQuery(query);
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
        /** Audit v4 Restoration: Clear error visibility */
        removeTyping();
        addMessage("assistant", "Sorry, there was an error connecting to SahayakSetu. Please try again.");
        updateStatus("Error", "red");
        setTimeout(() => updateStatus("Ready", "green"), 3000);
    }
}

function speakText(text) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    const scripts = {
        "hi-IN": /[\u0900-\u097F]/, "kn-IN": /[\u0C80-\u0CFF]/,
        "te-IN": /[\u0C00-\u0C7F]/, "ta-IN": /[\u0B80-\u0BFF]/,
        "bn-IN": /[\u0980-\u09FF]/
    };

    let detectedLang = "en-IN";
    for (const [lang, regex] of Object.entries(scripts)) {
        if (regex.test(text)) { detectedLang = lang; break; }
    }
    
    utterance.lang = (detectedLang === "en-IN") ? currentLanguage : detectedLang;
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang === utterance.lang && (v.name.includes("Neural") || v.name.includes("Google")));
    if (preferredVoice) utterance.voice = preferredVoice;

    window.speechSynthesis.speak(utterance);
}

function addMessage(type, content) {
    const chat = document.getElementById("conversation");
    const msg = document.createElement("div");
    msg.className = `message ${type}`;
    msg.textContent = content; 
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
    /** Audit v4 Restoration: Support for blue (processing) and yellow (unavailable) */
    const st = document.querySelector(".status-text");
    const d = document.querySelector(".status-dot");
    if (st) st.textContent = text;
    if (d) {
        const colorMap = {green: "#1DB954", orange: "#FF6B35", red: "#FF4444", blue: "#0066CC", yellow: "#FFD93D"};
        d.style.background = colorMap[color] || colorMap.green;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initParticles();
    initVapi();
    const input = document.getElementById("textInput");
    if (input) input.addEventListener("keydown", (e) => { if (e.key === "Enter") sendText(); });
});

window.speechSynthesis.onvoiceschanged = () => { window.speechSynthesis.getVoices(); };
