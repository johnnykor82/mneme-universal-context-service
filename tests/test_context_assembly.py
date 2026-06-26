from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import Settings
from mneme_service.utils import token_estimate


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))


def start_session(api: TestClient) -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-assembly",
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
    event_id: str,
    text: str,
    *,
    event_type: str = "USER_MESSAGE",
    role: str = "USER",
    turn_id: str = "turn-1",
    tool_name: str | None = None,
    timestamp: str = "2026-06-12T20:00:01Z",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": "session-assembly",
        "turn_id": turn_id,
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "role": role,
        "type": event_type,
        "timestamp": timestamp,
        "content": {"format": "TEXT", "text": text},
        "parent_event_ids": [],
    }
    if tool_name:
        payload["tool"] = {"name": tool_name, "call_id": f"{event_id}-call"}
    return payload


def ingest(api: TestClient, events: list[dict[str, Any]]) -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": "session-assembly", "events": events},
    )
    assert response.status_code == 200, response.text


def seed_execution_state(api: TestClient) -> None:
    start_session(api)
    ingest(
        api,
        [
            event("event-goal", "Ship semantic retrieval parity", timestamp="2026-06-12T20:00:01Z"),
            event(
                "event-tool-call",
                "run pytest",
                event_type="TOOL_CALL",
                role="ASSISTANT",
                tool_name="pytest",
                timestamp="2026-06-12T20:00:02Z",
            ),
            event(
                "event-tool-output",
                "pytest passed",
                event_type="TOOL_OUTPUT",
                role="TOOL",
                tool_name="pytest",
                timestamp="2026-06-12T20:00:03Z",
            ),
            event(
                "event-decision",
                "Decision: keep REST retrieval canonical",
                event_type="DECISION",
                role="ASSISTANT",
                timestamp="2026-06-12T20:00:04Z",
            ),
            event(
                "event-step",
                "Now add budgeted context assembly",
                turn_id="turn-2",
                timestamp="2026-06-12T20:00:05Z",
            ),
        ],
    )


