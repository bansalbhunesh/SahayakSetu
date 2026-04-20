from fastapi import APIRouter

from backend.config import CHAT_MODEL, SIMILARITY_THRESHOLD

router = APIRouter(tags=["health"])


@router.get("/health")
def handle_health():
    return {"status": "online", "model": CHAT_MODEL, "threshold": SIMILARITY_THRESHOLD}


@router.get("/")
def handle_root():
    return {"status": "SahayakSetu Backend Online", "model": CHAT_MODEL}
