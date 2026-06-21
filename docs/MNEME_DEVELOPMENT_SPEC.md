# Mneme Development Specification

Status: review index spec
Date: 2026-06-20

Note: this older document is an index-style review specification. For a
single-file, self-contained reviewer packet, use
`docs/MNEME_STANDALONE_SPEC.md`.

This document is the reviewer-facing specification for Mneme Context Service.
It consolidates the product boundary, business requirements, technical
requirements, acceptance criteria, and traceability links needed to review the
implementation.

It does not replace the protocol contracts. The canonical protocol details
remain in:

- `API_MCP_CONTRACT_V0.md`
- `MNEME_HOST_ADAPTER_CONTRACT_V0.md`
- `docs/PROVIDER_CONFIGURATION.md`
- `docs/BENCHMARKS.md`
- `docs/TESTING_AND_CI.md`

## 1. Purpose

Mneme is a local-first, vendor-neutral context memory service for long-running,
tool-using agents. It stores normalized agent events, builds searchable memory,
tracks execution state, and can assemble bounded request-only context for
runtimes that expose a host lifecycle hook.

The project exists to solve context loss and destructive compaction in
long-running agent workflows without making the host transcript mutable or
opaque.

## 2. Product Boundary

Mneme is:

- a daemon/service with REST lifecycle and control-plane APIs;
- a read-oriented MCP memory tool server for agents;
- a context preparation engine for host runtimes that provide request hooks;
- a local-first memory substrate with optional provider-backed quality layers.

Mneme is not:

- a hosted SaaS product in the current scope;
- a replacement for Codex, Claude Code, Hermes, OpenClaw, or other agents;
- a hidden automatic prompt injector for runtimes that do not expose hooks;
- a general chatbot user-memory product;
- an unaudited autonomous memory writer.

## 3. Target Users

- Agent runtime authors who need durable event memory.
- Coding-agent builders integrating context recovery.
- Developers running local/private long-running agents.
- Teams evaluating context management for tool-heavy workflows.
- Adapter authors building runtime-specific integrations.

## 4. Required Specification Sections

A complete Mneme feature or release specification should include:

1. Metadata: title, status, date, owners, reviewers, version.
2. Executive summary: what is being built and why.
3. Product boundary: in-scope, out-of-scope, non-goals.
4. Personas and use cases.
5. Business requirements and measurable success criteria.
6. Functional requirements.
7. Non-functional requirements: security, privacy, performance, reliability,
   observability, portability.
8. Architecture overview and component responsibilities.
9. Data model and persistence rules.
10. Public API/tool contract, schemas, errors, and versioning.
11. Integration contracts and adapter capability levels.
12. Security model and threat assumptions.
13. Configuration and deployment model.
14. Testing, benchmarks, acceptance criteria, and traceability matrix.
15. Migration and compatibility strategy.
16. Operations and troubleshooting.
17. Roadmap, rollout plan, and deferred work.
18. Risks, open questions, and explicit reviewer prompts.

## 5. Business Requirements

BR-1: Preserve raw agent history as structured events.

BR-2: Provide request-only context assembly that does not rewrite canonical
transcripts.

BR-3: Let agents inspect memory evidence through explicit tools.

BR-4: Keep local-first deployment viable without external providers.

BR-5: Support optional quality improvements through embeddings, reranking, and
LLM enrichment with explicit configuration and cost accounting.

BR-6: Keep host-runtime integration honest. MCP-only clients receive
agent-callable memory tools; automatic context assembly requires host lifecycle
hooks.

BR-7: Keep host adapters separable from the Mneme engine/core package.

## 6. Functional Requirements

FR-1: Session lifecycle

- Start sessions explicitly through REST.
- Reject events for unknown sessions.
- Preserve session metadata, project isolation, lineage, and resume/fresh
  classification.
- Provide session discovery for agent-facing tools when internal session ids are
  unknown.

FR-2: Event ingestion

- Accept normalized event batches.
- Enforce schema versions and payload limits.
- Store canonical event JSON and searchable text.
- Redact secrets before persistence, indexing, provider calls, and MCP-visible
  output.
- Support idempotent replay with stable event ids.

FR-3: Memory retrieval

- Provide keyword/recency retrieval in provider-free mode.
- Provide optional semantic retrieval through embeddings.
- Include graph dependency candidates and optional reranking.
- Support session, lineage, and global scopes.

FR-4: Context preparation

