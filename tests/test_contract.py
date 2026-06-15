from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import Settings
from mneme_service.tool_names import TOOL_NAMES


TOKEN = "test-token"


def client(tmp_path: Path, *, max_event_content_bytes: int = 1_048_576) -> TestClient:
    settings = Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        insecure_dev=False,
        max_event_content_bytes=max_event_content_bytes,
    )
    return TestClient(create_app(settings))


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def approx_tokens(value: str) -> int:
    return max(1, (len(value) + 3) // 4) if value else 0


def start_session(api: TestClient, session_id: str = "session-1", runtime: str = "HERMES") -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": session_id,
            "agent_id": "agent-1",
            "runtime": runtime,
            "project_id": "project-1",
            "model": "test-model",
            "tokenizer": "approx",
            "context_window_tokens": 100000,
            "cost_mode": "STANDARD",
            "started_at": "2026-06-09T12:00:00Z",
            "metadata": {"cwd": "/repo"},
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
    session_id: str = "session-1",
    turn_id: str = "turn-1",
    event_type: str = "TOOL_OUTPUT",
    role: str = "TOOL",
    parent_event_ids: list[str] | None = None,
    timestamp: str = "2026-06-09T12:00:01Z",
) -> dict:
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
        "tool": {"name": "exec_command", "call_id": "tool-call-1"},
        "parent_event_ids": parent_event_ids or [],
        "metadata": {"authorization": "Bearer sk-test-secret"},
    }


def ingest(api: TestClient, events: list[dict], session_id: str = "session-1"):
    return api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": session_id, "events": events},
    )


def test_auth_health_capabilities_and_session_idempotency(tmp_path: Path) -> None:
    api = client(tmp_path)

    assert api.get("/v1/health").status_code == 200
    assert api.get("/v1/capabilities").status_code == 401

    capabilities = api.get("/v1/capabilities", headers=auth_headers())
    assert capabilities.status_code == 200
    body = capabilities.json()
    assert body["default_cost_mode"] == "STANDARD"
    assert body["supports_embeddings"] is False
    assert body["supports_mcp_tools"] is True
    assert body["mcp_tools"] == list(TOOL_NAMES)
    assert "mneme.event.v0" in body["supported_schema_versions"]["event"]

    start_session(api)
    again = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-1",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "started_at": "2026-06-09T12:00:00Z",
        },
    )
    assert again.status_code == 200
    assert again.json()["created"] is False


def test_event_ingestion_redaction_duplicate_conflict_and_unknown_session(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)

    first = ingest(api, [event("event-1", "pytest failed with sk-test-secret in output")])
    assert first.status_code == 200, first.text
    assert first.json()["accepted"] == 1
    assert first.json()["duplicates"] == 0

    duplicate = ingest(api, [event("event-1", "pytest failed with sk-test-secret in output")])
    assert duplicate.status_code == 200
    assert duplicate.json()["accepted"] == 0
    assert duplicate.json()["duplicates"] == 1

    conflict = ingest(api, [event("event-1", "different immutable content")])
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"

    unsupported = ingest(api, [{**event("event-2", "bad schema"), "schema_version": "mneme.event.v9"}])
    assert unsupported.status_code == 400
    assert unsupported.json()["error"]["code"] == "BAD_REQUEST"

    unknown = ingest(api, [event("event-x", "unknown", session_id="missing-session")], session_id="missing-session")
    assert unknown.status_code == 404

    search = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"query": "pytest secret", "session_id": "session-1", "scope": "SESSION", "top_k": 10},
    )
    assert search.status_code == 200
    payload = search.json()
    assert payload["ok"] is True
    assert "sk-test-secret" not in str(payload)
    assert "[REDACTED]" in str(payload)


def test_oversized_inline_rejected_and_bytes_ref_accepted(tmp_path: Path) -> None:
    api = client(tmp_path, max_event_content_bytes=12)
    start_session(api)

    too_large = ingest(api, [event("event-large", "this text is too large")])
    assert too_large.status_code == 413
    assert too_large.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"

    bytes_ref_event = event("event-ref", "")
    bytes_ref_event["content"] = {
        "format": "BYTES_REF",
        "uri": "file:///tmp/mneme/blob-1",
        "hash": "sha256:abc",
        "size_bytes": 10_000_000,
        "media_type": "text/plain",
    }
    accepted = ingest(api, [bytes_ref_event])
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["accepted"] == 1


