# Mneme Universal Context Service - Standalone Specification

Status: Final v0.7.5 - Approved for v0 implementation
Date: 2026-06-21
Owner: Ivan Konstantinov
Scope: product, architecture, protocol, security, operations, testing, and acceptance requirements for Mneme core
Approval: Approved by Ivan Konstantinov on 2026-06-21 after final architecture review.

## 0. How To Read This Document

This is the single-file reviewer specification for Mneme Universal Context
Service. It is intended to be sent without attaching the rest of the repository
documentation.

This document is normative for the next compliance pass. The current alpha code
may not yet satisfy every MUST in this file. Reviewers have approved this
specification as the v0 target; the next step is to execute the implementation
gap plan and update the plugin/core until code, tests, and docs match this
accepted specification.

Requirement language:

- MUST: required for v0 compliance.
- SHOULD: expected unless a documented adapter/runtime constraint prevents it.
- MAY: optional behavior.
- CURRENT GAP: known alpha implementation gap to plan after approval.
- FUTURE: intentionally out of v0.

This document supersedes older review-index documents. Other repository docs
may remain useful implementation notes, but reviewers should treat this file as
the complete target specification.

v0.4 review response summary:

- defines local owner-token versus optional static scoped-token behavior without
  turning v0 into enterprise RBAC;
- removes automatic freshness magic and makes freshness adapter/source supplied;
- makes SQLite the default ACID blob store for v0 and demotes filesystem blobs
  to a future/optional driver;
- restores trace/cost endpoints and defines `mneme.audit_record.v0`;
- adds request/response examples for execution-state and segment endpoints;
- replaces SQLite writer backoff with a serialized writer requirement;
- tightens tokenizer, prompt-injection, MCP session-default, and OpenAPI source
  of truth rules.

v0.5 review response summary:

- fills remaining REST request/response schema gaps for session start/export,
  execution-state update, segment start/close/list, blob GC, and reindex jobs;
- makes error examples match the uniform `{ok:false,error:{...},warnings:[]}`
  envelope;
- defines segment/list scoping, retention cutoff semantics, blob GC/reindex
  authorization, idempotency coverage, and multipart event ingest rules;
- changes context packing so unused prompt budget cascades to tail/evidence
  before headroom, while headroom remains a hard reserve;
- lowers default SQLite blob limits and requires batch-first ingestion,
  single-range blob reads, and SQLite version consistency checks;
- keeps MCP v0 read-oriented and keeps `/v1/readiness/session` as the hard
  dependency gate, while documenting the review rationale and future write
  path explicitly.

v0.6 review response summary:

- defines the missing `mneme.segment.v0`, segment event summary, reindex job
  status polling, job status enums, session-start required fields, and
  segment-close outcome values;
- replaces inline base64 session export as the portable blob path with
  metadata-only JSON plus a streaming `multipart_bundle` export format;
- lowers the default SQLite blob limit to 2 MiB, defines
  `max_export_blob_inline_bytes`, and exposes export/blob limits through
  capabilities;
- clarifies context packing: headroom is a minimum hard reserve, unused prompt
  budget becomes unused slack rather than being consumed as extra headroom;
- changes oversized latest-message and deprecated-field conflicts to
  best-effort normalization/truncation by default, reserving `422` for strict
  callers or impossible minimum authority/user payloads;
- adds foreground-write priority over background jobs, automatic retention
  sweeps, embedding retry/backoff, provider-unavailable reindex policy, metrics
  and startup integrity requirements;
- moves alpha readiness fallback out of the normative API section into the
  compatibility gap notes and tightens MCP default-session injection mechanics.

v0.7 review response summary:

- protects the current latest user request from best-effort truncation; only
  historical tail messages may be truncated by default;
- changes privacy delete semantics to preserve anonymized forensic audit
  anchors for security-sensitive audit records while deleting/redacting session
  content;
- prevents retention sweeps from deleting active-session history unless an
  explicit force flag is supplied;
- replaces the primary portable blob export format with a streaming
  `tar_bundle` and demotes `multipart/mixed` to a non-required compatibility
  option;
- adds reindex cancellation, provider throttling/circuit-breaker expectations,
  provider-wait expiry, and background micro-transaction/yield rules;
- limits multipart ingest total blob bytes per request/transaction to avoid
  SQLite WAL spikes;
- defines remaining enums and edge cases for session resolution, segment
  creation, event importance, metrics formats, blob omission reasons, automatic
  cleanup principals, and MCP stale default sessions;
- demotes `COMPACTION_OWNER` to FUTURE until a compaction/summarization API is
  explicitly specified.

v0.7.1 review response summary:

- defines every schema that was still listed without a standalone shape:
  `mneme.context_prepare_request.v0`, `mneme.trace.v0`,
  `mneme.cost_report.v0`, `mneme.state_history_entry.v0`, and
  `mneme.session_lineage.v0`;
- adds explicit retention-cleanup request/response contracts, force-active
  cleanup race behavior, and idempotent reindex-cancel semantics;
- makes graph traversal scoring fully normative instead of "reference"
  behavior, including `importance_depth_decay`;
- adds `AUTH_FAILURE` to the audit action enum and clarifies system/audit tool
  naming, forensic anchor hashing, MCP-only `DEFAULT_SESSION_STALE`, and
  `session_resolution.source`;
- tightens operational validation for session ids, multipart blob/transaction
  limits, budget split keys, unknown export formats, idempotency-key retention,
  and context prepare requests without a user message.

v0.7.2 Hermes parity response summary:

- clarifies that runtime-neutral intent classification, automatic segmentation,
  and retrieval query construction are Mneme core quality responsibilities for
  `CONTEXT_ENGINE` paths, while host adapters may supply stronger explicit
  signals;
- defines deterministic Hermes-parity intent values and priority ordering for
  explicit switch, entity contradiction, embedding drift, clarification, and
  continuation cases;
- specifies automatic segmentation triggers, centroid-based embedding drift,
  adapter-supplied tool-domain shift signals, and `SEGMENT_DRIFT` tracing;
- adds selective indexing compression for long tool outputs while preserving
  raw/fetchable event content;
- clarifies memory-tool feedback continuity: audited direct memory reads create
  `MEMORY_READ` events, update state summaries, and create graph evidence
  without making MCP a model-callable write surface.

v0.7.3 Hermes parity determinism response summary:

- makes the Hermes-parity intelligence layer reproducible by adding explicit
  routing weights, scoring formula, score-breakdown schema, delta extraction
  schema, deterministic excerpt behavior, and memory-read graph edge semantics;
- defines default switch/contradiction terms near the algorithm, not only in
  config, so implementers do not need to infer required behavior from examples;
- defines the segmentation drift score components and adapter tool-domain
  signal guidance while keeping provider failures non-blocking;
- records product adoption gaps such as MCP writes, Hermes legacy bridge, and
  compaction owner as FUTURE rather than silently expanding v0.

v0.7.4 algorithmic hardening response summary:

- defines canonical JSON hashing for execution-state history so `state_hash`
  and `previous_state_hash` are reproducible across implementations;
- adds hard limits for graph traversal, writer queue depth, multipart write
  duration, and redaction time to avoid hidden OOM/latency failure modes;
- clarifies that `require_evidence=false` readiness is cheap and provider-free,
  while evidence readiness uses existing indexes and explicit provider-call
  policy;
- replaces model-token-dependent local contradiction windows with deterministic
  whitespace-word windows;
- tightens retry-safe segment creation, MCP versioning guidance, auth-failure
  principal semantics, context-prepare compression reporting, and multipart
  atomicity tests.

v0.7.5 final polish response summary:

- clarifies adapter recovery guidance for `422 REDACTION_TIMEOUT`;
- states that readiness provider calls share normal provider rate limits and
  circuit breakers;
- warns adapters and storage implementations to preserve array insertion order
  for state-hash fields rather than deriving arrays from unordered maps.

## 1. Executive Summary

Mneme is a local-first, vendor-neutral context memory service for long-running,
tool-using agents. It stores normalized agent events, builds searchable memory,
tracks execution state, and prepares bounded request-only context for host
runtimes that expose a pre-model-call lifecycle hook.

Mneme exists to reduce context loss, destructive compaction, and long-session
amnesia in coding and research agents without rewriting the canonical host
transcript. Mneme does not claim to invisibly replace prompts in runtimes that
do not provide prompt assembly hooks.

The product has three surfaces:

1. REST lifecycle/control plane for sessions, event ingestion, context
   preparation, traces, costs, blobs, export, and deletion.
2. MCP read-oriented memory tools for agents that can call tools but cannot
   delegate prompt assembly.
3. Host Adapter Contract for runtimes that want Mneme-prepared context to
   become the actual model input.

## 2. Product Boundary

Mneme is:

- a local daemon with a REST API under `/v1`;
- a local MCP server that proxies audited memory tools to REST;
- a normalized event store for agent history;
- a retrieval and context preparation engine;
- a host-runtime-neutral core intended to be packaged separately from adapters;
- a privacy-conscious local memory substrate with optional provider-backed
  quality layers.

Mneme is not:

- a hosted SaaS product in v0;
- an enterprise multi-tenant auth system in v0;
- a general chatbot memory product;
- a hidden prompt injector for closed runtimes;
- an autonomous code/file/database modifier;
- a guarantee that an LLM will safely ignore malicious retrieved text;
- a replacement for runtime-owned system/developer instructions.

## 3. Personas And Use Cases

Personas:

- Agent runtime authors building native context engines.
- Adapter authors integrating Mneme with Codex, Hermes, LangGraph, OpenAI
  Agents SDK, Claude Code style tools, or internal agent frameworks.
- Developers running long-lived local coding agents.
- Teams evaluating auditable memory and context preparation for private code.
- Reviewers verifying whether implementation matches protocol and business
  requirements.

Primary use cases:

- Preserve raw agent history across compaction and restarts.
- Recover prior decisions, errors, tool outputs, and task state.
- Search semantic or lexical memory evidence from an agent.
- Assemble a request-only prompt supplement before a model call when the host
  permits it.
- Audit what memory was read and why it was included.
- Export or delete a local session and its derived artifacts.

## 4. Business Requirements

BR-1: Preserve structured agent history.

- Mneme MUST store normalized session, turn, event, trace, and state records.
- Mneme MUST preserve raw content after configured redaction.
- Optional indexes MUST NOT become the only canonical memory source.

BR-2: Keep context preparation request-only.

- Mneme MUST NOT rewrite canonical host transcripts.
- Mneme-prepared context applies to one model request unless the host explicitly
  records it as a separate memory-read/audit event.

BR-3: Support explicit memory inspection.

- Agents MUST be able to search, fetch, expand, recall, and explain memory
  evidence through REST and MCP tools.
- Results MUST preserve provenance: event id, session id, timestamp, source
  references, and selection reason.

BR-4: Stay local-first.

- A single-user local daemon with SQLite MUST be supported.
- No hidden telemetry or unconfigured provider calls are allowed.

BR-5: Support optional quality layers.

- Embeddings, reranking, and LLM enrichment MAY improve retrieval/state quality.
- Provider use MUST be explicit, metered, and visible in capabilities and costs.

BR-6: Be honest about integration depth.

- MCP-only clients are `TOOLS_ONLY`.
- Automatic prompt/context replacement requires a host lifecycle hook before
  the model call.

BR-7: Keep core and adapters separable.

- The Mneme engine/core package MUST be publishable without Codex, Hermes, or
  other host-specific adapter code.
- Host adapters SHOULD be separate repositories/packages.

BR-8: Make reviewer and implementation traceability possible.

- Requirements MUST map to APIs, code areas, tests, and known gaps.
- A future code review MUST be able to determine whether the implementation
  satisfies this specification.

## 5. Integration Depth Model

Every adapter MUST declare the deepest integration level it actually provides.
User-facing documentation MUST NOT claim a deeper level.

| Level | Name | Host capability | Mneme behavior |
|---:|---|---|---|
| 0 | `TOOLS_ONLY` | Host can expose REST/MCP tools to the agent. | Agent can call memory tools. No automatic prompt replacement. |
| 1 | `EVENT_INGEST` | Host can send sessions, events, turns, usage, and tool lifecycle data. | Mneme stores and indexes history. |
| 2 | `PREPARE_INPUT` | Host can augment or filter run input before a model call, with limited prompt authority. | Mneme can prepare request context where the host permits it. |
| 3 | `CONTEXT_ENGINE` | Host calls Mneme immediately before prompt/model request submission and sends returned messages. | Mneme acts as active request-only context engine. |
| 4 | `COMPACTION_OWNER` | FUTURE: host delegates explicit/overflow compaction. | Not a v0 compliance level until a compaction/summarization API is specified. |
| 5 | `FULL_RUNTIME` | Mneme-owned or adapter-owned runner controls model invocation. | Mneme can enforce the full provider request policy. |

Codex status in v0:

- Codex/MCP is `TOOLS_ONLY` unless trusted local hooks/importers also ingest
  events through REST.
- Current public Codex command hooks do not provide a documented prompt
  replacement hook.
- Mneme MUST describe Codex as explicit memory tooling plus optional trusted
  ingestion hooks, not as automatic context replacement.

Hermes status in v0:

- Hermes is a deep integration target only after host lifecycle hooks equivalent
  to `prepare_model_request` are available and accepted.
- Until then, Hermes adapter work is deferred or must explicitly declare a
  lower integration depth.

### 5.1 Host Adapter Lifecycle Contract

Adapters at `EVENT_INGEST` depth or higher MUST map host lifecycle events to
Mneme calls. The names below are conceptual; host runtimes may expose different
native hook names.

| Hook | Required for | Mneme call | Purpose |
|---|---|---|---|
| `bootstrap_session` | `EVENT_INGEST+` | `POST /v1/sessions/start` | Create/resume session before events. |
| `ingest_events` | `EVENT_INGEST+` | `POST /v1/events` | Store user, assistant, tool, file, error, and decision events. |
| `prepare_model_request` | `CONTEXT_ENGINE+` | `POST /v1/context/prepare` | Prepare request-only model input immediately before provider call. |
| `after_model_response` | `EVENT_INGEST+` | `POST /v1/events` | Store assistant output, tool calls, tool outputs, and errors. |
| `complete_turn` | `EVENT_INGEST+` | `POST /v1/turns/complete` | Finalize status, usage, segment hints, and state updates. |
| `compact` | FUTURE `COMPACTION_OWNER+` | future compaction endpoint or adapter-local policy | Delegate explicit/overflow compaction. Not a v0 required hook. |
| `prepare_subagent_spawn` | optional | `POST /v1/sessions/start` plus lineage events | Link parent/child sessions and scoped context. |
| `on_subagent_ended` | optional | `POST /v1/events`, `POST /v1/turns/complete` | Finalize child outcome and parent-visible summary. |

Subagent lifecycle is optional in v0, but any adapter claiming subagent support
MUST test parent/child lineage, scope isolation, and child-summary behavior.

## 6. Architecture Overview

Core components:

| Component | Responsibility |
|---|---|
| REST daemon | Lifecycle, ingestion, context preparation, discovery, traces, cost reports, blobs, export/delete. |
| SQLite store | Sessions, events, turns, traces, audit records, blobs metadata, segments, embeddings, execution state, state history, lineage, graph edges. |
| Retrieval pipeline | Keyword, recency, optional embeddings, graph dependencies, optional reranker. |
| Context assembler | Budgeted request-only prompt construction with protected authority and evidence blocks. |
| MCP server | Read-oriented memory tools that proxy REST and preserve REST envelopes. |
| Host adapters | Runtime-specific lifecycle mapping and capability negotiation. |
| Provider clients | Optional OpenAI-compatible embeddings, reranking, and LLM enrichment clients. |
| Redaction engine | Secret and sensitive-metadata redaction before persistence/provider/log/tool output. |

Data flow:

1. Adapter starts or resumes a session through REST.
2. Adapter ingests normalized events through REST.
3. Optional providers derive embeddings/reranks/enrichment after redaction.
4. Agent or adapter reads memory through REST/MCP tools.
5. Deep adapters call `/v1/context/prepare` immediately before model request.
6. Host sends prepared request to the model if and only if host capability
   permits.
7. Mneme records traces, audit records, and cost counters.

## 7. Repository And Package Boundaries

Target publication boundary:

- `mneme-universal-context-service`: core daemon, REST/MCP server, storage,
  retrieval, context assembly, provider clients, generic tests, generic docs.
- `mneme-codex-adapter`: Codex-specific CLI, hooks, skills, setup, doctor,
  service management, and Codex docs.
- Future adapters: separate packages for Hermes, LangGraph, OpenAI Agents SDK,
  Claude Code style runtimes, etc.

The development checkout MAY temporarily contain adapter folders for dogfood,
but public core release artifacts MUST NOT require host-specific adapter files.

CURRENT GAP: if adapter code remains under `adapters/codex` in the core
checkout, the release plan must either move it to the adapter package or mark it
as development-only and exclude it from core distribution artifacts.

## 8. Configuration Model

Configuration precedence:

1. CLI flags for non-secret operational overrides.
2. Environment variables.
3. Explicit env file or token file with owner-only permissions.
4. TOML config file.
5. Defaults.

Secrets:

- Provider API keys MUST come from environment variables, an owner-only env
  file, OS keychain integration, or a future secret manager integration.
- Secrets MUST NOT be required in tracked TOML files.
- Secrets MUST NOT be passed on the command line in documented safe paths.

Required default config sections:

```toml
[daemon]
db_path = ".local/mneme.db"
host = "127.0.0.1"
port = 8765
insecure_dev = false
require_embeddings = false
strict_cost_mode = false
max_batch_events = 200
max_event_content_bytes = 1048576
max_blob_bytes = 2097152
max_session_id_length = 256
max_batch_total_blob_bytes = 20971520
max_multipart_metadata_overhead_bytes = 2097152
max_multipart_transaction_bytes = 23068672
max_multipart_transaction_ms = 2000
max_export_blob_inline_bytes = 0
max_export_session_memory_bytes = 33554432
idempotency_key_min_retention_seconds = 604800
max_writer_queue_depth = 1000
startup_integrity_check = true
metrics_enabled = true
metrics_format = "prometheus"

# Experimental filesystem blob driver only. The v0 compliant default stores
# server-owned blobs in SQLite BLOB rows and does not require blob_dir.
# blob_driver = "filesystem"
# blob_dir = ".local/mneme-blobs"
# trusted_adapter_paths = ["/repo/.mneme-trusted-blobs"]

[maintenance]
retention_sweep_interval_seconds = 3600
retention_sweep_on_startup = true
retention_sweep_on_session_close = true
retention_force_active_cleanup = false
vacuum_max_duration_ms = 500
checkpoint_max_pages = 1000

[maintenance.reindex]
enqueue_when_provider_unavailable = false
foreground_write_priority = true
max_job_events = 10000
max_events_per_transaction = 10
yield_between_transactions_ms = 50
provider_wait_timeout_seconds = 86400
provider_max_requests_per_minute = 60
provider_circuit_breaker_min_calls = 10
provider_circuit_breaker_failure_ratio = 0.5
provider_circuit_breaker_open_seconds = 60
provider_circuit_breaker_half_open_requests = 2
provider_recovery_ramp_initial_requests_per_minute = 10

[retrieval.graph]
importance_depth_decay = 0.5
max_traversal_steps = 1000
max_frontier_size = 500
max_branching_factor = 64

[retrieval.routing]
default_mode = "general"
explicit_switch_patterns = [
  "new topic", "switch to", "forget that", "instead",
  "let's move on", "different task", "change direction"
]
entity_contradiction_enabled = true
entity_negation_terms = ["not", "no", "without", "instead of", "remove", "delete"]
entity_replacement_terms = ["replace", "instead of", "use instead", "swap"]
question_about_output_enabled = true
delta_extraction_enabled = false

[retrieval.routing.weights.general]
semantic_similarity = 0.40
recency = 0.20
dependency = 0.30
type_weight = 0.10

[retrieval.routing.weights.reasoning]
semantic_similarity = 0.35
recency = 0.15
dependency = 0.40
type_weight = 0.10

[retrieval.routing.weights.factual]
semantic_similarity = 0.50
recency = 0.30
dependency = 0.10
type_weight = 0.10

[retrieval.routing.weights.debugging]
semantic_similarity = 0.30
recency = 0.40
dependency = 0.10
type_weight = 0.20

[segmentation]
enabled = true
drift_threshold = 0.35
min_centroid_events = 3
drift_weights = [0.4, 0.3, 0.3]
tool_domain_shift_enabled = true

[indexing]
tool_output_compress_threshold_tokens = 500
tool_output_summary_tokens = 100
max_redaction_time_ms = 250

[audit]
forensic_retention_days = 90
anonymize_deleted_session_audit = true

[auth]
token_env = "MNEME_AUTH_TOKEN"
token_file = null
project_isolation_key = null

[providers.embeddings]
enabled = false
provider = "openai_compatible"
model = "text-embedding-3-small"
base_url = "https://api.openai.com/v1"
api_key_env = "MNEME_EMBEDDING_API_KEY"
max_retries = 3
initial_backoff_ms = 250
max_backoff_ms = 5000

[providers.reranker]
enabled = false
provider = "jina"
model = "jina-reranker-v2-base-multilingual"
base_url = "https://api.jina.ai/v1"
api_key_env = "MNEME_RERANKER_API_KEY"
max_retries = 2
initial_backoff_ms = 250
max_backoff_ms = 5000

[providers.llm_enrichment]
enabled = false
provider = "openai_compatible"
model = "CONFIGURE_ME"
base_url = "https://api.openai.com/v1"
api_key_env = "MNEME_LLM_API_KEY"
max_retries = 2
initial_backoff_ms = 500
max_backoff_ms = 10000
```

Config validation rules:

- `daemon.max_session_id_length` MUST be between 1 and 256 inclusive; the
  default is 256.
- `daemon.max_multipart_transaction_bytes` MUST be at least
  `daemon.max_batch_total_blob_bytes +
  daemon.max_multipart_metadata_overhead_bytes`.
- `daemon.max_multipart_metadata_overhead_bytes` is a conservative bound for
  JSON event metadata, blob metadata rows, and savepoint bookkeeping in one
  multipart ingestion request. If the bound is exceeded, the request returns
  `413 PAYLOAD_TOO_LARGE` or `422 VALIDATION_ERROR` before storage writes.
- `daemon.idempotency_key_min_retention_seconds` MUST be positive. The
  reference default is seven days.
- `daemon.max_writer_queue_depth`,
  `daemon.max_multipart_transaction_ms`, and all graph traversal limits MUST be
  positive.
- `maintenance.reindex.provider_max_requests_per_minute`,
  `provider_circuit_breaker_min_calls`, `provider_circuit_breaker_open_seconds`,
  and `provider_circuit_breaker_half_open_requests` MUST be positive.
- `maintenance.reindex.provider_circuit_breaker_failure_ratio` MUST be in
  `(0, 1]`.
- `retrieval.graph.importance_depth_decay` MUST be in `(0, 1]`.
- `retrieval.routing.explicit_switch_patterns` MUST be non-empty when
  runtime-neutral routing is enabled.
- Each `retrieval.routing.weights.<mode>` table MUST contain non-negative
  `semantic_similarity`, `recency`, `dependency`, and `type_weight` values
  whose sum is `1.0 +/- 0.01`.
- `segmentation.drift_threshold` MUST be in `(0, 2]` for cosine-distance
  style embeddings.
