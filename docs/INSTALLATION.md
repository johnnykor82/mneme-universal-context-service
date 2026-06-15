# Installation

## Requirements

- Python 3.11 or 3.12
- Local SQLite database path
- A bearer token for daemon access

## Local Development Install

These commands are the current source checkout path. Future public GitHub
releases should keep this flow working and may add a shorter package install
path once distribution packaging is finalized.

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

## Multi-Machine Codex Setup

If two Codex machines share project files through symlinked directories, do not
assume Mneme is installed on both machines just because the shared files are
visible. Shared symlink files can carry docs, skills, snippets, and examples,
but runtime pieces remain per-machine:

- create or verify the local Python environment;
- install the Mneme package or editable checkout;
- start or install `mneme serve` with a local database path;
- configure `mneme mcp` in that machine's Codex environment;
- set local tokens and provider secrets;
- review and trust hook config on that machine;
- run `mneme codex-hook-capture` locally before enabling hook ingestion.

For future automated installers, treat each host as a separate install target
and provide an idempotent per-machine verify command.

## Optional Providers

Provider features are disabled by default. Configure them with `mneme.toml` and
environment variables. See [PROVIDER_CONFIGURATION.md](PROVIDER_CONFIGURATION.md).

For dogfood or public-readiness semantic memory, enable embeddings and start the
daemon with `require_embeddings = true` or `--require-embeddings`. This fails
fast when embeddings are missing instead of silently running keyword-only
memory.

## Public Release Status

Phase 15 publication preparation selected Apache-2.0 and completed the current
publication checklist. Phase 14C daemon/core parity is complete, so the next
publication work is creating or choosing the GitHub repository, publishing
Mneme plus `adapters/codex`, and rehearsing installation on the second Codex
machine as if it were a new user setup. Ongoing adapter work must preserve a
clear installation story for future GitHub users: explicit prerequisites,
copyable commands, example configs with placeholders, and no hidden dependency
on local private paths.
