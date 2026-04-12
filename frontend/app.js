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

        // Randomize color between saffron and green
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
let lastScroll = 0;
window.addEventListener("scroll", () => {
    const header = document.getElementById("header");
    const scrollY = window.scrollY;

    if (scrollY > 50) {
        header.style.borderBottomColor = "rgba(255,255,255,0.1)";
    } else {
        header.style.borderBottomColor = "rgba(255,255,255,0.06)";
    }

    lastScroll = scrollY;
});

// ── Vapi Voice Integration ─────────────────────────
function initVapi() {
    if (VAPI_PUBLIC_KEY === "YOUR_VAPI_PUBLIC_KEY") {
        console.warn("⚠️ Vapi not configured — voice will use text fallback");
        return;
    }

    try {
        if (window.Vapi) {
            vapiInstance = new window.Vapi(VAPI_PUBLIC_KEY);
            setupVapiEvents();
            updateStatus("Ready", "green");
            console.log("✅ Vapi initialized");
        } else {
            console.warn("Vapi SDK not loaded yet, retrying...");
            setTimeout(initVapi, 1000);
        }
    } catch (err) {
        console.error("Vapi init error:", err);
        updateStatus("Voice unavailable", "yellow");
    }
}

function setupVapiEvents() {
    if (!vapiInstance) return;

    vapiInstance.on("call-start", () => {
        console.log("📞 Call started");
        isCallActive = true;
        updateVoiceUI(true);
        updateStatus("Listening...", "green");
        addMessage("system", "🎤 Voice call started — speak in any Indian language");
    });

    vapiInstance.on("call-end", () => {
        console.log("📞 Call ended");
        isCallActive = false;
        updateVoiceUI(false);
        updateStatus("Ready", "green");
        addMessage("system", "📞 Call ended");
    });

    vapiInstance.on("speech-start", () => {
        updateStatus("Speaking...", "orange");
    });

    vapiInstance.on("speech-end", () => {
        updateStatus("Processing...", "blue");
    });

    vapiInstance.on("message", (msg) => {
        console.log("[VAPI MSG]", msg);

        if (msg.type === "transcript" && msg.transcriptType === "final") {
            if (msg.role === "user") {
                addMessage("user", msg.transcript);
            } else if (msg.role === "assistant") {
                addMessage("assistant", msg.transcript);
            }
        }
    });

    vapiInstance.on("error", (err) => {
        console.error("Vapi error:", err);
        updateStatus("Error", "red");
        addMessage("system", "⚠️ Voice error — try again or type your question in any language below");
    });
}

// ── Voice Toggle ───────────────────────────────────
function toggleVoice() {
    if (isCallActive) {
        stopVoice();
    } else {
        startVoice();
    }
}

function startVoice() {
    if (vapiInstance && VAPI_ASSISTANT_ID !== "YOUR_VAPI_ASSISTANT_ID") {
        // Use Vapi for voice
        vapiInstance.start(VAPI_ASSISTANT_ID);
    } else {
        // Fallback: use browser speech recognition
        startBrowserSpeech();
    }
}

function stopVoice() {
    if (vapiInstance && isCallActive) {
        vapiInstance.stop();
    }
    isCallActive = false;
    updateVoiceUI(false);
    updateStatus("Ready", "green");
}

// ── Browser Speech Fallback ────────────────────────
function startBrowserSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        addMessage("system", "⚠️ Speech recognition not supported in this browser. Please type your question below.");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";     // Support for English-speaking Indian users
    recognition.continuous = false;
    recognition.interimResults = false;

    isCallActive = true;
    updateVoiceUI(true);
    updateStatus("Listening...", "green");

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        addMessage("user", transcript);
        sendQuery(transcript);
    };

    recognition.onerror = (event) => {
        console.error("Speech error:", event.error);
        updateStatus("Ready", "green");
        isCallActive = false;
        updateVoiceUI(false);

        if (event.error === "no-speech") {
            addMessage("system", "🤔 Couldn't hear you — please try again or type your question");
        }
    };

    recognition.onend = () => {
        isCallActive = false;
        updateVoiceUI(false);
        updateStatus("Ready", "green");
    };

    recognition.start();
    addMessage("system", "🎤 Listening... (speak in any language)");
}

