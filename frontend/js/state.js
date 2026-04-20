import { SESSION_USER_ID_KEY } from "./constants.js";

export const appState = {
    vapiInstance: null,
    isVoiceCallActive: false,
    selectedLanguage: "hi-IN",
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
