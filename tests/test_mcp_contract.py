from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from mneme_service.app import create_app
from mneme_service.config import Settings

EXPECTED_TOOL_NAMES = (
    "resolve_session",
    "list_sessions",
    "context_search",
    "fetch_event",
    "expand_context",
    "recall_recent",
    "list_segments",
    "get_execution_state",
    "get_goal_history",
    "explain_context",
    "mneme_cost_report",
)
TOKEN = "test-token"


def structured_tool_result(result: Any) -> dict[str, Any]:
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
        return result[1]
    if isinstance(result, dict):
        return result
    raise AssertionError(f"Unexpected MCP tool result: {result!r}")


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def mcp_event(
    event_id: str,
    text: str,
    *,
    event_type: str = "TOOL_OUTPUT",
    role: str = "TOOL",
    parent_event_ids: list[str] | None = None,
    turn_id: str = "turn-1",
    timestamp: str = "2026-06-12T12:00:01Z",
) -> dict[str, Any]:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": "session-1",
        "turn_id": turn_id,
        "agent_id": "agent-1",
        "runtime": "CODEX_MCP",
        "role": role,
        "type": event_type,
        "timestamp": timestamp,
        "content": {"format": "TEXT", "text": text},
        "tool": {"name": "exec_command", "call_id": "tool-call-1"},
        "parent_event_ids": parent_event_ids or [],
    }


async def seed_mcp_parity_session(http: httpx.AsyncClient) -> None:
    session = await http.post(
        "/v1/sessions/start",
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-1",
            "agent_id": "agent-1",
            "runtime": "CODEX_MCP",
            "project_id": "project-1",
            "model": "test-model",
            "tokenizer": "approx",
            "context_window_tokens": 100000,
            "cost_mode": "STANDARD",
            "started_at": "2026-06-12T12:00:00Z",
        },
    )
    assert session.status_code == 200, session.text
    events = [
        mcp_event("event-call", "run pytest", event_type="TOOL_CALL"),
        mcp_event("event-output", "pytest failure in context assembler", parent_event_ids=["event-call"]),
        mcp_event(
            "event-decision",
            "decided to inspect assembler",
            event_type="DECISION",
            role="ASSISTANT",
            parent_event_ids=["event-output"],
            turn_id="turn-2",
            timestamp="2026-06-12T12:00:02Z",
        ),
    ]
    ingested = await http.post(
        "/v1/events",
        json={"schema_version": "mneme.event_batch.v0", "session_id": "session-1", "events": events},
    )
    assert ingested.status_code == 200, ingested.text
    completed = await http.post(
        "/v1/turns/complete",
        json={
            "schema_version": "mneme.turn.v0",
            "session_id": "session-1",
            "turn_id": "turn-2",
            "status": "COMPLETED",
            "started_at": "2026-06-12T12:00:00Z",
            "completed_at": "2026-06-12T12:00:30Z",
            "event_ids": ["event-output", "event-decision"],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "tool_call_count": 1},
        },
    )
    assert completed.status_code == 200, completed.text


async def mcp_call(server: Any, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return structured_tool_result(await server.call_tool(name, arguments))


async def parity_clients(tmp_path: Path) -> tuple[httpx.AsyncClient, Any]:
    app = create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN))
    transport = httpx.ASGITransport(app=app)
    http = httpx.AsyncClient(base_url="http://mneme.test", transport=transport, headers=auth_headers())
    from mneme_service.mcp_server import create_mcp_server

    server = create_mcp_server(base_url="http://mneme.test", token=TOKEN, transport=transport)
    return http, server


def test_mcp_server_module_imports() -> None:
    from mneme_service.mcp_server import TOOL_NAMES, create_mcp_server

    assert "resolve_session" in TOOL_NAMES
    assert "context_search" in TOOL_NAMES
    assert "mneme_cost_report" in TOOL_NAMES
    assert create_mcp_server is not None


def test_tool_names_match_contract() -> None:
    from mneme_service.mcp_server import TOOL_NAMES

    assert TOOL_NAMES == EXPECTED_TOOL_NAMES


