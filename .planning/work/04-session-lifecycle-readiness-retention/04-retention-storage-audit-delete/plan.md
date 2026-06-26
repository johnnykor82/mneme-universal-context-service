# Plan: 04-retention-storage-audit-delete

## Level

task

## Parent

`.planning/work/04-session-lifecycle-readiness-retention/plan.md`

## Status

complete

## Goal

Wire retention and privacy delete into storage, blob cleanup, and audit
semantics without preserving raw deleted content in forensic records.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 13.6, 14.2, 16 | Retention deletes eligible content/derivatives/blobs and preserves safe audit anchors |
| Section 18 | Background cleanup must use bounded storage operations and not starve foreground work |
| CM-033, CM-035, CM-051, CM-055, CM-056, CM-062 | Retention storage/audit/delete rows |
| S24-46, 67, 73 | Required delete/automatic-sweep/audit-anchor tests |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests proving retention cleanup removes eligible events,
  searchable derivatives, traces, and session-scoped blobs while preserving
  ineligible/in-scope retained data.
- [x] Add RED tests for anonymized forensic audit anchors after privacy delete.
- [x] Implement storage retention cleanup by session/project/cutoff with
  truthful deletion/orphan counts and blob reference cleanup.
- [x] Adjust `DELETE /v1/sessions/{id}` to preserve only safe forensic audit
  anchors and remove/redact session content, traces, blobs, and derivatives.
- [x] Wire session-close/startup sweep behavior only where it can be made
  observable and tested without overclaiming background infrastructure.
- [x] Run focused storage/blob/session tests and compile check.

## Expected File Touches

`mneme_service/storage.py`, `mneme_service/app.py`, `tests/test_storage.py`,
`tests/test_contract.py`, `tests/test_blobs.py`, `tests/test_openapi.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_blobs.py tests/test_openapi.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-46 | Delete removes searchable derivatives and blobs | complete | `tests/test_contract.py::test_retention_cleanup_deletes_eligible_events_and_orphan_blobs` plus existing blob delete tests verify event removal, blob-reference detach, orphan blob GC, and retained ineligible event access. |
| S24-67 | Automatic retention sweeps are observable and scoped | complete | `tests/test_contract.py::test_session_close_retention_sweep_is_observable_and_scoped` verifies session-close sweep deletes only the closed session scope and writes safe `RETENTION_CLEANUP` audit. |
| S24-73 | Delete preserves anonymized forensic audit anchors | complete | `tests/test_contract.py::test_delete_preserves_anonymized_forensic_audit_anchors` verifies `MEMORY_READ` and `SESSION_DELETE` anchors with raw session/event/content removed. |

**Compliance Status: COMPLETE FOR TASK 04**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| RED | New Task 04 targeted tests | Missing `status` response field and `Store.list_forensic_anchors`; close did not run retention sweep | Added spec counters/status, retention cleanup storage deletion, forensic anchors, and observable session-close sweep. |
| GREEN-1 | Focused suite after close sweep | Explicit cleanup tests saw `0` candidates because automatic close sweep had already deleted old events | Disabled session-close sweep only in explicit cleanup tests so explicit and automatic behavior are verified independently. |

## Evidence

- Targeted Task 04:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_retention_cleanup_deletes_eligible_events_and_orphan_blobs tests/test_contract.py::test_delete_preserves_anonymized_forensic_audit_anchors tests/test_contract.py::test_session_close_retention_sweep_is_observable_and_scoped -q`
  -> `3 passed, 1 warning`.
- Focused storage/blob/session/OpenAPI:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_blobs.py tests/test_openapi.py -q`
  -> `55 passed, 1 warning`.
- MCP regression:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
  -> `16 passed`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Diff hygiene:
  `git diff --check` -> passed.
