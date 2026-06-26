# Codex Dogfood Restart Setup

This handoff prepares a new Codex session to test Mneme through MCP. It keeps live Hermes and live `hermes-mneme` untouched.

This file is a local dogfood reference, not a public installer. Replace
absolute paths and `<mneme-auth-token>` for each machine.

Current local status:

- Mneme REST is installed as a LaunchAgent from `.local/com.openclaw.mneme-dogfood.plist`.
- The daemon listens on `http://127.0.0.1:8767`.
- `$HOME/.codex/config.toml` has been updated with `[mcp_servers.mneme]`.
- A backup exists at `$HOME/.codex/config.toml.bak-mneme-dogfood`.
- `adapters/codex/transcript.example.json` has been imported into `.local/mneme-dogfood.db`.

Mneme integration depth for this dogfood is `TOOLS_ONLY` plus offline/reference transcript ingestion:

- REST daemon stores sessions/events.
- `mneme codex-ingest` imports a provided transcript JSON through REST.
- `mneme mcp` exposes read-side memory tools to Codex.
- MCP does not write normal transcript events and does not automatically replace Codex prompt context.

## 1. REST Daemon

Already installed for dogfood through launchctl. Manual equivalent, from the project root:

```bash
cd /path/to/mneme-universal-context-service
export MNEME_AUTH_TOKEN="<mneme-auth-token>"
mkdir -p .local
.venv/bin/python -m mneme_service.cli serve \
  --db .local/mneme-dogfood.db \
  --port 8767
```

## 2. Example Transcript

Already imported once. Manual equivalent:

```bash
cd /path/to/mneme-universal-context-service
export MNEME_AUTH_TOKEN="<mneme-auth-token>"
.venv/bin/python -m mneme_service.cli codex-ingest \
  --input adapters/codex/transcript.example.json \
  --base-url http://127.0.0.1:8767
```

Expected first import result:

- `session.created` is `true`
- `events.accepted` is `3`
- `events.duplicates` is `0`

Expected second import result:

- `session.created` is `false`
- `events.accepted` is `0`
- `events.duplicates` is `3`

## 3. Codex MCP Config

Already added to `$HOME/.codex/config.toml`. The snippet is also saved in `adapters/codex/codex_mcp_dogfood.example.json`.

It intentionally uses an absolute Python executable plus `PYTHONPATH` so the MCP process can import this project even when Codex starts it from another working directory.

Do not point this at live Hermes or live `hermes-mneme`.

## 4. Restart Codex

Restart Codex so the new MCP server is loaded. Then send the prompt from `adapters/codex/MNEME_CODEX_NEW_SESSION_PROMPT.md`.

## Expected MCP Tools

The new Codex session should see Mneme memory tools, usually under an MCP namespace for `mneme`:

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

The imported example transcript contains:

- session id: `codex-example-session`
- searchable text: `focused pytest passed`
- expected tool-output event id: `codex-codex-example-session-turn-1-0003`

## Troubleshooting

If tools are not visible after restart:

- confirm the REST daemon is still running on `http://127.0.0.1:8767`;
- confirm the token in Codex MCP config equals the local `<mneme-auth-token>`;
- confirm the config command points to `/path/to/mneme-universal-context-service/.venv/bin/python`;
- confirm `PYTHONPATH` is `/path/to/mneme-universal-context-service`;
- restart Codex again after config changes.
