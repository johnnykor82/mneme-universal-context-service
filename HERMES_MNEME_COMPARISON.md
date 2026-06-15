# Hermes-Mneme vs Mneme Universal Context Service

Date: 2026-06-15
Status: post-Phase-14C parity completion

## Executive Summary

This document started as a pre-Phase-14 parity audit. At that point the
universal service was not functionally equivalent to `hermes-mneme`.

This is not because the product direction is impossible. It is because the
implementation deliberately started with the portable substrate: REST contract,
SQLite event store, idempotent ingestion, redaction, audit/traces, MCP read
tools, and Codex dogfood connectivity.

`hermes-mneme` is already a Hermes-native context engine. The older path owned a
hot path inside Hermes `compress()`. The newer local `_hermes-mneme-native`
copy uses native context-engine hooks when available: `on_turn_complete()` for
post-turn ingestion and `prepare_request_messages()` for request-only prompt
assembly, while keeping `compress()` as a legacy fallback. In both paths the
Mneme core ingests turns, updates execution state, embeds events, detects topic
drift, retrieves semantically, scores by intent/recency/dependency/type,
optionally reranks, enriches state with an LLM, and returns model-bound context.

Phase 14C has now closed the remaining runtime-neutral original-core gaps that
were safe to port without host-specific adapter work. Universal Mneme now has
the provider/config surface, required-embedding quality mode, hybrid/global
retrieval, model-change reindex, execution state recovery, segmentation and
intent signals, router/reranker behavior, LLM enrichment fields, budgeted
context preparation with memory hint/goal trail/checkpoint blocks, and richer
REST/MCP tools.

The remaining major gap is integration depth, not the daemon/core pipeline:
Hermes still needs the upstream native context-engine hook PR before Mneme
should be wired as a clean host adapter. Codex remains tools-only unless Codex
exposes a real host lifecycle hook for prompt/context insertion.

## Post-Phase-14C Status

| Area | Universal service after Phase 14C | Residual gap |
|---|---|---|
| REST/MCP substrate | Implemented and stronger than the old plugin path for schema versioning, redaction, audit, memory-read traces, costs, export/delete, and MCP/REST parity. | None for the v0 substrate. |
| Provider configuration | Implemented with `mneme.toml`, env, CLI, provider summaries, budget/segmentation/retrieval/enrichment/memory knobs, and secret-safe output. | Future host adapters may map their own env names to Mneme settings. |
| Embeddings and hybrid retrieval | Implemented provider abstraction, required-embedding mode, SQLite embedding rows, Python cosine fallback, global/session/lineage search, model-change reindex, configurable tool-output compression, degraded fallback, and cost counters. | `sqlite_vec` remains optional/documented; it is not installed in this local environment. |
| Execution state and goal history | Implemented deterministic state updates, persisted state, append-only history, state recovery, segment id, enrichment fields, decision rationale, REST/MCP tools, and export/delete coverage. | Host adapters still need to supply high-quality lifecycle metadata. |
| Segmentation and drift | Implemented continuation/switch/new-task/clarification classification, entity contradiction, question-about-output, embedding-drift rollover, centroid window, drift traces, fresh/resume classification, lineage, and one-shot resume fill. | Ranking calibration can improve with more dogfood data. |
| Typed graph and dependency scoring | Implemented typed graph edges, graph expansion, dependency candidates, and retrieval bonuses. | None blocking original-core parity. |
| Budgeted context assembly | Implemented request-only execution-state compression, memory access hint, goal trail, checkpoint hint, retrieved evidence with event ids, global candidates, protected tail, headroom, collision handling, and adapter metadata. | Automatic insertion still requires a host lifecycle hook. |
| Reranker | Implemented optional provider with Jina/Cohere score-list parsing, `reranker_top_k`, degraded fallback, traces, and cost counters. | Real-provider smoke should be re-run before each publication candidate. |
| LLM enrichment | Implemented optional OpenAI-compatible JSON enrichment for `intent_label`, `topic_tags`, decisions with rationale, `decision_summary`, active entities, and open loops. JSON recovery handles fenced/prose/truncated responses. | Current local dogfood daemon has no LLM provider configured, so real LLM smoke remains a publication gate if LLM docs claim live-provider readiness. |
| Acceptance evidence | Full local suite and parity acceptance pass with fake providers; dogfood daemon confirms required embeddings plus real embedding/reranker calls. | Second-machine GitHub install rehearsal still pending. |
| Hermes integration depth | Host adapter contract is documented and matches the intended native Hermes hook shape. | Implementation is intentionally deferred until upstream Hermes context-engine hooks are accepted; no compaction-based bridge should be built now. |

## Residual Work While Hermes PR Is Pending

Safe work that does not create duplicate Hermes integration effort:

1. Publish Mneme and `adapters/codex` to GitHub, then rehearse a second-machine
   install as a new user flow.
