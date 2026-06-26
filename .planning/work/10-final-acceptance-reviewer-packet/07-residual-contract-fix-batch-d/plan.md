# Plan: 07-residual-contract-fix-batch-d

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Implement a narrow Section 24 residual fix for event importance and segment
enum validation, especially S24-80 invalid enum rejection, without broad
segment lifecycle refactoring.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.3, 12.10, 14.3, 14.6 | Event importance plus segment schema and direct segment REST endpoints |
| CM-036, CM-040, CM-062 | Event/segment enum residual and Section 24 mapping |
| S24-80 | Event importance and segment created_by enums validate |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to confirm exact enum fields and test
  placement.
- [x] Add failing tests for invalid segment enum values currently accepted or
  under-tested.
- [x] Implement minimal validation in segment create/close flows, preserving
  existing generated-id and close behavior.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/schemas.py` if needed,
`tests/test_segments.py`, `docs/MNEME_V0_COMPLIANCE_MATRIX.md`,
`.planning/findings.md`, `.planning/progress.md`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py -q -k "enum or invalid"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_openapi.py tests/test_contract.py -q`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| CM-036, CM-040 / S24-80 | Event importance and segment enum validation | ✓ met | `tests/test_segments.py::test_event_importance_and_segment_created_by_enums_validate`; focused RED -> `1 failed, 8 deselected, 1 warning`; focused GREEN -> `1 passed, 8 deselected, 1 warning`; touched-area gate -> `45 passed, 1 warning`; full suite -> `265 passed, 1 warning`; compileall and diff hygiene passed. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
