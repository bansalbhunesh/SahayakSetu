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

export function speakResponseText(text, selectedLanguage) {
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

export function startBrowserSpeechFallback({ selectedLanguage, onUserText, onStart, onStop }) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        return false;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = selectedLanguage;
    recognition.start();
    onStart();

    const resetUI = () => {
        onStop();
    };

    recognition.onresult = (event) => {
        const query = event.results[0][0].transcript;
        onUserText(query);
        resetUI();
    };
    recognition.onend = resetUI;
    recognition.onerror = resetUI;
    return true;
}