2. Keep real-provider smoke checks for embeddings/reranker, and add an LLM
   enrichment smoke only when a local LLM provider is configured.
3. Optionally add and test `sqlite_vec` acceleration in an environment where
   the package is installed, while keeping Python cosine fallback portable.
4. Keep Codex docs honest that MCP is tools-only and automatic prompt insertion
   needs a real host lifecycle hook.

## Historical Pre-Phase-14 Comparison Table

The table below preserves the original pre-Phase-14 audit context. It explains
why the parity recovery milestone was created, but many "Universal service now"
entries are no longer current after Phase 14. Use the post-Phase-14 status
section above for the current project state.

| Area | `hermes-mneme` | Universal service now | Gap |
|---|---|---|---|
| Product shape | Hermes context-engine plugin loaded into Hermes runtime. | Runtime-neutral REST daemon plus MCP server. | Intentional architecture change. |
| Integration depth | Deep `CONTEXT_ENGINE`; newer native path uses `on_turn_complete()` plus request-only `prepare_request_messages()`, with `compress()` as legacy fallback. | `TOOLS_ONLY` for Codex/MCP unless a host adapter calls `/v1/context/prepare`. | Codex cannot get automatic prompt replacement through MCP alone. |
| Data ingestion | Automatic through native post-turn hook or legacy `compress()` path. | Explicit REST ingestion; Codex path is offline/reference `mneme codex-ingest`. | Needs real adapter ingestion lane. |
| Storage | SQLite event store plus sessions, lineage, execution state, state history, embedding index, graph tables. | SQLite sessions, events, turns, traces, audit records, synthetic segments. | New store is cleaner contract-wise but lacks embedding/state/lineage tables. |
| Idempotency | Deterministic event ids and `INSERT OR IGNORE` on re-ingest. | Immutable event hashes, duplicate/conflict handling. | Universal service is stronger at contract-level idempotency. |
| Semantic search | Yes. Jina/OpenAI-compatible embeddings, `sqlite-vec` KNN, Python cosine fallback. | No. Current search is keyword-term scoring plus recency ordering. | Major missing feature. |
| Embedding provider | Configured in plugin config: provider/model/endpoint/API key. Defaults to local Jina-compatible endpoint. | Not implemented. Capabilities report `supports_embeddings=false`. | Major missing feature. |
| Embedding batching | Yes. Batches embeddings and can run embedding work in a background executor. | No embedding path. | Missing. |
| Embedding outage behavior | Circuit breaker; events still stored; retrieval degrades. | No embedding provider to fail. | Must port degraded hybrid behavior later. |
| Tool-output embedding compression | Yes. Head/tail summary for embedding only; raw content stays in DB. | No embedding compression. | Missing. |
| Reranking | Optional second-stage reranker via Jina/BGE/Cohere-like endpoints. | Not implemented. Capabilities report `supports_reranking=false`. | Missing. |
| LLM enrichment | Optional background LLM enrichment for intent labels, topic tags, decisions, state. | Not implemented. Capabilities report `supports_llm_enrichment=false`. | Missing. |
| Provider config | `HERMES_CTX_*` env vars plus plugin-local `config.yaml`. | Only daemon/MCP connection settings and basic limits. | Needs `mneme.toml`/env config layer before providers. |
| Execution state | Maintains goal, current step, open loops, last tool, decision stack, active entities, enrichment. | No first-class execution state store yet beyond generic events/turns/traces. | Major missing feature. |
| State history | Append-only state history used for goal trail/recovery. | No goal/state history endpoint yet. | Missing. |
| Intent classifier | Deterministic classifier: continuation/switch/new task/clarification. Uses explicit phrases, entity contradiction, embedding drift, question-about-output. | No intent classifier. | Missing. |
| Segmentation | Embedding-drift session segmenter with centroid cache and hard switch triggers. | Segment record currently created from turn completion as one synthetic session segment. | Major missing feature. |
| Retrieval routing | Builds query from execution state + current message; selects mode and scoring weights. | Query is either explicit or derived from request messages; no intent-aware routing. | Missing. |
| Scoring logic | Weighted similarity, recency, dependency, and type scores. | Term-match count plus created-at ordering. | Major missing feature. |
| Execution graph | Tracks tool_call -> tool_output -> decision edges; used by dependency propagation and expand tools. | Parent/child expansion through `parent_event_ids`; no typed graph table. | Partial/shallower. |
| Prompt assembly | Token-budgeted prompt builder with memory hint, goal trail, execution state, retrieved context, protected tail, collision resolution. | `/context/prepare` inserts a simple `[MNEME RETRIEVED EVIDENCE]` message. | Major missing feature. |
| Pass-through logic | If prompt is under budget, returns original messages after ingest/index; forces assembly on resume. | `/context/prepare` can return `changed=false` under budget, but there is no host-owned hot path except future adapters. | Partially modeled, not deeply integrated. |
| Resume/restart behavior | Complex session drift, lineage, reassign, resume context-fill, cold-start recovery; Hermes-specific session-id discovery is separate from the underlying memory semantics. | Idempotent REST sessions/events; no runtime-neutral drift/carry-over semantics yet. | Missing for all deep adapters, not just Hermes. |
| Agent memory tools | `context_search`, `fetch_event`, `expand_context`, `get_execution_state`, `list_segments`, `get_goal_history`, `recall_recent`. | MCP exposes `context_search`, `fetch_event`, `expand_context`, `recall_recent`, `list_segments`, `explain_context`, `mneme_cost_report`. | Different but overlapping. Missing execution state and goal history; new service adds trace/cost tools. |
| Audit of memory reads | Tool results have estimated tokens, but no v0 REST/MCP audit contract. | Durable audit records, `MEMORY_READ` events, memory-read traces, MCP/REST parity tests. | Universal service is stronger here. |
| Privacy/redaction | Prototype docs mention local plugin behavior; not the core contract focus. | Recursive redaction before storage/search/traces/errors; tested privacy behavior. | Universal service is stronger here. |
| API surface | Hermes plugin API, native tool schemas. | Stable REST `/v1` plus MCP stdio server and contract docs. | Universal service is stronger for external adapters. |
| Observability | Per-turn JSONL trace and in-memory metrics. | REST traces, audit records, cost report endpoint. | Different; universal service has contract traces but less retrieval detail. |
| Test posture | Unit/integration/diagnostic tests for classifier, embedding batch, store, lineage/state bugs. | Contract tests for REST, MCP parity, audit/privacy, Codex ingest. | Different focus; new service lacks quality/retrieval tests. |

