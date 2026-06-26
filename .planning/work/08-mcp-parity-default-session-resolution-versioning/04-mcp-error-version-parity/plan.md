# Plan: 04-mcp-error-version-parity

## Level

task

## Parent

`.planning/work/08-mcp-parity-default-session-resolution-versioning/plan.md`

## Status

complete

## Goal

Align MCP/REST error mapping and version/schema reporting so MCP clients get
v0 envelopes, retryable flags, and explicit version evidence without tool-name
renaming or silent semantic drift.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 15 | MCP error mapping table and domain error codes. |
| Section 15 | MCP tool names remain unversioned; capabilities expose `mcp_tool_versions`; tool data includes schema versions where applicable. |
| CM-049, CM-050 | Schema version reporting/rejection and error mapping incomplete. |
| S24-30, S24-31, S24-117 | REST/MCP parity, full error mapping, and MCP version rejection/version evidence. |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add failing tests for REST client mapping of 415, 416, `STORAGE_BUSY`,
  retryable 429/503, and non-JSON fallback responses.
- [x] Add tests for MCP tool version/capability evidence and unsupported
  schema/version rejection where the current public contract accepts versioned
  requests.
- [x] Update `MnemeRestClient` and relevant envelope helpers to preserve
  contract error codes and retryable flags.
- [x] Run focused error/version parity verification and record exact results.

## Expected File Touches

`mneme_service/rest_client.py`, `mneme_service/app.py`,
`mneme_service/schemas.py`, `tests/test_mcp_contract.py`,
`tests/test_openapi.py`, `tests/test_contract.py`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_openapi.py tests/test_contract.py -q -k "error_mapping or retryable or mcp_tool_versions or schema_version"`
- Task gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_openapi.py tests/test_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 15 / CM-050 | MCP error mapping matches v0 table | ✓ met | RED focused check failed for missing 415/416 fallback mapping; GREEN focused gate `3 passed, 58 deselected, 1 warning`; touched-area gate `61 passed, 1 warning`. |
| Section 15 / CM-049 / S24-117 | Version/schema evidence and rejection behavior are covered | ✓ met | `mcp_tool_versions` remains asserted in capabilities; unsupported `mneme.tool_request.v99` is rejected with `422 VALIDATION_ERROR` on two REST tool routes. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
