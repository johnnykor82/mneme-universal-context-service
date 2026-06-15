# Milestone 2 MCP Server and Adapter Substrate Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first agent-facing MCP surface for Mneme by exposing the accepted v0 memory tools through a local MCP server that proxies the Milestone 1 REST daemon.

**Architecture:** REST remains the canonical lifecycle/control-plane API and the source of schema truth. The MCP server is a thin local process that validates tool input, calls the daemon's REST memory endpoints, and returns the shared `ok/data/error/warnings` envelope without reading SQLite directly. Codex/MCP is the first tools-only adapter substrate; deeper Hermes, LangGraph, and OpenAI Agents SDK adapters must follow `MNEME_HOST_ADAPTER_CONTRACT_V0.md` in later milestones.

**Tech Stack:** Python 3.12, FastAPI daemon from Milestone 1, official Model Context Protocol Python SDK, `httpx`, `pytest`, SQLite through the daemon only.

---

## Scope

### In Scope

- Add a local MCP server process launched by `mneme mcp`.
- Implement stdio transport first for local agent clients.
- Expose these MCP tools:
  - `context_search`
  - `fetch_event`
  - `expand_context`
  - `recall_recent`
  - `list_segments`
  - `explain_context`
  - `mneme_cost_report`
- Proxy tool calls to existing REST endpoints:
  - `/v1/tools/context_search`
  - `/v1/tools/fetch_event`
  - `/v1/tools/expand_context`
  - `/v1/tools/recall_recent`
  - `/v1/tools/list_segments`
  - `/v1/tools/explain_context`
  - `/v1/costs/session/{session_id}`
- Preserve the shared MCP result envelope from `API_MCP_CONTRACT_V0.md`.
- Add MCP/REST parity tests over synthetic fixture data.
- Add a Codex/MCP usage guide and config example under this project folder.
- Update `GET /v1/capabilities` to report MCP availability only when the implementation is present and documented.

### Out of Scope

- No event ingestion through MCP tools.
- No automatic prompt replacement for Codex.
- No live modification of `/Users/openclaw/.hermes/hermes-agent`.
- No live modification of `/Users/openclaw/.hermes/plugins/hermes-mneme`.
- No Hermes adapter implementation.
- No LangGraph adapter implementation.
- No OpenAI Agents SDK adapter implementation.
- No universal host adapter SDK implementation.
- No embeddings, reranking, LLM enrichment, or benchmarks.
- No remote hosted MCP transport unless it is trivial after stdio passes all tests.

## Design Decisions

1. **MCP proxies REST instead of sharing storage.**
   - Reason: REST is already the canonical contract surface, and direct SQLite access would create a second behavior path.
   - Consequence: MCP requires a running local daemon or a test ASGI/HTTP harness.

2. **Tool-level errors return structured `ok=false` payloads.**
   - Reason: The contract says recoverable tool failures should be model-readable.
   - Consequence: validation, not found, conflict, and daemon-unavailable errors are normalized into the shared envelope. True protocol failures may still surface as MCP transport errors.

3. **Stdio is the required transport for Milestone 2.**
   - Reason: It is the simplest local integration path for Codex-style MCP clients.
   - Consequence: streamable HTTP/SSE MCP transports can be added later without changing tool schemas.

4. **MCP tools do not mutate canonical transcript except through existing REST memory-read behavior.**
   - Reason: Direct memory tools should create audit records and `MEMORY_READ` events via REST; generated MCP responses should not be stored as user/assistant transcript events.

5. **REST tool hardening is part of this milestone.**
   - Reason: MCP/REST parity is only useful if the shared REST substrate satisfies the visible v0 tool contract.
   - Consequence: Before exposing MCP, tighten REST memory tools for memory-read traces, basic filter handling, recall limits, and predictable pagination/truncation behavior.

6. **Do not extract SQLite-backed tool logic for Milestone 2.**
   - Reason: A shared service layer may become useful later, but the safest v0 MCP substrate is an HTTP client that exercises the same daemon boundary as external adapters.
   - Consequence: `mcp_server.py` must not import `Store` or read SQLite directly. If route closures become too awkward later, extract behavior behind REST tests first.

