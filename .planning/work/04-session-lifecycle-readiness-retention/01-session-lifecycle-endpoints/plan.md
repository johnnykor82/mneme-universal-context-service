# Plan: 01-session-lifecycle-endpoints

## Level

task

## Parent

`.planning/work/04-session-lifecycle-readiness-retention/plan.md`

## Status

complete

## Goal

Add direct session lifecycle endpoints and validation required before retention
can safely act on session status.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.1, 14.2 | Session start required fields, generated-id rules, GET, close, export/delete continuity |
| Section 22 | Idempotency for session start generated id and close |
| CM-022, CM-035, CM-060, CM-062 | Session lifecycle and idempotency matrix rows |
| S24-2, 3, 48, 91, 92 | Required session get/close/generated-id/session-id/unknown-export tests |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add/adjust RED tests for redacted `GET /v1/sessions/{session_id}`,
  nondestructive close, generated-id-with-idempotency, and pathlike/oversized
  session id validation.
- [x] Implement session id validation shared by session-bound REST routes.
- [x] Implement generated session ids only when `Idempotency-Key` is present;
  incompatible generated-id replay must return `409 CONFLICT`.
- [x] Implement `GET /v1/sessions/{session_id}` with redacted session summary
  and visible derived counts.
- [x] Implement `POST /v1/sessions/{session_id}/close` with `status=ENDED`,
  `ended_at`, nondestructive event retention, and idempotency replay/conflict.
- [x] Update OpenAPI/session response schemas and keep export/delete behavior
  compatible with existing tests.
- [x] Run focused lifecycle tests and compile check.

## Evidence

| Gate | Result |
|---|---|
| RED lifecycle tests | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_get_session_returns_redacted_summary tests/test_contract.py::test_session_close_is_nondestructive_and_idempotent tests/test_contract.py::test_session_start_generates_id_only_with_idempotency_key tests/test_contract.py::test_session_id_validation_rejects_oversized_or_pathlike_ids tests/test_openapi.py::test_openapi_documents_session_lifecycle_read_and_close_routes -q` initially failed 5/5 for missing GET/close/generated-id/validation/OpenAPI behavior. |
| Targeted GREEN | Same command -> `5 passed, 1 warning`. |
| Focused contract/OpenAPI | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py -q` -> `21 passed, 1 warning`. |
| Focused Phase 4 subset | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_blobs.py tests/test_openapi.py tests/test_storage.py -q` -> `48 passed, 1 warning`. |
| Compile | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` -> passed. |

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`, `mneme_service/schemas.py`,
`mneme_service/errors.py`, `tests/test_contract.py`, `tests/test_openapi.py`,
possibly `tests/test_storage.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-2 | `GET /v1/sessions/{id}` returns redacted summary | verified | `tests/test_contract.py::test_get_session_returns_redacted_summary`; focused contract/OpenAPI `21 passed`. |
| S24-3 | Session close is nondestructive | verified | `tests/test_contract.py::test_session_close_is_nondestructive_and_idempotent`; focused contract/OpenAPI `21 passed`. |
| S24-48 | Generated session id requires and replays with `Idempotency-Key` | verified | `tests/test_contract.py::test_session_start_generates_id_only_with_idempotency_key`; targeted GREEN `5 passed`. |
| S24-91 | Session id validation rejects oversized/pathlike ids | verified | `tests/test_contract.py::test_session_id_validation_rejects_oversized_or_pathlike_ids`; targeted GREEN `5 passed`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| 1 | Focused contract/OpenAPI after initial GREEN | Legacy alpha BYTES_REF test still accepted arbitrary `file://` references and failed against Phase 3 owned blob implementation. | Updated the test to upload an owned `/v1/blobs` blob and ingest the returned `mneme-blob://` BYTES_REF; focused contract/OpenAPI then passed. |
