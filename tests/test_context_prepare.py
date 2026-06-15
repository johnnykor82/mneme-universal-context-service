from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import Settings


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def client(tmp_path: Path, **overrides: Any) -> TestClient:
    settings = Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN, **overrides)
    return TestClient(create_app(settings))


def start_session(api: TestClient, session_id: str) -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": session_id,
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": "project-1",
            "model": "test-model",
            "tokenizer": "approx",
            "context_window_tokens": 100000,
            "cost_mode": "STANDARD",
            "started_at": "2026-06-12T20:00:00Z",
        },
    )
    assert response.status_code == 200, response.text


def event(
    session_id: str,
    event_id: str,
    text: str,
    *,
    event_type: str = "USER_MESSAGE",
    role: str = "USER",
    turn_id: str = "turn-1",
    timestamp: str = "2026-06-12T20:00:01Z",
) -> dict[str, Any]:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": session_id,
        "turn_id": turn_id,
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "role": role,
        "type": event_type,
        "timestamp": timestamp,
        "content": {"format": "TEXT", "text": text},
        "parent_event_ids": [],
    }


def ingest(api: TestClient, session_id: str, events: list[dict[str, Any]]) -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": session_id, "events": events},
    )
    assert response.status_code == 200, response.text


def prepare(api: TestClient, session_id: str, *, query: str, scope: str = "LINEAGE") -> dict[str, Any]:
    response = api.post(
        "/v1/context/prepare",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.context_prepare_request.v0",
            "request_id": f"prepare-{session_id}",
            "prepare_id": f"prepare-{session_id}",
            "session_id": session_id,
            "turn_id": "turn-prepare",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "model": "test-model",
            "context_window_tokens": 100000,
            "budget_tokens": 1600,
            "request_messages": [
                {"schema_version": "mneme.message.v0", "role": "SYSTEM", "content": "system"},
                {"schema_version": "mneme.message.v0", "role": "USER", "content": "Continue."},
            ],
            "policy": {
                "mode": "AUTO",
                "cost_mode": "STANDARD",
                "include_execution_state": True,
                "include_retrieved_events": True,
                "include_recent_tail": False,
                "budget_split": {
                    "execution_state_ratio": 0.20,
                    "retrieved_context_ratio": 0.30,
                    "recent_tail_ratio": 0.40,
                    "headroom_ratio": 0.10,
                },
                "retrieval": {"query": query, "top_k": 5, "scope": scope},
            },
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def generated_content(body: dict[str, Any]) -> str:
    generated = [message for message in body["messages"] if message.get("metadata", {}).get("mneme_generated")]
    assert generated
    return generated[0]["content"]


def test_context_prepare_adds_memory_hint_goal_trail_and_checkpoint(tmp_path: Path) -> None:
    api = client(
        tmp_path,
        checkpoint_after_n_memory_calls=2,
        goal_trail_size=2,
        memory_access_hint_enabled=True,
    )
    start_session(api, "session-prepare")
    ingest(
        api,
        "session-prepare",
        [
            event("session-prepare", "event-goal-1", "Build provider parity", timestamp="2026-06-12T20:00:01Z"),
            event("session-prepare", "event-goal-2", "Continue context prepare parity", timestamp="2026-06-12T20:00:02Z"),
        ],
    )

    search = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-prepare", "query": "context prepare parity", "top_k": 1},
    )
    assert search.status_code == 200
    fetch = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-prepare", "event_id": "event-goal-2"},
    )
    assert fetch.status_code == 200

    body = prepare(api, "session-prepare", query="context prepare parity")
    content = generated_content(body)

    assert "[MNEME MEMORY ACCESS]" in content
    assert "[MNEME GOAL TRAIL]" in content
    assert "Build provider parity" in content
    assert "Continue context prepare parity" in content
    assert "[MNEME CHECKPOINT]" in content
    assert "event-goal-2" in content
    assert body["trace"]["context_blocks"] >= 4
    assert body["adapter_metadata"]["can_insert_automatically"] is False
    assert "host hook" in body["adapter_metadata"]["insertion_mode"]


def test_context_prepare_can_use_global_cross_session_candidates(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api, "session-source")
    ingest(
        api,
        "session-source",
        [event("session-source", "event-global", "global oauth callback evidence")],
    )
    start_session(api, "session-target")

    body = prepare(api, "session-target", query="global oauth callback", scope="GLOBAL")
    content = generated_content(body)

    assert "event-global" in content
    assert "global oauth callback evidence" in content
    assert body["trace"]["cross_session_event_ids"] == ["event-global"]
