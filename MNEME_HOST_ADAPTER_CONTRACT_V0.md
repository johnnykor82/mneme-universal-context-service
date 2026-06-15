# Mneme Host Adapter Contract v0

Date: 2026-06-12
Status: accepted architecture alignment
Scope: host-side integration contract; no daemon, MCP server, or runtime adapter implementation is approved by this document

## Purpose

This document defines the host-side contract that lets agent runtimes integrate
Mneme as a context engine rather than only as callable memory tools.

`API_MCP_CONTRACT_V0.md` remains the authoritative service contract for REST and
MCP. This document defines what an agent host must provide around that service:
lifecycle hooks, capability negotiation, prompt assembly authority, fallback
rules, and adapter conformance tests.

The goal is to avoid writing a completely new conceptual adapter for every
future agent runtime. Existing runtimes may still require thin native adapters,
but new runtimes can implement this contract directly and become Mneme-compatible
by design.

## Decision

Mneme is a universal context service plus a host adapter contract.

It is not a magic external process that can replace any agent's model-bound
prompt without cooperation from that agent. Full context-engine behavior requires
a host runtime hook immediately before the model request is built or sent.

Therefore Mneme exposes two complementary contracts:

1. **Service contract:** REST and MCP APIs for storage, retrieval, context
   preparation, traces, costs, export, and delete.
2. **Host adapter contract:** lifecycle and capability requirements for runtimes
   that want Mneme-prepared context to become the actual model input.

## Non-Goals

- No claim that MCP alone can replace a runtime's internal prompt assembly.
- No requirement that every existing agent runtime immediately support deep
  context-engine integration.
- No runtime-specific implementation in this document.
- No replacement for the REST/MCP schemas in `API_MCP_CONTRACT_V0.md`.
- No provider-specific prompt format beyond normalized `mneme.message.v0`.

## Terms

| Term | Meaning |
|---|---|
| Mneme service | The local daemon implementing REST `/v1` APIs and optional MCP tools. |
| Host runtime | The agent framework or application that owns session execution and model calls. |
| Host adapter | The thin runtime-specific layer that maps host lifecycle hooks to Mneme REST/MCP calls. |
| Deep integration | An adapter that can call `/v1/context/prepare` before a model request and send Mneme's returned messages to the model. |
| Tools-only integration | An adapter that exposes Mneme memory tools but cannot change the model request automatically. |

## Integration Depth Model

Every adapter must declare the deepest integration level it can honestly provide.

| Level | Name | Host capability | Mneme behavior |
|---:|---|---|---|
| 0 | `TOOLS_ONLY` | Host can expose REST or MCP tools to the agent. | Mneme provides searchable memory tools; no automatic prompt replacement is claimed. |
| 1 | `EVENT_INGEST` | Host can send session, event, turn, usage, and tool lifecycle data. | Mneme stores and indexes history; context preparation is not automatically applied. |
| 2 | `PREPARE_INPUT` | Host can filter, reorder, or augment run input before the model call, but may not own every prompt component. | Mneme can prepare a request-limited view where the host hook permits it. |
| 3 | `CONTEXT_ENGINE` | Host calls Mneme immediately before prompt/model request submission and sends the returned message set and optional system addition. | Mneme acts as the active request-only context engine. |
| 4 | `COMPACTION_OWNER` | Host delegates explicit and overflow compaction to the adapter. | Mneme may own compaction strategy in addition to request assembly. |
| 5 | `FULL_RUNTIME` | Adapter or Mneme-owned runner controls model invocation. | Mneme can enforce the full context policy around the provider call. |

Adapters may combine lower-level behavior with higher-level behavior. For
example, a `CONTEXT_ENGINE` adapter should normally also ingest events and expose
memory tools.

## Capability Negotiation

Before enabling automatic context preparation, the adapter must feature-detect
host capabilities and Mneme service capabilities.

The host-side capability object should be equivalent to:

```json
{
  "schema_version": "mneme.host_capabilities.v0",
  "host_id": "example-agent",
  "host_version": "1.2.3",
  "adapter_id": "mneme-example-adapter",
  "adapter_version": "0.1.0",
  "integration_depth": "CONTEXT_ENGINE",
  "capabilities": {
    "event_ingest": true,
    "turn_complete": true,
    "assemble_before_prompt": true,
    "message_rewrite": true,
    "system_prompt_addition": true,
    "history_filter": true,
    "tool_registry": true,
    "tool_result_ingest": true,
    "usage_reporting": true,
    "trace_linking": true,
    "bytes_ref": true,
    "compaction_delegate": false,
    "subagent_lifecycle": false,
    "mcp_client": true
  },
  "unsupported_behavior": "FAIL_CLOSED"
}
```

