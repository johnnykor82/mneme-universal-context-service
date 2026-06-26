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


def test_ingest_persists_parent_child_graph_edges_with_default_weight(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    ingest(
        api,
        [
            event("event-root", "USER_MESSAGE", "root", role="USER"),
            event("event-child", "ASSISTANT_MESSAGE", "child", role="ASSISTANT", parent_event_ids=["event-root"]),
        ],
    )

    exported = api.get("/v1/sessions/session-graph/export", headers=auth_headers())

    assert exported.status_code == 200, exported.text
    edges = exported.json()["event_graph_edges"]
    assert [
        (edge["source_event_id"], edge["target_event_id"], edge["edge_type"], edge["weight"])
        for edge in edges
    ] == [("event-root", "event-child", "PARENT_CHILD", 0.9)]


def test_ingest_persists_tool_input_edge_for_tool_call_parent(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    ingest(
        api,
        [
            event("event-user", "USER_MESSAGE", "run tests", role="USER"),
            event("event-tool-call", "TOOL_CALL", "pytest", role="ASSISTANT", parent_event_ids=["event-user"]),
        ],
    )

    exported = api.get("/v1/sessions/session-graph/export", headers=auth_headers())

    assert exported.status_code == 200, exported.text
    edges = exported.json()["event_graph_edges"]
    assert any(
        edge["source_event_id"] == "event-user"
        and edge["target_event_id"] == "event-tool-call"
        and edge["edge_type"] == "TOOL_INPUT"
        and edge["weight"] == 1.0
        for edge in edges
    )

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-graph", "seed_event_id": "event-tool-call", "mode": "TOOL_CHAIN", "depth": 1, "max_events": 5},
    )
    assert expanded.status_code == 200, expanded.text
    edge_by_id = {item["event_id"]: item["edge"] for item in expanded.json()["data"]["events"]}
    assert edge_by_id["event-user"] == "TOOL_INPUT"


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


def test_expand_context_tool_chain_mode_prioritizes_tool_result_edges(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    seed_graph(api)

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-graph", "seed_event_id": "event-output", "mode": "TOOL_CHAIN", "depth": 1, "max_events": 10},
    )

    assert expanded.status_code == 200, expanded.text
    body = expanded.json()
    assert body["data"]["mode"] == "TOOL_CHAIN"
    assert [item["event_id"] for item in body["data"]["events"]] == [
        "event-output",
        "event-call",
        "event-decision",
    ]
    assert [item["edge"] for item in body["data"]["events"]] == [
        "SEED",
        "TOOL_RESULT",
        "DECISION_FOLLOWS",
    ]


def test_expand_context_causal_mode_orders_equal_weight_neighbors_by_time(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    ingest(
        api,
        [
            {**event("event-root", "USER_MESSAGE", "root", role="USER"), "timestamp": "2026-06-12T19:00:01Z"},
            {**event("event-a", "ASSISTANT_MESSAGE", "older", role="ASSISTANT", parent_event_ids=["event-root"]), "timestamp": "2026-06-12T19:00:02Z"},
            {**event("event-z", "ASSISTANT_MESSAGE", "newer", role="ASSISTANT", parent_event_ids=["event-root"]), "timestamp": "2026-06-12T19:00:03Z"},
        ],
    )

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-graph", "seed_event_id": "event-root", "mode": "CAUSAL", "depth": 1, "max_events": 10},
    )

    assert expanded.status_code == 200, expanded.text
    body = expanded.json()
    assert body["data"]["mode"] == "CAUSAL"
    assert [item["event_id"] for item in body["data"]["events"]] == [
        "event-root",
        "event-z",
        "event-a",
    ]


def test_expand_context_stops_at_traversal_limits_with_warning(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    ingest(
        api,
        [
            event("event-root", "USER_MESSAGE", "root", role="USER"),
            event("event-a", "TOOL_OUTPUT", "a", role="TOOL", parent_event_ids=["event-root"]),
            event("event-b", "TOOL_OUTPUT", "b", role="TOOL", parent_event_ids=["event-root"]),
            event("event-c", "TOOL_OUTPUT", "c", role="TOOL", parent_event_ids=["event-root"]),
        ],
    )

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-graph", "seed_event_id": "event-root", "depth": 5, "max_events": 2},
    )

    assert expanded.status_code == 200, expanded.text
    body = expanded.json()
    assert [item["event_id"] for item in body["data"]["events"]] == ["event-root", "event-a"]
    assert body["data"]["truncated"] is True
    assert body["data"]["truncation_reason"] == "MAX_EVENTS"
    assert body["data"]["dropped_count"] == 2
    assert body["data"]["frontier_summary"] == {"queued": 2, "visited": 2}
    assert body["warnings"][0]["code"] == "GRAPH_TRAVERSAL_LIMIT_REACHED"
    assert body["warnings"][1]["code"] == "RESULT_TRUNCATED"
    assert body["warnings"][1]["details"] == {"dropped_count": 2, "frontier_queued": 2}


def test_expand_context_enforces_branching_factor_limit(tmp_path: Path) -> None:
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                graph_max_branching_factor=2,
            )
        )
    )
    start_session(api)
    ingest(
        api,
        [
            event("event-root", "USER_MESSAGE", "root", role="USER"),
            event("event-a", "TOOL_OUTPUT", "a", role="TOOL", parent_event_ids=["event-root"]),
            event("event-b", "TOOL_OUTPUT", "b", role="TOOL", parent_event_ids=["event-root"]),
            event("event-c", "TOOL_OUTPUT", "c", role="TOOL", parent_event_ids=["event-root"]),
            event("event-d", "TOOL_OUTPUT", "d", role="TOOL", parent_event_ids=["event-root"]),
        ],
    )

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-graph", "seed_event_id": "event-root", "depth": 1, "max_events": 10},
    )

    assert expanded.status_code == 200, expanded.text
    body = expanded.json()
    assert [item["event_id"] for item in body["data"]["events"]] == ["event-root", "event-a", "event-b"]
    assert body["data"]["truncated"] is True
    assert body["data"]["truncation_reason"] == "MAX_BRANCHING_FACTOR"
    assert body["warnings"][0]["code"] == "TRAVERSAL_LIMIT_REACHED"
    assert body["warnings"][0]["details"] == {"limit": "max_branching_factor", "count": 2}


