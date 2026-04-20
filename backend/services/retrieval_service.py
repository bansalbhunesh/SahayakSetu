"""Qdrant retrieval — single responsibility for vector search."""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.config import (
    NEAR_MISS_MAX,
    NEAR_MISS_SCORE_FLOOR,
    QDRANT_COLLECTION,
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
        )
        for result in raw_results
    ]


def filter_by_threshold(results: list[SearchResult], threshold: float) -> list[SearchResult]:
    return [result for result in results if result.score > threshold]


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


def retrieve_for_rag(query: str, similarity_threshold: float) -> tuple[list[SearchResult], list[SearchResult], str, str]:
    """
    Top confident matches (up to 3) plus up to two additional high-ranked hits
    for near-miss / gap analysis (not above threshold or not in top-3 set).
    """
    raw_results = search_schemes(query, limit=RAG_VECTOR_QUERY_LIMIT)
    relevant_results = filter_by_threshold(raw_results, similarity_threshold)[:3]
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


def build_context_from_results(results: list[SearchResult]) -> str:
    """RAG context text including verified URLs from metadata (never LLM-invented)."""
    parts: list[str] = []
    for result in results:
        chunk = result.document
        extras: list[str] = []
        if result.apply_link:
            extras.append(f"Official apply / learn more: {result.apply_link}")
        if result.source:
            extras.append(f"Scheme catalogue (MyScheme / reference): {result.source}")
        if extras:
            chunk = f"{chunk}\n" + "\n".join(extras)
        parts.append(chunk)
    return "\n\n".join(parts)
