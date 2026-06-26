# Plan: 03-idempotency-key-ledger

## Level

task

## Parent

`.planning/work/02-storage-migrations-writer-idempotency/plan.md`

## Status

complete

## Goal

Add a durable `Idempotency-Key` ledger for currently implemented mutating
endpoints.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 22 / CM-060 | Header name, compatible replay, incompatible replay conflict, retention minimum |
| S24-1, 6, 7, 9, 48 | Current session/event/turn/delete idempotency semantics |

## Active Step

Active Task: none (leaf)

## Steps

- [x] Add ledger storage table and canonical request fingerprinting.
  - Verification: REST-level contract tests verify replay/conflict behavior without using direct SQLite as the contract substitute.
- [x] Apply ledger to `/v1/sessions/start`, `/v1/events`, `/v1/turns/complete`, `/v1/context/prepare`, and `DELETE /v1/sessions/{id}`.
  - Verification: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_idempotency_key_replays_session_start_and_rejects_conflict tests/test_contract.py::test_idempotency_key_replays_event_batch_and_rejects_conflict tests/test_contract.py::test_idempotency_key_replays_turn_complete_and_rejects_conflict tests/test_contract.py::test_idempotency_key_replays_context_prepare_and_rejects_conflict tests/test_contract.py::test_idempotency_key_replays_delete_session -q` -> `5 passed, 1 warning`.
- [x] Reject same key with incompatible body as `409 CONFLICT`.
  - Verification: the same focused idempotency tests assert uniform `CONFLICT` error code for incompatible replay.
- [x] Preserve stable-id duplicate behavior where no `Idempotency-Key` is supplied.
  - Verification: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_security.py tests/test_openapi.py -q` -> `40 passed, 1 warning`.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 22 / CM-060 | ✓ met for currently implemented mutating endpoints | Durable ledger in `mneme_service/storage.py`, route helpers in `mneme_service/app.py`, replay/conflict tests in `tests/test_contract.py`. |
| S24-1 / 6 / 7 / 9 / 48 | ✓ met for current endpoint scope | Session/event/turn/context-prepare/delete compatible and incompatible replay covered; generated-id, segment, blob, and maintenance idempotency remain mapped to later endpoint phases. |

**Compliance Status: VERIFIED**

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|

## Notes

- Blob/segment/retention/maintenance endpoint idempotency is implemented when
  those endpoints land in their phases.
- Session close and execution-state update idempotency are also tied to later
  endpoint implementation phases; this task only covers routes currently
  implemented in the service.
