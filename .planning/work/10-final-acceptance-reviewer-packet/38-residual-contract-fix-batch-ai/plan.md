# Plan: 38-residual-contract-fix-batch-ai

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close or narrow the `CM-040` segment lifecycle residual by making direct segment
close semantics expose `ABANDONED` and `SUPERSEDED` outcomes/statuses
consistently through REST list/get responses.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.6 / CM-040 | Segment lifecycle supports closed, abandoned, and superseded states/outcomes. |
| Section 12 segment schemas | Segment close request/result use allowed lifecycle outcomes. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Inspect spec, current close implementation, and tests for segment lifecycle status/outcome semantics. | Found outcomes were accepted but direct close always stored public status `CLOSED`. |
| 2 | complete | Add focused failing tests for direct segment close with `ABANDONED` and `SUPERSEDED` outcomes. | RED: focused pytest failed because `ABANDONED` response status was `CLOSED`. |
| 3 | complete | Implement minimal public status/outcome mapping while preserving existing `CLOSED` behavior. | GREEN: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py -q -k "event_importance_and_segment_created_by_enums_validate"` -> `1 passed, 9 deselected, 1 warning`. |
| 4 | complete | Run touched-area verification and update matrix/planning evidence. | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_openapi.py -q -k "segment or openapi"` -> `20 passed, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_segments.py`
- `mneme_service/app.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused command selected after Step 1.
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_openapi.py -q -k "segment or openapi"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-040 abandoned/superseded lifecycle residual | verified | Direct segment close maps `ABANDONED` and `SUPERSEDED` outcomes to matching terminal public statuses and supports status filtering. |

**Compliance Status: VERIFIED.** `CM-040` is reclassified `COMPLIANT` in the
compliance matrix.
