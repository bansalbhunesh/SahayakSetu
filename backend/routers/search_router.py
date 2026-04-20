from fastapi import APIRouter, HTTPException

from backend.config import SIMILARITY_THRESHOLD
from backend.models.request_models import SearchRequest
from backend.models.response_models import SchemeSource, SearchResponse
from backend.services import llm_service, moderation_service, retrieval_service, session_service

router = APIRouter(tags=["search"])


@router.post("/api/search")
async def handle_search(search_request: SearchRequest):
    try:
        moderation = await moderation_service.check(
            search_request.query,
            search_request.language,
        )
        if not moderation.allowed:
            return SearchResponse(
                answer=None,
                provider=None,
                sources=[],
                moderation_blocked=True,
                moderation_category=moderation.category,
                redirect_message=moderation.redirect_message
                or "Please ask about Indian government schemes or civic services.",
            )

        relevant_results, near_miss_results, context, near_miss_context = (
            retrieval_service.retrieve_for_rag(search_request.query, SIMILARITY_THRESHOLD)
        )

        citation_index_block = retrieval_service.format_citation_index(relevant_results)

        history = session_service.get_history(search_request.user_id)
        messages = llm_service.build_messages(
            search_request.query,
            context,
            history,
            search_request.language,
            near_miss_context=near_miss_context,
            citation_index_block=citation_index_block,
        )
        raw_text, provider = await llm_service.generate(messages)

        answer_main, reasoning_why, near_miss_text = llm_service.parse_structured_response(raw_text)
        max_n = len(relevant_results)
        answer_main = llm_service.validate_citations_in_answer(answer_main, max_n)
        answer_main = llm_service.dedupe_citations(answer_main)
        if reasoning_why:
            reasoning_why = llm_service.dedupe_citations(
                llm_service.validate_citations_in_answer(reasoning_why, max_n)
            ).strip() or None
        if near_miss_text:
            near_miss_text = llm_service.dedupe_citations(
                llm_service.validate_citations_in_answer(near_miss_text, max_n)
            ).strip() or None
        session_text = llm_service.compose_session_assistant_text(
            answer_main,
            reasoning_why,
            near_miss_text,
        )
        session_service.append(search_request.user_id, search_request.query, session_text)

        sources = [
            SchemeSource(
                scheme=result.scheme_name,
                score=result.score,
                apply_link=result.apply_link,
                source=result.source,
                confidence_label=retrieval_service.confidence_label_for_score(result.score),
                cta_label=retrieval_service.cta_label_for_score(result.score),
                preview_text=retrieval_service.preview_snippet_from_document(result.document),
            )
            for result in relevant_results
        ]
        near_miss_sources = [
            SchemeSource(
                scheme=result.scheme_name,
                score=result.score,
                apply_link=result.apply_link,
                source=result.source,
                confidence_label=retrieval_service.confidence_label_for_score(result.score),
                cta_label=retrieval_service.cta_label_for_score(result.score),
                preview_text=retrieval_service.preview_snippet_from_document(result.document),
            )
            for result in near_miss_results
        ]
        return SearchResponse(
            answer=answer_main,
            provider=provider,
            sources=sources,
            moderation_blocked=False,
            redirect_message=None,
            reasoning_why=reasoning_why,
            near_miss_text=near_miss_text,
            near_miss_sources=near_miss_sources,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
