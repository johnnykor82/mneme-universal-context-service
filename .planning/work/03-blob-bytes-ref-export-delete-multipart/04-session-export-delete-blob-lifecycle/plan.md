# Plan: 04-session-export-delete-blob-lifecycle

## Level

task

## Parent

`.planning/work/03-blob-bytes-ref-export-delete-multipart/plan.md`

## Status

complete

## Goal

Align session export and delete with blob metadata, metadata-only JSON export,
portable `tar_bundle` export, stable omission reasons, and scoped blob cleanup.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 12.6 | `mneme.session_export.v0` and `mneme.session_export_manifest.v0` schemas |
| Section 13.6 | JSON metadata-only export, tar bundle blob bytes, session delete blob cleanup |
| Section 14.2 | Export query params, unknown format validation, omission reason enum, delete semantics |
| CM-031, CM-033, CM-035, CM-059 | Export/delete blob lifecycle and error gaps |
| S24-49, S24-62, S24-81, S24-92 | JSON export scope, tar bundle, omission enum, unknown format validation |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests proving `format=json` returns
  `schema_version=mneme.session_export.v0`, `format=json`, blob metadata with
  stable omitted reasons, and empty `blob_contents`.
- [x] Add RED tests proving cross-project export does not leak blob metadata.
- [x] Add RED tests proving unknown export format returns `422 VALIDATION_ERROR`
  with `details.field="format"`.
- [x] Add RED tests proving `format=tar_bundle&include_blobs=true` returns
  `application/x-tar` with `manifest.json` and `blobs/...` entries.
- [x] Add RED tests proving session delete removes blobs referenced only by the
  deleted session and leaves shared blobs or GC candidates safe.
- [x] Update export route query handling and storage export payload shape.
- [x] Implement tar bundle streaming response path and manifest generation.
- [x] Update session delete storage operations to clean blob refs/bytes inside
  the same transaction where possible.
- [x] Run focused export/delete/blob tests.

Step evidence:

- RED JSON/unknown format:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py::test_session_export_json_is_metadata_only_and_respects_scope tests/test_blobs.py::test_unknown_export_format_returns_422_validation_error -q`
  -> expected failures: legacy export lacked `schema_version`; unknown format returned `200`.
- RED tar bundle:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py::test_session_export_tar_bundle_streams_blob_parts -q`
  -> expected failure: `tar_bundle` returned `422`.
- RED delete:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py::test_delete_session_removes_session_scoped_blobs -q`
  -> expected failure: blob row remained after session delete.
- Focused Task 04/regression:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_openapi.py -q`
  -> `50 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`,
`mneme_service/schemas.py`, `tests/test_blobs.py`,
`tests/test_contract.py`, `tests/test_openapi.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_openapi.py -q`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 13.6 / Section 14.2 / S24-49 | JSON export is metadata-only and scoped | ✓ met | `tests/test_blobs.py::test_session_export_json_is_metadata_only_and_respects_scope`; `tests/test_blobs.py::test_cross_project_export_does_not_leak_blob_metadata`. |
| Section 14.2 / S24-62 | Tar bundle includes manifest and blob parts | ✓ met | `tests/test_blobs.py::test_session_export_tar_bundle_streams_blob_parts`; route returns `StreamingResponse` over a spooled tar file. |
| Section 14.2 / S24-81, S24-92 | Omission enum and unknown format validation | ✓ met | JSON export emits `FORMAT_JSON_METADATA_ONLY`; `tests/test_blobs.py::test_unknown_export_format_returns_422_validation_error`. |
| Section 13.6 | Session delete cleans owned blob lifecycle safely | ✓ met | `tests/test_blobs.py::test_delete_session_removes_session_scoped_blobs`; `Store.delete_session` deletes blob refs and blob rows in the session delete transaction. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
