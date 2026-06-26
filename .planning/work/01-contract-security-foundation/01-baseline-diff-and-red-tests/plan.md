# Plan: 01-baseline-diff-and-red-tests

## Level

task

## Parent

`.planning/work/01-contract-security-foundation/plan.md`

## Status

complete

## Goal

Identify exactly what the dirty Phase 1A work already covers, then add or
update first-phase RED tests for remaining contract/security gaps.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 8, 9, 14.1, 20, 21 | Foundation contract and security behaviors |
| CM-017, CM-018, CM-019, CM-034, CM-058, CM-059 | Rows to reconcile before coding |
| S24-25, S24-43, S24-59, S24-77, S24-85, S24-111, S24-118 | First RED coverage targets |

## Active Step

Active Task: none (leaf)

## Steps

- [x] Inspect dirty diffs for prior Phase 1A files without reverting anything.
  - Verification: `git diff -- mneme_service tests docs README.md`
- [x] Map existing tests to first-phase Section 24 numbers and identify gaps.
  - Verification: `rg -n "project_isolation|auth_failure|openapi|capabilities|readiness|Idempotency-Key" tests mneme_service`
- [x] Add or adjust focused RED tests for uncovered first-phase gaps.
  - Verification: focused pytest command fails for the expected missing behavior.
- [x] Record the gap/test mapping in the phase notes.
  - Verification: current task plan has test evidence before implementation begins.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Sections 8, 9, 14.1, 20, 21 | ~ partial | Dirty Phase 1A work and focused tests inventoried; implementation remains in downstream Phase 1 tasks |
| CM-017, CM-018, CM-019, CM-034, CM-058, CM-059 | ~ partial | Mapped to task 02-06 plans; no matrix rows marked compliant yet |
| S24 first-phase tests | ~ partial | Added RED/GREEN coverage for S24-25 project isolation and S24-118 auth-failure audit; remaining S24 targets stay in task-specific plans |

**Compliance Status: COMPLETE FOR BASELINE INVENTORY; PHASE 1 REMAINS PARTIAL**

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|
| `pytest` node id `tests/test_mcp_contract.py::test_mcp_context_search_fetch_expand_and_recall_recent` did not exist and exited 4 | 1 | Located actual MCP parity test names with `rg`; rerun with existing node ids only |
| `pytest` node id `tests/test_mcp_contract.py::test_mcp_rest_tool_parity_against_in_process_rest` did not exist and exited 4 | 2 | Listed all MCP test functions and selected `test_mcp_rest_memory_tool_parity` |

## Notes

- This task is executable only after plan approval.
- Dirty worktree inventory confirmed prior Phase 1A edits in `mneme_service/app.py`,
  `mneme_service/config.py`, `mneme_service/errors.py`,
  `mneme_service/storage.py`, `tests/test_config.py`,
  `tests/test_contract.py`, plus untracked `mneme_service/schemas.py` and
  `tests/test_openapi.py`.
- Added and verified `test_auth_failure_audit_uses_unauthenticated_principal`:
  initial RED failed because no auth-failure audit record was persisted; GREEN
  passed with `1 passed, 1 warning`.
- Added and verified `test_global_scope_respects_project_isolation_header`:
  initial RED exposed daemon-global `GLOBAL` search leakage; GREEN passed with
  `1 passed, 1 warning`.
- Post-compaction focused verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_auth_failure_audit_uses_unauthenticated_principal tests/test_contract.py::test_global_scope_respects_project_isolation_header -q`
  -> `2 passed, 1 warning`.
