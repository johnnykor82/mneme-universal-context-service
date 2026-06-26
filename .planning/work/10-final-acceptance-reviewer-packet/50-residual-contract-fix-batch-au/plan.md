# Plan: 50-residual-contract-fix-batch-au

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-028` by enforcing `audit.forensic_retention_days` for anonymized
forensic audit anchors created during privacy delete.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 12.7 / CM-028 | Deleted-session security-sensitive audit records are converted to anonymized forensic anchors and retained only within forensic retention policy. |
| Section 16 / CM-028 | Retention/privacy lifecycle must preserve local-owner forensics without keeping deleted-session evidence forever. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Use Spark/read-only audit to identify the narrow `CM-028` subgap. | Spark `019effdf-0bb8-7643-92e4-277edd948cc7` found missing runtime cleanup for aged forensic anchors. |
| 2 | complete | Add RED storage/contract test for forensic anchors older than retention cutoff. | RED: focused pytest failed with missing `Store.purge_forensic_anchors_older_than()`, and startup test failed before startup hook. |
| 3 | complete | Add minimal storage cleanup primitive for forensic anchors only. | Focused AU tests passed after adding storage purge and startup hook. |
| 4 | complete | Run touched verification and update matrix/planning evidence. | Touched audit/forensic/retention gate passed; compileall and `git diff --check` exit 0. |

## Expected File Touches

- `tests/test_contract.py`
- `mneme_service/storage.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_forensic_audit_anchors_expire_after_retention_days tests/test_contract.py::test_startup_purges_expired_forensic_audit_anchors -q`
- Touched:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "audit or forensic or retention"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-028 forensic retention sub-residual | ✓ met | Focused AU tests -> `2 passed`; touched gate -> `13 passed`; compileall and diff hygiene clean. |

**Compliance Status: VERIFIED**
