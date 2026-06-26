# Plan: 69-config-routing-audit-batch-bn

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Audit the remaining `CM-017` and `CM-039` configuration/routing residuals to
separate stale matrix text from concrete missing config validation or runtime
behavior.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 8 | Configuration model, validation, routing weights, provider/maintenance policy. |
| Sections 14.5.1, 14.11 | Runtime-neutral routing intelligence and routing score formulas. |
| CM-017, CM-039 | Config model and routing intelligence matrix rows. |

## Steps

| Step | Status | Verification |
|---|---|---|
| Use Spark read-only audit to classify each remaining `CM-017`/`CM-039` residual phrase | complete | Spark `Heisenberg` found a real shared routing-policy config gap and a stale provider-backed lifecycle residual. |
| Parent reviews audit and decides normalization versus implementation batch | complete | Parent confirmed `retrieval.routing` config parity should be implemented in a narrow follow-up batch. |
| Update matrix/planning evidence or create follow-up implementation task | complete | Created Batch BO for routing config model/validation/runtime propagation. |

## Expected File Touches

If stale: `docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`, and this plan tree only. If implementation is needed:
create a follow-up implementation batch before source/test edits.

## Verification Commands

- Audit:
  `rg -n "\\| CM-0(17|39) .*\\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- If matrix-only normalization:
  `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 8 / 14.5.1 / 14.11 / CM-017 / CM-039 | Config/routing residual disposition | ✓ met | Batch BN audit complete; Batch BO created for implementation. |

**Compliance Status: VERIFIED**
