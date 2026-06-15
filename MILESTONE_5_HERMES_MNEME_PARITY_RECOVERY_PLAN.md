# Milestone 5: Hermes-Mneme Functional Parity Recovery

Date: 2026-06-12
Status: planned

## Goal

Port the core functional behavior of `hermes-mneme` into the universal Mneme
daemon before continuing adapter work.

The goal is functional parity of the memory/context engine logic, not a
line-for-line copy of the Hermes plugin. Hermes-specific lifecycle hook wiring
stays out of the daemon and will later become a thin host adapter.

## Direction Change

Adapters are paused until the universal daemon has the core Mneme quality
pipeline:

- provider configuration;
- semantic embeddings and hybrid retrieval;
- execution state and goal history;
- segmentation and intent routing;
- runtime-neutral session/topic drift handling;
- graph/dependency-aware scoring;
- real budgeted `/v1/context/prepare`;
- optional reranking;
- optional LLM enrichment;
- parity/conformance tests.

Codex dogfood can continue only as a verification surface for this pipeline, not
as the main implementation target.

## Non-Goals

- Do not modify live Hermes.
- Do not modify live `hermes-mneme`.
- Do not implement Hermes, LangGraph, OpenAI Agents SDK, or deeper Codex host
  adapters during this milestone.
- Do not make hidden provider calls in minimal mode.
- Do not copy Hermes-specific session-id discovery code into the daemon.

In scope for this milestone: runtime-neutral drift semantics in the daemon:
topic switch, segment boundary, resume/fresh-session classification,
lineage/carry-over policy, and traces. Host adapters provide authoritative
lifecycle metadata; the daemon owns the portable memory decisions.

## Boundary: Generic Drift vs Host Hooks

Session/topic drift has two layers:

- Generic daemon layer: semantic drift scoring, explicit topic switches,
  segment rollover, resume vs fresh-session decisions, lineage/carry-over
  policy, first-turn resume context fill, and degraded behavior when embeddings
  are unavailable.
- Host adapter layer: how a runtime exposes `session_id`, conversation id,
  finalized turn snapshots, pre-request message replacement, model budget,
  platform/model metadata, and lifecycle events.

The local `_hermes-mneme-native` copy confirms this split. Its shared pipeline
uses `on_turn_complete()` for ingestion and `prepare_request_messages()` for
request-only assembly when native Hermes hooks exist, while keeping
`compress()` only as a legacy fallback.

## Porting Principle

Port behavior, tests, and concepts from `hermes-mneme`; do not preserve
Hermes-specific coupling.

| `hermes-mneme` piece | Universal daemon target |
|---|---|
| `config.py` provider/settings surface | `mneme.toml` plus env/CLI precedence and secret-safe examples |
| `index.py` embedding index | provider-backed embedding service, index tables, semantic search, keyword fallback |
| `compressor.py` embedding-only tool-output summary | embedding input preparation while preserving raw events |
| `store.py` execution state/history pieces | versioned REST schemas and SQLite tables for state and goal history |
| `classifier.py` | daemon-local deterministic intent classifier |
| `segmenter.py` | runtime-neutral segmenter over stored events/embeddings |
| `router.py` | retrieval pipeline: query build, semantic search, recency/type/dependency scoring, rerank hook |
| `graph.py` | typed event graph and dependency propagation |
| `prompt_builder.py` | `/v1/context/prepare` budgeted assembly |
| `enrichment.py` | optional provider-configured LLM enrichment |
| `engine.py` shared context pipeline | daemon service functions behind REST/MCP and `/v1/context/prepare` |
| `engine.py` Hermes hook transport/session-id discovery | future Hermes host adapter; not daemon core |

## Task 1: Provider Config Foundation

**Status:** complete

Create a configuration system before any provider network calls.

Deliverables:

- `mneme_service/config.py` expanded beyond daemon host/auth settings.
- Config precedence documented and tested:
  1. CLI arguments;
  2. environment variables;
  3. config file;
  4. defaults.
- Example `mneme.example.toml` with no real secrets.
- Secret handling rules for provider API keys.
- Capabilities reflect configured but disabled/enabled provider surfaces.

TDD verification:

```bash
.venv/bin/python -m pytest tests/test_config.py -q
.venv/bin/python -m pytest -q
.venv/bin/python -m py_compile mneme_service/*.py
```

Result: complete. Added `ProviderSettings`, `load_settings()`, `mneme.example.toml`,
provider-aware capabilities, and `mneme serve` provider/config flags without
making provider calls.

## Task 2: Embedding Provider and Index

**Status:** complete

Port semantic embedding behavior in a daemon-safe way.

