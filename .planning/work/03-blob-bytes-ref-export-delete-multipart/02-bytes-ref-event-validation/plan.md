# Plan: 02-bytes-ref-event-validation

## Level

task

## Parent

`.planning/work/03-blob-bytes-ref-export-delete-multipart/plan.md`

## Status

complete

## Goal

Ensure event ingestion accepts only owned, scoped `mneme-blob://` BYTES_REF
content by default and records blob references for lifecycle operations.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 13.3 | BYTES_REF shape uses `mneme-blob://...`, hash, size, media type, and `storage_owner=SERVER` |
| Section 13.6 | Session delete and GC depend on accurate blob references |
| Section 14.3 | Inline oversized content requires retry with BYTES_REF; binary/blob content remains metadata-safe |
| Section 17.2 | Binary blob bytes are not sent to providers by default |
| CM-024, CM-031, CM-033 | Event schema and BYTES_REF lifecycle gaps |
| S24-14, S24-47 | Oversized inline retry path and default rejection/gating of `file://` adapter blobs |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Replace the existing arbitrary BYTES_REF acceptance test with RED tests
  requiring a previously uploaded visible `mneme-blob://` reference.
- [x] Add RED tests proving scoped tokens cannot ingest cross-project blob refs.
- [x] Add RED tests proving default `file://` BYTES_REF references are rejected
  unless a future trusted adapter driver explicitly advertises support.
- [x] Add storage methods for blob reference attach/detach from events without
  double-counting duplicate event replay.
- [x] Update JSON event ingest validation to verify blob existence, hash, size,
  media type, storage owner, and caller visibility.
- [x] Ensure embedding/indexing text extraction treats BYTES_REF as metadata
  only and does not process raw blob bytes.
- [x] Run focused contract/blob tests.

Step evidence:

- RED:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py -q`
  -> expected failures: cross-project BYTES_REF accepted and blob `ref_count`
  remained `0` after event ingest.
- RED detach:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py::test_store_blob_reference_attach_detach_updates_ref_count_once -q`
  -> expected failure: `Store.detach_blob_reference` missing.
- Focused Task 02/regression:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_storage.py tests/test_openapi.py -q`
  -> `45 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`, `mneme_service/utils.py`,
`tests/test_blobs.py`, `tests/test_contract.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py -q`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 13.3 / CM-031 / S24-14 | BYTES_REF is backed by owned blob protocol | ✓ met | `tests/test_contract.py::test_oversized_inline_requires_owned_bytes_ref`; JSON event ingest verifies `mneme-blob://`, storage owner, hash, size, media type, existence, and session scope. |
| Section 13.3 / S24-47 | `file://` path is not accepted by default | ✓ met | `tests/test_contract.py::test_oversized_inline_requires_owned_bytes_ref` rejects `file://` BYTES_REF with `422 VALIDATION_ERROR`. |
| Section 17.2 | Binary blob bytes are metadata-only for indexing/redaction by default | ✓ met | Existing `text_from_content` BYTES_REF path emits only media type, URI, and hash; focused `45 passed` regression confirms ingest/search paths remain green. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
