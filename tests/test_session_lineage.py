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
        "started_at": "2026-06-12T17:00:00Z",
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
        "timestamp": "2026-06-12T17:00:01Z",
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


def test_lineage_carry_over_searches_parent_without_copying_events(tmp_path: Path) -> None:
    api = client(tmp_path)
    start(api, session_payload("session-parent"))
    ingest(
        api,
        user_event("event-parent", "Legacy parser context lives in the parent session", session_id="session-parent"),
        session_id="session-parent",
    )

    child = start(
        api,
        session_payload(
            "session-child",
            metadata={"lifecycle": "RESUME", "parent_session_id": "session-parent"},
        ),
    )
    assert child["session_state"]["classification"] == "RESUME"

    child_export = api.get("/v1/sessions/session-child/export", headers=auth_headers())
    assert child_export.status_code == 200
    assert child_export.json()["events"] == []
    assert child_export.json()["session_lineage"] == [
        {
            "schema_version": "mneme.session_lineage.v0",
            "old_session_id": "session-parent",
            "new_session_id": "session-child",
        }
    ]

    search = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-child", "query": "legacy parser", "scope": "SESSION", "top_k": 5},
    )
    assert search.status_code == 200, search.text
    assert search.json()["data"]["results"] == []

    lineage_search = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-child", "query": "legacy parser", "scope": "LINEAGE", "top_k": 5},
    )
    assert lineage_search.status_code == 200, lineage_search.text
    results = lineage_search.json()["data"]["results"]
    assert [item["event_id"] for item in results] == ["event-parent"]

    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-child", "event_id": "event-parent", "include_neighbors": False},
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["data"]["event"]["session_id"] == "session-parent"

    child_export_after_search = api.get("/v1/sessions/session-child/export", headers=auth_headers())
    assert child_export_after_search.status_code == 200
    assert all(event["event_id"] != "event-parent" for event in child_export_after_search.json()["events"])


def test_unrelated_sessions_do_not_share_carry_over_results(tmp_path: Path) -> None:
    api = client(tmp_path)
    start(api, session_payload("session-parent"))
    ingest(
        api,
        user_event("event-parent", "Private billing migration context", session_id="session-parent"),
        session_id="session-parent",
    )
    start(api, session_payload("session-unrelated"))

    search = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-unrelated", "query": "billing migration", "scope": "SESSION", "top_k": 5},
    )

    assert search.status_code == 200, search.text
    assert search.json()["data"]["results"] == []
