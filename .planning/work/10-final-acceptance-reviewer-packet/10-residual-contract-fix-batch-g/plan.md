# Plan: 10-residual-contract-fix-batch-g

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the narrow S24-8 residual for `/v1/turns/complete`: explicit failed,
interrupted, and cancelled final statuses should be accepted and invalid status
values rejected without changing unrelated turn persistence behavior.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.4, 14.4 | Turn schema and turn completion endpoint |
| CM-025, CM-037, CM-062 | Turn schema/endpoint residual and Section 24 mapping |
| S24-8 | Failed, interrupted, and cancelled turn completion status acceptance |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to confirm exact statuses and test
  placement.
- [x] Add failing tests for final turn status acceptance/rejection.
- [x] Implement minimal validation/result behavior in `/v1/turns/complete`.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/app.py`, likely `tests/test_contract.py`,
`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "turn_complete"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py -q`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| CM-025, CM-037 / S24-8 | Turn completion final status enum behavior | ✓ met | `tests/test_contract.py::test_turn_complete_accepts_failed_interrupted_cancelled_and_rejects_conflicts`; focused RED -> `1 failed, 1 passed, 28 deselected, 1 warning`; focused GREEN -> `2 passed, 28 deselected, 1 warning`; touched-area gate -> `38 passed, 1 warning`; Codex ingest compatibility gate -> `4 passed, 31 deselected, 1 warning`; full suite -> `268 passed, 1 warning`; compileall and diff hygiene passed. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
