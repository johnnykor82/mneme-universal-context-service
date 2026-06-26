# Plan: 05-session-discovery-lineage-search

## Level

task

## Parent

`.planning/work/05-state-segments-lineage-graph-routing/plan.md`

## Status

complete

## Goal

Stabilize session discovery, lineage-aware search/session resolution, and
caller-visible scope behavior after state, graph, segment, and routing changes.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.5 lineage schema, 14.10, 14.11 | Session lineage, discovery, context search |
| CM-044, CM-045 | Session discovery and context search gaps |
| S24-78 | Stable best-guess semantics for session resolution |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for stable session-resolution best-guess ordering and
  metadata without cross-project leaks.
- [x] Verify lineage search scope uses only caller-visible sessions.
- [x] Ensure exact inaccessible matches stay hidden or forbidden according to
  current route contract.
- [x] Add or update session-resolution metadata in tool results only where
  aligned with later MCP parity requirements.
- [x] Run focused contract/retrieval/MCP regression tests and compile check.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`, possibly
`mneme_service/schemas.py`, `tests/test_contract.py`,
`tests/test_retrieval.py`, `tests/test_mcp_contract.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_retrieval.py tests/test_mcp_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-78 | Resolve-session best-guess semantics are stable | complete | `tests/test_contract.py::test_resolve_session_best_guess_prefers_exact_project_path_before_recency`, `tests/test_contract.py::test_resolve_session_best_guess_is_null_for_recency_only_ambiguity`. |

**Compliance Status: COMPLETE FOR TASK 05**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| RED | Task 05 best-guess tests before implementation | `best_guess_session_id` missing from `resolve_session` response. | Added deterministic match sorting, `best_guess_session_id`, and `SESSION_RESOLUTION_AMBIGUOUS` warning. |
| GREEN | Focused Task 05 tests after scope changes | MCP parity surfaced canonical `MEMORY_READ` events through graph dependency and expansion after prior memory-tool calls. | Filtered `MEMORY_READ` events from graph dependency search and graph expansion results. |

## Evidence

- Targeted RED/GREEN:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_resolve_session_best_guess_prefers_exact_project_path_before_recency tests/test_contract.py::test_resolve_session_best_guess_is_null_for_recency_only_ambiguity tests/test_retrieval.py::test_context_search_project_scope_is_limited_to_visible_project tests/test_session_lineage.py::test_lineage_carry_over_searches_parent_without_copying_events tests/test_mcp_contract.py::test_mcp_resolve_session_tool_proxies_rest_envelope -q`
  -> `5 passed, 1 warning`.
- Focused Task 05:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_retrieval.py tests/test_mcp_contract.py tests/test_session_lineage.py -q`
  -> `49 passed, 1 warning`.
- Phase 5 focused subset:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py tests/test_graph.py tests/test_contract.py tests/test_retrieval.py tests/test_openapi.py tests/test_classifier.py tests/test_context_prepare.py tests/test_session_lineage.py tests/test_mcp_contract.py -q`
  -> `86 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Diff hygiene:
  `git diff --check`
  -> passed.

## Residual Notes

- `PROJECT` scope is now accepted for context search and bounded to the
  current session's project isolation key. `SESSION` is current-session-only;
  lineage carry-over requires explicit `LINEAGE`.
- `list_sessions` still uses `limit` without cursor pagination. Keep this as
  a residual CM-044/S24-26/S24-27 gap for the phase verification matrix unless
  the final Phase 5 evidence task expands scope.
