# Plan: 03-mcp-default-session-stale

## Level

task

## Parent

`.planning/work/08-mcp-parity-default-session-resolution-versioning/plan.md`

## Status

complete

## Goal

Add trusted immutable MCP default-session support with stale-default validation
and MCP-only `DEFAULT_SESSION_STALE`, while preserving the rule that Mneme MCP
does not maintain mutable cross-project current-session state.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 15 | Trusted immutable process/run defaults or host injection may fill omitted session ids. |
| Section 15 | Stale trusted default returns `DEFAULT_SESSION_STALE` with discovery guidance. |
| CM-049 | Default session injection and stale-default error are incomplete. |
| S24-28, S24-57, S24-60, S24-83 | Default trusted session, host injection, stale default, and no mutable current-session drift. |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add failing MCP tests for omitted `session_id` with trusted immutable
  default context, no default context, and stale default context.
- [x] Implement explicit default-session configuration on `create_mcp_server`
  and/or environment loading used by the MCP entrypoint, without adding mutable
  runtime state.
- [x] Validate the trusted default via authenticated session read/readiness on
  first session-bound call and return `DEFAULT_SESSION_STALE` on failure.
- [x] Add `session_resolution.source="TRUSTED_DEFAULT"` or `HOST_INJECTED`
  where applicable.
- [x] Run focused default-session verification and record exact results.

## Expected File Touches

`mneme_service/mcp_server.py`, `mneme_service/rest_client.py`,
`mneme_service/app.py`, `tests/test_mcp_contract.py`, `tests/test_contract.py`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q -k "default_session or stale or session_resolution"`
- Task gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 15 / S24-28,57,60 | Omitted session ids are accepted only from trusted immutable/default injection | ✓ met | RED check failed for missing `default_session_id`; GREEN focused gate after HOST_INJECTED coverage `7 passed, 15 deselected`; MCP+contract gate `50 passed, 1 warning`. |
| Section 15 / S24-83 | Stale defaults return `DEFAULT_SESSION_STALE` | ✓ met | `tests/test_mcp_contract.py::test_mcp_stale_trusted_default_session_returns_specific_error` verifies MCP-only error, non-retryable details, and discovery warning. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
