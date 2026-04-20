export const VAPI_PUBLIC_KEY = "c0fcebfd-1570-4dfa-8b47-9280bfbaaaf8";
export const VAPI_ASSISTANT_ID = "bd9bb2ff-9b1d-4f6a-86a2-11dfda391550";

export const BACKEND_URL =
    window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
        ? "http://localhost:8000"
        : "https://sahayaksetu-backend-3kxl.onrender.com";

export const SESSION_USER_ID_KEY = "sahayak_session_user_id";

/** Web Speech: continuous listen + interim captions (Alexa-style). */
export const USE_CONTINUOUS_VOICE = true;

export const INDIAN_STATES = [
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

export const LANGUAGE_LABELS = {
    "hi-IN": "हिन्दी",
    "kn-IN": "ಕನ್ನಡ",
    "ta-IN": "தமிழ்",
    "te-IN": "తెలుగు",
    "bn-IN": "বাংলা",
    "en-IN": "English",
};

export const LANGUAGE_FLAGS = {
    "hi-IN": "🇮🇳",
    "kn-IN": "🇮🇳",
    "ta-IN": "🇮🇳",
    "te-IN": "🇮🇳",
    "bn-IN": "🇮🇳",
    "en-IN": "🇮🇳",
};