7. **MCP milestone is a tools-only substrate, not deep context-engine integration.**
   - Reason: Deep context-engine behavior requires host lifecycle hooks defined in `MNEME_HOST_ADAPTER_CONTRACT_V0.md`.
   - Consequence: Codex/MCP docs must avoid automatic prompt replacement claims and should point future runtime authors to the host adapter contract.

## External Sources Checked

- Official MCP SDK overview: `https://modelcontextprotocol.io/docs/sdk`
- Official Python SDK docs: `https://py.sdk.modelcontextprotocol.io/`
- Official Python SDK server docs: `https://py.sdk.modelcontextprotocol.io/server/`
- Official Python SDK testing docs: `https://py.sdk.modelcontextprotocol.io/testing/`
- OpenAI Agents SDK MCP docs for later compatibility planning: `https://openai.github.io/openai-agents-python/mcp/`

## File Map

### Create

- `mneme_service/rest_client.py`
  - Async HTTP client wrapper used by MCP tools.
  - Owns auth headers, base URL normalization, timeout handling, and error-envelope conversion.

- `mneme_service/mcp_server.py`
  - Creates the MCP server, registers tools, and maps each tool to the REST client.
  - Contains no SQLite or retrieval logic.

- `mneme_service/tool_names.py`
  - Dependency-free list of v0 memory tool names shared by REST capabilities and MCP registration.

- `tests/test_mcp_contract.py`
  - Tests MCP tool discovery, tool output envelopes, MCP/REST parity, error envelopes, audit side effects, and cost report.

- `adapters/codex/MNEME_CODEX_MCP_USAGE.md`
  - Codex-facing usage guidance that does not claim automatic prompt control.

- `adapters/codex/mcp_server.example.json`
  - Example local MCP server config using `mneme mcp --base-url ...`.

### Modify

- `pyproject.toml`
  - Add official MCP Python SDK dependency.
  - Add any test-only dependency required by the SDK test harness if not already installed.

- `mneme_service/config.py`
  - Add MCP client settings: `base_url`, `request_timeout_seconds`, and optional daemon token source.

- `mneme_service/cli.py`
  - Add `mneme mcp` subcommand.
  - Keep `mneme serve` unchanged.

- `mneme_service/app.py`
  - Change capabilities to advertise `supports_mcp_tools=true` only after the MCP server is implemented.
  - Add durable memory-read traces for direct REST memory tools and return their `trace_id`.
  - Tighten visible v0 tool behavior before MCP parity tests are added.
  - Do not add MCP logic to the REST app.

- `task_plan.md`
  - Mark Milestone 2 planning complete when this plan is accepted.
  - Add Milestone 2 implementation phase.

- `progress.md`
  - Log the plan, decisions, verification commands, and explicit non-goals.

## Implementation Tasks

### Task 1: Add MCP SDK Dependency and Baseline Import Test

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/test_mcp_contract.py`

- [x] **Step 1: Add a failing import/discovery test**

```python
def test_mcp_server_module_imports() -> None:
    from mneme_service.mcp_server import TOOL_NAMES, create_mcp_server

    assert "context_search" in TOOL_NAMES
    assert "mneme_cost_report" in TOOL_NAMES
    assert create_mcp_server is not None
```

- [x] **Step 2: Run the focused test and confirm it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_server_module_imports -q
```

Expected:

```text
ModuleNotFoundError: No module named 'mneme_service.mcp_server'
```

- [x] **Step 3: Add dependencies**

In `pyproject.toml`, add the official MCP SDK dependency:

```toml
dependencies = [
  "fastapi>=0.115",
  "uvicorn>=0.30",
  "pydantic>=2.8",
  "mcp>=1.0",
]
```

If the SDK test harness requires an extra pytest plugin in the installed version, add it under `[project.optional-dependencies].test` only after a failing test proves it is needed.

- [x] **Step 4: Install dependencies locally**

Run:

```bash
.venv/bin/python -m pip install -e '.[test]'
```

Expected:

```text
Successfully installed ... mcp ...
```

### Task 2: Harden REST Memory Tool Substrate

**Files:**
- Modify: `mneme_service/app.py`
- Modify: `mneme_service/storage.py` if query filters require storage support
- Create: `mneme_service/tool_names.py`
- Modify: `tests/test_contract.py`

