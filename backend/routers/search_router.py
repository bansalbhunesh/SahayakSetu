import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.logging_setup import trace_id_var
from backend.models.request_models import SearchRequest
from backend.models.response_models import SearchResponse
from backend.rate_limit import limiter
from backend.services.search_execution import execute_search

router = APIRouter(tags=["search"])


@router.post("/api/search")
@limiter.limit("10/minute;100/hour")
async def handle_search(request: Request, search_request: SearchRequest) -> SearchResponse:
    try:
        return await execute_search(search_request)
    except HTTPException:
        raise


async def _search_ndjson_stream(search_request: SearchRequest):
    """Minimal NDJSON stream: meta line + one complete payload (token streaming TBD)."""
    meta = {"type": "meta", "trace_id": trace_id_var.get()}
    yield (json.dumps(meta, ensure_ascii=False) + "\n").encode("utf-8")
    try:
        result = await execute_search(search_request)
        line = {
            "type": "complete",
            "data": result.model_dump(mode="json"),
        }
        yield (json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8")
    except HTTPException as he:
        err = {"type": "error", "status_code": he.status_code, "detail": he.detail}
        yield (json.dumps(err, ensure_ascii=False, default=str) + "\n").encode("utf-8")


@router.post("/api/search/stream")
@limiter.limit("10/minute;100/hour")
async def handle_search_stream(request: Request, search_request: SearchRequest):
    return StreamingResponse(
        _search_ndjson_stream(search_request),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
