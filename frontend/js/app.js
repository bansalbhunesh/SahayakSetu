import { BACKEND_URL, INDIAN_STATES, LANGUAGE_FLAGS, LANGUAGE_LABELS, USE_CONTINUOUS_VOICE, VAPI_ASSISTANT_ID, VAPI_PUBLIC_KEY } from "./constants.js";
import {
    appendMessageToChat,
    downloadConversationTranscript,
    removeTypingIndicator,
    renderSchemePills,
    setStatusIndicator,
    showTypingIndicator,
    stripCitationMarkers,
    updateLanguageUI,
} from "./chat.js";
import { appState, setSelectedLanguage, setSessionUserId } from "./state.js";
import {
    setVoiceButtonState,
    speakResponseText,
    startBrowserSpeechFallback,
    stopBrowserSpeechRecognition,
} from "./voice.js";

const VAPI_SDK_MAX_ATTEMPTS = 60;
let vapiSdkLoadAttempts = 0;

const SCHEME_ROLE_MAP = {
    "pm kisan": "farmer",
    "mgnrega": "farmer",
    "rythu bharosa": "farmer",
    "ayushman bharat": "below poverty line household",
    "ujjwala yojana": "woman",
    "sukanya samriddhi": "woman",
    "gruha lakshmi": "woman",
    "pm awas yojana": "below poverty line household",
    "jan dhan yojana": "below poverty line household",
    "pm mudra yojana": "artisan",
    "pm vishwakarma": "artisan",
    "pm svanidhi": "artisan",
};

async function userFacingHttpMessage(resp) {
    const status = resp.status;
    if (status === 429) return "Too many requests. Please wait a minute and try again.";
    if (status === 503) return "The service is busy or temporarily unavailable. Please try again in a few minutes.";
    if (status === 422) {
        try {
            const j = await resp.json();
            const d = j.detail;
            if (Array.isArray(d) && d.length) {
                const parts = d.map((x) => (typeof x === "object" && x?.msg) || String(x));
                return `Invalid input: ${parts.join("; ")}`;
            }
        } catch { /* ignore */ }
        return "Invalid request. Please shorten or simplify your question.";
    }
    return `Something went wrong (HTTP ${status}). Please try again.`;
}

function setVoiceLiveCaption(text) {
    const el = document.getElementById("voiceLiveCaption");
    if (!el) return;
    const t = (text || "").trim();
    if (!t) { el.textContent = ""; el.classList.add("hidden"); return; }
    el.textContent = t;
    el.classList.remove("hidden");
}

function setVoiceState(state) {
    document.body?.setAttribute("data-voice-state", state || "idle");
    const hint = document.getElementById("voiceHint");
    const dbBar = document.getElementById("voiceDbBar");
    if (state === "listening") {
        if (hint) hint.textContent = "Listening… tap to stop";
        if (dbBar) { dbBar.classList.remove("hidden"); dbBar.classList.add("listening-anim"); }
    } else if (state === "thinking") {
        if (hint) hint.textContent = "Processing your question…";
        if (dbBar) { dbBar.classList.add("hidden"); dbBar.classList.remove("listening-anim"); }
    } else if (state === "speaking") {
        if (hint) hint.textContent = "Speaking your answer…";
        if (dbBar) { dbBar.classList.add("hidden"); dbBar.classList.remove("listening-anim"); }
    } else {
        if (hint) hint.textContent = `Listening for: ${LANGUAGE_LABELS[appState.selectedLanguage] || appState.selectedLanguage}`;
        if (dbBar) { dbBar.classList.add("hidden"); dbBar.classList.remove("listening-anim"); }
    }
}

function openLangPopover() {
    const popover = document.getElementById("langPopover");
    const btn = document.getElementById("langChipBtn");
    if (!popover || !btn) return;
    popover.hidden = false;
    btn.setAttribute("aria-expanded", "true");
}

