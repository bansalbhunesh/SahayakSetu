"""Environment configuration and client singletons."""

from __future__ import annotations

import os

import google.generativeai as genai
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL", "https://sahayaksetu-backend-3kxl.onrender.com")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.0-flash")
# If set, /chat/completions requires Authorization: Bearer <secret> or X-SahayakSetu-Key: <secret>
CHAT_COMPLETIONS_SECRET = os.getenv("CHAT_COMPLETIONS_SECRET", "").strip()


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None or not str(v).strip():
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


# True: moderation JSON/call failures block (fail-closed). False: fail-open (local dev).
MODERATION_STRICT = _env_bool("MODERATION_STRICT", False)

QDRANT_COLLECTION = "sahayak_schemes"
SIMILARITY_THRESHOLD = 0.2
RAG_VECTOR_QUERY_LIMIT = 5
# Adaptive floor: rejects very weak vector neighbours (junk) while tracking threshold changes.
NEAR_MISS_SCORE_FLOOR = SIMILARITY_THRESHOLD * 0.4
NEAR_MISS_MAX = 2
HISTORY_WINDOW = 20
MAX_SESSION_STORE_SIZE = 500
EVICT_COUNT = 100
LLM_HISTORY_MESSAGE_LIMIT = 4

if not QDRANT_URL or not GEMINI_API_KEY:
    raise RuntimeError(
        "Missing required env vars. "
        f"QDRANT_URL={'set' if QDRANT_URL else 'MISSING'}, "
        f"GEMINI_API_KEY={'set' if GEMINI_API_KEY else 'MISSING'}"
    )

qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
qdrant_client.set_model("BAAI/bge-small-en-v1.5")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel(CHAT_MODEL)

groq_client: OpenAI | None = None
if GROQ_API_KEY:
    groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
