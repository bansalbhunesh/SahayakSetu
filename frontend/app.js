/* SahayakSetu — frontend application logic */

const VAPI_PUBLIC_KEY = "c0fcebfd-1570-4dfa-8b47-9280bfbaaaf8";
const VAPI_ASSISTANT_ID = "bd9bb2ff-9b1d-4f6a-86a2-11dfda391550";
const BACKEND_URL =
    window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
        ? "http://localhost:8000"
        : "https://sahayaksetu-backend-3kxl.onrender.com";

const INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
];

const LANGUAGE_LABELS = {
    "hi-IN": "हिन्दी",
    "kn-IN": "ಕನ್ನಡ",
    "ta-IN": "தமிழ்",
    "te-IN": "తెలుగు",
    "bn-IN": "বাংলা",
    "en-IN": "English",
};

const LANGUAGE_FLAGS = {
    "hi-IN": "🇮🇳",
    "kn-IN": "🇮🇳",
    "ta-IN": "🇮🇳",
    "te-IN": "🇮🇳",
    "bn-IN": "🇮🇳",
    "en-IN": "🇮🇳",
};

let vapiInstance = null;
let isVoiceCallActive = false;
let selectedLanguage = "hi-IN";
const sessionUserId = "web-" + Math.random().toString(36).substring(2, 11);
const sessionSchemeNames = new Set();
let currentSheetScheme = "";

function populateStateSelect() {
    const select = document.getElementById("finderState");
    if (!select) return;
    INDIAN_STATES.forEach((name) => {
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name;
        select.appendChild(opt);
    });
    select.value = "Karnataka";
}

function setInteractionMode(mode) {
    const talkPanel = document.getElementById("talkPanel");
    const finderPanel = document.getElementById("finderPanel");
    const talkBtn = document.getElementById("modeTalkBtn");
    const finderBtn = document.getElementById("modeFinderBtn");
    if (!talkPanel || !finderPanel || !talkBtn || !finderBtn) return;

    if (mode === "finder") {
        talkPanel.classList.add("hidden");
        finderPanel.classList.remove("hidden");
        finderPanel.setAttribute("aria-hidden", "false");
        talkBtn.classList.remove("active");
        finderBtn.classList.add("active");
    } else {
        finderPanel.classList.add("hidden");
        finderPanel.setAttribute("aria-hidden", "true");
        talkPanel.classList.remove("hidden");
        finderBtn.classList.remove("active");
        talkBtn.classList.add("active");
    }
}

function handleEligibilitySubmit(event) {
    event.preventDefault();
    const state = document.getElementById("finderState")?.value || "";
    const roleInput = document.querySelector('input[name="finderRole"]:checked');
    const incomeInput = document.querySelector('input[name="finderIncome"]:checked');
    const role = roleInput?.value || "citizen";
    const income = incomeInput?.value || "unspecified";
    const query = `Show government welfare schemes for a ${role} in ${state} with annual family income ${income}. Summarise the most relevant central or state schemes and how to apply.`;
    submitQuery(query);
}

function initialiseVapiSDK() {
    if (VAPI_PUBLIC_KEY === "YOUR_VAPI_PUBLIC_KEY") return;
    try {
        if (window.Vapi) {
            vapiInstance = new window.Vapi(VAPI_PUBLIC_KEY);
            bindVapiEventHandlers();
            setStatusIndicator("Ready", "green");
        } else {
            setTimeout(initialiseVapiSDK, 500);
        }
    } catch {
        setStatusIndicator("Voice unavailable", "yellow");
    }
}

function bindVapiEventHandlers() {
    if (!vapiInstance) return;
    vapiInstance.on("call-start", () => {
        isVoiceCallActive = true;
        setVoiceButtonState(true);
        setStatusIndicator("Listening...", "green");
    });
    vapiInstance.on("call-end", () => {
        isVoiceCallActive = false;
        setVoiceButtonState(false);
        setStatusIndicator("Ready", "green");
    });
    vapiInstance.on("message", (msg) => {
        if (msg.type === "transcript" && msg.transcriptType === "final") {
            appendMessageToChat(msg.role === "user" ? "user" : "assistant", msg.transcript);
        }
    });
}