def test_mcp_tools_are_discoverable() -> None:
    from mneme_service.mcp_server import create_mcp_server

    server = create_mcp_server(base_url="http://mneme.test", token=None)
    tools = asyncio.run(server.list_tools())

    assert {tool.name for tool in tools} == set(EXPECTED_TOOL_NAMES)


def test_mcp_context_search_tool_proxies_rest_envelope() -> None:
    from mneme_service.mcp_server import create_mcp_server

    seen: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization", "")
        seen["url"] = str(request.url)
        seen["body"] = request.content.decode("utf-8")
        return httpx.Response(
            200,
            json={
                "ok": True,
                "data": {"results": [{"event_id": "event-1"}]},
                "trace_id": "trace-1",
                "warnings": [],
            },
        )

    server = create_mcp_server(
        base_url="http://mneme.test/",
        token="secret-token",
        transport=httpx.MockTransport(handler),
    )

    result = structured_tool_result(
        asyncio.run(
            server.call_tool(
                "context_search",
                {"query": "pytest", "session_id": "session-1", "scope": "SESSION", "top_k": 3},
            )
        )
    )

    assert seen["authorization"] == "Bearer secret-token"
    assert seen["url"] == "http://mneme.test/v1/tools/context_search"
    assert json.loads(seen["body"]) == {
        "query": "pytest",
        "session_id": "session-1",
        "scope": "SESSION",
        "top_k": 3,
        "filters": {},
        "include_content": False,
    }
    assert result["ok"] is True
    assert result["data"]["results"] == [{"event_id": "event-1"}]
    assert result["trace_id"] == "trace-1"


def test_mcp_resolve_session_tool_proxies_rest_envelope() -> None:
    from mneme_service.mcp_server import create_mcp_server

    seen: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.content.decode("utf-8")
        return httpx.Response(
            200,
            json={
                "ok": True,
                "data": {
                    "resolved_session_id": None,
                    "best_guess_session_id": "codex-session-1",
                    "resolution": "AMBIGUOUS",
                    "matches": [],
                },
                "warnings": [{"code": "SESSION_RESOLUTION_AMBIGUOUS", "message": "refine filters"}],
            },
        )

    server = create_mcp_server(base_url="http://mneme.test/", transport=httpx.MockTransport(handler))

    result = structured_tool_result(
        asyncio.run(
            server.call_tool(
                "resolve_session",
                {"project_path": "/repo/rlm-orchestrator", "thread_id": "thread-1", "limit": 3},
            )
        )
    )

    assert seen["url"] == "http://mneme.test/v1/tools/resolve_session"
    assert json.loads(seen["body"]) == {
        "session_id": None,
        "project_path": "/repo/rlm-orchestrator",
        "thread_id": "thread-1",
        "slug": None,
        "query": None,
        "limit": 3,
    }
    assert result["ok"] is True
    assert result["data"]["resolved_session_id"] is None
    assert result["data"]["best_guess_session_id"] == "codex-session-1"
    assert result["warnings"][0]["code"] == "SESSION_RESOLUTION_AMBIGUOUS"


def test_mcp_cost_report_tool_proxies_rest_tool_route() -> None:
    from mneme_service.mcp_server import create_mcp_server

    seen: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["body"] = request.content.decode("utf-8")
        return httpx.Response(
            200,
            json={
                "ok": True,
                "data": {"schema_version": "mneme.cost_report.v0", "session_id": "session-1"},
                "trace_id": None,
                "warnings": [],
            },
        )

    server = create_mcp_server(base_url="http://mneme.test/", transport=httpx.MockTransport(handler))

    result = structured_tool_result(
        asyncio.run(server.call_tool("mneme_cost_report", {"session_id": "session-1", "range": "SESSION"}))
    )

    assert seen["method"] == "POST"
    assert seen["url"] == "http://mneme.test/v1/tools/mneme_cost_report"
    assert json.loads(seen["body"]) == {"session_id": "session-1", "range": "SESSION", "granularity": "SUMMARY"}
    assert result["ok"] is True
    assert result["data"]["schema_version"] == "mneme.cost_report.v0"


