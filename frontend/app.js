/* ══════════════════════════════════════════════════
   SahayakSetu — Frontend Application Logic
   Handles Vapi voice integration + text fallback
   ══════════════════════════════════════════════════ */

// ── Configuration ──────────────────────────────────
const VAPI_PUBLIC_KEY = "c0fcebfd-1570-4dfa-8b47-9280bfbaaaf8";
const VAPI_ASSISTANT_ID = "bd9bb2ff-9b1d-4f6a-86a2-11dfda391550";
const BACKEND_URL = "https://sahayaksetu-backend-3kxl.onrender.com";

// ── State ──────────────────────────────────────────
let vapiInstance = null;
let isCallActive = false;
let currentLanguage = "hi-IN"; // Default to Hindi
let userId = "web-" + Math.random().toString(36).substr(2, 9);

// ── Init Particles ─────────────────────────────────
function initParticles() {
    const container = document.getElementById("particles");
    if (!container) return;

    for (let i = 0; i < 20; i++) {
        const particle = document.createElement("div");
        particle.className = "particle";
        particle.style.left = Math.random() * 100 + "%";
        particle.style.top = Math.random() * 100 + "%";
        particle.style.animationDelay = Math.random() * 5 + "s";
        particle.style.animationDuration = (5 + Math.random() * 8) + "s";

        const colors = ["#FF6B35", "#138808", "#FFD93D", "#0066CC"];
        particle.style.background = colors[Math.floor(Math.random() * colors.length)];
        container.appendChild(particle);
    }
}

// ── Smooth Scroll ──────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute("href")).scrollIntoView({
            behavior: "smooth",
        });
    });
});

// ── Header Scroll Effect ───────────────────────────
window.addEventListener("scroll", () => {
    const header = document.getElementById("header");
    const scrollY = window.scrollY;

    if (scrollY > 50) {
        header.style.borderBottomColor = "rgba(255,255,255,0.1)";
    } else {
        header.style.borderBottomColor = "rgba(255,255,255,0.06)";
    }
});

// ── Vapi Voice Integration ─────────────────────────
function initVapi() {
    if (VAPI_PUBLIC_KEY === "YOUR_VAPI_PUBLIC_KEY") return;

    try {
        if (window.Vapi) {
            vapiInstance = new window.Vapi(VAPI_PUBLIC_KEY);
            setupVapiEvents();
            updateStatus("Ready", "green");
        } else {
            setTimeout(initVapi, 1000);
        }
    } catch (err) {
        updateStatus("Voice unavailable", "yellow");
    }
}

function setupVapiEvents() {
    if (!vapiInstance) return;

    vapiInstance.on("call-start", () => {
        isCallActive = true;
        updateVoiceUI(true);
        updateStatus("Listening...", "green");
        addMessage("system", "🎤 Voice call started — speak in any Indian language");
    });

    vapiInstance.on("call-end", () => {
        isCallActive = false;
        updateVoiceUI(false);
        updateStatus("Ready", "green");
        addMessage("system", "📞 Call ended");
    });

    vapiInstance.on("message", (msg) => {
        if (msg.type === "transcript" && msg.transcriptType === "final") {
            if (msg.role === "user") {
                addMessage("user", msg.transcript);
            } else if (msg.role === "assistant") {
                addMessage("assistant", msg.transcript);
            }
        }
    });

    vapiInstance.on("error", (err) => {
        updateStatus("Error", "red");
        addMessage("system", "⚠️ Voice error — try again or type your question below");
    });
}

function toggleVoice() {
    if (isCallActive) stopVoice();
    else startVoice();
}

function startVoice() {
    if (vapiInstance && VAPI_ASSISTANT_ID !== "YOUR_VAPI_ASSISTANT_ID") vapiInstance.start(VAPI_ASSISTANT_ID);
    else startBrowserSpeech();
}

function stopVoice() {
    if (vapiInstance && isCallActive) vapiInstance.stop();
    isCallActive = false;
    updateVoiceUI(false);
    updateStatus("Ready", "green");
}

