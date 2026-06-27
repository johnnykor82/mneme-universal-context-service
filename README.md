# Mneme Context Service

Mneme is a local-first, vendor-neutral context memory service for long-running,
tool-using agents. It stores normalized agent events, builds searchable memory,
tracks execution state, and can assemble request-only context for runtimes that
provide a host lifecycle hook.

## What It Provides

- REST API for sessions, event ingestion, context preparation, traces, costs,
  export, and delete.
- MCP server exposing audited memory tools for agents.
- SQLite storage with redaction before persistence, indexing, provider calls,
  traces, and MCP results.
- Hybrid retrieval: keyword, recency, optional embeddings, graph dependency
  expansion, optional reranking.
- Runtime-neutral execution state, goal history, segmentation, session resume
  classification, lineage carry-over, and first-turn resume context fill.
- Budgeted `/v1/context/prepare` with execution-state, retrieved-evidence, and
  protected-tail packing, memory access hints, goal trail, checkpoint hints,
  global candidates, and adapter metadata.

## Integration Depth

Mneme Core exposes host-neutral REST/MCP capabilities. Host-specific lifecycle
behavior belongs in adapters.

- `TOOLS_ONLY`: MCP clients can call memory tools such as `context_search`,
  `fetch_event`, and `expand_context`. This does not automatically replace the
  host runtime's prompt.
- `EVENT_INGEST`: a host adapter maps lifecycle events to Mneme sessions,
  events, and turn completion.
- Deeper levels such as `PREPARE_INPUT` or `CONTEXT_ENGINE` require an adapter
  to own the host pre-model-request lifecycle. Core exposes request-only
  endpoints; it does not secretly mutate host prompts.

See [docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md](docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md)
for the host adapter contract.

## Specification

For architecture/code review, send
[docs/MNEME_STANDALONE_SPEC.md](docs/MNEME_STANDALONE_SPEC.md). It is the
single-file reviewer specification and does not require attaching the rest of
the documentation set.

[docs/MNEME_DEVELOPMENT_SPEC.md](docs/MNEME_DEVELOPMENT_SPEC.md) remains a
historical/index-style specification from the earlier review pass.

## Quick Start

Current source-checkout install:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
export MNEME_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
mneme serve --db .local/mneme.db
```

Health check:

```bash
curl -sS http://127.0.0.1:8765/v1/health
```

`/v1/health` is a liveness check only. REST clients that require Mneme
evidence at run start should use the same token as the daemon/MCP process and
call authenticated session readiness:

```bash
curl -sS -X POST http://127.0.0.1:8765/v1/readiness/session \
  -H "Authorization: Bearer $MNEME_AUTH_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"019edb86-1d22-78a3-b9e4-e6121c294056","query":"RLM Orchestrator MVP 1 benchmark evidence project status","require_evidence":true,"top_k":1}'
```

Run the MCP server as a separate process pointing at the daemon:

```bash
mneme mcp --base-url http://127.0.0.1:8765
```

## Configuration

Start from [mneme.example.toml](mneme.example.toml):

```bash
cp mneme.example.toml mneme.toml
mneme serve --config mneme.toml
```

Provider secrets should come from environment variables, not tracked config:

- `MNEME_EMBEDDING_API_KEY`
- `MNEME_RERANKER_API_KEY`
- `MNEME_LLM_API_KEY`

See [docs/PROVIDER_CONFIGURATION.md](docs/PROVIDER_CONFIGURATION.md).

For installation details, see [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Integrations

Mneme Core stays host-runtime-neutral. Host lifecycle capture, setup commands,
skills, and agent-specific guidance live in host adapters.

For Codex integration, see `johnnykor82/mneme-codex-adapter`. Core documents
the stable adapter contract in
[docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md](docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md).
MCP access is agent-callable memory tooling, not automatic prompt replacement.

## Tests

```bash
.venv/bin/python -m pytest -q
python3 -m py_compile mneme_service/*.py
```

The parity acceptance suite is:

```bash
.venv/bin/python -m pytest tests/test_parity_recovery.py -q
```

See [docs/TESTING_AND_CI.md](docs/TESTING_AND_CI.md).

## Benchmarks

```bash
mneme benchmark --events 30 --db .local/mneme-benchmark.db
```

The benchmark uses local fake providers and makes no external provider calls.
See [docs/BENCHMARKS.md](docs/BENCHMARKS.md).

Vector acceleration status is documented in
[docs/VECTOR_ACCELERATION.md](docs/VECTOR_ACCELERATION.md).

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Project Status

Phase 14C full Hermes-Mneme daemon/core parity completion is complete. The
current test suite covers provider configuration, embeddings, model-change
reindex, hybrid/global retrieval, execution state recovery, segmentation/session
drift, typed graph scoring, budgeted context assembly, optional reranking,
optional LLM enrichment, MCP parity, and parity acceptance behavior. Phase 15
publication preparation is complete with Apache-2.0 licensing.

## Publication Gate

The publication checklist is tracked in
[docs/PUBLICATION_CHECKLIST.md](docs/PUBLICATION_CHECKLIST.md).
Future publication must keep GitHub installation understandable and automatable
for users who do not have this local development environment, with Mneme
engine/core and host adapters published separately. Chosen public repository
names are `johnnykor82/mneme-universal-context-service` for core and
`johnnykor82/mneme-codex-adapter` for the Codex adapter.