def test_memory_tools_audit_memory_read_and_graph_expansion(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    call = event("event-call", "run pytest", event_type="TOOL_CALL")
    output = event("event-output", "pytest failure in context assembler", parent_event_ids=["event-call"])
    decision = event("event-decision", "decided to inspect assembler", event_type="DECISION", role="ASSISTANT", parent_event_ids=["event-output"])
    assert ingest(api, [call, output, decision]).status_code == 200

    search = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"query": "assembler failure", "session_id": "session-1", "scope": "SESSION", "top_k": 5},
    )
    assert search.status_code == 200
    search_body = search.json()
    assert search_body["data"]["results"][0]["event_id"] == "event-output"
    trace_id = search_body["trace_id"]
    assert trace_id

    trace = api.get(f"/v1/traces/{trace_id}", headers=auth_headers())
    assert trace.status_code == 200
    trace_body = trace.json()
    assert trace_body["trace_type"] == "MEMORY_READ"
    assert trace_body["tool"] == "context_search"
    assert trace_body["selected_event_ids"] == [item["event_id"] for item in search_body["data"]["results"]]

    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-1", "event_id": "event-output", "full": True, "include_neighbors": True},
    )
    assert fetched.status_code == 200
    fetched_body = fetched.json()
    assert fetched_body["data"]["neighbors"]

    fetch_trace = api.get(f"/v1/traces/{fetched_body['trace_id']}", headers=auth_headers())
    assert fetch_trace.status_code == 200
    assert set(fetch_trace.json()["selected_event_ids"]) == {"event-output", "event-call", "event-decision"}

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-1", "seed_event_id": "event-output", "mode": "TOOL_CHAIN", "depth": 2, "max_events": 10},
    )
    assert expanded.status_code == 200
    expanded_ids = {item["event_id"] for item in expanded.json()["data"]["events"]}
    assert {"event-call", "event-output", "event-decision"}.issubset(expanded_ids)

    exported = api.get("/v1/sessions/session-1/export", headers=auth_headers())
    assert exported.status_code == 200
    exported_body = exported.json()
    assert len(exported_body["audit_records"]) >= 3
    assert any(item["type"] == "MEMORY_READ" for item in exported_body["events"])


def test_memory_tool_filters_limits_and_segment_page_size(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    events = [
        event("event-error", "pytest crashed in parser", event_type="ERROR", role="RUNTIME", turn_id="turn-1"),
        event("event-old-error", "pytest older parser error", event_type="ERROR", role="RUNTIME", turn_id="turn-0", timestamp="2026-06-09T11:59:59Z"),
        event("event-output", "pytest output should be hidden from recent recall", event_type="TOOL_OUTPUT", role="TOOL", turn_id="turn-2"),
        event("event-decision", "pytest parser fix chosen", event_type="DECISION", role="ASSISTANT", turn_id="turn-3"),
        event("event-note", "small note", event_type="NOTE", role="ASSISTANT", turn_id="turn-4"),
    ]
    assert ingest(api, events).status_code == 200

    filtered = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={
            "query": "pytest",
            "session_id": "session-1",
            "scope": "SESSION",
            "top_k": 10,
            "filters": {
                "event_types": ["ERROR"],
                "after": "2026-06-09T12:00:00Z",
                "before": "2026-06-09T12:00:02Z",
            },
        },
    )
    assert filtered.status_code == 200
    filtered_results = filtered.json()["data"]["results"]
    assert [item["event_id"] for item in filtered_results] == ["event-error"]
    assert all(item["type"] == "ERROR" for item in filtered_results)

    recent = api.post(
        "/v1/tools/recall_recent",
        headers=auth_headers(),
        json={"session_id": "session-1", "turns": 4, "max_tokens": 12, "include_tool_outputs": False},
    )
    assert recent.status_code == 200
    recent_events = recent.json()["data"]["events"]
    recent_ids = [item["event_id"] for item in recent_events]
    assert all(item["type"] != "TOOL_OUTPUT" for item in recent_events)
    assert sum(approx_tokens(item["snippet"]) for item in recent_events) <= 12
    assert "event-note" in recent_ids
    assert "event-old-error" not in recent_ids

    completed = api.post(
        "/v1/turns/complete",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.turn.v0",
            "session_id": "session-1",
            "turn_id": "turn-4",
            "status": "COMPLETED",
            "started_at": "2026-06-09T12:00:00Z",
            "completed_at": "2026-06-09T12:00:45Z",
            "event_ids": ["event-note"],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "tool_call_count": 1},
        },
    )
    assert completed.status_code == 200

    bad_page_size = api.post(
        "/v1/tools/list_segments",
        headers=auth_headers(),
        json={"session_id": "session-1", "status": "ANY", "page_size": 0, "page_token": None},
    )
    assert bad_page_size.status_code == 422

    segments = api.post(
        "/v1/tools/list_segments",
        headers=auth_headers(),
        json={"session_id": "session-1", "status": "ANY", "page_size": 1, "page_token": None},
    )
    assert segments.status_code == 200
    assert len(segments.json()["data"]["segments"]) <= 1