function handleVoiceToggle() {
    if (isVoiceCallActive) {
        if (vapiInstance) vapiInstance.stop();
        isVoiceCallActive = false;
        setVoiceButtonState(false);
        setStatusIndicator("Ready", "green");
    } else if (vapiInstance && VAPI_ASSISTANT_ID !== "YOUR_VAPI_ASSISTANT_ID") {
        vapiInstance.start(VAPI_ASSISTANT_ID);
    } else {
        startBrowserSpeechFallback();
    }
}

function startBrowserSpeechFallback() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        appendMessageToChat("assistant", "Sorry, voice recognition is not supported in this browser.", {
            variant: "error",
        });
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = selectedLanguage;
    recognition.start();

    setStatusIndicator("Listening...", "green");
    setVoiceButtonState(true);
    isVoiceCallActive = true;

    const resetUI = () => {
        setVoiceButtonState(false);
        setStatusIndicator("Ready", "green");
        isVoiceCallActive = false;
    };

    recognition.onresult = (event) => {
        const query = event.results[0][0].transcript;
        appendMessageToChat("user", query);
        submitQuery(query);
        resetUI();
    };

    recognition.onend = resetUI;
    recognition.onerror = resetUI;
}

function triggerSchemeQuery(query) {
    appendMessageToChat("user", query);
    submitQuery(query);
}

function applyLanguageSelection(lang, el) {
    selectedLanguage = lang;
    document.querySelectorAll(".lang-pill").forEach((pill) => pill.classList.remove("active"));
    el.classList.add("active");
    const hint = document.getElementById("voiceHint");
    if (hint) {
        hint.textContent = `Listening for: ${LANGUAGE_LABELS[lang] || lang}`;
    }
    const sidebarLang = document.getElementById("sidebarLangDisplay");
    if (sidebarLang) {
        const flag = LANGUAGE_FLAGS[lang] || "🇮🇳";
        sidebarLang.textContent = `${flag} ${LANGUAGE_LABELS[lang] || lang}`;
    }
}

