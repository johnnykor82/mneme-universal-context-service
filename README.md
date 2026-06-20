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

For architecture/code review, start with
[docs/MNEME_DEVELOPMENT_SPEC.md](docs/MNEME_DEVELOPMENT_SPEC.md). It ties the
business requirements, product boundary, functional requirements, architecture,
contracts, security model, tests, and traceability links into one reviewer-facing
index spec.

## Quick Start

Current source-checkout install:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
export MNEME_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
mneme serve --db .local/mneme.db --token "$MNEME_AUTH_TOKEN"
```

Health check:

```bash
curl -sS http://127.0.0.1:8765/v1/health
```

Run the MCP server as a separate process pointing at the daemon:

```bash
mneme mcp --base-url http://127.0.0.1:8765 --token "$MNEME_AUTH_TOKEN"
```

## Configuration

Start from [mneme.example.toml](mneme.example.toml):

```bash
cp mneme.example.toml mneme.toml
mneme serve --config mneme.toml --token "$MNEME_AUTH_TOKEN"
```

Provider secrets should come from environment variables, not tracked config:

- `MNEME_EMBEDDING_API_KEY`
- `MNEME_RERANKER_API_KEY`
- `MNEME_LLM_API_KEY`

See [docs/PROVIDER_CONFIGURATION.md](docs/PROVIDER_CONFIGURATION.md).

For installation details, see [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Adapter Status

This development checkout currently contains Codex adapter work under
`adapters/codex` while the public split is being prepared. The public engine
repository should keep host adapters out of the core package; Codex-specific
hooks, skills, and setup docs belong in a separate adapter repository/package.

Codex can use Mneme through MCP as agent-callable memory tools. This is
tools-only integration, not automatic prompt replacement.

- [adapters/codex/CODEX_AGENT_INSTALL.md](adapters/codex/CODEX_AGENT_INSTALL.md)
- [adapters/codex/CODEX_DESKTOP_QUICKSTART.md](adapters/codex/CODEX_DESKTOP_QUICKSTART.md)
- [adapters/codex/MNEME_CODEX_MCP_USAGE.md](adapters/codex/MNEME_CODEX_MCP_USAGE.md)
- [adapters/codex/MNEME_CODEX_INGEST_USAGE.md](adapters/codex/MNEME_CODEX_INGEST_USAGE.md)
- [adapters/codex/MNEME_CODEX_HOOKS_USAGE.md](adapters/codex/MNEME_CODEX_HOOKS_USAGE.md)

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