function setLanguage(lang, el) {
    currentLanguage = lang;
    document.querySelectorAll(".lang-pill").forEach(p => p.classList.remove("active"));
    el.classList.add("active");
    
    const hint = document.getElementById("voiceHint");
    if (hint) {
        const langNames = {"hi-IN":"हिन्दी", "kn-IN":"ಕನ್ನಡ", "ta-IN":"தமிழ்", "te-IN":"తెలుగు", "bn-IN":"বাংলা", "en-IN":"English"};
        hint.textContent = `Listening for: ${langNames[lang]}`;
    }
}

function startBrowserSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        addMessage("system", "⚠️ Speech recognition not supported.");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = currentLanguage;
    recognition.onresult = (event) => {
        const finalTranscript = event.results[event.resultIndex][0].transcript;
        if (event.results[event.resultIndex].isFinal) {
            addMessage("user", finalTranscript);
            sendQuery(finalTranscript);
        }
    };
    recognition.start();
}

function sendText() {
    const input = document.getElementById("textInput");
    const query = input.value.trim();
    if (!query) return;
    addMessage("user", query);
    input.value = "";
    sendQuery(query);
}

document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("textInput");
    if (input) input.addEventListener("keydown", (e) => { if (e.key === "Enter") sendText(); });
    initParticles();
    initVapi();
});

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
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();

        // Show answer (Audit v3 fix: XSS safe construction)
        addMessage("assistant", data.answer);
        
        if (data.sources && data.sources.length > 0) {
            const topSource = data.sources[0];
            const sourceTag = document.createElement("span");
            sourceTag.className = "source-tag";
            sourceTag.textContent = `📚 ${topSource.scheme} (${(topSource.score * 100).toFixed(0)}% match)`;
            const lastMsg = document.querySelector("#conversation .message.assistant:last-child");
            if (lastMsg) lastMsg.appendChild(sourceTag);
        }

        if (!vapiInstance || !isCallActive) speakText(data.answer);
        updateStatus("Ready", "green");
    } catch (err) {
        removeTyping();
        updateStatus("Error", "red");
    }
}

function askAbout(query) {
    addMessage("user", query);
    sendQuery(query);
}

function speakText(text) {
    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        const containsHindi = /[\u0900-\u097F]/.test(text);
        utterance.lang = containsHindi ? "hi-IN" : currentLanguage;
        window.speechSynthesis.speak(utterance);
    }
}

function addMessage(type, content) {
    const conversation = document.getElementById("conversation");
    const msg = document.createElement("div");
    msg.className = `message ${type}`;
    msg.textContent = content; // Secure XSS Fix
    conversation.appendChild(msg);
    msg.scrollIntoView({ behavior: "smooth", block: "end" });
}

function showTyping() {
    const conversation = document.getElementById("conversation");
    const typing = document.createElement("div");
    typing.className = "message assistant typing-indicator";
    typing.id = "typing";
    typing.innerHTML = `<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>`;
    conversation.appendChild(typing);
}

function removeTyping() {
    const typing = document.getElementById("typing");
    if (typing) typing.remove();
}

function updateVoiceUI(active) {
    const btn = document.getElementById("voiceBtn");
    const micIcon = document.getElementById("micIcon");
    const stopIcon = document.getElementById("stopIcon");
    const label = document.getElementById("voiceLabel");
    if (active) {
        btn.classList.add("active");
        micIcon.classList.add("hidden");
        stopIcon.classList.remove("hidden");
        label.textContent = "Stop";
    } else {
        btn.classList.remove("active");
        micIcon.classList.remove("hidden");
        stopIcon.classList.add("hidden");
        label.textContent = "Talk";
    }
}

function updateStatus(text, color) {
    const statusText = document.querySelector(".status-text");
    const statusDot = document.querySelector(".status-dot");
    if (statusText) statusText.textContent = text;
    if (statusDot) {
        const colorMap = {green: "#1DB954", orange: "#FF6B35", red: "#FF4444", blue: "#0066CC", yellow: "#FFD93D"};
        statusDot.style.background = colorMap[color] || colorMap.green;
    }
}