Deliverables:

- Embedding provider abstraction.
- OpenAI/Jina-compatible HTTP embedding client.
- SQLite embedding index tables.
- Optional `sqlite-vec` support if dependency is installed.
- Python cosine fallback.
- Batch embedding path.
- Provider circuit breaker.
- Events remain stored when embedding fails.
- Tool-output embedding input compression while raw content stays intact.

TDD verification:

```bash
.venv/bin/python -m pytest tests/test_embeddings.py -q
.venv/bin/python -m pytest tests/test_contract.py -q
.venv/bin/python -m pytest -q
```

Result: complete. Added `mneme_service.embeddings`, an OpenAI/Jina-compatible
embedding provider with mocked/injectable HTTP transport support, a provider
circuit breaker, SQLite `embedding_index`/`embedding_metrics` tables, Python
cosine fallback search, batch indexing, tool-output embedding compression, and
best-effort ingestion integration that stores events even when embedding fails.
`sqlite_vec` is not installed in the project `.venv`, so Task 2 verified the
portable Python fallback path; hybrid REST/MCP retrieval integration starts in
Task 3.

## Task 3: Hybrid Retrieval Pipeline

**Status:** complete

Replace keyword-only retrieval with hybrid semantic plus lexical/recency
retrieval.

Deliverables:

- `context_search` can return semantic hits when embeddings are enabled.
- Keyword/recency fallback remains available and tested.
- Traces record retrieval strategies and degraded fallback reasons.
- Cost report counts embedding batches/items/input chars/failures.
- MCP/REST parity stays intact.

TDD verification:

```bash
.venv/bin/python -m pytest tests/test_retrieval.py -q
.venv/bin/python -m pytest tests/test_mcp_contract.py -q
.venv/bin/python -m pytest -q
```

Result: complete. REST `context_search` now uses hybrid retrieval when
embeddings are enabled: vector candidates from the embedding index are merged
with keyword/recency results, keyword/recency fallback remains available in
minimal mode, and memory-read traces record retrieval strategies, degraded
state, and fallback reasons. MCP parity remains intact because MCP tools proxy
the same REST surface.

## Task 4: Execution State and Goal History

**Status:** complete

Port the state layer without tying it to Hermes internals.

Deliverables:

- Versioned execution-state schema.
- SQLite execution state table.
- Append-only state history table.
- REST and MCP access to execution state and goal history, or an explicitly
  versioned replacement for the `hermes-mneme` tools.
- State update rules based on normalized events.
- Export/delete include state and history.

TDD verification:

```bash
.venv/bin/python -m pytest tests/test_state.py -q
.venv/bin/python -m pytest tests/test_mcp_contract.py -q
.venv/bin/python -m pytest -q
```

Result: complete. Added deterministic runtime-neutral execution state updates
from normalized events, SQLite `execution_state` and append-only
`state_history`, versioned REST/MCP tools `get_execution_state` and
`get_goal_history`, export/delete coverage, and MCP proxy/discovery tests. This
slice intentionally avoids Hermes lineage inheritance and LLM enrichment; those
remain later daemon/adapter concerns.

## Task 5: Segmentation, Intent Classification, and Drift Semantics

**Status:** complete

Port deterministic classification, embedding-drift segmentation, and the
runtime-neutral parts of session/topic drift handling.

Deliverables:

- Runtime-neutral classifier for continuation/switch/new-task/clarification.
- Segmenter using embedding drift and explicit switch triggers.
- Segment metadata stored and exposed through `list_segments`.
- Resume vs fresh-session classification based on adapter-supplied lifecycle
  metadata and existing daemon state.
- Lineage/carry-over semantics that prevent orphaned work across session
  rotation or restart without relying on Hermes thread-local internals.
- First-turn resume context-fill behavior that forces context assembly when a
  resumed session has prior events.
- Drift traces showing signals, decision, segment/session effects, and fallback
  reasons.
- Cold-start and embedding-outage behavior remains deterministic.
- Tests cover Russian and English switch/question patterns.

TDD verification:

```bash
.venv/bin/python -m pytest tests/test_classifier.py tests/test_segments.py tests/test_session_drift.py -q
.venv/bin/python -m pytest -q
```

Slice A result: complete. Added deterministic English/Russian classifier
coverage for continuation, explicit switch, and clarification. Added
event-ingest segment updates for accepted redacted `USER_MESSAGE` events:
explicit switches close the active segment and open a new one, continuation
messages extend the active segment, and `list_segments` exposes status,
anchors, counts, title, and drift reason. Remaining Task 5 work: new-task
labeling, embedding-drift segmentation, resume/fresh-session classification,
lineage/carry-over, first-turn resume context fill, and drift traces.

