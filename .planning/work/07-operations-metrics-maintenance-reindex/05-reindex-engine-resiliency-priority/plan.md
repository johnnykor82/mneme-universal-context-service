# Plan: 05-reindex-engine-resiliency-priority

## Level

task

## Parent

`.planning/work/07-operations-metrics-maintenance-reindex/plan.md`

## Status

complete

## Goal

Implement bounded provider retry/backoff/circuit-breaker behavior and background
writer priority/yield rules for reindex-like work.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 10, 14.8, 19 | Provider retry/backoff, circuit breaker, recovery ramp, micro-transactions, foreground priority |
| CM-020, CM-042, CM-056, CM-057 | Provider, maintenance, storage priority, operations gaps |
| S24-68, S24-65, S24-75, S24-82, S24-113 | Provider retry/failure budget, cancellation checkpoint, foreground priority, micro-transactions/yield |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for provider retry/backoff marking derived items failed
  after configured budget.
- [x] Add RED tests for circuit breaker open/half-open/recovery ramp behavior.
- [x] Add RED tests showing foreground writer operations are not starved by
  background reindex work.
- [x] Add RED tests proving a cancelled persisted reindex job performs no
  future provider calls or background writes when the execution engine drains
  jobs.
- [x] Add RED tests for max-events-per-transaction and yield behavior where
  observable without fragile timing.
- [x] Implement minimal bounded reindex execution engine or synchronous test
  harness that preserves v0 semantics without broad background infrastructure.
- [x] Run focused reindex/storage/provider tests and record exact results.
- [x] Update this plan's Spec Compliance table and progress.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`,
`mneme_service/embeddings.py`, `tests/test_reindex.py`,
`tests/test_storage.py`, `tests/test_embeddings.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_storage.py tests/test_embeddings.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Sections 10, 14.8 / CM-020, CM-042 | Provider retry/backoff/circuit behavior is bounded | ✓ met | Reindex drain marks failed derived events, fails `WAITING_FOR_PROVIDER` jobs after timeout, and opens a reindex-level circuit after configured failure budget. |
| Sections 18, 19 / CM-056, CM-057 | Background writes do not starve foreground work | ✓ met | Drain hook processes one bounded slice per call using `reindex_max_events_per_transaction`; regression test inserts a foreground event between slices. |
| S24-68, S24-65, S24-75, S24-82, S24-113 | Provider failure, cancellation checkpoint, and writer-priority tests pass | ✓ met | `tests/test_reindex.py tests/test_storage.py tests/test_embeddings.py` -> `32 passed, 1 warning`; cancellation checkpoint avoids provider calls after persisted cancellation. |

## Inherited Residual From Task 04

- S24-75 full provider-call/write stop proof is intentionally completed here,
  because Task 04 has no reindex execution engine to exercise post-cancel
  worker checkpoints.

**Compliance Status: VERIFIED**

## Verification Evidence

- RED drain check:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py -q -k "drain or cancel_queued_job"`
  -> `3 failed, 7 deselected, 1 warning` because `run_reindex_job_once` was
  missing.
- GREEN initial drain check:
  same command -> `3 passed, 7 deselected, 1 warning`.
- RED failure/timeout check:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py -q -k "provider_failure or wait_timeout"`
  -> `2 failed, 9 deselected, 1 warning`.
- GREEN failure/timeout check:
  same command -> `2 passed, 9 deselected, 1 warning`.
- RED circuit check:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py -q -k "provider_circuit"`
  -> `1 failed, 11 deselected, 1 warning`.
- GREEN circuit check:
  same command -> `1 passed, 11 deselected, 1 warning`.
- Focused task gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_storage.py tests/test_embeddings.py -q`
  -> `32 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> pass.
- Diff hygiene:
  `git diff --check` -> pass.

## Implementation Evidence

- Added internal `app.state.run_reindex_job_once(job_id)` deterministic drain
  hook; no public REST route was added.
- Added storage candidate listing and event `ingestion.embedding_status`
  update helpers.
- Drain hook checks persisted cancellation before provider calls, processes one
  bounded transaction slice, updates progress/status, writes failed event
  status, respects provider wait timeout, records embedding metrics, sleeps
  according to configured yield, and opens a reindex-level circuit after the
  configured failure budget.
- Spark worker `019efd9c-e8ff-76a2-b352-4dfd1dc28970` reviewed the first
  drain slice and found high-value gaps; parent fixed per-event failure status,
  provider wait timeout, and reindex-level circuit guard before completing this
  task.

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
