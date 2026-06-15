from __future__ import annotations

from pathlib import Path
from typing import Sequence

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import ProviderSettings, Settings


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def start_session(api: TestClient) -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-ret",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": "project-1",
            "model": "test-model",
            "tokenizer": "approx",
            "context_window_tokens": 100000,
            "cost_mode": "STANDARD",
            "started_at": "2026-06-12T13:00:00Z",
            "privacy": {
                "project_isolation_key": "project-1",
                "retention_days": 30,
                "redaction_profile": "DEFAULT",
                "redaction_policy": "IRREVERSIBLE",
            },
        },
    )
    assert response.status_code == 200, response.text


def event(event_id: str, text: str, *, timestamp: str = "2026-06-12T13:00:01Z") -> dict:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": "session-ret",
        "turn_id": "turn-1",
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "role": "TOOL",
        "type": "TOOL_OUTPUT",
        "timestamp": timestamp,
        "content": {"format": "TEXT", "text": text},
        "parent_event_ids": [],
    }


def ingest(api: TestClient, events: list[dict]) -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": "session-ret", "events": events},
    )
    assert response.status_code == 200, response.text


def embedding_settings(tmp_path: Path) -> Settings:
    return Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        embeddings=ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="text-embedding-test",
            base_url="https://embed.example.test/v1",
        ),
    )


class SemanticEmbeddingProvider:
    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        return [_vector_for(text) for text in texts]


class FailingEmbeddingProvider:
    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        raise RuntimeError("embedding provider unavailable")


def _vector_for(text: str) -> list[float]:
    lowered = text.lower()
    if "oauth" in lowered or "auth" in lowered or "authentication" in lowered or "refresh" in lowered:
        return [1.0, 0.0, 0.0]
    if "database" in lowered or "migration" in lowered:
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]


def test_context_search_returns_semantic_hit_when_keywords_miss(tmp_path: Path) -> None:
    api = TestClient(create_app(embedding_settings(tmp_path), embedding_provider=SemanticEmbeddingProvider()))
    start_session(api)
    ingest(
        api,
        [
            event("event-oauth", "oauth callback verifier rotated"),
            event("event-db", "database migration completed"),
        ],
    )

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={
            "session_id": "session-ret",
            "query": "authentication refresh flow",
            "scope": "SESSION",
            "top_k": 5,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data"]["results"][0]["event_id"] == "event-oauth"
    assert body["data"]["results"][0]["reason"] == "VECTOR_COSINE"

    trace = api.get(f"/v1/traces/{body['trace_id']}", headers=auth_headers())
    assert trace.status_code == 200
    retrieval = trace.json()["retrieval"]
    assert retrieval["strategies"] == ["VECTOR", "KEYWORD", "RECENCY"]
    assert retrieval["degraded"] is False
    assert retrieval["fallbacks"] == []


def test_context_search_global_scope_can_return_events_from_other_sessions(tmp_path: Path) -> None:
    api = TestClient(create_app(embedding_settings(tmp_path), embedding_provider=SemanticEmbeddingProvider()))
    start_session(api)
    other_session = {
        "schema_version": "mneme.session.v0",
        "session_id": "session-global",
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "project_id": "project-1",
        "model": "test-model",
        "tokenizer": "approx",
        "context_window_tokens": 100000,
        "cost_mode": "STANDARD",
        "started_at": "2026-06-12T13:10:00Z",
    }
    assert api.post("/v1/sessions/start", headers=auth_headers(), json=other_session).status_code == 200
    other_event = event("event-global-oauth", "oauth callback from another session")
    other_event["session_id"] = "session-global"
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-global",
            "events": [other_event],
        },
    )
    assert response.status_code == 200, response.text

    search = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={
            "session_id": "session-ret",
            "query": "authentication callback",
            "scope": "GLOBAL",
            "top_k": 5,
        },
    )

    assert search.status_code == 200, search.text
    results = search.json()["data"]["results"]
    assert results[0]["event_id"] == "event-global-oauth"
    assert results[0]["session_id"] == "session-global"


def test_context_search_uses_keyword_recency_fallback_without_embeddings(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    ingest(
        api,
        [
            event("event-old", "parser failure older", timestamp="2026-06-12T12:59:59Z"),
            event("event-new", "parser failure current", timestamp="2026-06-12T13:00:02Z"),
        ],
    )

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-ret", "query": "parser failure", "scope": "SESSION", "top_k": 1},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert [item["event_id"] for item in body["data"]["results"]] == ["event-new"]
    assert body["data"]["results"][0]["reason"] == "KEYWORD_RECENCY"

    trace = api.get(f"/v1/traces/{body['trace_id']}", headers=auth_headers())
    retrieval = trace.json()["retrieval"]
    assert retrieval["strategies"] == ["KEYWORD", "RECENCY"]
    assert retrieval["degraded"] is False
    assert retrieval["fallbacks"] == []


def test_context_search_records_degraded_trace_when_embedding_provider_fails(tmp_path: Path) -> None:
    api = TestClient(create_app(embedding_settings(tmp_path), embedding_provider=FailingEmbeddingProvider()))
    start_session(api)
    ingest(api, [event("event-fallback", "outage keyword evidence survives")])

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-ret", "query": "outage keyword", "scope": "SESSION", "top_k": 5},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data"]["results"][0]["event_id"] == "event-fallback"
    assert body["warnings"][0]["code"] == "EMBEDDINGS_UNAVAILABLE"

    trace = api.get(f"/v1/traces/{body['trace_id']}", headers=auth_headers())
    retrieval = trace.json()["retrieval"]
    assert retrieval["strategies"] == ["VECTOR", "KEYWORD", "RECENCY"]
    assert retrieval["degraded"] is True
    assert retrieval["fallbacks"] == ["EMBEDDINGS_UNAVAILABLE"]

    cost = api.get("/v1/costs/session/session-ret", headers=auth_headers())
    assert cost.status_code == 200
    assert cost.json()["failures"]["embedding_failures"] >= 1


def test_context_search_trace_reports_router_mode_and_weights(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    ingest(api, [event("event-debug", "auth traceback failed at callback")])

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-ret", "query": "why did auth traceback fail", "top_k": 1},
    )

    assert response.status_code == 200, response.text
    trace = api.get(f"/v1/traces/{response.json()['trace_id']}", headers=auth_headers())
    retrieval = trace.json()["retrieval"]
    assert retrieval["mode"] == "debugging"
    assert retrieval["weights"]["dependency"] == 0.2