Capability rules:

- `CONTEXT_ENGINE` requires `assemble_before_prompt=true`.
- `COMPACTION_OWNER` requires `compaction_delegate=true`.
- Automatic prompt/context replacement must not be advertised when
  `assemble_before_prompt=false`.
- If a required capability is missing, the adapter must either fail closed before
  the run or explicitly downgrade to a lower integration depth.
- Downgrades must be visible in logs, traces, or adapter status output.

## Required Lifecycle Hooks

The host adapter maps host lifecycle events to Mneme service calls.

| Hook | Required for | Mneme call | Purpose |
|---|---|---|---|
| `bootstrap_session` | `EVENT_INGEST+` | `POST /v1/sessions/start` | Create or resume the Mneme session before event ingestion. |
| `ingest_events` | `EVENT_INGEST+` | `POST /v1/events` | Store user, assistant, tool, file, error, and decision events. |
| `prepare_model_request` | `CONTEXT_ENGINE+` | `POST /v1/context/prepare` | Prepare request-only context immediately before the model call. |
| `after_model_response` | `EVENT_INGEST+` | `POST /v1/events` | Ingest assistant output, tool calls, tool outputs, and errors. |
| `complete_turn` | `EVENT_INGEST+` | `POST /v1/turns/complete` | Finalize turn status, usage counters, and segment hints. |
| `compact` | `COMPACTION_OWNER+` | future compaction endpoint or adapter-local policy | Delegate explicit or overflow compaction. |
| `prepare_subagent_spawn` | optional | `POST /v1/sessions/start` plus event links | Prepare parent/child context state. |
| `on_subagent_ended` | optional | `POST /v1/events` and `POST /v1/turns/complete` | Finalize child-session state and parent references. |

## `prepare_model_request` Requirements

This is the critical hook for deep context-engine behavior.

The adapter must call `/v1/context/prepare` after the host has determined the
candidate model messages, system/developer prompt material, model name, tool
set, token budget, and session identity, and before the model provider request
is sent.

The adapter must:

- map host messages to `mneme.message.v0`;
- pass stable `session_id`, `turn_id`, and `request_id`;
- pass the active model, tokenizer if known, context window, budget, and policy;
- preserve system/developer prompt authority according to the returned messages;
- if `changed=false`, send the original host request unchanged;
- if `changed=true`, send the returned `messages` for that one model request;
- link the returned `trace_id` to the host run/provider trace when possible;
- never persist Mneme-generated context as canonical conversation history unless
  the host explicitly records a separate memory-read event.

If the host can only append instructions but cannot replace or filter messages,
the adapter must declare `PREPARE_INPUT` or `TOOLS_ONLY`, not `CONTEXT_ENGINE`.

## Memory Tool Requirements

Adapters may expose Mneme memory tools through MCP or through host-native tools.

The minimum tool set is:

- `context_search`
- `fetch_event`
- `expand_context`
- `recall_recent`
- `list_segments`
- `explain_context`
- `mneme_cost_report`

Tool calls must preserve the shared result envelope and audit behavior from
`API_MCP_CONTRACT_V0.md`. Direct memory tool reads must be visible through
durable audit records and memory-read traces. They must not silently mutate the
canonical transcript.

## Event and Identity Requirements

Adapters must provide stable, replay-safe identifiers where the host permits it:

- `session_id`
- `turn_id`
- `event_id`
- `request_id`
- `tool_call_id`
- host/provider trace id, if available

Adapters must buffer events until Mneme acknowledges ingestion. On restart, they
must replay with the same stable ids so duplicate events are counted rather than
duplicated.

## Security and Privacy Requirements

- The adapter must authenticate to the local daemon unless explicitly configured
  for insecure development mode.
- The adapter must not log bearer tokens, raw secrets, or unredacted event
  payloads.
- Redaction remains enforced by the Mneme service before storage, search, traces,
  and derived indexes.
- Adapters should prefer `BYTES_REF` for large command output, binary data,
  artifacts, diffs, and logs.
- Cross-project or cross-session access must follow the privacy/isolation policy
  in `API_MCP_CONTRACT_V0.md`.
- Prompt-control claims in user-facing docs must match the declared integration
  depth.

## Adapter Contract Tests

A v0 host adapter is compatible only after passing tests for its declared depth.

Required for `TOOLS_ONLY`:

