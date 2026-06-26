# Plan: 05-project-scope-enforcement

## Level

task

## Parent

`.planning/work/01-contract-security-foundation/plan.md`

## Status

complete

## Goal

Apply effective project scope consistently so `GLOBAL` means caller-visible,
not daemon-global.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 9 | Effective project scope and cross-project restrictions |
| Sections 14.9-14.11 | Tool/discovery/search scope semantics |
| CM-019, CM-044, CM-045, CM-052 | Isolation and discovery leakage rows |
| S24-25, S24-26, S24-27, S24-29 | Project isolation and discovery filtering |

## Active Step

Active Task: none (leaf)

## Steps

- [x] Add fixtures with at least two project isolation keys and scoped principals.
  - Verification: tests can create visible and forbidden sessions.
- [x] Enforce scope in session discovery and memory tool routes.
  - Verification: `resolve_session`, `list_sessions`, and search tests filter results.
- [x] Enforce scope in export/delete and current session-bound endpoints.
  - Verification: forbidden cross-project access returns `403 FORBIDDEN`.
- [x] Prepare shared helper boundaries for future blob/retention scope checks.
  - Verification: helper unit tests cover OWNER and scoped adapter behavior.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 9 / CM-019 | ~ partial | Scoped tokens now restrict session start, discovery, `GLOBAL` search, memory tools, costs, export, and delete; future blob/retention routes inherit helper pattern when added |
| Sections 14.9-14.11 / CM-044 / CM-045 | ~ partial | `resolve_session` and `list_sessions` filter by caller-visible project scope; `GLOBAL` search uses visible session ids |
| Section 17.1 / CM-052 | ~ partial | Cross-project scoped-token access returns `403 FORBIDDEN`; candidate discovery is filtered |
| S24-25 / 26 / 27 / 29 | ~ partial | Added scoped-token tests for project start, discovery filtering, caller-visible global search, and cross-project session-bound endpoint forbiddance |

**Compliance Status: COMPLETE FOR TASK 05; FUTURE ROUTES REMAIN IN LATER PHASES**

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|

## Notes

- Blob read scope is fully verified when blob endpoints land in Phase 03.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_scoped_token_can_start_only_matching_project_session tests/test_contract.py::test_scoped_token_discovery_filters_other_projects tests/test_contract.py::test_scoped_token_global_search_is_caller_visible_without_header tests/test_contract.py::test_scoped_token_forbids_cross_project_session_bound_endpoints -q`
  -> `4 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py tests/test_config.py -q`
  -> `42 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_retrieval.py tests/test_parity_recovery.py tests/test_context_prepare.py -q`
  -> `28 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m py_compile mneme_service/app.py mneme_service/storage.py mneme_service/security.py tests/test_contract.py tests/test_openapi.py`
  -> passed.
