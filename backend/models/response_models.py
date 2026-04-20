from pydantic import BaseModel, Field


class SchemeSource(BaseModel):
    scheme: str
    score: float
    apply_link: str | None = None
    source: str | None = None
    confidence_label: str
    cta_label: str
    preview_text: str = ""


class SearchResponse(BaseModel):
    answer: str | None
    provider: str | None
    sources: list[SchemeSource]
    moderation_blocked: bool = False
    redirect_message: str | None = None
    moderation_category: str | None = None
    reasoning_why: str | None = None
    near_miss_text: str | None = None
    near_miss_sources: list[SchemeSource] = Field(default_factory=list)



class ModerationResult(BaseModel):
    allowed: bool
    category: str
    redirect_message: str | None = None