- `segmentation.drift_weights` MUST contain exactly three non-negative values
  whose sum is positive.
- `indexing.tool_output_compress_threshold_tokens` and
  `indexing.tool_output_summary_tokens` MUST be positive, and the summary
  target MUST be lower than the compression threshold.
- Invalid config MUST fail startup in normal mode. Test-only overrides MUST be
  explicit and MUST advertise degraded or insecure capability flags.

## 9. Authentication And Authorization

Authentication requirements:

- The daemon MUST require authentication by default, including loopback.
- Supported v0 schemes:
  - bearer token from environment or token file;
  - Unix domain socket permissions;
  - explicit insecure development mode.
- Non-loopback binding MUST require explicit configuration and MUST refuse
  insecure development mode.

Unsafe token passing:

- Commands such as `mneme mcp --token "$MNEME_AUTH_TOKEN"` expose secrets in
  process arguments and MUST NOT be the recommended path.
- `--token` MAY remain temporarily as a legacy/development option, but safe docs
  and generated configs MUST use environment variables or `--token-file`.
- MCP server startup SHOULD use `MNEME_AUTH_TOKEN`, `MNEME_AUTH_TOKEN_FILE`, or
  an adapter-generated owner-only env file.

Insecure development mode:

- MUST be activated explicitly with `daemon.insecure_dev=true` or
  `--insecure-dev`.
- MUST bind only to loopback or an owner-only Unix socket.
- MUST advertise `auth_schemes=["INSECURE_DEV"]` in capabilities.
- MUST emit a startup warning.
- MUST be rejected for non-loopback hosts.
- SHOULD be refused for non-temporary/public data directories unless a second
  explicit override is supplied.

Project isolation:

- Every session MUST have `privacy.project_isolation_key`.
- v0 default auth is a local owner token with `all-projects` scope. This is a
  local single-user boundary, not enterprise RBAC.
- Project isolation keys are mandatory logical privacy tags for filtering,
  export, delete, retention, and accidental cross-project discovery prevention.
- Optional scoped tokens MAY be configured through a static owner-only token
  registry. They are for adapter/process least privilege, not multi-user auth.
- REST requests MUST derive an effective project scope from the authenticated
  principal, session metadata, and optional `X-Mneme-Project-Isolation-Key`.
- Cross-project search, fetch, export, delete, discovery, and blob reads MUST be
  forbidden unless the effective principal has `all-projects` or the matching
  project key.
- `GLOBAL` search means all sessions visible to the current principal, not all
  sessions in the daemon.

Token scope configuration:

```toml
[auth]
mode = "owner_token"
token_env = "MNEME_AUTH_TOKEN"
token_file = null

[[auth.static_tokens]]
name = "local-owner"
token_env = "MNEME_AUTH_TOKEN"
project_scopes = ["*"]
role = "OWNER"

[[auth.static_tokens]]
name = "codex-repo-a"
token_file = ".local/tokens/codex-repo-a.token"
project_scopes = ["repo-a"]
role = "ADAPTER"
```

If no `auth.static_tokens` are configured, the single configured bearer token
is treated as the local owner token with `project_scopes=["*"]`. Scoped-token
files MUST be owner-readable only. Dynamic token administration APIs, JWT
issuance, remote identity providers, and multi-user RBAC are FUTURE work.

REST clients MUST send the configured bearer token on authenticated endpoints,
including loopback calls. A successful MCP call does not imply that direct REST
will work without authentication: the MCP process may be proxying REST with
`MNEME_AUTH_TOKEN`, `MNEME_AUTH_TOKEN_FILE`, or another configured token source
that is not visible to an external REST caller.

Discovery leakage controls:

- `resolve_session` and `list_sessions` MUST filter by effective project scope.
- Discovery results MUST be bounded, redacted, and audited.
- Candidate sessions in `NOT_FOUND` errors MUST be limited to at most 5 entries.
- Candidate fields MUST exclude raw `cwd` unless it is within the authorized
  project scope and redacted according to metadata rules.

## 10. Provider Modes And Cost Modes

`cost_mode` is a policy intent, not a guarantee that providers are available.
The server MUST resolve requested mode against capabilities and health.

Modes:

| Mode | Required behavior | Provider calls |
|---|---|---|
| `MINIMAL` | Keyword/recency retrieval, no external calls. | None. |
| `STANDARD` | Hybrid retrieval if embeddings are available; otherwise keyword/recency with warning unless strict requirements apply. | Embeddings MAY be used. |
| `QUALITY` | Best available retrieval: embeddings, graph dependencies, reranking, and LLM enrichment where configured. | Embeddings/reranker/enrichment MAY be used. |

Strictness rules:

- `daemon.require_embeddings=true` means the daemon MUST fail startup or report
  not-ready if embeddings are enabled but unavailable.
- `strict_cost_mode=true` means a request for `QUALITY` MUST fail with
  `503 PROVIDER_UNAVAILABLE` if required providers for that profile are absent.
- Without strict mode, the server MAY downgrade and MUST return
  `COST_MODE_DOWNGRADED` with missing feature details.
- If a provider is `enabled=true` but requires an API key and no key is
  available, startup MUST fail unless the provider explicitly supports anonymous
  local operation.
- Provider failures after startup MUST NOT lose ingested events. They MUST set
  degraded flags, trace fallbacks, and cost failure counters.

Capabilities MUST expose:

- supported cost modes;
- default cost mode;
- active provider status: configured, enabled, available, model id, base URL
  host redaction, and last health;
- strict mode settings;
- `requires_embeddings`, `supports_reranking`, `supports_llm_enrichment`;
- tokenizer/estimation metadata;
- vector acceleration status.

## 11. Tokenization And Budget Accounting

Token estimates are operational estimates, not provider billing truth.

The server MUST expose:

- `tokenizer_id`;
- `token_estimate_quality`: `EXACT`, `MODEL_APPROXIMATE`, or `CHAR_APPROXIMATE`;
- `tokenizer_source`: e.g. `adapter_supplied`, `tiktoken`, `provider_default`,
  or `char_4_fallback`.

Adapters SHOULD supply exact token counts when the host provider exposes them.
If unavailable, Mneme MAY use a deterministic approximate tokenizer. Traces and
cost reports MUST label estimates so reviewers do not mistake them for exact
provider accounting.

Tokenizer safety:

- `CHAR_APPROXIMATE` / `char_4_fallback` is allowed for liveness checks,
  minimal-mode local search, and non-model-bound diagnostics.
- `STANDARD` and `QUALITY` `/v1/context/prepare` responses intended for a real
  model request MUST use `EXACT` or `MODEL_APPROXIMATE` tokenization, or require
  adapter-supplied counts plus conservative safety margin.
- If only `CHAR_APPROXIMATE` is available for a model-bound prepare request,
  the server MUST either return `422 VALIDATION_ERROR` or downgrade to
  `MINIMAL`/`changed=false` with a warning. It MUST NOT risk sending an
  over-budget provider request while claiming `STANDARD` or `QUALITY`.

`provider_prompt_tokens_without_mneme_estimate`:

- MUST be labeled as counterfactual estimate.
- MUST include methodology in the cost report:
  - `DIRECT_FULL_HISTORY`;
  - `DIRECT_ACTIVE_WINDOW`;
  - `ADAPTER_REPORTED_BASELINE`;
  - `UNKNOWN`.
- MUST NOT be used alone as proof of cost savings without a benchmark baseline.

## 12. Data Model

All persisted objects MUST include `schema_version`.

Core schemas:

- `mneme.session.v0`
- `mneme.session_start.v0`
- `mneme.session_export.v0`
- `mneme.session_export_manifest.v0`
- `mneme.event_batch.v0`
- `mneme.event.v0`
- `mneme.event_summary.v0`
- `mneme.turn.v0`
- `mneme.message.v0`
- `mneme.context_prepare_request.v0`
- `mneme.context_prepare_response.v0`
- `mneme.retention_cleanup_request.v0`
- `mneme.retention_cleanup_result.v0`
- `mneme.trace.v0`
- `mneme.audit_record.v0`
- `mneme.cost_report.v0`
- `mneme.execution_state.v0`
- `mneme.execution_state_update.v0`
- `mneme.execution_state_update_result.v0`
- `mneme.state_history_entry.v0`
- `mneme.session_lineage.v0`
- `mneme.segment.v0`
- `mneme.segment_start.v0`
- `mneme.segment_close.v0`
- `mneme.graph_edge.v0`
- `mneme.blob.v0`
- `mneme.reindex_job.v0`

`session_id` is an opaque non-empty string. Mneme MUST NOT infer semantics from
whether it looks like `session-123`, a UUID-like Codex id such as
`019edb86-1d22-78a3-b9e4-e6121c294056`, or another host-generated value.
Adapters SHOULD supply a stable `session_id`; if omitted on session start, the
daemon MAY generate one, but retry-safe adapters MUST then use an
`Idempotency-Key`.

`session_id` validation:

- length MUST be 1..`daemon.max_session_id_length` characters after URL
  decoding;
- values MUST NOT contain NUL, ASCII control characters, `/`, `?`, or `#`;
- values are case-sensitive and otherwise opaque;
- invalid ids return `422 VALIDATION_ERROR` before lookup, not `404 NOT_FOUND`.

### 12.1 Session

```json
{
  "schema_version": "mneme.session.v0",
  "session_id": "session-123",
  "agent_id": "codex",
  "runtime": "CODEX",
  "project_id": "repo-name",
  "model": "model-name",
  "tokenizer": "provider-default",
  "context_window_tokens": 200000,
  "cost_mode": "STANDARD",
  "status": "ACTIVE",
  "started_at": "2026-06-21T12:00:00Z",
  "ended_at": null,
  "metadata": {
    "cwd": "/repo",
    "thread_id": "thread-123",
    "adapter_version": "0.1.0"
  },
  "privacy": {
    "project_isolation_key": "repo-name",
    "retention_days": 30,
    "redaction_profile": "DEFAULT",
    "redaction_policy": "IRREVERSIBLE"
  }
}
```

Session status values:

- `ACTIVE`
- `ENDED`
- `DELETED`

`PAUSED` is intentionally omitted from v0 because no pause/resume transition is
defined. It may be added later with an explicit endpoint and lifecycle rules.

### 12.2 Message

```json
{
  "schema_version": "mneme.message.v0",
  "role": "USER",
  "content": [
    {
      "type": "text",
      "text": "Analyze this file."
    },
    {
      "type": "image_ref",
      "uri": "mneme-blob://blob-123",
      "media_type": "image/png"
    }
  ],
  "name": null,
  "tool_call_id": null,
  "tool_calls": [],
  "metadata": {
    "provider_role": "user"
  }
}
```

`content` MAY be a string or an array of typed parts. v0 typed part values:

- `text`
- `json`
- `image_ref`
- `bytes_ref`
- `tool_call`
- `tool_result`

Adapters SHOULD use a string unless multipart content is required.

### 12.3 Event

```json
{
  "schema_version": "mneme.event.v0",
  "event_id": "event-001",
  "event_sequence": 42,
  "session_id": "session-123",
  "turn_id": "turn-001",
  "agent_id": "codex",
  "runtime": "CODEX",
  "role": "TOOL",
  "type": "TOOL_OUTPUT",
  "timestamp": "2026-06-21T12:00:00Z",
  "content": {
    "format": "TEXT",
    "text": "pytest failed with AssertionError",
    "hash": "sha256:example",
    "size_bytes": 35
  },
  "tool": {
    "name": "exec_command",
    "call_id": "tool-call-789",
    "input_summary": "pytest tests/test_context.py"
  },
  "parent_event_ids": ["event-000"],
  "source_refs": [],
  "token_estimate": 123,
  "importance": "NORMAL",
  "privacy": {
    "classification": "PROJECT",
    "redaction_applied": false,
    "source_trust": "UNTRUSTED_TOOL_OUTPUT"
  },
  "ingestion": {
    "status": "STORED",
    "degraded": false,
    "embedding_status": "PENDING"
  },
  "indexing": {
    "embedding_model_id": null,
    "compression_applied": false,
    "index_text_token_estimate": 35,
    "summary": null
  },
  "metadata": {
    "cwd": "/repo",
    "exit_code": 1
  },
  "error": null
}
```

Event type values:

- `SESSION_START`
- `TURN_START`
- `USER_MESSAGE`
- `SYSTEM_MESSAGE`
- `ASSISTANT_MESSAGE`
- `ASSISTANT_MESSAGE_CHUNK`
- `TOOL_CALL`
- `TOOL_OUTPUT`
- `COMMAND`
- `COMMAND_OUTPUT`
- `FILE_READ`
- `FILE_CHANGE`
- `DECISION`
- `ERROR`
- `STATE`
- `MEMORY_READ`
- `TURN_COMPLETE`

`parent_event_ids` length MUST default to a maximum of 64. Larger arrays MUST
return `422 VALIDATION_ERROR` unless the daemon advertises a higher limit.

`importance` values:

- `CRITICAL`
- `HIGH`
- `NORMAL`
- `LOW`

Adapters MAY set `importance` during ingestion when the host has explicit
importance signals. If omitted, Mneme MUST default to `NORMAL`. Mneme MAY apply
deterministic local defaults by event type only when documented and stable; it
MUST NOT infer `CRITICAL` from untrusted model/tool text without explicit
adapter or user signal.

Reference deterministic defaults when `importance` is omitted:

| Event type | Default importance |
|---|---|
| `DECISION`, `ERROR`, `STATE`, `TURN_COMPLETE`, `SESSION_START` | `HIGH` |
| `USER_MESSAGE`, `SYSTEM_MESSAGE`, `ASSISTANT_MESSAGE`, `TOOL_CALL`, `TOOL_OUTPUT`, `FILE_CHANGE` | `NORMAL` |
| `ASSISTANT_MESSAGE_CHUNK`, `COMMAND_OUTPUT`, `MEMORY_READ` | `LOW` |
| Any other supported type | `NORMAL` |

Adapters that explicitly set `importance` override these defaults. Provider
output and untrusted content MUST NOT raise importance above `NORMAL` without
a trusted adapter/user signal.

`indexing` records how the event participates in retrieval indexes:

- `embedding_model_id` is required for persisted embedding/vector index rows,
  and retrieval MUST filter vector candidates to the currently configured
  embedding model id. Mixed-model vector scoring is not v0 compliant.
- `compression_applied=true` means the searchable/indexed text is a redacted
  summary or excerpt, while the raw event content remains available through
  `fetch_event`, export, or `BYTES_REF`.
- `summary` is optional and MUST be redacted before persistence. It is not a
  replacement for raw content.

`source_trust` values:

- `HOST_AUTHORED`: trusted host/runtime metadata or state.
- `USER_MESSAGE`: user-authored request text.
- `ASSISTANT_MESSAGE`: model output.
- `TRUSTED_TOOL_OUTPUT`: output from a local trusted adapter/tool.
- `UNTRUSTED_TOOL_OUTPUT`: tool output that may contain external or
  user-controlled text.
- `WEB_CONTENT`: fetched web content.
- `FILE_CONTENT`: file content read from the project.
- `EXTERNAL_MCP_CONTENT`: content returned by another MCP server.
- `PROVIDER_OUTPUT`: embedding/reranking/LLM provider output.
- `UNKNOWN`: trust cannot be determined.

Adapters SHOULD set `source_trust`; otherwise Mneme MUST default external tool,
web, and file-like outputs to an untrusted category.
`EXTERNAL_MCP_CONTENT` is untrusted by default unless a separate source adapter
trust registration explicitly marks the upstream server/output as trusted; MCP
being local or read-oriented does not make returned content instruction
authority.

### 12.4 Turn

```json
{
  "schema_version": "mneme.turn.v0",
  "turn_id": "turn-001",
  "turn_sequence": 12,
  "session_id": "session-123",
  "agent_id": "codex",
  "runtime": "CODEX",
  "status": "COMPLETED",
  "started_at": "2026-06-21T12:00:00Z",
  "completed_at": "2026-06-21T12:00:45Z",
  "event_ids": ["event-001", "event-002"],
  "prepare_ids": ["prepare-001"],
  "trace_ids": ["trace-001"],
  "usage": {
    "prompt_tokens": 18000,
    "completion_tokens": 1200,
    "tool_call_count": 3
  },
  "outcome": {
    "summary": "Inspected files and identified failing test.",
    "error_count": 0
  },
  "error": null
}
```

Turn status values:

- `STARTED`
- `COMPLETED`
- `FAILED`
- `INTERRUPTED`
- `CANCELLED`

`POST /v1/turns/complete` MUST accept non-success status values. Failed or
interrupted turns SHOULD include `error.code`, `error.message`, and any safe
diagnostic metadata.

### 12.5 Execution State

```json
{
  "schema_version": "mneme.execution_state.v0",
  "session_id": "session-123",
  "goal": "Ship semantic retrieval parity",
  "current_step": "Add execution state history",
  "open_loops": ["rerun full pytest"],
  "last_tool": "pytest",
  "last_tool_output_summary": "41 passed",
  "decision_stack": [
    {
      "event_id": "event-decision",
      "timestamp": "2026-06-21T12:03:00Z",
      "text": "Keep REST retrieval canonical."
    }
  ],
  "active_entities": ["API_MCP_CONTRACT_V0.md"],
  "turn_count": 2,
  "enrichment": {
    "intent_label": "IMPLEMENTATION",
    "topic_tags": ["retrieval", "mcp"],
    "decision_summary": "REST remains canonical."
  }
}
```

Allowed `enrichment` fields:

- `intent_label`
- `topic_tags`
- `decisions`
- `decision_summary`
- `active_entities`
- `open_loops`

Unknown enrichment fields MUST be ignored or stored under adapter metadata, not
committed to canonical execution state.

Execution-state compression levels for context preparation:

- `FULL`: include goal, current step, open loops, last tool summary, active
  entities, decision stack, and enrichment summary.
- `COMPACT`: include goal, current step, top open loops, last tool summary, and
  latest decisions.
- `MINIMAL`: include goal and current step only.
- `TRUNCATED`: include a budget-truncated minimal form and warning
  `EXECUTION_STATE_TRUNCATED`.

### 12.6 Control Request And Result Schemas

Session start:

```json
{
  "schema_version": "mneme.session_start.v0",
  "session_id": "019edb86-1d22-78a3-b9e4-e6121c294056",
  "agent_id": "codex",
  "runtime": "CODEX",
  "project_id": "repo-name",
  "privacy": {
    "project_isolation_key": "repo-name",
    "retention_days": 30
  },
  "metadata": {
    "thread_id": "codex-thread-id",
    "cwd": "/repo"
  }
}
```

`session_id` MAY be omitted only when the caller supplies `Idempotency-Key` and
accepts a daemon-generated id in the response.

Required `mneme.session_start.v0` fields:

- `schema_version`
- `agent_id`
- `runtime`
- `project_id`
- `privacy.project_isolation_key`

Optional fields:

- `session_id`, only when `Idempotency-Key` is supplied;
- `privacy.retention_days`, defaulting to daemon policy;
- `metadata`, `model`, `tokenizer`, and `context_window_tokens`.

Execution-state update:

```json
{
  "schema_version": "mneme.execution_state_update.v0",
  "mode": "PATCH",
  "state": {
    "goal": "Ship semantic retrieval parity",
    "current_step": "Add execution state history"
  },
  "provenance": {
    "event_id": "event-state-001",
    "turn_id": "turn-001",
    "adapter_trace_id": "host-trace-123"
  }
}
```

Execution-state update result:

```json
{
  "schema_version": "mneme.execution_state_update_result.v0",
  "session_id": "session-123",
  "updated": true,
  "state": {
    "schema_version": "mneme.execution_state.v0",
    "session_id": "session-123",
    "goal": "Ship semantic retrieval parity",
    "current_step": "Add execution state history"
  },
  "history_entry": {
    "schema_version": "mneme.state_history_entry.v0",
    "timestamp": "2026-06-21T12:00:00Z",
    "goal": "Ship semantic retrieval parity",
    "current_step": "Add execution state history"
  }
}
```

State history entry:

```json
{
  "schema_version": "mneme.state_history_entry.v0",
  "history_id": "state-history-001",
  "session_id": "session-123",
  "sequence": 7,
  "timestamp": "2026-06-21T12:00:00Z",
  "mode": "PATCH",
  "changed_fields": ["goal", "current_step"],
  "state_hash": "sha256:new-state",
  "previous_state_hash": "sha256:previous-state",
  "provenance": {
    "event_id": "event-state-001",
    "turn_id": "turn-001",
    "adapter_trace_id": "host-trace-123"
  },
  "summary": {
    "goal": "Ship semantic retrieval parity",
    "current_step": "Add execution state history"
  }
}
```

`mneme.state_history_entry.v0` is append-only. It MUST NOT store unredacted
tool output excerpts unless the same redaction rules as event ingestion have
already been applied.

`state_hash` and `previous_state_hash` canonicalization:

- Hash input MUST be the full redacted `mneme.execution_state.v0` object after
  the update is applied.
- JSON MUST be canonicalized with RFC 8785 JSON Canonicalization Scheme (JCS)
  before hashing. If a platform cannot use a JCS library, it MUST produce the
  same bytes: UTF-8 JSON, lexicographically sorted object keys, no
  insignificant whitespace, normalized JSON string escaping, and no non-finite
  numbers.
- Arrays keep their stored order. Fields whose order is logically unordered
  MUST be sorted by a documented stable key before hashing. For v0,
  `active_entities`, `open_loops`, and `decision_stack` use their stored order
  and are therefore part of the hash.
- Adapters and storage layers MUST preserve array insertion order for these
  fields. Generating state arrays from unordered maps/sets and then relying on
  runtime iteration order is non-compliant. Sorting is allowed only when the
  sort key is explicitly documented and treated as part of the v0 hash
  contract for that field.
- Implementations MUST NOT hash pretty-printed JSON, database row order, or
  language-native map iteration order.
- The digest format is `sha256:<lowercase-hex-digest>`.

Session lineage:

```json
{
  "schema_version": "mneme.session_lineage.v0",
  "lineage_id": "lineage-001",
  "parent_session_id": "session-parent",
  "child_session_id": "session-child",
  "relationship": "RESUME",
  "project_isolation_key": "repo-name",
  "created_at": "2026-06-21T12:00:00Z",
  "created_by": "ADAPTER",
  "provenance": {
    "event_id": "event-session-start",
    "adapter_trace_id": "host-trace-123"
  },
  "metadata": {}
}
```

`mneme.session_lineage.v0` relationship values:

- `RESUME`
- `FORK`
- `SUBAGENT`
- `IMPORT`
- `MANUAL_LINK`

Lineage edges are scoped by project visibility. Mneme MUST reject lineage that
would create a cycle or connect sessions outside the caller's visible
`project_isolation_key`.

Context prepare request:

```json
{
  "schema_version": "mneme.context_prepare_request.v0",
  "request_id": "prepare-001",
  "session_id": "session-123",
  "turn_id": "turn-002",
  "request_messages": [],
  "policy": {
    "budget_tokens": 140000,
    "context_window_tokens": 200000,
    "cost_mode": "STANDARD",
    "preserve_authority": true,
    "allow_historical_tail_truncation": true,
    "strict_schema": false,
    "budget_split": {
      "headroom_ratio": 0.10,
      "execution_state_ratio": 0.12,
      "protected_tail_ratio": 0.28,
      "retrieved_evidence_ratio": 0.45,
      "hints_ratio": 0.05
    }
  },
  "retrieval": {
    "query": "What context matters for this request?",
    "scope": "SESSION",
    "top_k": 10,
    "filters": {}
  },
  "freshness": {
    "current_evidence_refs": [],
    "conflicting_event_ids": []
  }
}
```

