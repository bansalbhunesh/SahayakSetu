"""Task-execution planner over grounded sources."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from backend.services import llm_service
from backend.services.retrieval_service import SearchResult

EligibilityVerdict = Literal["eligible", "likely_eligible", "likely_ineligible", "unknown"]


class UserProfile(BaseModel):
    age: int | None = None
    gender: str | None = None
    state: str | None = None
    occupation: str | None = None
    annual_income: int | None = None
    category: str | None = None
    has_land: bool | None = None
    bpl: bool | None = None


class EligibilityCheck(BaseModel):
    scheme: str
    source_id: str
    verdict: EligibilityVerdict
    matched_criteria: list[str] = Field(default_factory=list)
    missing_criteria: list[str] = Field(default_factory=list)
    unknown_criteria: list[str] = Field(default_factory=list)


class ActionStep(BaseModel):
    order: int
    action: str
    where: str | None = None
    estimated_time: str | None = None


class AgentPlan(BaseModel):
    status: Literal["plan_ready", "need_more_info", "insufficient_data"]
    eligibility: list[EligibilityCheck] = Field(default_factory=list)
    documents_needed: list[str] = Field(default_factory=list)
    steps: list[ActionStep] = Field(default_factory=list)
    clarifying_questions: list[str] = Field(default_factory=list)
    disclaimer: str


async def build_plan(
    query: str,
    profile: UserProfile,
    sources: list[SearchResult],
    language: str,
) -> AgentPlan:
    if not sources:
        return _insufficient(language)
    prompt = _build_agent_prompt(query, profile, sources, language)
    raw, _provider = await llm_service.generate_json_prompt(prompt)
    try:
        plan = AgentPlan.model_validate(raw)
    except ValidationError:
        return _insufficient(language)

    valid_ids = {f"S{i+1}" for i in range(len(sources))}
    plan.eligibility = [e for e in plan.eligibility if e.source_id in valid_ids]
    plan.steps = [s for s in plan.steps if _url_grounded(s.where, sources)]
    if not plan.disclaimer:
        plan.disclaimer = _disclaimer(language)
    return plan


def slots_missing(profile: UserProfile, eligibility: list[EligibilityCheck]) -> list[str]:
    wanted: set[str] = set()
    for entry in eligibility:
        if entry.verdict != "unknown":
            continue
        for criterion in entry.unknown_criteria:
            low = criterion.lower()
            if "income" in low and profile.annual_income is None:
                wanted.add("annual_income")
            if "age" in low and profile.age is None:
                wanted.add("age")
            if "state" in low and profile.state is None:
                wanted.add("state")
            if "land" in low and profile.has_land is None:
                wanted.add("has_land")
            if "bpl" in low and profile.bpl is None:
                wanted.add("bpl")
    return sorted(wanted)


def _url_grounded(url: str | None, sources: list[SearchResult]) -> bool:
    if not url:
        return True
    return any(url == s.apply_link or url == s.source for s in sources)


def _insufficient(language: str) -> AgentPlan:
    return AgentPlan(status="insufficient_data", disclaimer=_disclaimer(language))


def _disclaimer(language: str) -> str:
    if language.startswith("hi"):
        return "यह सूचना आधिकारिक नहीं है। अंतिम पुष्टि के लिए official portal या CSC जाएं।"
    return "This is unofficial guidance. Confirm final eligibility at the official portal or your nearest CSC."


def _build_agent_prompt(query: str, profile: UserProfile, sources: list[SearchResult], language: str) -> str:
    sources_block = "\n".join(
        f"[S{i+1}] {s.scheme_name} — {s.document}" + (f"\n    apply: {s.apply_link}" if s.apply_link else "")
        for i, s in enumerate(sources)
    )
    profile_block = profile.model_dump_json(exclude_none=True)
    return AGENT_PROMPT.format(
        query=query,
        profile=profile_block,
        sources=sources_block,
        language=language,
    )


AGENT_PROMPT = """You are an action-planning agent for Indian welfare schemes.

USER QUERY: {query}
USER PROFILE (JSON, may be partial): {profile}
TARGET LANGUAGE: {language}

SOURCES (only truth you may use):
{sources}

Produce a strict JSON object with:
- status: plan_ready | need_more_info | insufficient_data
- eligibility: list[{scheme, source_id, verdict, matched_criteria, missing_criteria, unknown_criteria}]
- documents_needed: list[string]
- steps: list[{order, action, where, estimated_time}]
- clarifying_questions: list[string]
- disclaimer: string

Rules:
- Every eligibility row must reference valid source_id from SOURCES.
- Never invent thresholds or URLs.
- URLs in steps.where must be copied from source apply links.
- If profile data is missing to conclude, use unknown_criteria + clarifying_questions and set status=need_more_info.
- If sources are inadequate, set status=insufficient_data with empty lists.
- Translate user-facing values to TARGET LANGUAGE. Keep JSON keys and scheme names in English.
Return ONLY JSON.
"""
