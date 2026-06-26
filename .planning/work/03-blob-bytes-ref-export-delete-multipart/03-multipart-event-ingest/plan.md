# Plan: 03-multipart-event-ingest

## Level

task

## Parent

`.planning/work/03-blob-bytes-ref-export-delete-multipart/plan.md`

## Status

complete

## Goal

Implement multipart `/v1/events` ingestion with binary blob parts, placeholder
rewrite, digest-aware idempotency, byte limits, and atomic rollback.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 13.4 | Multipart event ingestion contract for `payload` and `blob.<client_part_id>` parts |
| Section 14.3 | Event ingestion remains batch-first and preserves raw content |
| Section 18 | Multipart byte and transaction guards use the writer lane safely |
| Section 21 | Multipart validation errors use 400/413/415 envelopes |
| Section 22 | Multipart replay uses `Idempotency-Key`, canonical payload hash, and binary part digests |
| CM-024, CM-031, CM-033, CM-036, CM-060 | Multipart, blob digest, atomicity, event ingest, and idempotency gaps |
| S24-17, S24-53, S24-66, S24-76, S24-114 | Multipart BYTES_REF creation, validation, digest hashing, limits, rollback |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for multipart `payload` plus binary parts producing
  normalized BYTES_REF content in stored events and responses.
- [x] Add RED tests for missing payload, missing blob part, unreferenced blob
  part, unsupported content type, part over `max_blob_bytes`, total blob bytes
  over limit, and malformed placeholder references.
- [x] Add RED tests for request-scoped idempotency replay and incompatible
  binary digest conflict.
- [x] Add RED tests that a forced blob persistence failure rolls back all
  events and blob metadata.
- [x] Add multipart parsing route branch for `/v1/events` while preserving the
  existing JSON request contract and OpenAPI documentation.
- [x] Add storage transaction helper for blob rows plus event rows so successful
  multipart requests become visible atomically.
- [x] Record original and normalized content hashes or equivalent audit/debug
  metadata for multipart events.
- [x] Run focused multipart/blob/contract tests.

Step evidence:

- RED create:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py::test_multipart_event_ingest_creates_bytes_ref_for_binary_parts -q`
  -> expected failure: `/v1/events` treated multipart body as invalid Pydantic JSON request.
- RED rollback:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py::test_multipart_ingest_blob_failure_rolls_back_all_events -q`
  -> expected failure: staged blob row remained after later invalid event schema.
- RED conflict rollback:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py::test_multipart_event_conflict_does_not_leave_blob_rows -q`
  -> expected failure: staged blob row remained after event-id conflict.
- RED transaction helper:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py::test_store_put_blob_records_and_events_is_atomic -q`
  -> expected failure: `Store.put_blob_records_and_events` missing.
- Focused Task 03/regression:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_storage.py tests/test_openapi.py -q`
  -> `54 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`,
`mneme_service/schemas.py`, `tests/test_blobs.py`,
`tests/test_contract.py`, `tests/test_storage.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_storage.py -q`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 13.4 / S24-17, S24-53 | Multipart payload and blob part contract | ✓ met | `tests/test_blobs.py::test_multipart_event_ingest_creates_bytes_ref_for_binary_parts`; `tests/test_blobs.py::test_multipart_event_ingest_validates_payload_and_blob_parts`. |
| Section 13.4 / Section 22 / S24-66 | Multipart digest-aware idempotency and hashes | ✓ met | `tests/test_blobs.py::test_multipart_event_ingest_replays_by_payload_and_blob_digest`; stored events include `original_content_hash` and `normalized_content_hash`. |
| Section 13.4 / Section 18 / S24-76, S24-114 | Multipart byte limits and rollback atomicity | ✓ met | `tests/test_blobs.py::test_multipart_event_ingest_rejects_blob_byte_limits`; rollback tests for invalid schema, event conflict, and transaction helper failure; `tests/test_storage.py::test_store_put_blob_records_and_events_is_atomic`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
