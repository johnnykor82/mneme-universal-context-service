from __future__ import annotations

from pathlib import Path
from typing import Sequence

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import ProviderSettings, Settings, StaticTokenSettings


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
    assert retrieval["strategies"] == ["VECTOR", "KEYWORD", "RECENCY", "RECENCY_REFILL"]
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


def test_context_search_project_scope_is_limited_to_visible_project(tmp_path: Path) -> None:
    settings = Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        static_tokens=(
            StaticTokenSettings(
                name="project-a",
                token="project-a-token",
                project_scopes=("project-a",),
                role="ADAPTER",
            ),
        ),
    )
    api = TestClient(create_app(settings))
    project_a_headers = {"Authorization": "Bearer project-a-token"}
    start_a = api.post(
        "/v1/sessions/start",
        headers=project_a_headers,
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-project-a",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": "project-a",
            "privacy": {"project_isolation_key": "project-a"},
        },
    )
    assert start_a.status_code == 200, start_a.text
    start_b = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-project-b",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": "project-b",
            "privacy": {"project_isolation_key": "project-b"},
        },
    )
    assert start_b.status_code == 200, start_b.text
    event_a = event("event-project-a", "shared project evidence")
    event_a["session_id"] = "session-project-a"
    event_b = event("event-project-b", "shared project evidence")
    event_b["session_id"] = "session-project-b"
    assert api.post(
        "/v1/events",
        headers=project_a_headers,
        json={"schema_version": "mneme.event_batch.v0", "session_id": "session-project-a", "events": [event_a]},
    ).status_code == 200
    assert api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": "session-project-b", "events": [event_b]},
    ).status_code == 200

    search = api.post(
        "/v1/tools/context_search",
        headers=project_a_headers,
        json={"session_id": "session-project-a", "query": "shared project evidence", "scope": "PROJECT", "top_k": 10},
    )

    assert search.status_code == 200, search.text
    assert [item["event_id"] for item in search.json()["data"]["results"]] == ["event-project-a"]


def test_global_scope_respects_project_isolation_for_scoped_token_without_header(tmp_path: Path) -> None:
    settings = Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        static_tokens=(
            StaticTokenSettings(
                name="project-a",
                token="project-a-token",
                project_scopes=("project-a",),
                role="ADAPTER",
            ),
        ),
    )
    api = TestClient(create_app(settings))
    project_a_headers = {"Authorization": "Bearer project-a-token"}
    start_a = api.post(
        "/v1/sessions/start",
        headers=project_a_headers,
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-global-project-a",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": "project-a",
            "privacy": {"project_isolation_key": "project-a"},
        },
    )
    assert start_a.status_code == 200, start_a.text
    start_b = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-global-project-b",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": "project-b",
            "privacy": {"project_isolation_key": "project-b"},
        },
    )
    assert start_b.status_code == 200, start_b.text

    event_a = event("event-global-project-a", "visible shared scoped evidence")
    event_a["session_id"] = "session-global-project-a"
    event_b = event("event-global-project-b", "hidden shared scoped evidence")
    event_b["session_id"] = "session-global-project-b"
    accepted_a = api.post(
        "/v1/events",
        headers=project_a_headers,
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-global-project-a",
            "events": [event_a],
        },
    )
    assert accepted_a.status_code == 200, accepted_a.text
    accepted_b = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-global-project-b",
            "events": [event_b],
        },
    )
    assert accepted_b.status_code == 200, accepted_b.text

    search = api.post(
        "/v1/tools/context_search",
        headers=project_a_headers,
        json={
            "session_id": "session-global-project-a",
            "query": "shared scoped evidence",
            "scope": "GLOBAL",
            "top_k": 10,
        },
    )

    assert search.status_code == 200, search.text
    event_ids = [item["event_id"] for item in search.json()["data"]["results"]]
    assert event_ids == ["event-global-project-a"]


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


def test_context_search_trace_captures_candidate_breadth_by_source(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    ingest(
        api,
        [
            event("event-auth-old", "auth parser failure older", timestamp="2026-06-12T13:00:02Z"),
            event("event-auth-new", "auth parser failure current", timestamp="2026-06-12T13:00:03Z"),
        ],
    )

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-ret", "query": "auth parser failure", "scope": "SESSION", "top_k": 1},
    )

    assert response.status_code == 200, response.text
    trace = api.get(f"/v1/traces/{response.json()['trace_id']}", headers=auth_headers())
    retrieval = trace.json()["retrieval"]
    assert retrieval["candidate_count_raw"] == 1
    assert retrieval["candidate_count_unique"] == 1
    assert retrieval["source_counts"] == {"vector": 0, "keyword": 1, "graph": 0, "refill": 0}
    assert retrieval["candidate_ids_by_source"]["keyword"] == ["event-auth-new"]