- [x] **Step 1: Add tests for memory-read trace ids**

Extend the existing memory tool test:

```python
search = api.post(
    "/v1/tools/context_search",
    headers=auth_headers(),
    json={"query": "assembler failure", "session_id": "session-1", "scope": "SESSION", "top_k": 5},
)
assert search.status_code == 200
trace_id = search.json()["trace_id"]
assert trace_id

trace = api.get(f"/v1/traces/{trace_id}", headers=auth_headers())
assert trace.status_code == 200
assert trace.json()["trace_type"] == "MEMORY_READ"
assert trace.json()["tool"] == "context_search"
assert trace.json()["selected_event_ids"] == ["event-output"]
```

- [x] **Step 2: Add tests for visible tool parameters**

Add focused assertions:

```python
filtered = api.post(
    "/v1/tools/context_search",
    headers=auth_headers(),
    json={
        "query": "pytest",
        "session_id": "session-1",
        "scope": "SESSION",
        "top_k": 10,
        "filters": {"event_types": ["ERROR"]},
    },
)
assert filtered.status_code == 200
assert all(item["type"] == "ERROR" for item in filtered.json()["data"]["results"])

recent = api.post(
    "/v1/tools/recall_recent",
    headers=auth_headers(),
    json={"session_id": "session-1", "turns": 3, "max_tokens": 12, "include_tool_outputs": False},
)
assert recent.status_code == 200
assert all(item["type"] != "TOOL_OUTPUT" for item in recent.json()["data"]["events"])

segments = api.post(
    "/v1/tools/list_segments",
    headers=auth_headers(),
    json={"session_id": "session-1", "status": "ANY", "page_size": 1, "page_token": None},
)
assert segments.status_code == 200
assert len(segments.json()["data"]["segments"]) <= 1
```

- [x] **Step 3: Implement memory-read trace helper**

Replace direct `trace_id=None` memory tool responses with a helper that:

- creates a `mneme.trace.v0` record with `trace_type="MEMORY_READ"`;
- stores `tool`, `session_id`, selected event ids, warnings, and latency;
- writes the existing audit record and `MEMORY_READ` event;
- returns the trace id to `tool_response`.

Suggested shape:

```python
def audit_memory_tool(store: Store, session_id: str, tool: str, event_ids: list[str]) -> str:
    trace_id = new_id("trace")
    trace = {
        "schema_version": "mneme.trace.v0",
        "trace_id": trace_id,
        "trace_type": "MEMORY_READ",
        "session_id": session_id,
        "tool": tool,
        "selected_event_ids": event_ids,
        "audit_entries": [{"action": "MEMORY_READ", "tool": tool, "event_ids": event_ids}],
        "warnings": [],
    }
    store.put_trace(trace)
    store.add_audit(session_id, "MEMORY_READ", tool, event_ids, trace_id=trace_id)
    # keep existing MEMORY_READ event behavior
    return trace_id
```

- [x] **Step 4: Tighten REST parameter behavior minimally**

Implement only deterministic local behavior required for v0:

- `context_search.filters.event_types`: filter results after lexical search.
- `context_search.filters.after` / `before`: compare ISO timestamp strings lexicographically for v0 synthetic fixtures.
- `recall_recent.include_tool_outputs=false`: remove `TOOL_OUTPUT` events from the result.
- `recall_recent.max_tokens`: stop adding snippets once approximate token budget is reached.
- `list_segments.page_size`: cap returned segments and keep `next_page_token=null` until multiple real segments exist.
- `expand_context.max_events`: keep existing truncation warning behavior.

- [x] **Step 5: Add dependency-free tool names module**

Create:

```python
TOOL_NAMES = (
    "context_search",
    "fetch_event",
    "expand_context",
    "recall_recent",
    "list_segments",
    "explain_context",
    "mneme_cost_report",
)
```

- [x] **Step 6: Run focused REST tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_contract.py -q
```

Expected:

```text
all REST contract tests pass
```

### Task 3: Add REST Client Wrapper

**Files:**
- Create: `mneme_service/rest_client.py`
- Test: `tests/test_mcp_contract.py`

- [x] **Step 1: Write tests for success, standard error conversion, and transport error conversion**

Add tests that use `respx` only if already available; otherwise use `httpx.MockTransport` to avoid new dependencies:

```python
import httpx
import pytest

