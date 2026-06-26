# Plan: 03-reindex-create-poll-scope-idempotency

## Level

task

## Parent

`.planning/work/07-operations-metrics-maintenance-reindex/plan.md`

## Status

complete

## Goal

Implement reindex job creation and polling with authorization scope,
idempotency, status/progress persistence, and provider availability handling.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.8 | `POST /v1/maintenance/reindex`, `GET /v1/maintenance/reindex/{job_id}`, job schema/status/progress, scope checks |
| Sections 10, 21, 22 | Provider availability, error envelopes, idempotency |
| CM-020, CM-042, CM-057, CM-060 | Provider status, maintenance endpoint, observability, idempotency |
| S24-52, S24-63 | Reindex enqueue and polling status/progress |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for scoped/owner reindex create permissions and
  out-of-scope `404`/`403` behavior.
- [x] Add RED tests for `Idempotency-Key` compatible replay and incompatible
  conflict on create.
- [x] Add RED tests for `QUEUED`, `WAITING_FOR_PROVIDER`, and progress fields
  on create/poll.
- [x] Implement persistent reindex job records and minimal job candidate
  selection for `PENDING`/`FAILED`/`force=true`.
- [x] Implement provider unavailable behavior:
  `503 PROVIDER_UNAVAILABLE` by default or `WAITING_FOR_PROVIDER` when
  enqueue-while-unavailable is configured.
- [x] Run focused reindex/API tests and record exact results.
- [x] Update this plan's Spec Compliance table and progress.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`,
`mneme_service/schemas.py`, `tests/test_reindex.py`,
`tests/test_openapi.py`, possibly `tests/test_embeddings.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_openapi.py tests/test_embeddings.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 14.8 / CM-042 | Reindex create/poll job lifecycle exists | ✓ met | `tests/test_reindex.py` verifies create/poll scope, persisted job records after app restart, status/progress fields, and candidate counts. |
| Sections 10, 21, 22 / CM-020, CM-060 | Provider and idempotency behavior is bounded | ✓ met | Default unavailable provider returns `503 PROVIDER_UNAVAILABLE`; enqueue mode creates `WAITING_FOR_PROVIDER`; `Idempotency-Key` replay/conflict covered. |
| S24-52 / S24-63 | Enqueue and polling required tests are covered | ✓ met | Focused reindex gate `53 passed, 1 warning` across reindex/OpenAPI/embeddings/metrics/contract. |

**Compliance Status: VERIFIED**

## Verification Evidence

- RED reindex check:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py -q`
  -> `4 failed, 1 warning` against the in-memory stub.
- GREEN reindex check:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py -q`
  -> `4 passed, 1 warning`.
- Focused task/regression gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_openapi.py tests/test_embeddings.py tests/test_metrics.py tests/test_contract.py -q`
  -> `53 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> pass.
- Diff hygiene:
  `git diff --check` -> pass.

## Implementation Evidence

- Added `tests/test_reindex.py` for scoped create/poll, idempotency
  replay/conflict, provider-unavailable defaults, `WAITING_FOR_PROVIDER`,
  `QUEUED`, candidate progress, and persistence across app restart.
- Added persistent `reindex_jobs` storage table and storage helpers in
  `mneme_service/storage.py`.
- Added candidate-count selection for scoped session/project/all jobs,
  `PENDING`/`FAILED`, active embedding-model missing rows, and `force=true`.
- Updated `/v1/maintenance/reindex` create in `mneme_service/app.py` to use
  normalized idempotency hash, provider availability behavior, and persistent
  job records.
- Updated reindex polling to return `404 NOT_FOUND` for missing or
  out-of-scope jobs.
- Spark worker `019efa10-e761-7460-a5db-c46bc2517cd3` performed read-only
  implementation audit; parent adopted its table/idempotency/scope/provider
  recommendations for Task 03.

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
