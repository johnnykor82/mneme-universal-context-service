# Plan: 02-tool-envelope-session-resolution

## Level

task

## Parent

`.planning/work/08-mcp-parity-default-session-resolution-versioning/plan.md`

## Status

complete

## Goal

Return `session_resolution` metadata from session-bound REST and MCP tool
results so callers can distinguish explicit arguments, trusted defaults, host
injection, and discovery-tool resolution.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.9 | Shared tool envelope includes optional/required `session_resolution`. |
| Section 15 | Tool responses should include resolution source for host-injected/default session behavior. |
| CM-043, CM-049 | Tool results omit session-resolution source. |
| S24-90 | MCP tool results include `session_resolution.source`. |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add failing tests for `session_resolution.source="EXPLICIT_ARGUMENT"`
  and resolved `session_id` on session-bound REST and MCP tool calls.
- [x] Extend tool envelope schema and helper behavior without changing
  non-session-bound tool responses unnecessarily.
- [x] Add `RESOLVED_BY_TOOL` evidence for `resolve_session`/`list_sessions`
  results where applicable.
- [x] Run focused session-resolution verification and record exact results.

## Expected File Touches

`mneme_service/schemas.py`, `mneme_service/app.py`,
`mneme_service/rest_client.py`, `tests/test_contract.py`,
`tests/test_mcp_contract.py`, `tests/test_openapi.py`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py tests/test_openapi.py -q -k "session_resolution or resolve_session"`
- Task gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py tests/test_openapi.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 14.9 / S24-90 | Session-bound tools include resolution metadata | ✓ met | RED focused check failed for missing metadata; GREEN focused check `4 passed, 50 deselected, 1 warning`; touched-area gate `54 passed, 1 warning`. |
| CM-043, CM-049 | REST/MCP envelopes expose source without leaking scope | ✓ met | `ToolResponseEnvelope` now includes typed optional `SessionResolution`; session-bound tools emit `EXPLICIT_ARGUMENT`, concrete resolve emits `RESOLVED_BY_TOOL`, and non-session-bound `list_sessions` remains unannotated. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
