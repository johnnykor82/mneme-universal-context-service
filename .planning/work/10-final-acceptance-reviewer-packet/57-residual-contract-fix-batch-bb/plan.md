# Plan: 57-residual-contract-fix-batch-bb

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-057` by adding test-guarded operations runbook guidance for
stop/restart, config-change restart expectations, in-flight request behavior,
and retry/idempotency guidance.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 19 / CM-057 | Operations and deployment evidence must describe runtime operations, restart/stop behavior, and release/runbook expectations. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Use Spark/read-only audit to identify smallest safe CM-057 slice. | Spark `019f003a-aea8-71d2-9336-673c4f81f535` recommended docs/test slice for stop/restart and in-flight behavior. |
| 2 | complete | Add RED documentation regression test for operations runbook guidance. | Focused docs pytest failed before update: `1 failed, 1 passed, 13 deselected`. |
| 3 | complete | Add concise operations runbook section to installation/testing docs. | Focused docs pytest passed after update: `2 passed, 13 deselected`. |
| 4 | complete | Run touched verification and update matrix/planning evidence. | `tests/test_codex_adapter.py -q` -> `15 passed`; compileall exit 0; `git diff --check` exit 0. |

## Expected File Touches

- `tests/test_codex_adapter.py`
- `docs/INSTALLATION.md`
- `docs/TESTING_AND_CI.md`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/progress.md`
- `.planning/findings.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q -k "operations_runbook or at_rest"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-057 stop/restart operations runbook residual | ✓ met | `docs/INSTALLATION.md` and `docs/TESTING_AND_CI.md` describe config-change restart, in-flight interruption, `retryable=true`, `Idempotency-Key`, and structured-log fields; `tests/test_codex_adapter.py::test_operations_runbook_describes_restart_and_in_flight_behavior`; docs gate `15 passed`; compile/diff clean. |

**Compliance Status: VERIFIED**