function closeLangPopover() {
    const popover = document.getElementById("langPopover");
    const btn = document.getElementById("langChipBtn");
    if (!popover || !btn) return;
    popover.hidden = true;
    btn.setAttribute("aria-expanded", "false");
}

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

    const showFinder = mode === "finder";
    talkPanel.classList.toggle("hidden", showFinder);
    finderPanel.classList.toggle("hidden", !showFinder);
    finderPanel.setAttribute("aria-hidden", String(!showFinder));
    talkBtn.classList.toggle("active", !showFinder);
    finderBtn.classList.toggle("active", showFinder);
    talkBtn.setAttribute("aria-selected", String(!showFinder));
    finderBtn.setAttribute("aria-selected", String(showFinder));
}

function applyLanguageSelection(lang, el) {
    setSelectedLanguage(lang);
    document.querySelectorAll(".lang-pill").forEach((pill) => pill.classList.remove("active"));
    if (el) el.classList.add("active");
    updateLanguageUI(lang);
    const flag = document.getElementById("langChipFlag");
    const label = document.getElementById("langChipLabel");
    if (flag) flag.textContent = LANGUAGE_FLAGS[lang] || "🇮🇳";
    if (label) label.textContent = LANGUAGE_LABELS[lang] || lang;
    closeLangPopover();
    setVoiceState("idle");
}

function detectBrowserLanguage() {
    const supported = new Set(Object.keys(LANGUAGE_LABELS));
    const candidates = [...(navigator.languages || []), navigator.language]
        .filter(Boolean)
        .map((x) => String(x));
    for (const raw of candidates) {
        if (supported.has(raw)) return raw;
        const base = `${raw.split("-")[0]}-IN`;
        if (supported.has(base)) return base;
    }
    return "en-IN";
}

function incomeBandToAnnualIncome(incomeRaw) {
    const v = (incomeRaw || "").toLowerCase();
    if (v.includes("below 1")) return 50000;
    if (v.includes("1 to 3")) return 200000;
    if (v.includes("3 to 6")) return 450000;
    if (v.includes("above 6")) return 800000;
    return null;
}

function buildProfileFromFinder() {
    const state = document.getElementById("finderState")?.value?.trim() || "";
    const role = document.querySelector('input[name="finderRole"]:checked')?.value || "";
    const income = document.querySelector('input[name="finderIncome"]:checked')?.value || "";
    const profile = {};
    if (state) profile.state = state;
    if (role) profile.occupation = role;
    const annual = incomeBandToAnnualIncome(income);
    if (annual != null) profile.annual_income = annual;
    if (role.toLowerCase().includes("below poverty")) profile.bpl = true;
    return profile;
}

function getProfileForRequest() {
    if (appState.lastFinderProfile && Object.keys(appState.lastFinderProfile).length) {
        return appState.lastFinderProfile;
    }
    const finderPanel = document.getElementById("finderPanel");
    if (finderPanel && !finderPanel.classList.contains("hidden")) {
        return buildProfileFromFinder();
    }
    return null;
}

function handleEligibilitySubmit(event) {
    event.preventDefault();
    const state = document.getElementById("finderState")?.value || "";
    const role = document.querySelector('input[name="finderRole"]:checked')?.value || "citizen";
    const income = document.querySelector('input[name="finderIncome"]:checked')?.value || "unspecified";
    appState.lastFinderProfile = buildProfileFromFinder();
    const query = `Show government welfare schemes for a ${role} in ${state} with annual family income ${income}. Summarise the most relevant central or state schemes and how to apply.`;
    setInteractionMode("talk");
    appendMessageToChat("user", query);
    submitQuery(query);
}

function triggerSchemeQuery(query) {
    appendMessageToChat("user", query);
    submitQuery(query);
}

function setSessionFromPayload(payload) {
    if (payload.session_user_id) setSessionUserId(payload.session_user_id);
}

function switchSidebarTab(tabName = "trust") {
    document.querySelectorAll('.sidebar-tab[data-tab]').forEach((tab) => {
        const active = tab.dataset.tab === tabName;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-selected", String(active));
    });
    document.querySelectorAll('.sidebar-panel[data-panel]').forEach((panel) => {
        panel.classList.toggle("active", panel.dataset.panel === tabName);
    });
}