def test_mcp_rest_memory_tool_parity(tmp_path: Path) -> None:
    async def scenario() -> None:
        http, server = await parity_clients(tmp_path)
        async with http:
            await seed_mcp_parity_session(http)

            resolve_payload = {"session_id": "session-1"}
            rest_resolve = (await http.post("/v1/tools/resolve_session", json=resolve_payload)).json()
            mcp_resolve = await mcp_call(server, "resolve_session", resolve_payload)
            assert rest_resolve["data"]["resolved_session_id"] == mcp_resolve["data"]["resolved_session_id"]

            list_payload = {"query": "project-1", "limit": 10}
            rest_list = (await http.post("/v1/tools/list_sessions", json=list_payload)).json()
            mcp_list = await mcp_call(server, "list_sessions", list_payload)
            assert [item["session_id"] for item in rest_list["data"]["sessions"]] == [
                item["session_id"] for item in mcp_list["data"]["sessions"]
            ]

            paged_payload = {"query": "project-1", "page_size": 1}
            rest_paged = (await http.post("/v1/tools/list_sessions", json=paged_payload)).json()
            mcp_paged = await mcp_call(server, "list_sessions", paged_payload)
            assert mcp_paged["data"]["next_page_token"] == rest_paged["data"]["next_page_token"]
            assert mcp_paged["data"]["matches_truncated"] == rest_paged["data"]["matches_truncated"]

            search_payload = {"query": "assembler failure", "session_id": "session-1", "scope": "SESSION", "top_k": 5}
            rest_search = (await http.post("/v1/tools/context_search", json=search_payload)).json()
            mcp_search = await mcp_call(server, "context_search", search_payload)
            assert rest_search["session_resolution"] == {
                "session_id": "session-1",
                "source": "EXPLICIT_ARGUMENT",
            }
            assert mcp_search["session_resolution"] == rest_search["session_resolution"]
            assert [item["event_id"] for item in rest_search["data"]["results"]] == [
                item["event_id"] for item in mcp_search["data"]["results"]
            ]

            fetch_payload = {"session_id": "session-1", "event_id": "event-output", "full": True, "include_neighbors": True}
            rest_fetch = (await http.post("/v1/tools/fetch_event", json=fetch_payload)).json()
            mcp_fetch = await mcp_call(server, "fetch_event", fetch_payload)
            assert rest_fetch["data"]["event"]["event_id"] == mcp_fetch["data"]["event"]["event_id"]
            assert {item["event_id"] for item in rest_fetch["data"]["neighbors"]} == {
                item["event_id"] for item in mcp_fetch["data"]["neighbors"]
            }

            expand_payload = {"session_id": "session-1", "seed_event_id": "event-output", "mode": "TOOL_CHAIN", "depth": 2, "max_events": 10}
            rest_expand = (await http.post("/v1/tools/expand_context", json=expand_payload)).json()
            mcp_expand = await mcp_call(server, "expand_context", expand_payload)
            assert [item["event_id"] for item in rest_expand["data"]["events"]] == [
                item["event_id"] for item in mcp_expand["data"]["events"]
            ]

            recent_payload = {"session_id": "session-1", "turns": 3, "max_tokens": 100, "include_tool_outputs": True}
            rest_recent = (await http.post("/v1/tools/recall_recent", json=recent_payload)).json()
            mcp_recent = await mcp_call(server, "recall_recent", recent_payload)
            assert [item["event_id"] for item in rest_recent["data"]["events"]] == [
                item["event_id"] for item in mcp_recent["data"]["events"]
            ]

            segments_payload = {"session_id": "session-1", "status": "ANY", "page_size": 20, "page_token": None}
            rest_segments = (await http.post("/v1/tools/list_segments", json=segments_payload)).json()
            mcp_segments = await mcp_call(server, "list_segments", segments_payload)
            assert rest_segments["data"]["segments"] == mcp_segments["data"]["segments"]
            assert rest_segments["data"]["next_page_token"] == mcp_segments["data"]["next_page_token"]

            explain_payload = {"trace_id": rest_search["trace_id"], "event_id": "event-output", "include_dropped_candidates": False}
            rest_explain = (await http.post("/v1/tools/explain_context", json=explain_payload)).json()
            mcp_explain = await mcp_call(server, "explain_context", explain_payload)
            assert rest_explain["data"] == mcp_explain["data"]

            rest_cost = (await http.post("/v1/tools/mneme_cost_report", json={"session_id": "session-1"})).json()
            mcp_cost = await mcp_call(server, "mneme_cost_report", {"session_id": "session-1"})
            assert mcp_cost["ok"] is True
            assert rest_cost["ok"] is True
            assert rest_cost["session_resolution"] == {
                "session_id": "session-1",
                "source": "EXPLICIT_ARGUMENT",
            }
            assert mcp_cost["session_resolution"] == rest_cost["session_resolution"]
            assert rest_cost["data"]["session_id"] == mcp_cost["data"]["session_id"]
            assert rest_cost["data"]["events_ingested"] == mcp_cost["data"]["events_ingested"]
            assert rest_cost["data"]["prepare_calls"] == mcp_cost["data"]["prepare_calls"]
            assert rest_cost["data"]["embedding_batches"] == mcp_cost["data"]["embedding_batches"]

    asyncio.run(scenario())


