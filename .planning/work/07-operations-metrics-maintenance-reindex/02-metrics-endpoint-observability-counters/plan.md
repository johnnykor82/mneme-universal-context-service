# Plan: 02-metrics-endpoint-observability-counters

## Level

task

## Parent

`.planning/work/07-operations-metrics-maintenance-reindex/plan.md`

## Status

complete

## Goal

Implement `/v1/metrics` and required safe operational/retrieval-intelligence
counter families.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 19 | `/v1/metrics`, operational counters, retrieval-intelligence counters, safe structured observability |
| CM-057 | Operations and observability gap |
| S24-72, S24-77, S24-108 | Metrics endpoint, capabilities advertised format, retrieval/segmentation quality metrics |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for `/v1/metrics` auth, format, and required metric family
  names.
- [x] Add RED tests that metrics output does not include bearer/provider secrets
  or unredacted evidence content.
- [x] Implement metrics collection/export for request counts/latency,
  provider calls/failures/latency, writer queue depth, background backlog,
  embedding pending/failed counts, reindex status counts, retention sweeps,
  blob bytes/count, startup integrity status, intent labels, segment rollover,
  routing modes, and indexing compression by event type where current data
  exists.
- [x] Ensure capabilities/docs advertise the actual metrics format.
- [x] Run focused metrics/OpenAPI tests and record exact results.
- [x] Update this plan's Spec Compliance table and progress.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`, possibly
`mneme_service/embeddings.py`, `tests/test_metrics.py`,
`tests/test_openapi.py`, `tests/test_contract.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_metrics.py tests/test_openapi.py tests/test_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 19 / CM-057 | Metrics endpoint and required metric families exist | ✓ met | `tests/test_metrics.py` verifies required Prometheus family names and secret-safe output; focused gate `38 passed, 1 warning`. |
| S24-72 / S24-77 / S24-108 | Metrics endpoint, capabilities format, retrieval-intelligence counters | ✓ met | `/v1/metrics` exports Prometheus text, capabilities advertise `metrics_format=prometheus`, and retrieval/segmentation/intelligence metric families are present with safe zero defaults when no labelled data exists. |

**Compliance Status: VERIFIED**

## Verification Evidence

- RED metrics check:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_metrics.py -q`
  -> `1 failed, 1 passed, 1 warning` because only
  `mneme_startup_integrity_status` existed.
- GREEN metrics check:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_metrics.py -q`
  -> `2 passed, 1 warning`.
- Focused task gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_metrics.py tests/test_openapi.py tests/test_contract.py -q`
  -> `38 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> pass.
- Diff hygiene:
  `git diff --check` -> pass.

## Implementation Evidence

- Added `tests/test_metrics.py` for required Prometheus family names and
  secret/evidence non-disclosure.
- Added lightweight HTTP request count/latency middleware and Prometheus text
  exporter in `mneme_service/app.py`.
- Added safe metric families for provider calls/failures/latency, writer queue
  depth, background backlog, embedding statuses, reindex status counts,
  retention sweeps, blob bytes/count, startup integrity, intent labels,
  segment rollovers, routing modes, indexing compression, and labelled
  retrieval quality placeholders.
- Added storage-level aggregate snapshot helpers in `mneme_service/storage.py`
  using numeric counts only; no event content or sensitive metadata values are
  exported.
- Spark worker `019efa0b-2da5-7d81-9c3f-59f5db5d4d32` performed read-only
  inventory of existing metric data sources and confirmed which families could
  be exported immediately versus represented by lightweight instrumentation.

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
