# Plan: 41-residual-contract-fix-batch-al

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-046` by implementing one explicit mode-specific
`expand_context` traversal behavior, with `TEMPORAL` mode as the preferred
minimal slice if inspection confirms it is safe.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.12 / CM-046 | Expand context modes have deterministic semantics; `TEMPORAL` returns seed, previous events, and next events by timestamp. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Inspect current mode handling and confirm the smallest safe mode-specific slice. | Selected `TEMPORAL`; current code only special-cased `SEGMENT` and routed all other modes to graph traversal. |
| 2 | complete | Add focused failing test for selected mode behavior. | RED: focused temporal pytest failed because graph fallback returned graph/segment-anchor neighbors instead of timestamp neighbors. |
| 3 | complete | Implement minimal mode-specific traversal without disrupting existing graph mode. | GREEN: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q -k "temporal_mode"` -> `1 passed, 6 deselected, 1 warning`. |
| 4 | complete | Run touched-area verification and update matrix/planning evidence. | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or temporal"` -> `9 passed, 41 deselected, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_graph.py`
- `mneme_service/app.py` or `mneme_service/storage.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused command selected after Step 1.
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or temporal"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-046 mode-specific traversal residual | verified | `tests/test_graph.py::test_expand_context_temporal_mode_uses_timestamp_order_without_graph_edges` verifies explicit `TEMPORAL` mode. |

**Compliance Status: VERIFIED for this sub-slice.** `CM-046` remains `PARTIAL`
pending `TOOL_CHAIN`/`CAUSAL` mode semantics and full edge-completeness
coverage.
