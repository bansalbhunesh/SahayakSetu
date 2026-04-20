from fastapi import APIRouter, HTTPException, Request

from backend.config import (
    DEBUG_RETRIEVAL,
    HYBRID_RETRIEVAL,
    LLM_JSON_MODE,
    RETRIEVAL_HARD_FLOOR,
    RETRIEVAL_SOFT_FLOOR,
    SIMILARITY_THRESHOLD,
)
from backend.rate_limit import limiter
from backend.models.request_models import SearchRequest
from backend.models.response_models import SchemeSource, SearchResponse
from backend.services import (
    cache_service,
    grounding_service,
    llm_service,
    moderation_service,
    retrieval_service,
    session_service,
)

router = APIRouter(tags=["search"])


def _confidence_bucket(top_score: float) -> str:
    if top_score > 0.6:
        return "high"
    if top_score >= 0.4:
        return "medium"
    return "low"


def _query_type(query: str) -> str:
    tokens = (query or "").split()
    if len(tokens) <= 3:
        return "short"
    if any(ch.isdigit() for ch in (query or "")):
        return "numeric"
    return "detailed"


def _guided_fallback(language: str) -> tuple[str, str]:
    lang = (language or "").lower()
    if lang.startswith("hi"):
        return (
            "मुझे इसका सटीक मिलान नहीं मिला। मैं इसे बेहतर ढंग से ढूंढने में मदद कर सकता हूँ।",
            "कृपया अपना राज्य, वार्षिक आय और श्रेणी (किसान/छात्र/महिला आदि) बताएं।",
        )
    return (
        "I couldn't find an exact verified match yet. I can help refine this.",
        "Please share your state, annual income, and category (farmer/student/woman/etc.).",
    )


@router.post("/api/search")
@limiter.limit("10/minute;100/hour")
async def handle_search(request: Request, search_request: SearchRequest):
    try:
        raw_user_id, signed_user_id = session_service.resolve_user_id(search_request.user_id)
        cached = await cache_service.get(search_request.query, search_request.language)
        if cached:
            cached["session_user_id"] = signed_user_id
            return SearchResponse(**cached)

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

        original_query = (search_request.query or "").strip()
        if len(original_query) > 300:
            guided_answer, guided_next_step = _guided_fallback(search_request.language)
            qtype = _query_type(original_query)
            return SearchResponse(
                answer=guided_answer,
                provider="query-too-long",
                sources=[],
                moderation_blocked=False,
                redirect_message=None,
                reasoning_why=None,
                near_miss_text=None,
                near_miss_sources=[],
                session_user_id=signed_user_id,
                confidence="low",
                next_step=guided_next_step,
                query_debug={"original": original_query, "rewritten": original_query, "type": qtype},
            )

        qtype = _query_type(original_query)
        rewritten_query = original_query
        if len(original_query.split()) <= 5:
            rewritten_query = await llm_service.rewrite_query(original_query, search_request.language)
        query_debug = {
            "original": original_query,
            "rewritten": rewritten_query,
            "type": qtype,
        }
        relevant_results, near_miss_results, context, near_miss_context = (
            retrieval_service.retrieve_for_rag(
                rewritten_query,
                SIMILARITY_THRESHOLD,
                use_hybrid=HYBRID_RETRIEVAL,
            )
        )
        retrieval_debug = (
            retrieval_service.build_retrieval_debug(rewritten_query, relevant_results)
            if DEBUG_RETRIEVAL
            else None
        )

        citation_index_block = retrieval_service.format_citation_index(relevant_results)
        source_index_block = retrieval_service.format_source_index(relevant_results)

        fallback = grounding_service.fallback_text_for_language(search_request.language)
        guided_answer, guided_next_step = _guided_fallback(search_request.language)
        top_score = max((r.score for r in relevant_results), default=0.0)
        if not relevant_results:
            return SearchResponse(
                answer=guided_answer,
                provider="retrieval-empty",
                sources=[],
                moderation_blocked=False,
                redirect_message=None,
                reasoning_why=None,
                near_miss_text=None,
                near_miss_sources=[],
                session_user_id=signed_user_id,
                confidence="low",
                next_step=guided_next_step,
                retrieval_debug=retrieval_debug,
                query_debug=query_debug,
            )

        score_spread = top_score - min((r.score for r in relevant_results), default=top_score)
        if score_spread < 0.05 and top_score < RETRIEVAL_HARD_FLOOR:
            return SearchResponse(
                answer=guided_answer,
                provider="retrieval-ambiguous",
                sources=[],
                moderation_blocked=False,
                redirect_message=None,
                reasoning_why=None,
                near_miss_text=None,
                near_miss_sources=[],
                session_user_id=signed_user_id,
                confidence="low",
                next_step=guided_next_step,
                retrieval_debug=retrieval_debug,
                query_debug=query_debug,
            )

        if top_score < RETRIEVAL_SOFT_FLOOR:
            return SearchResponse(
                answer=guided_answer,
                provider="retrieval-soft-gate",
                sources=[],
                moderation_blocked=False,
                redirect_message=None,
                reasoning_why=None,
                near_miss_text=None,
                near_miss_sources=[],
                session_user_id=signed_user_id,
                confidence="low",
                next_step=guided_next_step,
                retrieval_debug=retrieval_debug,
                query_debug=query_debug,
            )

        used_today, daily_cap = await session_service.increment_daily_llm_counter()
        if used_today > daily_cap:
            raise HTTPException(
                status_code=503,
                detail="Service temporarily at capacity. Please try again later.",
            )

        history = await session_service.get_history(raw_user_id)
        messages = llm_service.build_messages(
            search_request.query,
            context,
            history,
            search_request.language,
            near_miss_context=near_miss_context,
            citation_index_block=citation_index_block,
            source_index_block=source_index_block,
            json_mode=LLM_JSON_MODE,
        )
        answer_main = fallback
        reasoning_why = near_miss_text = None
        provider = None
        if LLM_JSON_MODE:
            try:
                structured, provider = await llm_service.generate_json(messages)
                verified = grounding_service.verify(structured, relevant_results, fallback)
                answer_main = verified.answer or fallback
                cleaned = [x.strip() for x in verified.why_it_fits if x and x.strip()]
                reasoning_why = "\n".join(f"- {x}" for x in cleaned) if cleaned else None
                near_miss_text = (verified.near_miss or "").strip() or None
            except Exception:
                raw_text, provider = await llm_service.generate(messages)
                answer_main, reasoning_why, near_miss_text = llm_service.parse_structured_response(raw_text)
        else:
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
        await session_service.append(raw_user_id, search_request.query, session_text)

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
        response = SearchResponse(
            answer=answer_main,
            provider=provider,
            sources=sources,
            moderation_blocked=False,
            redirect_message=None,
            reasoning_why=reasoning_why,
            near_miss_text=near_miss_text,
            near_miss_sources=near_miss_sources,
            session_user_id=signed_user_id,
            confidence=_confidence_bucket(top_score),
            next_step=(
                guided_next_step
                if RETRIEVAL_SOFT_FLOOR <= top_score < RETRIEVAL_HARD_FLOOR
                else None
            ),
            retrieval_debug=retrieval_debug,
            query_debug=query_debug,
        )
        cached_payload = response.model_dump()
        cached_payload.pop("session_user_id", None)
        cached_payload.pop("retrieval_debug", None)
        cached_payload.pop("query_debug", None)
        await cache_service.set(search_request.query, search_request.language, cached_payload)
        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