def test_expand_context_temporal_mode_uses_timestamp_order_without_graph_edges(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    events = [
        {**event("event-1", "USER_MESSAGE", "one", role="USER"), "timestamp": "2026-06-12T19:00:01Z"},
        {**event("event-2", "ASSISTANT_MESSAGE", "two", role="ASSISTANT"), "timestamp": "2026-06-12T19:00:02Z"},
        {**event("event-seed", "USER_MESSAGE", "seed", role="USER"), "timestamp": "2026-06-12T19:00:03Z"},
        {**event("event-4", "ASSISTANT_MESSAGE", "four", role="ASSISTANT"), "timestamp": "2026-06-12T19:00:04Z"},
        {**event("event-5", "USER_MESSAGE", "five", role="USER"), "timestamp": "2026-06-12T19:00:05Z"},
    ]
    ingest(api, events)

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-graph", "seed_event_id": "event-seed", "mode": "TEMPORAL", "depth": 5, "max_events": 5},
    )

    assert expanded.status_code == 200, expanded.text
    body = expanded.json()
    assert body["data"]["mode"] == "TEMPORAL"
    assert [item["event_id"] for item in body["data"]["events"]] == [
        "event-seed",
        "event-2",
        "event-1",
        "event-4",
        "event-5",
    ]
    assert body["data"]["truncated"] is False
    assert body["warnings"] == []


def test_expand_context_depth_limit_warns_and_bounds_importance_boost(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    ingest(
        api,
        [
            event("event-root", "USER_MESSAGE", "root", role="USER"),
            event("event-child", "TOOL_OUTPUT", "child", role="TOOL", parent_event_ids=["event-root"]),
            event("event-grandchild", "DECISION", "grandchild", role="ASSISTANT", parent_event_ids=["event-child"]),
        ],
    )

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-graph", "seed_event_id": "event-root", "depth": 1, "max_events": 10},
    )

    assert expanded.status_code == 200, expanded.text
    body = expanded.json()
    events = body["data"]["events"]
    assert [item["event_id"] for item in events] == ["event-root", "event-child"]
    assert "event-grandchild" not in {item["event_id"] for item in events}
    assert body["data"]["truncated"] is True
    assert body["data"]["truncation_reason"] == "DEPTH_LIMIT"
    assert body["warnings"][0]["code"] == "GRAPH_DEPTH_LIMIT_REACHED"
    boost_by_id = {item["event_id"]: item["importance_boost"] for item in events}
    assert boost_by_id["event-root"] == 1.0
    assert boost_by_id["event-child"] <= 0.6


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
