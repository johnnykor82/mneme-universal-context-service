# Plan: 03-blob-bytes-ref-export-delete-multipart

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Implement the owned SQLite blob store, BYTES_REF contract, multipart ingest,
blob export/delete, and GC lifecycle without overclaiming capabilities before
the corresponding verification passes.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 13, 14.2, 14.3, 14.8 | Blob/BYTES_REF, export, delete, multipart, GC |
| CM-031, CM-032, CM-033 | Blob lifecycle gaps |
| S24-14-17, 47, 49, 51, 53-54, 62, 66, 76, 81, 114 | Required tests |

## Active Task

Active Task: complete

## Tasks

| Task | Status | Purpose |
|---|---|---|
| `01-blob-storage-endpoints` | complete | Add SQLite-owned blob storage plus upload, metadata, content/range, delete, OpenAPI, and blob idempotency. |
| `02-bytes-ref-event-validation` | complete | Enforce owned `mneme-blob://` BYTES_REF references during event ingest and reject arbitrary `file://` references by default. |
| `03-multipart-event-ingest` | complete | Implement multipart `/v1/events` with placeholder rewrite, binary part digests, request-scoped idempotency, limits, and rollback. |
| `04-session-export-delete-blob-lifecycle` | complete | Align JSON/tar export and session delete with blob metadata, omitted reasons, tar bundle blob parts, and scoped cleanup. |
| `05-maintenance-blob-gc` | complete | Add scoped, idempotent `/v1/maintenance/blob-gc` with dry-run and deletion counts. |
| `06-phase-verification-evidence` | complete | Run focused/full verification and update compliance matrix, Section 24 mapping, progress, and phase compliance evidence. |

## Expected File Touches

| Area | Expected files |
|---|---|
| REST contract | `mneme_service/app.py`, `mneme_service/schemas.py`, `mneme_service/errors.py` |
| Storage | `mneme_service/storage.py` |
| Configuration/capabilities | `mneme_service/config.py`, `mneme_service/app.py`, `mneme_service/schemas.py` |
| Tests | `tests/test_blobs.py`, `tests/test_contract.py`, `tests/test_openapi.py`, `tests/test_storage.py` |
| Evidence | `docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`, `.planning/progress.md`, this plan tree |

## Required Verification Commands

- Focused Phase 3:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_openapi.py tests/test_storage.py -q`
- MCP regression:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
- Full suite:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Verification Gates

- No route may advertise `supports_blob_store`, `supports_blob_range_reads`, or
  `supports_export_bundle` until the matching endpoint/export tests pass.
- Every blob read/write/delete/GC route must enforce the existing principal and
  project/session scope rules.
- Every mutating blob/GC route added in this phase must use the existing
  durable `Idempotency-Key` ledger.
- Section 24 tests mapped to Phase 3 must either pass directly or have an
  equivalent named test recorded in the matrix.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 13 / CM-031 / CM-032 / CM-033 | verified | Owned `mneme-blob://` protocol, direct blob endpoints, SQLite storage, explicit GC, metadata-only JSON export, tar bundle export, and session-delete cleanup verified by `tests/test_blobs.py`, `tests/test_storage.py`, and focused Phase 3 `61 passed`. CM-033 remains `PARTIAL` only for later CLI/startup/retention-triggered GC and backup/restore procedure. |
| Section 14.2 / S24-49, 62, 81 | verified | JSON metadata-only export, unknown export format 422, stable omitted reason, and streaming `tar_bundle` verified in `tests/test_blobs.py`. |
| Section 14.3 / S24-17, 53, 66, 76, 114 | verified | Multipart placeholder rewrite, validation, digest-aware replay, total-byte limit, original/normalized hashes, and rollback verified in `tests/test_blobs.py`. |
| Section 14.8 / S24-51 | verified | Scoped, dry-run, idempotent `/v1/maintenance/blob-gc` verified in `tests/test_blobs.py`. |
| Section 21 / blob error envelopes | verified | 413/415/416/422 blob and multipart envelopes verified by focused Phase 3 tests. |
| Section 22 / blob, delete, and GC idempotency | verified | Blob upload/delete, multipart replay, and blob GC idempotency verified by focused Phase 3 tests. |

**Compliance Status: VERIFIED FOR PHASE 3 SCOPE**