## Historical Functional Parity Assessment

This section also reflects the pre-Phase-14 audit baseline.

| Category | Status |
|---|---|
| Universal REST/MCP substrate | New service ahead. |
| Safety, redaction, audit contract | New service ahead. |
| Codex MCP visibility | New service ahead. |
| Automatic context-engine behavior | `hermes-mneme` ahead. |
| Semantic retrieval quality | `hermes-mneme` ahead. |
| Execution state and goal tracking | `hermes-mneme` ahead. |
| Segmentation/classification/routing | `hermes-mneme` ahead. |
| Provider config and optional quality stack | `hermes-mneme` ahead. |

## Product Direction Read

The project is not going in the wrong direction if the goal is a universal
service that other runtimes can integrate. The substrate work was necessary:
without REST/MCP contracts, audit, redaction, idempotent ingestion, and adapter
boundaries, the `hermes-mneme` logic would stay trapped inside one runtime.

But the project is not yet a real replacement for `hermes-mneme`.

The next technical direction should change from "Codex dogfood polish" to
"port the Hermes-Mneme quality pipeline into the universal daemon in safe,
provider-configured phases." Codex dogfood should remain useful, but it should
dogfood the same retrieval pipeline that will later power Hermes.

## Recommended Reordered Roadmap

1. **Provider configuration surface**
   - Add config file/env precedence.
   - Keep minimal mode provider-free.
   - Add explicit embedding/reranker/enricher provider settings without making
     any provider calls yet.

2. **Embedding index and hybrid retrieval**
   - Add event embedding jobs, embedding cache/index tables, provider circuit
     breaker, and keyword fallback.
   - Add semantic search tests and degraded-mode tests.

3. **Execution state and goal history**
   - Add first-class execution state/state history schemas and endpoints.
   - Add `get_execution_state` and `get_goal_history` to MCP or equivalent
     v0/v1 tool names.

4. **Segmentation and intent routing**
   - Port deterministic classifier and embedding-drift segmenter.
   - Port runtime-neutral session/topic drift semantics: explicit switch,
     semantic drift, resume/fresh-session classification, lineage/carry-over,
     and first-turn resume context fill.
   - Replace basic `KEYWORD_RECENCY` traces with strategy-level traces:
     semantic, keyword, recency, dependency, rerank.

5. **Prompt/context assembly parity**
   - Upgrade `/v1/context/prepare` from a simple evidence insertion to a real
     budgeted assembly pipeline with protected tail, execution state, retrieved
     evidence, and collision resolution.

6. **Optional reranker and LLM enrichment**
   - Implement after provider config, redaction, and cost reporting are ready.
   - Keep failures non-fatal and visible in traces/cost reports.

7. **Codex dogfood on real retrieval**
   - Continue using MCP tools, but backed by semantic retrieval and execution
     state.
   - Keep documentation honest that Codex remains `TOOLS_ONLY` without a model
     request hook.

8. **Hermes adapter**
   - Once the daemon has retrieval/assembly parity, build the Hermes host
     adapter as a thin lifecycle bridge rather than copying the full old plugin.

## Current Plan Adjustment

The earlier recommendation to pause publication until parity recovery is now
satisfied at the daemon/core level. The next safe focus is publication and
second-machine installation rehearsal, while Hermes adapter implementation stays
deferred until native host hooks are accepted upstream.
