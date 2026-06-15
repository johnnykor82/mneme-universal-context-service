from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Sequence

import httpx
from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import ProviderSettings, Settings
from mneme_service.embeddings import EmbeddingIndex, OpenAICompatibleEmbeddingProvider
from mneme_service.storage import Store


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def start_session(api: TestClient) -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-emb",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": "project-1",
            "model": "test-model",
            "tokenizer": "approx",
            "context_window_tokens": 100000,
            "cost_mode": "STANDARD",
            "started_at": "2026-06-12T12:00:00Z",
            "privacy": {
                "project_isolation_key": "project-1",
                "retention_days": 30,
                "redaction_profile": "DEFAULT",
                "redaction_policy": "IRREVERSIBLE",
            },
        },
    )
    assert response.status_code == 200, response.text


def event(
    event_id: str,
    text: str,
    *,
    event_type: str = "USER_MESSAGE",
    role: str = "USER",
    turn_id: str = "turn-1",
) -> dict:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": "session-emb",
        "turn_id": turn_id,
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "role": role,
        "type": event_type,
        "timestamp": "2026-06-12T12:00:01Z",
        "content": {"format": "TEXT", "text": text},
        "parent_event_ids": [],
    }


class StaticEmbeddingProvider:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        batch = list(texts)
        self.calls.append(batch)
        return [_vector_for(text) if text.strip() else None for text in batch]


class FailingEmbeddingProvider:
    def __init__(self) -> None:
        self.calls = 0

    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        self.calls += 1
        raise RuntimeError("embedding provider unavailable")


class MixedDimensionEmbeddingProvider:
    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        return [[1.0, 0.0], [1.0, 0.0, 0.0]][: len(texts)]


def _vector_for(text: str) -> list[float]:
    lowered = text.lower()
    if "alpha" in lowered or "auth" in lowered or "oauth" in lowered:
        return [1.0, 0.0, 0.0]
    if "beta" in lowered or "database" in lowered:
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]


def test_openai_compatible_provider_batches_non_empty_inputs_and_uses_bearer_token() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url == "https://embed.example.test/v1/embeddings"
        assert request.headers["authorization"] == "Bearer sk-provider-secret"
        payload = json.loads(request.content)
        assert payload == {"model": "text-embedding-test", "input": ["alpha", "beta"]}
        return httpx.Response(
            200,
            json={
                "data": [
                    {"embedding": [1.0, 0.0, 0.0]},
                    {"embedding": [0.0, 1.0, 0.0]},
                ]
            },
        )

    provider = OpenAICompatibleEmbeddingProvider(
        ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="text-embedding-test",
            base_url="https://embed.example.test/v1",
            api_key="sk-provider-secret",
        ),
        transport=httpx.MockTransport(handler),
    )

    embeddings = provider.embed_texts(["alpha", "   ", "beta"])

    assert embeddings == [[1.0, 0.0, 0.0], None, [0.0, 1.0, 0.0]]
    assert len(requests) == 1


def test_openai_compatible_provider_opens_circuit_breaker_after_repeated_failures() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, json={"error": {"message": "down"}})

    provider = OpenAICompatibleEmbeddingProvider(
        ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="text-embedding-test",
            base_url="https://embed.example.test/v1",
        ),
        transport=httpx.MockTransport(handler),
        failure_threshold=2,
        cooldown_seconds=300,
    )

    assert provider.embed_texts(["alpha"]) == [None]
    assert provider.embed_texts(["alpha"]) == [None]
    assert provider.embed_texts(["alpha"]) == [None]

    assert calls == 2
    assert provider.circuit_open is True


def test_openai_compatible_provider_treats_malformed_embeddings_as_failure() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"embedding": "not-a-vector"}]})

    provider = OpenAICompatibleEmbeddingProvider(
        ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="text-embedding-test",
            base_url="https://embed.example.test/v1",
        ),
        transport=httpx.MockTransport(handler),
        failure_threshold=1,
        cooldown_seconds=300,
    )

    assert provider.embed_texts(["alpha"]) == [None]
    assert provider.circuit_open is True


def test_embedding_index_rejects_mixed_dimension_batch(tmp_path: Path) -> None:
    store = Store(tmp_path / "mneme.db")
    index = EmbeddingIndex(store, MixedDimensionEmbeddingProvider(), model_id="text-embedding-test", batch_size=10)

    stored = index.index_events(
        [
            {
                "event_id": "event-one",
                "session_id": "session-emb",
                "segment_id": "segment-session-emb",
                "text": "alpha one",
                "token_count": 2,
                "type": "USER_MESSAGE",
            },
            {
                "event_id": "event-two",
                "session_id": "session-emb",
                "segment_id": "segment-session-emb",
                "text": "alpha two",
                "token_count": 2,
                "type": "USER_MESSAGE",
            },
        ]
    )

    assert stored.embedding_items == 0
    assert stored.embedding_failures == 1
    assert store.list_embeddings("session-emb", "text-embedding-test") == []


