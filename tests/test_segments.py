from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import ProviderSettings, Settings, StaticTokenSettings
from mneme_service.enrichment import EnrichmentResult


TOKEN = "test-token"


def auth_headers(token: str = TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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


def ingest(api: TestClient, events: list[dict[str, Any]], *, token: str = TOKEN) -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(token),
        json={"schema_version": "mneme.event_batch.v0", "session_id": "session-seg", "events": events},
    )
    assert response.status_code == 200, response.text


def test_direct_segment_start_close_list_get_and_events(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    ingest(
        api,
        [
            user_event("event-anchor", "Manual segment anchor", "2026-06-12T15:00:01Z"),
            user_event("event-anchor-2", "Manual segment second anchor", "2026-06-12T15:00:02Z"),
        ],
    )

    started = api.post(
        "/v1/segments/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.segment_start.v0",
            "session_id": "session-seg",
            "segment_id": "segment-manual",
            "title": "Manual segment",
            "summary": "Manual lifecycle segment",
            "anchor_event_ids": ["event-anchor", "event-anchor-2"],
            "provenance": {"event_id": "event-anchor"},
        },
    )
    assert started.status_code == 200, started.text
    segment = started.json()["segment"]
    assert segment["schema_version"] == "mneme.segment.v0"
    assert segment["segment_id"] == "segment-manual"
    assert segment["session_id"] == "session-seg"
    assert segment["project_isolation_key"] == "project-1"
    assert segment["status"] == "OPEN"
    assert segment["created_by"] == "ADAPTER"
    assert segment["anchor_event_ids"] == ["event-anchor", "event-anchor-2"]

    exported = api.get("/v1/sessions/session-seg/export", headers=auth_headers())
    assert exported.status_code == 200, exported.text
    assert any(
        edge["source_event_id"] == "event-anchor"
        and edge["target_event_id"] == "event-anchor-2"
        and edge["edge_type"] == "SEGMENT_ANCHOR"
        for edge in exported.json()["event_graph_edges"]
    )

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-seg", "seed_event_id": "event-anchor-2", "depth": 1, "max_events": 5},
    )
    assert expanded.status_code == 200, expanded.text
    edge_by_id = {item["event_id"]: item["edge"] for item in expanded.json()["data"]["events"]}
    assert edge_by_id["event-anchor"] == "SEGMENT_ANCHOR"

    listed = api.get("/v1/segments?session_id=session-seg&page_size=10", headers=auth_headers())
    assert listed.status_code == 200, listed.text
    listed_segment = next(item for item in listed.json()["segments"] if item["segment_id"] == "segment-manual")
    assert listed_segment["status"] == "OPEN"

    fetched = api.get("/v1/segments/segment-manual", headers=auth_headers())
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["segment"]["title"] == "Manual segment"

    events = api.get("/v1/segments/segment-manual/events?page_size=5", headers=auth_headers())
    assert events.status_code == 200, events.text
    event_summary = events.json()["events"][0]
    assert event_summary["schema_version"] == "mneme.event_summary.v0"
    assert event_summary["event_id"] == "event-anchor"
    assert event_summary["importance"] == "NORMAL"
    assert event_summary["freshness"] == "RECENT"
    assert event_summary["redaction_applied"] is True

    closed = api.post(
        "/v1/segments/segment-manual/close",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.segment_close.v0",
            "session_id": "session-seg",
            "summary": "Closed manually",
            "outcome": "COMPLETED",
            "anchor_event_ids": ["event-anchor"],
            "provenance": {"event_id": "event-anchor"},
        },
    )
    assert closed.status_code == 200, closed.text
    assert closed.json()["segment"]["status"] == "CLOSED"
    assert closed.json()["segment"]["outcome"] == "COMPLETED"
    assert closed.json()["segment"]["closed_at"]


