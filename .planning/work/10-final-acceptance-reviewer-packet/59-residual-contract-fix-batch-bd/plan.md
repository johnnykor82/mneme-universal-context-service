# Plan: 59-residual-contract-fix-batch-bd

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Normalize stale `CM-033` matrix status after backup/restore, CLI blob-GC,
startup/session-close/retention cleanup, and operations evidence are present.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 13.5-13.6 / CM-033 | Blob storage layout, export, backup, and GC triggers must be safe, scoped, idempotent, and not overclaim background GC behavior. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Re-check Section 13.6 MUST/SHOULD boundary and current evidence. | Section 13.6 requires explicit REST/CLI/startup/session-close/retention triggers; periodic timer is SHOULD and not advertised as implemented. |
| 2 | complete | Update `CM-033` status/evidence/gap and matrix counts. | `rg -n "\\| CM-033 .*\\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md` returned no matches; summary counts are `COMPLIANT: 51`, `PARTIAL: 13`. |
| 3 | complete | Update planning evidence. | `git diff --check` exit 0. |

## Expected File Touches

- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/progress.md`
- `.planning/findings.md`

## Verification Commands

- Matrix audit:
  `rg -n "\\| CM-033 .*\\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-033 blob lifecycle/GC/export/backup matrix residual | ✓ met | Matrix now marks `CM-033` `COMPLIANT` with evidence for REST/CLI blob GC, export, startup/session-close/retention cleanup, backup/restore verification, and no background-GC overclaim; diff hygiene clean. |

**Compliance Status: VERIFIED**