Canonical `policy.budget_split` keys:

- `headroom_ratio`: required hard reserve for tokenizer variance and expected
  completion tokens.
- `execution_state_ratio`: required slot for execution state.
- `protected_tail_ratio`: required slot for recent tail messages.
- `retrieved_evidence_ratio`: required slot for retrieved evidence.
- `hints_ratio`: optional slot for goal/checkpoint hints; if omitted, default
  is `0.0`.

If the caller omits `budget_split`, the daemon uses the default values shown
above. If the caller supplies `budget_split`, the known keys MUST sum to
`1.0 +/- 0.01`. Unknown budget keys return `422 VALIDATION_ERROR`.

Trace:

```json
{
  "schema_version": "mneme.trace.v0",
  "trace_id": "trace-001",
  "session_id": "session-123",
  "kind": "CONTEXT_PREPARE",
  "created_at": "2026-06-21T12:00:00Z",
  "request_id": "prepare-001",
  "tool": null,
  "selected_event_ids": ["event-010"],
  "dropped_event_refs": [],
  "retrieval": {
    "scope": "SESSION",
    "top_k": 10,
    "candidate_count": 12,
    "selected_count": 1,
    "degraded": false
  },
  "budget": {
    "budget_tokens": 140000,
    "minimum_headroom_tokens": 14000,
    "unused_context_slack_tokens": 1200
  },
  "warnings": [],
  "error": null
}
```

Trace `kind` values include `CONTEXT_PREPARE`, `MEMORY_READ`,
`SEGMENT_DRIFT`, `REINDEX`, `RETENTION_CLEANUP`, `AUTH_FAILURE`, and
`INTERNAL_ERROR`. Trace payloads MUST contain redacted summaries and ids, not
raw secrets or untrusted evidence inserted as instructions.

Cost report:

```json
{
  "schema_version": "mneme.cost_report.v0",
  "session_id": "session-123",
  "period": {
    "from": "2026-06-21T12:00:00Z",
    "to": "2026-06-21T13:00:00Z"
  },
  "usage": {
    "prompt_tokens": 120000,
    "completion_tokens": 8000,
    "embedding_tokens": 45000,
    "reranker_calls": 0,
    "llm_enrichment_tokens": 0,
    "tool_calls": 32
  },
  "estimated_cost": null,
  "provider_breakdown": [],
  "baseline": {
    "provider_prompt_tokens_without_mneme_estimate": 350000,
    "methodology": "DIRECT_ACTIVE_WINDOW"
  },
  "warnings": []
}
```

`estimated_cost` MAY be `null` when pricing metadata is unavailable. Baseline
estimates are counterfactual and MUST NOT be represented as measured savings
without a benchmark run.

Retention cleanup request:

```json
{
  "schema_version": "mneme.retention_cleanup_request.v0",
  "dry_run": false,
  "force_active_cleanup": false,
  "reason": "manual_owner_cleanup"
}
```

Retention cleanup result:

```json
{
  "schema_version": "mneme.retention_cleanup_result.v0",
  "session_id": "session-123",
  "status": "COMPLETED",
  "dry_run": false,
  "force_active_cleanup": false,
  "cutoff_timestamp": "2026-05-22T12:00:00Z",
  "events_deleted": 12,
  "state_history_deleted": 2,
  "graph_edges_deleted": 30,
  "blobs_deleted": 1,
  "blobs_orphaned": 0,
  "skipped_active_session": false,
  "in_flight_reads_blocked": 0,
  "warnings": []
}
```

`mneme.retention_cleanup_result.v0` status values:

- `COMPLETED`
- `DRY_RUN`
- `SKIPPED_ACTIVE_SESSION`
- `CONFLICT_IN_FLIGHT_READS`
- `FAILED`

Segment start:

```json
{
  "schema_version": "mneme.segment_start.v0",
  "session_id": "session-123",
  "segment_id": "segment-004",
  "title": "Hermes ContextEngine PR",
  "summary": "Work on native context-engine hooks.",
  "anchor_event_ids": ["event-010"],
  "provenance": {
    "event_id": "event-010",
    "turn_id": "turn-002"
  }
}
```

Required `segment_start.v0` fields:

- `schema_version`
- `session_id`

`segment_id` MAY be omitted only when the caller supplies `Idempotency-Key` and
accepts a daemon-generated id. Retry-safe adapters SHOULD either supply a
stable `segment_id` or an `Idempotency-Key`. If `segment_id` is omitted and
`Idempotency-Key` is missing, the daemon MUST return `422 VALIDATION_ERROR`
before creating a segment.

Segment close:

```json
{
  "schema_version": "mneme.segment_close.v0",
  "session_id": "session-123",
  "closed_at": "2026-06-21T12:30:00Z",
  "summary": "Finished parity investigation.",
  "outcome": "COMPLETED",
  "anchor_event_ids": ["event-010", "event-099"],
  "provenance": {
    "event_id": "event-099",
    "turn_id": "turn-003"
  }
}
```

`segment_close.v0` outcome values:

- `COMPLETED`
- `ABANDONED`
- `SUPERSEDED`
- `INTERRUPTED`
- `CANCELLED`
- `UNKNOWN`

Stored segment:

```json
{
  "schema_version": "mneme.segment.v0",
  "segment_id": "segment-004",
  "session_id": "session-123",
  "project_isolation_key": "repo-name",
  "title": "Hermes ContextEngine PR",
  "summary": "Work on native context-engine hooks.",
  "status": "CLOSED",
  "outcome": "COMPLETED",
  "started_at": "2026-06-21T12:00:00Z",
  "closed_at": "2026-06-21T12:30:00Z",
  "anchor_event_ids": ["event-010", "event-099"],
  "event_count": 24,
  "last_event_id": "event-099",
  "created_by": "ADAPTER",
  "metadata": {}
}
```

`mneme.segment.v0` status values:

- `OPEN`
- `CLOSED`
- `ABANDONED`
- `SUPERSEDED`

`mneme.segment.v0` `created_by` values:

- `ADAPTER`: explicit host/adapter boundary.
- `AUTOMATIC`: deterministic daemon segmentation.
- `ENRICHMENT`: optional provider-assisted segmentation.
- `IMPORTER`: offline importer or migration tool.

Segment event summary:

```json
{
  "schema_version": "mneme.event_summary.v0",
  "event_id": "event-010",
  "session_id": "session-123",
  "turn_id": "turn-002",
  "type": "TOOL_OUTPUT",
  "role": "TOOL",
  "timestamp": "2026-06-21T12:05:00Z",
  "importance": "NORMAL",
  "freshness": "RECENT",
  "snippet": "pytest failed with AssertionError",
  "redaction_applied": true
}
```

Session export:

```json
{
  "schema_version": "mneme.session_export.v0",
  "format": "json",
  "session": {},
  "turns": [],
  "events": [],
  "segments": [],
  "blobs_metadata": [],
  "blob_contents": [],
  "exported_at": "2026-06-21T12:00:00Z",
  "redaction_applied": true
}
```

For `format=json`, `blob_contents` MUST be empty unless a deployment explicitly
enables inline legacy blob export with `max_export_blob_inline_bytes > 0`.
Portable blob exports use `mneme.session_export_manifest.v0` inside the
`tar_bundle` format.

Session export manifest:

```json
{
  "schema_version": "mneme.session_export_manifest.v0",
  "format": "tar_bundle",
  "session_id": "session-123",
  "manifest_part": "manifest.json",
  "blob_parts": [
    {
      "blob_id": "blob-123",
      "path": "blobs/blob-123.bin",
      "size_bytes": 2097152,
      "hash": "sha256:example",
      "media_type": "application/pdf",
      "redaction_scope": "BINARY_METADATA_ONLY"
    }
  ],
  "exported_at": "2026-06-21T12:00:00Z",
  "redaction_applied": true
}
```

Context prepare response:

```json
{
  "schema_version": "mneme.context_prepare_response.v0",
  "request_id": "prepare-001",
  "prepare_id": "prepare-001",
  "session_id": "session-123",
  "turn_id": "turn-002",
  "changed": true,
  "messages": [],
  "trace_id": "trace-001",
  "trace": {
    "budget_tokens": 140000,
    "minimum_headroom_tokens": 14000,
    "execution_state_compression_level": "COMPACT",
    "unused_context_slack_tokens": 1200,
    "latest_user_message_preserved": true,
    "selected_event_ids": ["event-010"],
    "dropped_event_refs": []
  },
  "warnings": []
}
```

Reindex job:

```json
{
  "schema_version": "mneme.reindex_job.v0",
  "job_id": "reindex-001",
  "scope": "PROJECT",
  "project_isolation_key": "repo-name",
  "statuses": ["PENDING", "FAILED"],
  "status": "QUEUED",
  "created_at": "2026-06-21T12:00:00Z",
  "started_at": null,
  "completed_at": null,
  "progress": {
    "candidate_count": 100,
    "processed_count": 0,
    "failed_count": 0
  },
  "error": null
}
```

Reindex job status values:

- `QUEUED`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`
- `WAITING_FOR_PROVIDER`

### 12.7 Audit Record

```json
{
  "schema_version": "mneme.audit_record.v0",
  "audit_id": "audit-001",
  "trace_id": "trace-001",
  "session_id": "session-123",
  "project_isolation_key": "repo-name",
  "action": "MEMORY_READ",
  "tool": "context_search",
  "event_ids": ["event-001"],
  "created_at": "2026-06-21T12:00:00Z",
  "principal": {
    "name": "local-owner",
    "role": "OWNER",
    "project_scopes": ["*"]
  },
  "request": {
    "scope": "SESSION",
    "include_content": false
  },
  "result": {
    "selected_count": 1,
    "redaction_applied": true
  }
}
```

Audit action values:

- `MEMORY_READ`
- `CONTEXT_PREPARE`
- `AUTH_FAILURE`
- `SESSION_EXPORT`
- `SESSION_DELETE`
- `RETENTION_CLEANUP`
- `BLOB_READ`
- `BLOB_WRITE`
- `BLOB_DELETE`
- `BLOB_GC`
- `EXECUTION_STATE_UPDATE`
- `SEGMENT_START`
- `SEGMENT_CLOSE`
- `REINDEX_REQUEST`
- `REINDEX_CANCEL`
- `MAINTENANCE_SYSTEM_SWEEP`

`tool` is nullable. For model/tool-driven memory reads it SHOULD be the public
tool name such as `context_search`. For automatic daemon work it MUST be
`SYSTEM_DAEMON`; for authentication failures before tool routing it MUST be
`AUTH`.

For `AUTH_FAILURE` before a token can be resolved to a principal, the audit
principal MUST be:

```json
{
  "name": "UNAUTHENTICATED",
  "role": "UNAUTHENTICATED",
  "project_scopes": []
}
```

Audit records MUST be durable for live sessions. v0 session delete is a hard
privacy delete for session content, traces, retrieved excerpts, and
session-scoped derived data, but it MUST NOT erase all forensic evidence of
security-sensitive actions. Audit records for `MEMORY_READ`, `SESSION_EXPORT`,
`SESSION_DELETE`, `AUTH_FAILURE`, denied cross-project access, and maintenance
actions MUST be converted to anonymized forensic anchors when the source
session is deleted:

- raw `session_id`, event ids, trace ids, excerpts, prompts, and tool payloads
  are removed or replaced with salted hashes;
- action type, timestamp, principal class, project-scope hash, selected counts,
  and redaction/security flags may be retained;
- retained anchors follow `audit.forensic_retention_days`;
- normal session export MUST NOT include anchors for deleted sessions.

Forensic anchor hashes MUST use a per-record random salt. A deployment SHOULD
also use an operator-controlled pepper stored outside SQLite, such as an
environment variable or OS keychain entry. Static daemon-wide salts stored only
inside the database are not sufficient for deleted-session audit anonymity.

Tamper-evident audit logs or external audit shipping are FUTURE, but v0 MUST
preserve enough anonymized audit evidence for local owner incident review.

### 12.8 Graph Edge

```json
{
  "schema_version": "mneme.graph_edge.v0",
  "source_event_id": "event-tool-call",
  "target_event_id": "event-tool-output",
  "session_id": "session-123",
  "edge_type": "TOOL_RESULT",
  "weight": 1.0,
  "created_at": "2026-06-21T12:00:00Z"
}
```

Initial edge weights:

- `TOOL_RESULT`: `1.0`
- `TOOL_INPUT`: `1.0`
- `PARENT_CHILD`: `0.9`, generated from explicit `parent_event_ids`.
- `DECISION_FOLLOWS`: `0.8`
- `MEMORY_READ_EVIDENCE`: `0.8`, generated from a direct memory-read event to
  the selected evidence event ids returned to the caller.
- `SEGMENT_ANCHOR`: `0.7`, generated when `segment_start` or
  `segment_close` includes `anchor_event_ids`.
- `SEGMENT_MEMBER`: `0.5`, generated for events assigned to a segment by
  automatic segmentation or explicit adapter metadata.
- temporal `FOLLOWS`: `0.2`

Traversal score is deterministic:

```text
score = edge.weight * bounded_importance_boost(seed_event, target_event, depth) * (mode.depth_decay ** max(depth - 1, 0))
```

Default `depth_decay` is `0.6` for `TOOL_CHAIN`, `SEGMENT`, and `TEMPORAL`
traversal, and `0.85` for `CAUSAL` traversal so longer causal chains are not
discarded too aggressively. Ties sort by newer timestamp, then stable event id.
Default `importance_depth_decay` is
`retrieval.graph.importance_depth_decay=0.5`.

Initial `importance_multiplier` values before depth bounding:

- `CRITICAL`: `1.5`
- `HIGH`: `1.25`
- `NORMAL`: `1.0`
- `LOW`: `0.75`
- unknown importance: `1.0`

`bounded_importance_boost` MUST decay or cap importance with graph depth so a
single `CRITICAL` event does not pull an unbounded chain of low-relevance
neighbors. Normative behavior:

- depth `0`: use seed importance multiplier;
- depth `1`: use `max(seed, target)` multiplier, capped at `1.5`;
- depth `>=2`: multiply the target multiplier by
  `importance_depth_decay ** (depth - 1)` and cap the result at `1.1`.

The algorithm is intentionally target-aware for candidate scoring, but the
depth cap prevents "importance bombs" from consuming all `max_events`.
Implementations MAY expose a different `importance_depth_decay` only if the
configured value is advertised in capabilities and used consistently for all
traversal and test expectations in that daemon.

Dynamic learned edge weights are FUTURE.

### 12.9 Entity Modifier

`mneme.entity_modifier.v0` is used when optional delta extraction is enabled
for `CONTINUATION` messages. It is a deterministic state-update hint, not a
trusted adapter override.

```json
{
  "schema_version": "mneme.entity_modifier.v0",
  "modifier_type": "ADD",
  "entity": "PostgreSQL",
  "value": null,
  "source": "DETERMINISTIC_PATTERN",
  "source_span": {
    "start_char": 12,
    "end_char": 22
  }
}
```

`modifier_type` values:

- `ADD`: add or reinforce an active entity.
- `REMOVE`: remove an active entity if it exists.
- `REPLACE`: replace `entity` with `value`; `value` MUST be non-null.
- `CONSTRAINT`: add a constraint-like entity without removing existing
  entities.

`source` values:

- `DETERMINISTIC_PATTERN`
- `ADAPTER_SIGNAL`
- `PROVIDER_GUARDED`

Automatic v0 delta extraction MAY update only `execution_state.active_entities`.
Other execution-state fields require a trusted adapter call to
`POST /v1/sessions/{session_id}/execution_state`.

## 13. Blob And BYTES_REF Protocol

Inline event content above `max_event_content_bytes` MUST be rejected with
`413 PAYLOAD_TOO_LARGE`. The adapter MUST retry with `BYTES_REF`.

`BYTES_REF` MUST be backed by an explicit blob protocol. It is not valid to
reference arbitrary undocumented daemon filesystem paths.

### 13.1 Blob Ownership

Blob ownership values:

- `SERVER`: Mneme owns the blob bytes in its configured blob store.
- `ADAPTER`: FUTURE/optional; the adapter owns the referenced external
  file/object and Mneme stores metadata only.

Server-owned blobs are REQUIRED for v0 compliance. Adapter-owned `file://`
references are not part of the v0 compliant path unless a deployment explicitly
enables an experimental trusted-path driver.

### 13.2 Blob Schema

```json
{
  "schema_version": "mneme.blob.v0",
  "blob_id": "blob-123",
  "uri": "mneme-blob://blob-123",
  "owner": "SERVER",
  "session_id": "session-123",
  "project_isolation_key": "repo-name",
  "hash": "sha256:example",
  "size_bytes": 2097152,
  "media_type": "text/plain",
  "created_at": "2026-06-21T12:00:00Z",
  "ref_count": 1,
  "retention": {
    "delete_with_session": true,
    "expires_at": null
  },
  "metadata": {
    "source": "tool-output"
  }
}
```

### 13.3 BYTES_REF Content Shape

```json
{
  "format": "BYTES_REF",
  "uri": "mneme-blob://blob-123",
  "hash": "sha256:example",
  "size_bytes": 2097152,
  "media_type": "text/plain",
  "storage_owner": "SERVER"
}
```

`file://` URIs are FUTURE/experimental in v0. If a deployment enables them,
it MUST define `blob.trusted_adapter_paths`, mark exports as non-portable, and
pass additional path traversal tests. The default compliant v0 path is
`mneme-blob://...`.

### 13.4 Blob Endpoints

Required REST endpoints:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/blobs` | Upload server-owned bytes and return a `BYTES_REF`. |
| `GET` | `/v1/blobs/{blob_id}` | Return blob metadata, not bytes. |
| `GET` | `/v1/blobs/{blob_id}/content` | Return blob bytes if caller has project scope. |
| `DELETE` | `/v1/blobs/{blob_id}` | Delete an unreferenced blob or mark it for GC. |
| `POST` | `/v1/maintenance/blob-gc` | Run idempotent orphan cleanup for the configured blob store. |

`POST /v1/blobs` request:

- Body: `application/octet-stream` or multipart upload.
- Headers:
  - `X-Mneme-Session-Id`
  - `X-Mneme-Project-Isolation-Key`
  - `Content-Type`
  - optional `Digest: sha-256=<base64 or hex>`
  - optional `Idempotency-Key`

Response:

```json
{
  "schema_version": "mneme.blob.v0",
  "blob_id": "blob-123",
  "bytes_ref": {
    "format": "BYTES_REF",
    "uri": "mneme-blob://blob-123",
    "hash": "sha256:example",
    "size_bytes": 2097152,
    "media_type": "text/plain",
    "storage_owner": "SERVER"
  }
}
```

`POST /v1/events` MAY also accept multipart event ingestion for adapter DX. In
that mode, JSON event parts and binary parts are submitted in one request; the
server stores binary parts as server-owned blobs and returns normalized
`BYTES_REF` metadata in the ingestion response. The canonical persisted event
still contains `BYTES_REF`, not inline bytes.

Multipart event ingestion contract:

- Content type is `multipart/form-data`.
- One part named `payload` MUST contain `mneme.event_batch.v0` JSON.
- Binary parts MUST be named `blob.<client_part_id>`.
- JSON event content MAY reference `multipart://<client_part_id>` placeholders;
  the daemon rewrites them to `mneme-blob://...` `BYTES_REF` values after
  successful blob persistence.
- Idempotency and immutable event identity are computed from the canonical
  pre-rewrite logical payload plus each referenced binary part digest. The
  persisted normalized representation stores `mneme-blob://...` references.
  Implementations SHOULD record both `original_content_hash` and
  `normalized_content_hash` for audit/debugging.
- Embedded multipart blob idempotency is request-scoped: a repeated
  `POST /v1/events` with the same `Idempotency-Key`, canonical payload hash,
  and binary part digests returns the same normalized `BYTES_REF` metadata.
  Without `Idempotency-Key`, stable event ids plus part digests still prevent
  duplicate referenced blob rows for replayed events, but retry-safe adapters
  SHOULD send the header.
- Maximum multipart blob part count defaults to `max_batch_events`.
- Malformed multipart boundaries return `400 BAD_REQUEST`.
- Unsupported media types return `415 UNSUPPORTED_MEDIA_TYPE`.
- Any part above `max_blob_bytes` returns `413 PAYLOAD_TOO_LARGE`.
- Total blob bytes across one multipart request MUST NOT exceed
  `max_batch_total_blob_bytes`; the reference default is 20 MiB. Larger
  submissions return `413 PAYLOAD_TOO_LARGE` with guidance to split the batch.
- A single SQLite multipart transaction or savepoint group MUST NOT exceed
  `max_multipart_transaction_bytes`; the reference default is 22 MiB.
- A single SQLite multipart foreground write SHOULD also respect
  `max_multipart_transaction_ms`; if the daemon cannot safely complete within
  this bound, it SHOULD reject or ask the client to split the request before
  entering the writer lane. This is a latency guard, not a correctness
  substitute for atomic commit/rollback.
- The effective allowed total blob bytes for one multipart request is
  `min(max_batch_total_blob_bytes, max_multipart_transaction_bytes -
  max_multipart_metadata_overhead_bytes)`. With reference defaults this is
  20 MiB for blob bytes plus 2 MiB reserved for event/blob metadata and
  savepoint bookkeeping.
- The whole multipart request is atomic for metadata: if blob persistence
  fails, events referencing those blobs MUST NOT be committed.
- For the v0 SQLite blob driver, binary blob rows and event rows MUST be
  written in a transaction or nested savepoint sequence bounded by
  `max_multipart_transaction_bytes`. If the transaction fails, neither
  referenced events nor blob metadata may remain committed. Implementations
  that support request-level micro-transactions MUST hide partially staged
  batches from retrieval until the whole HTTP request commits and MUST use the
  request `Idempotency-Key` plus part digests for replay safety.
- Experimental filesystem blob drivers MUST write blob files to a temporary
  pending area and promote them only after event commit, or record pending
  blobs for immediate reconciliation/GC before reporting success.

Blob content reads:

- `GET /v1/blobs/{blob_id}/content` MUST set `Content-Type` from blob metadata.
- The reference daemon MUST support single byte-range requests for blob content.
- Valid single ranges return `206 Partial Content` with `Content-Range`.
- Unsatisfiable ranges return `416 RANGE_NOT_SATISFIABLE`.
- Malformed range headers return `400 BAD_REQUEST`.
- Multiple ranges MAY return `416 RANGE_NOT_SATISFIABLE` unless the daemon
  explicitly advertises multipart range support.
- A no-`Range` request MAY return `200 OK` for blobs within safe response
  limits. If the blob would exceed the configured direct-download response
  limit, return `413 PAYLOAD_TOO_LARGE` with guidance to retry with `Range`.

### 13.5 Blob Storage Layout

Reference daemon storage:

- The v0 compliant reference store keeps server-owned blob bytes in SQLite BLOB
  rows, keyed by `blob_id` and content hash. This preserves ACID behavior with
  event metadata and avoids filesystem/SQLite two-phase consistency problems.
- The default SQLite blob driver limit is `max_blob_bytes=2097152` (2 MiB).
  Larger artifacts require an explicitly enabled experimental filesystem driver
  or a future chunked blob protocol.
