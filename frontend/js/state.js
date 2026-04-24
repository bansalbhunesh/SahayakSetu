import { SESSION_USER_ID_KEY } from "./constants.js";

const LANGUAGE_PREF_KEY = "sahayak_selected_language";

export const appState = {
    /** Prevents overlapping /api/search calls from double-submit or voice+text races. */
    searchInFlight: false,
    vapiInstance: null,
    isVoiceCallActive: false,
    /** True when using Web Speech (not Vapi); used so Stop targets the right transport. */
    browserRecognitionActive: false,
    selectedLanguage: localStorage.getItem(LANGUAGE_PREF_KEY) || "hi-IN",
    sessionUserId: localStorage.getItem(SESSION_USER_ID_KEY) || "",
    sessionSchemeNames: new Set(),
    currentSheetScheme: "",
    lastRetrievalDebug: null,
    lastTraceId: null,
    /** Last structured profile from Eligibility Finder (sent with /api/search). */
    lastFinderProfile: null,
};

export function setSessionUserId(id) {
    appState.sessionUserId = id || "";
    if (id) {
        localStorage.setItem(SESSION_USER_ID_KEY, id);
    }
}

export function setSelectedLanguage(lang) {
    appState.selectedLanguage = lang || "hi-IN";
    localStorage.setItem(LANGUAGE_PREF_KEY, appState.selectedLanguage);
}