def test_resolve_session_reports_resolved_by_tool_source(tmp_path: Path) -> None:
    async def scenario() -> None:
        http, server = await parity_clients(tmp_path)
        async with http:
            await seed_mcp_parity_session(http)

            payload = {"session_id": "session-1"}
            rest_resolve = (await http.post("/v1/tools/resolve_session", json=payload)).json()
            mcp_resolve = await mcp_call(server, "resolve_session", payload)

            assert rest_resolve["session_resolution"] == {
                "session_id": "session-1",
                "source": "RESOLVED_BY_TOOL",
            }
            assert mcp_resolve["session_resolution"] == rest_resolve["session_resolution"]

    asyncio.run(scenario())


def test_mcp_trusted_default_session_fills_omitted_session_id(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN))
        transport = httpx.ASGITransport(app=app)
        http = httpx.AsyncClient(base_url="http://mneme.test", transport=transport, headers=auth_headers())
        from mneme_service.mcp_server import create_mcp_server

        server = create_mcp_server(
            base_url="http://mneme.test",
            token=TOKEN,
            transport=transport,
            default_session_id="session-1",
        )
        async with http:
            await seed_mcp_parity_session(http)

            search = await mcp_call(server, "context_search", {"query": "assembler failure", "scope": "SESSION"})

            assert search["ok"] is True
            assert search["session_resolution"] == {
                "session_id": "session-1",
                "source": "TRUSTED_DEFAULT",
            }
            assert "event-output" in [item["event_id"] for item in search["data"]["results"]]

    asyncio.run(scenario())


def test_mcp_host_injected_default_session_reports_host_injected_source(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN))
        transport = httpx.ASGITransport(app=app)
        http = httpx.AsyncClient(base_url="http://mneme.test", transport=transport, headers=auth_headers())
        from mneme_service.mcp_server import create_mcp_server

        server = create_mcp_server(
            base_url="http://mneme.test",
            token=TOKEN,
            transport=transport,
            default_session_id="session-1",
            default_session_source="HOST_INJECTED",
        )
        async with http:
            await seed_mcp_parity_session(http)

            state = await mcp_call(server, "get_execution_state", {})

            assert state["ok"] is True
            assert state["session_resolution"] == {
                "session_id": "session-1",
                "source": "HOST_INJECTED",
            }

    asyncio.run(scenario())


def test_mcp_omitted_session_without_trusted_default_returns_validation_error() -> None:
    from mneme_service.mcp_server import create_mcp_server

    server = create_mcp_server(base_url="http://mneme.test")

    result = structured_tool_result(
        asyncio.run(server.call_tool("context_search", {"query": "assembler failure", "scope": "SESSION"}))
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "VALIDATION_ERROR"
    assert "session_id" in result["error"]["message"]


def test_mcp_stale_trusted_default_session_returns_specific_error(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN))
        transport = httpx.ASGITransport(app=app)
        from mneme_service.mcp_server import create_mcp_server

        server = create_mcp_server(
            base_url="http://mneme.test",
            token=TOKEN,
            transport=transport,
            default_session_id="missing-session",
        )

        result = await mcp_call(server, "context_search", {"query": "assembler failure", "scope": "SESSION"})

        assert result["ok"] is False
        assert result["error"]["code"] == "DEFAULT_SESSION_STALE"
        assert result["error"]["retryable"] is False
        assert result["error"]["details"] == {"session_id": "missing-session"}
        assert result["warnings"][0]["code"] == "RESOLVE_SESSION_REQUIRED"

    asyncio.run(scenario())