- SQLite blob writes and reads SHOULD use incremental blob I/O or equivalent
  streaming so the daemon does not load the entire blob into memory when a
  ranged operation would suffice.
- Deployments SHOULD set a bounded `PRAGMA journal_size_limit` appropriate for
  local disk capacity.
- Optional filesystem blob storage is FUTURE/experimental. If implemented, it
  MUST use write-temp/fsync/rename, hash verification, and reconciliation before
  being marked compliant.

The filesystem path MUST NOT be exposed as the canonical URI. The canonical URI
is `mneme-blob://blob_id`.

### 13.6 Blob GC, Export, And Backup

- Session delete MUST delete server-owned SQLite blobs referenced only by that
  session in the same transaction where possible, or mark them for garbage
  collection.
- Export MUST include blob metadata. `format=json` is metadata-only by default.
  Portable exports that include blob bytes MUST use the streaming
  `tar_bundle` format so large blobs are not accumulated as one base64 JSON
  document or hard-to-parse `multipart/mixed` response.
- Inline base64 blob export is a legacy/diagnostic extension only. It is
  disabled by default with `max_export_blob_inline_bytes=0`; if a deployment
  enables it, each inlined blob MUST remain below that limit and the capability
  response MUST advertise the configured value.
- Backup MUST include SQLite; if an experimental filesystem blob store is used,
  backup MUST include both SQLite and the blob directory in one consistent
  snapshot.
- Orphan blob GC MUST be safe and idempotent.
- GC runs when explicitly invoked by `/v1/maintenance/blob-gc`, a CLI command
  such as `mneme maintenance blob-gc`, startup maintenance when configured, or
  retention cleanup. v0 MUST NOT pretend background GC exists unless it is
  actually implemented and observable.
- Retention cleanup sweeps MUST run automatically at daemon startup and session
  close when the corresponding config flags are enabled. A periodic retention
  timer SHOULD run according to `maintenance.retention_sweep_interval_seconds`.
  These sweeps are background maintenance and MUST be observable in logs,
  traces, or metrics.
- `/v1/maintenance/blob-gc` requires an authenticated principal. If no
  `project_isolation_key` or `session_id` filter is supplied, only an `OWNER`
  principal with `all-projects` scope may run it. Scoped adapter tokens may run
  GC only for their visible project/session scope. The response MUST report
  candidate, deleted, skipped, and dry-run counts.

CURRENT GAP: the existing alpha contract mentions `BYTES_REF` but does not yet
fully implement this blob lifecycle.

## 14. REST API

All REST endpoints use JSON unless noted. All authenticated endpoints must
enforce project scope.

### 14.1 Health And Capabilities

Required:

- `GET /v1/health`
- `GET /v1/capabilities`
- `POST /v1/readiness/session`
- `GET /v1/metrics`
- `GET /openapi.json`

`/v1/health` is liveness only. It MUST NOT be treated as a readiness check for
hard dependencies because it does not prove authentication, session visibility,
or evidence availability.

Hard dependencies that need Mneme evidence at run start MUST call authenticated
`/v1/readiness/session` with the target `session_id`, a task-specific query
when evidence is required, and `require_evidence=true`.

Readiness request:

```json
{
  "session_id": "019edb86-1d22-78a3-b9e4-e6121c294056",
  "query": "project benchmark evidence status",
  "require_evidence": true,
  "allow_provider_calls": false,
  "top_k": 1,
  "scope": "SESSION"
}
```

Readiness outcomes:

- `401 UNAUTHENTICATED`: missing or invalid bearer token; fail configuration.
- `404 NOT_FOUND`: unknown session id; fail session resolution.
- `412 FAILED_PRECONDITION` with `details.reason=NO_EVIDENCE`: session exists
  but required evidence was not found; fail the run-start evidence gate.
- `200 ok=true`: Mneme is usable for the session and can return evidence.

When `require_evidence=false`, readiness checks authentication, project scope,
session existence, SQLite accessibility, and cached provider/storage status
only. It MUST NOT perform embedding, reranker, or LLM provider calls. It MUST
return `200 ok=true` for an existing visible session even when no evidence
matches the optional query.

When `require_evidence=true`, readiness verifies that Mneme can return at
least one visible evidence item for the supplied query/scope. The default
compliant path MUST use already persisted indexes and local lexical fallback.
It MUST NOT make external provider calls unless the request explicitly opts in
with `allow_provider_calls=true` and the daemon advertises that readiness
provider calls are supported. If provider calls are not allowed and no local
evidence is available, return `412 FAILED_PRECONDITION` with
`details.reason=NO_EVIDENCE` or `details.reason=INDEX_UNAVAILABLE`, as
appropriate.

Readiness calls with `allow_provider_calls=true` share the same provider
request budgets, rate limits, circuit breakers, retries, and cost accounting as
normal retrieval/context operations. Adapters SHOULD NOT poll provider-enabled
readiness before every turn; use `require_evidence=false` for cheap session
startup checks.

Alpha daemons that predate `/v1/readiness/session` are covered by the
compatibility notes in Section 27. A v0 compliant daemon MUST expose
`/v1/readiness/session`; `/v1/health` and unauthenticated probes are never
sufficient readiness checks for hard dependencies.

Capabilities MUST include:

```json
{
  "api_version": "v1",
  "service_version": "0.1.0",
  "supported_cost_modes": ["MINIMAL", "STANDARD", "QUALITY"],
  "default_cost_mode": "STANDARD",
  "strict_cost_mode": false,
  "supports_embeddings": true,
  "requires_embeddings": false,
  "supports_reranking": false,
  "supports_llm_enrichment": false,
  "supports_context_prepare": true,
  "supports_mcp_tools": true,
  "supports_blob_store": true,
  "supports_blob_range_reads": true,
  "supports_export_bundle": true,
  "supported_export_formats": ["json", "tar_bundle"],
  "supports_project_isolation": true,
  "supports_session_readiness": true,
  "supports_retention_cleanup": true,
  "supports_reindex_jobs": true,
  "supports_reindex_job_polling": true,
  "supports_openapi": true,
  "supports_metrics": true,
  "metrics_format": "prometheus",
  "auth_schemes": ["BEARER_TOKEN", "UNIX_SOCKET"],
  "supported_schema_versions": {
    "session": ["mneme.session.v0"],
    "session_start": ["mneme.session_start.v0"],
    "session_export": ["mneme.session_export.v0"],
    "session_export_manifest": ["mneme.session_export_manifest.v0"],
    "event_batch": ["mneme.event_batch.v0"],
    "event": ["mneme.event.v0"],
    "event_summary": ["mneme.event_summary.v0"],
    "turn": ["mneme.turn.v0"],
    "message": ["mneme.message.v0"],
    "context_prepare_request": ["mneme.context_prepare_request.v0"],
    "context_prepare_response": ["mneme.context_prepare_response.v0"],
    "retention_cleanup_request": ["mneme.retention_cleanup_request.v0"],
    "retention_cleanup_result": ["mneme.retention_cleanup_result.v0"],
    "trace": ["mneme.trace.v0"],
    "audit_record": ["mneme.audit_record.v0"],
    "cost_report": ["mneme.cost_report.v0"],
    "execution_state": ["mneme.execution_state.v0"],
    "execution_state_update": ["mneme.execution_state_update.v0"],
    "execution_state_update_result": ["mneme.execution_state_update_result.v0"],
    "state_history_entry": ["mneme.state_history_entry.v0"],
    "session_lineage": ["mneme.session_lineage.v0"],
    "segment": ["mneme.segment.v0"],
    "segment_start": ["mneme.segment_start.v0"],
    "segment_close": ["mneme.segment_close.v0"],
    "graph_edge": ["mneme.graph_edge.v0"],
    "blob": ["mneme.blob.v0"],
    "reindex_job": ["mneme.reindex_job.v0"]
  },
  "mcp_tool_versions": {
    "resolve_session": "v0",
    "list_sessions": "v0",
    "context_search": "v0",
    "fetch_event": "v0",
    "expand_context": "v0",
    "recall_recent": "v0",
    "list_segments": "v0",
    "get_execution_state": "v0",
    "get_goal_history": "v0",
    "explain_context": "v0",
    "mneme_cost_report": "v0"
  },
  "limits": {
    "max_batch_events": 200,
    "max_event_content_bytes": 1048576,
    "max_blob_bytes": 2097152,
    "max_session_id_length": 256,
    "max_batch_total_blob_bytes": 20971520,
    "max_multipart_metadata_overhead_bytes": 2097152,
    "max_multipart_transaction_bytes": 23068672,
    "max_export_blob_inline_bytes": 0,
    "max_export_session_memory_bytes": 33554432,
    "top_k": 10,
    "top_k_max": 100,
    "page_size_default": 20,
    "page_size_max": 1000,
    "expand_context_depth_default": 2,
    "expand_context_depth_max": 5,
    "expand_context_max_events_default": 12,
    "expand_context_max_events_max": 200,
    "max_latency_ms_default": 250,
    "max_parent_event_ids": 64,
    "idempotency_key_min_retention_seconds": 604800,
    "graph_importance_depth_decay": 0.5
  },
  "tokenizer": {
    "tokenizer_id": "char_4_fallback",
    "token_estimate_quality": "CHAR_APPROXIMATE"
  },
  "storage": {
    "sqlite_wal": true,
    "blob_driver": "sqlite",
    "schema_version": 3,
    "migration_status": "CURRENT",
    "vector_acceleration": "PYTHON_FALLBACK"
  }
}
```

### 14.2 Session Lifecycle

Required:

- `POST /v1/sessions/start`
- `GET /v1/sessions/{session_id}`
- `POST /v1/sessions/{session_id}/close`
- `POST /v1/sessions/{session_id}/retention/cleanup`
- `GET /v1/sessions/{session_id}/export`
- `DELETE /v1/sessions/{session_id}`

`POST /v1/sessions/start` MUST be idempotent for the same compatible
`session_id`. Incompatible reuse returns `409 CONFLICT`.

Request:

```json
{
  "schema_version": "mneme.session_start.v0",
  "session_id": "019edb86-1d22-78a3-b9e4-e6121c294056",
  "agent_id": "codex",
  "runtime": "CODEX",
  "project_id": "repo-name",
  "privacy": {
    "project_isolation_key": "repo-name",
    "retention_days": 30
  },
  "metadata": {
    "thread_id": "codex-thread-id",
    "cwd": "/repo"
  }
}
```

`session_id` SHOULD be supplied by host adapters that already have a stable
thread/run id. If omitted, the daemon generates a session id; callers that need
retry safety MUST provide `Idempotency-Key`.

`GET /v1/sessions/{session_id}` returns a redacted session object and derived
counts visible to the caller.

`POST /v1/sessions/{session_id}/close` sets `status=ENDED` and `ended_at`; it
does not delete events.

`POST /v1/sessions/{session_id}/retention/cleanup` applies
`privacy.retention_days` and blob GC for that session. For `ENDED` sessions,
the cutoff is computed from `ended_at` when available, otherwise from request
processing time with warning `ENDED_SESSION_MISSING_ENDED_AT` in the response,
logs, and metrics. Events, derived searchable records, and session-scoped blobs
older than the cutoff are eligible for cleanup unless another retained record
still references them.

Request body is `mneme.retention_cleanup_request.v0`. `force_active_cleanup`
MUST be supplied in the JSON body, not as an ambiguous query parameter. If no
body is supplied, defaults are `dry_run=false` and
`force_active_cleanup=false`.

Response body is `mneme.retention_cleanup_result.v0` and MUST include
`cutoff_timestamp`, deletion counts, orphan counts, `dry_run`,
`force_active_cleanup`, and whether an active session was skipped.

Retention cleanup MUST NOT delete events, state history, graph edges, or blobs
belonging to `ACTIVE` sessions by default. Cleanup of active-session data
requires explicit `force_active_cleanup=true` and OWNER authorization; scoped
adapter tokens cannot force active cleanup.

If `force_active_cleanup=true` targets an `ACTIVE` session and the daemon has
in-flight `context_prepare`, memory-read, export, or blob-read requests for the
same session, the endpoint MUST return `409 CONFLICT` with
`details.reason=IN_FLIGHT_READS`. v0 does not allow deleting active-session
data underneath ongoing reads. A future implementation may support deferred
deletion, but it must advertise that behavior explicitly.

Authorization:

- `OWNER` with `all-projects` may run cleanup for any session visible to the
  daemon.
- Scoped adapter tokens may run cleanup for any non-active session within their
  visible `project_isolation_key`.
- Cross-project cleanup requests from scoped tokens return `403 FORBIDDEN`.

Automatic retention sweeps MUST use the same authorization and scope logic as
the explicit endpoint. Startup and session-close sweeps are configured through
`maintenance.retention_sweep_on_startup` and
`maintenance.retention_sweep_on_session_close`; periodic sweeps use
`maintenance.retention_sweep_interval_seconds`. All automatic sweeps MUST be
observable in logs/traces/metrics and MUST run at background priority.
Automatic sweeps run as principal `SYSTEM_DAEMON` and MUST create a
`RETENTION_CLEANUP` or `MAINTENANCE_SYSTEM_SWEEP` audit record containing safe
counts and scope metadata, not raw event content.

`GET /v1/sessions/{session_id}/export` query parameters:

- `format=json`: required v0 metadata-only JSON export.
- `format=tar_bundle`: required v0 portable export for blob bytes.
- Unknown `format` values return `422 VALIDATION_ERROR` with
  `details.field="format"`.
- `include_blobs=false`: default; include blob metadata only.
- `include_blobs=true`: valid only with `format=tar_bundle` unless the
  daemon explicitly advertises legacy inline export with
  `max_export_blob_inline_bytes > 0`.
- `include_audit=false`: default; do not include audit records.
- `include_audit=true`: include audit records only when the caller has
  permission; otherwise return `403 FORBIDDEN` or omit with an explicit warning
  when policy allows partial export.

`format=json` response:

```json
{
  "schema_version": "mneme.session_export.v0",
  "format": "json",
  "session": {},
  "turns": [],
  "events": [],
  "segments": [],
  "blobs_metadata": [
    {
      "blob_id": "blob-123",
      "uri": "mneme-blob://blob-123",
      "size_bytes": 2097152,
      "hash": "sha256:example",
      "media_type": "application/pdf",
      "omitted_reason": "FORMAT_JSON_METADATA_ONLY"
    }
  ],
  "blob_contents": [],
  "audit_records": [],
  "exported_at": "2026-06-21T12:00:00Z",
  "redaction_applied": true
}
```

Blob omission reason values:

- `FORMAT_JSON_METADATA_ONLY`
- `INLINE_LIMIT_EXCEEDED`
- `SCOPE_FORBIDDEN`
- `BLOB_DELETED`
- `BINARY_REDACTION_UNAVAILABLE`
- `POLICY_EXCLUDED`

`format=tar_bundle` response:

- Content type: `application/x-tar`.
- The response MUST be streamed from storage; a compliant daemon MUST NOT build
  the whole archive in memory.
- `max_export_session_memory_bytes` applies to JSON export, legacy inline blob
  export, and non-compliant diagnostic/export tooling. It is not permission to
  buffer a compliant `tar_bundle` response in memory.
- Tar entry `manifest.json` contains `mneme.session_export_manifest.v0`.
- Tar entries under `blobs/` contain raw blob bytes. Manifest `blob_parts.path`
  links each blob to its tar entry and to `blobs_metadata`.
- A legacy `multipart_bundle` MAY be supported as a compatibility extension,
  but it is not a required v0 portable export format.

`DELETE /v1/sessions/{session_id}` removes or irreversibly redacts session data
according to retention policy. v0 privacy delete removes session content,
retrieved excerpts, traces, blobs, and derived indexes inside the deleted
session scope. Security-sensitive audit records are retained only as
anonymized forensic anchors as defined in Section 12.7.

### 14.3 Event Ingestion

Required:

- `POST /v1/events`

Rules:

- Unknown sessions return `404 NOT_FOUND`.
- Stable `event_id` replay with identical immutable fields returns success and
  increments duplicate counters.
- Stable `event_id` reuse with incompatible immutable fields returns
  `409 CONFLICT`.
- Inline payload above `max_event_content_bytes` returns
  `413 PAYLOAD_TOO_LARGE`.
- Batch ingestion MAY partially accept valid entries and reject invalid entries.
- Adapter ingestion SHOULD be batch-first. High-volume streams such as
  `ASSISTANT_MESSAGE_CHUNK`, command output chunks, and parallel tool outputs
  SHOULD be buffered and sent in batches up to `max_batch_events` or a short
  latency window. Single-event writes remain valid for low-volume adapters but
  SHOULD NOT be used for bursty streaming workloads.

Derived intelligence during ingestion:

- Mneme core MUST preserve raw event content after redaction and immutable
  hashing. Indexing or compression decisions MUST NOT destroy the fetchable raw
  event body.
- Deterministic execution-state updates, intent classification, segmentation,
  graph-edge creation, and index scheduling are derived projections from stored
  events. If a derived projection fails, the canonical event remains stored and
  the projection is repaired through reindex/rebuild paths.
- Textual `TOOL_OUTPUT` and `COMMAND_OUTPUT` events whose token estimate is
  above `indexing.tool_output_compress_threshold_tokens` MUST use selective
  indexing compression: the searchable/embedding input is a redacted summary or
  deterministic excerpt of about `indexing.tool_output_summary_tokens`, while
  the full raw content remains available by event id or blob reference.
- Compression defaults by event type:

  | Event type | Indexing compression default |
  |---|---|
  | `TOOL_OUTPUT`, `COMMAND_OUTPUT` | Compress when textual and above `indexing.tool_output_compress_threshold_tokens`. |
  | `USER_MESSAGE`, `SYSTEM_MESSAGE`, `DECISION`, `STATE`, `TURN_COMPLETE` | Do not compress by default. |
  | `ASSISTANT_MESSAGE`, `ASSISTANT_MESSAGE_CHUNK` | Do not compress by default in v0; adapters SHOULD chunk high-volume streams rather than hiding model output behind summaries. |
  | Binary/blob-like content | Do not summarize raw bytes; index only safe metadata or a redacted textual extraction supplied by a trusted adapter. |

- Provider-assisted summarization MAY be used for indexing compression only
  after redaction. If that provider is unavailable, the daemon MUST fall back to
  a deterministic redacted excerpt or mark embedding/indexing degraded; it MUST
  NOT block event persistence.
- Deterministic excerpt behavior is normative when provider summarization is
  unavailable: after redaction and tokenization, if the redacted text fits the
  target token budget, use it unchanged; otherwise take the first 60% of target
  tokens and the last 40% of target tokens, join them with the literal marker
  `[...]`, and then trim to the target budget. Implementations MAY respect
  sentence boundaries only when the result remains deterministic for the same
  input and tokenizer.
- Persisted embedding rows MUST record `embedding_model_id`; vector retrieval
  MUST ignore rows whose model id differs from the active embedding model.

### 14.4 Turn Completion

Required:

- `POST /v1/turns/complete`

Rules:

- Accepts statuses: `COMPLETED`, `FAILED`, `INTERRUPTED`, `CANCELLED`.
- Idempotent by `session_id + turn_id + status + immutable outcome fields`.
- Repeated compatible calls return the already recorded turn.
- Incompatible repeated calls return `409 CONFLICT`.
- The endpoint updates derived state, segments, graph edges, provider metrics,
  and usage counters when possible.

### 14.5 Explicit Execution State Update

Required for `EVENT_INGEST+` adapters that can provide reliable state:

- `POST /v1/sessions/{session_id}/execution_state`

Purpose: let a trusted adapter explicitly update state fields when automatic
inference is insufficient.

Rules:

- This is REST only in v0. MCP remains read-oriented.
- Updates must be scoped to the session and project key.
- Updates create `mneme.state_history_entry.v0`.
- Updates must include provenance: `event_id`, `turn_id`, or adapter trace id.
- Unknown fields are rejected with `422 VALIDATION_ERROR`.

Request:

```json
{
  "schema_version": "mneme.execution_state_update.v0",
  "mode": "PATCH",
  "state": {
    "goal": "Ship semantic retrieval parity",
    "current_step": "Add execution state history",
    "open_loops": ["rerun full pytest"],
    "active_entities": ["API_MCP_CONTRACT_V0.md"]
  },
  "provenance": {
    "event_id": "event-state-001",
    "turn_id": "turn-001",
    "adapter_trace_id": "host-trace-123"
  }
}
```

`mode` values:

- `PATCH`: update only supplied allowed fields.
- `REPLACE`: replace the complete execution-state object, preserving immutable
  `session_id` and schema fields.

Response:

```json
{
  "schema_version": "mneme.execution_state_update_result.v0",
  "session_id": "session-123",
  "updated": true,
  "state": {
    "schema_version": "mneme.execution_state.v0",
    "session_id": "session-123",
    "goal": "Ship semantic retrieval parity",
    "current_step": "Add execution state history"
  },
  "history_entry": {
    "schema_version": "mneme.state_history_entry.v0",
    "timestamp": "2026-06-21T12:00:00Z",
    "goal": "Ship semantic retrieval parity",
    "current_step": "Add execution state history"
  }
}
```

Automatic state inference still occurs from:

- `STATE` events;
- `DECISION` events;
- turn outcome summaries;
- assistant messages with explicit current-step/plan signals;
- tool outputs and errors for last tool and open-loop signals;
- optional LLM enrichment constrained to allowed state fields.

### 14.5.1 Runtime-Neutral Intent And Routing Intelligence

Hermes-parity quality requires more than storing memory. For `CONTEXT_ENGINE`
paths, Mneme core MUST provide deterministic runtime-neutral routing
intelligence so host adapters do not each reimplement topic-switch and
continuation logic. Adapters MAY supply stronger explicit lifecycle signals,
but absence of those signals MUST NOT reduce Mneme to naive query concatenation.

Intent values:

- `SWITCH`: user explicitly or semantically pivots away from the current task.
- `NEW_TASK`: embedding drift indicates a likely new task/topic without an
  explicit switch phrase.
- `CLARIFICATION`: user asks about the immediately previous output or tool
  result.
- `CONTINUATION`: default ongoing-task continuation.

Deterministic priority order:

1. Explicit switch phrase from `retrieval.routing.explicit_switch_patterns` or
   adapter-supplied current-task boundary signal -> `SWITCH`.
2. Entity contradiction against current goal/current step/active entities when
   `entity_contradiction_enabled=true` -> `SWITCH`.
3. Segmenter or embedding-drift signal above `segmentation.drift_threshold` ->
   `NEW_TASK` unless an explicit switch already matched.
4. Question about previous output when `question_about_output_enabled=true`
   and the message references the last assistant/tool entities ->
   `CLARIFICATION`.
5. Otherwise -> `CONTINUATION`.

Default explicit switch phrases are:

- `new topic`
- `switch to`
- `forget that`
- `instead`
- `let's move on`
- `different task`
- `change direction`

Deployments MAY add localized or project-specific switch phrases, but MUST NOT
remove all defaults unless runtime-neutral routing is explicitly disabled.

Entity contradiction detection:

- uses current `execution_state.goal`, `current_step`, and `active_entities`;
- performs exact case-insensitive phrase checks for active entities before any
  provider-assisted extraction;
- treats an active entity as contradicted when a configured negation term
  appears within five whitespace-delimited words before the entity, or when a
  configured replacement pattern such as `replace <old> with <new>`, `use
  <new> instead of <old>`, or `<new> instead of <old>` names the active entity
  as `<old>`;