def test_automatic_segment_members_emit_segment_member_edges(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    ingest(
        api,
        [
            user_event("event-segment-root", "Parser parity work", "2026-06-12T15:00:01Z"),
            user_event("event-segment-member", "Continue parser parity work", "2026-06-12T15:00:02Z"),
        ],
    )

    exported = api.get("/v1/sessions/session-seg/export", headers=auth_headers())

    assert exported.status_code == 200, exported.text
    assert any(
        edge["source_event_id"] == "event-segment-root"
        and edge["target_event_id"] == "event-segment-member"
        and edge["edge_type"] == "SEGMENT_MEMBER"
        and edge["weight"] == 0.5
        for edge in exported.json()["event_graph_edges"]
    )


def test_segment_start_generates_id_only_with_idempotency_key(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    payload = {
        "schema_version": "mneme.segment_start.v0",
        "session_id": "session-seg",
        "title": "Generated segment",
        "provenance": {"turn_id": "turn-generated"},
    }

    missing_key = api.post("/v1/segments/start", headers=auth_headers(), json=payload)
    assert missing_key.status_code == 422
    assert missing_key.json()["error"]["details"]["field"] == "segment_id"

    headers = {**auth_headers(), "Idempotency-Key": "segment-generate-key"}
    first = api.post("/v1/segments/start", headers=headers, json=payload)
    replay = api.post("/v1/segments/start", headers=headers, json=payload)

    assert first.status_code == 200, first.text
    assert replay.status_code == 200, replay.text
    assert first.json() == replay.json()
    assert first.json()["segment"]["segment_id"].startswith("segment-")


def test_event_importance_and_segment_created_by_enums_validate(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)

    invalid_importance = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-seg",
            "events": [
                {
                    **user_event("event-invalid-importance", "Invalid importance", "2026-06-12T15:00:01Z"),
                    "importance": "URGENT",
                }
            ],
        },
    )
    assert invalid_importance.status_code == 422
    assert invalid_importance.json()["error"]["details"]["field"] == "importance"

    valid_event = user_event("event-valid-importance", "Valid importance", "2026-06-12T15:00:02Z")
    ingest(api, [{**valid_event, "importance": "HIGH"}])

    invalid_created_by = api.post(
        "/v1/segments/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.segment_start.v0",
            "session_id": "session-seg",
            "segment_id": "segment-invalid-created-by",
            "created_by": "ROBOT",
            "anchor_event_ids": ["event-valid-importance"],
            "provenance": {"event_id": "event-valid-importance"},
        },
    )
    assert invalid_created_by.status_code == 422
    assert invalid_created_by.json()["error"]["details"]["field"] == "created_by"

    valid_created_by = api.post(
        "/v1/segments/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.segment_start.v0",
            "session_id": "session-seg",
            "segment_id": "segment-valid-created-by",
            "created_by": "IMPORTER",
            "anchor_event_ids": ["event-valid-importance"],
            "provenance": {"event_id": "event-valid-importance"},
        },
    )
    assert valid_created_by.status_code == 200, valid_created_by.text
    assert valid_created_by.json()["segment"]["created_by"] == "IMPORTER"

    events = api.get("/v1/segments/segment-valid-created-by/events?page_size=5", headers=auth_headers())
    assert events.status_code == 200, events.text
    assert events.json()["events"][0]["importance"] == "HIGH"

    invalid_status = api.get("/v1/segments?session_id=session-seg&status=BOGUS", headers=auth_headers())
    assert invalid_status.status_code == 422
    assert invalid_status.json()["error"]["details"]["field"] == "status"

    invalid_outcome = api.post(
        "/v1/segments/segment-valid-created-by/close",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.segment_close.v0",
            "session_id": "session-seg",
            "outcome": "FAILED",
            "provenance": {"event_id": "event-valid-importance"},
        },
    )
    assert invalid_outcome.status_code == 422
    assert invalid_outcome.json()["error"]["details"]["field"] == "outcome"

    abandoned = api.post(
        "/v1/segments/segment-valid-created-by/close",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.segment_close.v0",
            "session_id": "session-seg",
            "outcome": "ABANDONED",
            "provenance": {"event_id": "event-valid-importance"},
        },
    )
    assert abandoned.status_code == 200, abandoned.text
    assert abandoned.json()["segment"]["status"] == "ABANDONED"
    assert abandoned.json()["segment"]["outcome"] == "ABANDONED"
    assert abandoned.json()["segment"]["closed_at"]

    abandoned_list = api.get("/v1/segments?session_id=session-seg&status=ABANDONED", headers=auth_headers())
    assert abandoned_list.status_code == 200, abandoned_list.text
    assert [segment["segment_id"] for segment in abandoned_list.json()["segments"]] == ["segment-valid-created-by"]

    superseded_start = api.post(
        "/v1/segments/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.segment_start.v0",
            "session_id": "session-seg",
            "segment_id": "segment-superseded",
            "anchor_event_ids": ["event-valid-importance"],
        },
    )
    assert superseded_start.status_code == 200, superseded_start.text

    superseded = api.post(
        "/v1/segments/segment-superseded/close",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.segment_close.v0",
            "session_id": "session-seg",
            "outcome": "SUPERSEDED",
            "provenance": {"event_id": "event-valid-importance"},
        },
    )
    assert superseded.status_code == 200, superseded.text
    assert superseded.json()["segment"]["status"] == "SUPERSEDED"
    assert superseded.json()["segment"]["outcome"] == "SUPERSEDED"


