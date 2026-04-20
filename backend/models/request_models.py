from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    user_id: str = "anonymous"
    language: str = "hi-IN"


class VapiWebhookRequest(BaseModel):
    message: dict
