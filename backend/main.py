"""FastAPI application factory — wiring only."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import (
    CHAT_COMPLETIONS_SECRET,
    CHAT_MODEL,
    GROQ_API_KEY,
    MODERATION_STRICT,
    QDRANT_URL,
)
from backend.routers import health_router, search_router, voice_router


def create_app() -> FastAPI:
    app = FastAPI(title="SahayakSetu API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router.router)
    app.include_router(search_router.router)
    app.include_router(voice_router.router)

    @app.on_event("startup")
    async def startup_event():
        print("\n[STARTUP] SahayakSetu - Intelligence Activated")
        print(f"   Primary: {CHAT_MODEL}")
        print(f"   Fallback: {'Groq-Llama-3.3' if GROQ_API_KEY else 'None'}")
        print(f"   RAG: Qdrant @ {QDRANT_URL[:20]}...")
        print("   --- Policy ---")
        if MODERATION_STRICT:
            print("   MODERATION_STRICT: on (classifier errors → block)")
        else:
            print("   MODERATION_STRICT: off (classifier errors → allow; use on in production)")
        if CHAT_COMPLETIONS_SECRET:
            print("   /chat/completions: auth enabled (Bearer or X-SahayakSetu-Key)")
        else:
            print("   /chat/completions: auth disabled — set CHAT_COMPLETIONS_SECRET in production")

    return app


app = create_app()
