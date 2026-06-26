# Plan: 26-residual-contract-fix-batch-w

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the retention grouped Section 24 row by auditing the remaining periodic
sweep note against the canonical spec language: startup and session-close
sweeps are mandatory, while a periodic timer is `SHOULD` and not a required
public CI blocker for S24-67.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 14.2, 24 | Retention cleanup, automatic startup/session-close sweeps, active-session skip/conflict behavior |
| CM-035, CM-042, CM-062 | Session lifecycle, maintenance lifecycle, required tests |
| S24-46, S24-50, S24-67, S24-74, S24-86 | Retention/delete required tests |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Audit canonical MUST/SHOULD wording for automatic retention sweeps.
- [x] Confirm startup, session-close, active skip, cutoff, delete, and in-flight
      conflict evidence exists.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`, and this plan.

## Verification Commands

- Inherited full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `287 passed, 1 warning`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-46, S24-50, S24-67, S24-74, S24-86 | Retention/delete required tests | compliant | Batch T/U retention gates and full suite `287 passed`. |

**Compliance Status: COMPLIANT**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
