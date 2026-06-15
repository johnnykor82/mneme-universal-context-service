# Mneme Universal Context Service: Implementation Paths and MVP

Date: 2026-06-08
Status: strategy draft

## Decision Summary

Recommended path:

> Build Mneme first as a local daemon with REST API + MCP server, then provide Hermes as the first deep adapter and Codex/MCP as the first broad adapter.

Do not start with a hosted cloud product. Do not start by trying to support every agent framework. The first goal is proof, not scale.

## Why This Path

Mneme's strongest claim is not "we have another memory database." Its strongest claim is:

> Long-running tool agents need an event-context layer that preserves raw operational history and assembles bounded request-only context without destructive compression.

To prove that, the MVP must show three things:

1. A real agent can write structured events into Mneme.
2. Mneme can assemble useful context under a budget.
3. The agent performs better after overflow/restart than without Mneme.

REST + MCP is the shortest credible path to show this across multiple agents.

## Candidate Paths

### Path A: Local Daemon + REST + MCP

This is the recommended MVP.

Architecture:

- `mneme serve` starts a local daemon.
- Agents call REST endpoints for lifecycle integration.
- MCP exposes memory tools for agents that cannot replace their prompt assembly directly.
- SQLite is the default event store.
- Optional embedding/reranking/enrichment providers are configured locally.

Pros:

- Works across runtimes.
- Easy to demo locally.
- Clear integration contract.
- MCP gives immediate compatibility with Codex-like clients.
- REST gives serious runtime authors a stable API.

Cons:

- Requires daemon packaging.
- Needs careful auth/local-port/security defaults.
- More moving parts than a library-only implementation.

Best first adapters:

- Hermes native adapter, because we already have proof from the PR prototype.
- Generic MCP adapter, because it gives broad agent compatibility.

Verdict: **best first product path**.

### Path B: MCP-Only Memory Server

Architecture:

- Mneme is an MCP server only.
- Agents use tools like `context_search`, `fetch_event`, and `recall_recent`.
- No automatic request preparation.

Pros:

- Fastest to make useful for Codex, Claude Code, Cursor, and other MCP-capable tools.
- Easy to explain.
- Lower integration burden.

Cons:

- Does not prove the core request-only context assembly idea.
- Agent must decide when to call memory tools.
- Cannot solve context overflow automatically.

Verdict: **good demo layer, insufficient as the whole product**.

### Path C: Python/TypeScript Library

Architecture:

- Mneme is imported as a library.
- Agent runtime calls functions directly.
- No daemon.

Pros:

- Simple for framework users.
- Lower operational complexity.
- Good for LangGraph/OpenAI Agents SDK examples.

Cons:

- Harder to connect to closed or external agent runtimes.
- Harder to share memory across processes.
- Less product-like.

Verdict: **useful later as SDK wrapper around REST, not first architecture**.

### Path D: Hosted Mneme Cloud

Architecture:

- Mneme runs as a cloud service.
- Agents send events to hosted storage and retrieval.

Pros:

- Monetization path.
- Easier team dashboards.
- Enterprise analytics possible.

Cons:

- Privacy concerns are severe.
- Requires auth, billing, multi-tenancy, deletion, compliance.
- Distracts from proving the core idea.

Verdict: **not MVP**.

## Recommended MVP

### MVP Name

`mneme-context-service`

### MVP Goal

Prove that an external event-context service improves continuity for long-running tool-using agents after context overflow and restart.

### MVP Scope

Build:

- local daemon;
- REST API;
- MCP server;
- SQLite event store;
- event ingestion;
- request context preparation;
- memory tools;
- minimal/standard/quality cost modes;
- trace and overhead reporting;
- benchmark harness;
- Hermes adapter;
- generic MCP adapter.

Do not build yet:

- hosted cloud;
- web dashboard;
- enterprise auth;
- multi-user team memory;
- complex distributed storage;
- automatic adapters for every framework.

## MVP Repository Shape

Potential repo:

```text
mneme-context-service/
  README.md
  docs/
    architecture.md
    api.md
    benchmarks.md
    cost-model.md
    adapters.md
  mneme_service/
    server.py
    api/
    core/
    storage/
    retrieval/
    assembly/
    mcp/
  adapters/
    hermes/
    codex-mcp/
    langgraph/
    openai-agents/
  benchmarks/
    scenarios/
    runners/
    reports/
  examples/
    simple_agent/
    long_coding_task/
```

## API v0

REST endpoints:

- `POST /v1/sessions/start`
- `POST /v1/events`
- `POST /v1/turns/complete`
- `POST /v1/context/prepare`
- `POST /v1/tools/context_search`
- `POST /v1/tools/fetch_event`
- `POST /v1/tools/expand_context`
- `POST /v1/tools/recall_recent`
- `GET /v1/traces/{trace_id}`
- `GET /v1/costs/session/{session_id}`

MCP tools:

- `context_search`
- `fetch_event`
- `expand_context`
- `list_segments`
- `recall_recent`
- `explain_context`
- `mneme_cost_report`

## Adapter Strategy

### Hermes Adapter

Purpose:

- Demonstrate deep integration with lifecycle hooks.
- Show automatic request-only context assembly.

Required contract:

- `on_turn_complete` sends finalized transcript/events.
- `prepare_request_messages` calls `/v1/context/prepare`.
- Hermes tools expose Mneme memory tools.

Status:

- We already have prototype evidence through `hermes-mneme` native hook work.

### Codex Adapter

Purpose:

- Demonstrate broad compatibility through MCP and Codex plugins.

Realistic first version:

- MCP memory tools;
- Codex plugin packaging;
- skill instructions that teach Codex when to call Mneme;
- optional hooks for logging where supported.

Not realistic first version:

- replacing Codex's internal prompt assembly.

### LangGraph Adapter

Purpose:

- Show that Mneme fits framework-based agents.

Shape:

- wrapper node before model call;
- event ingestion after graph node execution;
- Mneme tools in the graph tool registry.

### OpenAI Agents SDK Adapter

Purpose:

- Show compatibility with a modern generic agent SDK.

Shape:

- middleware/wrapper around model invocation;
- event ingestion after tool/model events;
- optional context preparation before model request.

## Benchmark Harness

The benchmark must show value in terms that non-Mneme users understand.

### Required Scenarios

1. **Long Coding Task**
   - A task requiring many file reads, command runs, failures, and retries.

2. **Old Tool Output Recall**
   - A required answer depends on exact output from many turns earlier.

3. **Restart Continuity**
   - Agent stops mid-task, restarts, and must continue without repeating work.

4. **Context Overflow**
   - Agent exceeds a configured context threshold and must continue after context assembly.

5. **Memory Tool Navigation**
   - Agent must search, fetch, and expand prior events to answer correctly.

### Baselines

Compare:

- no memory service;
- built-in compaction/summarization;
- vector-only memory;
- Mneme minimal mode;
- Mneme standard mode;
- Mneme quality mode.

### Metrics

Primary:

- task success;
- exact recall;
- restart continuation score;
- duplicate-work rate;
- raw evidence recovery.

Secondary:

- prompt tokens over time;
- assembly latency;
- embedding calls;
- reranker calls;
- enrichment calls;
- total extra cost;
- hallucinated-memory rate.

## Cost Model

Mneme must make cost visible.

### Minimal Mode

Includes:

- SQLite event store;
- token estimates;
- keyword/recency retrieval;
- protected recent tail;
- no embeddings;
- no reranker;
- no LLM enrichment.

Purpose:

- prove low-overhead local continuity.

### Standard Mode

Includes:

- local embeddings;
- vector + keyword retrieval;
- graph expansion;
- no LLM enrichment by default;
- reranker off by default.

Purpose:

- best default for developers.

### Quality Mode

Includes:

- embeddings;
- reranking;
- periodic LLM enrichment;
- detailed traces;
- stronger context assembly.

Purpose:

- showcase quality for demos and enterprise workflows.

### Cost Report

Every benchmark and demo should include:

```json
{
  "session_id": "session-123",
  "mode": "standard",
  "events_ingested": 480,
  "embedding_batches": 31,
  "embedding_items": 392,
  "reranker_calls": 0,
  "enrichment_calls": 0,
  "prepare_calls": 9,
  "prepare_latency_ms_p50": 84,
  "prepare_latency_ms_p95": 210,
  "extra_provider_tokens": 0,
  "assembled_prompt_tokens_avg": 88000
}
```

The important business message:

> Mneme can run in cheap local modes and only spend extra model calls when explicitly configured to do so.

## Presentation Package

Minimum public-facing package:

- one architecture diagram;
- one before/after context overflow trace;
- one benchmark table;
- one cost table;
- one 3-minute demo video;
- one README with quickstart;
- one blog post explaining "event memory vs destructive compression."

## Recommended First Milestones

### Milestone 1: Protocol Freeze

Deliver:

- REST API draft;
- MCP tool schemas;
- event schema;
- trace schema;
- cost report schema.

### Milestone 2: Local Daemon MVP

Deliver:

- daemon;
- SQLite store;
- event ingestion;
- keyword/recency retrieval;
- context prepare;
- basic traces.

### Milestone 3: MCP Tool Server

Deliver:

- `context_search`;
- `fetch_event`;
- `expand_context`;
- `recall_recent`;
- `explain_context`.

### Milestone 4: Hermes Reference Adapter

Deliver:

- deep lifecycle integration;
- automatic request preparation;
- memory tools.

### Milestone 5: Benchmark Harness

Deliver:

- scenarios;
- baseline runner;
- Mneme runner;
- metric report.

### Milestone 6: Public Demo

Deliver:

- README;
- architecture diagram;
- demo logs;
- benchmark results;
- cost model.

## Strategic Recommendation

Build this as a developer-facing open-source project first.

The highest-probability path to attention is:

1. credible OSS implementation;
2. clear benchmark results;
3. clean integration story;
4. strong README;
5. public issue/PR history showing real agent-runtime pain;
6. demos that show exact raw evidence recovery after context pressure.

Trying to monetize too early would weaken the project. The better first outcome is reputation, adoption, and technical credibility.