function appendMessageToChat(role, content, options = {}) {
    const chat = document.getElementById("conversation");
    if (!chat) return;

    const variant = options.variant || (role === "user" ? "user" : "assistant");
    if (variant === "moderation") {
        const msg = document.createElement("div");
        msg.className = "message assistant moderation-block";
        const cat = options.moderationCategory;
        if (cat === "harmful") {
            const line = document.createElement("div");
            line.className = "moderation-category-headline";
            line.textContent = "We can't assist with that request.";
            msg.appendChild(line);
        } else if (cat === "off_topic") {
            const line = document.createElement("div");
            line.className = "moderation-category-headline";
            line.textContent = "I help with government schemes and civic services.";
            msg.appendChild(line);
        }
        const prefix = document.createElement("span");
        prefix.className = "moderation-prefix";
        prefix.textContent = "🙏 ";
        msg.appendChild(prefix);
        msg.appendChild(document.createTextNode(content || ""));
        chat.appendChild(msg);
        msg.scrollIntoView({ behavior: "smooth", block: "end" });
        return;
    }

    if (variant === "error") {
        const msg = document.createElement("div");
        msg.className = "message error";
        msg.textContent = content || "Something went wrong.";
        chat.appendChild(msg);
        msg.scrollIntoView({ behavior: "smooth", block: "end" });
        return;
    }

    if (role === "user") {
        const msg = document.createElement("div");
        msg.className = "message user";
        msg.textContent = content || "";
        chat.appendChild(msg);
        msg.scrollIntoView({ behavior: "smooth", block: "end" });
        return;
    }

    const wrap = document.createElement("div");
    wrap.className = "assistant-wrap";

    const msg = document.createElement("div");
    msg.className = "message assistant";
    const srcList = options.sources || [];
    if (srcList.length) {
        renderMessageWithCitations(msg, content || "", srcList);
    } else {
        msg.textContent = content || "No answer provided.";
    }
    wrap.appendChild(msg);

    if (srcList.length) {
        appendCitationFootnotes(wrap, srcList);
    }

    const why = options.reasoningWhy;
    if (why && why.trim()) {
        const panel = document.createElement("div");
        panel.className = "explain-panel";
        const h = document.createElement("div");
        h.className = "explain-panel-title";
        h.textContent = "Why this fits you";
        panel.appendChild(h);
        const body = document.createElement("div");
        body.className = "explain-panel-body";
        body.textContent = why.trim();
        panel.appendChild(body);
        wrap.appendChild(panel);
    }

    const nearText = options.nearMissText;
    const nearSrc = options.nearMissSources || [];
    if ((nearText && nearText.trim()) || nearSrc.length) {
        const panel = document.createElement("div");
        panel.className = "near-miss-panel";
        const h = document.createElement("div");
        h.className = "near-miss-panel-title";
        h.textContent = "Almost eligible";
        panel.appendChild(h);
        if (nearText && nearText.trim()) {
            const body = document.createElement("div");
            body.className = "near-miss-panel-body";
            body.textContent = nearText.trim();
            panel.appendChild(body);
        }
        if (nearSrc.length) {
            appendAssistantSourceLinks(panel, nearSrc, "Reference (lower match)");
        }
        wrap.appendChild(panel);
    }

    const topScore =
        typeof options.topScore === "number"
            ? options.topScore
            : Array.isArray(options.sources) && options.sources.length
              ? Math.max(...options.sources.map((s) => s.score || 0))
              : null;

    if (topScore !== null && !Number.isNaN(topScore)) {
        const sortedSrc = [...(options.sources || [])].sort((a, b) => (b.score || 0) - (a.score || 0));
        const serverLabel = sortedSrc[0]?.confidence_label;

        const meter = document.createElement("div");
        meter.className = "confidence-meter";
        const fill = document.createElement("div");
        fill.className = "confidence-meter-fill";
        const pct = Math.round(Math.min(1, Math.max(0, topScore)) * 100);
        fill.style.width = `${pct}%`;
        let band = "mid";
        let label = "Moderate match";
        if (topScore < 0.4) {
            band = "low";
            label = "Low confidence";
        } else if (topScore > 0.7) {
            band = "high";
            label = "Strong match (based on available data)";
        }
        fill.classList.add(band);
        meter.appendChild(fill);
        const cap = document.createElement("div");
        cap.className = "confidence-label";
        const displayLabel = serverLabel || label;
        const emoji = confidenceEmojiForLabel(displayLabel);
        cap.textContent = `${emoji}${displayLabel} · match strength`;
        wrap.appendChild(meter);
        wrap.appendChild(cap);
    }

    appendAssistantSourceLinks(wrap, options.sources || [], "Official portals (verified)");

    chat.appendChild(wrap);
    wrap.scrollIntoView({ behavior: "smooth", block: "end" });
}

function confidenceEmojiForLabel(label) {
    if (!label) return "";
    if (/strong match/i.test(label) || /verified/i.test(label)) return "🟢 ";
    if (/moderate/i.test(label)) return "🟡 ";
    return "🟠 ";
}

function stripCitationMarkers(text) {
    if (!text) return "";
    return text.replace(/\s*\[\d+\]/g, "").trim();
}

function citationHoverTitle(source) {
    if (!source) return "";
    const scheme = source.scheme || "Scheme";
    const preview = (source.preview_text || "").trim();
    const line = preview ? `${scheme} — ${preview}` : `${scheme} — Official catalogue match`;
    return line.length > 280 ? `${line.slice(0, 278)}…` : line;
}

function renderMessageWithCitations(msgEl, text, sources) {
    msgEl.textContent = "";
    const max = Array.isArray(sources) ? sources.length : 0;
    if (!text || !max) {
        msgEl.textContent = text || "";
        return;
    }
    const re = /\[(\d+)\]/g;
    let last = 0;
    let m;
    while ((m = re.exec(text)) !== null) {
        const chunk = text.slice(last, m.index);
        if (chunk) msgEl.appendChild(document.createTextNode(chunk));
        const n = parseInt(m[1], 10);
        if (n >= 1 && n <= max) {
            const sup = document.createElement("sup");
            sup.className = "cite-ref";
            const a = document.createElement("a");
            a.href = `#src-footnote-${n}`;
            a.className = "cite-ref-link";
            a.textContent = `[${n}]`;
            a.title = citationHoverTitle(sources[n - 1]);
            sup.appendChild(a);
            msgEl.appendChild(sup);
        } else {
            msgEl.appendChild(document.createTextNode(m[0]));
        }
        last = re.lastIndex;
    }
    const tail = text.slice(last);
    if (tail) msgEl.appendChild(document.createTextNode(tail));
}

