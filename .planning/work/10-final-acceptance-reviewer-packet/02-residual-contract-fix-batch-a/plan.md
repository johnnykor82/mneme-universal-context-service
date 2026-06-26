# Plan: 02-residual-contract-fix-batch-a

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Implement a bounded security/idempotency residual batch identified by Task 01:
token-file permission hardening and `Idempotency-Key` behavior for remaining
mutating execution-state and segment endpoints.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 9, 17.1 | Token handling and threat boundary hardening |
| Section 22 | Idempotency-Key ledger coverage for mutating routes |
| CM-019, CM-052, CM-060 | Project isolation/token handling/security and idempotency residuals |
| S24 1,4,5,6,7,9 | Idempotency residual group for mutating endpoints |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add failing tests for owner-readable token-file permission rejection.
- [x] Add failing tests for `Idempotency-Key` replay/conflict on execution-state
  update.
- [x] Add failing tests for `Idempotency-Key` replay/conflict on segment
  mutating endpoints where currently uncovered.
- [x] Implement minimal code to pass those tests without changing unrelated
  auth, storage, or endpoint semantics.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/config.py`, `mneme_service/app.py`, `mneme_service/storage.py`,
`tests/test_config.py`, `tests/test_state.py`, `tests/test_segments.py`,
possibly `tests/test_contract.py`.

## Verification Commands

- RED/GREEN focused security:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q -k "token_file"`
- RED/GREEN focused idempotency:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py -q -k "idempotency"`
- Batch gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_state.py tests/test_segments.py tests/test_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Sections 9, 17.1 / CM-019, CM-052 | Token-file permission hardening | ✓ met | `tests/test_config.py::test_auth_token_file_rejects_group_or_world_readable_permissions` and `test_static_token_file_rejects_group_or_world_readable_permissions`; focused RED -> 2 permission failures, GREEN focused -> `8 passed, 30 deselected, 1 warning`. |
| Section 22 / CM-060 / S24 1,4,5,6,7,9 | Idempotency-Key coverage for remaining mutating endpoints | ✓ met | `tests/test_state.py` covers execution-state replay/conflict; `tests/test_segments.py` covers segment close replay/conflict; batch gate `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_state.py tests/test_segments.py tests/test_contract.py -q` -> `66 passed, 1 warning`; compileall and diff hygiene passed. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
