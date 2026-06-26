# Plan: 01-residual-matrix-section24-audit

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Audit every remaining `PARTIAL` compliance matrix row and Section 24 partial
mapping after Phase 9, then classify each as already covered by existing
evidence, a real residual implementation/test gap, or an explicit deferral
candidate requiring user approval.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 23-25 | Testing, acceptance, traceability |
| Sections 27-30 | Gap register, reviewer checklist, approval gate |
| CM-012, CM-061, CM-062, CM-063, CM-065 | Final acceptance rows |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Spawn Spark workers for independent residual row clusters.
- [x] Build a row-by-row residual disposition table in `.planning/findings.md`.
- [x] Identify the smallest real implementation/test fix batches for Tasks 02
  and 03.
- [x] Update this plan with exact residual counts and recommended next active
  task.
- [x] Run no production implementation until the audit identifies bounded fixes.

## Expected File Touches

`.planning/findings.md`, `.planning/progress.md`, this plan, possibly
`.planning/work/10-final-acceptance-reviewer-packet/02-residual-contract-fix-batch-a/plan.md`
and `03-residual-contract-fix-batch-b/plan.md`.

## Verification Commands

- `rg -n "\\| CM-[0-9]+ .*\\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `rg -n "\\| [0-9, ]+ \\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Sections 23-25, 27-30 | Residual gaps are fully classified before final fixes | ✓ met | Spark audits classified Phase 9 residuals: matrix has `COMPLIANT=12`, `PARTIAL=52`, `OUT_OF_SCOPE/FUTURE=1`; Section 24 maps all 1-119 with 39 compliant IDs and 80 partial IDs. |
| CM-012, CM-061, CM-062, CM-063, CM-065 | Final acceptance path is concrete | ✓ met | Findings identify real B-gap clusters plus C decision points CM-013/014 and acceptance rows CM-061/062; next active task is Batch A security/idempotency residuals. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