- Prepare bounded request-only context through `/v1/context/prepare`.
- Include retrieved evidence, execution state, goal trail, memory hints,
  checkpoint hints, global candidates, and protected recent tail when budgets
  allow.
- Return traces and adapter metadata.

FR-5: Execution state

- Maintain runtime-neutral execution state: goal, current step, decisions,
  active entities, open loops, last tool, and enrichment signals.
- Expose state and goal history through REST/MCP memory tools.

FR-6: Segmentation and drift

- Detect topic switches and resume/fresh session signals.
- Create segment records and expose segment skeletons.
- Preserve lineage without copying canonical events.

FR-7: MCP memory tools

- Expose read-oriented memory tools through MCP.
- Proxy MCP behavior through REST so REST remains canonical.
- Expose `resolve_session` and `list_sessions` before session-bound tools.
- Audit memory reads for session-bound tools.

FR-8: Cost and traceability

- Record traces for context preparation and memory reads.
- Expose cost reports for ingested events, provider calls, index size, and
  latency summaries.

## 7. Non-Functional Requirements

Security:

- Require authentication by default.
- Redact common secrets before persistence and model/provider-visible output.
- Do not print or expose raw bearer tokens or API keys.
- Keep MCP read-only unless a future write contract is explicitly approved.

Privacy:

- Use local SQLite by default.
- Keep project isolation keys in session privacy metadata.
- Treat stored tool output and imported transcripts as untrusted evidence.

Reliability:

- Ingestion should store canonical events before optional provider work.
- Provider failures should degrade retrieval quality, not lose events.
- Replay with stable ids must be idempotent.

Performance:

- Provider-free mode must work for tests and local fallback.
- Provider-backed retrieval should remain optional and measurable.
- Context preparation must enforce token budgets and return degraded warnings
  instead of silently overflowing.

Portability:

- The engine/core must remain host-runtime neutral.
- Host-specific setup belongs in adapter repositories/packages.

## 8. Architecture

Primary components:

- REST daemon: lifecycle, ingestion, context preparation, traces, costs,
  capabilities, export/delete.
- SQLite store: sessions, events, turns, traces, audit records, segments,
  embeddings, execution state, state history, lineage, graph edges.
- Retrieval pipeline: keyword/recency, optional embeddings, graph expansion,
  optional reranker.
- Context assembler: budgeted request context construction.
- MCP server: agent-facing memory tools that proxy REST.
- Host adapters: runtime-specific translation layers outside the engine/core.

Detailed architecture references:

- `MNEME_UNIVERSAL_CONTEXT_SERVICE_CONCEPT.md`
- `IMPLEMENTATION_PATHS_AND_MVP.md`
- `HERMES_MNEME_COMPARISON.md`
- `MILESTONE_6_FULL_HERMES_MNEME_PARITY_COMPLETION_PLAN.md`

## 9. Data Model

Canonical schemas are defined in `API_MCP_CONTRACT_V0.md`.

Core objects:

- `mneme.session.v0`
- `mneme.event_batch.v0`
- `mneme.event.v0`
- `mneme.turn.v0`
- `mneme.context_prepare_request.v0`
- `mneme.context_prepare_response.v0`
- `mneme.trace.v0`
- `mneme.cost_report.v0`
- `mneme.execution_state.v0`
- `mneme.state_history_entry.v0`
- `mneme.session_lineage.v0`
- `mneme.graph_edge.v0`

Persistence rules:

- Sessions are explicit lifecycle records.
- Events are immutable by stable id and immutable-hash checks.
- Memory reads are auditable and represented as trace/audit records.
- Optional provider artifacts must not become the only canonical memory source.

## 10. API And MCP Contract

REST is the lifecycle and control-plane surface.

MCP is the agent-facing memory tool surface.

The REST/MCP contract must define:

- route/tool names;
- request and response schemas;
- error envelopes;
- warnings;
- redaction behavior;
- trace ids;
- versioning and compatibility;
- capability detection.

Discovery requirement:

- Agents must not guess internal session ids.
- If a session id is unknown, agents should use `resolve_session` or
  `list_sessions` with project path, thread id, slug, or query.
- Session-bound tools should keep returning `NOT_FOUND` for invalid ids, with
  details that point to the discovery path.

Canonical reference: `API_MCP_CONTRACT_V0.md`.

## 11. Integration Modes

`TOOLS_ONLY`

- Agent can call MCP memory tools.
- No automatic prompt replacement.
- Suitable for Codex/MCP today.

`CONTEXT_ENGINE`