def test_mcp_and_rest_accept_same_codex_uuid_session_id(tmp_path: Path) -> None:
    async def scenario() -> None:
        http, server = await parity_clients(tmp_path)
        rlm_session_id = "019edb86-1d22-78a3-b9e4-e6121c294056"
        async with http:
            session = await http.post(
                "/v1/sessions/start",
                json={
                    "schema_version": "mneme.session.v0",
                    "session_id": rlm_session_id,
                    "agent_id": "agent-1",
                    "runtime": "CODEX_MCP",
                    "project_id": "/repo/rlm-orchestrator",
                    "model": "test-model",
                    "tokenizer": "approx",
                    "context_window_tokens": 100000,
                    "cost_mode": "STANDARD",
                    "started_at": "2026-06-21T12:00:00Z",
                    "metadata": {"cwd": "/repo/rlm-orchestrator"},
                },
            )
            assert session.status_code == 200, session.text
            event_payload = {**mcp_event("rlm-event-1", "RLM Orchestrator MVP 1 benchmark evidence project status")}
            event_payload["session_id"] = rlm_session_id
            ingested = await http.post(
                "/v1/events",
                json={"schema_version": "mneme.event_batch.v0", "session_id": rlm_session_id, "events": [event_payload]},
            )
            assert ingested.status_code == 200, ingested.text

            search_payload = {
                "query": "RLM Orchestrator MVP 1 benchmark evidence project status",
                "session_id": rlm_session_id,
                "scope": "SESSION",
                "top_k": 5,
            }
            rest_search = (await http.post("/v1/tools/context_search", json=search_payload)).json()
            mcp_search = await mcp_call(server, "context_search", search_payload)

            assert rest_search["ok"] is True
            assert mcp_search["ok"] is True
            assert [item["event_id"] for item in rest_search["data"]["results"]] == [
                item["event_id"] for item in mcp_search["data"]["results"]
            ] == ["rlm-event-1"]

    asyncio.run(scenario())


def test_mcp_memory_tools_write_audit_records_and_traces(tmp_path: Path) -> None:
    async def scenario() -> None:
        http, server = await parity_clients(tmp_path)
        async with http:
            await seed_mcp_parity_session(http)

            search = await mcp_call(
                server,
                "context_search",
                {"query": "assembler failure", "session_id": "session-1", "scope": "SESSION", "top_k": 5},
            )
            fetch = await mcp_call(
                server,
                "fetch_event",
                {"session_id": "session-1", "event_id": "event-output", "full": True, "include_neighbors": True},
            )
            expand = await mcp_call(
                server,
                "expand_context",
                {"session_id": "session-1", "seed_event_id": "event-output", "mode": "TOOL_CHAIN", "depth": 2, "max_events": 10},
            )

            exported = (await http.get("/v1/sessions/session-1/export?include_audit=true")).json()
            audited_tools = {record["tool"] for record in exported["audit_records"]}
            assert {"context_search", "fetch_event", "expand_context"} <= audited_tools
            assert len([event for event in exported["events"] if event["type"] == "MEMORY_READ"]) >= 3

            expected_trace_events = {
                search["trace_id"]: [item["event_id"] for item in search["data"]["results"]],
                fetch["trace_id"]: ["event-output", *[item["event_id"] for item in fetch["data"]["neighbors"]]],
                expand["trace_id"]: [item["event_id"] for item in expand["data"]["events"]],
            }
            for trace_id, event_ids in expected_trace_events.items():
                trace = (await http.get(f"/v1/traces/{trace_id}")).json()
                assert trace["trace_type"] == "MEMORY_READ"
                assert trace["selected_event_ids"] == event_ids
                assert trace["audit_entries"] == [
                    {"action": "MEMORY_READ", "tool": trace["tool"], "event_ids": event_ids}
                ]

    asyncio.run(scenario())