def prepare(api: TestClient) -> dict[str, Any]:
    response = api.post(
        "/v1/context/prepare",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.context_prepare_request.v0",
            "request_id": "prepare-state",
            "prepare_id": "prepare-state",
            "session_id": "session-assembly",
            "turn_id": "turn-3",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "model": "test-model",
            "context_window_tokens": 100000,
            "budget_tokens": 1200,
            "request_messages": [
                {"schema_version": "mneme.message.v0", "role": "SYSTEM", "content": "system"},
                {"schema_version": "mneme.message.v0", "role": "USER", "content": "Continue."},
            ],
            "policy": {
                "mode": "AUTO",
                "cost_mode": "STANDARD",
                "include_execution_state": True,
                "include_retrieved_events": False,
                "include_recent_tail": False,
                "budget_split": {
                    "execution_state_ratio": 0.20,
                    "retrieved_evidence_ratio": 0.30,
                    "protected_tail_ratio": 0.40,
                    "headroom_ratio": 0.10,
                },
                "retrieval": {"query": "zzzz unmatched", "top_k": 5},
            },
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def prepare_truncated_execution_state(api: TestClient) -> dict[str, Any]:
    response = api.post(
        "/v1/context/prepare",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.context_prepare_request.v0",
            "request_id": "prepare-state-truncated",
            "prepare_id": "prepare-state-truncated",
            "session_id": "session-assembly",
            "turn_id": "turn-state-truncated",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "model": "test-model",
            "context_window_tokens": 100000,
            "budget_tokens": 120,
            "request_messages": [
                {"schema_version": "mneme.message.v0", "role": "SYSTEM", "content": "system"},
                {"schema_version": "mneme.message.v0", "role": "USER", "content": "Continue."},
            ],
            "policy": {
                "mode": "AUTO",
                "cost_mode": "STANDARD",
                "include_execution_state": True,
                "include_retrieved_events": False,
                "include_recent_tail": False,
                "budget_split": {
                    "execution_state_ratio": 0.05,
                    "retrieved_evidence_ratio": 0.0,
                    "protected_tail_ratio": 0.85,
                    "headroom_ratio": 0.10,
                },
                "retrieval": {"query": "zzzz unmatched", "top_k": 5},
            },
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def prepare_long_tail(api: TestClient) -> dict[str, Any]:
    old_message = "oldest message should be dropped " + ("alpha " * 120)
    recent_assistant = "recent assistant summary should stay " + ("delta " * 10)
    final_user = "final protected user request should stay " + ("gamma " * 12)
    response = api.post(
        "/v1/context/prepare",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.context_prepare_request.v0",
            "request_id": "prepare-tail",
            "prepare_id": "prepare-tail",
            "session_id": "session-assembly",
            "turn_id": "turn-tail",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "model": "test-model",
            "context_window_tokens": 100000,
            "budget_tokens": 180,
            "request_messages": [
                {"schema_version": "mneme.message.v0", "role": "SYSTEM", "content": "system prompt"},
                {"schema_version": "mneme.message.v0", "role": "USER", "content": old_message},
                {"schema_version": "mneme.message.v0", "role": "ASSISTANT", "content": recent_assistant},
                {"schema_version": "mneme.message.v0", "role": "USER", "content": final_user},
            ],
            "policy": {
                "mode": "AUTO",
                "cost_mode": "STANDARD",
                "preserve_system_prompt": True,
                "include_execution_state": False,
                "include_retrieved_events": False,
                "include_recent_tail": True,
                "budget_split": {
                    "execution_state_ratio": 0.0,
                    "retrieved_evidence_ratio": 0.0,
                    "protected_tail_ratio": 0.90,
                    "headroom_ratio": 0.10,
                },
                "retrieval": {"query": "zzzz unmatched", "top_k": 5},
            },
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def seed_retrieved_budget(api: TestClient) -> None:
    start_session(api)
    ingest(
        api,
        [
            event(
                "event-long",
                "retrievalbudget " + ("large over budget evidence " * 80),
                timestamp="2026-06-12T20:00:01Z",
            ),
            event(
                "event-short",
                "retrievalbudget winner concise evidence",
                timestamp="2026-06-12T20:00:02Z",
            ),
        ],
    )


def prepare_retrieved_budget(api: TestClient) -> dict[str, Any]:
    response = api.post(
        "/v1/context/prepare",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.context_prepare_request.v0",
            "request_id": "prepare-retrieved",
            "prepare_id": "prepare-retrieved",
            "session_id": "session-assembly",
            "turn_id": "turn-retrieved",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "model": "test-model",
            "context_window_tokens": 100000,
            "budget_tokens": 200,
            "request_messages": [
                {"schema_version": "mneme.message.v0", "role": "SYSTEM", "content": "system"},
                {"schema_version": "mneme.message.v0", "role": "USER", "content": "Continue."},
            ],
            "policy": {
                "mode": "AUTO",
                "cost_mode": "STANDARD",
                "include_execution_state": False,
                "include_retrieved_events": True,
                "include_recent_tail": False,
                "budget_split": {
                    "execution_state_ratio": 0.0,
                    "retrieved_evidence_ratio": 0.20,
                    "protected_tail_ratio": 0.70,
                    "headroom_ratio": 0.10,
                },
                "retrieval": {"query": "retrievalbudget winner", "top_k": 5},
            },
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def seed_collision_budget(api: TestClient) -> None:
    start_session(api)
    ingest(
        api,
        [
            event(
                "event-collision",
                "collisionmatch winner concise evidence",
                timestamp="2026-06-12T20:00:01Z",
            )
        ],
    )


def prepare_collision_budget(api: TestClient) -> dict[str, Any]:
    old_message = "old collision context should be dropped " + ("alpha " * 120)
    recent_assistant = "recent collision assistant should stay " + ("delta " * 8)
    final_user = "final collision user request should stay " + ("gamma " * 8)
    system_prompt = "system collision prompt " + ("system " * 24)
    response = api.post(
        "/v1/context/prepare",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.context_prepare_request.v0",
            "request_id": "prepare-collision",
            "prepare_id": "prepare-collision",
            "session_id": "session-assembly",
            "turn_id": "turn-collision",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "model": "test-model",
            "context_window_tokens": 100000,
            "budget_tokens": 120,
            "request_messages": [
                {"schema_version": "mneme.message.v0", "role": "SYSTEM", "content": system_prompt},
                {"schema_version": "mneme.message.v0", "role": "USER", "content": old_message},
                {"schema_version": "mneme.message.v0", "role": "ASSISTANT", "content": recent_assistant},
                {"schema_version": "mneme.message.v0", "role": "USER", "content": final_user},
            ],
            "policy": {
                "mode": "AUTO",
                "cost_mode": "STANDARD",
                "preserve_system_prompt": True,
                "include_execution_state": False,
                "include_retrieved_events": True,
                "include_recent_tail": True,
                "budget_split": {
                    "execution_state_ratio": 0.0,
                    "retrieved_evidence_ratio": 0.60,
                    "protected_tail_ratio": 0.20,
                    "headroom_ratio": 0.20,
                },
                "retrieval": {"query": "collisionmatch winner", "top_k": 5},
            },
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_context_prepare_inserts_execution_state_block_without_persisting_it(tmp_path: Path) -> None:
    api = client(tmp_path)
    seed_execution_state(api)

    body = prepare(api)

    assert body["changed"] is True
    generated = [message for message in body["messages"] if message.get("metadata", {}).get("mneme_generated")]
    assert len(generated) == 1
    assert "[MNEME EXECUTION STATE]" in generated[0]["content"]
    assert "Ship semantic retrieval parity" in generated[0]["content"]
    assert "Now add budgeted context assembly" in generated[0]["content"]
    assert "pytest" in generated[0]["content"]
    assert body["trace"]["execution_state_tokens"] > 0
    assert body["trace"]["retrieved_tokens"] == 0
    assert body["trace"]["minimum_headroom_tokens"] == 120
    assert body["trace"]["execution_state_compression_level"] in {"FULL", "COMPACT", "MINIMAL", "TRUNCATED", "DROPPED_FOR_BUDGET"}
    assert body["trace"]["unused_context_slack_tokens"] >= 0
    assert "execution_state_ratio" in body["trace"]["budget_split"]
    assert body["trace"]["selected_event_ids"] == []

    exported = api.get("/v1/sessions/session-assembly/export", headers=auth_headers())
    assert exported.status_code == 200
    assert "[MNEME EXECUTION STATE]" not in str(exported.json()["events"])


def test_context_prepare_trace_reports_truncated_execution_state_compression_level(tmp_path: Path) -> None:
    api = client(tmp_path)
    seed_execution_state(api)

    body = prepare_truncated_execution_state(api)

    assert body["changed"] is True
    assert body["trace"]["execution_state_compression_level"] == "TRUNCATED"
    assert "EXECUTION_STATE_TRUNCATED" in body["trace"]["warnings"]
    stored_trace = api.get(f"/v1/traces/{body['trace_id']}", headers=auth_headers())
    assert stored_trace.status_code == 200
    assert stored_trace.json()["execution_state_compression_level"] == "TRUNCATED"
    assert "EXECUTION_STATE_TRUNCATED" in stored_trace.json()["warnings"]


def test_context_prepare_packs_retrieved_context_and_traces_dropped_events(tmp_path: Path) -> None:
    api = client(tmp_path)
    seed_retrieved_budget(api)

    body = prepare_retrieved_budget(api)

    assert body["changed"] is True
    generated = [message for message in body["messages"] if message.get("metadata", {}).get("mneme_generated")]
    assert len(generated) == 1
    assert "event-short" in generated[0]["content"]
    assert "event-long" not in generated[0]["content"]
    assert body["trace"]["retrieved_tokens"] <= body["trace"]["retrieved_evidence_budget_tokens"]
    assert body["trace"]["selected_event_ids"] == ["event-short"]
    assert body["trace"]["dropped_event_refs"] == [
        {"event_id": "event-long", "reason": "RETRIEVED_CONTEXT_BUDGET_EXCEEDED"}
    ]

    stored_trace = api.get(f"/v1/traces/{body['trace_id']}", headers=auth_headers())
    assert stored_trace.status_code == 200
    assert stored_trace.json()["dropped_events"] == [
        {"event_id": "event-long", "reason": "RETRIEVED_CONTEXT_BUDGET_EXCEEDED"}
    ]


def test_context_prepare_resolves_collision_by_dropping_retrieved_context(tmp_path: Path) -> None:
    api = client(tmp_path)
    seed_collision_budget(api)

    body = prepare_collision_budget(api)

    assert body["changed"] is True
    assert not [message for message in body["messages"] if message.get("metadata", {}).get("mneme_generated")]
    rendered = "\n".join(message["content"] for message in body["messages"])
    assert "final collision user request should stay" in rendered
    assert "old collision context should be dropped" not in rendered
    assert body["trace"]["retrieved_tokens"] == 0
    assert body["trace"]["selected_event_ids"] == []
    assert body["trace"]["dropped_event_refs"] == [
        {"event_id": "event-collision", "reason": "CONTEXT_COLLISION_BUDGET_EXCEEDED"}
    ]
    assembled_tokens = sum(token_estimate(message["content"]) for message in body["messages"])
    assert assembled_tokens + body["trace"]["headroom_tokens"] <= body["trace"]["budget_tokens"]


def test_context_prepare_protects_recent_tail_when_request_exceeds_budget(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)

    body = prepare_long_tail(api)

    assert body["changed"] is True
    assert not [message for message in body["messages"] if message.get("metadata", {}).get("mneme_generated")]
    rendered = "\n".join(message["content"] for message in body["messages"])
    assert body["messages"][0]["role"] == "SYSTEM"
    assert "recent assistant summary should stay" in rendered
    assert "final protected user request should stay" in rendered
    assert "oldest message should be dropped" not in rendered
    assert body["trace"]["input_request_tokens"] > body["trace"]["budget_tokens"]
    assert body["trace"]["protected_tail_tokens"] > 0
    assert body["trace"]["retrieved_tokens"] == 0
    assert body["trace"]["selected_event_ids"] == []
