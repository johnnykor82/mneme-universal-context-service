# Plan: 37-residual-contract-fix-batch-ah

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Add direct `SEGMENT_ANCHOR` graph-edge evidence for segment anchor events and
narrow the remaining graph/segment/expand-context residuals tracked by
`CM-029`, `CM-040`, and `CM-046`.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 12.8 / CM-029 | Graph edges include segment anchor relationships. |
| Section 14.6 / CM-040 | Segments preserve anchor events and lifecycle metadata. |
| Section 14.12 / CM-046 | Expand-context graph traversal can expose complete segment-anchor adjacency. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Inspect current segment anchor persistence and graph-edge helpers. | Found direct segment anchors were validated/persisted, and `SEGMENT_ANCHOR` scoring existed, but no edge producer existed. |
| 2 | complete | Add failing test proving segment start with `anchor_event_ids` emits/export exposes `SEGMENT_ANCHOR` edges. | RED: focused segment test failed because export lacked `SEGMENT_ANCHOR`. |
| 3 | complete | Implement minimal segment-anchor edge storage without changing unrelated edge semantics. | GREEN: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py -q -k "direct_segment_start_close_list_get_and_events"` -> `1 passed, 9 deselected, 1 warning`. |
| 4 | complete | Run touched-area verification and update matrix/planning evidence. | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_graph.py -q -k "segment or graph or anchor"` -> `15 passed, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_segments.py` or `tests/test_graph.py`
- `mneme_service/app.py` or `mneme_service/storage.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused command selected after Step 1.
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_graph.py -q -k "segment or graph or anchor"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-029 `SEGMENT_ANCHOR` subrequirement | verified | `tests/test_segments.py::test_direct_segment_start_close_list_get_and_events` verifies exported `SEGMENT_ANCHOR` graph edge. |
| CM-040 segment-anchor subrequirement | verified | Direct segment start now persists anchors and creates graph edge evidence. |
| CM-046 segment-anchor traversal/evidence subrequirement | verified | Expand-context graph mode traverses the new `SEGMENT_ANCHOR` edge. |

**Compliance Status: VERIFIED for this sub-slice.** `CM-029`, `CM-040`, and
`CM-046` remain `PARTIAL` pending broader edge taxonomy/frontier/lifecycle
coverage.
