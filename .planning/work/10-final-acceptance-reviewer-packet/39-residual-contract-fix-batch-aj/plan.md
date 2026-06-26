# Plan: 39-residual-contract-fix-batch-aj

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close or narrow `CM-046` and `CM-029` by enforcing explicit
expand-context frontier/branching traversal limits and reporting deterministic
limit warnings.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.12 / CM-046 | Expand context traversal is bounded by max events, depth, frontier, and branching limits. |
| Section 12.8 / CM-029 | Graph traversal/scoring semantics are deterministic and bounded. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Inspect spec/config/current `expand_graph` behavior for frontier and branching limits. | Found config keys existed but `expand_graph()` did not enforce them. |
| 2 | complete | Add focused failing graph test for branching/frontier limit behavior and warning metadata. | RED: focused branching-factor pytest failed because all root neighbors were returned. |
| 3 | complete | Implement minimal traversal-limit enforcement without changing existing max-events/depth behavior. | GREEN: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q -k "branching_factor"` -> `1 passed, 5 deselected, 1 warning`. |
| 4 | complete | Run touched-area verification and update matrix/planning evidence. | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or traversal"` -> `8 passed, 41 deselected, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_graph.py`
- `mneme_service/app.py`
- `mneme_service/config.py` if config keys are missing
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused command selected after Step 1.
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or traversal"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-046 frontier/branching residual | verified | `tests/test_graph.py::test_expand_context_enforces_branching_factor_limit` verifies configured branching limit and `TRAVERSAL_LIMIT_REACHED` warning details. |
| CM-029 traversal-limit residual | verified | Graph traversal now receives and enforces configured branching/frontier/visited-node limits. |

**Compliance Status: VERIFIED for this sub-slice.** `CM-029` and `CM-046`
remain `PARTIAL` pending mode-specific traversal, result-truncation details,
and complete edge taxonomy coverage.
