import { BACKEND_URL, INDIAN_STATES, VAPI_ASSISTANT_ID, VAPI_PUBLIC_KEY } from "./constants.js";
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
import { appState, setSessionUserId } from "./state.js";
import { setVoiceButtonState, speakResponseText, startBrowserSpeechFallback } from "./voice.js";

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
}

function applyLanguageSelection(lang, el) {
    appState.selectedLanguage = lang;
    document.querySelectorAll(".lang-pill").forEach((pill) => pill.classList.remove("active"));
    if (el) el.classList.add("active");
    updateLanguageUI(lang);
}

function handleEligibilitySubmit(event) {
    event.preventDefault();
    const state = document.getElementById("finderState")?.value || "";
    const role = document.querySelector('input[name="finderRole"]:checked')?.value || "citizen";
    const income = document.querySelector('input[name="finderIncome"]:checked')?.value || "unspecified";
    const query = `Show government welfare schemes for a ${role} in ${state} with annual family income ${income}. Summarise the most relevant central or state schemes and how to apply.`;
    submitQuery(query);
}

function triggerSchemeQuery(query) {
    appendMessageToChat("user", query);
    submitQuery(query);
}

function setSessionFromPayload(payload) {
    if (payload.session_user_id) {
        setSessionUserId(payload.session_user_id);
    }
}

