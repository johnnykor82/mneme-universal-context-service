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
mneme serve --db .local/mneme.db
```

The daemon binds to loopback by default.

## Local Storage And At-Rest Guidance

Mneme stores canonical records and server-owned blob bytes in the configured
SQLite database path, for example `.local/mneme.db`. The default v0 runtime has
no optional external blob path; server-owned blob bytes live in SQLite. The
default v0 local storage path does not enable mandatory database encryption.

Use owner-only local storage permissions:

- SQLite database, environment, and token files: `0600`
- Mneme data directories such as `.local`: `0700`

For stronger at-rest protection, place the Mneme data directory on an
OS-encrypted volume or use a deployment that provides SQLCipher-compatible
SQLite encryption. The default local SQLite setup is not enterprise confidential
unless encryption is configured outside the default v0 runtime.

## Operations Runbook

Config changes require restart of the `mneme serve` process. Stop the daemon
with the host service manager or a normal process signal, then start it again
with the same database path and token source.

During stop or restart, in-flight requests may be interrupted. Clients should
retry responses marked `retryable=true`, and mutating callers should use an
`Idempotency-Key` so a retried session start, event batch, turn completion,
context prepare, retention cleanup, blob operation, reindex operation, or
maintenance command can replay safely instead of duplicating work.

Production operators should retain structured logs that include request id,
trace id, endpoint, status, and project or session scope metadata. Mneme does
not log bearer tokens or memory evidence content in operational logs.

## Migration And Release Notes

Stable releases must list tested Python versions and migration impacts. For the
current v0 line, the tested Python versions are 3.11 and 3.12.

Before any destructive migration, startup requires either an explicit backup
path or an explicit operator bypass:

```bash
mneme serve --db .local/mneme.db --backup-before-migrate .local/mneme.before-migrate.db
```

Use `--no-backup-before-migrate` only after an operator has created and verified
an out-of-band backup. Release notes for a version with a destructive migration
must identify the affected schema version, the migration impact, and the backup
or bypass command used during rollout.

Health check:

```bash
curl -sS http://127.0.0.1:8765/v1/health
```

This check only proves the process is alive. Local REST clients must send the
same bearer token configured for `mneme serve` or `mneme mcp`. For a hard
dependency, verify authenticated session usability before the run:

```bash
curl -sS -X POST http://127.0.0.1:8765/v1/readiness/session \
  -H "Authorization: Bearer $MNEME_AUTH_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"019edb86-1d22-78a3-b9e4-e6121c294056","query":"RLM Orchestrator MVP 1 benchmark evidence project status","require_evidence":true,"top_k":1}'
```

## Start The MCP Server

Run the MCP server as a separate process and point it at the REST daemon:

```bash
mneme mcp --base-url http://127.0.0.1:8765
```

The MCP server is a proxy over the REST memory tools. It does not replace the
host runtime's prompt by itself.

## Run The Local Benchmark

```bash
mneme benchmark --events 30 --db .local/mneme-benchmark.db
```

This is a local smoke benchmark with local fake providers and no external
provider calls. It reports benchmark methodology and labeled synthetic quality
metrics, but it has no comparative baseline and is not proof of token or cost
reduction.

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
- run `mneme-codex codex-hook-capture` locally before enabling hook ingestion.

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
publication checklist. Phase 14C daemon/core parity is complete, but public
publication must split the Mneme engine/core from host adapters. The first
mixed repository was made private and should not be used as the public install
source. The next publication work is a clean core repository, a separate Codex
adapter repository/package, and then a second-machine installation rehearsal as
if by a new user. The chosen GitHub names are
`johnnykor82/mneme-universal-context-service` for core and
`johnnykor82/mneme-codex-adapter` for Codex. Ongoing adapter work must preserve
a clear installation story for future GitHub users: explicit prerequisites,
copyable commands, example configs with placeholders, and no hidden dependency
on local private paths.
