export function setVoiceButtonState(active) {
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

let activeRecognition = null;

export function stopBrowserSpeechRecognition() {
    if (!activeRecognition) return;
    try {
        activeRecognition.stop();
    } catch (_) {
        /* ignore */
    }
}

export function speakResponseText(text, selectedLanguage, options = {}) {
    const { onStart, onEnd } = options;
    if (!text || !("speechSynthesis" in window)) {
        onEnd?.();
        return;
    }
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

    utterance.onstart = () => onStart?.();
    utterance.onend = () => onEnd?.();
    utterance.onerror = () => onEnd?.();

    window.speechSynthesis.speak(utterance);
}

export function startBrowserSpeechFallback({
    selectedLanguage,
    onUserText,
    onStart,
    onStop,
    continuous = false,
    onInterim,
} = {}) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        return false;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = selectedLanguage;
    recognition.continuous = Boolean(continuous);
    recognition.interimResults = Boolean(continuous);

    const resetUI = () => {
        activeRecognition = null;
        onStop();
    };

    if (!continuous) {
        recognition.onresult = (event) => {
            const query = event.results[0][0].transcript;
            onUserText(query);
            resetUI();
        };
        recognition.onend = resetUI;
        recognition.onerror = resetUI;
    } else {
        let finalBuf = "";
        let lastLive = "";
        recognition.onresult = (event) => {
            let interim = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const res = event.results[i];
                const piece = (res[0] && res[0].transcript) || "";
                if (res.isFinal) finalBuf += piece;
                else interim += piece;
            }
            lastLive = (finalBuf + interim).trim();
            if (onInterim) onInterim(lastLive);
        };
        recognition.onend = () => {
            const q = finalBuf.trim() || lastLive.trim();
            if (q) onUserText(q);
            resetUI();
        };
        recognition.onerror = () => {
            const q = finalBuf.trim() || lastLive.trim();
            if (q) onUserText(q);
            resetUI();
        };
    }

    activeRecognition = recognition;
    try {
        recognition.start();
    } catch {
        activeRecognition = null;
        return false;
    }
    onStart();
    return true;
}