function pulseEvidenceTab() {
    const tab = document.querySelector('.sidebar-tab[data-tab="evidence"]');
    if (!(tab instanceof HTMLElement)) return;
    tab.classList.remove("tab-glow");
    void tab.offsetWidth;
    tab.classList.add("tab-glow");
}

function updateEvidencePanel(payload) {
    const trustDot = document.getElementById("sidebarTrustDot");
    const trustLabel = document.getElementById("sidebarTrustLabel");
    const trustHint = document.getElementById("sidebarTrustHint");
    const queryUnderstanding = document.getElementById("sidebarQueryUnderstanding");
    const evidenceList = document.getElementById("sidebarEvidenceList");
    if (!trustDot || !trustLabel || !trustHint || !queryUnderstanding || !evidenceList) return;

    const confidence = payload?.confidence || "low";
    const confidenceLabel = confidence === "high" ? "Verified signal" : confidence === "medium" ? "Partial signal" : "Needs clarification";
    trustLabel.textContent = confidenceLabel;
    trustDot.dataset.level = confidence;
    trustHint.textContent = payload?.next_step || "Grounded answer generated from retrieved government scheme sources.";

    const qd = payload?.query_debug;
    if (qd?.original && qd?.rewritten && qd.original !== qd.rewritten) {
        queryUnderstanding.textContent = `${qd.original} -> ${qd.rewritten}`;
    } else if (qd?.rewritten) {
        queryUnderstanding.textContent = qd.rewritten;
    } else {
        queryUnderstanding.textContent = payload?.query || "No rewrite data for this response.";
    }

    const rows = Array.isArray(payload?.sources) ? [...payload.sources] : [];
    rows.sort((a, b) => (b.score || 0) - (a.score || 0));
    const topRows = rows.slice(0, 3);
    evidenceList.innerHTML = "";
    if (!topRows.length) {
        evidenceList.innerHTML = `<p class="sidebar-empty">No evidence scores returned for this response.</p>`;
        return;
    }
    topRows.forEach((source, idx) => {
        const row = document.createElement("div");
        row.className = "sidebar-evidence-row";
        const pct = Math.round(Math.min(1, Math.max(0, source.score || 0)) * 100);
        row.innerHTML = `
          <div class="sidebar-evidence-head">
            <span class="sidebar-evidence-rank">#${idx + 1}</span>
            <span class="sidebar-evidence-name">${source.scheme || "Scheme source"}</span>
            <span class="sidebar-evidence-score">${pct}%</span>
          </div>
          <div class="sidebar-evidence-meter"><span style="width:${pct}%"></span></div>
        `;
        evidenceList.appendChild(row);
    });
}

function triggerConfetti(btn) {
    const colors = ["#ea7a1f", "#f2a33a", "#fde68a", "#2ecc71", "#5dade2", "#e74c3c"];
    const burst = document.createElement("div");
    burst.style.cssText = "position:absolute;top:50%;left:50%;pointer-events:none;z-index:50;";
    for (let i = 0; i < 8; i++) {
        const p = document.createElement("span");
        const angle = (i / 8) * 360;
        const dist = 28 + Math.random() * 18;
        const tx = Math.round(Math.cos(angle * Math.PI / 180) * dist);
        const ty = Math.round(Math.sin(angle * Math.PI / 180) * dist);
        p.style.cssText = `
            position:absolute;width:6px;height:6px;border-radius:50%;
            background:${colors[i % colors.length]};
            --tx:${tx}px;--ty:${ty}px;
            animation:confetti-fly 0.65s ease-out forwards;
        `;
        burst.appendChild(p);
    }
    const wrapper = btn.closest(".reaction-row") || btn;
    wrapper.style.position = "relative";
    wrapper.appendChild(burst);
    setTimeout(() => burst.remove(), 800);
}

