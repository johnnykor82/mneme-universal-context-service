from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Any

import httpx
from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import Settings


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def start_session(api: TestClient, session_id: str = "session-state") -> None:
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
            "started_at": "2026-06-12T14:00:00Z",
        },
    )
    assert response.status_code == 200, response.text


def state_event(
    event_id: str,
    text: str,
    *,
    session_id: str = "session-state",
    event_type: str = "USER_MESSAGE",
    role: str = "USER",
    turn_id: str = "turn-1",
    tool_name: str | None = None,
    timestamp: str = "2026-06-12T14:00:01Z",
) -> dict[str, Any]:
    event = {
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
    if tool_name:
        event["tool"] = {"name": tool_name, "call_id": f"{event_id}-call"}
    return event


def ingest(api: TestClient, events: list[dict[str, Any]], session_id: str = "session-state") -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": session_id, "events": events},
    )
    assert response.status_code == 200, response.text


def tool(api: TestClient, name: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = api.post(f"/v1/tools/{name}", headers=auth_headers(), json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def seed_state_session(api: TestClient) -> None:
    start_session(api)
    ingest(
        api,
        [
            state_event("event-goal", "Ship semantic retrieval parity", timestamp="2026-06-12T14:00:01Z"),
            state_event(
                "event-tool-call",
                "run pytest",
                event_type="TOOL_CALL",
                role="ASSISTANT",
                tool_name="pytest",
                timestamp="2026-06-12T14:00:02Z",
            ),
            state_event(
                "event-tool-output",
                "pytest passed",
                event_type="TOOL_OUTPUT",
                role="TOOL",
                tool_name="pytest",
                timestamp="2026-06-12T14:00:03Z",
            ),
            state_event(
                "event-decision",
                "Decision: keep REST retrieval canonical",
                event_type="DECISION",
                role="ASSISTANT",
                timestamp="2026-06-12T14:00:04Z",
            ),
            state_event(
                "event-next-step",
                "Now add execution state history",
                turn_id="turn-2",
                timestamp="2026-06-12T14:00:05Z",
            ),
        ],
    )


def test_event_ingest_updates_execution_state_and_goal_history(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    seed_state_session(api)

    state = tool(api, "get_execution_state", {"session_id": "session-state"})

    assert state["ok"] is True
    data = state["data"]
    assert data["schema_version"] == "mneme.execution_state.v0"
    assert data["session_id"] == "session-state"
    assert data["goal"] == "Ship semantic retrieval parity"
    assert data["current_step"] == "Now add execution state history"
    assert data["turn_count"] == 2
    assert data["last_tool"] == "pytest"
    assert data["last_tool_output_summary"] == "pytest passed"
    assert data["decision_stack"][-1]["text"] == "Decision: keep REST retrieval canonical"

    history = tool(api, "get_goal_history", {"session_id": "session-state", "limit": 10})
    assert history["ok"] is True
    rows = history["data"]["history"]
    assert len(rows) >= 2
    assert rows[0]["goal"] == "Ship semantic retrieval parity"
    assert rows[-1]["current_step"] == "Now add execution state history"
    assert rows[-1]["schema_version"] == "mneme.state_history_entry.v0"


def test_execution_state_defaults_include_segment_and_enrichment_fields(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)

    state = tool(api, "get_execution_state", {"session_id": "session-state"})["data"]

    assert state["segment_id"] == "segment-session-state"
    assert state["enrichment"] == {
        "decision_summary": None,
        "intent_label": None,
        "topic_tags": [],
    }


def test_decision_events_preserve_rationale_when_present(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)
    decision = state_event(
        "event-decision-rationale",
        "Use REST as canonical boundary",
        event_type="DECISION",
        role="ASSISTANT",
    )
    decision["metadata"] = {"rationale": "MCP proxies REST and avoids split behavior"}

    ingest(api, [decision])

    state = tool(api, "get_execution_state", {"session_id": "session-state"})["data"]
    assert state["decision_stack"][-1]["decision"] == "Use REST as canonical boundary"
    assert state["decision_stack"][-1]["rationale"] == "MCP proxies REST and avoids split behavior"


def test_execution_state_recovers_from_history_when_current_state_is_missing(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    api = TestClient(create_app(Settings(db_path=db_path, auth_token=TOKEN)))
    seed_state_session(api)
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM execution_state WHERE session_id = ?", ("session-state",))

    state = tool(api, "get_execution_state", {"session_id": "session-state"})["data"]

    assert state["goal"] == "Ship semantic retrieval parity"
    assert state["current_step"] == "Now add execution state history"
    assert state["enrichment"]["intent_label"] is None


def test_execution_state_and_history_survive_restart_export_and_delete(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    api = TestClient(create_app(Settings(db_path=db_path, auth_token=TOKEN)))
    seed_state_session(api)

    restarted = TestClient(create_app(Settings(db_path=db_path, auth_token=TOKEN)))
    state = tool(restarted, "get_execution_state", {"session_id": "session-state"})
    history = tool(restarted, "get_goal_history", {"session_id": "session-state", "limit": 5})

    assert state["data"]["goal"] == "Ship semantic retrieval parity"
    assert history["data"]["history"][-1]["current_step"] == "Now add execution state history"

    exported = restarted.get("/v1/sessions/session-state/export", headers=auth_headers())
    assert exported.status_code == 200
    body = exported.json()
    assert body["execution_state"]["goal"] == "Ship semantic retrieval parity"
    assert body["state_history"]

    deleted = restarted.delete("/v1/sessions/session-state", headers=auth_headers())
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert restarted.get("/v1/sessions/session-state/export", headers=auth_headers()).status_code == 404


def test_mcp_execution_state_and_goal_history_proxy_rest(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN))
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(base_url="http://mneme.test", transport=transport, headers=auth_headers()) as http:
            from mneme_service.mcp_server import create_mcp_server

            server = create_mcp_server(base_url="http://mneme.test", token=TOKEN, transport=transport)
            tool_names = {tool.name for tool in await server.list_tools()}
            assert "get_execution_state" in tool_names
            assert "get_goal_history" in tool_names

            start = await http.post(
                "/v1/sessions/start",
                json={
                    "schema_version": "mneme.session.v0",
                    "session_id": "session-state",
                    "agent_id": "agent-1",
                    "runtime": "CODEX_MCP",
                    "started_at": "2026-06-12T14:00:00Z",
                },
            )
            assert start.status_code == 200, start.text
            ingest_response = await http.post(
                "/v1/events",
                json={
                    "schema_version": "mneme.event_batch.v0",
                    "session_id": "session-state",
                    "events": [state_event("event-goal", "Remember the MCP state goal")],
                },
            )
            assert ingest_response.status_code == 200, ingest_response.text

            rest_state = (await http.post("/v1/tools/get_execution_state", json={"session_id": "session-state"})).json()
            mcp_state = await server.call_tool("get_execution_state", {"session_id": "session-state"})
            if isinstance(mcp_state, tuple):
                mcp_state = mcp_state[1]
            assert rest_state["data"]["goal"] == mcp_state["data"]["goal"]

            rest_history = (await http.post("/v1/tools/get_goal_history", json={"session_id": "session-state", "limit": 5})).json()
            mcp_history = await server.call_tool("get_goal_history", {"session_id": "session-state", "limit": 5})
            if isinstance(mcp_history, tuple):
                mcp_history = mcp_history[1]
            assert rest_history["data"]["history"] == mcp_history["data"]["history"]

    asyncio.run(scenario())
