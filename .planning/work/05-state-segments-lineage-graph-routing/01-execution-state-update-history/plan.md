# Plan: 01-execution-state-update-history

## Level

task

## Parent

`.planning/work/05-state-segments-lineage-graph-routing/plan.md`

## Status

complete

## Goal

Add the explicit REST execution-state update contract with scoped authorization,
PATCH/REPLACE behavior, required provenance, deterministic state hashes, and
append-only state history evidence.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.5, 14.5 | `mneme.execution_state.v0`, explicit update endpoint, state history entries, canonical hashes |
| CM-026 | Execution state and state history gaps |
| S24-10, 11, 109, 119 | Explicit update, provenance, canonical hash, compression trace/state interactions |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for `POST /v1/sessions/{session_id}/execution_state`
  PATCH and REPLACE modes.
- [x] Add RED tests requiring at least one provenance identifier:
  `event_id`, `turn_id`, or `adapter_trace_id`.
- [x] Add RED tests rejecting unknown state fields with `422 VALIDATION_ERROR`.
- [x] Implement typed request/response schemas and OpenAPI route docs.
- [x] Implement deterministic state hashing over canonical redacted state.
- [x] Persist append-only `mneme.state_history_entry.v0` with sequence,
  changed fields, previous/new state hash, provenance, and summary.
- [x] Run focused state/OpenAPI tests and compile check.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/schemas.py`, `mneme_service/state.py`,
`mneme_service/storage.py`, `tests/test_state.py`, `tests/test_openapi.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_openapi.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-10 | Explicit execution-state update records history | complete | `tests/test_state.py::test_explicit_execution_state_update_patch_replace_records_history`. |
| S24-11 | Execution-state update requires provenance | complete | `tests/test_state.py::test_execution_state_update_requires_provenance_and_rejects_unknown_fields`. |
| S24-109 | Canonical state hashes are deterministic | partial | `test_explicit_execution_state_update_patch_replace_records_history` verifies stable hash fields and previous-hash chaining; broader JCS fixture coverage remains possible later. |
| S24-119 | State/compression trace interactions remain inspectable | partial | Existing state/context tests continue passing; dedicated compression-trace coverage remains in Phase 6. |

**Compliance Status: COMPLETE FOR TASK 01**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| RED | Targeted state/OpenAPI tests before implementation | `405 Method Not Allowed` and missing OpenAPI path | Added typed execution-state update route, schemas, storage history/hash support. |

## Evidence

- Targeted RED:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py::test_explicit_execution_state_update_patch_replace_records_history tests/test_state.py::test_execution_state_update_requires_provenance_and_rejects_unknown_fields tests/test_openapi.py::test_openapi_documents_core_route_request_and_response_models -q`
  -> `3 failed, 1 warning` before implementation.
- Targeted GREEN:
  same command -> `3 passed, 1 warning`.
- Focused state/OpenAPI:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_openapi.py -q`
  -> `14 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Phase 5 focused subset:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py tests/test_graph.py tests/test_contract.py tests/test_retrieval.py tests/test_openapi.py -q`
  -> `48 passed, 1 warning`.
- Diff hygiene:
  `git diff --check` -> passed.
