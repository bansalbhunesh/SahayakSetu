from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    user_id: str | None = None
    language: str = "hi-IN"
    profile: dict | None = None


class VapiWebhookRequest(BaseModel):
    message: dict
