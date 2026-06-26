# Plan: 01-baseline-storage-red-tests

## Level

task

## Parent

`.planning/work/02-storage-migrations-writer-idempotency/plan.md`

## Status

complete

## Goal

Identify current storage/idempotency behavior, then add focused RED tests for
the first Phase 2 implementation slices.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 18 / CM-056 | WAL, busy timeout, schema version, migrations, startup integrity |
| Section 22 / CM-060 | `Idempotency-Key` ledger and compatible/incompatible replay |
| S24-1, 6, 7, 9, 40-42, 56, 71, 113 | Phase 2 required test targets |

## Active Step

Active Task: none (leaf)

## Steps

- [x] Inspect current storage initialization, connection, and mutating endpoint behavior.
  - Verification: `rg -n "CURRENT_SCHEMA_VERSION|schema_migrations|idempotency|busy_timeout" mneme_service/storage.py tests/test_storage.py tests/test_contract.py` confirmed the Phase 2 surface and later implementation points.
- [x] Add RED migration/startup integrity tests.
  - Verification: initial `tests/test_storage.py` focused run failed on missing `CURRENT_SCHEMA_VERSION`; after implementation `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py -q` -> `3 passed`.
- [x] Add RED idempotency ledger tests for current mutating endpoints.
  - Verification: initial focused idempotency run failed for session start replay, event batch replay, and delete replay; after route ledger implementation the five endpoint-focused tests -> `5 passed, 1 warning`.
- [x] Add deterministic writer/busy behavior tests.
  - Verification: added deterministic queue-depth and storage-busy envelope coverage; `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_security.py tests/test_openapi.py -q` -> `40 passed, 1 warning`.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 18 / CM-056 | ✓ met for baseline/task scope | RED/green tests added in `tests/test_storage.py` and writer/busy checks in `tests/test_contract.py`; focused suite `40 passed, 1 warning`. |
| Section 22 / CM-060 | ✓ met for baseline/task scope | `Idempotency-Key` RED/green contract tests cover start/events/turn/context-prepare/delete replay and conflict. |
| S24 Phase 2 targets | ✓ mapped for baseline/task scope | Tests now cover S24-40/42/56/71/113 and current endpoint idempotency targets; final matrix update remains in task 05. |

**Compliance Status: VERIFIED**

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|
| Idempotency replay returned ordinary duplicate/404 behavior instead of first response | RED focused contract tests | Added durable idempotency table plus route-level replay/conflict helpers. |
| New delete replay test temporarily referenced `restarted` from a previous test | RED test cleanup | Moved the existing export-after-delete assertion back into the restart/delete test before implementing ledger behavior. |

## Notes

- Do not mark CM-056/CM-060 compliant until implementation and verification land.
