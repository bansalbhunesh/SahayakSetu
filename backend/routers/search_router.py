import asyncio
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


def _ndjson_line(obj: dict) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, default=str) + "\n").encode("utf-8")


async def _search_ndjson_stream(search_request: SearchRequest):
    """NDJSON: meta, optional ``token`` lines during LLM generation, then ``complete`` or ``error``."""
    meta = {"type": "meta", "trace_id": trace_id_var.get()}
    yield _ndjson_line(meta)
    q: asyncio.Queue[dict[str, object]] = asyncio.Queue()

    async def emit(ev: dict[str, object]) -> None:
        await q.put(ev)

    task = asyncio.create_task(execute_search(search_request, stream_emit=emit))
    while True:
        if task.done():
            while True:
                try:
                    ev = q.get_nowait()
                except asyncio.QueueEmpty:
                    break
                yield _ndjson_line(ev)
            break
        try:
            ev = await asyncio.wait_for(q.get(), timeout=0.1)
        except asyncio.TimeoutError:
            continue
        yield _ndjson_line(ev)
    try:
        result = task.result()
    except HTTPException as he:
        yield _ndjson_line({"type": "error", "status_code": he.status_code, "detail": he.detail})
        return
    yield _ndjson_line({"type": "complete", "data": result.model_dump(mode="json")})


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
