from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import Settings


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))


def session_payload(session_id: str = "session-drift", *, metadata: dict | None = None) -> dict:
    return {
        "schema_version": "mneme.session.v0",
        "session_id": session_id,
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "project_id": "project-1",
        "model": "test-model",
        "tokenizer": "approx",
        "context_window_tokens": 100000,
        "cost_mode": "STANDARD",
        "started_at": "2026-06-12T16:00:00Z",
        "metadata": metadata or {"cwd": "/repo"},
        "privacy": {
            "project_isolation_key": "project-1",
            "retention_days": 30,
            "redaction_profile": "DEFAULT",
            "redaction_policy": "IRREVERSIBLE",
        },
    }


def user_event(event_id: str, *, session_id: str = "session-drift") -> dict:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": session_id,
        "turn_id": "turn-1",
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "role": "USER",
        "type": "USER_MESSAGE",
        "timestamp": "2026-06-12T16:00:01Z",
        "content": {"format": "TEXT", "text": "Continue the parser work"},
        "parent_event_ids": [],
    }


def start(api: TestClient, payload: dict) -> dict:
    response = api.post("/v1/sessions/start", headers=auth_headers(), json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def ingest(api: TestClient, event: dict, *, session_id: str = "session-drift") -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": session_id, "events": [event]},
    )
    assert response.status_code == 200, response.text


def test_new_empty_session_is_classified_fresh(tmp_path: Path) -> None:
    api = client(tmp_path)

    body = start(api, session_payload())

    assert body["created"] is True
    assert body["session_state"]["classification"] == "FRESH"
    assert body["session_state"]["resume_source"] == "NEW_SESSION"
    assert body["session_state"]["signals"]["prior_event_count"] == 0
    assert body["session_state"]["requires_context_fill"] is False


def test_existing_session_with_prior_events_is_classified_resume(tmp_path: Path) -> None:
    api = client(tmp_path)
    start(api, session_payload())
    ingest(api, user_event("event-1"))

    body = start(api, session_payload(metadata={"cwd": "/repo", "lifecycle": "RESUME"}))

    assert body["created"] is False
    assert body["session_state"]["classification"] == "RESUME"
    assert body["session_state"]["resume_source"] == "EXISTING_SESSION_EVENTS"
    assert body["session_state"]["signals"]["prior_event_count"] == 1
    assert body["session_state"]["signals"]["adapter_resume_requested"] is True
    assert body["session_state"]["requires_context_fill"] is True


def test_adapter_lifecycle_metadata_can_classify_new_session_as_resume(tmp_path: Path) -> None:
    api = client(tmp_path)

    body = start(
        api,
        session_payload(
            "session-child",
            metadata={
                "cwd": "/repo",
                "lifecycle": "RESUME",
                "parent_session_id": "session-parent",
            },
        ),
    )

    assert body["created"] is True
    assert body["session_state"]["classification"] == "RESUME"
    assert body["session_state"]["resume_source"] == "ADAPTER_METADATA"
    assert body["session_state"]["signals"]["lineage_session_id"] == "session-parent"
    assert body["session_state"]["requires_context_fill"] is False
