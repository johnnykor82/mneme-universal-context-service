# Plan: 01-blob-storage-endpoints

## Level

task

## Parent

`.planning/work/03-blob-bytes-ref-export-delete-multipart/plan.md`

## Status

complete

## Goal

Implement SQLite-owned blob storage and the direct blob REST endpoints required
by Section 13.4.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 13.1-13.5 | Server-owned SQLite blobs, blob schema, BYTES_REF response shape, single-range reads |
| Section 21 | `413 PAYLOAD_TOO_LARGE`, `415 UNSUPPORTED_MEDIA_TYPE`, `416 RANGE_NOT_SATISFIABLE`, `404 NOT_FOUND` envelopes |
| Section 22 | `POST /v1/blobs` and `DELETE /v1/blobs/{id}` idempotency |
| CM-031, CM-032 | Owned blob protocol and direct blob endpoints |
| S24-15, S24-16, S24-54 | Upload/metadata/content/range/delete, 413 envelope, single-range semantics |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for blob upload, metadata fetch, full content fetch, valid
  range fetch, malformed range, unsatisfiable range, oversized upload, unsupported
  media type, scoped visibility, and blob upload/delete idempotency.
- [x] Add storage tables and methods for server-owned SQLite blobs with hash,
  media type, session/project scope, reference count, retention metadata, and
  byte content.
- [x] Add error helpers or route handling for `415 UNSUPPORTED_MEDIA_TYPE` and
  `416 RANGE_NOT_SATISFIABLE`.
- [x] Add `POST /v1/blobs`, `GET /v1/blobs/{blob_id}`,
  `GET /v1/blobs/{blob_id}/content`, and `DELETE /v1/blobs/{blob_id}`.
- [x] Add typed OpenAPI/Pydantic response/request schemas for blob routes.
- [x] Update capabilities only for direct blob store and single-range support
  after route tests pass.
- [x] Run focused verification for blob/storage/openapi tests.

Step evidence:

- RED:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_storage.py -q`
  -> expected failures: `/v1/blobs` returned 404 and blob tables were absent.
- GREEN:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_storage.py -q`
  -> `9 passed, 1 warning`.
- Capabilities/OpenAPI RED:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q`
  -> expected failure: `supports_blob_store` remained `False` after route
  implementation.
- Focused Task 01 verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_openapi.py tests/test_storage.py -q`
  -> `14 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.

## Expected File Touches

`mneme_service/storage.py`, `mneme_service/app.py`,
`mneme_service/errors.py`, `mneme_service/schemas.py`,
`tests/test_blobs.py`, `tests/test_openapi.py`, `tests/test_storage.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_openapi.py tests/test_storage.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 13.1-13.5 / CM-031 / CM-032 | Owned SQLite blob endpoint lifecycle | ✓ met | `tests/test_blobs.py` covers upload, metadata, full content, range content, scoped visibility, delete; `tests/test_storage.py` covers blob tables. |
| Section 21 / S24-16, S24-54 | Blob error envelopes and range semantics | ✓ met | `tests/test_blobs.py::test_blob_upload_errors_use_contract_envelopes`; `tests/test_blobs.py::test_blob_upload_fetch_metadata_content_range_delete_and_gc`. |
| Section 22 | Blob upload/delete idempotency | ✓ met | `tests/test_blobs.py::test_blob_upload_fetch_metadata_content_range_delete_and_gc` verifies upload replay/conflict and delete replay. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