- MUST use deterministic local word splitting for this window: Unicode
  whitespace separates words; punctuation is ignored at word boundaries; model
  or provider tokenizers MUST NOT be used for the local contradiction window;
- MUST be deterministic when provider enrichment is disabled;
- MAY use provider-guarded entity extraction only after redaction, and provider
  output MUST NOT override trusted adapter-supplied execution state.

Query construction:

- For `CONTINUATION`, the hot-path retrieval query SHOULD be built primarily
  from execution state (`goal`, `current_step`, `active_entities`,
  `last_tool_output_summary`) rather than the raw short message alone.
- For `SWITCH` and `NEW_TASK`, the current user message and extracted entities
  SHOULD be included so retrieval pivots to the new topic.
- For `CLARIFICATION`, recent assistant/tool output entities SHOULD be included
  so retrieval can explain or expand the previous result.
- If the adapter supplies an explicit `retrieval.query`, Mneme MAY use it, but
  traces SHOULD still record classifier signals and `query_built_from`.

Routing modes:

- `general`: balanced similarity, recency, dependency, and type weighting.
- `reasoning`: increases graph/dependency contribution.
- `factual`: increases semantic similarity and recency.
- `debugging`: increases recency and tool-output type weighting.

`context_search` and `/v1/context/prepare` MAY accept a routing mode. If no
mode is supplied, use `retrieval.routing.default_mode`. The selected mode and
score breakdown SHOULD be visible in traces when debug detail is enabled.

Delta extraction for `CONTINUATION` messages is optional in v0. If enabled, it
MUST produce `mneme.entity_modifier.v0` objects and follow these rules:

- Automatic v0 delta extraction may update only `active_entities`.
- `remove <entity>`, `delete <entity>`, `without <entity>`, and `no <entity>`
  create `REMOVE` modifiers when `<entity>` matches an active entity.
- `replace <old> with <new>`, `use <new> instead of <old>`, and
  `<new> instead of <old>` create a `REPLACE` modifier.
- `add <entity>`, `include <entity>`, and `use <entity>` create `ADD`
  modifiers unless the same span is already part of a replacement rule.
- `must <phrase>`, `needs to <phrase>`, `should <phrase>`, `ensure <phrase>`,
  and `make it <phrase>` create `CONSTRAINT` modifiers.
- Conflicts in the same message resolve in this order:
  `REPLACE` -> `REMOVE` -> `CONSTRAINT` -> `ADD`.
- All extracted spans MUST be redacted before being persisted in traces or
  state history. Provider-assisted extraction is allowed only when explicitly
  configured and MUST fall back to the deterministic rules above.
- Trusted adapter-supplied state remains authoritative. Automatic modifiers
  are discarded when they conflict with a trusted adapter update in the same
  turn.

### 14.6 Segments

Required:

- `POST /v1/segments/start`
- `POST /v1/segments/{segment_id}/close`
- `GET /v1/segments`
- `GET /v1/segments/{segment_id}`
- `GET /v1/segments/{segment_id}/events`
- `POST /v1/tools/list_segments`

Automatic segmentation is a Mneme core feature for runtime-neutral topic
quality. Adapters MUST also have a way to mark task boundaries explicitly when
the host knows a task has changed.

Automatic segmentation triggers:

- explicit switch intent (`SWITCH`) from Section 14.5.1 closes the current
  active segment and opens a new one synchronously;
- embedding drift above `segmentation.drift_threshold` after at least
  `segmentation.min_centroid_events` indexed user-message embeddings in the
  active segment opens a new segment with drift reason `EMBEDDING_DRIFT`;
- adapter-supplied tool-domain shift metadata MAY open a new segment when
  `segmentation.tool_domain_shift_enabled=true`;
- adapters may explicitly call `POST /v1/segments/start` when they have a
  stronger host lifecycle signal.

Drift score:

```text
drift_score =
  w_embedding * embedding_distance
  + w_topic_entropy * topic_entropy
  + w_tool_domain * tool_domain_shift_score
```

The weights come from `segmentation.drift_weights` in this order. Components
MUST be normalized to `[0, 1]` before scoring:

- `embedding_distance`: cosine-style distance from the redacted current
  user-message embedding to the active segment centroid. If embeddings are
  unavailable, this component is `0` and the trace records degradation.
- `topic_entropy`: deterministic normalized entropy of topic tags or retrieved
  evidence buckets over the recent segment window. If the daemon has no topic
  tags/buckets, this component is `0`; topic entropy is not required to block
  v0 ingestion.
- `tool_domain_shift_score`: `1.0` when trusted adapter metadata reports a
  domain shift for recent tool activity, otherwise `0.0`.

An implementation MUST roll over when either direct `embedding_distance` or
the combined `drift_score` exceeds `segmentation.drift_threshold`, subject to
`min_centroid_events`.

Tool-domain guidance for adapters:

- adapters SHOULD label tool calls with `metadata.tool_domain` when practical;
- recommended domains are `code`, `filesystem`, `git`, `research`, `data`,
  `communication`, `browser`, and `memory`;
- a tool-domain shift is present when the latest trusted tool domain differs
  from the dominant recent domain in the active segment and the adapter believes
  that difference reflects a task boundary, not a normal substep;
- Mneme MUST treat this as a trusted signal only when it comes from an adapter
  principal allowed to write event metadata for the session.

Centroid behavior:

- segment centroid calculation uses redacted, indexed user-message embeddings
  assigned to the active segment;
- cold-start segments with fewer than `min_centroid_events` MUST NOT roll over
  solely due to embedding drift;
- provider failures MUST degrade segmentation gracefully and leave the current
  segment active with a warning/trace, not block event ingestion.

When automatic segmentation rolls over a segment, Mneme MUST emit a redacted
`SEGMENT_DRIFT` trace containing intent, drift reason, closed/opened segment
ids, event counts, and warnings. Raw user/tool text MUST NOT be embedded in the
trace.

`GET /v1/segments` query parameters:

- `session_id`: optional; when supplied, list only that session.
- `scope`: `SESSION`, `PROJECT`, or `GLOBAL`; default `SESSION` when
  `session_id` is supplied, otherwise `PROJECT`.
- `project_isolation_key`: optional narrowing filter; cannot expand caller
  scope.
- `status`: optional segment status filter.
- `page_size` and `page_token`: required pagination controls.

`GLOBAL` segment listing is limited to sessions visible to the authenticated
principal and MUST NOT bypass project isolation.

`GET /v1/segments` response:

```json
{
  "segments": [
    {
      "schema_version": "mneme.segment.v0",
      "segment_id": "segment-004",
      "session_id": "session-123",
      "project_isolation_key": "repo-name",
      "title": "Hermes ContextEngine PR",
      "summary": "Work on native context-engine hooks.",
      "status": "OPEN",
      "outcome": null,
      "started_at": "2026-06-21T12:00:00Z",
      "closed_at": null,
      "anchor_event_ids": ["event-010"],
      "event_count": 12,
      "last_event_id": "event-021",
      "created_by": "ADAPTER",
      "metadata": {}
    }
  ],
  "next_page_token": null
}
```

`GET /v1/segments/{segment_id}/events` returns paginated
`mneme.event_summary.v0` objects for a segment under caller scope:

```json
{
  "events": [
    {
      "schema_version": "mneme.event_summary.v0",
      "event_id": "event-010",
      "session_id": "session-123",
      "turn_id": "turn-002",
      "type": "TOOL_OUTPUT",
      "role": "TOOL",
      "timestamp": "2026-06-21T12:05:00Z",
      "importance": "NORMAL",
      "freshness": "RECENT",
      "snippet": "pytest failed with AssertionError",
      "redaction_applied": true
    }
  ],
  "next_page_token": null
}
```

Segment start request:

```json
{
  "schema_version": "mneme.segment_start.v0",
  "session_id": "session-123",
  "segment_id": "segment-004",
  "title": "Hermes ContextEngine PR",
  "summary": "Work on native context-engine hooks.",
  "anchor_event_ids": ["event-010"],
  "provenance": {
    "event_id": "event-010",
    "turn_id": "turn-002"
  }
}
```

Segment close request:

```json
{
  "schema_version": "mneme.segment_close.v0",
  "session_id": "session-123",
  "closed_at": "2026-06-21T12:30:00Z",
  "summary": "Finished parity investigation.",
  "outcome": "COMPLETED",
  "anchor_event_ids": ["event-010", "event-099"],
  "provenance": {
    "event_id": "event-099",
    "turn_id": "turn-003"
  }
}
```

`summary`, `outcome`, and `anchor_event_ids` are optional. `session_id` is
required to prevent cross-session close mistakes when segment ids are
adapter-generated. If `anchor_event_ids` are supplied, Mneme MUST create or
update `SEGMENT_ANCHOR` graph edges for visible events in the same session.

`GET /v1/segments/{segment_id}` returns `mneme.segment.v0` metadata without the
full event list. `GET /v1/segments` is the direct REST equivalent of
`list_segments`; `POST /v1/tools/list_segments` remains the tool-envelope path.

### 14.7 Trace And Cost Endpoints

Required:

- `GET /v1/traces/{trace_id}`
- `GET /v1/costs/session/{session_id}`

Adapters SHOULD retain `trace_id` values returned by context preparation and
memory tools. `GET /v1/traces/{trace_id}` is the canonical way to inspect a
known trace. A future trace-search endpoint MAY be added, but v0 does not
require reverse lookup from arbitrary event ids.

`GET /v1/costs/session/{session_id}` returns `mneme.cost_report.v0`.

### 14.8 Maintenance Endpoints

Required:

- `POST /v1/maintenance/blob-gc`
- `POST /v1/maintenance/reindex`
- `GET /v1/maintenance/reindex/{job_id}`
- `POST /v1/maintenance/reindex/{job_id}/cancel`

`POST /v1/maintenance/blob-gc` request:

```json
{
  "scope": "PROJECT",
  "project_isolation_key": "repo-name",
  "session_id": null,
  "dry_run": true
}
```

Authorization:

- `OWNER` with `all-projects` may run daemon-wide maintenance.
- Scoped adapter tokens may run maintenance only for visible
  `project_isolation_key` or `session_id`.
- Unscoped daemon-wide GC requests from scoped tokens return `403 FORBIDDEN`.

Blob GC response includes `candidate_count`, `deleted_count`, `skipped_count`,
`dry_run`, and warnings.

`POST /v1/maintenance/reindex` triggers background embedding/search index
repair for events with `embedding_status` in `PENDING` or `FAILED`, or for all
events when `force=true` and the caller is authorized.

Request:

```json
{
  "scope": "PROJECT",
  "project_isolation_key": "repo-name",
  "session_id": null,
  "statuses": ["PENDING", "FAILED"],
  "force": false,
  "max_job_events": 10000
}
```

Response:

```json
{
  "schema_version": "mneme.reindex_job.v0",
  "job_id": "reindex-001",
  "scope": "PROJECT",
  "project_isolation_key": "repo-name",
  "statuses": ["PENDING", "FAILED"],
  "status": "QUEUED",
  "created_at": "2026-06-21T12:00:00Z",
  "started_at": null,
  "completed_at": null,
  "progress": {
    "candidate_count": 100,
    "processed_count": 0,
    "failed_count": 0
  },
  "error": null
}
```

`GET /v1/maintenance/reindex/{job_id}` returns `mneme.reindex_job.v0` with
updated status and progress. Unknown or out-of-scope jobs return `404
NOT_FOUND`.

`POST /v1/maintenance/reindex/{job_id}/cancel` requests cooperative
cancellation for a queued, waiting, or running reindex job. It returns the
updated `mneme.reindex_job.v0`. Completed jobs remain `COMPLETED`; already
cancelled jobs remain `CANCELLED`. Cancellation MUST stop future provider
requests and future background writes after the current micro-transaction
finishes.

Status values:

- `QUEUED`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`
- `WAITING_FOR_PROVIDER`

Reindex jobs MUST respect provider configuration and cost mode. If embeddings
are required but the provider is unavailable, return `503 PROVIDER_UNAVAILABLE`
when `maintenance.reindex.enqueue_when_provider_unavailable=false` (the
default). If delayed provider jobs are explicitly enabled, the job may be
created with `WAITING_FOR_PROVIDER`; it MUST NOT consume foreground write queue
capacity until the provider is healthy. `WAITING_FOR_PROVIDER` jobs expire or
fail after `maintenance.reindex.provider_wait_timeout_seconds` unless the owner
extends or requeues them.

Failed embedding/index writes SHOULD be retried automatically with provider
client retry settings and exponential backoff. Manual reindex is for forced or
bulk repair, not the only path for transient provider failures.

Background reindex, embedding, enrichment, and retention jobs MUST run at lower
priority than foreground event ingestion, state updates, and turn completion.
On writer-lane pressure, background work pauses or backs off before foreground
writes receive `429`/`503`. Foreground starvation during background maintenance
is a compliance failure.

Background jobs MUST use micro-transactions no larger than
`maintenance.reindex.max_events_per_transaction` for reindex-like writes and
MUST yield at least `maintenance.reindex.yield_between_transactions_ms`
between write transactions when foreground traffic is present. This is the
priority mechanism; SQLite itself has no writer-priority lock.

Provider calls from background reindex/backlog drain MUST be throttled by
`maintenance.reindex.provider_max_requests_per_minute` or a stricter
provider-specific limit. Circuit breakers MUST avoid dumping a large accumulated
`PENDING` backlog into a provider immediately after recovery.
The normative default circuit breaker opens when at least
`provider_circuit_breaker_min_calls` have been attempted and the recent failure
ratio reaches `provider_circuit_breaker_failure_ratio`; it remains open for
`provider_circuit_breaker_open_seconds`, then enters half-open with at most
`provider_circuit_breaker_half_open_requests` trial requests. After recovery,
backlog drain MUST start at no more than
`provider_recovery_ramp_initial_requests_per_minute` and ramp up gradually to
`provider_max_requests_per_minute` only while provider calls succeed.

### 14.9 Memory Tool Parity Endpoints

Required REST tool endpoints:

- `POST /v1/tools/resolve_session`
- `POST /v1/tools/list_sessions`
- `POST /v1/tools/context_search`
- `POST /v1/tools/fetch_event`
- `POST /v1/tools/expand_context`
- `POST /v1/tools/recall_recent`
- `POST /v1/tools/list_segments`
- `POST /v1/tools/get_execution_state`
- `POST /v1/tools/get_goal_history`
- `POST /v1/tools/explain_context`
- `POST /v1/tools/mneme_cost_report`

All return the shared tool envelope:

```json
{
  "ok": true,
  "data": {},
  "trace_id": "trace-001",
  "session_resolution": {
    "session_id": "session-123",
    "source": "EXPLICIT_ARGUMENT"
  },
  "warnings": []
}
```

`session_resolution` is optional for non-session-bound tools and required for
session-bound tools. `session_resolution.source` values:

- `EXPLICIT_ARGUMENT`: caller supplied `session_id`.
- `TRUSTED_DEFAULT`: MCP/server used immutable process or initialize metadata.
- `HOST_INJECTED`: trusted host proxy/middleware injected the session per call.
- `RESOLVED_BY_TOOL`: tool result comes from `resolve_session` or
  `list_sessions` recovery.

REST and MCP session-bound tools accept the same Mneme `session_id` values.
For example, `019edb86-1d22-78a3-b9e4-e6121c294056` is a valid external
Codex/Mneme session id format for both REST and MCP when the caller is
authenticated. If MCP succeeds for a session and direct REST returns
`401 UNAUTHENTICATED`, the session id format is not the suspected cause; the
REST caller must configure the same bearer token boundary used by the MCP
process.

### 14.10 Session Discovery

`resolve_session` input:

```json
{
  "session_id": null,
  "project_path": "/repo/my-project",
  "thread_id": "codex-thread-id",
  "slug": "my-project",
  "query": "my project",
  "project_isolation_key": "repo-name",
  "limit": 10,
  "page_token": null
}
```

Output:

```json
{
  "resolved_session_id": "session-123",
  "resolution": "SINGLE_MATCH",
  "best_guess_session_id": "session-123",
  "matches": [],
  "next_page_token": null,
  "matches_truncated": false
}
```

Resolution values:

- `EXACT_SESSION_ID`
- `SINGLE_MATCH`
- `AMBIGUOUS`
- `NOT_FOUND`

`AMBIGUOUS` and `NOT_FOUND` MAY return `ok=true` with warnings for tool-level
recovery. REST may still use `404` for direct session-bound operations.

`best_guess_session_id` semantics:

- `EXACT_SESSION_ID`: duplicate `resolved_session_id`.
- `SINGLE_MATCH`: duplicate `resolved_session_id`.
- `AMBIGUOUS`: MAY contain the safest candidate if one is clearly preferred.
- `NOT_FOUND`: MUST be `null`.

For `AMBIGUOUS`, "clearly preferred" is deterministic: sort visible
candidates by exact `thread_id` match, exact normalized `project_path` match,
exact `project_isolation_key` match, newest `started_at`/`updated_at`, then
stable `session_id`. `best_guess_session_id` MAY be returned only when the top
candidate is strictly ahead on at least one match dimension before recency; if
the tie reaches recency-only ordering, it MUST be `null`.

When ambiguous:

- warning code MUST be `SESSION_RESOLUTION_AMBIGUOUS`;
- agent guidance MUST say to call `list_sessions` with the same project filters
  or refine `project_path`, `thread_id`, or `slug`;
- results MUST be scoped and redacted.
- `best_guess_session_id` MAY be supplied only when one candidate is clearly
  best by exact thread, project path, or project isolation match. Recency alone
  is not enough. Agents MAY continue with this id only if their policy permits
  ambiguous recovery and they surface the warning; strict clients SHOULD ask
  for user confirmation or refine filters.

`list_sessions` MUST support `page_size`, `page_token`, and `next_page_token`.
It MUST never silently truncate without `next_page_token` or
`matches_truncated=true`.

### 14.11 Context Search

Search scopes:

- `SESSION`: current session only.
- `LINEAGE`: current session plus explicit lineage sessions visible to caller.
- `PROJECT`: all sessions sharing the effective project isolation key.
- `GLOBAL`: all sessions visible to the principal. For non-admin local tokens,
  this is normally equivalent to `PROJECT`.

`GLOBAL` MUST NOT bypass project isolation.

Search/routing parameters:

- `query`: caller-supplied query string. If omitted in `context/prepare`, Mneme
  builds a query from execution state and Section 14.5.1 intent.
- `mode`: optional `general`, `reasoning`, `factual`, or `debugging`; defaults
  to `retrieval.routing.default_mode`.
- `filters`: event type, time, segment, freshness, and adapter metadata filters
  where supported.

Candidate scoring MUST combine semantic similarity, recency, graph dependency,
and event type weighting:

```text
score(c) =
  w_semantic * semantic_similarity(c)
  + w_recency * recency_score(c)
  + w_dependency * dependency_score(c)
  + w_type * type_weight(c)