// ── Text Input ─────────────────────────────────────
function sendText() {
    const input = document.getElementById("textInput");
    const query = input.value.trim();

    if (!query) return;

    addMessage("user", query);
    input.value = "";
    sendQuery(query);
}

// Handle Enter key
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("textInput");
    if (input) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                sendText();
            }
        });
    }

    initParticles();
    initVapi();
});

// ── API Call ───────────────────────────────────────
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

        // Show answer
        let answerHtml = data.answer;
        if (data.sources && data.sources.length > 0) {
            const topSource = data.sources[0];
            answerHtml += `<span class="source-tag">📚 ${topSource.scheme} (${(topSource.score * 100).toFixed(0)}% match)</span>`;
        }

        addMessage("assistant", answerHtml, true);

        // Speak the answer (TTS fallback)
        if (!vapiInstance || !isCallActive) {
            speakText(data.answer);
        }

        updateStatus("Ready", "green");
    } catch (err) {
        removeTyping();
        console.error("API error:", err);
        addMessage("assistant", "Sorry, there was an error connecting to the server. Please make sure the backend is running.");
        updateStatus("Error", "red");
        setTimeout(() => updateStatus("Ready", "green"), 3000);
    }
}

// ── Ask About (Scheme Cards) ───────────────────────
function askAbout(query) {
    addMessage("user", query);
    sendQuery(query);

    // Scroll to conversation
    document.getElementById("conversation").scrollIntoView({
        behavior: "smooth",
        block: "center",
    });
}

// ── TTS Fallback ───────────────────────────────────
function speakText(text) {
    if ("speechSynthesis" in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);

        // Try to find a Hindi voice
        const voices = window.speechSynthesis.getVoices();
        const hindiVoice = voices.find((v) =>
            v.lang.startsWith("hi") || v.name.toLowerCase().includes("hindi")
        );

        if (hindiVoice) {
            utterance.voice = hindiVoice;
        }

        utterance.rate = 0.95;
        utterance.pitch = 1;
        window.speechSynthesis.speak(utterance);
    }
}

// ── UI Helpers ─────────────────────────────────────
function addMessage(type, content, isHtml = false) {
    const conversation = document.getElementById("conversation");
    const msg = document.createElement("div");
    msg.className = `message ${type}`;

    if (isHtml) {
        msg.innerHTML = content;
    } else {
        msg.textContent = content;
    }

    conversation.appendChild(msg);

    // Scroll to bottom
    msg.scrollIntoView({ behavior: "smooth", block: "end" });
}

function showTyping() {
    const conversation = document.getElementById("conversation");
    const typing = document.createElement("div");
    typing.className = "message assistant typing-indicator";
    typing.id = "typing";
    typing.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    conversation.appendChild(typing);
    typing.scrollIntoView({ behavior: "smooth", block: "end" });
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
        label.textContent = "Tap to Stop";
    } else {
        btn.classList.remove("active");
        micIcon.classList.remove("hidden");
        stopIcon.classList.add("hidden");
        label.textContent = "Tap to Talk";
    }
}

function updateStatus(text, color) {
    const statusText = document.querySelector(".status-text");
    const statusDot = document.querySelector(".status-dot");

    if (statusText) statusText.textContent = text;

    if (statusDot) {
        const colorMap = {
            green: "#1DB954",
            orange: "#FF6B35",
            red: "#FF4444",
            blue: "#0066CC",
            yellow: "#FFD93D",
        };
        statusDot.style.background = colorMap[color] || colorMap.green;
    }
}
