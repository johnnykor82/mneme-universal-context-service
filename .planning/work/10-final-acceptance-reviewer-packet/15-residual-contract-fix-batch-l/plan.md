# Plan: 15-residual-contract-fix-batch-l

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the Section 24 session export residual by enforcing
`include_audit=false` as the JSON export default while preserving explicit
`include_audit=true` audit evidence for authorized callers.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.2 | Session export query parameters and audit inclusion policy |
| CM-035, CM-062 | Session lifecycle/export residuals |
| S24-2, S24-3, S24-48, S24-49, S24-91, S24-92 | Session lifecycle and export edge coverage |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add failing tests for default `include_audit=false` and explicit
  `include_audit=true`.
- [x] Implement minimal JSON export audit inclusion control.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`, `tests/test_blobs.py`,
`tests/test_contract.py`, `docs/MNEME_V0_COMPLIANCE_MATRIX.md`,
`.planning/findings.md`, `.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py -q -k "export or memory_tools_audit or cost_report"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_openapi.py -q -k "export or audit or openapi"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-2/S24-3/S24-48/S24-49/S24-91/S24-92 | JSON export defaults audit records off and includes them only by explicit authorized request | ✓ met | `tests/test_blobs.py::test_session_export_json_excludes_audit_by_default_and_includes_on_request`; existing audit evidence tests now request `include_audit=true`; RED -> `1 failed, 7 passed, 45 deselected, 1 warning`; focused GREEN -> `8 passed, 45 deselected, 1 warning`; touched-area gate -> `17 passed, 44 deselected, 1 warning`; MCP regression -> `1 passed, 24 deselected`; full suite -> `277 passed, 1 warning`; compileall and `git diff --check` clean. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| 1 | `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` | `tests/test_mcp_contract.py::test_mcp_memory_tools_write_audit_records_and_traces` still expected audit records from default export. | Update the MCP audit-evidence test to request `include_audit=true`, then rerun focused MCP and full verification. |