def test_segment_close_replays_with_idempotency_key(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    start = api.post(
        "/v1/segments/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.segment_start.v0",
            "session_id": "session-seg",
            "segment_id": "segment-close-replay",
            "title": "Close replay",
            "provenance": {"turn_id": "turn-close"},
        },
    )
    assert start.status_code == 200, start.text
    payload = {
        "schema_version": "mneme.segment_close.v0",
        "session_id": "session-seg",
        "summary": "Closed once",
        "outcome": "COMPLETED",
        "provenance": {"turn_id": "turn-close"},
    }
    headers = {**auth_headers(), "Idempotency-Key": "segment-close-replay"}

    first = api.post("/v1/segments/segment-close-replay/close", headers=headers, json=payload)
    replay = api.post("/v1/segments/segment-close-replay/close", headers=headers, json=payload)

    assert first.status_code == 200, first.text
    assert replay.status_code == 200, replay.text
    assert first.json() == replay.json()


def test_segment_close_idempotency_key_rejects_conflict(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    start = api.post(
        "/v1/segments/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.segment_start.v0",
            "session_id": "session-seg",
            "segment_id": "segment-close-conflict",
            "title": "Close conflict",
            "provenance": {"turn_id": "turn-close"},
        },
    )
    assert start.status_code == 200, start.text
    headers = {**auth_headers(), "Idempotency-Key": "segment-close-conflict"}
    first_payload = {
        "schema_version": "mneme.segment_close.v0",
        "session_id": "session-seg",
        "summary": "First close",
        "outcome": "COMPLETED",
        "provenance": {"turn_id": "turn-close"},
    }
    second_payload = {
        "schema_version": "mneme.segment_close.v0",
        "session_id": "session-seg",
        "summary": "Different close",
        "outcome": "COMPLETED",
        "provenance": {"turn_id": "turn-close"},
    }

    first = api.post("/v1/segments/segment-close-conflict/close", headers=headers, json=first_payload)
    conflict = api.post("/v1/segments/segment-close-conflict/close", headers=headers, json=second_payload)

    assert first.status_code == 200, first.text
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"


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


def test_trusted_tool_domain_shift_contributes_to_segment_drift_score_trace(tmp_path: Path) -> None:
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                static_tokens=(
                    StaticTokenSettings(
                        name="project-1-adapter",
                        token="project-1-token",
                        project_scopes=("project-1",),
                        role="ADAPTER",
                    ),
                ),
                drift_threshold=0.5,
                drift_weights=(0.1, 0.1, 0.8),
            )
        )
    )
    start_session(api)
    ingest(api, [user_event("event-1", "Continue parser work", "2026-06-12T15:00:01Z")])
    owner_shift = user_event("event-2", "Continue after owner metadata", "2026-06-12T15:00:02Z")
    owner_shift["metadata"] = {
        "tool_domain": "git",
        "tool_domain_shift": True,
        "secret": "sk-test-domain-secret",
    }
    ingest(api, [owner_shift])

    owner_segments = api.post(
        "/v1/tools/list_segments",
        headers=auth_headers(),
        json={"session_id": "session-seg", "status": "ANY", "page_size": 10},
    )
    assert owner_segments.status_code == 200, owner_segments.text
    assert len(owner_segments.json()["data"]["segments"]) == 1

    adapter_shift = user_event("event-3", "Continue after adapter metadata", "2026-06-12T15:00:03Z")
    adapter_shift["metadata"] = {
        "tool_domain": "git",
        "tool_domain_shift": True,
        "secret": "sk-test-domain-secret",
    }
    ingest(api, [adapter_shift], token="project-1-token")

    exported = api.get("/v1/sessions/session-seg/export", headers=auth_headers())
    assert exported.status_code == 200, exported.text
    traces = [
        trace
        for trace in exported.json()["traces"]
        if trace.get("trace_type") == "SEGMENT_DRIFT" and trace.get("event_id") == "event-3"
    ]
    assert len(traces) == 1
    trace = traces[0]
    assert trace["decision"]["intent"] == "NEW_TASK"
    assert trace["decision"]["drift_reason"] == "TOOL_DOMAIN_SHIFT"
    assert trace["decision"]["drift_score"] == 0.9
    assert trace["decision"]["drift_threshold"] == 0.5
    assert trace["decision"]["drift_components"] == {
        "embedding_distance": 0.0,
        "topic_entropy": 1.0,
        "tool_domain_shift_score": 1.0,
    }
    assert trace["decision"]["drift_weights"] == {
        "embedding": 0.1,
        "topic_entropy": 0.1,
        "tool_domain": 0.8,
    }
    assert trace["signals"]["tool_domain_shift"] is True
    assert trace["signals"]["tool_domain_shift_trusted"] is True
    assert trace["signals"]["tool_domain"] == "git"
    assert trace["segment_effect"]["closed_event_count"] == 2
    assert trace["segment_effect"]["opened_event_count"] == 1
    assert "sk-test-domain-secret" not in str(trace)


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
