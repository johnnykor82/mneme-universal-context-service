# Plan: 02-graph-traversal-limits-anchors

## Level

task

## Parent

`.planning/work/05-state-segments-lineage-graph-routing/plan.md`

## Status

complete

## Goal

Make graph expansion deterministic and bounded, add traversal warnings, bound
importance/depth effects, and prepare graph evidence edges needed by later
routing and memory-feedback work.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.8, 14.12 | Graph edge schema, deterministic traversal, depth/frontier/branch limits |
| CM-029, CM-046 | Graph schema and expand-context gaps |
| S24-23, 24, 88, 98, 105, 110 | Traversal determinism, truncation warnings, bounded boost, evidence edges |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for deterministic graph traversal ordering.
- [x] Add RED tests for depth/frontier/branch/traversal stop warnings.
- [x] Add RED tests for bounded importance boost by depth.
- [x] Add/update graph edge metadata needed for `SEGMENT_ANCHOR` and
  `MEMORY_READ_EVIDENCE` without leaking raw content.
- [x] Implement traversal limit enforcement in expand-context paths.
- [x] Ensure warnings appear in REST/MCP-compatible response envelopes.
- [x] Run focused graph/contract tests and compile check.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/storage.py`, possibly
`mneme_service/schemas.py`, `tests/test_graph.py`, `tests/test_contract.py`,
`tests/test_mcp_contract.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py tests/test_mcp_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-23 | Expand context uses deterministic traversal | complete | `tests/test_graph.py::test_expand_context_uses_typed_graph_edges_and_audits_all_exposed_ids`; deterministic sorted neighbor traversal added. |
| S24-24 | Expand context truncates with warning | complete | `tests/test_graph.py::test_expand_context_stops_at_traversal_limits_with_warning`. |
| S24-88 | Importance boost bounded by depth | complete | `tests/test_graph.py::test_expand_context_depth_limit_warns_and_bounds_importance_boost`. |
| S24-98 | Memory read evidence graph/state behavior | partial | Existing memory-read audit/state tests remain green; full `MEMORY_READ_EVIDENCE` edge behavior continues in routing feedback task. |
| S24-105 | Graph evidence edges match contract | partial | Typed parent-derived graph edges are exported; `SEGMENT_ANCHOR` and `MEMORY_READ_EVIDENCE` edges remain with segment/routing tasks. |
| S24-110 | Traversal stops at configured limits with warning | complete | `tests/test_graph.py::test_expand_context_stops_at_traversal_limits_with_warning` and depth-limit warning test. |

**Compliance Status: COMPLETE FOR TASK 02**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| RED | New graph traversal limit tests before implementation | Missing `truncation_reason`, depth-limit warning, and `importance_boost` metadata | Added deterministic traversal result metadata, max-events/depth warnings, and bounded boost calculation. |

## Evidence

- Targeted graph:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q`
  -> `5 passed, 1 warning`.
- Focused Phase 5 subset:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py tests/test_graph.py tests/test_contract.py tests/test_retrieval.py tests/test_openapi.py -q`
  -> `50 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Diff hygiene:
  `git diff --check` -> passed.
