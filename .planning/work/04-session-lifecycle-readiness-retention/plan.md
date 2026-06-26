# Plan: 04-session-lifecycle-readiness-retention

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Complete session lifecycle, generated-id rules, readiness semantics, retention
cleanup, and lifecycle audit without weakening project isolation, blob cleanup,
or idempotency guarantees established in earlier phases.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.1, 14.2 | Session start/get/close/generated-id/export/delete/retention lifecycle |
| Sections 13.6, 16 | Retention cleanup, blob GC coupling, audit/forensic anchors |
| Section 14.1 | Readiness semantics and capabilities truthfulness |
| Section 22 | Idempotency for generated session start, close, and retention cleanup |
| CM-022, CM-035 | Session schema and lifecycle gaps |
| CM-033, CM-042 | Retention-triggered blob GC and maintenance lifecycle gaps |
| CM-034, CM-058 | Capabilities/OpenAPI truthfulness for newly implemented lifecycle routes |
| CM-048, CM-051 | Evidence freshness/lifecycle audit gaps touched by cleanup semantics |
| CM-055, CM-056 | At-rest/retention derivative cleanup and bounded storage operation implications |
| CM-060, CM-061, CM-062 | Idempotency, testing/acceptance, and required test mapping |
| S24-2, 3, 46, 48, 50, 59, 64, 67, 73, 74, 84, 86, 91, 111 | Required tests for this phase |

## Active Task

Active Task: none

## Tasks

| Task | Status | Purpose |
|---|---|---|
| `01-session-lifecycle-endpoints` | complete | Add redacted `GET /v1/sessions/{id}`, nondestructive close, generated-id-with-idempotency, session-id validation, and close idempotency. |
| `02-readiness-capabilities-contract` | complete | Align readiness outcomes, provider-call boundaries, OpenAPI schemas, and capabilities flags for implemented lifecycle support. |
| `03-retention-cleanup-endpoint` | complete | Add `POST /v1/sessions/{id}/retention/cleanup` request/response contract, scope checks, active skip/force semantics, and idempotency. |
| `04-retention-storage-audit-delete` | complete | Implement retention deletion of eligible events/derivatives/blobs, session-close/startup sweep hooks where in-scope, and anonymized forensic audit anchors for privacy delete. |
| `05-phase-verification-evidence` | complete | Run focused/full verification and update compliance matrix, Section 24 mapping, progress, findings, and phase compliance evidence. |

## Expected File Touches

| Area | Expected files |
|---|---|
| REST contract | `mneme_service/app.py`, `mneme_service/schemas.py`, `mneme_service/errors.py` |
| Storage/lifecycle | `mneme_service/storage.py`, possibly `mneme_service/config.py` |
| Tests | `tests/test_contract.py`, `tests/test_blobs.py`, `tests/test_openapi.py`, `tests/test_storage.py` |
| Evidence | `docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`, `.planning/progress.md`, this plan tree |

## Required Verification Commands

- Focused Phase 4:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_blobs.py tests/test_openapi.py tests/test_storage.py -q`
- MCP regression:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
- Full suite:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Verification Gates

- `GET /v1/sessions/{id}` and close must enforce the same principal/project
  visibility rules as export/delete.
- Generated session ids may be accepted only with `Idempotency-Key`.
- Retention cleanup must skip active sessions by default and must not allow
  scoped adapter tokens to force active cleanup.
- Retention cleanup and delete must preserve or create only safe anonymized
  forensic audit anchors; no raw event content may survive via audit records.
- Capabilities may advertise retention cleanup only after the endpoint and
  focused tests pass.
- Every Section 24 test mapped to Phase 4 must either pass directly or have an
  equivalent named test recorded in the matrix.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Sections 12.1 / 14.2 / CM-022 / CM-035 | partial | Direct session get/close/generated-id/session-id validation/retention/delete behavior covered by `tests/test_contract.py`; remaining gaps include in-flight-read conflict tracking and export `include_audit` policy. |
| Section 14.1 / CM-034 / CM-058 / S24-59, 84, 111 | partial | Readiness and capabilities/OpenAPI evidence covered by `tests/test_contract.py` and `tests/test_openapi.py`; metrics/reindex/adaptor-depth capabilities remain later phases. |
| Sections 13.6 / 16 / CM-033 / CM-042 / CM-051 / CM-055 / CM-056 / S24-46, 50, 64, 67, 73, 74, 86 | partial | Tasks 03-04 added retention cleanup contract, ENDED cutoff candidate/deletion counting, active default skip, scoped-force rejection, idempotency replay, actual eligible event/blob/derived cleanup, session-close sweep evidence, OpenAPI evidence, and anonymized forensic anchors. Remaining nuance for phase verification: in-flight-read conflict tracking is not separately implemented. |
| Section 22 / S24-48 | partial | Generated-id, close, and retention cleanup idempotency covered; segment/execution-state/reindex idempotency remains later phases. |
| Sections 23-24 / CM-061 / CM-062 | partial | Phase 4 focused `55 passed`, MCP `16 passed`, full `196 passed`, compile and diff hygiene passed; matrix Section 24 mapping updated. |

**Compliance Status: COMPLETE FOR PHASE 4; ROADMAP-WIDE COMPLIANCE STILL PARTIAL**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