1. `memory_tools_are_discoverable`
2. `context_search_fetch_expand_return_shared_envelope`
3. `memory_tool_reads_create_audit_records`
4. `tool_errors_use_standard_shape`
5. `docs_do_not_claim_automatic_prompt_replacement`

Required for `EVENT_INGEST`:

1. `session_start_is_idempotent`
2. `event_replay_is_idempotent_after_restart`
3. `unknown_session_ingest_is_rejected_or_prevented`
4. `turn_complete_records_usage`
5. `redaction_precedes_storage_and_search`

Required for `PREPARE_INPUT`:

1. `prepare_is_called_before_model_call_when_supported`
2. `changed_false_sends_original_request`
3. `budget_and_message_schema_validation_errors_are_visible`
4. `trace_id_links_to_host_run`

Required for `CONTEXT_ENGINE`:

1. `assemble_before_prompt_capability_is_required`
2. `mneme_returned_messages_are_model_bound`
3. `system_messages_are_preserved`
4. `request_only_context_does_not_mutate_transcript`
5. `missing_prompt_hook_fails_closed_or_downgrades`

Required for `COMPACTION_OWNER`:

1. `compact_hook_is_registered`
2. `overflow_recovery_uses_adapter_compaction`
3. `compaction_failure_has_safe_fallback_or_fail_closed_behavior`

Optional for subagent-aware hosts:

1. `subagent_spawn_links_parent_child_sessions`
2. `subagent_end_records_child_summary_or_cleanup`
3. `isolated_subagent_mode_does_not_leak_parent_private_context`

## Compatibility Strategy

### Existing Agents

Existing agents still need thin native adapters because their lifecycle hook
names, prompt authority boundaries, tool registries, and trace systems differ.

The adapter should be thin: normalize host events, call Mneme REST/MCP, enforce
capability negotiation, and map Mneme's response back into host-specific prompt
or tool APIs.

### New Agents

New agent runtimes can implement this contract directly. To be Mneme-ready, a
new runtime should expose:

- a pre-model-call hook equivalent to `prepare_model_request`;
- a post-turn or post-run hook for event ingestion and usage;
- a tool registration surface for Mneme memory tools;
- optional compaction and subagent lifecycle hooks;
- a capability declaration that lets adapters fail closed or downgrade honestly.

### Hermes and OpenClaw-Style Context Engines

Hermes/OpenClaw-style runtimes with native context-engine slots are the deepest
fit. Their native adapter should implement the host context-engine interface and
delegate storage, retrieval, and preparation to Mneme.

### Codex/MCP

Codex/MCP should be documented as `TOOLS_ONLY` unless the runtime exposes a
supported pre-model-call hook. MCP makes Mneme memory callable by the agent, but
does not by itself prove automatic context replacement.

### LangGraph

LangGraph-style applications can usually reach `PREPARE_INPUT` or
`CONTEXT_ENGINE` by inserting a Mneme wrapper node or middleware before model
nodes. The graph remains the owner of graph state unless the application
explicitly writes Mneme-prepared context into state.

### OpenAI Agents SDK

OpenAI Agents SDK adapters should use the deepest available hook for the SDK
version in use. Session input callbacks and model input filters can support
`PREPARE_INPUT` or deeper behavior when they control the final model input for a
turn. MCP tools remain useful but are not the same as prompt replacement.

## Milestone Impact

- Milestone 2 remains focused on the MCP server and Codex/MCP tools-only
  substrate.
- Host Adapter Contract v0 should be treated as a documentation and design
  alignment checkpoint before deeper adapters.
- A later milestone should create a reference host adapter SDK or template that
  implements capability negotiation and the common REST client behavior.
- Runtime-specific adapters should declare their integration depth and pass only
  the tests applicable to that depth.

## Source Notes

The contract is aligned with these current public integration models:

- OpenClaw context engine lifecycle:
  `https://docs.openclaw.ai/concepts/context-engine`
- OpenClaw context model:
  `https://docs.openclaw.ai/concepts/context`
- OpenAI Agents SDK context model:
  `https://openai.github.io/openai-agents-python/context/`
- OpenAI Agents SDK sessions and `session_input_callback`:
  `https://openai.github.io/openai-agents-python/sessions/`
- OpenAI Agents SDK MCP integration:
  `https://openai.github.io/openai-agents-python/mcp/`

These sources support the same boundary: memory/tool access is useful, but data
becomes model-bound context only when the host runtime places it into the model
request through instructions, input/history, or an equivalent prompt assembly
hook.
