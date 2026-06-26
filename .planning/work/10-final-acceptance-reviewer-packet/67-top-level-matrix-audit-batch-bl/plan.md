# Plan: 67-top-level-matrix-audit-batch-bl

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Audit `CM-002` and `CM-003` to determine whether their top-level service-shape
and product-boundary residuals are stale, still blocked by remaining detailed
matrix rows, or require concrete implementation/documentation fixes.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 1-2 | Standalone local context service, product boundary, request-only context insertion, no hidden prompt mutation. |
| CM-002, CM-003 | Top-level service shape and product-boundary matrix rows. |

## Steps

| Step | Status | Verification |
|---|---|---|
| Use Spark read-only audit to classify `CM-002` and `CM-003` | complete | Spark `Dalton` classified `CM-002` as a final-acceptance umbrella dependency and `CM-003` as a real docs/packaging gap. |
| Parent reviews audit and determines matrix disposition | complete | Parent confirmed `CM-002` stays `PARTIAL` until deeper rows/final gates close; `CM-003` needs a follow-up docs/test implementation batch. |
| Update matrix/planning evidence or create follow-up implementation task(s) | complete | Created follow-up Batch BM for `CM-003` release-facing core/adapter boundary cleanup. |

## Expected File Touches

If stale/final-only: `docs/MNEME_V0_COMPLIANCE_MATRIX.md`,
`.planning/findings.md`, `.planning/progress.md`, and this plan tree only. If a
real gap is found: create a follow-up implementation plan before source/test
edits.

## Verification Commands

- Audit:
  `rg -n "\\| CM-00[23] .*\\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- If matrix-only normalization:
  `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Sections 1-2 / CM-002 / CM-003 | Top-level service and boundary disposition | ✓ met | Batch BL audit complete; `CM-002` retained as umbrella dependency, `CM-003` routed to Batch BM. |

**Compliance Status: VERIFIED**