function _reportError(errorCode, queryPrefix = "") {
    try {
        fetch(`${BACKEND_URL}/api/error`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                error: errorCode,
                trace_id: appState.lastTraceId,
                language: appState.selectedLanguage,
                query_prefix: (queryPrefix || "").slice(0, 50),
            }),
        }).catch(() => {}); // fire-and-forget, never throw
    } catch (_) {}
}

async function _sendFeedback(value, queryPreview, answerPreview) {
    try {
        fetch(`${BACKEND_URL}/api/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                value,
                trace_id: appState.lastTraceId,
                session_user_id: appState.sessionUserId,
                query_preview: (queryPreview || "").slice(0, 100),
                answer_preview: (answerPreview || "").slice(0, 200),
            }),
        }).catch(() => {});
    } catch (_) {}
}

async function submitQuery(query) {
    const q = (query == null ? "" : String(query)).trim();
    if (!q || appState.searchInFlight) return;
    appState.searchInFlight = true;
    localStorage.setItem("sahayak_last_query", q);
    setStatusIndicator("Thinking...", "orange");
    setVoiceState("thinking");
    showTypingIndicator();
    try {
        const resp = await fetch(`${BACKEND_URL}/api/search`, {
            method: "POST",
            signal: AbortSignal.timeout(25000),
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: q,
                user_id: appState.sessionUserId,
                language: appState.selectedLanguage,
                profile: getProfileForRequest(),
                include_plan: true,
            }),
        });
        removeTypingIndicator();
        if (!resp.ok) {
            const msg = await userFacingHttpMessage(resp);
            throw new Error(msg);
        }
        const ct = (resp.headers.get("content-type") || "").toLowerCase();
        if (!ct.includes("application/json")) throw new Error("Server returned an unexpected response. Please try again.");
        const payload = await resp.json();
        // Always capture trace ID — needed for debug panel and error correlation.
        appState.lastTraceId = resp.headers.get("X-Trace-Id") || null;
        setSessionFromPayload(payload);

        if (payload.moderation_blocked) {
            appendMessageToChat("assistant", payload.redirect_message || "Please ask about welfare schemes.", {
                variant: "moderation",
                moderationCategory: payload.moderation_category,
            });
            updateEvidencePanel(payload);
            switchSidebarTab("evidence");
            pulseEvidenceTab();
            setStatusIndicator("Ready", "green");
            setVoiceState("idle");
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
            confidence: payload.confidence,
            nextStep: payload.next_step,
            queryDebug: payload.query_debug,
            plan: payload.plan,
            eligibilityHints: payload.eligibility_hints || [],
        });
        if (payload.retrieval_debug) {
            appState.lastRetrievalDebug = payload.retrieval_debug;
            renderDebugDrawer();
        }
        sources.forEach((s) => s.scheme && appState.sessionSchemeNames.add(s.scheme));
        (payload.near_miss_sources || []).forEach((s) => s.scheme && appState.sessionSchemeNames.add(s.scheme));
        renderSchemePills(appState.sessionSchemeNames);
        updateEvidencePanel(payload);
        switchSidebarTab("evidence");
        pulseEvidenceTab();

        const canBrowserTts = !appState.vapiInstance || !appState.isVoiceCallActive;
        if (canBrowserTts && payload.answer) {
            setVoiceState("speaking");
            speakResponseText(stripCitationMarkers(payload.answer), appState.selectedLanguage, {
                onStart: () => setStatusIndicator("Speaking...", "blue"),
                onEnd: () => { setStatusIndicator("Ready", "green"); setVoiceState("idle"); },
            });
        } else {
            setStatusIndicator("Ready", "green");
            setVoiceState("idle");
        }
    } catch (err) {
        removeTypingIndicator();
        const fallback = "Sorry, there was an error connecting to SahayakSetu. Please try again.";
        let msg = fallback;
        let errorCode = "fetch_failed";
        if (err && err.name === "TimeoutError") {
            msg = "The request timed out. The server may be starting up — please try again in a moment.";
            errorCode = "timeout";
        } else if (err instanceof SyntaxError) {
            msg = "Invalid response from server. Please try again.";
            errorCode = "parse_error";
        } else if (err && typeof err.message === "string" && err.message.trim()) {
            msg = err.message;
        }
        appendMessageToChat("assistant", msg, { variant: "error" });
        setStatusIndicator("Error", "red");
        setVoiceState("idle");
        setTimeout(() => setStatusIndicator("Ready", "green"), 3000);
        _reportError(errorCode, query);
    } finally {
        appState.searchInFlight = false;
    }
}

function renderDebugDrawer() {
    const host = document.getElementById("debugDrawerContent");
    const trace = document.getElementById("debugTraceId");
    if (!host || !trace) return;
    trace.textContent = `Trace ID: ${appState.lastTraceId || "n/a"}`;
    host.textContent = appState.lastRetrievalDebug ? JSON.stringify(appState.lastRetrievalDebug, null, 2) : "No retrieval debug payload yet.";
}

function toggleDebugDrawer(forceOpen = null) {
    const drawer = document.getElementById("debugDrawer");
    if (!drawer) return;
    const isOpen = drawer.classList.contains("open");
    const open = forceOpen === null ? !isOpen : Boolean(forceOpen);
    drawer.classList.toggle("open", open);
    drawer.setAttribute("aria-hidden", String(!open));
    drawer.toggleAttribute("inert", !open);
}

function decorateSchemeCards() {
    document.querySelectorAll(".scheme-card").forEach((card) => {
        const trigger = card.querySelector(".scheme-card-trigger");
        if (!trigger) return;
        const schemeLabel = (trigger.getAttribute("data-scheme") || "this scheme").trim();
        const ministry = trigger.getAttribute("data-ministry") || "";
        const lower = ministry.toLowerCase();
        if (lower.includes("finance")) card.dataset.ministry = "finance";
        else if (lower.includes("health")) card.dataset.ministry = "health";
        else if (lower.includes("housing") || lower.includes("urban")) card.dataset.ministry = "housing";
        else if (lower.includes("agriculture") || lower.includes("farm")) card.dataset.ministry = "agri";
        else card.dataset.ministry = "default";

        const schemeName = (trigger.getAttribute("data-scheme") || "").toLowerCase();
        const matchedRole = Object.entries(SCHEME_ROLE_MAP).find(([k]) => schemeName.includes(k))?.[1] || "farmer";
        const eligBtn = document.createElement("button");
        eligBtn.type = "button";
        eligBtn.className = "scheme-check-eligibility";
        eligBtn.dataset.action = "scheme-eligibility";
        eligBtn.dataset.role = matchedRole;
        eligBtn.dataset.scheme = trigger.getAttribute("data-scheme") || "";
        eligBtn.textContent = "Check eligibility →";
        card.appendChild(eligBtn);

        const applyAnchor = card.querySelector(".scheme-link-apply");
        if (applyAnchor instanceof HTMLAnchorElement) {
            applyAnchor.setAttribute("aria-label", `Apply now for ${schemeLabel}`);
        }
        const sourceAnchor = card.querySelector(".scheme-link-source");
        if (sourceAnchor instanceof HTMLAnchorElement) {
            sourceAnchor.setAttribute("aria-label", `Official information for ${schemeLabel}`);
        }
    });
}

function handleTextSubmit() {
    const input = document.getElementById("textInput");
    const query = input?.value.trim();
    if (!query || appState.searchInFlight) return;
    appendMessageToChat("user", query);
    input.value = "";
    submitQuery(query);
}

function initialiseVapiSDK() {
    if (VAPI_PUBLIC_KEY === "YOUR_VAPI_PUBLIC_KEY") return;
    try {
        if (window.Vapi) {
            appState.vapiInstance = new window.Vapi(VAPI_PUBLIC_KEY);
            bindVapiEventHandlers();
            vapiSdkLoadAttempts = 0;
            setStatusIndicator("Ready", "green");
        } else {
            vapiSdkLoadAttempts += 1;
            if (vapiSdkLoadAttempts >= VAPI_SDK_MAX_ATTEMPTS) {
                setStatusIndicator("Voice SDK unavailable", "yellow");
                const hint = document.getElementById("voiceHint");
                if (hint) hint.textContent = "Voice active (browser fallback mode)";
                return;
            }
            setTimeout(initialiseVapiSDK, 500);
        }
    } catch {
        setStatusIndicator("Voice unavailable", "yellow");
        const hint = document.getElementById("voiceHint");
        if (hint) hint.textContent = "Voice active (browser fallback mode)";
    }
}

function bindVapiEventHandlers() {
    if (!appState.vapiInstance) return;
    appState.vapiInstance.on("call-start", () => {
        appState.isVoiceCallActive = true;
        appState.browserRecognitionActive = false;
        setVoiceButtonState(true);
        setVoiceState("listening");
        setStatusIndicator("Listening...", "green");
    });
    appState.vapiInstance.on("call-end", () => {
        appState.isVoiceCallActive = false;
        setVoiceButtonState(false);
        setVoiceState("idle");
        setStatusIndicator("Ready", "green");
    });
    appState.vapiInstance.on("message", (msg) => {
        if (msg.type === "transcript" && msg.transcriptType === "final") {
            appendMessageToChat(msg.role === "user" ? "user" : "assistant", msg.transcript);
        }
    });
}

function handleVoiceToggle() {
    if (appState.isVoiceCallActive) {
        if (appState.browserRecognitionActive) {
            stopBrowserSpeechRecognition();
        } else if (appState.vapiInstance) {
            appState.vapiInstance.stop();
        }
        appState.isVoiceCallActive = false;
        appState.browserRecognitionActive = false;
        setVoiceButtonState(false);
        setVoiceLiveCaption("");
        setVoiceState("idle");
        setStatusIndicator("Ready", "green");
        return;
    }
    if (appState.vapiInstance && VAPI_ASSISTANT_ID !== "YOUR_VAPI_ASSISTANT_ID") {
        appState.vapiInstance.start(VAPI_ASSISTANT_ID);
        return;
    }
    const started = startBrowserSpeechFallback({
        selectedLanguage: appState.selectedLanguage,
        continuous: USE_CONTINUOUS_VOICE,
        onInterim: (live) => {
            setVoiceLiveCaption(live);
            setStatusIndicator("Listening...", "green");
        },
        onStart: () => {
            setStatusIndicator("Listening...", "green");
            setVoiceButtonState(true);
            setVoiceState("listening");
            appState.isVoiceCallActive = true;
            appState.browserRecognitionActive = true;
            setVoiceLiveCaption("");
        },
        onStop: () => {
            setVoiceButtonState(false);
            setVoiceLiveCaption("");
            setVoiceState("thinking");
            setStatusIndicator("Processing...", "orange");
            appState.isVoiceCallActive = false;
            appState.browserRecognitionActive = false;
        },
        onUserText: (query) => {
            appendMessageToChat("user", query);
            submitQuery(query);
        },
    });
    if (!started) {
        appendMessageToChat("assistant", "Sorry, voice recognition is not supported in this browser. Please type your question below.", { variant: "error" });
    }
}

function openSchemeSheetFromButton(button) {
    const title = button.getAttribute("data-scheme") || "";
    appState.currentSheetScheme = title;
    document.getElementById("sheetSchemeTitle").textContent = title;
    document.getElementById("sheetMinistry").textContent = button.getAttribute("data-ministry") || "";
    document.getElementById("sheetBenefit").textContent = button.getAttribute("data-benefit") || "";
    document.getElementById("sheetEligibility").textContent = button.getAttribute("data-eligibility") || "";

    const applyUrl = button.getAttribute("data-apply-link");
    const sourceUrl = button.getAttribute("data-source");
    const applyLink = document.getElementById("sheetApplyLink");
    const sourceLink = document.getElementById("sheetSourceLink");
    if (applyLink) { applyLink.classList.toggle("hidden", !applyUrl); if (applyUrl) applyLink.href = applyUrl; }
    if (sourceLink) { sourceLink.classList.toggle("hidden", !sourceUrl); if (sourceUrl) sourceLink.href = sourceUrl; }

    const sheet = document.getElementById("schemeSheet");
    sheet.classList.add("open");
    sheet.setAttribute("aria-hidden", "false");
    sheet.removeAttribute("inert");
}

function closeSchemeSheet() {
    const sheet = document.getElementById("schemeSheet");
    sheet.classList.remove("open");
    sheet.setAttribute("aria-hidden", "true");
    sheet.setAttribute("inert", "");
}

function wireSchemeSheet() {
    const askBtn = document.getElementById("sheetAskBtn");
    if (!askBtn) return;
    askBtn.onclick = () => {
        const query = `Tell me more about ${appState.currentSheetScheme} and how I can apply.`;
        closeSchemeSheet();
        triggerSchemeQuery(query);
    };
}

function initSidebarSample() {
    const evidenceList = document.getElementById("sidebarEvidenceList");
    if (!evidenceList) return;
    const samples = [
        { scheme: "PM Kisan", score: 0.91 },
        { scheme: "MGNREGA", score: 0.78 },
    ];
    evidenceList.innerHTML = "";
    const lbl = document.createElement("p");
    lbl.className = "sidebar-sample-label";
    lbl.textContent = "Sample — ask a question for real results";
    evidenceList.appendChild(lbl);
    samples.forEach((s, idx) => {
        const pct = Math.round(s.score * 100);
        const row = document.createElement("div");
        row.className = "sidebar-evidence-row";
        row.innerHTML = `
          <div class="sidebar-evidence-head">
            <span class="sidebar-evidence-rank">#${idx + 1}</span>
            <span class="sidebar-evidence-name">${s.scheme}</span>
            <span class="sidebar-evidence-score">${pct}%</span>
          </div>
          <div class="sidebar-evidence-meter"><span style="width:${pct}%"></span></div>
        `;
        evidenceList.appendChild(row);
    });
}

function initLastQueryBanner() {
    const lastQuery = localStorage.getItem("sahayak_last_query");
    if (!lastQuery) return;
    const chat = document.getElementById("conversation");
    if (!chat) return;
    const banner = document.createElement("div");
    banner.className = "last-query-banner";
    const label = document.createElement("span");
    label.className = "last-query-text";
    label.textContent = `Last time: "${lastQuery.slice(0, 55)}${lastQuery.length > 55 ? "…" : ""}"`;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "last-query-link";
    btn.textContent = "Ask again →";
    btn.onclick = () => {
        banner.remove();
        appendMessageToChat("user", lastQuery);
        submitQuery(lastQuery);
    };
    banner.appendChild(label);
    banner.appendChild(btn);
    chat.appendChild(banner);
}

function wireDomEvents() {
    const form = document.getElementById("eligibilityForm");
    form?.addEventListener("submit", handleEligibilitySubmit);

    document.querySelectorAll(".scheme-card-trigger").forEach((btn) => {
        btn.addEventListener("click", () => openSchemeSheetFromButton(btn));
    });

    document.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof Element)) return;

        // Close lang popover on outside click
        const popover = document.getElementById("langPopover");
        const chipBtn = document.getElementById("langChipBtn");
        if (popover && !popover.hidden && !popover.contains(target) && !chipBtn?.contains(target) && target !== chipBtn) {
            closeLangPopover();
        }

        const actionEl = target.closest("[data-action]");
        if (!(actionEl instanceof HTMLElement)) return;
        const action = actionEl.dataset.action;
        if (!action) return;

        if (action === "mode-talk") setInteractionMode("talk");
        if (action === "mode-finder") setInteractionMode("finder");
        if (action === "toggle-voice") handleVoiceToggle();
        if (action === "send-text") handleTextSubmit();
        if (action === "share-transcript") downloadConversationTranscript();
        if (action === "close-sheet") closeSchemeSheet();
        if (action === "close-debug") toggleDebugDrawer(false);
        if (action === "sidebar-tab") switchSidebarTab(actionEl.dataset.tab || "trust");
        if (action === "toggle-lang") {
            const p = document.getElementById("langPopover");
            if (p?.hidden) openLangPopover(); else closeLangPopover();
        }
        if (action === "select-language") {
            const lang = actionEl.dataset.lang;
            if (lang) applyLanguageSelection(lang, actionEl);
        }
        if (action === "select-language-inline") {
            const lang = actionEl.dataset.lang;
            if (!lang) return;
            const popoverPill = document.querySelector(`.lang-pill[data-lang="${lang}"]`);
            applyLanguageSelection(lang, popoverPill instanceof HTMLElement ? popoverPill : null);
        }
        if (action === "example-query") {
            const query = actionEl.dataset.query;
            if (query && !appState.searchInFlight) {
                setInteractionMode("talk");
                appendMessageToChat("user", query);
                submitQuery(query);
                setTimeout(() => document.getElementById("conversation")?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 80);
            }
        }
        if (action === "scheme-eligibility") {
            const role = actionEl.dataset.role || "farmer";
            const scheme = actionEl.dataset.scheme || "";
            setInteractionMode("finder");
            const roleInput = document.querySelector(`input[name="finderRole"][value="${role}"]`);
            if (roleInput) roleInput.checked = true;
            document.getElementById("finderPanel")?.scrollIntoView({ behavior: "smooth" });
            if (scheme) setStatusIndicator(`Checking ${scheme}…`, "orange");
        }
        if (action === "react") {
            const val = actionEl.dataset.value;
            const row = actionEl.closest(".reaction-row");
            if (!row) return;
            row.querySelectorAll(".reaction-btn").forEach((b) => b.classList.remove("reaction-selected"));
            actionEl.classList.add("reaction-selected");
            _sendFeedback(val, row.dataset.query || "", row.dataset.answer || "");
            if (val === "up") {
                triggerConfetti(actionEl);
                if (!row.querySelector(".reaction-wa-btn")) {
                    const answer = row.dataset.answer || "";
                    const shareText = `SahayakSetu (सहायक सेतु) found this:\n\n${answer.slice(0, 200)}…\n\nAsk about govt schemes: https://sahayaksetu.vercel.app`;
                    const wa = document.createElement("a");
                    wa.className = "reaction-wa-btn";
                    wa.href = `https://wa.me/?text=${encodeURIComponent(shareText)}`;
                    wa.target = "_blank";
                    wa.rel = "noopener noreferrer";
                    wa.textContent = "📱 Share";
                    row.appendChild(wa);
                }
            }
        }
    });

    const input = document.getElementById("textInput");
    if (input) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) handleTextSubmit();
        });
    }

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", (e) => {
            e.preventDefault();
            const t = document.querySelector(anchor.getAttribute("href"));
            if (t) t.scrollIntoView({ behavior: "smooth" });
        });
    });

    document.addEventListener("keydown", (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "d") {
            event.preventDefault();
            toggleDebugDrawer();
        }
        if (event.key === "Escape") {
            toggleDebugDrawer(false);
            closeLangPopover();
        }
    });
}

function bootstrap() {
    populateStateSelect();
    initialiseVapiSDK();
    wireSchemeSheet();
    wireDomEvents();
    decorateSchemeCards();
    switchSidebarTab("trust");
    initSidebarSample();
    initLastQueryBanner();
    document.getElementById("schemeSheet")?.setAttribute("inert", "");
    document.getElementById("debugDrawer")?.setAttribute("inert", "");

    if (window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = () => { window.speechSynthesis.getVoices(); };
    }
    const hasSavedPref = Boolean(localStorage.getItem("sahayak_selected_language"));
    const initialLang = hasSavedPref ? appState.selectedLanguage : detectBrowserLanguage();
    applyLanguageSelection(
        initialLang,
        document.querySelector(`.lang-pill[data-lang="${initialLang}"]`) || document.querySelector(".lang-pill"),
    );
}

document.addEventListener("DOMContentLoaded", bootstrap);
