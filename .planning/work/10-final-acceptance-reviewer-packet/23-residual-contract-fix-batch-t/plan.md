# Plan: 23-residual-contract-fix-batch-t

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the narrow startup automatic retention sweep residual for S24-67 by
running configured startup sweeps observably and scoped per ended session.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 13.6, 14.2, 18, 24 | Automatic retention sweeps on daemon startup/session close are observable and scoped |
| CM-035, CM-042, CM-061, CM-062 | Session lifecycle, maintenance lifecycle, required tests |
| S24-67 | `automatic_retention_sweeps_are_observable_and_scoped` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Review existing retention cleanup/session-close sweep implementation.
- [x] Add a focused startup sweep regression test.
- [x] Implement the smallest startup sweep hook needed.
- [x] Run focused and touched-area retention verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`tests/test_contract.py`, `mneme_service/app.py`, possibly
`mneme_service/storage.py` only if an existing storage helper is missing,
`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "startup_retention_sweep or retention_sweep"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_storage.py tests/test_metrics.py -q -k "retention or sweep or metrics"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-67 | Automatic retention sweeps are observable and scoped | partial | Startup and session-close sweeps are covered by `tests/test_contract.py::test_startup_retention_sweep_is_observable_and_scoped` and `tests/test_contract.py::test_session_close_retention_sweep_is_observable_and_scoped`; periodic sweep timer remains a separate residual. Batch T focused gate `1 passed`; touched-area gate `9 passed`; full suite `286 passed`. |

**Compliance Status: PARTIAL**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| 1 | Focused startup sweep test before implementation | Old ended-session event remained fetchable after restart with `retention_sweep_on_startup=true`. | Added startup sweep hook using existing cleanup/blob-GC/audit primitives. |
