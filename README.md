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

Mneme has two integration modes:

- `TOOLS_ONLY`: MCP clients can call memory tools such as `context_search`,
  `fetch_event`, and `expand_context`. This does not automatically replace the
  host runtime's prompt.
- `CONTEXT_ENGINE`: a host adapter calls REST lifecycle hooks, including
  `/v1/context/prepare`, before model requests. This is required for automatic
  request-context assembly.

See [MNEME_HOST_ADAPTER_CONTRACT_V0.md](MNEME_HOST_ADAPTER_CONTRACT_V0.md) for
the host adapter contract.

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
  -d '{"session_id":"example-session","query":"project status and next action","require_evidence":true,"top_k":1}'
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

## Host Adapters

This repository's primary package is the Mneme engine/core. Runtime-specific
adapters connect to Mneme through the REST/MCP contracts. MCP gives
tool-capable hosts agent-callable memory tools; automatic request-context
assembly requires a host lifecycle hook as defined in
[MNEME_HOST_ADAPTER_CONTRACT_V0.md](MNEME_HOST_ADAPTER_CONTRACT_V0.md).

The repository also carries Codex reference docs and helper code used by the
current compatibility tests. Codex Desktop users should prefer the separate
adapter package for installation:

[johnnykor82/mneme-codex-adapter](https://github.com/johnnykor82/mneme-codex-adapter).

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

Mneme v0 compliance work targets
[docs/MNEME_STANDALONE_SPEC.md](docs/MNEME_STANDALONE_SPEC.md). The current
test suite covers provider configuration, embeddings, model-change
reindex, hybrid/global retrieval, execution state recovery, segmentation/session
drift, typed graph scoring, budgeted context assembly, optional reranking,
optional LLM enrichment, MCP parity, and parity acceptance behavior.

## Publication Gate

This repository keeps internal planning files, local development notes, and
unrelated project artifacts out of the public history. Host-specific adapter
release packaging remains separate from the core service package.
