"""Qdrant retrieval — single responsibility for vector search."""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.config import (
    HYBRID_KEYWORD_WEIGHT,
    NEAR_MISS_MAX,
    NEAR_MISS_SCORE_FLOOR,
    QDRANT_COLLECTION,
    RAG_VECTOR_CANDIDATE_LIMIT,
    RAG_VECTOR_QUERY_LIMIT,
    qdrant_client,
)


@dataclass
class SearchResult:
    scheme_name: str
    document: str
    score: float
    apply_link: str | None = None
    source: str | None = None
    source_id: str | None = None
    vector_score: float = 0.0
    keyword_score: float = 0.0
    blended_score: float = 0.0


def search_schemes(query: str, limit: int = 3) -> list[SearchResult]:
    raw_results = qdrant_client.query(
        collection_name=QDRANT_COLLECTION,
        query_text=query,
        limit=limit,
    )
    return [
        SearchResult(
            scheme_name=result.metadata.get("scheme", "Scheme"),
            document=result.document,
            score=result.score,
            apply_link=result.metadata.get("apply_link"),
            source=result.metadata.get("source"),
            vector_score=float(result.score),
            keyword_score=0.0,
            blended_score=float(result.score),
        )
        for result in raw_results
    ]


def filter_by_threshold(results: list[SearchResult], threshold: float) -> list[SearchResult]:
    return [result for result in results if result.score > threshold]


def _query_tokens(text: str) -> set[str]:
    # Language-agnostic-ish tokenization: keep unicode word chars, strip tiny tokens.
    toks = re.findall(r"\w+", (text or "").lower(), flags=re.UNICODE)
    return {t for t in toks if len(t) > 2}


def _keyword_overlap_score(query: str, document: str) -> float:
    q = _query_tokens(query)
    if not q:
        return 0.0
    d = _query_tokens(document)
    if not d:
        return 0.0
    score = len(q & d) / (len(q) + 1e-5)
    q_text = (query or "").strip().lower()
    d_text = (document or "").lower()
    if q_text and q_text in d_text:
        score += 0.2
    return max(0.0, min(1.0, score))


def _normalize(scores: list[float]) -> list[float]:
    if not scores:
        return []
    min_s = min(scores)
    max_s = max(scores)
    if max_s - min_s == 0:
        return [0.5 for _ in scores]
    return [(s - min_s) / (max_s - min_s) for s in scores]


def _hybrid_weight_for_query(query: str, base_weight: float) -> float:
    tokens = (query or "").split()
    query_weight = 0.25
    if len(tokens) <= 3:
        query_weight = 0.5
    elif any(ch.isdigit() for ch in (query or "")):
        query_weight = 0.4
    # Blend operator tune and query-adaptive heuristic.
    return max(0.0, min(1.0, (max(0.0, min(1.0, base_weight)) + query_weight) / 2.0))


