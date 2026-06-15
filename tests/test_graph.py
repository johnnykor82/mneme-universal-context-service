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


def start_session(api: TestClient) -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-graph",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": "project-1",
            "started_at": "2026-06-12T19:00:00Z",
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
    event_type: str,
    text: str,
    *,
    role: str,
    parent_event_ids: list[str] | None = None,
) -> dict:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": "session-graph",
        "turn_id": "turn-1",
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "role": role,
        "type": event_type,
        "timestamp": "2026-06-12T19:00:01Z",
        "content": {"format": "TEXT", "text": text},
        "parent_event_ids": parent_event_ids or [],
    }


def ingest(api: TestClient, events: list[dict]) -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": "session-graph", "events": events},
    )
    assert response.status_code == 200, response.text


def seed_graph(api: TestClient) -> None:
    ingest(
        api,
        [
            event("event-call", "TOOL_CALL", "run pytest", role="ASSISTANT"),
            event("event-output", "TOOL_OUTPUT", "pytest failed in assembler", role="TOOL", parent_event_ids=["event-call"]),
            event("event-decision", "DECISION", "inspect next step", role="ASSISTANT", parent_event_ids=["event-output"]),
        ],
    )


def test_ingest_persists_typed_graph_edges_and_exports_them(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    seed_graph(api)

    exported = api.get("/v1/sessions/session-graph/export", headers=auth_headers())

    assert exported.status_code == 200, exported.text
    edges = exported.json()["event_graph_edges"]
    assert [
        (edge["source_event_id"], edge["target_event_id"], edge["edge_type"])
        for edge in edges
    ] == [
        ("event-call", "event-output", "TOOL_RESULT"),
        ("event-output", "event-decision", "DECISION_FOLLOWS"),
    ]
    assert all(edge["schema_version"] == "mneme.graph_edge.v0" for edge in edges)


def test_expand_context_uses_typed_graph_edges_and_audits_all_exposed_ids(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    seed_graph(api)

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-graph", "seed_event_id": "event-output", "depth": 1, "max_events": 10},
    )

    assert expanded.status_code == 200, expanded.text
    events = expanded.json()["data"]["events"]
    edge_by_id = {item["event_id"]: item["edge"] for item in events}
    assert edge_by_id == {
        "event-output": "SEED",
        "event-call": "TOOL_RESULT",
        "event-decision": "DECISION_FOLLOWS",
    }

    trace = api.get(f"/v1/traces/{expanded.json()['trace_id']}", headers=auth_headers())
    assert trace.status_code == 200
    assert set(trace.json()["selected_event_ids"]) == {"event-call", "event-output", "event-decision"}


def test_context_search_includes_graph_dependencies_for_keyword_hit(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    seed_graph(api)

    search = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-graph", "query": "assembler failed", "scope": "SESSION", "top_k": 3},
    )

    assert search.status_code == 200, search.text
    results = search.json()["data"]["results"]
    assert [item["event_id"] for item in results] == ["event-output", "event-call", "event-decision"]
    assert results[0]["reason"] == "KEYWORD_RECENCY"
    assert results[1]["reason"] == "GRAPH_DEPENDENCY:TOOL_RESULT"
    assert results[2]["reason"] == "GRAPH_DEPENDENCY:DECISION_FOLLOWS"
