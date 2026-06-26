# Plan: 11-residual-contract-fix-batch-h

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the narrow Section 24 execution-state residuals: canonical JSON byte
hashing for state history and explicit context-prepare trace reporting when
execution state is truncated for budget.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.5, 14.13 | Execution state hash/history and context prepare trace |
| CM-026, CM-047, CM-062 | State history and context prepare Section 24 residuals |
| S24-109 | `state_history_hash_uses_canonical_json_bytes` |
| S24-119 | `context_prepare_trace_reports_execution_state_compression_level` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to confirm exact residuals and minimal
  implementation scope.
- [x] Add failing tests for canonical state hash invariance/hash-chain evidence
  and truncated execution-state trace warnings.
- [x] Implement minimal trace warning propagation for truncated execution state.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/app.py`, `tests/test_state.py`, `tests/test_context_assembly.py`
or `tests/test_context_prepare.py`, `docs/MNEME_V0_COMPLIANCE_MATRIX.md`,
`.planning/findings.md`, `.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_context_assembly.py -q -k "canonical_json_bytes or compression_level"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_context_assembly.py tests/test_context_prepare.py tests/test_openapi.py -q`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| CM-026 / S24-109 | State history hash uses canonical JSON bytes and hash-chain evidence | ✓ met | `tests/test_state.py::test_state_history_hash_uses_canonical_json_bytes`; focused Batch H GREEN -> `2 passed, 14 deselected, 1 warning`; touched-area gate -> `39 passed, 1 warning`; full suite -> `270 passed, 1 warning`. |
| CM-047 / S24-119 | Context prepare trace reports execution-state compression level and truncation warning | ✓ met | `tests/test_context_assembly.py::test_context_prepare_trace_reports_truncated_execution_state_compression_level`; focused RED -> `1 failed, 1 passed, 14 deselected, 1 warning`; focused GREEN -> `2 passed, 14 deselected, 1 warning`; resume-fill regression check -> `3 passed, 14 deselected, 1 warning`; touched-area gate -> `39 passed, 1 warning`; full suite -> `270 passed, 1 warning`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
