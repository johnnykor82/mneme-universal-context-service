# Plan: 42-residual-contract-fix-batch-am

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-029`/`CM-046` by adding explicit mode-aware graph traversal
ordering/filtering for `TOOL_CHAIN` and `CAUSAL`, without schema changes.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 12.8 / CM-029 | Graph edge traversal uses edge taxonomy consistently enough for mode-specific expansion. |
| Section 14.12 / CM-046 | `expand_context` modes have deterministic semantics; `TOOL_CHAIN` and `CAUSAL` use mode-specific graph traversal behavior. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Use Spark/read-only audit to identify the smallest safe slice. | Spark `019effb9-da16-7593-b1c0-65090a3ebd63` recommended mode-aware neighbor planning with no schema change. |
| 2 | complete | Add focused RED tests for `TOOL_CHAIN` and `CAUSAL` ordering. | RED: focused pytest failed with generic graph ordering for both new tests. |
| 3 | complete | Thread mode into graph expansion and apply deterministic mode-specific neighbor ordering/filtering. | GREEN: focused pytest -> `2 passed, 7 deselected, 1 warning`. |
| 4 | complete | Run touched-area verification and update matrix/planning evidence. | Touched-area pytest -> `11 passed, 41 deselected, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_graph.py`
- `mneme_service/app.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q -k "tool_chain_mode or causal_mode"`
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or traversal or tool_chain or causal"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-029 / CM-046 mode-specific traversal residual | verified | `tests/test_graph.py::test_expand_context_tool_chain_mode_prioritizes_tool_result_edges`; `tests/test_graph.py::test_expand_context_causal_mode_orders_equal_weight_neighbors_by_time`; touched-area pytest `11 passed`. |

**Compliance Status: VERIFIED for this sub-slice.** `CM-029` and `CM-046`
remain `PARTIAL` pending full edge taxonomy and edge-completeness coverage.