```

Default mode weights are:

| Mode | semantic | recency | dependency | type |
|---|---:|---:|---:|---:|
| `general` | 0.40 | 0.20 | 0.30 | 0.10 |
| `reasoning` | 0.35 | 0.15 | 0.40 | 0.10 |
| `factual` | 0.50 | 0.30 | 0.10 | 0.10 |
| `debugging` | 0.30 | 0.40 | 0.10 | 0.20 |

Component rules:

- all components MUST be normalized to `[0, 1]`;
- `semantic_similarity` comes from active embedding-model vector scoring when
  embeddings are available, or from a deterministic lexical fallback when the
  daemon advertises degraded retrieval;
- `recency_score` MUST be deterministic for the same event timestamp and query
  time, and MUST be monotonic with newer evidence scoring at least as high as
  older evidence before other factors;
- `dependency_score` comes from Section 12.8 graph traversal and is `0` when
  no relevant graph path is found;
- `type_weight` is a deterministic event-type boost/penalty table, advertised
  in capabilities or trace metadata when it differs from the default.

The selected `mode` changes only these weights and MUST NOT bypass
project/session scope. Debug traces SHOULD include per-candidate score
breakdowns when enabled. A score breakdown object has this shape:

```json
{
  "event_id": "event-123",
  "mode": "reasoning",
  "final_score": 0.82,
  "components": {
    "semantic_similarity": 0.70,
    "recency_score": 0.50,
    "dependency_score": 1.0,
    "type_weight": 0.75
  },
  "weights": {
    "semantic_similarity": 0.35,
    "recency": 0.15,
    "dependency": 0.40,
    "type_weight": 0.10
  },
  "scope_applied": "SESSION",
  "embedding_model_id": "text-embedding-3-small"
}
```

### 14.12 Expand Context

Traversal algorithm MUST be deterministic.

Modes:

- `TOOL_CHAIN`: BFS over `TOOL_RESULT`, `TOOL_INPUT`, parent/child edges, seed
  first, then tool call, tool output, downstream decisions.
- `CAUSAL`: BFS over parent/child and decision edges by edge weight then time.
- `TEMPORAL`: seed, previous events, next events by timestamp.
- `SEGMENT`: segment anchors, segment skeleton, then member events by
  importance and time.

Traversal hard limits:

- Every traversal MUST track visited event ids and MUST NOT revisit a node.
- `retrieval.graph.max_traversal_steps` limits the number of visited nodes,
  regardless of `max_events`.
- `retrieval.graph.max_frontier_size` limits queued nodes waiting for
  expansion.
- `retrieval.graph.max_branching_factor` limits the number of outgoing edges
  expanded per node after deterministic sorting by edge weight, timestamp, and
  event id. This prevents high-degree edges such as broad `PARENT_CHILD`,
  `FOLLOWS`, or `MEMORY_READ_EVIDENCE` fan-out from consuming the traversal.
- When any traversal hard limit is reached, return the selected results so far,
  set `truncated=true`, and include warning `TRAVERSAL_LIMIT_REACHED` with the
  limit name and count. The daemon MUST NOT continue searching unboundedly
  after filling `max_events`.

When `max_events` is reached:

- return `truncated=true`;
- include warning `RESULT_TRUNCATED`;
- include `dropped_count` and traversal frontier summary when possible.

### 14.13 Context Prepare

Required for deep adapters:

- `POST /v1/context/prepare`

Validation:

- `budget_tokens > 0`
- `budget_tokens <= context_window_tokens`
- `request_messages` use `mneme.message.v0`
- `budget_split` contains only canonical keys:
  `headroom_ratio`, `execution_state_ratio`, `protected_tail_ratio`,
  `retrieved_evidence_ratio`, and `hints_ratio`
- `budget_split` values are non-negative and sum to `1.0 +/- 0.01`

Headroom canonical field:

- `policy.budget_split.headroom_ratio` is canonical.
- `policy.headroom_ratio` is deprecated and MUST be rejected or normalized with
  warning `DEPRECATED_FIELD_NORMALIZED`.
- If both are present and differ, default behavior is to use the canonical
  `policy.budget_split.headroom_ratio`, ignore the deprecated field, and emit
  `DEPRECATED_FIELD_NORMALIZED`. Strict schema clients MAY request
  `422 VALIDATION_ERROR` for this conflict.

Budget packing algorithm:

1. Estimate or accept exact token counts.
2. Reserve `minimum_headroom_tokens` first as a hard reserve for tokenizer
   variance and expected completion tokens. Prompt slots MUST NOT consume this
   minimum reserve.
3. Preserve system/developer authority messages if requested and within hard
   budget.
4. Preserve the latest user-authored message in the current request. If
   multiple user messages are present, preserve the newest user message as the
   latest request and treat earlier user messages as recent tail candidates.
   If no user-authored message exists, this step is a no-op,
   `latest_user_message_preserved=false`, and the request is not invalid solely
   for lacking a user message.
   The current latest user request MUST NOT be best-effort truncated or
   silently dropped. If it cannot fit with authority messages and
   `minimum_headroom_tokens`, return `422 VALIDATION_ERROR` with
   `details.reason=LATEST_USER_MESSAGE_EXCEEDS_BUDGET`.
5. Build execution-state block under its fixed target share; if too large,
   compress to `FULL`, `COMPACT`, `MINIMAL`, or `TRUNCATED`. The chosen level
   MUST be returned in `trace.execution_state_compression_level` so adapters can
   reason about degraded state detail.
6. Build protected recent tail as whole messages/turn units from newest to
   oldest, excluding the protected latest user request from step 4. Historical
   tail messages may be truncated only when the caller allows text truncation;
   default best-effort truncation applies to historical tail text, not to the
   current latest user request. Strict callers MAY request
   `422 VALIDATION_ERROR`; callers MAY explicitly allow dropping oversized
   non-authority historical tail messages.
7. Cascade unused prompt budget before building evidence:
   - unused execution-state budget flows to protected recent tail;
   - unused protected-tail budget flows to retrieved evidence;
   - unused retrieved-evidence budget remains unused slack after evidence
     packing. It may make the final unused budget larger than
     `minimum_headroom_tokens`, but it is not consumed as part of the hard
     headroom reserve.
8. Build retrieved evidence from selected candidates under its fixed slot plus
   cascaded unused prompt budget.
9. Drop whole retrieved evidence items before dropping protected tail.
10. Add optional memory hints, goal trail, and checkpoint hints only if budget
   remains in their own slot. Hints MUST NOT consume
   `minimum_headroom_tokens`.
11. Verify final projected tokens plus `minimum_headroom_tokens` fit hard
   budget. If even system/developer authority messages, the unmodified latest
   user message, and minimal execution state cannot fit after safe truncation
   of historical tail/evidence, return `422 VALIDATION_ERROR` with
   `details.reason=MINIMUM_REQUIRED_CONTENT_EXCEEDS_BUDGET`.
12. Emit trace with selected/dropped refs and reasons, including any cascaded
    budget amounts, `minimum_headroom_tokens`, and final
    `unused_context_slack_tokens`.

Priority when over budget:

1. System/developer authority.
2. Latest user request.
3. Minimal execution state.
4. Protected recent tail.
5. Retrieved evidence.
6. Hints/checkpoint/goal trail.

Warnings:

- `REQUEST_UNDER_BUDGET`
- `CONTEXT_COLLISION_BUDGET_EXCEEDED`
- `EXECUTION_STATE_TRUNCATED`
- `RECENT_TAIL_TRUNCATED`
- `RETRIEVED_CONTEXT_DROPPED`
- `COST_MODE_DOWNGRADED`
- `PROVIDER_DEGRADED`
- `DEPRECATED_FIELD_NORMALIZED`

### 14.14 Evidence Freshness

Every retrieval result and selected context evidence item SHOULD include
`freshness`.

Freshness values:

- `CURRENT`: supplied by a host adapter that has just verified the source of
  truth, such as current file content, current git state, or a just-ingested
  host event.
- `RECENT`: recent session evidence that has not been externally revalidated.
- `HISTORICAL`: older evidence useful for rationale/history.
- `STALE_OR_CONFLICTING`: conflicts with current source evidence.
- `UNKNOWN`: source freshness cannot be determined.

Conflict rule:

- `CURRENT` evidence wins over Mneme memory only when the adapter/source
  connector explicitly supplies the current evidence and either marks memory
  evidence as conflicting or provides `conflicting_event_ids`/equivalent
  structured conflict metadata.
- Context traces MUST include `FRESHNESS_CONFLICT` when memory evidence is
  dropped or downgraded because supplied current source evidence explicitly
  conflicts with it.
- Mneme core MUST NOT claim to independently verify current filesystem or git
  state unless a host adapter or source connector explicitly supplies that
  evidence during the request.
- Without adapter/source freshness signals, Mneme MAY derive `RECENT` or
  `HISTORICAL` from timestamps, but MUST NOT automatically mark old evidence as
  `STALE_OR_CONFLICTING`.

## 15. MCP Tool Contract

MCP tools proxy REST. REST remains canonical.

Required MCP tools:

- `resolve_session`
- `list_sessions`
- `context_search`
- `fetch_event`
- `expand_context`
- `recall_recent`
- `list_segments`
- `get_execution_state`
- `get_goal_history`
- `explain_context`
- `mneme_cost_report`

MCP v0 is read-oriented. It MUST NOT expose model-callable write tools unless a
future write contract is approved. The `TOOLS_ONLY` write gap is a known v0
product limitation: trusted hooks/importers write through REST, while a future
`append_insight`/`save_decision` MCP tool requires a separate approval model,
threat model, and audit contract before it can be added.

Tool versioning:

- MCP tool names remain unversioned in v0 for usability.
- Each tool result MUST include `schema_version` in `data` where applicable.
- `/v1/capabilities` MUST expose `mcp_tool_versions`.
- Backward-compatible changes SHOULD negotiate through capabilities and
  response/request `schema_version`, not by renaming tools.
- Breaking future changes MUST either add new tool names, e.g.
  `context_search_v2`, or negotiate via explicit schema version only when old
  clients can safely reject unsupported versions. A gateway MUST NOT silently
  change semantics behind an unchanged MCP tool name.

MCP error mapping:

| REST status | MCP `error.code` | Tool result |
|---:|---|---|
| 400 | `BAD_REQUEST` | `ok=false` |
| 401 | `UNAUTHENTICATED` | `ok=false` |
| 403 | `FORBIDDEN` | `ok=false` |
| 404 | `NOT_FOUND` | `ok=false` except recoverable discovery outcomes |
| 409 | `CONFLICT` | `ok=false` |
| 413 | `PAYLOAD_TOO_LARGE` | `ok=false` |
| 422 | `VALIDATION_ERROR` | `ok=false` |
| 429 | `RATE_LIMITED` | `ok=false`, `retryable=true` |
| 503 | `PROVIDER_UNAVAILABLE` | `ok=false`, `retryable=true` |
| 500 | `INTERNAL_ERROR` | MCP transport error or `ok=false` depending on server state |

Additional MCP/domain error codes:

- `DEFAULT_SESSION_STALE`: trusted immutable default session id was configured
  but no longer exists or is outside caller scope. The model MUST NOT interpret
  this as "memory is empty"; the host adapter must refresh or recreate the
  session. This is MCP-only and has no REST/HTTP equivalent; direct REST
  callers receive the normal `404 NOT_FOUND` for missing sessions.

MCP startup MUST NOT require tokens in argv. Use environment, token file, or
owner-only env file.

Session friction mitigation:

- MCP server instructions MUST tell the model to resolve sessions before
  session-bound calls when no trusted session id exists.
- Host adapters that know the current project/session MUST launch MCP with a
  default project/session context or inject it into tool calls before reaching
  the model. The model should not spend routine calls rediscovering a session
  the host already knows.
- The MCP server MUST NOT keep a mutable global "current session" that can
  silently drift when the user switches projects. Default context is valid only
  when supplied as trusted immutable process/run configuration or when injected
  per call by the host adapter before the model-visible tool call reaches
  Mneme.
- Trusted immutable process/run configuration MAY be supplied through
  environment variables such as `MNEME_MCP_DEFAULT_SESSION_ID` and
  `MNEME_MCP_DEFAULT_PROJECT_KEY`, through MCP `initialize` metadata when the
  host transport supports immutable per-server metadata, or through a host
  proxy that rewrites tool arguments per call before they reach Mneme.
- Per-call host injection SHOULD be implemented by a trusted host proxy or
  middleware that adds `session_id` and `project_isolation_key` to the tool
  arguments before the call reaches the Mneme MCP server. Tool responses SHOULD
  include `session_resolution.source="HOST_INJECTED"` for audit/debugging.
- If a long-lived MCP process serves multiple projects, it MUST use per-call
  host injection or require explicit `session_id`; it MUST NOT update a shared
  mutable default session at runtime.
- If the host changes project/session and relies on immutable process config,
  it MUST restart the MCP process with the new config.
- When trusted immutable default context is configured, session-bound MCP tools
  MUST accept omitted `session_id` and fill it from that context. The response
  MUST include the resolved `session_id`.
- MCP startup or first session-bound tool call MUST verify the configured
  default session via authenticated readiness or `GET
  /v1/sessions/{session_id}`. `POST /v1/readiness/session` is required when the
  adapter also needs evidence availability; `GET /v1/sessions/{session_id}` is
  sufficient for default-session existence/scope validation. If missing, return
  `DEFAULT_SESSION_STALE` with discovery guidance instead of silently treating
  results as empty.
- If a trusted current session is available, MCP MAY expose `get_current_session`
  as a compatible addition. `resolve_session` and `list_sessions` remain
  required for ambiguous or cross-session workflows.

## 16. Audit, MEMORY_READ, And Traces

Every memory read MUST create durable audit evidence unless the daemon was
started in an explicit test-only unaudited mode.

Default behavior:

- `context_search`, `fetch_event`, `expand_context`, `recall_recent`,
  `get_execution_state`, `get_goal_history`, `list_segments`,
  `explain_context`, and `mneme_cost_report` create traces.
- Direct memory tools create `MEMORY_READ` events by default.
- `/v1/context/prepare` MAY use its trace audit entry instead of creating a
  canonical `MEMORY_READ` event, to avoid retrieval pollution.
- Retrieval filters exclude `MEMORY_READ` by default.
- Direct `MEMORY_READ` events SHOULD update
  `execution_state.last_tool` and `last_tool_output_summary` with a redacted
  summary of the memory action/result, and SHOULD create graph edges from the
  memory-read event to selected evidence event ids. This preserves the Hermes
  tool-result feedback loop without making MCP a model-callable write surface.
- `last_tool_output_summary` for memory reads MUST be bounded and redacted. The
  default format is:
  `memory_read:<tool_name> results=<count> top_event=<event_id|null> top_type=<type|null> top_excerpt=<redacted_excerpt>`.
  `top_excerpt` is the first sentence of the top result snippet, or the first
  50 tokens when sentence splitting is unavailable, and the whole summary MUST
  fit within 120 tokens by default.
- Memory-read graph links MUST use edge type `MEMORY_READ_EVIDENCE` with the
  Section 12.8 default weight. These edges connect the `MEMORY_READ` event to
  evidence returned or expanded for the caller; they do not make the evidence
  writable by MCP.
- Host adapters that separately capture model-visible MCP tool calls SHOULD
  ingest those host transcript tool calls/results as ordinary `TOOL_CALL` and
  `TOOL_OUTPUT` events through REST. If they do, Mneme must deduplicate or link
  them to the corresponding `MEMORY_READ` trace rather than double-counting
  evidence.

Audit modes are daemon configuration, not a public request bypass:

- `FULL`: trace plus audit plus direct `MEMORY_READ` when applicable.
- `TRACE_ONLY`: trace/audit record, no canonical memory-read event.
- `DISABLED_TEST_ONLY`: only available when the daemon starts with a test-only
  environment/config flag such as `MNEME_ALLOW_UNAUDITED_TOOLS_FOR_TESTS=true`.

Production configs MUST reject `DISABLED_TEST_ONLY`. Public REST/MCP requests
MUST NOT be able to disable audit per call.

## 17. Security And Privacy

### 17.1 Threat Model

In scope:

- malicious local project dependencies reading process args/env;
- malicious tool output stored in memory;
- prompt injection inside retrieved evidence;
- cross-project metadata leakage;
- accidental secrets in logs, tool outputs, env dumps, diffs, and transcripts;
- provider requests receiving unredacted content;
- stale or conflicting evidence from memory versus current files;
- filesystem access to SQLite and blobs by local user processes.

Out of scope for v0:

- enterprise multi-user RBAC;
- hostile OS account with full access to the user's files;
- remote hosted multi-tenant deployment;
- perfect LLM immunity to prompt injection.

### 17.2 Redaction

Redaction MUST run before:

- persistence;
- indexing;
- embeddings;
- reranking;
- LLM enrichment;
- traces;
- logs;
- MCP/REST output.

Default redaction profile MUST include:

- `Authorization:` and `Proxy-Authorization:` headers;
- `Bearer <token>`;
- OpenAI-style `sk-...` keys;
- GitHub `ghp_`, `github_pat_`, `gho_`, `ghu_`, `ghs_`, `ghr_` tokens;
- AWS access keys matching `AKIA...` / `ASIA...`;
- Google API key patterns such as `AIza...`;
- private key PEM blocks;
- database URLs with credentials;
- URLs containing username/password credentials;
- JWT-like three-part base64url tokens when high confidence;
- `.env` style assignments for names containing `KEY`, `TOKEN`, `SECRET`,
  `PASSWORD`, `PASS`, `CREDENTIAL`, `PRIVATE`, `COOKIE`;
- caller-marked sensitive JSON fields.

Redaction performance and failure behavior:

- Redaction MUST use bounded-time regex/pattern engines or equivalent scanning
  logic. Implementations MUST avoid patterns with unbounded catastrophic
  backtracking on `max_event_content_bytes` inputs.
- `indexing.max_redaction_time_ms` bounds the synchronous redaction budget for
  one event/blob text extraction in the foreground path.
- If redaction exceeds the configured budget, the daemon MUST NOT persist
  unredacted plaintext silently. It MUST either reject the item with
  `422 REDACTION_TIMEOUT`, store only safe metadata plus a content hash, or
  mark the item as `ingestion.degraded=true` with `redaction_scope=METADATA_ONLY`
  when that behavior is explicitly advertised.
- Adapter guidance for `422 REDACTION_TIMEOUT`: retrying the same inline
  payload is expected to fail again. Adapters SHOULD split the payload into
  smaller events when semantic boundaries allow it, or upload it as a
  `BYTES_REF` blob and ingest metadata/reference content instead. Binary or
  opaque blob bytes use metadata-only redaction by default unless an explicit
  safe text extraction policy is configured.
- `source_trust=HOST_AUTHORED` does not bypass default redaction in v0.

Redaction output format:

- apply specific high-confidence patterns before generic token/secret patterns;
- apply multiline private-key and credential block patterns before line-oriented
  `.env` assignment patterns;
- replace content with `[REDACTED:TOKEN]`, `[REDACTED:SECRET]`, or another
  neutral class that does not expose provider-specific prefixes by default;
- record redaction metadata with internal kind, field, and hash of original
  where safe;
- never store reversible secrets by default.

False positives/negatives:

- The spec acknowledges regex redaction is imperfect.
- Reviewers and users MUST NOT treat redaction as a substitute for project-level
  secret hygiene.
- Provider privacy docs MUST state exactly what is sent to configured external
  providers.

Binary blob caveat:

- Text/JSON redaction applies to textual event content, metadata, headers, and
  text-like blob media types before persistence.
- Non-text binary blob bytes, such as images, PDFs, archives, and compiled
  binaries, cannot be safely redacted by the default regex redactor.
- Adapters are responsible for not uploading sensitive binary artifacts unless
  the user/project policy permits it.
- Mneme MUST redact binary blob metadata where possible, MUST NOT extract text
  from or send non-text blob bytes to embeddings/rerankers/LLM providers unless
  an explicit extractor policy is configured, and MUST mark such blobs as
  `redaction_scope=BINARY_METADATA_ONLY` or equivalent metadata.

### 17.3 Prompt Injection Through Memory

Retrieved memory is evidence, not instruction authority.

Mitigations required:

- Retrieved evidence blocks MUST be rendered with clear labels and provenance.
- Tool/web/file outputs MUST carry `source_trust` labels.
- The context assembler MUST NOT put untrusted evidence into system/developer
  role messages.
- Evidence text MUST be wrapped in a strict data-only structure, preferably XML
  or JSON. Example:

```xml
<mneme_untrusted_evidence event_id="event-001" source_trust="UNTRUSTED_TOOL_OUTPUT">
...literal evidence text...
</mneme_untrusted_evidence>
```

- Literal evidence text MUST be escaped for the selected wrapper format before
  rendering. XML wrappers MUST XML-escape text and attributes or use CDATA with
  correct `]]>` splitting. JSON wrappers MUST use JSON string encoding. Raw
  string interpolation into XML/JSON wrappers is forbidden. Unpredictable
  delimiters may be an additional defense but MUST NOT be the only escaping
  mechanism.
- If the host/provider supports a tool, data, or evidence channel, untrusted
  retrieved evidence MUST be placed there. If the host only supports ordinary
  chat roles, the adapter MUST keep evidence out of system/developer messages,
  include the data-only wrapper, and add a system/developer instruction that
  text inside `mneme_untrusted_evidence` is data to inspect, not instructions to
  execute.
- High-risk content MAY be summarized or flagged with
  `prompt_injection_risk=true`.
- The model-facing text MUST say evidence is untrusted data, but the spec does
  not claim this fully solves prompt injection.
- Host adapters MUST preserve current system/developer/user instructions above
  Mneme evidence.

### 17.4 At-Rest Protection

v0 local default uses SQLite for canonical records and server-owned blob bytes
without mandatory encryption.

Required guidance:

- document database path and any optional external blob paths;
- recommend filesystem permissions `0600` for SQLite/env/token files and `0700`
  for Mneme data directories;
- document optional SQLCipher or OS-encrypted volume strategy where available;
- do not claim enterprise confidentiality without encryption configuration.

FUTURE: first-class SQLCipher/keychain integration.

## 18. Storage, Migrations, And Concurrency

SQLite requirements:

- WAL mode SHOULD be enabled.
- `busy_timeout` MUST be set.
- Write transactions MUST be short.
- The reference daemon MUST serialize writes through one writer lane or an
  equivalent transaction queue. SQLite is single-writer; v0 must not rely on
  many independent write connections competing through retry loops.
- The writer lane SHOULD operate on batches. Adapter docs SHOULD recommend
  buffering high-volume event streams and sending `POST /v1/events` batches up
  to `max_batch_events` rather than one event per chunk.
- The writer lane MUST have a bounded queue. Queue depth MUST NOT exceed
  `daemon.max_writer_queue_depth`; excess foreground requests return
  `429 RATE_LIMITED` with `retryable=true`, and excess background writes are
  delayed or dropped according to their job policy.
- Background embedding/enrichment jobs MUST enqueue writes instead of competing
  directly with foreground ingestion.
- Foreground writes from event ingestion, turn completion, execution-state
  update, segment operations, and explicit user requests MUST have strict
  priority over background embedding, enrichment, reindex, retention, and GC
  writes. Background jobs MUST use bounded batch sizes and adaptive backoff so
  they do not starve active agents.
- Background jobs MUST perform SQLite writes in micro-transactions and yield
  between transactions when foreground work is queued. They MUST NOT use a
  long-running `BEGIN IMMEDIATE` transaction for a whole reindex/GC/retention
  job.
- Multipart ingest must respect `max_batch_total_blob_bytes` and
  `max_multipart_transaction_bytes`; oversized batches fail before storage
  mutation with `413 PAYLOAD_TOO_LARGE`. Implementations SHOULD also enforce
  `max_multipart_transaction_ms` as a foreground latency guard by rejecting or
  asking clients to split large requests before entering a long write
  transaction.
- If the writer queue is full or SQLite remains busy after bounded internal
  retries, return `429 RATE_LIMITED` or `503 STORAGE_BUSY` with
  `retryable=true`.
- Reads MUST not observe partially written batches.

Migration requirements:

- Store schema version in `PRAGMA user_version` and a `schema_migrations` table.
- `PRAGMA user_version` is the quick compatibility gate; `schema_migrations`
  records detailed migration history. On startup they MUST agree on the current
  schema version. If they diverge, the daemon MUST fail closed with
  `SCHEMA_VERSION_MISMATCH` and require backup/repair rather than guessing.
- Migrations MUST be ordered, idempotent, and tested from each supported
  previous version.
- Startup MUST refuse unknown newer schema versions.
- Startup MUST create a backup or require explicit `--no-backup-before-migrate`
  before destructive migrations.
- Release notes MUST include migration impacts.
- Startup integrity check MUST run by default (`startup_integrity_check=true`),
  using SQLite integrity checks and schema/version consistency checks. If
  corruption is detected, the daemon MUST fail closed for writes and either
  refuse startup or start in explicit read-only recovery mode with clear
  operator warnings.

Backup/restore:

- Backup MUST include SQLite. If an experimental filesystem blob driver is
  enabled, backup MUST also include the blob directory.
- Hot backup SHOULD use SQLite backup API.
- Restore MUST verify schema version, blob metadata, and blob hash integrity.
- `VACUUM`/checkpoint maintenance MAY be provided as explicit maintenance
  operations; they MUST NOT run unbounded while foreground agents are active.
  Bounded means each maintenance slice respects configured duration/page limits
  such as `maintenance.vacuum_max_duration_ms` and
  `maintenance.checkpoint_max_pages`, and yields when writer queue depth is
  non-zero.

Provider retry:

- Provider clients for embeddings, reranking, and LLM enrichment MUST support
  timeout plus bounded retry configuration.
- Transient provider failures SHOULD retry with exponential backoff and jitter
  before marking a derived item `FAILED`.
- Persistent failures MUST leave canonical events stored and mark derived
  provider status as `FAILED` or `PENDING_RETRY` with retry metadata.

CURRENT GAP: migration and backup/restore mechanisms must be added or explicitly
deferred before public stable release.

## 19. Operations And Deployment

Supported v0 deployment:

- local source checkout or package install;
- Python 3.11+; release notes MUST list tested Python versions;
- loopback HTTP and/or Unix socket;
- SQLite database;
- optional provider credentials.

Commands required for developer/core:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
.venv/bin/python -m pytest -q
mneme serve --config mneme.toml
mneme mcp --base-url http://127.0.0.1:8765
mneme benchmark --events 30 --db .local/mneme-benchmark.db
```

Safe service config:

- macOS launchd MAY be supported by adapter packages.
- Linux systemd and Windows service managers are not required for core v0, but
  docs MUST provide a manual foreground run path and clearly label supported
  service managers.
- Multi-machine setups MUST be per-machine for daemon, token, database, MCP
  config, provider secrets, and hook trust. Shared symlinked docs/skills do not
  imply shared runtime state.

Observability:

- `/v1/metrics` MUST expose either Prometheus text format or documented
  structured JSON metrics; the format MUST be advertised in capabilities or
  docs.
- Required metric families: request count/latency by endpoint/status, provider
  call count/failure/latency, writer queue depth, background job backlog,
  embedding pending/failed counts, reindex job status counts, retention sweep
  counts, blob storage bytes/count, and startup integrity status.
- Retrieval-intelligence metric families MUST include intent classification
  counters by label, segment rollover counters by reason, routing mode counters,
  and indexing-compression counters by event type.
- When a benchmark or dogfood evaluation run supplies ground-truth labels,
  Mneme SHOULD report retrieval quality metrics such as precision@k, recall@k,
  MRR, segment boundary accuracy, segment coherence, and intent-classification
  confusion counts in the benchmark output or a structured quality report.
  These metrics are not required for unlabeled ordinary runtime requests.
- Structured logs MUST include request id, trace id where applicable, endpoint,
  status/error code, project scope where safe, latency, and background job id.