from mneme_service.rest_client import MnemeRestClient


@pytest.mark.anyio
async def test_rest_client_posts_tool_with_bearer_token() -> None:
    seen = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json={"ok": True, "data": {"results": []}, "warnings": []})

    client = MnemeRestClient(
        base_url="http://mneme.test",
        token="secret-token",
        transport=httpx.MockTransport(handler),
    )

    result = await client.post_tool("context_search", {"session_id": "s1", "query": "pytest"})

    assert seen["authorization"] == "Bearer secret-token"
    assert result == {"ok": True, "data": {"results": []}, "warnings": []}


@pytest.mark.anyio
async def test_rest_client_normalizes_rest_error_to_tool_envelope() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"error": {"code": "NOT_FOUND", "message": "Event not found.", "retryable": False}},
        )

    client = MnemeRestClient(base_url="http://mneme.test", transport=httpx.MockTransport(handler))

    result = await client.post_tool("fetch_event", {"session_id": "s1", "event_id": "missing"})

    assert result["ok"] is False
    assert result["error"]["code"] == "NOT_FOUND"
```

- [x] **Step 2: Implement `MnemeRestClient`**

Create:

```python
from __future__ import annotations

from typing import Any

import httpx


class MnemeRestClient:
    def __init__(
        self,
        *,
        base_url: str,
        token: str | None = None,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    async def post_tool(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", f"/v1/tools/{name}", json=payload)

    async def cost_report(self, session_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/v1/costs/session/{session_id}")

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._headers(),
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = await client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            return {
                "ok": False,
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": str(exc),
                    "retryable": True,
                    "details": {"base_url": self.base_url},
                },
            }

        if response.status_code >= 400:
            body = response.json()
            return {"ok": False, "error": body.get("error", body)}
        return response.json()
```

- [x] **Step 3: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_mcp_contract.py::test_rest_client_posts_tool_with_normalized_base_url_and_bearer_token tests/test_mcp_contract.py::test_rest_client_normalizes_rest_error_to_tool_envelope tests/test_mcp_contract.py::test_rest_client_normalizes_transport_error_to_tool_envelope -q
```

Expected:

```text
3 passed
```

### Task 4: Register MCP Tools

**Files:**
- Create: `mneme_service/mcp_server.py`
- Modify: `tests/test_mcp_contract.py`

- [x] **Step 1: Add tool registration tests**

Use the MCP SDK's in-process testing helpers where available. If the installed SDK names differ, inspect official testing docs and keep the assertion intent unchanged.

```python
import pytest

from mneme_service.mcp_server import TOOL_NAMES, create_mcp_server


def test_tool_names_match_contract() -> None:
    assert TOOL_NAMES == (
        "context_search",
        "fetch_event",
        "expand_context",
        "recall_recent",
        "list_segments",
        "explain_context",
        "mneme_cost_report",
    )


@pytest.mark.anyio
async def test_mcp_tools_are_discoverable() -> None:
    from mcp.server.fastmcp import Client

    server = create_mcp_server(base_url="http://mneme.test", token=None)

    async with Client(server) as client:
        tools = await client.list_tools()

    assert {tool.name for tool in tools} == set(TOOL_NAMES)
```

- [x] **Step 2: Implement `create_mcp_server`**

Register each tool with the official Python SDK. Keep tool signatures explicit and close to `API_MCP_CONTRACT_V0.md`.

```python
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .rest_client import MnemeRestClient
from .tool_names import TOOL_NAMES


def create_mcp_server(*, base_url: str, token: str | None = None, timeout: float = 10.0) -> FastMCP:
    mcp = FastMCP("mneme-context-service")
    rest = MnemeRestClient(base_url=base_url, token=token, timeout=timeout)

    @mcp.tool()
    async def context_search(
        query: str,
        session_id: str,
        scope: str = "SESSION",
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        include_content: bool = False,
    ) -> dict[str, Any]:
        return await rest.post_tool(
            "context_search",
            {
                "query": query,
                "session_id": session_id,
                "scope": scope,
                "top_k": top_k,
                "filters": filters or {},
                "include_content": include_content,
            },
        )

    @mcp.tool()
    async def fetch_event(
        event_id: str,
        session_id: str,
        full: bool = True,
        include_neighbors: bool = False,
    ) -> dict[str, Any]:
        return await rest.post_tool(
            "fetch_event",
            {
                "event_id": event_id,
                "session_id": session_id,
                "full": full,
                "include_neighbors": include_neighbors,
            },
        )

    @mcp.tool()
    async def expand_context(
        seed_event_id: str,
        session_id: str,
        mode: str = "TOOL_CHAIN",
        depth: int = 2,
        max_events: int = 12,
        include_content: bool = True,
    ) -> dict[str, Any]:
        return await rest.post_tool(
            "expand_context",
            {
                "seed_event_id": seed_event_id,
                "session_id": session_id,
                "mode": mode,
                "depth": depth,
                "max_events": max_events,
                "include_content": include_content,
            },
        )

    @mcp.tool()
    async def recall_recent(
        session_id: str,
        turns: int = 3,
        max_tokens: int = 12000,
        include_tool_outputs: bool = True,
    ) -> dict[str, Any]:
        return await rest.post_tool(
            "recall_recent",
            {
                "session_id": session_id,
                "turns": turns,
                "max_tokens": max_tokens,
                "include_tool_outputs": include_tool_outputs,
            },
        )

    @mcp.tool()
    async def list_segments(
        session_id: str,
        status: str = "ANY",
        page_size: int = 20,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        return await rest.post_tool(
            "list_segments",
            {
                "session_id": session_id,
                "status": status,
                "page_size": page_size,
                "page_token": page_token,
            },
        )

    @mcp.tool()
    async def explain_context(
        trace_id: str,
        event_id: str | None = None,
        include_dropped_candidates: bool = False,
    ) -> dict[str, Any]:
        return await rest.post_tool(
            "explain_context",
            {
                "trace_id": trace_id,
                "event_id": event_id,
                "include_dropped_candidates": include_dropped_candidates,
            },
        )

    @mcp.tool()
    async def mneme_cost_report(
        session_id: str,
        range: str = "SESSION",
        granularity: str = "SUMMARY",
    ) -> dict[str, Any]:
        report = await rest.cost_report(session_id)
        if "ok" in report:
            return report
        return {"ok": True, "data": report, "warnings": []}

    return mcp
```

- [x] **Step 3: Run MCP discovery tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_mcp_contract.py::test_tool_names_match_contract tests/test_mcp_contract.py::test_mcp_tools_are_discoverable tests/test_mcp_contract.py::test_mcp_context_search_tool_proxies_rest_envelope -q
```

Expected:

```text
3 passed
```

### Task 5: Add MCP/REST Parity Tests

**Files:**
- Modify: `tests/test_mcp_contract.py`
- Modify only if needed: `tests/test_contract.py` helper extraction

- [x] **Step 1: Extract or duplicate minimal fixture helpers**

Use the existing session/event fixture shape from `tests/test_contract.py`. Keep duplication acceptable if extracting helpers would churn the Milestone 1 tests.

- [x] **Step 2: Write parity tests**

Required assertions:

```python
@pytest.mark.anyio
async def test_mcp_rest_context_search_parity(tmp_path: Path) -> None:
    # Arrange: start test daemon app with one session and a matching event.
    # Act: call REST /v1/tools/context_search and MCP context_search.
    # Assert: event ids and envelope shape match.
    assert rest_result["ok"] is True
    assert mcp_result["ok"] is True
    assert [r["event_id"] for r in rest_result["data"]["results"]] == [
        r["event_id"] for r in mcp_result["data"]["results"]
    ]
```

Add equivalent focused tests for:

- `fetch_event`
- `expand_context`
- `recall_recent`
- `list_segments`
- `explain_context`
- `mneme_cost_report`

- [x] **Step 3: Run parity tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_mcp_contract.py -q
```

Expected:

```text
all MCP contract tests pass
```

### Task 6: Verify Audit and Privacy Side Effects Through MCP

**Files:**
- Modify: `tests/test_mcp_contract.py`

- [x] **Step 1: Add MCP audit regression test**

```python
@pytest.mark.anyio
async def test_mcp_memory_tools_write_audit_records(tmp_path: Path) -> None:
    # Arrange: create daemon app, session, and event.
    # Act: call MCP context_search, fetch_event, and expand_context.
    # Assert: REST export contains audit_records and MEMORY_READ events.
    assert len(exported["audit_records"]) >= 3
    assert any(event["type"] == "MEMORY_READ" for event in exported["events"])
```

- [x] **Step 2: Add MCP redaction regression test**

```python
@pytest.mark.anyio
async def test_mcp_results_do_not_leak_redacted_secret(tmp_path: Path) -> None:
    # Arrange: ingest an event containing sk-mcp-secret.
    # Act: call MCP context_search and fetch_event.
    # Assert: secret is absent and [REDACTED] is present.
    assert "sk-mcp-secret" not in str(search_result)
    assert "sk-mcp-secret" not in str(fetch_result)
    assert "[REDACTED]" in str(search_result)
    assert "[REDACTED]" in str(fetch_result)
```

- [x] **Step 3: Run focused privacy tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_mcp_contract.py -q
```

Expected:

```text
all MCP contract tests pass
```

### Task 7: Add CLI `mneme mcp`

**Files:**
- Modify: `mneme_service/config.py`
- Modify: `mneme_service/cli.py`
- Modify: `tests/test_mcp_contract.py`

- [x] **Step 1: Add CLI argument parsing tests**

Prefer testing parser construction directly. If the parser is currently inside `main()`, first extract `build_parser()`.

```python
from mneme_service.cli import build_parser


def test_mcp_cli_accepts_base_url_and_token() -> None:
    parser = build_parser()
    args = parser.parse_args([
        "mcp",
        "--base-url",
        "http://127.0.0.1:8765",
        "--token",
        "test-token",
    ])

    assert args.command == "mcp"
    assert args.base_url == "http://127.0.0.1:8765"
    assert args.token == "test-token"
```

- [x] **Step 2: Implement CLI subcommand**

Add:

```python
mcp_command = subcommands.add_parser("mcp")
mcp_command.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"))
mcp_command.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
mcp_command.add_argument("--timeout", type=float, default=10.0)
```

Run:

```python
server = create_mcp_server(base_url=args.base_url, token=args.token, timeout=args.timeout)
server.run()
```

Use the SDK's documented stdio run method for the installed version. Do not start the REST daemon from `mneme mcp`; it must be an explicit separate process.

- [x] **Step 3: Run CLI tests and smoke command**

Run:

```bash
.venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_cli_accepts_base_url_and_token -q
.venv/bin/python -m mneme_service.cli mcp --help
```

Expected:

```text
test passes
usage: mneme mcp ...
```

### Task 8: Update Capabilities and Documentation

**Files:**
- Modify: `mneme_service/app.py`
- Create: `adapters/codex/MNEME_CODEX_MCP_USAGE.md`
- Create: `adapters/codex/mcp_server.example.json`
- Modify: `tests/test_contract.py`
- Modify: `tests/test_mcp_contract.py`

- [x] **Step 1: Update capability expectation**

After MCP server implementation exists, update the existing capabilities test:

```python
assert body["supports_mcp_tools"] is True
```

Also assert the advertised tool list if the API adds one:

```python
assert "context_search" in body["mcp_tools"]
assert "mneme_cost_report" in body["mcp_tools"]
```

- [x] **Step 2: Update REST capabilities response**

Add:

```python
"supports_mcp_tools": True,
"mcp_tools": list(TOOL_NAMES),
```

Avoid importing MCP SDK at REST app import time if that makes `/v1/health` depend on the MCP package. If needed, define the shared `TOOL_NAMES` tuple in a tiny dependency-free module such as `mneme_service/tool_names.py`.

- [x] **Step 3: Write Codex usage guide**

`adapters/codex/MNEME_CODEX_MCP_USAGE.md` must include:

- Start daemon:

```bash
mneme serve --db /path/to/mneme.db --token "$MNEME_AUTH_TOKEN"
```

- Configure MCP server:

```bash
mneme mcp --base-url http://127.0.0.1:8765 --token "$MNEME_AUTH_TOKEN"
```

  - State explicitly:
    - Codex/MCP uses Mneme as agent-callable memory tools.
    - It does not automatically replace Codex internal prompt context.
    - Deep context-engine integrations require host lifecycle hooks described in `MNEME_HOST_ADAPTER_CONTRACT_V0.md`.
    - The agent should call `context_search`, `fetch_event`, and `expand_context` when it needs prior evidence.
    - All memory reads are audited by the daemon.

- [x] **Step 4: Add example config**

`adapters/codex/mcp_server.example.json`:

```json
{
  "mcpServers": {
    "mneme": {
      "command": "mneme",
      "args": [
        "mcp",
        "--base-url",
        "http://127.0.0.1:8765"
      ],
      "env": {
        "MNEME_AUTH_TOKEN": "replace-with-local-token"
      }
    }
  }
}
```

### Task 9: Full Verification

**Files:**
- Modify: `progress.md`
- Modify: `task_plan.md`

- [x] **Step 1: Run all tests**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected:

```text
all tests pass
```

- [x] **Step 2: Run compile check**

Run:

```bash
.venv/bin/python -m py_compile mneme_service/*.py
```

Expected: exit code 0.

- [x] **Step 3: Run daemon smoke**

Run:

```bash
.venv/bin/python -m mneme_service.cli serve --db /private/tmp/mneme-mcp-plan-smoke.db --insecure-dev --port 8766
curl -sS http://127.0.0.1:8766/v1/health
```

Expected:

```json
{"status":"OK", "...": "..."}
```

- [x] **Step 4: Run MCP smoke**

Use the SDK testing helper or a local MCP client to:

- start `mneme mcp --base-url http://127.0.0.1:8766`;
- list tools;
- call `context_search` against a prepared synthetic session.

Expected:

```text
tools include context_search, fetch_event, expand_context, recall_recent, list_segments, explain_context, mneme_cost_report
context_search returns ok=true with the expected event id
```

- [x] **Step 5: Update planning files**

Update:

- `task_plan.md`: mark Milestone 2 implementation complete only after tests and smoke pass.
- `progress.md`: record files changed, exact verification commands, warning output, and non-goals preserved.

## Acceptance Criteria

- `mneme mcp --help` works.
- MCP server exposes all seven v0 tools.
- MCP tools return the same shared envelope as REST memory tools.
- MCP/REST parity tests cover search, fetch, expand, recent recall, segments, explain, and cost report.
- MCP memory calls create daemon audit records, `MEMORY_READ` events, and memory-read traces through REST.
- MCP results do not leak redacted secrets.
- Capabilities advertise MCP tools after implementation.
- Codex usage guide avoids unsupported claims about automatic prompt replacement.
- Codex usage guide links to `MNEME_HOST_ADAPTER_CONTRACT_V0.md` for future context-engine integrations.
- Full `pytest` and `py_compile` pass.
- Live Hermes and live `hermes-mneme` are untouched.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| SDK API names differ from docs or installed version. | Keep Task 1 small, inspect installed SDK after dependency install, and adjust tests to the official helper names without changing contract assertions. |
| MCP server duplicates REST behavior. | MCP must call `MnemeRestClient`; no SQLite imports in `mcp_server.py`. |
| Tool errors become MCP protocol failures instead of model-readable payloads. | Add explicit tests for missing event and daemon-unavailable paths. |
| Codex documentation over-promises prompt control. | Include a test or review checklist that scans guidance for "automatic prompt replacement" claims. |
| Capabilities import MCP SDK at REST startup and break daemon if MCP package is absent. | Put `TOOL_NAMES` in a dependency-free module or keep the dependency mandatory once Milestone 2 ships. |
| MCP parity hides incomplete REST tool behavior. | Harden REST tool parameters first, then run MCP parity against the hardened behavior. |

## Handoff Notes

- Start implementation with Task 1 and keep each task green before moving on.
- Prefer subagent-driven execution because tests, client wrapper, MCP registration, and docs can be reviewed in small slices.
- Do not begin Hermes, LangGraph, or OpenAI Agents SDK adapter code from this plan; this milestone only creates the MCP substrate and Codex guidance.
