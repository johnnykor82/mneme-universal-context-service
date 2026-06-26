# Plan: 04-reindex-cancel-provider-safety

## Level

task

## Parent

`.planning/work/07-operations-metrics-maintenance-reindex/plan.md`

## Status

complete

## Goal

Implement cooperative reindex cancellation and provider-call safety semantics.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.8 | `POST /v1/maintenance/reindex/{job_id}/cancel`, cooperative cancellation, final-state idempotency |
| Sections 19, 21 | Operational observability and error/warning behavior |
| CM-042, CM-057 | Maintenance and operations gaps |
| S24-75, S24-87 | Cancel endpoint persists cooperative cancellation and final-state idempotency; full provider-call/write stop proof requires Task 05 execution path |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for cancelling `QUEUED`, `WAITING_FOR_PROVIDER`, and
  `RUNNING` jobs.
- [x] Add RED tests proving final states (`COMPLETED`, `FAILED`, `CANCELLED`)
  replay idempotently and do not restart work.
- [x] Add RED tests that cancel stops future provider calls and future
  background writes after the current micro-transaction at the Task 04 boundary;
  full worker-path S24-75 proof is transferred to Task 05.
- [x] Implement cancel endpoint with scope checks and persisted status updates.
- [x] Add metrics/audit/trace evidence for cancellation where current Phase 7
  observability supports it.
- [x] Run focused cancel/reindex tests and record exact results.
- [x] Update this plan's Spec Compliance table and progress.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`,
`tests/test_reindex.py`, possibly `tests/test_metrics.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_metrics.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 14.8 / CM-042 | Reindex cancel semantics exist | ✓ met | `tests/test_reindex.py` covers `WAITING_FOR_PROVIDER`, `QUEUED`, manually seeded `RUNNING`, and persisted `CANCELLED` status. |
| Section 19 / CM-057 | Cancellation is observable and safe at endpoint boundary | ✓ met | Session-scoped cancel writes safe `REINDEX_CANCEL` audit evidence and metrics expose `mneme_reindex_jobs_total{status="CANCELLED"}`. |
| S24-87 | Final-state cancel idempotency tests pass | ✓ met | `COMPLETED` final-state cancel preserves status/history; repeated `CANCELLED` cancel returns the same job. |
| S24-75 | Provider/write stop after cancellation | ✓ met for Task 04 boundary; full worker proof transferred | Current cancel endpoint performs no provider calls or background writes and preserves zero progress for cancelled queued jobs; full post-cancel worker checkpoint proof requires the Task 05 execution engine and is explicitly added there. |

**Compliance Status: VERIFIED**

## Verification Evidence

- RED audit check:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py -q -k "cancel_queued_job"`
  -> `1 failed, 6 deselected, 1 warning` because `REINDEX_CANCEL` audit was
  missing.
- Focused task gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_metrics.py -q`
  -> `10 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> pass.
- Diff hygiene:
  `git diff --check` -> pass.

## Implementation Evidence

- Extended `tests/test_reindex.py` for persisted waiting/queued/running cancel,
  repeated cancel idempotency, final-state preservation, no provider calls
  during cancel, zero progress after queued cancel, metrics bucket, and
  session-scoped `REINDEX_CANCEL` audit.
- Updated `/v1/maintenance/reindex/{job_id}/cancel` to persist cancellation
  through `Store.update_reindex_job` and write safe audit evidence for
  session-scoped jobs.
- Spark worker `019efd97-2eb4-7e92-8ca0-bca1fbe6e47d` reviewed the boundary and
  recommended leaving full S24-75 worker-path proof to Task 05 because no
  reindex execution engine exists before that task.

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