- Logs MUST NOT include bearer tokens, provider secrets, or unredacted evidence
  content.

Config reload:

- v0 MAY require restart after config changes.
- If restart is required, docs MUST say so.
- In-flight request cancellation semantics MUST be documented for service
  stop/restart. Minimum v0 behavior: finish current request when possible,
  otherwise return retryable errors and leave canonical event ingestion
  idempotent for replay.

## 20. OpenAPI And SDK Readiness

The REST API MUST expose an OpenAPI schema at `/openapi.json`.

OpenAPI is the REST schema source of truth for implementation and SDK
generation. JSON snippets in this Markdown document are normative examples for
review readability; generated OpenAPI and contract tests must be kept in sync
with them before a release is considered compliant.

Requirements:

- schema includes all public REST endpoints;
- error envelopes are documented;
- security schemes are documented;
- examples include success and common failure cases;
- CI SHOULD validate that the generated schema is parseable;
- future SDKs SHOULD be generated or validated from this schema.

Markdown docs are not enough for adapter authors in other languages.

## 21. Errors And Warnings

REST error envelope:

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid event payload.",
    "retryable": false,
    "details": {
      "field": "events[0].event_id",
      "reason": "Required field is missing."
    },
    "trace_id": "trace-err-001",
    "request_id": "request-001"
  },
  "warnings": []
}
```

HTTP mapping:

| Status | Code | Meaning |
|---:|---|---|
| 400 | `BAD_REQUEST` | Malformed JSON or unsupported envelope. |
| 401 | `UNAUTHENTICATED` | Missing or invalid token/socket auth. |
| 403 | `FORBIDDEN` | Authenticated but outside project/session scope. |
| 404 | `NOT_FOUND` | Session, turn, event, blob, or trace does not exist. |
| 409 | `CONFLICT` | Idempotent id reused with incompatible payload. |
| 412 | `FAILED_PRECONDITION` | Authenticated request is valid, but a required readiness condition such as evidence availability is not met. |
| 413 | `PAYLOAD_TOO_LARGE` | Event, batch, or blob exceeds limits. |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | Unsupported upload or multipart content type. |
| 416 | `RANGE_NOT_SATISFIABLE` | Blob content byte range is invalid or unsatisfiable. |
| 422 | `VALIDATION_ERROR` | Semantically invalid payload or lifecycle state. |
| 429 | `RATE_LIMITED` | Local queue, SQLite busy timeout, or provider throttle. |
| 503 | `PROVIDER_UNAVAILABLE` | Required provider unavailable. |
| 503 | `STORAGE_BUSY` | SQLite/storage retry budget exhausted. |
| 500 | `INTERNAL_ERROR` | Unexpected service failure. |

Clients MUST inspect `error.code`, not HTTP status alone. In particular,
`503 PROVIDER_UNAVAILABLE` and `503 STORAGE_BUSY` have different retry causes
and operator actions even though they share a status code.

Example 409:

```json
{
  "ok": false,
  "error": {
    "code": "CONFLICT",
    "message": "event_id already exists with incompatible immutable fields.",
    "retryable": false,
    "details": {
      "event_id": "event-001",
      "field": "content.hash"
    }
  },
  "warnings": []
}
```

Example 413:

```json
{
  "ok": false,
  "error": {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "Inline content exceeds max_event_content_bytes; upload a blob and retry with BYTES_REF.",
    "retryable": false,
    "details": {
      "max_event_content_bytes": 1048576,
      "actual_bytes": 2097152,
      "retry_with": "POST /v1/blobs"
    }
  },
  "warnings": []
}
```

Example 413 for blob upload:

```json
{
  "ok": false,
  "error": {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "Blob upload exceeds max_blob_bytes=2097152.",
    "retryable": false,
    "details": {
      "max_blob_bytes": 2097152,
      "actual_bytes": 209715200
    }
  },
  "warnings": []
}
```

Example 422 for latest user request over budget:

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Latest user message cannot fit without truncation.",
    "retryable": false,
    "details": {
      "reason": "LATEST_USER_MESSAGE_EXCEEDS_BUDGET",
      "budget_tokens": 4000,
      "minimum_headroom_tokens": 800
    }
  },
  "warnings": []
}
```

Example 412:

```json
{
  "ok": false,
  "error": {
    "code": "FAILED_PRECONDITION",
    "message": "Session exists, but required evidence was not found.",
    "retryable": false,
    "details": {
      "session_id": "019edb86-1d22-78a3-b9e4-e6121c294056",
      "reason": "NO_EVIDENCE",
      "query": "project benchmark evidence status"
    }
  },
  "warnings": []
}
```

Example 422:

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "budget_split ratios must sum to 1.0 +/- 0.01.",
    "retryable": false,
    "details": {
      "sum": 1.2,
      "field": "policy.budget_split"
    }
  },
  "warnings": []
}
```

Example 403:

```json
{
  "ok": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Requested session is outside the caller project scope.",
    "retryable": false,
    "details": {
      "session_id": "session-other",
      "scope": "PROJECT"
    }
  },
  "warnings": []
}
```

Warning codes:

- `REQUEST_UNDER_BUDGET`
- `RESULT_TRUNCATED`
- `SESSION_RESOLUTION_AMBIGUOUS`
- `COST_MODE_DOWNGRADED`
- `PROVIDER_DEGRADED`
- `PROVIDER_UNAVAILABLE`
- `EXECUTION_STATE_TRUNCATED`
- `RECENT_TAIL_TRUNCATED`
- `RETRIEVED_CONTEXT_DROPPED`
- `CONTEXT_COLLISION_BUDGET_EXCEEDED`
- `DEPRECATED_FIELD_NORMALIZED`
- `FRESHNESS_CONFLICT`
- `STALE_OR_CONFLICTING_EVIDENCE`

`FRESHNESS_CONFLICT` is emitted in traces when Mneme drops or downgrades memory
evidence because fresher adapter/source evidence explicitly marks it as
conflicting.
`STALE_OR_CONFLICTING_EVIDENCE` is emitted in user/tool responses when returned
results include evidence marked stale/conflicting or when results were omitted
because only stale/conflicting evidence was available.

## 22. Idempotency

Idempotency-Key:

- HTTP header name is exactly `Idempotency-Key`.
- Supported on all mutating endpoints:
  - `POST /v1/sessions/start`
  - `POST /v1/events`
  - `POST /v1/turns/complete`
  - `POST /v1/context/prepare`
  - `POST /v1/blobs`
  - `POST /v1/sessions/{id}/close`
  - `POST /v1/sessions/{id}/execution_state`
  - `POST /v1/sessions/{id}/retention/cleanup`
  - `POST /v1/segments/start`
  - `POST /v1/segments/{id}/close`
  - `POST /v1/maintenance/blob-gc`
  - `POST /v1/maintenance/reindex`
  - `POST /v1/maintenance/reindex/{job_id}/cancel`
  - `DELETE /v1/sessions/{id}`
  - `DELETE /v1/blobs/{id}`
- Stable resource ids remain primary where present.
- If both stable id and header exist, both must be compatible.
- Idempotency records MUST be retained for at least
  `daemon.idempotency_key_min_retention_seconds` or until the target session is
  deleted, whichever is later for session-scoped mutation safety. The daemon
  MAY retain them longer.

Event idempotency:

- identical immutable fields: success with duplicate count;
- incompatible immutable fields: `409 CONFLICT`.

Turn idempotency:

- repeated compatible turn complete: success with existing turn status;
- incompatible repeated turn completion: `409 CONFLICT`.

Context prepare idempotency:

- `request_id` is the retry key;
- repeated compatible request returns same or equivalent response and MUST NOT
  create canonical transcript events.

Blob idempotency:

- same `Idempotency-Key` and hash returns same blob metadata;
- same key with different hash returns `409 CONFLICT`.

Delete idempotency:

- repeated delete with same key returns final deleted state.

Maintenance idempotency:

- repeated compatible GC dry-run returns an equivalent summary;
- repeated compatible reindex request returns the existing queued/running job
  when the same `Idempotency-Key`, scope, statuses, and force flag are used;
- repeated cancel on a `CANCELLED` job returns the `CANCELLED` job;
- repeated cancel on a `COMPLETED` job returns the `COMPLETED` job without
  rewriting history;
- incompatible repeated maintenance requests return `409 CONFLICT`.

State and segment idempotency:

- repeated compatible execution-state updates return the same latest state and
  MUST NOT create duplicate history entries;
- repeated compatible segment start/close calls return the existing segment
  metadata;
- incompatible repeats return `409 CONFLICT`.

## 23. Testing And Acceptance

Local checks:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/test_parity_recovery.py -q
.venv/bin/python -m compileall -q mneme_service tests
rg -n "^(<<<<<<<|=======|>>>>>>>)" .
rg -n "[[:blank:]]$" .
```

CI:

- MUST run unit/contract tests with fake providers.
- MUST not require real provider secrets.
- MUST validate generated OpenAPI schema.
- MUST run migration tests across supported schema versions.
- SHOULD run concurrency tests for parallel ingestion and reads.

Release/provider smoke:

- Real provider tests SHOULD be release-gated, not mandatory public CI.
- If release notes claim embeddings readiness, run a real embedding smoke and
  verify `embedding_items > 0` and `embedding_failures == 0`.
- If release notes claim reranker readiness, run real reranker smoke and verify
  `reranker_calls > 0` and `reranker_failures == 0`.
- If release notes claim live LLM enrichment readiness, run real LLM enrichment
  smoke and verify allowed structured fields only.

Benchmark requirements:

- Local smoke benchmark MAY use fake providers.
- Comparative benchmark MUST include:
  - Mneme path;
  - direct prompt baseline;
  - Mneme-only retrieval baseline when applicable;
  - same synthetic corpus and task set;
  - quality/evidence coverage score;
  - latency;
  - provider prompt token estimates with methodology.
- Token savings claims MUST NOT be made from Mneme-only benchmarks.

`estimated_extra_cost`:

- `null` means pricing metadata is missing or the estimate is intentionally not
  computed.
- non-null values MUST include currency, provider price source, timestamp, and
  methodology.

Minimum conformance corpus:

- at least 5 sessions;
- at least 100 events;
- at least 3 runtime labels;
- at least one large `BYTES_REF` event;
- at least two project isolation keys;
- at least one failed/interrupted turn;
- at least one prompt-injection-like untrusted tool output fixture;
- at least one unknown-newer-schema fixture that proves startup refuses unsafe
  downgrade/open;
- at least one migration-from-previous-version fixture once the project has a
  first published schema migration. This fixture is REQUIRED before stable
  release, but not before the first alpha schema exists.

## 24. Required Contract Tests

Core:

1. `session_start_is_idempotent`
2. `get_session_returns_redacted_summary`
3. `session_close_is_nondestructive`
4. `unknown_session_event_ingest_is_rejected`
5. `event_ingest_preserves_raw_content_after_redaction`
6. `event_ingest_is_idempotent`
7. `event_conflict_is_detected`
8. `turn_complete_accepts_failed_interrupted_cancelled`
9. `turn_complete_is_idempotent`
10. `explicit_execution_state_update_patch_replace_records_history`
11. `execution_state_update_requires_provenance`
12. `manual_segment_start_close_events_and_metadata_work`
13. `direct_segment_list_and_get_return_metadata`
14. `oversized_inline_payload_requires_blob_then_bytes_ref`
15. `blob_upload_fetch_metadata_content_range_delete_and_gc`
16. `blob_413_payload_too_large_has_error_envelope`
17. `multipart_event_ingest_creates_bytes_ref_for_binary_parts`
18. `context_prepare_budget_split_validates`
19. `context_prepare_cascades_unused_budget_to_tail_then_evidence`
20. `context_prepare_rejects_char_approx_for_standard_quality_model_bound_prepare`
21. `context_prepare_preserves_authority_and_latest_user`
22. `context_prepare_does_not_persist_generated_context`
23. `expand_context_uses_deterministic_traversal`
24. `expand_context_truncates_with_warning`
25. `global_scope_respects_project_isolation`
26. `resolve_session_filters_and_paginates`
27. `list_sessions_filters_and_paginates`
28. `mcp_default_session_context_injects_session_id`
29. `not_found_guides_discovery_without_leaking_metadata`
30. `mcp_rest_tool_parity`
31. `mcp_errors_map_from_rest_errors`
32. `memory_tool_reads_create_audit_records`
33. `audit_disabled_only_by_test_daemon_config`
34. `audit_record_schema_is_persisted`
35. `retrieved_prompt_injection_fixture_is_wrapped_as_untrusted_data`
36. `redaction_default_profile_covers_common_secret_fixtures`
37. `minimal_mode_makes_no_provider_calls`
38. `cost_mode_downgrade_warns_or_strict_fails`
39. `provider_missing_key_fails_startup_when_enabled`
40. `sqlite_serialized_writer_queue_prevents_busy_writer_races`
41. `schema_migrations_upgrade_existing_database`
42. `unknown_newer_schema_version_refuses_startup`
43. `openapi_schema_is_parseable_and_matches_examples`
44. `trace_and_cost_rest_endpoints_return_expected_schemas`
45. `cost_report_includes_baseline_methodology`
46. `delete_removes_searchable_derivatives_and_blobs`
47. `file_uri_blob_adapter_requires_trusted_path_if_enabled`
48. `session_start_generates_id_only_with_idempotency_key`
49. `session_export_json_is_metadata_only_and_respects_scope`
50. `retention_cleanup_uses_event_timestamp_cutoff`
51. `maintenance_blob_gc_requires_scope_and_is_idempotent`
52. `maintenance_reindex_enqueues_pending_failed_embeddings`
53. `multipart_event_ingest_validates_payload_and_blob_parts`
54. `blob_content_single_range_semantics`
55. `context_prepare_never_truncates_latest_user_message`
56. `schema_version_mismatch_refuses_startup`
57. `mcp_default_session_context_uses_trusted_immutable_process_config`
58. `event_ingest_batch_first_handles_streaming_bursts`
59. `readiness_session_distinguishes_auth_missing_session_and_no_evidence`
60. `mcp_default_session_context_supports_host_per_call_injection`
61. `segment_schema_and_event_summaries_match_contract`
62. `session_export_tar_bundle_streams_blob_parts`
63. `maintenance_reindex_job_polling_reports_status_progress`
64. `retention_cleanup_requires_visible_scope`
65. `foreground_writer_priority_prevents_background_starvation`
66. `multipart_event_ingest_hashes_original_payload_and_blob_digests`
67. `automatic_retention_sweeps_are_observable_and_scoped`
68. `provider_retry_backoff_marks_derived_items_failed_after_budget`
69. `untrusted_evidence_rendering_escapes_xml_or_json`
70. `context_prepare_minimum_required_content_over_budget_returns_422`
71. `startup_integrity_check_fails_closed_or_read_only`
72. `metrics_endpoint_exposes_required_operational_counters`
73. `delete_preserves_anonymized_forensic_audit_anchors`
74. `retention_sweep_skips_active_sessions_without_force`
75. `maintenance_reindex_cancel_stops_provider_calls_and_writes`
76. `multipart_event_ingest_rejects_total_blob_bytes_over_limit`
77. `metrics_capabilities_advertise_format`
78. `resolve_session_best_guess_semantics_are_stable`
79. `segment_start_generates_id_only_with_idempotency_key`
80. `event_importance_and_segment_created_by_enums_validate`
81. `export_blob_omitted_reason_enum_is_stable`
82. `background_jobs_use_micro_transactions_and_yield`
83. `mcp_default_session_stale_returns_specific_error`
84. `readiness_require_evidence_false_checks_session_only`
85. `public_core_schemas_are_defined_in_openapi`
86. `retention_cleanup_request_response_and_force_conflict_contract`
87. `maintenance_reindex_cancel_is_idempotent_for_final_states`
88. `graph_traversal_importance_boost_is_bounded_by_depth`
89. `context_prepare_budget_split_rejects_unknown_keys`
90. `mcp_tool_results_include_session_resolution_source`
91. `session_id_validation_rejects_oversized_or_pathlike_ids`
92. `unknown_export_format_returns_422_validation_error`
93. `intent_classifier_priority_chain_matches_runtime_neutral_contract`
94. `automatic_segmentation_rolls_over_on_explicit_switch_and_embedding_drift`
95. `selective_indexing_compression_preserves_fetchable_raw_tool_output`
96. `vector_retrieval_filters_by_embedding_model_id`
97. `context_search_routing_modes_change_score_breakdown_without_scope_leak`
98. `memory_tool_feedback_updates_state_and_graph_without_polluting_retrieval`
99. `context_prepare_builds_continuation_query_from_execution_state`
100. `segment_drift_trace_is_redacted_and_contains_boundary_metadata`
101. `delta_extraction_emits_entity_modifiers_with_deterministic_conflict_order`
102. `routing_score_formula_uses_default_mode_weights_and_component_breakdown`
103. `entity_contradiction_detects_negated_active_entities_without_provider`
104. `deterministic_index_excerpt_is_stable_when_summary_provider_unavailable`
105. `memory_read_summary_and_memory_read_evidence_edges_match_contract`
106. `segmentation_drift_score_combines_embedding_entropy_and_domain_signals`
107. `tool_domain_shift_metadata_is_trusted_adapter_scoped`
108. `quality_metrics_report_labeled_retrieval_and_segmentation_evaluations`
109. `state_history_hash_uses_canonical_json_bytes`
110. `expand_context_stops_at_traversal_limits_with_warning`
111. `readiness_require_evidence_false_makes_no_provider_calls`
112. `entity_contradiction_uses_whitespace_word_window_not_model_tokens`
113. `writer_queue_depth_limit_returns_retryable_429`
114. `multipart_ingest_blob_failure_rolls_back_all_events`
115. `redaction_timeout_does_not_persist_unredacted_plaintext`
116. `segment_start_without_idempotency_or_segment_id_returns_422`
117. `mcp_versioning_reports_capabilities_and_rejects_unsupported_schema`
118. `auth_failure_audit_uses_unauthenticated_principal`
119. `context_prepare_trace_reports_execution_state_compression_level`

Adapter depth:

- `TOOLS_ONLY`: memory tools discoverable, no prompt replacement claim.
- `EVENT_INGEST`: replay-safe event/turn ingestion.
- `CONTEXT_ENGINE`: prepare called immediately before model request and returned
  messages are model-bound.
- `COMPACTION_OWNER`: FUTURE; not a v0 adapter-depth compliance target until
  a compaction/summarization API is specified.

## 25. Traceability Matrix

| Requirement | API/tool | Code area | Required tests |
|---|---|---|---|
| BR-1 / FR-session | `/v1/sessions/start`, `GET /v1/sessions/{id}`, export, retention cleanup | storage, app | 1, 2, 48, 49, 50, 62, 64, 67, 73, 74, 79, 81, 86, 91, 92 |
| BR-1 / FR-events | `/v1/events` | storage, redaction, app | 4, 5, 6, 7, 53, 58, 76, 80, 114, 115 |
| BR-2 / FR-prepare | `/v1/context/prepare` | app context assembly | 18, 19, 20, 21, 22, 55, 70, 89, 93, 99, 101, 102, 119 |
| BR-3 / FR-tools | REST tools, MCP tools | app, mcp_server | 26, 27, 28, 30, 31, 57, 60, 78, 83, 90, 117 |
| BR-4 / local-first | health, config, integrity, metrics | cli, config | 37, 71, 72, 77, 108, 113 |
| BR-5 / providers | capabilities, costs, reindex | config, embeddings, reranker, enrichment | 38, 39, 52, 63, 68, 75, 87 |
| BR-6 / integration depth | host adapter contract | docs, adapter packages | adapter depth tests |
| BR-7 / package split | packaging | pyproject, release config | publication checklist |
| FR-BYTES_REF | `/v1/blobs`, `BYTES_REF`, blob GC | storage, app | 14, 15, 16, 17, 47, 51, 54, 66, 76 |
| FR-isolation | all scoped endpoints | auth, storage, app | 25, 26, 27, 29 |
| FR-state | state endpoint/tools | state, storage | 10, 11, 98, 99, 109, 119 |
| FR-segments | segment endpoints/tools | segments, storage | 12, 13, 61, 94, 100, 116 |
| FR-audit/traces | `/v1/traces/{id}`, audit records, tools | audit, traces, storage | 32, 33, 34, 44, 85, 98, 100, 118, 119 |
| FR-costs | `/v1/costs/session/{id}`, costs/tool report | storage, app | 44, 45, 85 |
| FR-readiness | `/v1/readiness/session` | app, auth, retrieval | 59, 84, 111 |
| FR-maintenance | `/v1/maintenance/blob-gc`, `/v1/maintenance/reindex` | app, storage, providers | 51, 52, 63, 64, 65, 67, 74, 75, 82, 86, 87 |
| FR-migrations | startup/migration | storage | 41, 42, 56 |
| FR-concurrency | ingestion/search | storage | 40, 58, 65, 76, 82, 113, 114 |
| FR-routing-intelligence | intent, routing modes, query construction | classifier, retrieval, app | 93, 97, 99, 101, 102, 103, 112 |
| FR-indexing-compression | embedding/index input compression | indexing, storage, retrieval | 95, 96, 104 |
| FR-segmentation-intelligence | segment drift, domain shift, quality metrics | segments, retrieval, metrics | 94, 100, 106, 107, 108 |
| FR-memory-feedback | memory reads update state and graph safely | tools, audit, graph | 98, 105 |
| FR-security-redaction | all input/output paths | security | 36, 115 |
| FR-prompt-injection | context rendering | app, security | 35, 69 |
| FR-graph | `expand_context`, graph traversal | graph, retrieval | 23, 88, 110 |
| FR-openapi | `/openapi.json` | app | 43, 85 |

## 26. Known Limitations And Non-Goals

Known limitations:

- Codex remains tools-only for prompt assembly until Codex exposes a supported
  prompt/request hook.
- Regex redaction is imperfect.
- Prompt-injection mitigation reduces risk but cannot guarantee LLM obedience.
- Local SQLite without at-rest encryption is not enterprise confidential by
  default.
- Python vector fallback may be too slow for large corpora without vector
  acceleration.
- Semantic search covers text and text-extracted content only. Non-text binary
  blobs are searchable by metadata/hash/session provenance unless an explicit
  safe extractor policy is configured.
- Public service management may initially be better on macOS than Linux/Windows
  unless adapter packages add service managers.
- `TOOLS_ONLY` runtimes cannot write model-discovered insights through MCP in
  v0. They need trusted REST hooks/importers for ingestion until a future
  audited MCP write contract is approved.
- `COMPACTION_OWNER` is not a v0 compliance level. Mneme can prepare request
  context in v0, but it does not yet expose a summarize/compact endpoint that
  owns host transcript compaction.

Non-goals for v0:

- Hosted cloud Mneme.
- Enterprise RBAC.
- Collaborative multi-user workspaces.
- Fully automatic integration with arbitrary closed runtimes.
- Model answer synthesis endpoint.
- MCP write/checkpoint tools.
- Mneme-owned session compaction/summarization endpoint.

## 27. Compliance Gap Register

The following items are expected to become implementation-plan work after
reviewer approval:

| Gap | Severity | Required decision |
|---|---|---|
| Full blob/BYTES_REF lifecycle | Critical | Implement SQLite-backed blob API, single-range content retrieval, explicit scoped GC, multipart event ingest, metadata-only JSON export plus streaming `tar_bundle`, and BYTES_REF redaction/export behavior, or remove BYTES_REF from v0. |
| Project isolation implementation | Critical | Implement v0 owner token plus logical project isolation filters. Add static scoped-token registry only if multi-project sharing is enabled before alpha. |
| Safe token handling | Critical | Replace recommended CLI token args with env/token-file paths. |
| REST/MCP schema completeness | Critical | Implement the Section 12 core schemas, explicit state-update body, direct segment endpoints, trace/cost endpoints, maintenance endpoints, and matching OpenAPI/tests. |
| Prompt-injection evidence handling | High | Add `source_trust`, data-only wrapper rendering, tool/data/evidence channel support where available, and prompt-injection fixtures. |
| Tokenizer quality guardrails | High | Reject or downgrade STANDARD/QUALITY model-bound prepare when only `CHAR_APPROXIMATE` is available. |
| Blob storage consistency | High | Use SQLite BLOBs as the default v0 blob store with a 2 MiB default limit, range streaming, and WAL/journal safeguards; keep filesystem/file URI storage experimental and trusted-path gated. |
| Migration framework | High | Add schema versioning, migration tests, backup-before-migrate. |
| Serialized SQLite writer | High | Add writer lane/transaction queue, `max_writer_queue_depth`, foreground-write priority over background jobs, bounded busy behavior, multipart transaction time guard, and concurrency tests. |
| OpenAPI schema quality | High | Validate `/openapi.json` and examples in CI. |
| Context budget cascading packing | High | Align implementation and traces with hard headroom reserve, state-to-tail-to-evidence budget cascade, oversized latest-message behavior, and protected-tail priority. |
| Canonical state hashing | High | Hash execution-state history from RFC 8785/JCS canonical JSON bytes and test stable hashes across key order/whitespace variants. |
| Bounded graph traversal | High | Enforce max traversal steps, frontier size, and branching factor so `expand_context` cannot OOM or time out on cyclic/high-degree graphs. |
| Readiness provider-call boundary | High | Ensure `require_evidence=false` makes no external provider calls and `require_evidence=true` uses local persisted indexes unless provider calls are explicitly allowed. |
| Redaction bounded latency | High | Implement bounded-time redaction or safe metadata-only degradation/rejection so oversized/hostile inputs never persist unredacted plaintext after timeout. |
| Runtime-neutral routing intelligence | High | Implement deterministic intent classifier, default switch/entity-contradiction rules, query construction, routing weights, scoring formula, and trace score breakdowns so Mneme preserves Hermes retrieval quality without host-specific logic. |
| Delta extraction determinism | High | Implement optional `mneme.entity_modifier.v0` extraction with deterministic conflict ordering and active-entity-only automatic updates, or keep `delta_extraction_enabled=false` and report the feature unsupported. |
| Automatic segmentation parity | High | Implement explicit-switch and embedding/drift-score segment rollover, centroid rules, `SEGMENT_DRIFT` traces, topic-entropy fallback behavior, and trusted adapter tool-domain shift overrides. |
| Selective indexing compression | High | Compress long textual tool/command outputs for indexing/embedding with the deterministic excerpt fallback while preserving raw fetchable event content and embedding model version filters. |
| Memory-tool feedback continuity | Medium | Ensure audited memory reads update state summaries and create `MEMORY_READ_EVIDENCE` graph links without polluting retrieval or turning MCP into a write API. |
| MCP default session context | Medium | Accept omitted `session_id` only from trusted immutable process/run context or host per-call injection; prevent mutable cross-project server state. |
| Maintenance reindex | Medium | Add scoped `/v1/maintenance/reindex` and `GET /v1/maintenance/reindex/{job_id}` for pending/failed embedding/index repair with provider retry/backoff and polling. |
| Observability and integrity | Medium | Add `/v1/metrics`, structured logs, startup integrity check, retrieval-intelligence counters, labeled benchmark quality reports, and read-only recovery/fail-closed behavior for corruption. |
| Real provider smoke gate | Medium | Add release-gated scripts/docs. |
| Codex automatic ingestion DX | Medium | Keep hook ladder honest; improve doctor/setup but do not overclaim. |
| Backup/restore docs/tools | Medium | Add minimum backup procedure before stable release. |
| Optional MCP write/checkpoint story | Future | Keep model-callable MCP writes out of v0; evaluate future `append_insight`/`save_decision` only with a separate threat model, approval model, and audit contract. |
| TOOLS_ONLY write-gap adoption | Future | Evaluate an official sidecar/importer path that captures approved host stdout/transcripts through REST without making MCP writes model-callable. |
| Hermes legacy bridge | Future | If native Hermes context-engine hooks remain blocked, evaluate a legacy bridge that uses existing safe hooks as a migration aid while clearly labeling reduced guarantees. |
| Compaction owner API | Future | Keep `COMPACTION_OWNER` out of v0 compliance until a `context/summarize` or equivalent compaction endpoint defines redaction, audit, budget, and provider behavior. |

Compatibility notes:

- Alpha daemons deployed before `/v1/readiness/session` may be used by
  hard-dependency clients only in a compatibility mode: the client first checks
  `/v1/capabilities` or version metadata, then performs an authenticated
  `POST /v1/tools/context_search` with `top_k=1` as a temporary run-start
  evidence gate. This fallback is not v0 compliant daemon behavior. It exists
  only to distinguish "old daemon lacks readiness endpoint" from "session is
  missing" during migration.
- The fallback MUST still treat `401` as auth/config failure, `404` as missing
  session/tool failure, and zero results as no evidence. It MUST NOT collapse
  these into "empty memory."
- Draft v0.6 described `multipart_bundle` as the portable blob export format.
  v0.7.1 replaces the required portable format with `tar_bundle`.
  Implementations MAY continue accepting `format=multipart_bundle` only as a
  compatibility extension advertised in `supported_export_formats`. If not
  advertised, `multipart_bundle` MUST return `422 VALIDATION_ERROR` like any
  other unsupported format.

## 28. Review Finding Coverage Matrix

| Reviewer concern | Spec section that addresses it |
|---|---|
| `BYTES_REF` has no protocol | Section 13 defines blob schema, endpoints, SQLite default storage, multipart ingest, content/range behavior, GC, backup/export behavior. |
| Token scope mechanism unspecified | Section 9 defines the v0 owner-token model, logical project isolation keys, and optional static scoped-token registry. |
| Project isolation missing from API | Sections 9, 14.10, and 14.11 define scoped auth, discovery filtering, and `GLOBAL` limits. |
| `cost_mode` vs capabilities unclear | Section 10 defines mode mapping, strict mode, downgrade warnings, and provider startup rules. |
| Token in MCP process argv | Sections 9, 15, and 19 prohibit safe docs from using CLI token args. |
| `Idempotency-Key` incomplete | Section 22 defines the header and mutating endpoint behavior. |
| Insecure mode underspecified | Section 9 defines activation, loopback-only behavior, and capability disclosure. |
| Missing provider required behavior | Section 10 defines enabled/provider-key/fail-start rules. |
| Discovery leaks metadata | Sections 9 and 14.10 bound, redact, scope, paginate, and audit discovery. |
| `MEMORY_READ` disable path missing | Section 16 makes unaudited mode daemon-config-only and test-only; public requests cannot disable audit. |
| `mneme.audit_record.v0` undefined | Section 12.7 defines the audit record schema. |
| Control schemas missing from Core Schemas | Section 12.6 defines session start/export, execution-state update/result, context prepare request/response, retention cleanup request/result, segment start/close, trace, cost, state history, lineage, and reindex job schemas. |
| Execution state update unclear | Sections 12.5 and 14.5 define schema and explicit REST update path. |
| `GET /v1/traces/{trace_id}` and cost endpoint missing | Section 14.7 defines trace and cost report endpoints. |
| Direct segment endpoints missing | Section 14.6 defines direct list/get/close segment endpoints, scoping, and tool parity. |
| `PAUSED` status lacks transitions | Section 12 omits `PAUSED` from v0 until a pause/resume endpoint exists. |
| `expand_context` traversal unclear | Section 14.12 defines deterministic traversal per mode. |
| `context/prepare` budget behavior unclear | Section 14.13 defines hard headroom reserve, budget cascade, whole-message truncation, tokenizer requirements, and oversized-tail behavior. |
| Cost estimate methodology unclear | Sections 11 and 23 define counterfactual methodology and null semantics. |
| Manual segment management missing | Section 14.6 defines segment start/close/events. |
| REST/MCP error mismatch | Sections 15 and 21 define mapping and examples. |
| MCP versioning missing | Section 15 defines tool versioning strategy and `mcp_tool_versions` format. |
| `DEFAULT_SESSION_STALE` HTTP ambiguity | Section 15 defines it as MCP-only; direct REST uses normal HTTP `404 NOT_FOUND`. |
| `session_resolution.source` undefined | Sections 14.9 and 15 define `session_resolution.source` in the shared tool envelope. |
| `GLOBAL` scope violates isolation | Section 14.11 limits `GLOBAL` to caller-visible sessions. |
| Monorepo/package boundary unclear | Section 7 defines core/adapter split and current gap. |
| Tokenizer unspecified / `char_4` fallback unsafe | Section 11 defines tokenizer metadata and forbids `CHAR_APPROXIMATE` for STANDARD/QUALITY model-bound prepare. |
| SQLite migrations missing | Section 18 defines migration framework. |
| SQLite concurrent writers underspecified | Sections 8 and 18 require a serialized writer lane/transaction queue, `max_writer_queue_depth`, and bounded busy behavior. |
| Writer queue can grow without bound | Sections 8 and 18 define `max_writer_queue_depth` and retryable `429 RATE_LIMITED` behavior. |
| Real provider smoke missing | Section 23 defines release-gated real-provider smoke. |
| Error examples missing | Section 21 includes 409, 413, 422, and 403 examples. |
| Codex chicken-and-egg memory issue | Sections 5 and 15 define Codex as tools-only plus optional ingestion hooks. |
| LLM UX friction for session discovery | Sections 14.10 and 15 define discovery flow, trusted default-session injection, and optional `get_current_session`. |
| Prompt injection through memory | Section 17.3 defines source-trust labels, data-only wrapper, tool/data/evidence channel preference, and limitation honesty. |
| Redaction pattern ambiguity | Section 17.2 lists the default redaction profile, ordering, multiline handling, and neutral output classes. |
| Vector fallback performance risk | Sections 10, 18, and 26 require capability disclosure and avoid overclaiming latency. |
| No OpenAPI/Swagger | Section 20 makes OpenAPI the REST schema source of truth and requires CI validation. |
| Backup/restore missing | Section 18 defines backup/restore requirements. |
| Subagent hooks untested | Section 5.1 requires tests for any subagent-support claim. |
| Freshness illusion / stale memory vs current files | Section 14.14 defines freshness as adapter/source supplied and forbids Mneme core from claiming independent current-file/git verification. |
| Blob GC schedule/trigger unclear | Section 13.6 defines explicit endpoint, CLI, startup, and retention triggers; no hidden background GC is assumed. |
| `retention_days` cleanup unclear | Section 14.2 defines explicit cleanup endpoint semantics. |
| `force_active_cleanup` request body missing | Sections 12.6 and 14.2 define `mneme.retention_cleanup_request.v0`, `force_active_cleanup`, and response counts. |
| Active cleanup races with in-flight reads | Section 14.2 requires `409 CONFLICT` with `IN_FLIGHT_READS`. |
| Blob filesystem ACID risk | Section 13 makes SQLite BLOBs the default v0 store and gates filesystem storage as experimental. |
| `AUTH_FAILURE` missing from audit enum | Section 12.7 includes `AUTH_FAILURE` and clarifies `tool` values for auth/system audit records. |
| Public schemas listed but undefined | Section 12.6 defines standalone shapes for context prepare request, trace, cost report, state history entry, and session lineage. |
| `tar_bundle` memory limit ambiguity | Section 14.2 clarifies that compliant `tar_bundle` must stream and `max_export_session_memory_bytes` applies to JSON/legacy/diagnostic export paths. |
| Reindex cancel idempotency missing | Sections 14.8 and 22 define cancel final-state behavior. |
| Graph scoring not normative | Section 12.8 makes `bounded_importance_boost` normative and defines `importance_depth_decay`. |
| Budget split keys not enumerated | Sections 12.6 and 14.13 list canonical `budget_split` keys and unknown-key failure behavior. |
| Public audit-disable request field unsafe | Section 16 removes public audit-disable behavior and keeps unaudited mode test-daemon-only. |
| OpenAPI/examples drift risk | Section 20 requires OpenAPI validation and snippet/example sync checks. |
| Graph edge weights undefined | Section 12.8 defines edge schema, initial weights, generated parent/segment edge types, and scoring formula. |
| REST error examples omit envelope fields | Section 21 gives all error examples with `{ok:false,error:{...},warnings:[]}`. |
| Session export format missing | Sections 12.6 and 14.2 define `mneme.session_export.v0`, query params, blob metadata/content behavior, and audit inclusion. |
| Segment list/close underspecified | Section 14.6 defines `GET /v1/segments` scoping and `segment_close` body. |
| Blob Range behavior unclear | Section 13.4 defines single-range support, malformed/unsatisfiable range errors, and oversized direct-download behavior. |
| `parent_event_ids` edge type unclear | Section 12.8 defines generated `PARENT_CHILD` edges. |
| Multipart event ingest underspecified | Section 13.4 defines part names, content type, placeholder rewrite, limits, and failure behavior. |
| `PRAGMA user_version` vs migrations table conflict | Section 18 defines `user_version` as quick gate, `schema_migrations` as history, and mismatch fail-closed behavior. |
| SQLite BLOB 100 MiB risk | Sections 8 and 13.5 set the default SQLite BLOB limit to 2 MiB and require streaming/journal safeguards. |
| Binary blob redaction ambiguity | Section 17.2 defines binary metadata-only redaction and adapter responsibility for sensitive binary artifacts. |
| Reindex API missing | Sections 12.6 and 14.8 define `mneme.reindex_job.v0` and `/v1/maintenance/reindex`. |
| Batch ingestion vs serialized writer risk | Sections 14.3 and 18 require batch-first adapter guidance and writer-lane batch behavior. |
| MCP default session cross-project risk | Section 15 forbids mutable global current-session state and allows omitted `session_id` only from trusted immutable context or host per-call injection. |
| MCP write/checkpoint gap | Section 26 keeps MCP write/checkpoint tools out of v0; Section 15 and 27 record future `append_insight`/`save_decision` as a separate write contract decision. |
| Readiness endpoint over-engineering concern | Section 14.1 keeps `/v1/readiness/session` as the hard-dependency gate, makes `require_evidence=false` provider-free, and requires explicit opt-in before readiness can make provider calls. Section 27 limits `context_search top_k=1` to alpha compatibility mode. |
| `mneme.segment.v0` missing | Sections 12.6 and 14.6 define stored segment metadata, status values, list/get responses, and segment event summaries. |
| `max_export_blob_inline_bytes` missing | Sections 8, 13.6, and 14.1 define the default `0` value and capabilities exposure; Section 14.2 avoids inline blobs for portable export. |
| Session export base64 OOM risk | Sections 13.6 and 14.2 make JSON metadata-only and define streaming `tar_bundle` for blob bytes. |
| Reindex polling missing | Sections 12.6 and 14.8 define reindex job status values and `GET /v1/maintenance/reindex/{job_id}`. |
| Headroom hard reserve contradiction | Section 14.13 defines `minimum_headroom_tokens` and `unused_context_slack_tokens` instead of flowing evidence budget into headroom. |
| Minimum budget impossible case | Section 14.13 defines `MINIMUM_REQUIRED_CONTENT_EXCEEDS_BUDGET` as the `422` reason after best-effort truncation. |
| `segment_close.outcome` enum missing | Section 12.6 defines allowed close outcome values. |
| Retention cleanup auth missing | Section 14.2 defines owner/scoped-token authorization for retention cleanup. |
| Foreground writer starvation risk | Sections 14.8 and 18 require foreground priority, bounded writer queue, multipart time/byte guards, and background adaptive backoff. |
| Provider retry policy missing | Sections 8, 14.8, and 18 define retry/backoff and automatic retry before derived status failure. |
| XML wrapper injection | Section 17.3 forbids raw interpolation and requires XML/JSON escaping. |
| MCP session injection mechanics unclear | Section 15 defines immutable env/initialize/proxy injection options and forbids mutable cross-project defaults. |
| Freshness conflict requires hidden comparison | Section 14.14 limits `FRESHNESS_CONFLICT` to adapter/source-supplied conflicts. |
| Observability missing | Sections 14.1 and 19 require `/v1/metrics` and structured logs. |
| Database recovery missing | Sections 8 and 18 require startup integrity checks and fail-closed/read-only recovery behavior. |
| Latest user request truncation risk | Section 14.13 forbids best-effort truncation of the current latest user request and returns `LATEST_USER_MESSAGE_EXCEEDS_BUDGET` when it cannot fit. |
| Audit delete breaks forensics | Sections 12.7 and 14.2 preserve anonymized forensic audit anchors while deleting/redacting session content. |
| Reindex runaway job cancellation missing | Section 14.8 defines `POST /v1/maintenance/reindex/{job_id}/cancel`, cooperative cancellation, provider throttling, and wait timeout. |
| Multipart ingest WAL/OOM risk | Sections 8, 13.4, and 18 define total blob byte, transaction byte, and transaction-time limits plus micro-transaction/yield behavior. |
| `multipart/mixed` export DX risk | Sections 12.6, 13.6, and 14.2 make streaming `tar_bundle` the required portable blob export format. |
| Retention sweeps delete active-session history | Section 14.2 skips `ACTIVE` sessions unless OWNER explicitly uses `force_active_cleanup=true`. |
| Compaction owner API missing | Sections 5, 26, and 27 demote `COMPACTION_OWNER` to FUTURE until a compaction/summarization endpoint is specified. |
| `best_guess_session_id` edge cases | Section 14.10 defines values for `EXACT_SESSION_ID`, `SINGLE_MATCH`, `AMBIGUOUS`, and `NOT_FOUND`. |
| `segment_start.segment_id` optionality unclear | Section 12.6 requires either stable `segment_id` or `Idempotency-Key` for daemon-generated segment ids and returns `422` if both are missing. |
| Importance assignment unclear | Sections 12.3 and 12.8 define event importance values, defaulting, adapter responsibility, and bounded graph boost behavior. |
| `metrics_format` missing | Sections 8 and 14.1 define `metrics_format` and advertise it in capabilities. |
| `created_by` and `omitted_reason` enums missing | Sections 12.6 and 14.2 define stable enum values for segment creators and export blob omission reasons. |
| MCP default session stale race | Section 15 requires startup/first-call default-session verification and `DEFAULT_SESSION_STALE`. |
| Hermes intent classifier lost in abstraction | Section 14.5.1 makes deterministic runtime-neutral intent classification and query construction a Mneme core responsibility for `CONTEXT_ENGINE` paths. |
| Hermes automatic segmentation underspecified | Section 14.6 defines explicit-switch, embedding-drift, centroid, tool-domain-shift, and `SEGMENT_DRIFT` trace behavior. |
| Hermes selective compression missing | Sections 12.3 and 14.3 define selective indexing compression for long tool/command outputs while preserving raw fetchable content. |
| Hermes memory-tool feedback loop missing | Section 16 requires direct memory reads to update state summaries and graph evidence links without making MCP model-callable writes. |
| Hermes routing modes missing | Sections 14.5.1 and 14.11 define `general`, `reasoning`, `factual`, and `debugging` routing modes with traceable score effects. |
| Delta extraction schema missing | Sections 12.9 and 14.5.1 define `mneme.entity_modifier.v0`, deterministic extraction rules, conflict ordering, and active-entity-only automatic updates. |
| Routing scoring formula missing | Section 14.11 defines the scoring formula, default mode weights, normalized components, and score-breakdown shape. |
| Explicit switch/entity contradiction underspecified | Section 14.5.1 defines default switch phrases, negation/replacement terms, and deterministic contradiction behavior. |
| Entity contradiction depends on model tokenizer | Section 14.5.1 uses a deterministic whitespace-word window, not provider/model tokenization. |
| Deterministic indexing excerpt unspecified | Section 14.3 defines the no-provider fallback excerpt algorithm and event-type compression defaults. |
| Memory-read summary/edge semantics unspecified | Sections 12.8 and 16 define `MEMORY_READ_EVIDENCE` edges and bounded `last_tool_output_summary` format. |
| Retrieval quality metrics missing | Section 19 defines runtime intelligence counters and labeled benchmark quality report expectations. |
| `state_hash` canonicalization missing | Section 12.6 defines RFC 8785/JCS canonical JSON bytes and lowercase SHA-256 digest format for state history hashes. |
| `expand_context` can traverse unbounded graph | Sections 8 and 14.12 define max traversal steps, frontier size, branching factor, visited-node behavior, and `TRAVERSAL_LIMIT_REACHED`. |
| Multipart atomicity rollback untested | Sections 13.4 and 24 require rollback of all events/blob metadata on multipart blob failure. |
| Redaction regex latency unbounded | Sections 8 and 17.2 define `indexing.max_redaction_time_ms` and forbid silent unredacted persistence on timeout. |
| MCP versioning ambiguity | Section 15 defines capabilities/schema-version negotiation for compatible changes and new tool names only for breaking semantics. |
| `AUTH_FAILURE` principal unknown | Section 12.7 defines the `UNAUTHENTICATED` principal for pre-token auth failures. |
| Context prepare state compression hidden | Sections 12.6 and 14.13 require `trace.execution_state_compression_level`. |
| `EXTERNAL_MCP_CONTENT` trust ambiguity | Section 12.3 defines it as untrusted by default unless a separate source-adapter trust registration marks it trusted. |

## 29. Reviewer Checklist

Reviewers should answer:

1. Is the product boundary honest and narrow enough?
2. Are `TOOLS_ONLY`, `EVENT_INGEST`, and `CONTEXT_ENGINE` claims clear?
3. Is the blob/BYTES_REF protocol sufficient for external adapters?
4. Is project isolation enforceable with the proposed owner-token/static-token
   model?
5. Are token handling rules safe enough for local MCP processes?
6. Are provider/cost-mode downgrade and fail-closed rules unambiguous?
7. Is context budget packing deterministic and testable?
8. Are REST and MCP error semantics aligned?
9. Are migrations, backup, and concurrency specified enough for local SQLite?
10. Are freshness semantics honest about adapter-supplied current source
    evidence?
11. Are audit records, traces, costs, state updates, and segments specified
    enough for implementation and code review?
12. Are export, retention cleanup, blob GC, and reindex scoped and safe enough?
13. Are graph traversal, writer queue, multipart ingest, readiness checks, and
    redaction bounded so hostile or large inputs fail predictably?
14. Are prompt-injection and text/binary redaction limitations stated honestly?
15. Is MCP default-session behavior safe from cross-project leakage?
16. Is OpenAPI treated as the REST source of truth with examples kept in sync?
17. Is the testing plan sufficient for later code review against this spec?
18. Which compliance gaps must be closed before public release versus after
    alpha dogfood?

## 30. Approval Gate

This specification should be reviewed before the next compliance
implementation pass.

Approval means:

- reviewers accept this as the target v0 requirement set;
- known gaps can be converted into implementation tasks;
- future code review can compare code/tests against this document.

Approval does not mean:

- the current alpha implementation already satisfies every MUST;
- Codex has automatic prompt replacement;
- provider quality/cost claims are validated without benchmark evidence.
