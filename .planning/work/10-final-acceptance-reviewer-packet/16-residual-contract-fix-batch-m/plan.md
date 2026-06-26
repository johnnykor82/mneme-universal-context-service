# Plan: 16-residual-contract-fix-batch-m

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the Section 24 trace/cost REST residual by documenting
`/v1/traces/{trace_id}` and `/v1/costs/session/{session_id}` with typed
OpenAPI response schemas while preserving existing runtime payloads.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.6, 14.7 | Trace and cost report response schemas |
| CM-041, CM-058, CM-062 | Trace/cost endpoint residuals |
| S24-44 | `trace_and_cost_rest_endpoints_return_expected_schemas` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to confirm minimal response-model scope.
- [x] Add failing OpenAPI test for trace/cost response schema refs.
- [x] Add minimal Pydantic response models and route `response_model` bindings.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/schemas.py`, `tests/test_openapi.py`,
`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q -k "trace or cost or core_v0"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_contract.py tests/test_mcp_contract.py -q -k "trace or cost or openapi or memory_tools_write_audit"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-44 | Trace and cost REST endpoints return expected typed schemas | ✓ met | `tests/test_openapi.py::test_openapi_documents_trace_and_cost_response_models`; RED -> `1 failed, 1 passed, 7 deselected, 1 warning`; focused GREEN -> `2 passed, 7 deselected, 1 warning`; touched-area gate -> `14 passed, 54 deselected, 1 warning`; full suite -> `278 passed, 1 warning`; compileall and `git diff --check` clean. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| 1 | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_contract.py tests/test_mcp_contract.py -q -k "trace or cost or openapi or memory_tools_write_audit"` | `TraceResponse.created_at_ms` and `CostReportResponse.llm_enrichment_calls` were too strict for existing runtime payloads. | Keep schema properties but make compatibility fields optional/defaulted, preserving runtime payload shape. |