function switchSidebarTab(tabName = "trust") {
    const tabs = document.querySelectorAll('.sidebar-tab[data-tab]');
    const panels = document.querySelectorAll('.sidebar-panel[data-panel]');
    tabs.forEach((tab) => {
        const active = tab.dataset.tab === tabName;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-selected", String(active));
    });
    panels.forEach((panel) => {
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
    const confidenceLabel =
        confidence === "high" ? "Verified signal" : confidence === "medium" ? "Partial signal" : "Needs clarification";
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

async function submitQuery(query) {
    setStatusIndicator("Thinking...", "orange");
    showTypingIndicator();
    try {
        const resp = await fetch(`${BACKEND_URL}/api/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query,
                user_id: appState.sessionUserId,
                language: appState.selectedLanguage,
            }),
        });
        removeTypingIndicator();
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const payload = await resp.json();
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
        });
        if (payload.retrieval_debug) {
            appState.lastRetrievalDebug = payload.retrieval_debug;
            appState.lastTraceId = resp.headers.get("X-Trace-Id") || "n/a";
            renderDebugDrawer();
        }
        sources.forEach((s) => s.scheme && appState.sessionSchemeNames.add(s.scheme));
        (payload.near_miss_sources || []).forEach((s) => s.scheme && appState.sessionSchemeNames.add(s.scheme));
        renderSchemePills(appState.sessionSchemeNames);
        updateEvidencePanel(payload);
        switchSidebarTab("evidence");
        pulseEvidenceTab();

        if (!appState.vapiInstance || !appState.isVoiceCallActive) {
            speakResponseText(stripCitationMarkers(payload.answer), appState.selectedLanguage);
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

function renderDebugDrawer() {
    const host = document.getElementById("debugDrawerContent");
    const trace = document.getElementById("debugTraceId");
    if (!host || !trace) return;
    trace.textContent = `Trace ID: ${appState.lastTraceId || "n/a"}`;
    host.textContent = appState.lastRetrievalDebug
        ? JSON.stringify(appState.lastRetrievalDebug, null, 2)
        : "No retrieval debug payload yet.";
}

function toggleDebugDrawer(forceOpen = null) {
    const drawer = document.getElementById("debugDrawer");
    if (!drawer) return;
    const isOpen = drawer.classList.contains("open");
    const open = forceOpen === null ? !isOpen : Boolean(forceOpen);
    drawer.classList.toggle("open", open);
    drawer.setAttribute("aria-hidden", String(!open));
}

function decorateSchemeCards() {
    document.querySelectorAll(".scheme-card").forEach((card) => {
        const trigger = card.querySelector(".scheme-card-trigger");
        const ministry = trigger?.getAttribute("data-ministry") || "";
        const lower = ministry.toLowerCase();
        if (lower.includes("finance")) card.dataset.ministry = "finance";
        else if (lower.includes("health")) card.dataset.ministry = "health";
        else if (lower.includes("housing") || lower.includes("urban")) card.dataset.ministry = "housing";
        else if (lower.includes("agriculture") || lower.includes("farm")) card.dataset.ministry = "agri";
        else card.dataset.ministry = "default";
    });
}

function handleTextSubmit() {
    const input = document.getElementById("textInput");
    const query = input?.value.trim();
    if (!query) return;
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
            setStatusIndicator("Ready", "green");
        } else {
            setTimeout(initialiseVapiSDK, 500);
        }
    } catch {
        setStatusIndicator("Voice unavailable", "yellow");
    }
}

function bindVapiEventHandlers() {
    if (!appState.vapiInstance) return;
    appState.vapiInstance.on("call-start", () => {
        appState.isVoiceCallActive = true;
        setVoiceButtonState(true);
        setStatusIndicator("Listening...", "green");
    });
    appState.vapiInstance.on("call-end", () => {
        appState.isVoiceCallActive = false;
        setVoiceButtonState(false);
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
        if (appState.vapiInstance) appState.vapiInstance.stop();
        appState.isVoiceCallActive = false;
        setVoiceButtonState(false);
        setStatusIndicator("Ready", "green");
        return;
    }
    if (appState.vapiInstance && VAPI_ASSISTANT_ID !== "YOUR_VAPI_ASSISTANT_ID") {
        appState.vapiInstance.start(VAPI_ASSISTANT_ID);
        return;
    }
    const started = startBrowserSpeechFallback({
        selectedLanguage: appState.selectedLanguage,
        onStart: () => {
            setStatusIndicator("Listening...", "green");
            setVoiceButtonState(true);
            appState.isVoiceCallActive = true;
        },
        onStop: () => {
            setVoiceButtonState(false);
            setStatusIndicator("Ready", "green");
            appState.isVoiceCallActive = false;
        },
        onUserText: (query) => {
            appendMessageToChat("user", query);
            submitQuery(query);
        },
    });
    if (!started) {
        appendMessageToChat("assistant", "Sorry, voice recognition is not supported in this browser.", {
            variant: "error",
        });
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
    if (applyLink) {
        applyLink.classList.toggle("hidden", !applyUrl);
        if (applyUrl) applyLink.href = applyUrl;
    }
    if (sourceLink) {
        sourceLink.classList.toggle("hidden", !sourceUrl);
        if (sourceUrl) sourceLink.href = sourceUrl;
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
        const query = `Tell me more about ${appState.currentSheetScheme} and how I can apply.`;
        closeSchemeSheet();
        triggerSchemeQuery(query);
    };
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
        if (action === "select-language") {
            const lang = actionEl.dataset.lang;
            if (lang) applyLanguageSelection(lang, actionEl);
        }
    });

    const input = document.getElementById("textInput");
    if (input) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") handleTextSubmit();
        });
    }

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", (e) => {
            e.preventDefault();
            const target = document.querySelector(anchor.getAttribute("href"));
            if (target) target.scrollIntoView({ behavior: "smooth" });
        });
    });

    document.addEventListener("keydown", (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "d") {
            event.preventDefault();
            toggleDebugDrawer();
        }
        if (event.key === "Escape") toggleDebugDrawer(false);
    });
}

function bootstrap() {
    populateStateSelect();
    initialiseVapiSDK();
    wireSchemeSheet();
    wireDomEvents();
    decorateSchemeCards();
    switchSidebarTab("trust");

    if (window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.getVoices();
        };
    }
    applyLanguageSelection(
        appState.selectedLanguage,
        document.querySelector(`.lang-pill[data-lang="${appState.selectedLanguage}"]`) ||
            document.querySelector(".lang-pill"),
    );
}

document.addEventListener("DOMContentLoaded", bootstrap);