def test_segment_tools_return_manifest_skeleton_and_fetch_metadata(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    events = [
        event(
            "event-user-1",
            "Start parser parity work",
            event_type="USER_MESSAGE",
            role="USER",
            turn_id="turn-1",
            timestamp="2026-06-09T12:00:01Z",
        ),
        event(
            "event-tool-1",
            "run pytest for parser",
            event_type="TOOL_CALL",
            role="ASSISTANT",
            turn_id="turn-1",
            timestamp="2026-06-09T12:00:02Z",
        ),
        event(
            "event-assistant-1",
            "parser parity looks stable",
            event_type="ASSISTANT_MESSAGE",
            role="ASSISTANT",
            turn_id="turn-1",
            timestamp="2026-06-09T12:00:03Z",
        ),
        event(
            "event-user-2",
            "Switch to billing migration",
            event_type="USER_MESSAGE",
            role="USER",
            turn_id="turn-2",
            timestamp="2026-06-09T12:00:04Z",
        ),
    ]
    assert ingest(api, events).status_code == 200

    segments = api.post(
        "/v1/tools/list_segments",
        headers=auth_headers(),
        json={"session_id": "session-1", "status": "ANY", "page_size": 20, "page_token": None},
    )
    assert segments.status_code == 200
    segment_rows = segments.json()["data"]["segments"]
    first_segment = segment_rows[0]
    assert first_segment["events_by_type"]["USER_MESSAGE"] == 1
    assert first_segment["events_by_type"]["TOOL_CALL"] == 1
    assert first_segment["events_by_type"]["ASSISTANT_MESSAGE"] == 1
    assert first_segment["first_user_snippet"] == "Start parser parity work"
    assert first_segment["last_user_snippet"] == "Start parser parity work"
    assert first_segment["goal_at_end"]
    assert "topic_tags" in first_segment

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-1", "seed_event_id": "event-user-1", "mode": "segment", "max_events": 10},
    )
    assert expanded.status_code == 200
    skeleton = expanded.json()["data"]
    assert skeleton["mode"] == "SEGMENT"
    assert skeleton["segment_id"] == first_segment["segment_id"]
    assert [item["event_id"] for item in skeleton["events"]] == [
        "event-user-1",
        "event-tool-1",
        "event-assistant-1",
    ]

    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-1", "event_id": "event-user-1"},
    )
    assert fetched.status_code == 200
    metadata = fetched.json()["data"]["metadata"]
    assert metadata["segment_id"] == first_segment["segment_id"]
    assert metadata["token_estimate"] > 0
    assert metadata["truncated"] is False


