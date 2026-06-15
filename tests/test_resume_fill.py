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


def session_payload(session_id: str, *, metadata: dict | None = None) -> dict:
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
        "started_at": "2026-06-12T18:00:00Z",
        "metadata": metadata or {"cwd": "/repo"},
        "privacy": {
            "project_isolation_key": "project-1",
            "retention_days": 30,
            "redaction_profile": "DEFAULT",
            "redaction_policy": "IRREVERSIBLE",
        },
    }


def user_event(event_id: str, text: str, *, session_id: str) -> dict:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": session_id,
        "turn_id": "turn-1",
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "role": "USER",
        "type": "USER_MESSAGE",
        "timestamp": "2026-06-12T18:00:01Z",
        "content": {"format": "TEXT", "text": text},
        "parent_event_ids": [],
    }


def start(api: TestClient, payload: dict) -> dict:
    response = api.post("/v1/sessions/start", headers=auth_headers(), json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def ingest(api: TestClient, event: dict, *, session_id: str) -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": session_id, "events": [event]},
    )
    assert response.status_code == 200, response.text


def prepare(api: TestClient, session_id: str, request_id: str) -> dict:
    response = api.post(
        "/v1/context/prepare",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.context_prepare_request.v0",
            "request_id": request_id,
            "prepare_id": request_id,
            "session_id": session_id,
            "turn_id": "turn-resume",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "model": "test-model",
            "context_window_tokens": 100000,
            "budget_tokens": 2000,
            "request_messages": [
                {"schema_version": "mneme.message.v0", "role": "USER", "content": "Start the next step."}
            ],
            "policy": {
                "mode": "AUTO",
                "cost_mode": "STANDARD",
                "include_retrieved_events": True,
                "retrieval": {"query": "zzzz qqqq unmatched", "top_k": 5},
            },
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_first_context_prepare_after_resume_forces_prior_context_once(tmp_path: Path) -> None:
    api = client(tmp_path)
    start(api, session_payload("session-resume"))
    ingest(
        api,
        user_event("event-prior", "Prior parser decision should be carried into resume.", session_id="session-resume"),
        session_id="session-resume",
    )

    resumed = start(api, session_payload("session-resume", metadata={"cwd": "/repo", "lifecycle": "RESUME"}))
    assert resumed["session_state"]["requires_context_fill"] is True

    first = prepare(api, "session-resume", "prepare-resume-1")
    assert first["changed"] is True
    assert first["trace"]["selected_event_ids"] == ["event-prior"]
    assert first["trace"]["selected_event_refs"][0]["reason"] == "RESUME_CONTEXT_FILL"
    assert "Prior parser decision" in str(first["messages"])

    second = prepare(api, "session-resume", "prepare-resume-2")
    assert second["changed"] is False
    assert second["warnings"] == ["REQUEST_UNDER_BUDGET"]


def test_first_context_prepare_after_lineage_resume_uses_parent_context(tmp_path: Path) -> None:
    api = client(tmp_path)
    start(api, session_payload("session-parent"))
    ingest(
        api,
        user_event("event-parent", "Parent session carries the migration invariant.", session_id="session-parent"),
        session_id="session-parent",
    )

    child = start(
        api,
        session_payload("session-child", metadata={"lifecycle": "RESUME", "parent_session_id": "session-parent"}),
    )
    assert child["session_state"]["requires_context_fill"] is True

    first = prepare(api, "session-child", "prepare-child-1")
    assert first["changed"] is True
    assert first["trace"]["selected_event_ids"] == ["event-parent"]
    assert "Parent session carries" in str(first["messages"])
