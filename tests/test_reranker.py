from __future__ import annotations

from pathlib import Path
from typing import Sequence

import httpx
from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import ProviderSettings, Settings
from mneme_service.reranker import HttpRerankerProvider, RerankResult


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def start_session(api: TestClient) -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-rerank",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": "project-1",
            "model": "test-model",
            "tokenizer": "approx",
            "context_window_tokens": 100000,
            "cost_mode": "STANDARD",
            "started_at": "2026-06-12T21:00:00Z",
        },
    )
    assert response.status_code == 200, response.text


def event(event_id: str, text: str, *, timestamp: str) -> dict:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": "session-rerank",
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
        json={"schema_version": "mneme.event_batch.v0", "session_id": "session-rerank", "events": events},
    )
    assert response.status_code == 200, response.text


def reranker_settings(tmp_path: Path) -> Settings:
    return Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        reranker=ProviderSettings(
            enabled=True,
            provider="jina",
            model="jina-reranker-test",
            base_url="https://rerank.example.test/v1",
        ),
    )


class PreferenceReranker:
    def rerank(self, query: str, documents: Sequence[str]) -> RerankResult:
        scores = []
        for index, document in enumerate(documents):
            scores.append({"index": index, "score": 1.0 if "oauth" in document else 0.1})
        return RerankResult(scores=sorted(scores, key=lambda item: item["score"], reverse=True))


class FailingReranker:
    def rerank(self, query: str, documents: Sequence[str]) -> RerankResult:
        return RerankResult(scores=[], degraded=True, fallback_reason="RERANKER_UNAVAILABLE")


def test_http_reranker_parses_jina_cohere_style_results() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "results": [
                    {"index": 1, "relevance_score": 0.92},
                    {"index": 0, "score": 0.12},
                ]
            },
        )

    provider = HttpRerankerProvider(
        ProviderSettings(
            enabled=True,
            provider="jina",
            model="jina-reranker-test",
            base_url="https://rerank.example.test/v1",
            api_key="sk-reranker-secret",
        ),
        transport=httpx.MockTransport(handler),
    )

    result = provider.rerank("auth refresh", ["database migration", "oauth verifier"])

    assert result.degraded is False
    assert result.scores == [{"index": 1, "score": 0.92}, {"index": 0, "score": 0.12}]
    assert requests[0].url == "https://rerank.example.test/v1/rerank"
    assert requests[0].headers["authorization"] == "Bearer sk-reranker-secret"
    assert requests[0].read()


def test_http_reranker_parses_aligned_scores_response() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"scores": [0.12, 0.92]})

    provider = HttpRerankerProvider(
        ProviderSettings(
            enabled=True,
            provider="jina",
            model="jina-reranker-test",
            base_url="https://rerank.example.test/v1",
        ),
        transport=httpx.MockTransport(handler),
    )

    result = provider.rerank("auth refresh", ["database migration", "oauth verifier"])

    assert result.degraded is False
    assert result.scores == [{"index": 1, "score": 0.92}, {"index": 0, "score": 0.12}]


def test_http_reranker_degrades_when_response_indexes_are_out_of_range() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"index": 99, "relevance_score": 0.99}]})

    provider = HttpRerankerProvider(
        ProviderSettings(
            enabled=True,
            provider="jina",
            model="jina-reranker-test",
            base_url="https://rerank.example.test/v1",
        ),
        transport=httpx.MockTransport(handler),
        failure_threshold=1,
    )

    result = provider.rerank("auth refresh", ["oauth verifier"])

    assert result.degraded is True
    assert result.fallback_reason == "RERANKER_UNAVAILABLE"
    assert result.scores == []
    assert provider.circuit_open is True


def test_context_search_applies_reranker_and_records_cost(tmp_path: Path) -> None:
    api = TestClient(create_app(reranker_settings(tmp_path), reranker_provider=PreferenceReranker()))
    start_session(api)
    ingest(
        api,
        [
            event("event-oauth", "auth oauth verifier root cause", timestamp="2026-06-12T21:00:01Z"),
            event("event-db", "auth database migration follow-up", timestamp="2026-06-12T21:00:02Z"),
        ],
    )

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-rerank", "query": "auth", "top_k": 2},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert [item["event_id"] for item in body["data"]["results"]] == ["event-oauth", "event-db"]
    assert body["data"]["results"][0]["reason"] == "RERANKED"

    trace = api.get(f"/v1/traces/{body['trace_id']}", headers=auth_headers())
    retrieval = trace.json()["retrieval"]
    assert retrieval["strategies"] == ["KEYWORD", "RECENCY", "RERANK"]
    assert retrieval["degraded"] is False

    cost = api.get("/v1/costs/session/session-rerank", headers=auth_headers())
    assert cost.status_code == 200
    assert cost.json()["reranker_calls"] == 1
    assert cost.json()["failures"]["reranker_failures"] == 0


def test_context_search_respects_reranker_top_k_setting(tmp_path: Path) -> None:
    settings = reranker_settings(tmp_path)
    settings = Settings(
        db_path=settings.db_path,
        auth_token=settings.auth_token,
        reranker_top_k=1,
        reranker=settings.reranker,
    )
    api = TestClient(create_app(settings, reranker_provider=PreferenceReranker()))
    start_session(api)
    ingest(
        api,
        [
            event("event-oauth", "auth oauth verifier root cause", timestamp="2026-06-12T21:00:01Z"),
            event("event-db", "auth database migration follow-up", timestamp="2026-06-12T21:00:02Z"),
        ],
    )

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-rerank", "query": "auth", "top_k": 2},
    )

    assert response.status_code == 200, response.text
    assert [item["event_id"] for item in response.json()["data"]["results"]] == ["event-oauth"]


def test_context_search_keeps_original_order_when_reranker_fails(tmp_path: Path) -> None:
    api = TestClient(create_app(reranker_settings(tmp_path), reranker_provider=FailingReranker()))
    start_session(api)
    ingest(
        api,
        [
            event("event-old", "auth old evidence", timestamp="2026-06-12T21:00:01Z"),
            event("event-new", "auth new evidence", timestamp="2026-06-12T21:00:02Z"),
        ],
    )

    response = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-rerank", "query": "auth", "top_k": 2},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert [item["event_id"] for item in body["data"]["results"]] == ["event-new", "event-old"]
    assert body["warnings"][0]["code"] == "RERANKER_UNAVAILABLE"

    trace = api.get(f"/v1/traces/{body['trace_id']}", headers=auth_headers())
    retrieval = trace.json()["retrieval"]
    assert retrieval["strategies"] == ["KEYWORD", "RECENCY", "RERANK"]
    assert retrieval["degraded"] is True
    assert retrieval["fallbacks"] == ["RERANKER_UNAVAILABLE"]

    cost = api.get("/v1/costs/session/session-rerank", headers=auth_headers())
    assert cost.json()["failures"]["reranker_failures"] == 1