def test_mcp_results_do_not_leak_redacted_secret(tmp_path: Path) -> None:
    async def scenario() -> None:
        http, server = await parity_clients(tmp_path)
        async with http:
            await seed_mcp_parity_session(http)
            ingested = await http.post(
                "/v1/events",
                json={
                    "schema_version": "mneme.event_batch.v0",
                    "session_id": "session-1",
                    "events": [
                        mcp_event(
                            "event-secret",
                            "tool output included sk-mcp-secret",
                            timestamp="2026-06-12T12:00:03Z",
                        )
                    ],
                },
            )
            assert ingested.status_code == 200, ingested.text

            search = await mcp_call(
                server,
                "context_search",
                {"query": "sk-mcp-secret", "session_id": "session-1", "scope": "SESSION", "top_k": 5},
            )
            fetch = await mcp_call(
                server,
                "fetch_event",
                {"session_id": "session-1", "event_id": "event-secret", "full": True, "include_neighbors": False},
            )
            missing = await mcp_call(
                server,
                "fetch_event",
                {"session_id": "session-1", "event_id": "missing-sk-mcp-secret", "full": True, "include_neighbors": False},
            )

            success_text = json.dumps({"search": search, "fetch": fetch}, sort_keys=True)
            error_text = json.dumps(missing, sort_keys=True)
            assert "sk-mcp-secret" not in success_text
            assert "[REDACTED]" in success_text
            assert "sk-mcp-secret" not in error_text
            assert "[REDACTED]" in error_text

    asyncio.run(scenario())


def test_mcp_cli_accepts_base_url_token_and_timeout() -> None:
    from mneme_service.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(
        [
            "mcp",
            "--base-url",
            "http://127.0.0.1:8765",
            "--token",
            "test-token",
            "--timeout",
            "2.5",
        ]
    )

    assert args.command == "mcp"
    assert args.base_url == "http://127.0.0.1:8765"
    assert args.token == "test-token"
    assert args.timeout == 2.5


def test_mcp_cli_uses_environment_defaults(monkeypatch: Any) -> None:
    from mneme_service.cli import build_parser

    monkeypatch.setenv("MNEME_BASE_URL", "http://mneme-env.test")
    monkeypatch.setenv("MNEME_AUTH_TOKEN", "env-token")
    monkeypatch.setenv("MNEME_MCP_DEFAULT_SESSION_ID", "session-env")

    args = build_parser().parse_args(["mcp"])

    assert args.base_url == "http://mneme-env.test"
    assert args.token == "env-token"
    assert args.timeout == 10.0
    assert args.default_session_id == "session-env"


def test_mcp_cli_runs_stdio_server_without_starting_daemon(monkeypatch: Any) -> None:
    from mneme_service import cli

    calls: dict[str, Any] = {}

    class FakeServer:
        def run(self, transport: str = "stdio") -> None:
            calls["transport"] = transport

    def fake_create_mcp_server(
        *,
        base_url: str,
        token: str | None,
        timeout: float,
        default_session_id: str | None,
    ) -> FakeServer:
        calls["base_url"] = base_url
        calls["token"] = token
        calls["timeout"] = timeout
        calls["default_session_id"] = default_session_id
        return FakeServer()

    def fail_uvicorn_run(*_: Any, **__: Any) -> None:
        raise AssertionError("mneme mcp must not start the REST daemon")

    monkeypatch.setattr(cli, "create_mcp_server", fake_create_mcp_server)
    monkeypatch.setattr(cli.uvicorn, "run", fail_uvicorn_run)

    cli.main(
        [
            "mcp",
            "--base-url",
            "http://mneme.test",
            "--token",
            "test-token",
            "--timeout",
            "3",
            "--default-session-id",
            "session-cli",
        ]
    )

    assert calls == {
        "base_url": "http://mneme.test",
        "token": "test-token",
        "timeout": 3.0,
        "default_session_id": "session-cli",
        "transport": "stdio",
    }


