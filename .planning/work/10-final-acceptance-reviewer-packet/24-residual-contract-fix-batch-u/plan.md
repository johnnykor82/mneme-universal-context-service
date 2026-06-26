# Plan: 24-residual-contract-fix-batch-u

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the narrow S24-86 forced active retention cleanup conflict residual by
tracking in-flight memory reads and returning `409 CONFLICT` with
`details.reason=IN_FLIGHT_READS` when active cleanup would race a read.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 14.2, 16, 21, 24 | Forced active cleanup must reject concurrent in-flight memory reads with uniform conflict error |
| CM-035, CM-051, CM-059, CM-062 | Session lifecycle, memory-read audit/trace, errors, required tests |
| S24-86 | `retention_cleanup_request_response_and_force_conflict_contract` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Inspect memory-read tool response/audit flow and retention cleanup guard.
- [x] Add a focused forced-active cleanup in-flight-read conflict test.
- [x] Implement the smallest in-flight read tracker and cleanup guard.
- [x] Run focused and touched-area retention/memory-read verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`tests/test_contract.py`, `mneme_service/app.py`,
`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "in_flight_reads or retention_cleanup"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_mcp_contract.py -q -k "retention or memory_read or in_flight"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-86 | Retention cleanup request/response and forced active conflict contract | compliant | `tests/test_contract.py::test_retention_cleanup_force_active_conflicts_with_in_flight_reads`; focused Batch U gate `5 passed`; touched-area gate `9 passed`; full suite `287 passed`. |

**Compliance Status: COMPLIANT**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
