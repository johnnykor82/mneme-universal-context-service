# Installation

## Requirements

- Python 3.11 or 3.12
- Local SQLite database path
- A bearer token for daemon access

## Local Install

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
```

Run tests:

```bash
.venv/bin/python -m pytest -q
```

## Start The REST Daemon

```bash
export MNEME_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
mneme serve --db .local/mneme.db --token "$MNEME_AUTH_TOKEN"
```

The daemon binds to loopback by default.

Health check:

```bash
curl -sS http://127.0.0.1:8765/v1/health
```

## Start The MCP Server

Run the MCP server as a separate process and point it at the REST daemon:

```bash
mneme mcp --base-url http://127.0.0.1:8765 --token "$MNEME_AUTH_TOKEN"
```

The MCP server is a proxy over the REST memory tools. It does not replace the
host runtime's prompt by itself.

## Optional Providers

Provider features are disabled by default. Configure them with `mneme.toml` and
environment variables. See [PROVIDER_CONFIGURATION.md](PROVIDER_CONFIGURATION.md).

For production-like semantic memory, enable embeddings and start the daemon
with `require_embeddings = true` or `--require-embeddings`. This fails fast
when embeddings are missing instead of silently running keyword-only memory.

## Host Adapters

Runtime-specific adapters install separately. A host adapter should connect to
this daemon through the REST/MCP contracts and declare its integration depth
according to [MNEME_HOST_ADAPTER_CONTRACT_V0.md](../MNEME_HOST_ADAPTER_CONTRACT_V0.md).

For Codex Desktop, use the separate adapter repository:
`https://github.com/johnnykor82/mneme-codex-adapter`.
