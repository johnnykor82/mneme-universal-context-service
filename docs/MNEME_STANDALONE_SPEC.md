# Mneme Universal Context Service - Standalone Specification

Status: draft v0.4 for external architecture review
Date: 2026-06-21
Owner: Ivan Konstantinov
Scope: product, architecture, protocol, security, operations, testing, and acceptance requirements for Mneme core

## 0. How To Read This Document

This is the single-file reviewer specification for Mneme Universal Context
Service. It is intended to be sent without attaching the rest of the repository
documentation.

This document is normative for the next compliance pass. The current alpha code
may not yet satisfy every MUST in this file. After reviewers approve this
specification, the next step is to create an implementation gap plan and update
the plugin/core until code, tests, and docs match the accepted specification.

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
| 4 | `COMPACTION_OWNER` | Host delegates explicit/overflow compaction. | Mneme may own compaction strategy. |
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
| `compact` | `COMPACTION_OWNER+` | future compaction endpoint or adapter-local policy | Delegate explicit/overflow compaction. |
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
blob_dir = ".local/mneme-blobs"
host = "127.0.0.1"
port = 8765
insecure_dev = false
require_embeddings = false
strict_cost_mode = false
max_batch_events = 200
max_event_content_bytes = 1048576
max_blob_bytes = 104857600

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

[providers.reranker]
enabled = false
provider = "jina"
model = "jina-reranker-v2-base-multilingual"
base_url = "https://api.jina.ai/v1"
api_key_env = "MNEME_RERANKER_API_KEY"

[providers.llm_enrichment]
enabled = false
provider = "openai_compatible"
model = "CONFIGURE_ME"
base_url = "https://api.openai.com/v1"
api_key_env = "MNEME_LLM_API_KEY"
```

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
- `mneme.event_batch.v0`
- `mneme.event.v0`
- `mneme.turn.v0`
- `mneme.message.v0`
- `mneme.context_prepare_request.v0`
- `mneme.context_prepare_response.v0`
- `mneme.trace.v0`
- `mneme.audit_record.v0`
- `mneme.cost_report.v0`
- `mneme.execution_state.v0`
- `mneme.state_history_entry.v0`
- `mneme.session_lineage.v0`
- `mneme.segment.v0`
- `mneme.graph_edge.v0`
- `mneme.blob.v0`

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

### 12.6 Audit Record

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

Audit records MUST be durable for live sessions. Privacy delete may remove
session-scoped audit records in v0 local mode; enterprise/tamper-evident audit
is FUTURE.

### 12.7 Graph Edge

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
- explicit `parent_event_ids`: `0.9`
- `DECISION_FOLLOWS`: `0.8`
- temporal `FOLLOWS`: `0.2`

Traversal MAY apply deterministic depth decay, default `0.6 ** depth`. Dynamic
learned edge weights are FUTURE.

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
  "size_bytes": 10485760,
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
  "size_bytes": 10485760,
  "media_type": "text/plain",
  "storage_owner": "SERVER"
}
```

`file://` URIs are FUTURE/experimental in v0.4. If a deployment enables them,
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
    "size_bytes": 10485760,
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

Blob content reads:

- `GET /v1/blobs/{blob_id}/content` MUST set `Content-Type` from blob metadata.
- The reference daemon SHOULD support `Range` requests for large blobs.
- If range streaming is unsupported, the daemon MUST reject oversized downloads
  with `413 PAYLOAD_TOO_LARGE` rather than buffering beyond configured limits.

### 13.5 Blob Storage Layout

Reference daemon storage:

- The v0 compliant reference store keeps server-owned blob bytes in SQLite BLOB
  rows, keyed by `blob_id` and content hash. This preserves ACID behavior with
  event metadata and avoids filesystem/SQLite two-phase consistency problems.
- Optional filesystem blob storage is FUTURE/experimental. If implemented, it
  MUST use write-temp/fsync/rename, hash verification, and reconciliation before
  being marked compliant.

The filesystem path MUST NOT be exposed as the canonical URI. The canonical URI
is `mneme-blob://blob_id`.

### 13.6 Blob GC, Export, And Backup

- Session delete MUST delete server-owned SQLite blobs referenced only by that
  session in the same transaction where possible, or mark them for garbage
  collection.
- Export MUST include blob metadata and MAY include blob bytes depending on
  `include_blobs`.