def test_context_prepare_validation_trace_and_off_mode(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    assert ingest(api, [event("event-prepare", "important old pytest evidence")]).status_code == 200

    request = {
        "schema_version": "mneme.context_prepare_request.v0",
        "request_id": "prepare-1",
        "prepare_id": "prepare-1",
        "session_id": "session-1",
        "turn_id": "turn-2",
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "model": "test-model",
        "context_window_tokens": 100000,
        "budget_tokens": 2000,
        "request_messages": [
            {"schema_version": "mneme.message.v0", "role": "SYSTEM", "content": "system"},
            {"schema_version": "mneme.message.v0", "role": "USER", "content": "continue pytest work"},
        ],
        "policy": {
            "mode": "AUTO",
            "cost_mode": "STANDARD",
            "preserve_system_prompt": True,
            "include_recent_tail": True,
            "include_retrieved_events": True,
            "retrieval": {"query": "continue pytest work sk-trace-secret", "top_k": 24},
            "budget_split": {
                "execution_state_ratio": 0.05,
                "retrieved_context_ratio": 0.30,
                "recent_tail_ratio": 0.55,
                "headroom_ratio": 0.10,
            },
        },
    }

    prepared = api.post("/v1/context/prepare", headers=auth_headers(), json=request)
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert body["changed"] is True
    assert body["messages"][0]["role"] == "SYSTEM"
    assert body["trace_id"]
    assert body["trace"]["selected_event_ids"] == ["event-prepare"]

    trace = api.get(f"/v1/traces/{body['trace_id']}", headers=auth_headers())
    assert trace.status_code == 200
    assert trace.json()["selected_events"][0]["event_id"] == "event-prepare"
    assert "sk-trace-secret" not in str(trace.json())
    assert "[REDACTED]" in str(trace.json())

    off_request = {**request, "request_id": "prepare-off", "prepare_id": "prepare-off", "policy": {**request["policy"], "mode": "OFF"}}
    off = api.post("/v1/context/prepare", headers=auth_headers(), json=off_request)
    assert off.status_code == 200
    assert off.json()["changed"] is False

    bad_split = {**request, "request_id": "bad-split", "prepare_id": "bad-split"}
    bad_split["policy"] = {**request["policy"], "budget_split": {"execution_state_ratio": 2.0}}
    assert api.post("/v1/context/prepare", headers=auth_headers(), json=bad_split).status_code == 422

    bad_messages = {**request, "request_id": "bad-message", "prepare_id": "bad-message", "request_messages": [{"role": "USER"}]}
    assert api.post("/v1/context/prepare", headers=auth_headers(), json=bad_messages).status_code == 422


def test_turn_complete_cost_export_delete_and_restart_idempotency(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    api = TestClient(create_app(Settings(db_path=db_path, auth_token=TOKEN)))
    runtimes = ["HERMES", "GENERIC_MCP", "LANGGRAPH"]
    for session_idx in range(5):
        session_id = f"session-{session_idx}"
        start_session(api, session_id=session_id, runtime=runtimes[session_idx % len(runtimes)])
        events = [
            event(
                f"event-{session_idx}-{idx}",
                f"synthetic event {idx} runtime {runtimes[session_idx % len(runtimes)]}",
                session_id=session_id,
                turn_id=f"turn-{idx % 5}",
            )
            for idx in range(20)
        ]
        assert ingest(api, events, session_id=session_id).status_code == 200

    completed = api.post(
        "/v1/turns/complete",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.turn.v0",
            "session_id": "session-0",
            "turn_id": "turn-1",
            "status": "COMPLETED",
            "started_at": "2026-06-09T12:00:00Z",
            "completed_at": "2026-06-09T12:00:45Z",
            "event_ids": ["event-0-1"],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "tool_call_count": 1},
        },
    )
    assert completed.status_code == 200

    restarted = TestClient(create_app(Settings(db_path=db_path, auth_token=TOKEN)))
    replay = ingest(restarted, [event("event-0-0", "synthetic event 0 runtime HERMES", session_id="session-0", turn_id="turn-0")], session_id="session-0")
    assert replay.status_code == 200
    assert replay.json()["duplicates"] == 1

    cost = restarted.get("/v1/costs/session/session-0", headers=auth_headers())
    assert cost.status_code == 200
    assert cost.json()["events_ingested"] == 20
    assert cost.json()["embedding_batches"] == 0

    exported = restarted.get("/v1/sessions/session-0/export", headers=auth_headers())
    assert exported.status_code == 200
    assert len(exported.json()["events"]) >= 20

    deleted = restarted.delete("/v1/sessions/session-0", headers={**auth_headers(), "Idempotency-Key": "delete-1"})
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert restarted.get("/v1/sessions/session-0/export", headers=auth_headers()).status_code == 404
