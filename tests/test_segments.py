from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import ProviderSettings, Settings
from mneme_service.enrichment import EnrichmentResult


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def start_session(api: TestClient) -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-seg",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": "project-1",
            "started_at": "2026-06-12T15:00:00Z",
        },
    )
    assert response.status_code == 200, response.text


def user_event(event_id: str, text: str, timestamp: str) -> dict[str, Any]:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": "session-seg",
        "turn_id": event_id.replace("event", "turn"),
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "role": "USER",
        "type": "USER_MESSAGE",
        "timestamp": timestamp,
        "content": {"format": "TEXT", "text": text},
        "parent_event_ids": [],
    }


def ingest(api: TestClient, events: list[dict[str, Any]]) -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": "session-seg", "events": events},
    )
    assert response.status_code == 200, response.text


class DriftEmbeddingProvider:
    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        return [_drift_vector(text) for text in texts]


class EntityEnrichmentProvider:
    def enrich(self, event_payload: dict[str, Any], state: dict[str, Any]) -> EnrichmentResult:
        return EnrichmentResult(updates={"active_entities": ["OAuthFlow"]})


def _drift_vector(text: str) -> list[float]:
    lowered = text.lower()
    if "billing" in lowered or "parser" in lowered:
        return [0.0, 1.0]
    return [1.0, 0.0]


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


def test_explicit_topic_switch_rolls_over_segments_and_list_segments_exposes_metadata(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)

    ingest(
        api,
        [
            user_event("event-1", "Continue retrieval work", "2026-06-12T15:00:01Z"),
            user_event("event-2", "New topic: fix the billing parser", "2026-06-12T15:00:02Z"),
            user_event("event-3", "Новая тема: исправим отчеты", "2026-06-12T15:00:03Z"),
        ],
    )

    response = api.post(
        "/v1/tools/list_segments",
        headers=auth_headers(),
        json={"session_id": "session-seg", "status": "ANY", "page_size": 10},
    )

    assert response.status_code == 200, response.text
    segments = response.json()["data"]["segments"]
    assert [segment["status"] for segment in segments] == ["CLOSED", "CLOSED", "ACTIVE"]
    assert [segment["anchor_event_ids"][0] for segment in segments] == ["event-1", "event-2", "event-3"]
    assert segments[0]["event_count"] == 1
    assert segments[1]["title"] == "New topic: fix the billing parser"
    assert segments[2]["title"] == "Новая тема: исправим отчеты"
    assert segments[2]["drift_reason"] == "EXPLICIT_SWITCH"

    exported = api.get("/v1/sessions/session-seg/export", headers=auth_headers())
    assert exported.status_code == 200
    traces = [
        trace
        for trace in exported.json()["traces"]
        if trace.get("trace_type") == "SEGMENT_DRIFT" and trace.get("event_id") == "event-2"
    ]
    assert len(traces) == 1
    trace = traces[0]
    assert trace["decision"]["intent"] == "SWITCH"
    assert trace["decision"]["drift_reason"] == "EXPLICIT_SWITCH"
    assert trace["signals"]["explicit_switch"] is True
    assert trace["segment_effect"]["closed_segment_id"] == "segment-session-seg-1"
    assert trace["segment_effect"]["opened_segment_id"] == "segment-session-seg-2"


def test_continuation_does_not_create_new_segment(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    ingest(
        api,
        [
            user_event("event-1", "Continue retrieval work", "2026-06-12T15:00:01Z"),
            user_event("event-2", "Keep going on retrieval work", "2026-06-12T15:00:02Z"),
        ],
    )

    response = api.post(
        "/v1/tools/list_segments",
        headers=auth_headers(),
        json={"session_id": "session-seg", "status": "ANY", "page_size": 10},
    )

    assert response.status_code == 200, response.text
    segments = response.json()["data"]["segments"]
    assert len(segments) == 1
    assert segments[0]["status"] == "ACTIVE"
    assert segments[0]["event_count"] == 2


def test_high_embedding_drift_rolls_over_active_segment(tmp_path: Path) -> None:
    api = TestClient(create_app(embedding_settings(tmp_path), embedding_provider=DriftEmbeddingProvider()))
    start_session(api)
    ingest(
        api,
        [
            user_event("event-1", "Continue retrieval work", "2026-06-12T15:00:01Z"),
            user_event("event-2", "Keep retrieval context work going", "2026-06-12T15:00:02Z"),
            user_event("event-3", "Still on retrieval memory work", "2026-06-12T15:00:03Z"),
        ],
    )
    ingest(api, [user_event("event-4", "Refactor the billing parser", "2026-06-12T15:00:04Z")])

    response = api.post(
        "/v1/tools/list_segments",
        headers=auth_headers(),
        json={"session_id": "session-seg", "status": "ANY", "page_size": 10},
    )

    assert response.status_code == 200, response.text
    segments = response.json()["data"]["segments"]
    assert [segment["status"] for segment in segments] == ["CLOSED", "ACTIVE"]
    assert [segment["event_count"] for segment in segments] == [3, 1]
    assert segments[1]["anchor_event_ids"] == ["event-4"]
    assert segments[1]["drift_reason"] == "EMBEDDING_DRIFT"

    exported = api.get("/v1/sessions/session-seg/export", headers=auth_headers())
    assert exported.status_code == 200
    traces = [
        trace
        for trace in exported.json()["traces"]
        if trace.get("trace_type") == "SEGMENT_DRIFT" and trace.get("event_id") == "event-4"
    ]
    assert len(traces) == 1
    trace = traces[0]
    assert trace["decision"]["intent"] == "NEW_TASK"
    assert trace["decision"]["drift_reason"] == "EMBEDDING_DRIFT"
    assert trace["signals"]["embedding_drift"] > 0.35
    assert trace["segment_effect"]["closed_segment_id"] == "segment-session-seg-1"
    assert trace["segment_effect"]["opened_segment_id"] == "segment-session-seg-2"
    assert trace["fallbacks"] == []


def test_entity_contradiction_rolls_over_active_segment(tmp_path: Path) -> None:
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                enricher_every_n_turns=1,
                llm_enrichment=ProviderSettings(
                    enabled=True,
                    provider="openai_compatible",
                    model="gpt-test",
                    base_url="https://llm.example.test/v1",
                ),
            ),
            enrichment_provider=EntityEnrichmentProvider(),
        )
    )
    start_session(api)
    ingest(api, [user_event("event-1", "Continue OAuthFlow work", "2026-06-12T15:00:01Z")])
    ingest(api, [user_event("event-2", "Do not use OAuthFlow anymore", "2026-06-12T15:00:02Z")])

    response = api.post(
        "/v1/tools/list_segments",
        headers=auth_headers(),
        json={"session_id": "session-seg", "status": "ANY", "page_size": 10},
    )

    assert response.status_code == 200, response.text
    segments = response.json()["data"]["segments"]
    assert [segment["status"] for segment in segments] == ["CLOSED", "ACTIVE"]
    assert segments[1]["anchor_event_ids"] == ["event-2"]

    exported = api.get("/v1/sessions/session-seg/export", headers=auth_headers())
    trace = [
        trace
        for trace in exported.json()["traces"]
        if trace.get("trace_type") == "SEGMENT_DRIFT" and trace.get("event_id") == "event-2"
    ][0]
    assert trace["signals"]["entity_contradiction"] is True