def _dedupe_by_scheme(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for r in results:
        key = (r.scheme_name or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    return deduped


def _hybrid_rerank(query: str, results: list[SearchResult]) -> list[SearchResult]:
    """
    Lightweight rerank: blend vector score with keyword overlap.
    score = (1-w)*vector + w*keyword, where w defaults to 0.3.
    """
    if not results:
        return []
    weight = _hybrid_weight_for_query(query, HYBRID_KEYWORD_WEIGHT)
    vector_raw = [float(r.vector_score or r.score) for r in results]
    keyword_raw = [_keyword_overlap_score(query, r.document or "") for r in results]
    vector_norm = _normalize(vector_raw)
    keyword_norm = _normalize(keyword_raw)

    reranked: list[SearchResult] = []
    for i, r in enumerate(results):
        blended = ((1.0 - weight) * vector_norm[i]) + (weight * keyword_norm[i])
        reranked.append(
            SearchResult(
                scheme_name=r.scheme_name,
                document=r.document,
                score=blended,
                apply_link=r.apply_link,
                source=r.source,
                source_id=r.source_id,
                vector_score=vector_norm[i],
                keyword_score=keyword_norm[i],
                blended_score=blended,
            )
        )
    reranked.sort(key=lambda x: x.score, reverse=True)
    return _dedupe_by_scheme(reranked)


def confidence_label_for_score(score: float) -> str:
    """Human-readable retrieval confidence (vector similarity — not legal eligibility proof)."""
    if score > 0.7:
        return "Strong match (based on available data)"
    if score > 0.4:
        return "Moderate match"
    return "Low confidence"


def cta_label_for_score(score: float) -> str:
    """Primary action on official portal link — stronger CTA only when retrieval is confident."""
    return "Apply Now" if score > 0.7 else "Check Eligibility"


def _result_key(result: SearchResult) -> tuple[str, str]:
    return (result.scheme_name, result.document)


def retrieve_for_rag(
    query: str,
    similarity_threshold: float,
    *,
    use_hybrid: bool = False,
) -> tuple[list[SearchResult], list[SearchResult], str, str]:
    """
    Top confident matches (up to 3) plus up to two additional high-ranked hits
    for near-miss / gap analysis (not above threshold or not in top-3 set).
    """
    candidate_limit = RAG_VECTOR_CANDIDATE_LIMIT if use_hybrid else RAG_VECTOR_QUERY_LIMIT
    raw_results = search_schemes(query, limit=candidate_limit)
    if use_hybrid:
        raw_results = _hybrid_rerank(query, raw_results)
    else:
        raw_results = _dedupe_by_scheme(raw_results)
    relevant_results = filter_by_threshold(raw_results, similarity_threshold)[:4]
    rel_keys = {_result_key(r) for r in relevant_results}

    near_miss_results: list[SearchResult] = []
    for result in raw_results:
        if _result_key(result) in rel_keys:
            continue
        if result.score < NEAR_MISS_SCORE_FLOOR:
            continue
        near_miss_results.append(result)
        if len(near_miss_results) >= NEAR_MISS_MAX:
            break

    for i, result in enumerate(relevant_results, start=1):
        result.source_id = f"S{i}"
    for i, result in enumerate(near_miss_results, start=1):
        result.source_id = f"N{i}"

    context = build_context_from_results(relevant_results)
    if near_miss_results:
        near_header = (
            "Lower-confidence retrieval matches (possible near-misses — compare user profile "
            "to eligibility; mention only real gaps, do not invent rules):\n\n"
        )
        near_context = near_header + build_context_from_results(near_miss_results)
    else:
        near_context = ""

    return relevant_results, near_miss_results, context, near_context


def build_retrieval_debug(query: str, results: list[SearchResult]) -> dict:
    return {
        "query": query,
        "top_results": [
            {
                "scheme": r.scheme_name,
                "vector": round(float(r.vector_score or 0.0), 4),
                "keyword": round(float(r.keyword_score or 0.0), 4),
                "blended": round(float(r.blended_score or r.score), 4),
                "final_score": round(float(r.score), 4),
            }
            for r in results[:5]
        ],
    }


def truncate_at_word_boundary(text: str, max_len: int) -> str:
    """Prefer ending on a full word when truncating (avoids 'elig…' mid-token)."""
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rstrip()
    if " " in cut:
        head = cut.rsplit(" ", 1)[0]
        base = head if head else cut
    else:
        base = cut
    # Drop trailing sentence punctuation so we never produce "farmers.…"
    base = re.sub(r"[.,;:]\s*$", "", base).rstrip()
    if not base:
        return "…"
    return base + "…"


def preview_snippet_from_document(document: str, max_len: int = 140) -> str:
    """One-line snippet for UI tooltips (not legal advice)."""
    snippet = (document or "").replace("\n", " ").strip()
    snippet = re.sub(r"\s+([.,;:])", r"\1", snippet)
    return truncate_at_word_boundary(snippet, max_len)


def format_citation_index(results: list[SearchResult]) -> str:
    """Numbered lines for in-answer [1], [2] citations — order must match API `sources`."""
    if not results:
        return ""
    lines: list[str] = []
    for i, result in enumerate(results, start=1):
        snippet = (result.document or "").replace("\n", " ").strip()
        snippet = re.sub(r"\s+([.,;:])", r"\1", snippet)
        snippet = truncate_at_word_boundary(snippet, 180)
        lines.append(f"[{i}] {result.scheme_name}: {snippet}")
    return "\n".join(lines)


def format_source_index(results: list[SearchResult]) -> str:
    """Strict source tags for anti-hallucination JSON contracts."""
    if not results:
        return ""
    lines: list[str] = []
    for i, result in enumerate(results, start=1):
        sid = result.source_id or f"S{i}"
        snippet = (result.document or "").replace("\n", " ").strip()
        snippet = re.sub(r"\s+([.,;:])", r"\1", snippet)
        snippet = truncate_at_word_boundary(snippet, 220)
        lines.append(f"[{sid}] {result.scheme_name}: {snippet}")
    return "\n".join(lines)


def build_context_from_results(results: list[SearchResult]) -> str:
    """RAG context text including verified URLs from metadata (never LLM-invented)."""
    parts: list[str] = []
    for i, result in enumerate(results, start=1):
        sid = result.source_id or f"S{i}"
        chunk = result.document
        extras: list[str] = []
        if result.apply_link:
            extras.append(f"Official apply / learn more: {result.apply_link}")
        if result.source:
            extras.append(f"Scheme catalogue (MyScheme / reference): {result.source}")
        extras.append("Freshness date: unknown")
        if extras:
            chunk = f"{chunk}\n" + "\n".join(extras)
        parts.append(f"[{sid}]\n{chunk}")
    return "\n\n".join(parts)
