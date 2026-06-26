# Plan: 04-writer-lane-storage-busy

## Level

task

## Parent

`.planning/work/02-storage-migrations-writer-idempotency/plan.md`

## Status

complete

## Goal

Add the current-process serialized write boundary and storage busy/rate-limit
error surfaces required before heavier background jobs arrive.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 18 / CM-056 | Busy timeout, serialized writes, bounded queue, foreground priority |
| Section 21 | `429 RATE_LIMITED` and `503 STORAGE_BUSY` retryable envelopes |
| S24-40, 65, 82, 113 | Writer queue, foreground priority, micro-transaction/yield, SQLite busy |

## Active Step

Active Task: none (leaf)

## Steps

- [x] Add deterministic tests around busy timeout/queue behavior that do not rely on flaky timing.
  - Verification: `tests/test_contract.py::test_writer_queue_depth_limit_returns_retryable_429` holds a writer slot and verifies `429 RATE_LIMITED`; `tests/test_storage.py::test_store_initializes_schema_version_migration_history_and_busy_timeout` verifies nonzero SQLite `busy_timeout`.
- [x] Introduce a small writer-lane abstraction for current foreground writes.
  - Verification: runtime write methods now use `Store.write_connect()`/`WriterLane`; `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_security.py tests/test_openapi.py -q` -> `40 passed, 1 warning`.
- [x] Return retryable error envelopes for configured full/busy conditions.
  - Verification: `tests/test_contract.py::test_writer_queue_depth_limit_returns_retryable_429` checks `RATE_LIMITED`; `tests/test_contract.py::test_storage_busy_returns_retryable_503` checks `STORAGE_BUSY`.
- [x] Avoid long-running background-job design until reindex/retention phases.
  - Verification: this task only adds the foreground writer lane/error surface; background reindex/retention priority and micro-transaction behavior remain in phases 07/09 where those jobs are implemented.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 18 / CM-056 | ✓ met for current foreground writer scope | `WriterLane` serializes Store writes with bounded queue depth and SQLite `busy_timeout`; focused suite `40 passed, 1 warning`. |
| Section 21 / S24-40 / 65 / 82 / 113 | ✓ met for current scope; later background portions tracked | Retryable `RATE_LIMITED`/`STORAGE_BUSY` envelopes covered; foreground priority over future background jobs and reindex micro-transaction/yield semantics remain tied to later maintenance/reindex implementation. |

**Compliance Status: VERIFIED**

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|