Slice B result: complete. Added `NEW_TASK` intent resolution for high embedding
drift and event-driven segment embedding ids. When embeddings are enabled and
the active segment has at least three indexed embeddings, a user message whose
embedding is far from the active segment centroid rolls over to a new segment
with `drift_reason=EMBEDDING_DRIFT`. Cold start and provider failure stay
deterministic by yielding drift `0.0`. Remaining Task 5 work:
resume/fresh-session classification, lineage/carry-over, first-turn resume
context fill, and drift traces.

Slice C result: complete. Added redacted `SEGMENT_DRIFT` traces whenever a
user message causes an explicit-switch or embedding-drift segment rollover.
The trace records classifier signals, intent/drift reason, closed/opened
segment ids, event counts, fallbacks, and warnings without copying raw message
content. Updated the API/MCP contract additively to document the trace type and
payload. Remaining Task 5 work: resume/fresh-session classification,
lineage/carry-over, and first-turn resume context fill.

Slice D result: complete. Added `mneme.session_state.v0` classification to
`POST /v1/sessions/start` responses. New empty sessions classify as `FRESH`;
existing sessions with canonical events or turns classify as `RESUME` with
`resume_source=EXISTING_SESSION_EVENTS`; adapter lifecycle metadata can classify
a newly created session as `RESUME` with `resume_source=ADAPTER_METADATA`.
The decision includes prior counts, adapter resume signals, lineage session id,
and `requires_context_fill` for resumed sessions with prior daemon state.
Remaining Task 5 work: lineage/carry-over and first-turn resume context fill.

Slice E result: complete. Added `mneme.session_lineage.v0` edges created from
adapter lineage metadata when both sessions exist. Session-scoped search,
fetch, recent recall, graph expansion, and embedding lookup can now resolve the
lineage chain so resumed/rotated sessions can carry over parent evidence
without copying parent canonical events into the child export. Updated the
API/MCP contract and export shape to expose lineage edges. Remaining Task 5
work: first-turn resume context fill.

Slice F result: complete. Added a persisted one-shot resume context-fill latch
set by `POST /v1/sessions/start` when `mneme.session_state.v0` reports
`requires_context_fill=true`. The next successful `/v1/context/prepare` now
fills from recent current/lineage events with reason `RESUME_CONTEXT_FILL` when
ordinary retrieval selects no evidence, then marks the latch fulfilled so later
under-budget requests can pass through normally. Task 5 is complete.

## Task 6: Typed Event Graph and Dependency Scoring

**Status:** complete

Port graph-aware context recovery.

Deliverables:

- Typed graph edges for tool call, tool output, decision/follows relations.
- Dependency traversal for `expand_context`.
- Dependency bonuses in retrieval scoring.
- Memory-read audit still accounts for all exposed event ids.

TDD verification:

```bash
.venv/bin/python -m pytest tests/test_graph.py tests/test_retrieval.py -q
.venv/bin/python -m pytest tests/test_mcp_contract.py -q
```

Slice A result: complete. Added `mneme.graph_edge.v0` persistence for typed
edges derived from event `parent_event_ids`, including `TOOL_RESULT`,
`DECISION_FOLLOWS`, and generic `FOLLOWS`. Export now includes
`event_graph_edges`, and `expand_context` uses typed graph edges while
preserving memory-read audit coverage for all exposed event ids. Remaining Task
6 work: dependency bonuses in retrieval scoring.

Slice B result: complete. `context_search` now adds direct graph neighbors of
primary semantic/keyword hits as dependency candidates before `top_k` packing.
Graph dependency candidates use strategy `GRAPH_DEPENDENCY`, reason
`GRAPH_DEPENDENCY:<edge_type>`, and a smaller bonus score so primary matches
stay ahead while tool calls, tool outputs, and decisions remain recoverable.
Task 6 is complete.

## Task 7: Budgeted Context Assembly

**Status:** complete

Upgrade `/v1/context/prepare` from evidence insertion to real request-only
assembly.

Deliverables:

- Execution state block.
- Retrieved context block.
- Protected tail policy.
- Budget split and collision resolution.
- `changed=false` pass-through when appropriate.
- Trace records for selected/dropped events and token budgets.
- No Mneme-generated context persisted as canonical transcript.

Completed slices:

- Slice A: `/v1/context/prepare` now inserts a request-only
  `[MNEME EXECUTION STATE]` block when `policy.include_execution_state=true`,
  the derived execution state is non-empty, and the block fits
  `budget_split.execution_state_ratio`. The generated block is returned in the
  prepared message list and is not stored as a canonical transcript event.