def test_embedding_index_persists_rows_and_python_cosine_fallback_returns_semantic_matches(tmp_path: Path) -> None:
    store = Store(tmp_path / "mneme.db")
    provider = StaticEmbeddingProvider()
    index = EmbeddingIndex(store, provider, model_id="text-embedding-test", batch_size=10)

    stored = index.index_events(
        [
            {
                "event_id": "event-auth",
                "session_id": "session-emb",
                "segment_id": "segment-session-emb",
                "text": "oauth refresh token handshake",
                "token_count": 7,
                "type": "USER_MESSAGE",
            },
            {
                "event_id": "event-db",
                "session_id": "session-emb",
                "segment_id": "segment-session-emb",
                "text": "database migration status",
                "token_count": 5,
                "type": "TOOL_OUTPUT",
            },
        ]
    )

    assert stored.embedding_batches == 1
    assert stored.embedding_items == 2
    assert stored.embedding_failures == 0
    assert index.search("authentication refresh flow", session_id="session-emb", top_k=1)[0]["event_id"] == "event-auth"

    with sqlite3.connect(tmp_path / "mneme.db") as conn:
        rows = conn.execute("SELECT event_id, embedding_model_id, type FROM embedding_index ORDER BY event_id").fetchall()
    assert rows == [
        ("event-auth", "text-embedding-test", "USER_MESSAGE"),
        ("event-db", "text-embedding-test", "TOOL_OUTPUT"),
    ]


def test_embedding_index_top_k_zero_means_unlimited_and_global_search_crosses_sessions(tmp_path: Path) -> None:
    store = Store(tmp_path / "mneme.db")
    provider = StaticEmbeddingProvider()
    index = EmbeddingIndex(store, provider, model_id="text-embedding-test", batch_size=10)
    index.index_events(
        [
            {
                "event_id": "event-auth-a",
                "session_id": "session-a",
                "segment_id": "segment-a",
                "text": "oauth refresh handshake alpha",
                "token_count": 4,
                "type": "USER_MESSAGE",
            },
            {
                "event_id": "event-auth-b",
                "session_id": "session-b",
                "segment_id": "segment-b",
                "text": "authentication callback alpha",
                "token_count": 3,
                "type": "USER_MESSAGE",
            },
        ]
    )

    unlimited = index.search("auth alpha", session_id="session-a", top_k=0)
    global_results = index.search_global("auth alpha", top_k=0)

    assert [item["event_id"] for item in unlimited] == ["event-auth-a"]
    assert {item["event_id"] for item in global_results} == {"event-auth-a", "event-auth-b"}


def test_embedding_drift_uses_centroid_window_for_recent_topic_evolution(tmp_path: Path) -> None:
    store = Store(tmp_path / "mneme.db")
    provider = StaticEmbeddingProvider()
    full_centroid = EmbeddingIndex(store, provider, model_id="text-embedding-test", batch_size=10)
    windowed_centroid = EmbeddingIndex(
        store,
        provider,
        model_id="text-embedding-test",
        batch_size=10,
        centroid_window=1,
    )
    full_centroid.index_events(
        [
            {
                "event_id": "event-old-db-1",
                "session_id": "session-window",
                "segment_id": "segment-window",
                "text": "database migration beta",
                "token_count": 3,
                "type": "USER_MESSAGE",
            },
            {
                "event_id": "event-old-db-2",
                "session_id": "session-window",
                "segment_id": "segment-window",
                "text": "database status beta",
                "token_count": 3,
                "type": "USER_MESSAGE",
            },
            {
                "event_id": "event-recent-auth",
                "session_id": "session-window",
                "segment_id": "segment-window",
                "text": "oauth callback alpha",
                "token_count": 3,
                "type": "USER_MESSAGE",
            },
        ]
    )

    all_history_drift = full_centroid.embedding_drift_against_segment(
        "auth alpha",
        session_id="session-window",
        segment_id="segment-window",
        min_embeddings=1,
    )
    recent_window_drift = windowed_centroid.embedding_drift_against_segment(
        "auth alpha",
        session_id="session-window",
        segment_id="segment-window",
        min_embeddings=1,
    )

    assert all_history_drift > 0.2
    assert recent_window_drift == 0.0


