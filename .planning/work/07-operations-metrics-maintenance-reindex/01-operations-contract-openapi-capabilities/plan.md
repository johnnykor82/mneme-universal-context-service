# Plan: 01-operations-contract-openapi-capabilities

## Level

task

## Parent

`.planning/work/07-operations-metrics-maintenance-reindex/plan.md`

## Status

complete

## Goal

Define and test the Phase 7 public contract surface before implementing deeper
metrics and reindex behavior.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 14.7, 14.8, 19, 20, 21 | Trace/cost, maintenance/reindex, metrics, OpenAPI, errors |
| CM-041, CM-042, CM-057, CM-058 | Trace/cost schemas, maintenance endpoint schemas, metrics contract, OpenAPI readiness |
| S24-44, S24-45, S24-52, S24-63, S24-72, S24-77, S24-108 | Trace/cost, reindex, metrics contract hooks |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED OpenAPI/capabilities tests for `/v1/metrics`, reindex
  create/poll/cancel routes, typed schemas, and error envelopes.
- [x] Add RED tests that capabilities advertise metrics/reindex support only
  when the corresponding route behavior exists.
- [x] Add/complete request/response schemas for metrics and reindex job objects.
- [x] Add minimal route stubs only where needed to make the contract
  inspectable, without claiming behavior not yet implemented.
- [x] Run focused OpenAPI/capabilities tests and record exact results.
- [x] Update this plan's Spec Compliance table and progress.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/schemas.py`,
`tests/test_openapi.py`, `tests/test_config.py`, possibly
`tests/test_contract.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_config.py tests/test_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 20 / CM-058 | OpenAPI exposes typed Phase 7 route schemas | ✓ met | `tests/test_openapi.py` documents `/v1/metrics`, `/v1/maintenance/reindex`, `/v1/maintenance/reindex/{job_id}`, `/v1/maintenance/reindex/{job_id}/cancel`, typed schemas, and v0 error envelopes; focused gate `54 passed, 1 warning`. |
| Sections 14.7, 14.8, 19 / CM-041, CM-042, CM-057 | Capabilities and route contracts are truthful | ✓ met | Capabilities now advertise `supports_metrics`, `supports_reindex_jobs`, and `supports_reindex_job_polling`; runtime contract guard in `tests/test_contract.py` verifies metrics auth/text and reindex create/poll/cancel shapes. |
| S24-44, S24-45, S24-52, S24-63, S24-72, S24-77, S24-108 | Required operational route tests have contract anchors | ✓ met | Contract anchors added for metrics and reindex routes; deeper behavior remains scheduled in Phase 7 Tasks 02-05. |

**Compliance Status: VERIFIED**

## Verification Evidence

- RED check:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q -k "metrics_and_reindex or capabilities_match_metrics"`
  -> `1 failed, 1 passed, 6 deselected, 1 warning` on missing
  `MetricsResponse`.
- New focused GREEN check:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_contract.py -q -k "metrics_and_reindex or capabilities_match_metrics or capabilities_advertise"`
  -> `4 passed, 32 deselected, 1 warning`.
- Required task gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_config.py tests/test_contract.py -q`
  -> `54 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> pass.
- Diff hygiene:
  `git diff --check` -> pass.

## Implementation Evidence

- Added typed schemas in `mneme_service/schemas.py`:
  `MetricsResponse`, `ReindexRequest`, `ReindexCancelRequest`,
  `ReindexJobProgress`, and `ReindexJobResponse`.
- Added `/v1/metrics` Prometheus text contract in `mneme_service/app.py`.
- Added minimal in-process reindex create/poll/cancel route contract in
  `mneme_service/app.py` with project/session/all scope checks and v0 job shape.
- Updated capabilities to advertise metrics and reindex support required by
  Final v0.7.5 Section 14.1.
- Spark worker `019efa06-1860-7670-8ef0-e460b4254498` performed read-only
  contract review and confirmed required paths/status values/schemas; parent
  limited this task to metrics/reindex contract and left trace/cost typing and
  deeper job lifecycle to later Phase 7 tasks.

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
