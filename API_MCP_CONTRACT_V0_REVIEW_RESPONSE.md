# API/MCP Contract v0 Review Response

Date: 2026-06-08
Status: response for second external review
Related spec: `API_MCP_CONTRACT_V0.md`

## Summary

I reviewed the external feedback and re-reviewed the contract independently.
Most of the critique was technically valid: the previous draft was strong
structurally, but still left several protocol choices ambiguous enough to create
incompatible implementations.

This revision keeps the original architecture intact:

- REST remains the lifecycle/control-plane surface.
- MCP remains the agent-facing memory-tool surface.
- Context preparation remains request-only and does not mutate the canonical
  transcript.
- Implementation is still gated on spec approval.

## Feedback Accepted and Fixed

### Oversized Payloads

Accepted. The previous draft allowed two interpretations for oversized inline
content. The revised contract now states:

- inline event content above `max_event_content_bytes` must return
  `413 PAYLOAD_TOO_LARGE`;
- adapters must retry with `BYTES_REF`;
- the server must not silently transform inline content into `BYTES_REF`.

The adapter test was updated to require this behavior.

### Event Idempotency and `409 CONFLICT`

Accepted. The revised Event Schema now defines immutable fields for idempotency
comparison. Reusing `event_id` with changes to those fields returns
`409 CONFLICT`. Metadata changes may be ignored or stored as duplicate
annotations, but must not mutate the original event by default.

### `request_messages` Schema

Accepted. The revised contract adds `mneme.message.v0` with common fields:
`role`, `content`, optional `name`, `tool_call_id`, `tool_calls`, and
`metadata`. The context prepare examples now use this schema explicitly.

### Context Prepare Validation

Accepted. The revised contract now validates:

- `budget_tokens > 0`;
- `budget_tokens <= context_window_tokens`;
- `budget_split` values are non-negative;
- `budget_split` sums to `1.0 +/- 0.01`;
- `policy.retrieval.query` is optional and falls back to the latest user message
  in `AUTO` mode.

### `expand_context` Limits

Accepted. The revised contract now requires depth, event-count, and latency
limits. Large graph expansions return truncated results with warning
`RESULT_TRUNCATED`.

### Redaction

Accepted. The revised contract now says redaction is irreversible by default in
v0, applies recursively to JSON/string values and metadata, and must run before
storage, indexing, provider calls, and logs.

### Memory Read Audit

Accepted with a small design constraint. The revised contract requires every
memory read to create a durable audit record. Direct MCP/REST memory tool calls
also create `MEMORY_READ` events by default. `/context/prepare` may rely on its
trace audit entry instead of creating a separate event to avoid retrieval
pollution.

Retrieval filters exclude `MEMORY_READ` events by default.

### REST/MCP Parity

Accepted. The revised contract now states that REST `/v1/tools/*` endpoints use
the same input schema, output `data` schema, limits, trace semantics, and
warnings as MCP tools. REST remains the canonical schema source.

### `fetch_event.neighbors` and Graph Edge Values

Accepted. `fetch_event` now defines direct graph neighbors. `expand_context`
now defines edge values: `PARENT`, `CHILD`, `SEED`, `PREVIOUS`, `NEXT`,
`SEGMENT_MEMBER`, `TOOL_INPUT`, and `TOOL_OUTPUT`.

### Schema Version Negotiation

Accepted. The revised contract states every schema-bound request and persisted
object must include `schema_version`; unsupported schema versions return
`400 BAD_REQUEST`. `/v1/capabilities` now advertises supported versions for all
shared schemas, including messages.

### Restart/Replay

Accepted. The revised contract says adapters must buffer events until Mneme
acknowledges ingestion and replay with stable IDs after adapter or service
restart.

### Streaming Responses

Accepted. The revised contract adds optional `ASSISTANT_MESSAGE_CHUNK` events.
Adapters may either ingest only the final `ASSISTANT_MESSAGE` or ingest chunks
followed by a final message. Retrieval prefers the final message by default.

### Metrics and Sequence Diagram

Partially accepted. A sequence diagram was added. `/v1/metrics` was added as an
optional endpoint, not required for v0, because the core protocol should not
depend on Prometheus-style diagnostics.

### Session Auto-Creation

Accepted. The revised contract explicitly forbids implicit session creation
during event ingestion. Unknown sessions return `404 NOT_FOUND`.

### Adapter Contract Tests

Accepted. The test suite now covers:

- unsupported schema versions;
- message schema validation;
- budget split validation;
- mandatory memory-read audit;
- streaming chunk behavior;
- unknown session rejection;
- graph expansion truncation;
- strict oversized payload handling.

The conformance corpus is now specified as synthetic fixtures with at least
5 sessions, 100 events, and 3 runtime labels.

## Feedback Partially Accepted

### Automatic `MEMORY_READ` for Every Read

The revised spec requires direct tool calls to create `MEMORY_READ` events by
default. It does not require `/context/prepare` to always create an additional
event, because the prepare trace already records selected events, reasons,
latency, token accounting, and privacy actions. This avoids polluting retrieval
with internal prepare activity while preserving durable auditability.

### `/v1/metrics`

Kept optional. It is useful for daemon diagnostics and benchmarks, but not
required for the protocol's first implementation.

## Feedback Not Adopted as Mandatory

No major external feedback was rejected outright. The only constraint I did not
make mandatory is `/v1/metrics`, for the reason above.

## Remaining Review Questions

The revised spec intentionally leaves only review-level questions:

1. Is `mneme.message.v0` sufficient for the first Hermes, Codex/MCP, LangGraph,
   and OpenAI Agents SDK adapters?
2. Is `max_event_content_bytes=1048576` the right default for the reference
   daemon?
3. Should `/v1/metrics` become required for v0, or stay optional?

## Implementation Status

No service, daemon, adapter, SDK, or MCP server implementation has started.
The next step is another external review of the revised contract.
