"""FastAPI application factory — wiring + safety middleware."""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.config import (
    ALLOWED_ORIGINS,
    ALLOWED_ORIGIN_REGEX,
    CHAT_MODEL,
    ENV,
    FRONTEND_ORIGIN,
    GROQ_API_KEY,
    MODERATION_STRICT,
    QDRANT_URL,
)
from backend.logging_setup import setup_logging, trace_id_var
from backend.rate_limit import limiter
from backend.routers import health_router, search_router, voice_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    qdrant_preview = (QDRANT_URL or "")[:20] + ("..." if len(QDRANT_URL or "") > 20 else "")
    print("\n[STARTUP] SahayakSetu - Intelligence Activated")
    print(f"   Primary: {CHAT_MODEL}")
    print(f"   Fallback: {'Groq-Llama-3.3' if GROQ_API_KEY else 'None'}")
    print(f"   RAG: Qdrant @ {qdrant_preview}")
    print("   --- Policy ---")
    if MODERATION_STRICT:
        print("   MODERATION_STRICT: on (classifier errors -> block)")
    else:
        print("   MODERATION_STRICT: off (classifier errors -> allow; use on in production)")
    print(f"   ENV: {ENV}")
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="SahayakSetu API", lifespan=_lifespan)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS or [FRONTEND_ORIGIN],
        allow_origin_regex=ALLOWED_ORIGIN_REGEX or None,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-User-Id", "X-Trace-Id"],
        expose_headers=["X-Trace-Id"],
    )

    @app.middleware("http")
    async def trace_middleware(request: Request, call_next):
        trace_id = request.headers.get("x-trace-id") or uuid.uuid4().hex
        token = trace_id_var.set(trace_id)
        try:
            response = await call_next(request)
            response.headers["X-Trace-Id"] = trace_id
            return response
        finally:
            trace_id_var.reset(token)

    app.include_router(health_router.router)
    app.include_router(search_router.router)
    app.include_router(voice_router.router)

    @app.exception_handler(Exception)
    async def safe_exception_handler(request: Request, exc: Exception):
        ref = uuid.uuid4().hex[:8]
        logger.exception("unhandled_exception", extra={"path": request.url.path, "ref": ref})
        return JSONResponse(status_code=500, content={"detail": f"Internal error. Reference: {ref}"})

    return app


app = create_app()
