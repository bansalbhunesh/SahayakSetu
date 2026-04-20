import { SESSION_USER_ID_KEY } from "./constants.js";

export const appState = {
    vapiInstance: null,
    isVoiceCallActive: false,
    selectedLanguage: "hi-IN",
    sessionUserId: localStorage.getItem(SESSION_USER_ID_KEY) || "",
    sessionSchemeNames: new Set(),
    currentSheetScheme: "",
};

export function setSessionUserId(id) {
    appState.sessionUserId = id || "";
    if (id) {
        localStorage.setItem(SESSION_USER_ID_KEY, id);
    }
}
