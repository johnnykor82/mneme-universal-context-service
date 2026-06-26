# Plan: 33-residual-contract-fix-batch-ad

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close a narrow turn-completion derived segment update gap: `POST
/v1/turns/complete` must identify and update the segment(s) associated with
completed turn events instead of returning a synthetic default segment id.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 12.4 / CM-025 | Turn schema and turn-completion linkage to related derived records |
| Section 14.4 / CM-037 | Turn completion updates segments and usage counters when possible |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Add failing contract test proving turn completion returns and annotates the event-linked segment. | RED: focused pytest failed because response returned synthetic `segment-{session_id}` instead of event-linked segment id. |
| 2 | complete | Implement the smallest segment-link update in turn completion/storage while preserving existing segment lifecycle fields. | GREEN: focused `turn_complete_links` test passed. |
| 3 | complete | Run touched-area verification and update matrix/planning evidence. | Touched-area gate `27 passed, 35 deselected, 1 warning`; compile and `git diff --check` passed. |

## Expected File Touches

- `tests/test_contract.py`
- `mneme_service/app.py`
- `mneme_service/storage.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "turn_complete_links"`
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_segments.py tests/test_state.py -q -k "turn_complete or segment or state"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-025 turn/segment linkage subrequirement | ✓ met | `tests/test_contract.py::test_turn_complete_links_event_segment_without_clobbering_lifecycle`; CM-025 remains row-level `PARTIAL` for execution-state/graph/provider/broader usage semantics. |
| CM-037 segment update on turn completion subrequirement | ✓ met | Response now returns event-linked segment ids and segment metadata records last turn id/status/usage without clobbering lifecycle fields. |

**Compliance Status: VERIFIED**
