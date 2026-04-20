from fastapi import APIRouter, HTTPException, Request

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
