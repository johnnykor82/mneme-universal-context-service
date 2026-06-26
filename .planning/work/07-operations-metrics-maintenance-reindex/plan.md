# Plan: 07-operations-metrics-maintenance-reindex

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Complete operational metrics, maintenance endpoints, provider retry/backoff,
reindex lifecycle, and operational observability required for v0 compliance.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 10, 14.7, 14.8, 19, 21, 23-25 | Provider/cost behavior, trace/cost endpoints, maintenance/reindex, metrics, errors, testing, traceability |
| CM-020, CM-041, CM-042, CM-057, CM-061, CM-062, CM-063 | Provider, trace/cost, maintenance, operations, test and matrix evidence |
| S24-37-39, 44-45, 52, 63, 68, 72, 75, 77, 87, 108 | Operations/reindex/metrics/cost required tests |

## Active Task

Active Task: none

## Tasks

| Task | Status | Purpose |
|---|---|---|
| `01-operations-contract-openapi-capabilities` | complete | Establish typed contract/capability/OpenAPI surface for metrics, reindex maintenance, trace/cost schema, and error envelopes before behavior work. |
| `02-metrics-endpoint-observability-counters` | complete | Implement `/v1/metrics` and required operational/retrieval-intelligence counters with safe output. |
| `03-reindex-create-poll-scope-idempotency` | complete | Add reindex create/poll endpoints, scoped authorization, idempotency, status/progress persistence, and OpenAPI schemas. |
| `04-reindex-cancel-provider-safety` | complete | Add cooperative cancel semantics, final-state idempotency, provider-call stop behavior, and cancel evidence. |
| `05-reindex-engine-resiliency-priority` | complete | Add provider wait/retry/backoff/circuit breaker/ramp and background priority/yield behavior. |
| `06-phase-verification-evidence` | complete | Run Phase 7 focused/full verification and update matrix, Section 24 mapping, findings, progress, and roadmap evidence. |

## Expected File Touches

| Area | Expected files |
|---|---|
| REST contract/OpenAPI | `mneme_service/app.py`, `mneme_service/schemas.py`, `tests/test_openapi.py`, `tests/test_contract.py` |
| Metrics/operations | `mneme_service/app.py`, `mneme_service/storage.py`, `tests/test_metrics.py` or `tests/test_contract.py` |
| Reindex jobs | `mneme_service/app.py`, `mneme_service/storage.py`, `mneme_service/embeddings.py`, `tests/test_reindex.py`, `tests/test_embeddings.py` |
| Capabilities/provider status | `mneme_service/config.py`, `mneme_service/app.py`, `tests/test_config.py`, `tests/test_openapi.py` |
| Evidence | `docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`, `.planning/progress.md`, this plan tree |

## Required Verification Commands

- Phase 7 focused gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_contract.py tests/test_embeddings.py tests/test_config.py -q`
- Reindex/metrics focused gate after endpoint work:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_metrics.py tests/test_openapi.py -q`
- MCP regression:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
- Full suite:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Verification Gates

- Capabilities must not overclaim unsupported operations before implementation.
- `/v1/metrics` must expose the configured format and required families without
  leaking bearer tokens, provider secrets, or unredacted evidence.
- Reindex create/poll/cancel endpoints must enforce project/session scope and
  use v0 error envelopes.
- Reindex jobs must expose `QUEUED`, `RUNNING`, `WAITING_FOR_PROVIDER`,
  `COMPLETED`, `FAILED`, and `CANCELLED` where relevant.
- Cancellation must stop future provider requests and future background writes
  after the current micro-transaction.
- Provider wait/retry/backoff/circuit-breaker behavior must be bounded and
  observable.
- Background work must not starve foreground writer operations.
- Every Phase 7 Section 24 mapping must either pass directly or be recorded as
  an explicit residual gap.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Sections 10, 14.7, 14.8, 19, 21 | ✓ met for Phase 7 scope | `/v1/metrics` and reindex maintenance routes are implemented, scoped, typed in OpenAPI, and covered by `tests/test_metrics.py`, `tests/test_reindex.py`, `tests/test_openapi.py`, and `tests/test_contract.py`; trace/cost schema residuals remain recorded for later/final acceptance. |
| CM-020, CM-041, CM-042, CM-057 | ✓ evidence updated | `docs/MNEME_V0_COMPLIANCE_MATRIX.md` now records Phase 7 improvements and residual gaps; impacted rows remain `PARTIAL` where their row-level scope exceeds this phase. |
| S24-37-39, 44-45, 52, 63, 68, 72, 75, 77, 87, 108 | ✓ mapped | S24-52/63 moved to direct compliant evidence; S24-68/75/87 and S24-72/77/108 updated with new tests and residual breadth notes where applicable. |

**Compliance Status: VERIFIED**

## Planning Evidence

- Spark worker `019ef9fa-9f61-7cd0-8271-000a8760729a` performed a read-only
  Phase 7 audit and recommended contract foundation before reindex API,
  cancellation, resiliency, and metrics/observability completion.
- Parent review split metrics into its own early task so `/v1/metrics` can
  provide observability while later reindex behavior lands.