def test_context_search_recency_refills_underfilled_results(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    ingest(
        api,
        [
            event("event-first", "unique needle evidence", timestamp="2026-06-12T13:00:01Z"),
            event("event-second", "recent fallback two", timestamp="2026-06-12T13:00:02Z"),
            event("event-third", "recent fallback three", timestamp="2026-06-12T13:00:03Z"),
        ],
    )

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-ret", "query": "needle", "scope": "SESSION", "top_k": 3},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    results = body["data"]["results"]
    assert [item["event_id"] for item in results] == ["event-first", "event-third", "event-second"]
    assert [item["reason"] for item in results] == ["KEYWORD_RECENCY", "RECENCY_REFILL", "RECENCY_REFILL"]
    assert body["warnings"][0]["code"] == "RECENCY_REFILL_USED"

    trace = api.get(f"/v1/traces/{body['trace_id']}", headers=auth_headers())
    retrieval = trace.json()["retrieval"]
    assert "RECENCY_REFILL" in retrieval["strategies"]
    assert retrieval["source_counts"]["refill"] == 2
    assert retrieval["candidate_ids_by_source"]["refill"] == ["event-third", "event-second"]


def test_context_search_propagates_adapter_supplied_freshness(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    current = event("event-current-source", "adapter verified current file evidence")
    current["metadata"] = {"freshness": "CURRENT"}
    ingest(api, [current])

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-ret", "query": "verified current file", "scope": "SESSION", "top_k": 1},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data"]["results"][0]["event_id"] == "event-current-source"
    assert body["data"]["results"][0]["freshness"] == "CURRENT"


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
    assert retrieval["mode"] == "general"
    assert retrieval["weights"]["dependency"] == 0.30


def test_context_search_uses_configured_default_mode_when_not_supplied(tmp_path: Path) -> None:
    settings = Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        routing_default_mode="factual",
        routing_mode_weights={
            "general": {
                "semantic_similarity": 0.4,
                "recency": 0.2,
                "dependency": 0.3,
                "type_weight": 0.1,
            },
            "reasoning": {
                "semantic_similarity": 0.35,
                "recency": 0.15,
                "dependency": 0.4,
                "type_weight": 0.1,
            },
            "factual": {
                "semantic_similarity": 0.80,
                "recency": 0.10,
                "dependency": 0.05,
                "type_weight": 0.05,
            },
            "debugging": {
                "semantic_similarity": 0.3,
                "recency": 0.4,
                "dependency": 0.1,
                "type_weight": 0.2,
            },
        },
    )
    api = TestClient(create_app(settings))
    start_session(api)
    ingest(api, [event("event-auth", "auth traceback failed at callback")])

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-ret", "query": "why did auth traceback fail", "top_k": 1},
    )

    assert response.status_code == 200, response.text
    trace = api.get(f"/v1/traces/{response.json()['trace_id']}", headers=auth_headers())
    retrieval = trace.json()["retrieval"]
    assert retrieval["mode"] == "factual"
    assert retrieval["weights"]["semantic_similarity"] == 0.80


def test_context_search_accepts_mode_and_reports_score_breakdown(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    ingest(api, [event("event-reasoning", "graph dependency design note")])

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-ret", "query": "graph design", "mode": "reasoning", "scope": "SESSION", "top_k": 1},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    result = body["data"]["results"][0]
    assert result["score_breakdown"]["mode"] == "reasoning"
    assert result["score_breakdown"]["event_id"] == "event-reasoning"
    assert result["score_breakdown"]["weights"] == {
        "semantic_similarity": 0.35,
        "recency": 0.15,
        "dependency": 0.40,
        "type_weight": 0.10,
    }
    assert result["score_breakdown"]["scope_applied"] == "SESSION"
    assert set(result["score_breakdown"]["components"]) == {
        "semantic_similarity",
        "recency_score",
        "dependency_score",
        "type_weight",
    }

    trace = api.get(f"/v1/traces/{body['trace_id']}", headers=auth_headers())
    retrieval = trace.json()["retrieval"]
    assert retrieval["mode"] == "reasoning"
    assert retrieval["score_breakdowns"][0]["event_id"] == "event-reasoning"
