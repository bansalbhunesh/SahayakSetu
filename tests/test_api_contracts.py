"""API contract tests: all HTTP entry points, validation, and failure modes."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import pathlib
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("ENV", "development")

from backend.main import app  # noqa: E402
from backend.services.retrieval_service import SearchResult  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def _mock_retrieval_and_llm(monkeypatch):
    from backend.services import llm_service, retrieval_service

    async def _rewrite(q: str, _lang: str) -> str:
        return q

    def _retrieve(_q: str, _threshold: float, **_kwargs):
        return (
            [SearchResult(scheme_name="PMAY", document="PMAY info", score=0.8)],
            [],
            "PMAY context",
            "",
        )

    async def _generate_json(_messages):
        return (
            {
                "status": "insufficient_context",
                "answer": None,
                "claims": [],
                "why_it_fits": [],
                "near_miss": None,
                "next_step": None,
            },
            "test-model",
        )

    monkeypatch.setattr(llm_service, "rewrite_query", _rewrite)
    monkeypatch.setattr(llm_service, "generate_json", _generate_json)
    monkeypatch.setattr(retrieval_service, "retrieve_for_rag", _retrieve)


def test_get_health_returns_online():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "online"
    assert "model" in data
    assert "threshold" in data


def test_get_root_returns_status():
    r = client.get("/")
    assert r.status_code == 200
    assert "status" in r.json()


def test_get_ready_503_when_not_ready(monkeypatch):
    from backend.routers import health_router

    async def _down():
        return {
            "ready": False,
            "dependencies": {
                "qdrant": "down",
                "redis": "down",
                "llm": {"primary": "x", "fallback": "none", "ready": False},
            },
        }

    monkeypatch.setattr(health_router, "readiness_snapshot", _down)
    r = client.get("/ready")
    assert r.status_code == 503
    body = r.json()
    assert body.get("detail", {}).get("ready") is False


def test_post_search_missing_query_422():
    r = client.post("/api/search", json={"language": "en-IN"})
    assert r.status_code == 422


def test_post_search_query_wrong_type_422():
    r = client.post("/api/search", json={"query": 123, "language": "en-IN"})
    assert r.status_code == 422


def test_post_search_blank_query_422():
    r = client.post("/api/search", json={"query": "   ", "language": "en-IN"})
    assert r.status_code == 422


def test_post_search_oversized_query_422():
    from backend import config

    limit = config.MAX_QUERY_CHARS
    r = client.post("/api/search", json={"query": "x" * (limit + 1), "language": "en-IN"})
    assert r.status_code == 422


def test_post_search_happy_path_200():
    r = client.post("/api/search", json={"query": "PMAY eligibility Karnataka", "language": "en-IN"})
    assert r.status_code == 200
    data = r.json()
    assert "moderation_blocked" in data


def test_post_search_accepts_optional_profile():
    r = client.post(
        "/api/search",
        json={
            "query": "PM Kisan",
            "language": "hi-IN",
            "profile": {"state": "Karnataka", "annual_income": 120000},
        },
    )
    assert r.status_code == 200


def test_vapi_webhook_invalid_json_returns_400(monkeypatch):
    from backend.routers import voice_router

    monkeypatch.setattr(voice_router, "VAPI_WEBHOOK_SECRET", "")
    monkeypatch.setattr(voice_router, "ENV", "development")
    r = client.post("/vapi-webhook", content=b"not json {{{", headers={"Content-Type": "application/json"})
    assert r.status_code == 400


def test_vapi_webhook_malformed_tool_calls_no_500(monkeypatch):
    from backend.routers import voice_router

    monkeypatch.setattr(voice_router, "VAPI_WEBHOOK_SECRET", "")
    monkeypatch.setattr(voice_router, "ENV", "development")
    body = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                "not-a-dict",
                {"id": "1"},
                {"id": "2", "function": "not-dict"},
                {
                    "id": "3",
                    "function": {"name": "search_schemes", "arguments": "not-json"},
                },
                {
                    "id": "4",
                    "function": {
                        "name": "search_schemes",
                        "arguments": json.dumps({"query": "PM Kisan benefits", "language": "en-IN"}),
                    },
                },
            ],
        }
    }
    r = client.post("/vapi-webhook", json=body)
    assert r.status_code == 200
    payload = r.json()
    assert "results" in payload
    ids = {x.get("toolCallId") for x in payload["results"]}
    assert "3" in ids
    assert "4" in ids


def test_vapi_webhook_production_missing_secret_returns_503(monkeypatch):
    from backend.routers import voice_router

    monkeypatch.setattr(voice_router, "VAPI_WEBHOOK_SECRET", "")
    monkeypatch.setattr(voice_router, "ENV", "production")
    r = client.post("/vapi-webhook", json={"message": {"type": "assistant-request"}})
    assert r.status_code == 503
    detail = r.json().get("detail")
    assert isinstance(detail, dict)
    assert detail.get("error") == "webhook_secret_not_configured"


def test_vapi_webhook_signed_invalid_json_400(monkeypatch):
    from backend.routers import voice_router

    secret = b"sig-secret"
    monkeypatch.setattr(voice_router, "VAPI_WEBHOOK_SECRET", secret.decode())
    raw = b"{broken"
    sig = hmac.new(secret, raw, hashlib.sha256).hexdigest()
    r = client.post(
        "/vapi-webhook",
        content=raw,
        headers={"X-Vapi-Signature": sig, "Content-Type": "application/json"},
    )
    assert r.status_code == 400
