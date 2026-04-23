from fastapi import APIRouter, HTTPException

from backend.config import CHAT_MODEL, SIMILARITY_THRESHOLD
from backend.services.dependency_health import readiness_snapshot

router = APIRouter(tags=["health"])


@router.get("/health")
def handle_health():
    return {"status": "online", "model": CHAT_MODEL, "threshold": SIMILARITY_THRESHOLD}


@router.get("/ready")
async def handle_ready():
    snapshot = await readiness_snapshot()
    if not snapshot["ready"]:
        raise HTTPException(status_code=503, detail=snapshot)
    return snapshot


@router.get("/ping")
def handle_ping():
    return "pong"


@router.get("/")
def handle_root():
    return {"status": "SahayakSetu Backend Online", "model": CHAT_MODEL}
