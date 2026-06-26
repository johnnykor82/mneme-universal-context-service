# Plan: 03-retention-cleanup-endpoint

## Level

task

## Parent

`.planning/work/04-session-lifecycle-readiness-retention/plan.md`

## Status

complete

## Goal

Add the explicit retention cleanup endpoint contract before deeper storage
cleanup logic is broadened.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 13.6, 14.2 | `POST /v1/sessions/{id}/retention/cleanup`, cutoff semantics, active skip, scoped authorization |
| Section 22 | Retention cleanup idempotency |
| CM-033, CM-035, CM-042, CM-060, CM-062 | Retention cleanup and maintenance mapping |
| S24-50, 64, 74, 86 | Required retention endpoint tests |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for retention cleanup request/response shape, timestamp
  cutoff, visible scope enforcement, active-session skip, and force-active
  conflict/authorization behavior.
- [x] Add typed `RetentionCleanupRequest` and `RetentionCleanupResponse` schemas.
- [x] Implement `POST /v1/sessions/{session_id}/retention/cleanup` with
  existing principal/project scope checks.
- [x] Implement dry-run/default body semantics and `Idempotency-Key`
  replay/conflict for compatible/incompatible requests.
- [x] Keep cleanup behavior conservative until storage deletion is implemented
  in Task 04; counts must be truthful and not overclaim deleted records.
- [x] Update OpenAPI and capabilities only for behavior that is actually tested.
  `supports_retention_cleanup` remains `false` until Task 04 implements actual
  deletion/audit lifecycle, to avoid overclaiming completed cleanup behavior.
- [x] Run focused retention endpoint tests and compile check.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/schemas.py`, `mneme_service/storage.py`,
`tests/test_contract.py`, `tests/test_openapi.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-50 | Retention cleanup uses event timestamp cutoff | complete | `tests/test_contract.py::test_retention_cleanup_uses_ended_session_timestamp_cutoff` verifies ENDED-session cutoff and event candidate count. |
| S24-64 | Retention cleanup requires visible scope | complete | `tests/test_contract.py::test_retention_cleanup_requires_visible_scope_and_owner_for_active_force` verifies cross-project scoped token rejection. |
| S24-74 | Active sessions are skipped unless force is valid | complete | `tests/test_contract.py::test_retention_cleanup_skips_active_by_default_and_replays` and scoped force-active rejection test. |
| S24-86 | Request/response and force conflict contract | partial | Typed request/response, default body, idempotency replay, OpenAPI, and OWNER-only force covered. In-flight-read `409 IN_FLIGHT_READS` remains for Task 04/cleanup execution because there is no in-flight read tracker yet. |

**Compliance Status: COMPLETE FOR TASK 03 CONTRACT; FULL RETENTION CLEANUP REMAINS TASK 04**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| RED | Targeted retention/OpenAPI tests before implementation | `405 Method Not Allowed` and missing OpenAPI path | Added typed retention cleanup route and schemas. |
| GREEN-1 | Targeted retention/OpenAPI tests after first route patch | `require_schema(..., required=False)` unsupported; optional body produced OpenAPI `anyOf null` schema | Switched to `Body(default_factory=RetentionCleanupRequest)` and optional schema-version validation. |

## Evidence

- Targeted RED:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_retention_cleanup_skips_active_by_default_and_replays tests/test_contract.py::test_retention_cleanup_uses_ended_session_timestamp_cutoff tests/test_contract.py::test_retention_cleanup_requires_visible_scope_and_owner_for_active_force tests/test_openapi.py::test_openapi_documents_session_lifecycle_read_and_close_routes -q`
  -> `4 failed, 1 warning` before implementation.
- Targeted GREEN:
  same command -> `4 passed, 1 warning`.
- Focused contract/OpenAPI:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py -q`
  -> `25 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Phase 4 focused subset:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_blobs.py tests/test_openapi.py tests/test_storage.py -q`
  -> `52 passed, 1 warning`.
