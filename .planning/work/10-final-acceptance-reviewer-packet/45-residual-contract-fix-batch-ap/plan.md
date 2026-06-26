# Plan: 45-residual-contract-fix-batch-ap

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close or narrow the remaining `CM-029`/`CM-046` graph edge taxonomy residual by
adding derived `TOOL_INPUT` edge coverage and automatic `SEGMENT_MEMBER` edges.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 12.8 / CM-029 | Graph edge taxonomy includes `TOOL_INPUT` and `SEGMENT_MEMBER` with deterministic weights. |
| Section 14.12 / CM-046 | Expand-context graph traversal can traverse the complete implemented edge taxonomy. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Use Spark/read-only audit to identify minimal implementation path and ambiguities. | Spark `019effc6-8303-7543-b845-6a76c3f5c027` found no explicit tool-input event model; recommended derived parent→TOOL_CALL `TOOL_INPUT` plus ingest-time `SEGMENT_MEMBER`. |
| 2 | complete | Add focused RED tests for `TOOL_INPUT` and `SEGMENT_MEMBER` edges. | RED: focused pytest failed because `TOOL_INPUT` exported as `PARENT_CHILD` and no `SEGMENT_MEMBER` edge existed. |
| 3 | complete | Implement derived edge typing and segment-member edge persistence. | GREEN: focused pytest -> `2 passed, 20 deselected, 1 warning`. |
| 4 | complete | Run touched-area verification and update matrix/planning evidence. | Touched-area pytest -> `27 passed, 38 deselected, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_graph.py`
- `tests/test_segments.py`
- `mneme_service/storage.py`
- `mneme_service/app.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_segments.py -q -k "tool_input or segment_member"`
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_segments.py tests/test_contract.py -q -k "graph or segment or tool_input or segment_member"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-029 complete implemented edge taxonomy | verified | `tests/test_graph.py::test_ingest_persists_tool_input_edge_for_tool_call_parent`; `tests/test_segments.py::test_automatic_segment_members_emit_segment_member_edges`; touched-area pytest `27 passed`. |
| CM-046 edge-completeness traversal | verified | `TOOL_CHAIN` expand-context test covers derived `TOOL_INPUT`; graph/segment touched-area pytest stayed green. |

**Compliance Status: VERIFIED.** `CM-029` and `CM-046` are now `COMPLIANT`.

Note: `TOOL_INPUT` is implemented as a derived edge for parent message →
`TOOL_CALL` because Final v0.7.5 does not define a distinct persisted
`TOOL_INPUT` event type.