function appendCitationFootnotes(wrap, sources) {
    if (!Array.isArray(sources) || !sources.length) return;
    let primaryIdx = 0;
    let bestScore = -1;
    sources.forEach((s, i) => {
        const sc = typeof s.score === "number" ? s.score : 0;
        if (sc > bestScore) {
            bestScore = sc;
            primaryIdx = i;
        }
    });
    const block = document.createElement("div");
    block.className = "citation-source-block";
    const title = document.createElement("div");
    title.className = "citation-footnotes-title";
    title.textContent = "Sources";
    block.appendChild(title);
    const hint = document.createElement("p");
    hint.className = "citation-footnotes-hint";
    hint.textContent =
        "Sources are from official government portals (MyScheme catalogue).";
    block.appendChild(hint);
    const ol = document.createElement("ol");
    ol.className = "citation-footnotes";
    ol.setAttribute("aria-label", "Source references");
    sources.forEach((s, idx) => {
        const num = idx + 1;
        const li = document.createElement("li");
        li.className = "citation-footnote-item";
        li.id = `src-footnote-${num}`;
        const isPrimary = idx === primaryIdx;
        if (isPrimary) {
            li.classList.add("primary-source");
            const lead = document.createElement("strong");
            lead.className = "citation-fn-primary-line";
            lead.textContent = `[${num}] ${s.scheme || "Scheme"} — Official Source`;
            li.appendChild(lead);
            if (s.source) {
                const catalogueLink = document.createElement("a");
                catalogueLink.href = s.source;
                catalogueLink.target = "_blank";
                catalogueLink.rel = "noopener noreferrer";
                catalogueLink.className = "citation-fn-link citation-fn-primary-link";
                catalogueLink.textContent = "MyScheme.gov.in / catalogue";
                li.appendChild(catalogueLink);
            }
        } else {
            const head = document.createElement("span");
            head.className = "citation-fn-label";
            head.textContent = `[${num}] `;
            li.appendChild(head);
            const name = document.createElement("strong");
            name.className = "citation-fn-scheme";
            name.textContent = s.scheme || "Scheme";
            li.appendChild(name);
            li.appendChild(document.createTextNode(" — "));
            if (s.source) {
                const catalogueLink = document.createElement("a");
                catalogueLink.href = s.source;
                catalogueLink.target = "_blank";
                catalogueLink.rel = "noopener noreferrer";
                catalogueLink.className = "citation-fn-link";
                catalogueLink.textContent = "MyScheme / catalogue";
                li.appendChild(catalogueLink);
            } else {
                li.appendChild(document.createTextNode("Retrieved context"));
            }
        }
        ol.appendChild(li);
    });
    block.appendChild(ol);
    wrap.appendChild(block);
}

function appendAssistantSourceLinks(container, sources, headingText) {
    if (!Array.isArray(sources) || !sources.length) return;
    const rows = sources.filter((s) => s.apply_link || s.source);
    if (!rows.length) return;

    const block = document.createElement("div");
    block.className = "source-links-block";
    const heading = document.createElement("div");
    heading.className = "source-links-heading";
    heading.textContent = headingText || "Official portals (verified)";
    block.appendChild(heading);

    rows.forEach((s) => {
        const row = document.createElement("div");
        row.className = "source-links-row";
        const name = document.createElement("div");
        name.className = "source-links-scheme-name";
        name.textContent = s.scheme || "Scheme";
        row.appendChild(name);
        if (s.confidence_label) {
            const tier = document.createElement("div");
            tier.className = "source-links-confidence";
            tier.textContent = `${confidenceEmojiForLabel(s.confidence_label)}${s.confidence_label}`;
            row.appendChild(tier);
        }
        const links = document.createElement("div");
        links.className = "scheme-links";
        if (s.apply_link) {
            const a = document.createElement("a");
            a.href = s.apply_link;
            a.target = "_blank";
            a.rel = "noopener noreferrer";
            a.className = "scheme-link scheme-link-apply";
            const isApply = s.cta_label === "Apply Now";
            a.textContent = isApply ? "🔗 Apply Now" : "🔍 Check Eligibility";
            links.appendChild(a);
        }
        if (s.source) {
            const b = document.createElement("a");
            b.href = s.source;
            b.target = "_blank";
            b.rel = "noopener noreferrer";
            b.className = "scheme-link scheme-link-source";
            b.textContent = "📄 Official Info";
            links.appendChild(b);
        }
        row.appendChild(links);
        block.appendChild(row);
    });

    container.appendChild(block);
}