- Backup MUST include SQLite; if an experimental filesystem blob store is used,
  backup MUST include both SQLite and the blob directory in one consistent
  snapshot.
- Orphan blob GC MUST be safe and idempotent.
- GC runs only when explicitly invoked by `/v1/maintenance/blob-gc`, a CLI
  command such as `mneme maintenance blob-gc`, startup maintenance when
  configured, or retention cleanup. v0 MUST NOT pretend background GC exists
  unless it is actually implemented and observable.

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
  "query": "RLM Orchestrator MVP 1 benchmark evidence project status",
  "require_evidence": true,
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

Until a deployed daemon exposes `/v1/readiness/session`, hard dependencies MAY
temporarily use authenticated `POST /v1/tools/context_search` with
`top_k=1` as the run-start gate. The fallback MUST still distinguish `401`,
`404`, and zero-result/no-evidence outcomes instead of collapsing them into
"empty memory".

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
  "supports_project_isolation": true,
  "supports_openapi": true,
  "auth_schemes": ["BEARER_TOKEN", "UNIX_SOCKET"],
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
    "max_blob_bytes": 104857600,
    "top_k": 10,
    "top_k_max": 100,
    "page_size_default": 20,
    "page_size_max": 1000,
    "expand_context_depth_default": 2,
    "expand_context_depth_max": 5,
    "expand_context_max_events_default": 12,
    "expand_context_max_events_max": 200,
    "max_latency_ms_default": 250,
    "max_parent_event_ids": 64
  },
  "tokenizer": {
    "tokenizer_id": "char_4_fallback",
    "token_estimate_quality": "CHAR_APPROXIMATE"
  },
  "storage": {
    "sqlite_wal": true,
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

`GET /v1/sessions/{session_id}` returns a redacted session object and derived
counts visible to the caller.

`POST /v1/sessions/{session_id}/close` sets `status=ENDED` and `ended_at`; it
does not delete events.

`POST /v1/sessions/{session_id}/retention/cleanup` applies
`privacy.retention_days` and blob GC for that session. v0 MAY also run the same
cleanup at startup when configured, but it MUST be explicit and observable in
logs/traces.

`DELETE /v1/sessions/{session_id}` removes or irreversibly redacts session data
according to retention policy. v0 privacy delete removes traces/audit records
inside the deleted session scope. FUTURE enterprise/tamper-evident audit logs
may retain hashed delete markers.

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

### 14.6 Segments

Required:

- `POST /v1/segments/start`
- `POST /v1/segments/{segment_id}/close`
- `GET /v1/segments`
- `GET /v1/segments/{segment_id}`
- `GET /v1/segments/{segment_id}/events`
- `POST /v1/tools/list_segments`

Automatic segmentation remains supported, but adapters MUST have a way to mark
task boundaries explicitly when the host knows a task has changed.

`GET /v1/segments/{segment_id}/events` returns paginated event summaries for a
segment under caller scope.

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

### 14.8 Memory Tool Parity Endpoints

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
  "warnings": []
}
```

REST and MCP session-bound tools accept the same Mneme `session_id` values.
For example, `019edb86-1d22-78a3-b9e4-e6121c294056` is a valid external
Codex/Mneme session id format for both REST and MCP when the caller is
authenticated. If MCP succeeds for a session and direct REST returns
`401 UNAUTHENTICATED`, the session id format is not the suspected cause; the
REST caller must configure the same bearer token boundary used by the MCP
process.

### 14.9 Session Discovery

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

When ambiguous:

- warning code MUST be `SESSION_RESOLUTION_AMBIGUOUS`;
- agent guidance MUST say to call `list_sessions` with the same project filters
  or refine `project_path`, `thread_id`, or `slug`;
- results MUST be scoped and redacted.

`list_sessions` MUST support `page_size`, `page_token`, and `next_page_token`.
It MUST never silently truncate without `next_page_token` or
`matches_truncated=true`.

### 14.10 Context Search

Search scopes:

- `SESSION`: current session only.
- `LINEAGE`: current session plus explicit lineage sessions visible to caller.
- `PROJECT`: all sessions sharing the effective project isolation key.
- `GLOBAL`: all sessions visible to the principal. For non-admin local tokens,
  this is normally equivalent to `PROJECT`.

`GLOBAL` MUST NOT bypass project isolation.

### 14.11 Expand Context

Traversal algorithm MUST be deterministic.

Modes:

- `TOOL_CHAIN`: BFS over `TOOL_RESULT`, `TOOL_INPUT`, parent/child edges, seed
  first, then tool call, tool output, downstream decisions.
- `CAUSAL`: BFS over parent/child and decision edges by edge weight then time.
- `TEMPORAL`: seed, previous events, next events by timestamp.
- `SEGMENT`: segment anchors, segment skeleton, then member events by
  importance and time.

When `max_events` is reached:

- return `truncated=true`;
- include warning `RESULT_TRUNCATED`;
- include `dropped_count` and traversal frontier summary when possible.

### 14.12 Context Prepare

Required for deep adapters:

- `POST /v1/context/prepare`

Validation:

- `budget_tokens > 0`
- `budget_tokens <= context_window_tokens`
- `request_messages` use `mneme.message.v0`
- `budget_split` values are non-negative and sum to `1.0 +/- 0.01`

Headroom canonical field:

- `policy.budget_split.headroom_ratio` is canonical.
- `policy.headroom_ratio` is deprecated and MUST be rejected or normalized with
  warning `DEPRECATED_FIELD_NORMALIZED`.
- If both are present and differ, return `422 VALIDATION_ERROR`.

Budget packing algorithm:

1. Estimate or accept exact token counts.
2. Reserve headroom first.
3. Preserve system/developer authority messages if requested and within hard
   budget.
4. Preserve the latest user message.
5. Build execution-state block under its fixed target share; if too large, compress
   to `FULL`, `COMPACT`, `MINIMAL`, or `TRUNCATED`.
6. Build protected recent tail as whole messages/turn units from newest to
   oldest. Do not cut a message mid-token unless the caller explicitly allows
   text truncation for a single oversized message.
7. Build retrieved evidence from selected candidates under its fixed slot.
   Unused state/tail/evidence budget flows to headroom by default. A future
   `fluid_overflow=true` mode MAY permit unused state/tail budget to flow to
   retrieved evidence, but only when tokenizer quality is `EXACT` or
   `MODEL_APPROXIMATE`.
8. Drop whole retrieved evidence items before dropping protected tail.
9. Add optional memory hints, goal trail, and checkpoint hints only if budget
   remains in their own slot or headroom policy permits.
10. Verify final projected tokens plus headroom fit hard budget.
11. Emit trace with selected/dropped refs and reasons.

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

### 14.13 Evidence Freshness

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

- `CURRENT` evidence wins over Mneme memory when they disagree.
- Context traces MUST include `FRESHNESS_CONFLICT` when memory evidence is
  dropped or downgraded because fresher source evidence disagrees.
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
future write contract is approved.

Tool versioning:

- MCP tool names remain unversioned in v0 for usability.
- Each tool result MUST include `schema_version` in `data` where applicable.
- `/v1/capabilities` MUST expose `mcp_tool_versions`.
- Breaking future changes MUST add new tool names, e.g. `context_search_v2`, or
  negotiate via explicit schema version.

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

MCP startup MUST NOT require tokens in argv. Use environment, token file, or
owner-only env file.

Session friction mitigation:

- MCP server instructions MUST tell the model to resolve sessions before
  session-bound calls when no trusted session id exists.
- Host adapters that know the current project/session MUST launch MCP with a
  default project/session context or inject it into tool calls before reaching
  the model. The model should not spend routine calls rediscovering a session
  the host already knows.
- When default context is configured, session-bound MCP tools MAY accept omitted
  `session_id` and fill it from trusted server-side context. The response MUST
  include the resolved `session_id`.
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

Redaction output format:

- replace content with `[REDACTED:<kind>]`;
- record redaction metadata with kind, field, and hash of original where safe;
- never store reversible secrets by default.

False positives/negatives:

- The spec acknowledges regex redaction is imperfect.
- Reviewers and users MUST NOT treat redaction as a substitute for project-level
  secret hygiene.
- Provider privacy docs MUST state exactly what is sent to configured external
  providers.

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
- Background embedding/enrichment jobs MUST enqueue writes instead of competing
  directly with foreground ingestion.
- If the writer queue is full or SQLite remains busy after bounded internal
  retries, return `429 RATE_LIMITED` or `503 STORAGE_BUSY` with
  `retryable=true`.
- Reads MUST not observe partially written batches.

Migration requirements:

- Store schema version in `PRAGMA user_version` and a `schema_migrations` table.
- Migrations MUST be ordered, idempotent, and tested from each supported
  previous version.
- Startup MUST refuse unknown newer schema versions.
- Startup MUST create a backup or require explicit `--no-backup-before-migrate`
  before destructive migrations.
- Release notes MUST include migration impacts.

Backup/restore:

- Backup MUST include SQLite. If an experimental filesystem blob driver is
  enabled, backup MUST also include the blob directory.
- Hot backup SHOULD use SQLite backup API.
- Restore MUST verify schema version, blob metadata, and blob hash integrity.

CURRENT GAP: migration and backup/restore mechanisms must be added or explicitly
deferred before public stable release.

## 19. Operations And Deployment

Supported v0 deployment:

- local source checkout or package install;
- Python 3.11 or 3.12;
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
| 422 | `VALIDATION_ERROR` | Semantically invalid payload or lifecycle state. |
| 429 | `RATE_LIMITED` | Local queue, SQLite busy timeout, or provider throttle. |
| 503 | `PROVIDER_UNAVAILABLE` | Required provider unavailable. |
| 503 | `STORAGE_BUSY` | SQLite/storage retry budget exhausted. |
| 500 | `INTERNAL_ERROR` | Unexpected service failure. |

Example 409:

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "event_id already exists with incompatible immutable fields.",
    "retryable": false,
    "details": {
      "event_id": "event-001",
      "field": "content.hash"
    }
  }
}
```

