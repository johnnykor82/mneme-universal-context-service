# Plan: 04-final-verification-matrix

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

in_progress

## Goal

Run final verification and update the compliance matrix so every in-scope row
is `COMPLIANT`, with only explicit user-approved non-goals/future deferrals left
outside compliance.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 23-25 | Final testing and traceability |
| CM-061, CM-062, CM-063 | Verification, required tests, traceability |

## Active Subtask

Active Subtask: none

## Planned Steps

- [ ] Run focused residual verification from Tasks 02-03.
- [ ] Run full local pytest suite.
- [ ] Run compileall and diff hygiene.
- [ ] Verify `/openapi.json` parse/schema checks.
- [ ] Update matrix counts, row statuses, and Section 24 mapping.

## Expected File Touches

`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/progress.md`,
`.planning/findings.md`, this plan.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| CM-061, CM-062, CM-063 | Final verification and mapping are current | pending | |

**Compliance Status: PENDING**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