def test_event_ingest_indexes_redacted_content_and_compresses_tool_output_without_changing_raw_event(tmp_path: Path) -> None:
    provider = StaticEmbeddingProvider()
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                embeddings=ProviderSettings(
                    enabled=True,
                    provider="openai_compatible",
                    model="text-embedding-test",
                    base_url="https://embed.example.test/v1",
                ),
            ),
            embedding_provider=provider,
        )
    )
    start_session(api)
    long_tool_output = "alpha head " + ("middle " * 900) + "auth tail sk-embedding-secret"

    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-emb",
            "events": [
                event("event-user", "alpha oauth sk-embedding-secret"),
                event(
                    "event-tool",
                    long_tool_output,
                    event_type="TOOL_OUTPUT",
                    role="TOOL",
                ),
            ],
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["accepted"] == 2
    embedded_text = "\n".join(provider.calls[0])
    assert "sk-embedding-secret" not in embedded_text
    assert "[REDACTED]" in embedded_text
    assert "...[truncated " in provider.calls[0][1]
    assert provider.calls[0][1].startswith("alpha head")
    assert provider.calls[0][1].endswith("auth tail [REDACTED]")

    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-emb", "event_id": "event-tool", "full": True},
    )
    assert fetched.status_code == 200
    fetched_text = fetched.json()["data"]["event"]["content"]["text"]
    assert fetched_text.startswith("alpha head")
    assert "middle middle" in fetched_text
    assert "sk-embedding-secret" not in fetched_text
    assert "[REDACTED]" in fetched_text

    cost = api.get("/v1/costs/session/session-emb", headers=auth_headers())
    assert cost.status_code == 200
    assert cost.json()["embedding_batches"] == 1


def test_tool_output_embedding_compression_uses_settings_threshold(tmp_path: Path) -> None:
    provider = StaticEmbeddingProvider()
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                tool_output_compress_threshold_tokens=10000,
                embeddings=ProviderSettings(
                    enabled=True,
                    provider="openai_compatible",
                    model="text-embedding-test",
                    base_url="https://embed.example.test/v1",
                ),
            ),
            embedding_provider=provider,
        )
    )
    start_session(api)
    long_tool_output = "alpha head " + ("middle " * 900) + "auth tail"

    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-emb",
            "events": [
                event(
                    "event-tool-uncompressed",
                    long_tool_output,
                    event_type="TOOL_OUTPUT",
                    role="TOOL",
                )
            ],
        },
    )

    assert response.status_code == 200, response.text
    assert provider.calls[0][0] == long_tool_output
    assert "...[truncated " not in provider.calls[0][0]


def test_reindex_on_model_change_indexes_existing_events_for_new_model(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    first_provider = StaticEmbeddingProvider()
    first_api = TestClient(
        create_app(
            Settings(
                db_path=db_path,
                auth_token=TOKEN,
                embeddings=ProviderSettings(
                    enabled=True,
                    provider="openai_compatible",
                    model="embedding-old",
                    base_url="https://embed.example.test/v1",
                ),
            ),
            embedding_provider=first_provider,
        )
    )
    start_session(first_api)
    accepted = first_api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-emb",
            "events": [event("event-reindex", "oauth reindex alpha")],
        },
    )
    assert accepted.status_code == 200, accepted.text

    second_provider = StaticEmbeddingProvider()
    TestClient(
        create_app(
            Settings(
                db_path=db_path,
                auth_token=TOKEN,
                reindex_on_model_change=True,
                embeddings=ProviderSettings(
                    enabled=True,
                    provider="openai_compatible",
                    model="embedding-new",
                    base_url="https://embed.example.test/v1",
                ),
            ),
            embedding_provider=second_provider,
        )
    )

    store = Store(db_path)
    assert [row["event_id"] for row in store.list_embeddings("session-emb", "embedding-new")] == ["event-reindex"]
    cost = store.cost_report("session-emb")
    assert cost["embedding_items"] == 2


def test_event_ingest_stores_event_when_embedding_provider_fails(tmp_path: Path) -> None:
    provider = FailingEmbeddingProvider()
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                embeddings=ProviderSettings(
                    enabled=True,
                    provider="openai_compatible",
                    model="text-embedding-test",
                    base_url="https://embed.example.test/v1",
                ),
            ),
            embedding_provider=provider,
        )
    )
    start_session(api)

    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-emb",
            "events": [event("event-kept", "alpha evidence survives provider outage")],
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["stored_event_ids"] == ["event-kept"]
    assert provider.calls == 1
    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-emb", "event_id": "event-kept", "full": True},
    )
    assert fetched.status_code == 200
    assert fetched.json()["data"]["event"]["event_id"] == "event-kept"

    cost = api.get("/v1/costs/session/session-emb", headers=auth_headers())
    assert cost.status_code == 200
    assert cost.json()["embedding_batches"] == 1
    assert cost.json()["embedding_items"] == 0
    assert cost.json()["failures"]["embedding_failures"] == 1
