"""Environment configuration and client singletons."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient

try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types
except Exception:  # pragma: no cover - environment-dependent import
    google_genai = None
    google_genai_types = None

legacy_genai = None
if google_genai is None or google_genai_types is None:
    try:
        import google.generativeai as legacy_genai
    except Exception:  # pragma: no cover - environment-dependent import
        legacy_genai = None

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ENV = os.getenv("ENV", "development").strip().lower()
BACKEND_URL = os.getenv("BACKEND_URL", "https://sahayaksetu-backend-3kxl.onrender.com")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://sahayak-setu.vercel.app")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", FRONTEND_ORIGIN).split(",")
    if origin.strip()
]
ALLOWED_ORIGIN_REGEX = os.getenv("ALLOWED_ORIGIN_REGEX", r"^https://[a-z0-9-]+\.vercel\.app$").strip()

# In development, automatically permit any localhost origin so the frontend
# served by a local file server or dev server can reach the API without CORS errors.
if ENV == "development":
    _local_origins = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]
    for _o in _local_origins:
        if _o not in ALLOWED_ORIGINS:
            ALLOWED_ORIGINS.append(_o)
    ALLOWED_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.0-flash")
VAPI_WEBHOOK_SECRET = os.getenv("VAPI_WEBHOOK_SECRET", "").strip()
# Signed-body timestamp skew (seconds). Mitigates replay of very old captured payloads.
VAPI_WEBHOOK_MAX_SKEW_S = int(os.getenv("VAPI_WEBHOOK_MAX_SKEW_S", "300"))


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None or not str(v).strip():
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


# True: moderation JSON/call failures block (fail-closed). False: fail-open (local dev).
MODERATION_STRICT = _env_bool("MODERATION_STRICT", False)
# If True, Vapi webhook JSON must include a parseable timestamp (strict integrations).
VAPI_WEBHOOK_REQUIRE_TIMESTAMP = _env_bool("VAPI_WEBHOOK_REQUIRE_TIMESTAMP", False)
# True enables structured JSON generation path for /api/search.
# Default ON in production to keep grounding verifier active.
LLM_JSON_MODE = _env_bool("LLM_JSON_MODE", ENV == "production")
# Enable lightweight hybrid retrieval: vector score + keyword overlap blend.
HYBRID_RETRIEVAL = _env_bool("HYBRID_RETRIEVAL", False)
DEBUG_RETRIEVAL = _env_bool("DEBUG_RETRIEVAL", False)

QDRANT_COLLECTION = "sahayak_schemes"
SIMILARITY_THRESHOLD = 0.2
RAG_VECTOR_QUERY_LIMIT = 8
RAG_VECTOR_CANDIDATE_LIMIT = 12
HYBRID_KEYWORD_WEIGHT = float(os.getenv("HYBRID_KEYWORD_WEIGHT", "0.3"))
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
# Adaptive floor: rejects very weak vector neighbours (junk). Default 0.15 (panel tuning); override via env.
NEAR_MISS_SCORE_FLOOR = float(
    os.getenv("NEAR_MISS_SCORE_FLOOR", str(max(0.15, SIMILARITY_THRESHOLD * 0.4)))
)
NEAR_MISS_MAX = 2
HISTORY_WINDOW = 20
MAX_SESSION_STORE_SIZE = 500
EVICT_COUNT = 100
LLM_HISTORY_MESSAGE_LIMIT = 4
RETRIEVAL_SOFT_FLOOR = 0.35
RETRIEVAL_HARD_FLOOR = 0.55

# External call limits — tune via env in production.
LLM_CALL_TIMEOUT_S = float(os.getenv("LLM_CALL_TIMEOUT_S", "120"))
AGENT_PLAN_CALL_TIMEOUT_S = float(os.getenv("AGENT_PLAN_CALL_TIMEOUT_S", "90"))
MODERATION_CALL_TIMEOUT_S = float(os.getenv("MODERATION_CALL_TIMEOUT_S", "45"))
REWRITE_QUERY_TIMEOUT_S = float(os.getenv("REWRITE_QUERY_TIMEOUT_S", "30"))
API_RETRY_ATTEMPTS = int(os.getenv("API_RETRY_ATTEMPTS", "3"))
API_RETRY_BASE_DELAY_S = float(os.getenv("API_RETRY_BASE_DELAY_S", "0.4"))
API_RETRY_MAX_DELAY_S = float(os.getenv("API_RETRY_MAX_DELAY_S", "6.0"))
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "16000"))
MAX_QUERY_CHARS = int(os.getenv("MAX_QUERY_CHARS", "600"))

if not QDRANT_URL:
    raise RuntimeError(
        "Missing required env vars. QDRANT_URL=MISSING"
    )
if not (GEMINI_API_KEY or GROQ_API_KEY):
    raise RuntimeError("Missing required env vars. Provide GEMINI_API_KEY or GROQ_API_KEY.")

qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
qdrant_client.set_model(EMBEDDING_MODEL)

class _GeminiAdapter:
    """Unified generate_content adapter for google-genai and legacy SDK."""

    def __init__(self, model: str, api_key: str):
        self.model = model
        self._mode = None
        self._client: Any = None
        self._legacy_model: Any = None
        if google_genai is not None and google_genai_types is not None:
            self._client = google_genai.Client(api_key=api_key)
            self._mode = "google-genai"
        elif legacy_genai is not None:
            legacy_genai.configure(api_key=api_key)
            self._legacy_model = legacy_genai.GenerativeModel(model)
            self._mode = "legacy-generativeai"

    def generate_content(self, prompt: str, generation_config: dict[str, Any] | None = None):
        if self._mode == "google-genai":
            cfg = google_genai_types.GenerateContentConfig(**(generation_config or {}))
            return self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=cfg,
            )
        if self._mode == "legacy-generativeai":
            return self._legacy_model.generate_content(
                prompt,
                generation_config=generation_config,
            )
        raise RuntimeError("gemini_sdk_unavailable")

    def generate_content_stream(self, prompt: str, generation_config: dict[str, Any] | None = None):
        """Iterator of response chunks (incremental text in ``chunk.text`` where supported)."""
        if self._mode == "google-genai":
            cfg = google_genai_types.GenerateContentConfig(**(generation_config or {}))
            return self._client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config=cfg,
            )
        if self._mode == "legacy-generativeai":
            return self._legacy_model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True,
            )
        raise RuntimeError("gemini_sdk_unavailable")


gemini_model = None
if GEMINI_API_KEY:
    gemini_model = _GeminiAdapter(CHAT_MODEL, GEMINI_API_KEY)

groq_client: OpenAI | None = None
if GROQ_API_KEY:
    groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
