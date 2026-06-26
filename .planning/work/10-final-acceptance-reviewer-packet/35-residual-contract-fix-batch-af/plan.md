# Plan: 35-residual-contract-fix-batch-af

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close a narrow turn-completion graph/provenance subgap by emitting an
idempotent canonical `TURN_COMPLETE` event whose `parent_event_ids` link to the
completed turn events.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.3, 12.4 / CM-025 | `TURN_COMPLETE` event and turn completion provenance |
| Sections 12.8, 14.4 / CM-037 | Graph edges are generated from explicit `parent_event_ids` |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Add failing contract test proving turn completion emits a `TURN_COMPLETE` event and graph edge. | RED: focused pytest failed because export lacked the event/edge. |
| 2 | complete | Add minimal idempotent event emission in turn completion using existing normalization/hash/storage/graph helpers. | GREEN: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "turn_complete_emits_event"` -> `1 passed, 42 deselected, 1 warning`. |
| 3 | complete | Run touched-area verification and update matrix/planning evidence. | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_graph.py -q -k "turn_complete or graph or edge"` -> `11 passed, 37 deselected, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_contract.py`
- `mneme_service/app.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "turn_complete_emits_event"`
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_graph.py -q -k "turn_complete or graph or edge"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-025 turn-complete event/provenance subrequirement | verified | `tests/test_contract.py::test_turn_complete_emits_event_and_graph_provenance` plus Batch AF touched-area gate `11 passed`. |
| CM-037 graph/provenance update on turn completion subrequirement | verified | Export now contains canonical `TURN_COMPLETE` event with `parent_event_ids`; exported graph edges include parent-derived `FOLLOWS`. |

**Compliance Status: VERIFIED for this sub-slice.** `CM-025` and `CM-037`
remain `PARTIAL` pending provider-metric and broader usage-counter evidence.