Example 413:

```json
{
  "error": {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "Inline content exceeds max_event_content_bytes; upload a blob and retry with BYTES_REF.",
    "retryable": false,
    "details": {
      "max_event_content_bytes": 1048576,
      "actual_bytes": 2097152,
      "retry_with": "POST /v1/blobs"
    }
  }
}
```

Example 413 for blob upload:

```json
{
  "ok": false,
  "error": {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "Blob upload exceeds max_blob_bytes.",
    "retryable": false,
    "details": {
      "max_blob_bytes": 104857600,
      "actual_bytes": 209715200
    }
  },
  "warnings": []
}
```

Example 422:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "budget_split ratios must sum to 1.0 +/- 0.01.",
    "retryable": false,
    "details": {
      "sum": 1.2,
      "field": "policy.budget_split"
    }
  }
}
```

Example 403:

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Requested session is outside the caller project scope.",
    "retryable": false,
    "details": {
      "session_id": "session-other",
      "scope": "PROJECT"
    }
  }
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
  - `DELETE /v1/sessions/{id}`
  - `DELETE /v1/blobs/{id}`
- Stable resource ids remain primary where present.
- If both stable id and header exist, both must be compatible.

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
19. `context_prepare_fixed_slot_packing_preserves_tail_before_evidence`
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

Adapter depth:

- `TOOLS_ONLY`: memory tools discoverable, no prompt replacement claim.
- `EVENT_INGEST`: replay-safe event/turn ingestion.
- `CONTEXT_ENGINE`: prepare called immediately before model request and returned
  messages are model-bound.
- `COMPACTION_OWNER`: compaction hook registered and failure behavior defined.

## 25. Traceability Matrix

| Requirement | API/tool | Code area | Required tests |
|---|---|---|---|
| BR-1 / FR-session | `/v1/sessions/start`, `GET /v1/sessions/{id}` | storage, app | 1, 2 |
| BR-1 / FR-events | `/v1/events` | storage, redaction, app | 4, 5, 6, 7 |
| BR-2 / FR-prepare | `/v1/context/prepare` | app context assembly | 18, 19, 20, 21, 22 |
| BR-3 / FR-tools | REST tools, MCP tools | app, mcp_server | 26, 27, 28, 30, 31 |
| BR-4 / local-first | health, config | cli, config | 37 |
| BR-5 / providers | capabilities, costs | config, embeddings, reranker, enrichment | 38, 39 |
| BR-6 / integration depth | host adapter contract | docs, adapter packages | adapter depth tests |
| BR-7 / package split | packaging | pyproject, release config | publication checklist |
| FR-BYTES_REF | `/v1/blobs`, `BYTES_REF` | storage, app | 14, 15, 16, 17, 47 |
| FR-isolation | all scoped endpoints | auth, storage, app | 25, 26, 27, 29 |
| FR-state | state endpoint/tools | state, storage | 10, 11 |
| FR-segments | segment endpoints/tools | segments, storage | 12, 13 |
| FR-audit/traces | `/v1/traces/{id}`, audit records, tools | audit, traces, storage | 32, 33, 34, 44 |
| FR-costs | `/v1/costs/session/{id}`, costs/tool report | storage, app | 44, 45 |
| FR-migrations | startup/migration | storage | 41, 42 |
| FR-concurrency | ingestion/search | storage | 40 |
| FR-security-redaction | all input/output paths | security | 36 |
| FR-prompt-injection | context rendering | app, security | 35 |
| FR-openapi | `/openapi.json` | app | 43 |

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
- Public service management may initially be better on macOS than Linux/Windows
  unless adapter packages add service managers.

Non-goals for v0:

- Hosted cloud Mneme.
- Enterprise RBAC.
- Collaborative multi-user workspaces.
- Fully automatic integration with arbitrary closed runtimes.
- Model answer synthesis endpoint.
- MCP write/checkpoint tools.

## 27. Compliance Gap Register

The following items are expected to become implementation-plan work after
reviewer approval:

| Gap | Severity | Required decision |
|---|---|---|
| Full blob/BYTES_REF lifecycle | Critical | Implement SQLite-backed blob API, content/range retrieval, explicit GC, multipart event ingest, and BYTES_REF redaction/export behavior, or remove BYTES_REF from v0. |
| Project isolation implementation | Critical | Implement v0 owner token plus logical project isolation filters. Add static scoped-token registry only if multi-project sharing is enabled before alpha. |
| Safe token handling | Critical | Replace recommended CLI token args with env/token-file paths. |
| REST/MCP schema completeness | Critical | Implement `mneme.audit_record.v0`, explicit state-update body, direct segment endpoints, trace/cost endpoints, and matching OpenAPI/tests. |
| Prompt-injection evidence handling | High | Add `source_trust`, data-only wrapper rendering, tool/data/evidence channel support where available, and prompt-injection fixtures. |
| Tokenizer quality guardrails | High | Reject or downgrade STANDARD/QUALITY model-bound prepare when only `CHAR_APPROXIMATE` is available. |
| Blob storage consistency | High | Use SQLite BLOBs as the default v0 blob store; keep filesystem/file URI storage experimental and trusted-path gated. |
| Migration framework | High | Add schema versioning, migration tests, backup-before-migrate. |
| Serialized SQLite writer | High | Add writer lane/transaction queue, bounded busy behavior, and concurrency tests. |
| OpenAPI schema quality | High | Validate `/openapi.json` and examples in CI. |
| Context budget fixed-slot packing | High | Align implementation and traces with deterministic slots, whole-message truncation, and protected-tail priority. |
| MCP default session context | Medium | Let host adapters inject trusted current session/project context or expose `get_current_session` when available. |
| Real provider smoke gate | Medium | Add release-gated scripts/docs. |
| Codex automatic ingestion DX | Medium | Keep hook ladder honest; improve doctor/setup but do not overclaim. |
| Backup/restore docs/tools | Medium | Add minimum backup procedure before stable release. |
| Optional MCP write/checkpoint story | Future | Keep model-callable MCP writes out of v0 unless a separate write contract and approval model is designed. |

## 28. Review Finding Coverage Matrix

| Reviewer concern | Spec section that addresses it |
|---|---|
| `BYTES_REF` has no protocol | Section 13 defines blob schema, endpoints, SQLite default storage, multipart ingest, content/range behavior, GC, backup/export behavior. |
| Token scope mechanism unspecified | Section 9 defines the v0 owner-token model, logical project isolation keys, and optional static scoped-token registry. |
| Project isolation missing from API | Sections 9, 14.9, and 14.10 define scoped auth, discovery filtering, and `GLOBAL` limits. |
| `cost_mode` vs capabilities unclear | Section 10 defines mode mapping, strict mode, downgrade warnings, and provider startup rules. |
| Token in MCP process argv | Sections 9, 15, and 19 prohibit safe docs from using CLI token args. |
| `Idempotency-Key` incomplete | Section 22 defines the header and mutating endpoint behavior. |
| Insecure mode underspecified | Section 9 defines activation, loopback-only behavior, and capability disclosure. |
| Missing provider required behavior | Section 10 defines enabled/provider-key/fail-start rules. |
| Discovery leaks metadata | Sections 9 and 14.9 bound, redact, scope, paginate, and audit discovery. |
| `MEMORY_READ` disable path missing | Section 16 makes unaudited mode daemon-config-only and test-only; public requests cannot disable audit. |
| `mneme.audit_record.v0` undefined | Section 12.6 defines the audit record schema. |
| Execution state update unclear | Sections 12.5 and 14.5 define schema and explicit REST update path. |
| `GET /v1/traces/{trace_id}` and cost endpoint missing | Section 14.7 defines trace and cost report endpoints. |
| Direct segment endpoints missing | Section 14.6 defines direct list/get segment endpoints and tool parity. |
| `PAUSED` status lacks transitions | Section 12 omits `PAUSED` from v0 until a pause/resume endpoint exists. |
| `expand_context` traversal unclear | Section 14.11 defines deterministic traversal per mode. |
| `context/prepare` budget behavior unclear | Section 14.12 defines fixed-slot packing, whole-message truncation, tokenizer requirements, and future guarded overflow. |
| Cost estimate methodology unclear | Sections 11 and 23 define counterfactual methodology and null semantics. |
| Manual segment management missing | Section 14.6 defines segment start/close/events. |
| REST/MCP error mismatch | Sections 15 and 21 define mapping and examples. |
| MCP versioning missing | Section 15 defines tool versioning strategy and `mcp_tool_versions` format. |
| `GLOBAL` scope violates isolation | Section 14.10 limits `GLOBAL` to caller-visible sessions. |
| Monorepo/package boundary unclear | Section 7 defines core/adapter split and current gap. |
| Tokenizer unspecified / `char_4` fallback unsafe | Section 11 defines tokenizer metadata and forbids `CHAR_APPROXIMATE` for STANDARD/QUALITY model-bound prepare. |
| SQLite migrations missing | Section 18 defines migration framework. |
| SQLite concurrent writers underspecified | Section 18 requires a serialized writer lane/transaction queue and bounded busy behavior. |
| Real provider smoke missing | Section 23 defines release-gated real-provider smoke. |
| Error examples missing | Section 21 includes 409, 413, 422, and 403 examples. |
| Codex chicken-and-egg memory issue | Sections 5 and 15 define Codex as tools-only plus optional ingestion hooks. |
| LLM UX friction for session discovery | Sections 14.9 and 15 define discovery flow, default-session injection, and optional `get_current_session`. |
| Prompt injection through memory | Section 17.3 defines source-trust labels, data-only wrapper, tool/data/evidence channel preference, and limitation honesty. |
| Redaction pattern ambiguity | Section 17.2 lists the default redaction profile. |
| Vector fallback performance risk | Sections 10, 18, and 26 require capability disclosure and avoid overclaiming latency. |
| No OpenAPI/Swagger | Section 20 makes OpenAPI the REST schema source of truth and requires CI validation. |
| Backup/restore missing | Section 18 defines backup/restore requirements. |
| Subagent hooks untested | Section 5.1 requires tests for any subagent-support claim. |
| Freshness illusion / stale memory vs current files | Section 14.13 defines freshness as adapter/source supplied and forbids Mneme core from claiming independent current-file/git verification. |
| Blob GC schedule/trigger unclear | Section 13.6 defines explicit endpoint, CLI, startup, and retention triggers; no hidden background GC is assumed. |
| `retention_days` cleanup unclear | Section 14.2 defines explicit cleanup endpoint semantics. |
| Blob filesystem ACID risk | Section 13 makes SQLite BLOBs the default v0 store and gates filesystem storage as experimental. |
| Public audit-disable request field unsafe | Section 16 removes public audit-disable behavior and keeps unaudited mode test-daemon-only. |
| OpenAPI/examples drift risk | Section 20 requires OpenAPI validation and snippet/example sync checks. |
| Graph edge weights undefined | Section 12.7 defines edge schema, initial weights, and depth decay. |
| MCP write/checkpoint gap | Section 26 keeps MCP write/checkpoint tools out of v0; a future write contract is required before adding model-callable writes. |

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
12. Are prompt-injection and redaction limitations stated honestly?
13. Is OpenAPI treated as the REST source of truth with examples kept in sync?
14. Is the testing plan sufficient for later code review against this spec?
15. Which compliance gaps must be closed before public release versus after
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