async function submitQuery(query) {
    setStatusIndicator("Thinking...", "orange");
    showTypingIndicator();
    try {
        const resp = await fetch(`${BACKEND_URL}/api/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query, user_id: sessionUserId, language: selectedLanguage }),
        });
        removeTypingIndicator();

        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const payload = await resp.json();

        if (payload.moderation_blocked) {
            appendMessageToChat("assistant", payload.redirect_message || "Please ask about welfare schemes.", {
                variant: "moderation",
                moderationCategory: payload.moderation_category,
            });
            setStatusIndicator("Ready", "green");
            return;
        }

        const sources = payload.sources || [];
        const topScore = sources.length ? Math.max(...sources.map((s) => s.score || 0)) : null;
        appendMessageToChat("assistant", payload.answer, {
            topScore,
            sources,
            reasoningWhy: payload.reasoning_why,
            nearMissText: payload.near_miss_text,
            nearMissSources: payload.near_miss_sources || [],
        });

        sources.forEach((s) => {
            if (s.scheme) sessionSchemeNames.add(s.scheme);
        });
        (payload.near_miss_sources || []).forEach((s) => {
            if (s.scheme) sessionSchemeNames.add(s.scheme);
        });
        renderSchemePills();

        if (!vapiInstance || !isVoiceCallActive) {
            speakResponseText(stripCitationMarkers(payload.answer));
        }
        setStatusIndicator("Ready", "green");
    } catch {
        removeTypingIndicator();
        appendMessageToChat(
            "assistant",
            "Sorry, there was an error connecting to SahayakSetu. Please try again.",
            { variant: "error" },
        );
        setStatusIndicator("Error", "red");
        setTimeout(() => setStatusIndicator("Ready", "green"), 3000);
    }
}

function speakResponseText(text) {
    if (!text || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const scripts = {
        "hi-IN": /[\u0900-\u097F]/,
        "kn-IN": /[\u0C80-\u0CFF]/,
        "te-IN": /[\u0C00-\u0C7F]/,
        "ta-IN": /[\u0B80-\u0BFF]/,
        "bn-IN": /[\u0980-\u09FF]/,
    };

    let detectedLang = "en-IN";
    for (const [lang, regex] of Object.entries(scripts)) {
        if (regex.test(text)) {
            detectedLang = lang;
            break;
        }
    }

    utterance.lang = detectedLang === "en-IN" ? selectedLanguage : detectedLang;
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(
        (v) => v.lang === utterance.lang && (v.name.includes("Neural") || v.name.includes("Google")),
    );
    if (preferredVoice) utterance.voice = preferredVoice;

    window.speechSynthesis.speak(utterance);
}

function handleTextSubmit() {
    const input = document.getElementById("textInput");
    const q = input?.value.trim();
    if (!q) return;
    appendMessageToChat("user", q);
    input.value = "";
    submitQuery(q);
}

function showTypingIndicator() {
    const chat = document.getElementById("conversation");
    if (!chat) return;
    const t = document.createElement("div");
    t.className = "typing-indicator";
    t.id = "typing";
    t.innerHTML = `<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>`;
    chat.appendChild(t);
}

function removeTypingIndicator() {
    const t = document.getElementById("typing");
    if (t) t.remove();
}

function setVoiceButtonState(active) {
    const btn = document.getElementById("voiceBtn");
    const mic = document.getElementById("micIcon");
    const stop = document.getElementById("stopIcon");
    const waveform = document.getElementById("voiceWaveform");
    const label = document.getElementById("voiceLabel");
    if (!btn || !mic || !stop || !waveform || !label) return;

    if (active) {
        btn.classList.add("active");
        mic.classList.add("hidden");
        waveform.classList.remove("hidden");
        stop.classList.remove("hidden");
        label.textContent = "Stop";
    } else {
        btn.classList.remove("active");
        mic.classList.remove("hidden");
        waveform.classList.add("hidden");
        stop.classList.add("hidden");
        label.textContent = "Talk";
    }
}

function setStatusIndicator(text, colorKey) {
    const st = document.getElementById("statusText") || document.querySelector(".status-text");
    const d = document.getElementById("statusDot") || document.querySelector(".status-dot");
    if (st) st.textContent = text;
    if (d) {
        const colorMap = {
            green: "var(--color-success)",
            orange: "var(--color-accent)",
            red: "var(--color-error)",
            yellow: "var(--color-warn)",
            blue: "#5dade2",
        };
        d.style.background = colorMap[colorKey] || colorMap.green;
        const pulse = text === "Thinking..." || text === "Listening...";
        d.classList.toggle("pulse", pulse);
    }
}

function renderSchemePills() {
    const host = document.getElementById("schemePills");
    if (!host) return;
    host.innerHTML = "";
    sessionSchemeNames.forEach((name) => {
        const span = document.createElement("span");
        span.className = "scheme-pill";
        span.textContent = name;
        host.appendChild(span);
    });
}

function downloadConversationTranscript() {
    const chat = document.getElementById("conversation");
    if (!chat) return;
    const lines = [];
    chat.querySelectorAll(".message, .source-links-block, .citation-source-block").forEach((node) => {
        let speaker = "Assistant";
        if (node.classList.contains("user")) speaker = "You";
        if (node.classList.contains("error")) speaker = "System";
        if (node.classList.contains("moderation-block")) speaker = "Notice";
        if (node.classList.contains("source-links-block")) speaker = "Links";
        if (node.classList.contains("citation-source-block")) speaker = "Sources";
        lines.push(`${speaker}: ${node.textContent.trim()}`);
    });
    const blob = new Blob([lines.join("\n\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sahayaksetu-chat.txt";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}

function openSchemeSheetFromButton(button) {
    const title = button.getAttribute("data-scheme") || "";
    currentSheetScheme = title;
    document.getElementById("sheetSchemeTitle").textContent = title;
    document.getElementById("sheetMinistry").textContent = button.getAttribute("data-ministry") || "";
    document.getElementById("sheetBenefit").textContent = button.getAttribute("data-benefit") || "";
    document.getElementById("sheetEligibility").textContent = button.getAttribute("data-eligibility") || "";

    const applyUrl = button.getAttribute("data-apply-link");
    const sourceUrl = button.getAttribute("data-source");
    const applyLink = document.getElementById("sheetApplyLink");
    const sourceLink = document.getElementById("sheetSourceLink");
    if (applyLink) {
        if (applyUrl) {
            applyLink.href = applyUrl;
            applyLink.classList.remove("hidden");
        } else {
            applyLink.classList.add("hidden");
        }
    }
    if (sourceLink) {
        if (sourceUrl) {
            sourceLink.href = sourceUrl;
            sourceLink.classList.remove("hidden");
        } else {
            sourceLink.classList.add("hidden");
        }
    }

    const sheet = document.getElementById("schemeSheet");
    sheet.classList.add("open");
    sheet.setAttribute("aria-hidden", "false");
}

function closeSchemeSheet() {
    const sheet = document.getElementById("schemeSheet");
    sheet.classList.remove("open");
    sheet.setAttribute("aria-hidden", "true");
}

function wireSchemeSheet() {
    const askBtn = document.getElementById("sheetAskBtn");
    if (!askBtn) return;
    askBtn.onclick = () => {
        const q = `Tell me more about ${currentSheetScheme} and how I can apply.`;
        closeSchemeSheet();
        triggerSchemeQuery(q);
    };
}

document.addEventListener("DOMContentLoaded", () => {
    populateStateSelect();
    initialiseVapiSDK();
    wireSchemeSheet();

    document.querySelectorAll(".scheme-card-trigger").forEach((btn) => {
        btn.addEventListener("click", () => openSchemeSheetFromButton(btn));
    });

    const input = document.getElementById("textInput");
    if (input) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") handleTextSubmit();
        });
    }

    if (window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.getVoices();
        };
    }

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute("href"));
            if (target) target.scrollIntoView({ behavior: "smooth" });
        });
    });

    applyLanguageSelection(
        "hi-IN",
        document.querySelector('.lang-pill[data-lang="hi-IN"]') || document.querySelector(".lang-pill"),
    );
});
