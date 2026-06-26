# Plan: 06-residual-contract-fix-batch-c

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Implement a narrow idempotency residual fix for `POST
/v1/maintenance/reindex/{job_id}/cancel`: preserve existing final-state
idempotency while adding durable `Idempotency-Key` ledger replay/conflict
semantics.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.8 | Maintenance endpoint reindex cancel contract |
| Section 22 | Mutating maintenance routes use `Idempotency-Key` ledger semantics |
| CM-042, CM-060, CM-062 | Maintenance/idempotency residual and Section 24 mapping |
| S24-75 | Reindex cancel stops future provider calls/writes and remains safely repeatable |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to confirm the minimal helper pattern and
  test placement.
- [x] Add failing tests for reindex cancel replay and conflict with
  `Idempotency-Key`.
- [x] Implement minimal route-level ledger support without changing final-state
  cancel semantics for calls without `Idempotency-Key`.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/app.py`, `tests/test_reindex.py`, possibly
`tests/test_contract.py`, `docs/MNEME_V0_COMPLIANCE_MATRIX.md`,
`.planning/findings.md`, `.planning/progress.md`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py -q -k "cancel and idempotency"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_contract.py tests/test_openapi.py -q`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| CM-060 / Section 22 | Reindex cancel has ledger-backed `Idempotency-Key` replay/conflict | ✓ met | `tests/test_reindex.py::test_reindex_cancel_idempotency_key_replays_and_conflicts`; focused RED -> `1 failed, 12 deselected, 1 warning`; focused GREEN -> `1 passed, 12 deselected, 1 warning`. |
| CM-042 / S24-75 | Reindex cancel preserves safe final-state behavior | ✓ met | Existing final-state and provider-stop tests still pass; touched-area gate `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_contract.py tests/test_openapi.py -q` -> `49 passed, 1 warning`; full suite -> `264 passed, 1 warning`; compileall and diff hygiene passed. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