def test_rest_client_posts_tool_with_normalized_base_url_and_bearer_token() -> None:
    from mneme_service.rest_client import MnemeRestClient

    seen: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization", "")
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["body"] = request.content.decode("utf-8")
        return httpx.Response(200, json={"ok": True, "data": {"results": []}, "warnings": []})

    client = MnemeRestClient(
        base_url="http://mneme.test/",
        token="secret-token",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(client.post_tool("context_search", {"session_id": "s1", "query": "pytest"}))

    assert seen["authorization"] == "Bearer secret-token"
    assert seen["method"] == "POST"
    assert seen["url"] == "http://mneme.test/v1/tools/context_search"
    assert json.loads(seen["body"]) == {"session_id": "s1", "query": "pytest"}
    assert result == {"ok": True, "data": {"results": []}, "warnings": []}


def test_rest_client_normalizes_rest_error_to_tool_envelope() -> None:
    from mneme_service.rest_client import MnemeRestClient

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Event not found.",
                    "retryable": False,
                    "details": {"event_id": "missing"},
                }
            },
        )

    client = MnemeRestClient(base_url="http://mneme.test", transport=httpx.MockTransport(handler))

    result = asyncio.run(client.post_tool("fetch_event", {"session_id": "s1", "event_id": "missing"}))

    assert result["ok"] is False
    assert result["error"]["code"] == "NOT_FOUND"
    assert result["error"]["message"] == "Event not found."
    assert result["error"]["retryable"] is False
    assert result["error"]["details"] == {"event_id": "missing"}
    assert result["warnings"] == []


def test_rest_client_error_mapping_covers_v0_fallback_status_codes() -> None:
    from mneme_service.rest_client import MnemeRestClient

    async def mapped(status_code: int) -> dict[str, Any]:
        async def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code, text=f"fallback {status_code}")

        client = MnemeRestClient(base_url="http://mneme.test", transport=httpx.MockTransport(handler))
        return await client.post_tool("fetch_event", {"session_id": "s1", "event_id": "missing"})

    unsupported = asyncio.run(mapped(415))
    ranged = asyncio.run(mapped(416))
    limited = asyncio.run(mapped(429))

    assert unsupported["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert unsupported["error"]["retryable"] is False
    assert ranged["error"]["code"] == "RANGE_NOT_SATISFIABLE"
    assert ranged["error"]["retryable"] is False
    assert limited["error"]["code"] == "RATE_LIMITED"
    assert limited["error"]["retryable"] is True


def test_rest_client_preserves_storage_busy_contract_error() -> None:
    from mneme_service.rest_client import MnemeRestClient

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            json={
                "error": {
                    "code": "STORAGE_BUSY",
                    "message": "Writer queue is full.",
                    "details": {"queue_depth": 8},
                }
            },
        )

    client = MnemeRestClient(base_url="http://mneme.test", transport=httpx.MockTransport(handler))
    result = asyncio.run(client.post_tool("context_search", {"session_id": "s1", "query": "pytest"}))

    assert result["ok"] is False
    assert result["error"]["code"] == "STORAGE_BUSY"
    assert result["error"]["retryable"] is True
    assert result["error"]["details"] == {"queue_depth": 8}


def test_rest_tool_rejects_unsupported_schema_version(tmp_path: Path) -> None:
    async def scenario() -> None:
        http, _server = await parity_clients(tmp_path)
        async with http:
            await seed_mcp_parity_session(http)

            for path, payload in (
                (
                    "/v1/tools/context_search",
                    {
                        "schema_version": "mneme.tool_request.v99",
                        "session_id": "session-1",
                        "query": "assembler failure",
                    },
                ),
                (
                    "/v1/tools/mneme_cost_report",
                    {
                        "schema_version": "mneme.tool_request.v99",
                        "session_id": "session-1",
                    },
                ),
            ):
                rejected = await http.post(path, json=payload)

                assert rejected.status_code == 422
                body = rejected.json()
                assert body["error"]["code"] == "VALIDATION_ERROR"
                assert body["error"]["details"]["field"] == "schema_version"
                assert body["error"]["details"]["supported_schema_versions"] == ["mneme.tool_request.v0"]

    asyncio.run(scenario())


def test_rest_client_normalizes_transport_error_to_tool_envelope() -> None:
    from mneme_service.rest_client import MnemeRestClient

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("daemon unavailable", request=request)

    client = MnemeRestClient(base_url="http://mneme.test/", transport=httpx.MockTransport(handler))

    result = asyncio.run(client.post_tool("context_search", {"session_id": "s1", "query": "pytest"}))

    assert result["ok"] is False
    assert result["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert result["error"]["retryable"] is True
    assert result["error"]["details"] == {"base_url": "http://mneme.test"}
    assert result["warnings"] == []