- Host adapter calls REST lifecycle hooks.
- Host adapter calls `/v1/context/prepare` before model requests.
- Required for automatic request-context assembly.

Canonical reference: `MNEME_HOST_ADAPTER_CONTRACT_V0.md`.

## 12. Configuration And Deployment

Supported current deployment:

- Python package installed locally.
- `mneme serve` daemon.
- SQLite database path configured by CLI/config file.
- Bearer token from environment.
- Optional provider settings from `mneme.toml` and environment variables.
- MCP process started separately and pointed at the daemon.

References:

- `docs/INSTALLATION.md`
- `docs/PROVIDER_CONFIGURATION.md`
- `mneme.example.toml`

## 13. Testing And Acceptance

Required verification layers:

- Unit and contract tests for REST routes.
- MCP discovery and parity tests.
- Redaction/privacy tests.
- Codex adapter/hook tests where adapter code is present.
- Provider-free fallback tests.
- Optional provider smoke tests when provider claims are made.
- Parity acceptance tests against recovered Hermes-Mneme behavior.
- Compile checks for Python modules.

Current command references:

- `.venv/bin/python -m pytest -q`
- `.venv/bin/python -m pytest tests/test_parity_recovery.py -q`
- `python3 -m py_compile mneme_service/*.py`

Detailed reference: `docs/TESTING_AND_CI.md`.

## 14. Benchmarks

Benchmark documentation must distinguish:

- direct prompt baseline;
- Mneme retrieval/context-preparation path;
- provider-free fallback;
- provider-backed quality path;
- token, latency, and quality metrics;
- cases where Mneme can cost more than direct prompting.

Canonical reference: `docs/BENCHMARKS.md`.

## 15. Traceability Matrix

| Requirement | Implementation Area | Verification |
|---|---|---|
| Explicit sessions | `mneme_service/app.py`, `Store.put_session` | `tests/test_contract.py` |
| Event ingestion | `POST /v1/events`, `Store.put_event` | `tests/test_contract.py`, `tests/test_codex_ingest.py` |
| MCP tools proxy REST | `mneme_service/mcp_server.py`, `MnemeRestClient` | `tests/test_mcp_contract.py` |
| Session discovery | `resolve_session`, `list_sessions`, `Store.list_sessions` | `tests/test_contract.py`, `tests/test_mcp_contract.py` |
| Redaction | `mneme_service/security.py`, REST error handler | privacy tests in contract/MCP suites |
| Execution state | `mneme_service/state.py`, state history storage | `tests/test_state.py` |
| Context preparation | `/v1/context/prepare` | `tests/test_context_assembly.py`, parity tests |
| Provider config | `mneme_service/config.py` | `tests/test_config.py`, provider docs |
| Codex tools-only honesty | Codex docs/skill/snippets | `tests/test_mcp_contract.py`, `tests/test_codex_adapter.py` |

## 16. Roadmap Status

Completed:

- concept and architecture;
- API/MCP contract;
- host adapter contract;
- local daemon MVP;
- MCP substrate;
- Codex transcript/hook adapter groundwork;
- provider config, embeddings, hybrid retrieval, execution state, segmentation,
  lineage, graph scoring, reranking, enrichment, and context assembly parity;
- clean public core/adapter publication split;
- Codex/MCP session discovery hotfix in the working tree.

Deferred:

- Hermes host adapter implementation until upstream Hermes context-engine hooks
  are accepted.
- MCP write/checkpoint tools until a separate security-reviewed write contract
  exists.
- Hosted/cloud product shape.

## 17. Risks And Reviewer Prompts

Reviewers should check:

- whether product boundaries are still clean between engine/core and adapters;
- whether MCP remains honestly tools-only for Codex;
- whether session discovery can leak too much cross-project metadata;
- whether redaction is strong enough for session summaries and error details;
- whether `NOT_FOUND` guidance is helpful without being noisy;
- whether provider degradation preserves canonical event storage;
- whether benchmarks measure quality, not just token count;
- whether public docs match the actual install path.

## 18. Open Questions

- Should the engine/core repository include a generated OpenAPI schema artifact
  in addition to contract markdown?
- Should session discovery support explicit project-isolation filtering in the
  public API, or is current metadata matching sufficient for v0?
- Should MCP discovery tools audit anonymous discovery calls separately from
  session-bound memory reads?
- Should `mneme-memory` become part of the core package or remain adapter-owned?
- What is the first stable public version after the engine/adapter repository
  split is fully rehearsed?
