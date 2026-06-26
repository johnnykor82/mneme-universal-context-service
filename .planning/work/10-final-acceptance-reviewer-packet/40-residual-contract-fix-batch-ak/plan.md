# Plan: 40-residual-contract-fix-batch-ak

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-046` by adding `RESULT_TRUNCATED`, `dropped_count`, and frontier
summary details for graph-mode `expand_context` when `max_events` truncates the
result.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.12 / CM-046 | When `max_events` is reached, expand context returns `truncated=true`, warning `RESULT_TRUNCATED`, `dropped_count`, and frontier summary when possible. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Inspect current max-events truncation response and warning shape. | Confirmed graph mode lacked `RESULT_TRUNCATED`, `dropped_count`, and frontier summary. |
| 2 | complete | Add focused failing graph test for `RESULT_TRUNCATED`, dropped count, and frontier summary. | RED: focused pytest failed because `dropped_count` was missing. |
| 3 | complete | Implement minimal response metadata for max-events truncation. | GREEN: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q -k "traversal_limits_with_warning"` -> `1 passed, 5 deselected, 1 warning`. |
| 4 | complete | Run touched-area verification and update matrix/planning evidence. | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or traversal"` -> `8 passed, 41 deselected, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_graph.py`
- `mneme_service/app.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q -k "traversal_limits_with_warning"`
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or traversal"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-046 result truncation detail residual | verified | `tests/test_graph.py::test_expand_context_stops_at_traversal_limits_with_warning` verifies `RESULT_TRUNCATED`, `dropped_count`, and frontier summary. |

**Compliance Status: VERIFIED for this sub-slice.** `CM-046` remains `PARTIAL`
pending mode-specific traversal semantics and full edge-completeness coverage.