- Slice B: when a request is over budget and
  `policy.include_recent_tail=true`, `/v1/context/prepare` now preserves the
  system prompt plus a contiguous recent message tail under
  `budget_split.recent_tail_ratio`, records `protected_tail_tokens`, and avoids
  inserting empty Mneme-generated messages.
- Slice C: retrieved evidence is now packed under
  `budget_split.retrieved_context_ratio`. Events that do not fit are excluded
  from the generated evidence block and recorded as
  `RETRIEVED_CONTEXT_BUDGET_EXCEEDED` in response `dropped_event_refs` and
  stored trace `dropped_events`.
- Slice D: final assembly now checks total message tokens plus headroom. When
  independently budgeted blocks collide, prepare drops retrieved evidence first
  with reason `CONTEXT_COLLISION_BUDGET_EXCEEDED`, can drop the state block
  next, and then tightens the protected tail if needed. Task 7 is complete.

TDD verification:

```bash
.venv/bin/python -m pytest tests/test_context_assembly.py -q
.venv/bin/python -m pytest tests/test_contract.py -q
.venv/bin/python -m pytest -q
```

## Task 8: Optional Reranker

**Status:** complete

Port reranker behavior after semantic retrieval is stable.

Deliverables:

- Provider-configured reranker client.
- Jina/BGE/Cohere-compatible response parsing.
- Failure keeps original ranking and records degraded trace/failure count.
- Cost report includes reranker calls/failures.

TDD verification:

```bash
.venv/bin/python -m pytest tests/test_reranker.py -q
.venv/bin/python -m pytest -q
```

Result: complete. Added `mneme_service.reranker.HttpRerankerProvider` with
Jina/Cohere-style `/rerank` parsing, REST-canonical `context_search` reranking,
degraded fallback to original ranking, trace strategy/fallback metadata, and
per-session reranker call/failure metrics in cost reports. Tests use injected
fake providers and `httpx.MockTransport`; no real provider calls are made.

## Task 9: Optional LLM Enrichment

**Status:** complete

Port LLM enrichment after provider config and redaction are in place.

Deliverables:

- Provider-configured OpenAI-compatible enrichment client.
- Strict JSON prompt and safe parse/recovery behavior.
- Enrichment writes only redacted, structured state fields.
- Failures do not block ingestion/retrieval.
- Cost report includes enrichment calls/failures.

TDD verification:

```bash
.venv/bin/python -m pytest tests/test_enrichment.py -q
.venv/bin/python -m pytest -q
```

Result: complete. Added `mneme_service.enrichment.HttpLLMEnrichmentProvider`
with OpenAI-compatible chat-completions JSON mode, strict JSON-only prompt,
safe structured parsing, redacted enrichment application to execution state,
non-blocking failure behavior, and per-session enrichment call/failure metrics.
Tests use injected fake providers and `httpx.MockTransport`; no real provider
calls are made.

## Task 10: Parity Acceptance Suite

**Status:** complete

Define the minimum behavior that proves the universal daemon is a real Mneme
successor.

Acceptance criteria:

- Minimal mode works with zero provider calls.
- Semantic mode retrieves paraphrased evidence that keyword search misses.
- Embedding outage degrades to keyword/recency without losing events.
- State/goal history survives daemon restart.
- Segmentation separates explicit topic switches.
- Session/topic drift handles resume, fresh session rotation, lineage/carry-over,
  and first-turn resume context fill without Hermes-specific hooks.
- `/context/prepare` includes state, retrieved evidence, and protected tail
  under budget.
- MCP tools expose the same data as REST tools.
- Redaction precedes storage, indexing, provider calls, traces, and MCP results.

TDD verification:

```bash
.venv/bin/python -m pytest tests/test_parity_recovery.py -q
.venv/bin/python -m pytest -q
.venv/bin/python -m py_compile mneme_service/*.py
```

Result: complete. Added `tests/test_parity_recovery.py` with end-to-end
acceptance coverage for minimal mode, provider-backed semantic/reranked/enriched
retrieval, embedding outage fallback, restart-safe state/history, segmentation,
resume/fresh session drift, lineage carry-over, one-shot resume fill,
budgeted `/v1/context/prepare`, MCP/REST parity, and redaction across storage,
provider inputs, traces, and MCP results. Phase 14 is complete.

## After This Milestone

Only after this milestone is complete:

1. resume Codex dogfood automation using real semantic/execution-state memory;
2. prepare GitHub publication with honest feature claims;
3. plan the Hermes adapter as a thin host lifecycle bridge;
4. plan other runtime adapters.
