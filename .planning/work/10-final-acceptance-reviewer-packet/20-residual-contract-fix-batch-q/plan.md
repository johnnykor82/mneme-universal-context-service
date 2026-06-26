# Plan: 20-residual-contract-fix-batch-q

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the narrow S24-113 contract-proof residual by adding a focused foreground
writer queue saturation test that proves retryable `429 RATE_LIMITED` behavior.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 18, 21, 23 | Serialized writer lane and retryable queue-full errors |
| CM-056, CM-059, CM-062 | Storage/concurrency, errors, required tests |
| S24-113 | `writer_queue_depth_limit_returns_retryable_429` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to isolate the residual.
- [x] Add a focused failing contract test for S24-113.
- [x] Implement the smallest runtime/test adjustment needed.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`tests/test_contract.py`, possibly `mneme_service/app.py` only if the existing
error envelope does not match the required contract, `docs/MNEME_V0_COMPLIANCE_MATRIX.md`,
`.planning/findings.md`, `.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "writer_queue_depth_limit"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_storage.py -q -k "writer_queue or storage_busy or schema_version"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-113 | Writer queue depth limit returns retryable 429 | compliant | `tests/test_contract.py::test_writer_queue_depth_limit_returns_retryable_429`; Batch Q touched-area gate `3 passed`; full suite `282 passed`. |

**Compliance Status: COMPLIANT**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
