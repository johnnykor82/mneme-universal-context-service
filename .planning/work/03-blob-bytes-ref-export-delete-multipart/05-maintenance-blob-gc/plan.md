# Plan: 05-maintenance-blob-gc

## Level

task

## Parent

`.planning/work/03-blob-bytes-ref-export-delete-multipart/plan.md`

## Status

complete

## Goal

Implement scoped, idempotent blob garbage collection with dry-run support and
safe candidate/deleted/skipped counts.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 13.6 | Orphan blob GC is safe, idempotent, explicit, and observable |
| Section 14.8 | `/v1/maintenance/blob-gc` request, authorization, and response counts |
| Section 21 | GC auth/scope errors use standard envelopes |
| Section 22 | Compatible GC dry-run requests replay equivalent summaries |
| CM-033, CM-042, CM-052, CM-060 | Blob GC, maintenance auth, security boundary, idempotency gaps |
| S24-51 | Maintenance blob GC requires scope and is idempotent |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for owner daemon-wide dry-run GC, project-scoped GC, and
  scoped-token rejection of unscoped daemon-wide GC.
- [x] Add RED tests for GC idempotency replay and incompatible request conflict.
- [x] Add RED tests proving dry-run does not delete candidates and non-dry-run
  deletes only unreferenced visible blob rows.
- [x] Add request/response schemas for blob GC and OpenAPI route documentation.
- [x] Add storage GC candidate selection and deletion bounded to session/project
  scope.
- [x] Add `POST /v1/maintenance/blob-gc` with existing auth and idempotency
  helpers.
- [x] Update capabilities for implemented blob store/export bundle without
  overclaiming retention cleanup or reindex jobs.
- [x] Run focused blob/maintenance/openapi tests.

Step evidence:

- RED:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py::test_maintenance_blob_gc_requires_scope_and_is_idempotent tests/test_blobs.py::test_scoped_token_cannot_run_unscoped_blob_gc -q`
  -> expected failures: `/v1/maintenance/blob-gc` returned 404.
- Focused Task 05:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_openapi.py -q`
  -> `23 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`,
`mneme_service/schemas.py`, `tests/test_blobs.py`,
`tests/test_openapi.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_openapi.py -q`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 13.6 / Section 14.8 / S24-51 | Scoped, idempotent blob GC | ✓ met | `tests/test_blobs.py::test_maintenance_blob_gc_requires_scope_and_is_idempotent`; `tests/test_blobs.py::test_scoped_token_cannot_run_unscoped_blob_gc`. |
| Section 21 | GC auth/scope errors use standard envelopes | ✓ met | Scoped unscoped GC returns `403 FORBIDDEN`; invalid idempotency replay returns `409 CONFLICT`. |
| Section 22 | Compatible GC replay uses idempotency ledger | ✓ met | `Idempotency-Key` replay/conflict covered in `test_maintenance_blob_gc_requires_scope_and_is_idempotent`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
