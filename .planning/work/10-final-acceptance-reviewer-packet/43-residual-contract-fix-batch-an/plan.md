# Plan: 43-residual-contract-fix-batch-an

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-029`/`CM-046` by aligning parent-derived graph edges with the
Section 12.8 `PARENT_CHILD` edge type and default weight.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 12.8 / CM-029 | Explicit `parent_event_ids` generate `PARENT_CHILD` edges with default weight `0.9`. |
| Section 14.12 / CM-046 | `TOOL_CHAIN`/`CAUSAL` traversal includes parent/child graph edges using the canonical taxonomy. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Add/adjust focused RED expectations for canonical `PARENT_CHILD` edges and weight. | RED: focused pytest failed because ordinary parent links still exported `FOLLOWS` with weight `1.0`. |
| 2 | complete | Update graph edge producer and traversal allow-lists for `PARENT_CHILD`. | GREEN: focused pytest -> `2 passed, 51 deselected, 1 warning`. |
| 3 | complete | Run touched-area verification and update matrix/planning evidence. | Touched-area pytest -> `12 passed, 41 deselected, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_graph.py`
- `tests/test_contract.py`
- `mneme_service/storage.py`
- `mneme_service/app.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "parent_child or turn_complete_emits_event"`
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or traversal or turn_complete_emits_event"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-029 / CM-046 parent-child edge taxonomy residual | verified | `tests/test_graph.py::test_ingest_persists_parent_child_graph_edges_with_default_weight`; `tests/test_contract.py::test_turn_complete_emits_event_and_graph_provenance`; touched-area pytest `12 passed`. |

**Compliance Status: VERIFIED for this sub-slice.** `CM-029` and `CM-046`
remain `PARTIAL` pending explicit `TOOL_INPUT`/`SEGMENT_MEMBER` edge coverage.
